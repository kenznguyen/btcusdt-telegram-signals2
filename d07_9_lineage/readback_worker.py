"""One-shot subprocess used for independent byte readback."""
from __future__ import annotations

import errno
import hashlib
import json
import os
import stat
import sys
from pathlib import Path


def readback(root_value: str, relative_value: str) -> dict:
    parts = relative_value.split("/")
    if (
        not relative_value or relative_value.startswith("/")
        or "\\" in relative_value
        or any(part in {"", ".", ".."} for part in parts)
        or (len(parts[0]) == 2 and parts[0][1] == ":")
    ):
        raise ValueError("UNSAFE_RELATIVE_PATH")

    root = Path(root_value).resolve(strict=True)
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    file_flags = os.O_RDONLY | os.O_NOFOLLOW
    root_fd = os.open(str(root), directory_flags)
    current_fd = root_fd
    file_fd = None
    try:
        for part in parts[:-1]:
            next_fd = os.open(part, directory_flags, dir_fd=current_fd)
            if current_fd != root_fd:
                os.close(current_fd)
            current_fd = next_fd
        file_fd = os.open(parts[-1], file_flags, dir_fd=current_fd)
        if not stat.S_ISREG(os.fstat(file_fd).st_mode):
            raise ValueError("EVIDENCE_TARGET_NOT_REGULAR_FILE")

        hasher = hashlib.sha256()
        byte_length = 0
        with os.fdopen(file_fd, "rb") as stream:
            file_fd = None
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                byte_length += len(chunk)
                hasher.update(chunk)
        return {"byteLength": byte_length, "sha256": hasher.hexdigest()}
    finally:
        if file_fd is not None:
            os.close(file_fd)
        if current_fd != root_fd:
            os.close(current_fd)
        os.close(root_fd)


def main() -> int:
    try:
        request = json.load(sys.stdin)
        result = readback(request["root"], request["path"])
        json.dump({"ok": True, **result}, sys.stdout, sort_keys=True)
        return 0
    except ValueError as exc:
        json.dump({"ok": False, "error": str(exc)}, sys.stdout, sort_keys=True)
        return 2
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            error = "SYMLINK_PATH_FORBIDDEN"
        elif exc.errno == errno.ENOTDIR:
            error = "EVIDENCE_TARGET_NOT_REGULAR_FILE"
        elif exc.errno == errno.ENOENT:
            error = "READBACK_TARGET_UNAVAILABLE"
        else:
            error = "READBACK_IO_ERROR"
        json.dump({"ok": False, "error": error}, sys.stdout, sort_keys=True)
        return 2
    except Exception:
        json.dump({"ok": False, "error": "READBACK_WORKER_FAILED"}, sys.stdout, sort_keys=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
