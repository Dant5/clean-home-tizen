"""Bounded SDB transport for the optional Home companion; no root provider."""
import socket
import struct
import time
from .sdb import Sdb, SdbError, MAX_DATA, OPEN, OKAY, WRTE, CLSE


class DeviceSessionError(SdbError):
    pass


class BoundedSdb(Sdb):
    def __init__(self, host):
        super().__init__(host, timeout=5)
        self.deadline = None

    def _recv_exact(self, length):
        if length > MAX_DATA:
            raise DeviceSessionError("Unexpected developer packet size")
        data = bytearray()
        while len(data) < length:
            remaining = (self.deadline - time.monotonic()) if self.deadline else 5
            if remaining <= 0:
                raise DeviceSessionError("Developer operation timed out; do not retry changes blindly")
            self.sock.settimeout(min(5, remaining))
            chunk = self.sock.recv(length - len(data))
            if not chunk:
                raise DeviceSessionError("Developer connection closed")
            data.extend(chunk)
        return bytes(data)

    def _recv(self):
        cmd, arg0, arg1, length, checksum, magic = struct.unpack("<6I", self._recv_exact(24))
        if magic != cmd ^ 0xFFFFFFFF or length > MAX_DATA:
            raise DeviceSessionError("Invalid developer packet")
        payload = self._recv_exact(length) if length else b""
        if checksum != sum(payload) & 0xFFFFFFFF:
            raise DeviceSessionError("Developer packet checksum mismatch")
        return cmd, arg0, arg1, payload

    def service(self, name):
        local_id = self._next_id
        self._next_id += 1
        self._send(OPEN, local_id, 0, name.encode() + b"\0")
        output = bytearray()
        remote_id = None
        while True:
            cmd, arg0, arg1, payload = self._recv()
            if arg1 != local_id:
                continue
            if cmd == OKAY:
                remote_id = arg0
            elif cmd == WRTE:
                output.extend(payload)
                if len(output) > 131072:
                    raise DeviceSessionError("Developer output exceeds the allowed size")
                self._send(OKAY, local_id, arg0)
            elif cmd == CLSE:
                if remote_id is not None:
                    self._send(CLSE, local_id, arg0)
                return output.decode(errors="replace")

    def shell_bounded(self, command, seconds=30, limit=131072):
        # All companion callers supply fixed helper arguments, never user scripts.
        self.deadline = time.monotonic() + seconds
        try:
            output = self.shell(command)
            if len(output.encode()) > limit:
                raise DeviceSessionError("Developer output exceeds the allowed size")
            return output
        finally:
            self.deadline = None

    def push(self, data, path):
        self.deadline = time.monotonic() + 15
        try:
            return super().push(data, path)
        finally:
            self.deadline = None
