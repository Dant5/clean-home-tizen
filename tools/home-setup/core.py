"""Device-bound originals and the optional, firmware-scoped native Home setup."""
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import socket
import sys
import time
import urllib.request

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(ROOT))
from vendor.aerotizen.transport import BoundedSdb, DeviceSessionError
from vendor.aerotizen import sdk

TARGET = "D5Q60BHome.CleanHome"
SAMSUNG = "com.samsung.tv.csfs"
MODEL = "QA55Q60BAWXXY"
FIRMWARE = "Version=T-NKLBUABC-1720.7;"
KEYS = ("db/appfw/home_appid", "db/appfw/startup_appid", "db/appfw/booting_appid_backup", "db/first_screen/type")
APPID = re.compile(r"[A-Za-z0-9_.-]{1,128}\Z")


def private_ipv4(value):
    try:
        address = ipaddress.IPv4Address(value)
    except (ValueError, TypeError):
        raise ValueError("Enter the TV's local IPv4 address from Network Status") from None
    # is_private also includes reserved/test ranges; require an actual LAN range.
    octets = address.packed
    if not (octets[0] == 10 or (octets[0] == 172 and 16 <= octets[1] <= 31) or (octets[0] == 192 and octets[1] == 168)):
        raise ValueError("Use a local home-network TV address")
    return str(address)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def device_binding(output):
    if not isinstance(output, str) or len(output) > 2048 or any(word in output.lower() for word in ("error", "failed", "unsupported", "not supported", "unknown command")):
        raise ValueError("The TV's developer identity could not be read")
    candidates = set()
    for line in output.splitlines():
        value = re.sub(r"^\s*(?:device\s+unique\s+id|duid)\s*[:=]\s*", "", line, flags=re.I).strip()
        if re.fullmatch(r"[A-Za-z0-9+/_=#.:-]{16,512}", value): candidates.add(value)
    if len(candidates) != 1:
        raise ValueError("The TV did not report a single usable developer identity")
    return hashlib.sha256(next(iter(candidates)).encode()).hexdigest()


def sync_directory(folder):
    if os.name == "posix":
        descriptor = os.open(folder, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(descriptor)
        finally: os.close(descriptor)


def snapshot(query):
    if query.get("readOnly") is not True or query.get("uid") != 901 or query.get("firmware") != FIRMWARE or query.get("target") != TARGET:
        raise ValueError("This native setup is not verified on this TV software")
    def read(item):
        if not isinstance(item, dict) or item.get("ok") is not True or "value" not in item:
            raise ValueError("A required original TV preference could not be read")
        return item["value"]
    home = {"Main": read(query.get("homeOperation")), "Strings": {k: read(query.get("keys", {}).get(k)) for k in KEYS}, "AutoStart": read(query.get("autostart"))}
    last = read(query.get("lastApp"))
    validate_home(home)
    if type(last) is not int or last not in (0, 1):
        raise ValueError("Unknown Last App preference")
    return home, last, read(query.get("bootSupported")) == 1


def validate_home(home):
    if not isinstance(home, dict) or set(home) != {"Main", "Strings", "AutoStart"} or not isinstance(home["Strings"], dict) or set(home["Strings"]) != set(KEYS):
        raise ValueError("Incomplete original Home snapshot")
    if type(home["AutoStart"]) is not int or home["AutoStart"] not in (0, 1) or any(not isinstance(v, str) or not APPID.fullmatch(v) for v in [home["Main"], *home["Strings"].values()]):
        raise ValueError("Invalid original Home snapshot")


def read_payload(folder):
    manifest = json.loads((folder / "payload.json").read_text())
    expected = {name + suffix for name in ("CleanHomeReadOnlyInspection", "CleanHomeNativeControl") for suffix in (".dll", ".runtimeconfig.json", ".deps.json")}
    if manifest.get("schema") != 1 or set(manifest.get("files", {})) != expected:
        raise ValueError("Rebuild the companion: native helper manifest is incomplete")
    files = {}
    for name, digest in manifest["files"].items():
        path = folder / name
        if path.is_symlink() or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("Invalid native helper package")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError("Native helper integrity check failed")
        files[name] = data
    if sum(map(len, files.values())) > 2 * 1024 * 1024:
        raise ValueError("Native helper payload too large")
    return files


class Store:
    def __init__(self, folder=None):
        if folder is None:
            base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local/share"))
            folder = base / "CleanHome" / "recovery"
        self.folder = Path(folder).resolve()
        if self.folder.is_relative_to(ROOT):
            raise ValueError("Recovery originals must be outside the source repository")
        self.folder.mkdir(mode=0o700, parents=True, exist_ok=True)
        if os.name == "posix":
            os.chmod(self.folder, 0o700)

    def path(self, binding, suffix):
        if not re.fullmatch(r"[a-f0-9]{64}", binding):
            raise ValueError("Invalid TV binding")
        path = self.folder / (binding + suffix)
        if path.is_symlink():
            raise ValueError("Recovery files must not be symbolic links")
        return path

    def original(self, binding):
        path = self.path(binding, ".original.json")
        if not path.exists():
            return None
        if path.stat().st_size > 8192:
            raise ValueError("Recovery original is too large")
        envelope = json.loads(path.read_text())
        record = envelope["original"]
        if hashlib.sha256(canonical(record)).hexdigest() != envelope["sha256"] or record.get("binding") != binding or record.get("model") != MODEL or record.get("firmware") != FIRMWARE or record.get("target") != TARGET or record.get("schema") != 1:
            raise ValueError("Recovery original is corrupt or belongs to another TV")
        validate_home(record["home"])
        if record["home"]["Main"] != SAMSUNG or record["home"]["Strings"][KEYS[0]] != SAMSUNG or type(record["lastApp"]) is not int or record["lastApp"] not in (0, 1):
            raise ValueError("Recovery file does not contain original Samsung Home settings")
        return record

    def save_original(self, binding, home, last):
        record = {"schema": 1, "binding": binding, "target": TARGET, "model": MODEL, "firmware": FIRMWARE, "home": home, "lastApp": last, "saved": int(time.time())}
        envelope = {"original": record, "sha256": hashlib.sha256(canonical(record)).hexdigest()}
        path = self.path(binding, ".original.json")
        # Exclusive creation: never replace an existing TV's originals.
        with path.open("xb") as output:
            os.chmod(path, 0o600)
            output.write(canonical(envelope))
            output.flush()
            os.fsync(output.fileno())
        sync_directory(self.folder)
        if self.original(binding) != record:
            raise ValueError("Recovery original readback failed")
        return record

    def status(self, binding, state=None):
        path = self.path(binding, ".status.json")
        if state is None:
            return json.loads(path.read_text()) if path.exists() else {"phase": "original"}
        temporary = self.path(binding, ".status.tmp")
        with temporary.open("wb") as output:
            os.chmod(temporary, 0o600)
            output.write(canonical(state))
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        sync_directory(self.folder)
        return state


class Transport:
    def __init__(self, host, files):
        self.host, self.files = private_ipv4(host), files
        self.connection = BoundedSdb(self.host)

    def __enter__(self):
        # Avoid environment proxies and redirects for LAN device identification.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args): return None
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        with opener.open("http://" + self.host + ":8001/api/v2/", timeout=5) as response:
            metadata = json.loads(response.read(65537))
        device = metadata.get("device", {})
        if device.get("modelName", device.get("model")) != MODEL:
            raise ValueError("This setup currently supports only the verified " + MODEL + " model")
        try:
            self.connection.connect(attempts=1)
            self.binding = device_binding(self.connection.shell_bounded("0 getduid", 8))
            return self
        except BaseException:
            self.connection.close()
            raise

    def __exit__(self, *args): self.connection.close()

    def run(self, action, original=None):
        files = dict(self.files)
        if action == "query":
            entry, args = "CleanHomeReadOnlyInspection.dll", ("--query",)
        elif action in ("apply-all", "restore-all") and original:
            entry = "CleanHomeNativeControl.dll"
            files["OriginalHome.json"] = canonical(original["home"])
            args = (action, "OriginalHome.json", str(original["lastApp"]))
        else:
            raise ValueError("Unsupported companion action")
        result = sdk.run(self.connection, files, entry, args)
        lines = [line for line in result["stdout"].splitlines() if line.startswith("{")]
        if len(lines) != 1:
            raise DeviceSessionError("Helper did not return one verifiable result; check before retrying")
        data = json.loads(lines[0])
        if result["exit_code"] != 0 or (action != "query" and data.get("Success") is not True):
            raise DeviceSessionError("Native setup refused or rolled back. Inspect the TV before trying again.")
        return data


class Companion:
    def __init__(self, store, files, transport=Transport):
        self.store, self.files, self.transport = store, files, transport

    def perform(self, host, action):
        if action not in ("inspect", "apply", "undo"):
            raise ValueError("Unknown setup action")
        with self.transport(private_ipv4(host), self.files) as tv:
            home, last, eligible = snapshot(tv.run("query"))
            original = self.store.original(tv.binding)
            status = self.store.status(tv.binding)
            baseline = home["Main"] == SAMSUNG and home["Strings"][KEYS[0]] == SAMSUNG
            active = eligible and home["Main"] == TARGET and home["Strings"][KEYS[0]] == TARGET and home["AutoStart"] == 1 and last == 0
            if active and original and home["Strings"][KEYS[-1]] != original["home"]["Strings"][KEYS[-1]]:
                active = False
            if action == "inspect":
                # Inspect reads preferences and stages temporary getter files only.
                return {"model": MODEL, "firmware": "1720.7", "supported": True, "installed": eligible, "active": active, "canApply": bool(eligible and baseline and status["phase"] not in ("pending", "unknown") and (not original or (home == original["home"] and last == original["lastApp"]))), "canUndo": bool(original), "recovery": str(self.store.folder), "phase": status["phase"]}
            if action == "apply":
                if active and original:
                    return {"success": True, "message": "Clean Home is already set up. No settings were changed."}
                if status["phase"] in ("pending", "unknown"):
                    raise ValueError("An earlier change was interrupted. Use Undo first; the saved originals are safe.")
                if not eligible or not baseline:
                    raise ValueError("Install Clean Home first. The TV must still use its original Samsung Home.")
                if original is None:
                    original = self.store.save_original(tv.binding, home, last)
                if home != original["home"] or last != original["lastApp"]:
                    raise ValueError("The TV's settings changed since its originals were saved. Setup stopped.")
            elif original is None:
                raise ValueError("No original settings for this TV were found on this computer. Do not uninstall Clean Home yet.")
            self.store.status(tv.binding, {"phase": "pending", "action": action})
            try:
                tv.run("apply-all" if action == "apply" else "restore-all", original)
                after, after_last, _ = snapshot(tv.run("query"))
                if action == "undo":
                    verified = after == original["home"] and after_last == original["lastApp"]
                else:
                    verified = after["Main"] == TARGET and after["Strings"][KEYS[0]] == TARGET and after["AutoStart"] == 1 and after_last == 0 and after["Strings"][KEYS[-1]] == original["home"]["Strings"][KEYS[-1]]
                if not verified:
                    raise ValueError("Readback did not confirm the result. Use Undo before any uninstall.")
            except BaseException:
                self.store.status(tv.binding, {"phase": "unknown", "action": action})
                raise
            self.store.status(tv.binding, {"phase": "active" if action == "apply" else "original"})
            return {"success": True, "message": "Clean Home now owns Home and power-on. Samsung Home remains available inside Clean Home." if action == "apply" else "Original Samsung Home and Last App settings restored. You can now uninstall Clean Home if you wish."}
