"""Optional local-browser setup. Run this on the TV's Developer Mode host PC."""
import argparse
import json
import os
from pathlib import Path
import secrets
import socket
import sys
import threading
import time
import hashlib
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from core import Companion, Store, read_payload
from vendor.aerotizen.sdb import SdbError
from diagnostics import Diagnostics
from reports import validate as validate_report, send as send_report


class ProcessLock:
    def __init__(self, folder): self.path = folder / "companion.lock"
    def __enter__(self):
        if self.path.is_symlink(): raise ValueError("Invalid setup lock file")
        self.file = self.path.open("a+b")
        os.chmod(self.path, 0o600)
        try:
            if os.name == "nt":
                import msvcrt
                self.file.seek(0)
                self.file.write(b"0")
                self.file.flush()
                self.file.seek(0)
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.file.close()
            raise ValueError("Clean Home Setup is already running. Use its existing browser window.") from None
        return self
    def __exit__(self, *args): self.file.close()


def create_server(companion, diagnostics=None, sender=send_report):
    diagnostics = diagnostics or Diagnostics(getattr(companion, "files", {}))
    cached = {"host": None, "report": None, "sent": None, "receipt": None, "sent_at": None}
    token = secrets.token_hex(32)
    operation = threading.Lock()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def respond(self, value, code=200, html=False, attachment=False):
            data = value.encode() if html else json.dumps(value).encode()
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8" if html else "application/json")
            self.send_header("Content-Length", str(len(data)))
            if attachment: self.send_header("Content-Disposition", 'attachment; filename="clean-home-compatibility.json"')
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'nonce-" + token + "'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
            self.end_headers()
            try: self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError): pass
        def permitted(self):
            host = "127.0.0.1:" + str(self.server.server_port)
            return self.headers.get("Host") == host and (self.headers.get("Origin") in (None, "http://" + host))
        def do_GET(self):
            if self.path == "/report/" + token + ".json" and self.permitted():
                if not operation.acquire(blocking=False):
                    self.respond({"error": "A TV operation is running"}, 409)
                    return
                try:
                    if cached["report"] is None: self.respond({"error": "Run Check TV first"}, 400)
                    else: self.respond(validate_report(cached["report"]), attachment=True)
                finally: operation.release()
                return
            if self.path != "/" or not self.permitted():
                self.respond({"error": "Not found"}, 404)
                return
            folder = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
            self.respond((folder / "index.html").read_text(encoding="utf-8").replace("__TOKEN__", token), html=True)
        def do_POST(self):
            self.connection.settimeout(5)
            if self.path != "/action" or not self.permitted() or self.headers.get("X-Clean-Home") != token or self.headers.get("Content-Type") != "application/json":
                self.respond({"error": "Request not allowed"}, 403)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 2 or length > 512: raise ValueError("Invalid request size")
                request = json.loads(self.rfile.read(length))
                if not isinstance(request, dict) or set(request) != {"host", "action", "confirmed"}: raise ValueError("Invalid setup request")
                if request["action"] not in ("inspect", "diagnose", "apply", "undo", "send-report"): raise ValueError("Unknown action")
                if request["action"] not in ("inspect", "diagnose") and request["confirmed"] is not True: raise ValueError("Choose the confirmation box before changing Home")
            except (ValueError, TypeError, socket.timeout):
                self.respond({"error": "Invalid request or missing confirmation"}, 400)
                return
            if not operation.acquire(blocking=False):
                self.respond({"error": "A TV operation is already running. Please wait."}, 409)
                return
            try:
                action, host = request["action"], request["host"]
                if action == "diagnose":
                    cached["host"], cached["report"] = None, None
                    report = validate_report(diagnostics.run(host))
                    result = {"supported": report["profile"] == "known", "active": False, "canApply": False, "canUndo": False, "installed": False, "phase": report["phase"], "recovery": ""}
                    if report["profile"] == "known":
                        try:
                            result.update(companion.perform(host, "inspect"))
                            report["phase"] = result["phase"] if result["phase"] in ("original", "active", "unknown") else "unknown"
                        except (ValueError, OSError, RuntimeError, SdbError):
                            report["checks"]["homeSetup"] = ["fail", "STRICT_CHECK_FAILED", "None"]
                    cached["host"], cached["report"] = host, validate_report(report)
                    self.respond({**result, "report": cached["report"]})
                elif action == "send-report":
                    if cached["host"] != host or cached["report"] is None: raise ValueError("Run Check TV before sending a report")
                    report = validate_report(cached["report"])
                    digest = hashlib.sha256(json.dumps(report, sort_keys=True).encode()).hexdigest()
                    if digest == cached["sent"]:
                        self.respond({"receipt": cached["receipt"], "duplicate": True})
                    elif cached["sent_at"] is not None and time.monotonic() - cached["sent_at"] < 60:
                        raise ValueError("Please wait one minute before sending another report")
                    else:
                        receipt = sender(report)
                        cached.update(sent=digest, receipt=receipt, sent_at=time.monotonic())
                        self.respond({"receipt": receipt})
                else:
                    result = companion.perform(host, action)
                    if action in ("apply", "undo") and cached["host"] == host and cached["report"]:
                        cached["report"]["action"] = action
                        cached["report"]["phase"] = "active" if action == "apply" else "original"
                        cached["report"]["checks"]["homeSetup"] = ["pass", "OK", "None"]
                        result["report"] = validate_report(cached["report"])
                    self.respond(result)
            except (ValueError, OSError, RuntimeError, SdbError) as error:
                if request["action"] in ("apply", "undo") and cached["host"] == request["host"] and cached["report"]:
                    cached["report"]["action"] = request["action"]
                    cached["report"]["phase"] = "unknown"
                    cached["report"]["checks"]["homeSetup"] = ["fail", "NOT_CONFIRMED", "None"]
                # Never expose native output, DUIDs, packets or stack traces.
                safe = str(error) if isinstance(error, ValueError) else "The TV did not confirm the operation. Keep the recovery folder and use Check TV, then Undo if needed. Close Apps2Samsung and check Developer Mode's Host PC address."
                self.respond({"error": safe, **({"report": validate_report(cached["report"])} if cached["host"] == request["host"] and cached["report"] else {})}, 400)
            finally:
                operation.release()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = False
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--check-package", action="store_true", help="Verify bundled assets offline; never contact a TV")
    args = parser.parse_args()
    directory = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    files = read_payload(directory / "payload")
    if args.check_package:
        text = (directory / "index.html").read_text(encoding="utf-8")
        if "__TOKEN__" not in text or "Check TV" not in text: raise ValueError("Setup page is missing")
        print("Native payload hashes and UTF-8 setup page verified. No TV contacted.")
        return
    store = Store()
    companion = Companion(store, files)
    with ProcessLock(store.folder):
        server = create_server(companion)
        url = "http://127.0.0.1:" + str(server.server_port)
        print("Clean Home Setup: " + url)
        print("Recovery originals: " + str(store.folder))
        print("Close this terminal after setup. No background TV watcher is installed.")
        if not args.no_browser: webbrowser.open(url)
        try: server.serve_forever()
        except KeyboardInterrupt: pass
        finally: server.server_close()


if __name__ == "__main__":
    try: main()
    except (ValueError, OSError) as error: raise SystemExit(str(error))
