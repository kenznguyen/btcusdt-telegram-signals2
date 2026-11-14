"""One-shot subprocess used for independent byte readback."""
from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
from pathlib import Path, PurePosixPath


def readback(root_value: str, relative_value: str) -> dict:
    relative = PurePosixPath(relative_value)
    if relative.is_absolute() or not relative.parts or "\\" in relative_value:
        raise ValueError("UNSAFE_RELATIVE_PATH")
    if any(part in {"", ".", ".."} for part in relative.parts):
        raise ValueError("UNSAFE_RELATIVE_PATH")

    root = Path(root_value).resolve(strict=True)
    candidate = root
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError("SYMLINK_PATH_FORBIDDEN")

    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise ValueError("PATH_ESCAPES_EVIDENCE_ROOT")
    mode = resolved.stat().st_mode
    if not stat.S_ISREG(mode):
        raise ValueError("EVIDENCE_TARGET_NOT_REGULAR_FILE")

    hasher = hashlib.sha256()
    byte_length = 0
    with resolved.open("rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            byte_length += len(chunk)
            hasher.update(chunk)
    return {"byteLength": byte_length, "sha256": hasher.hexdigest()}


def main() -> int:
    try:
        request = json.load(sys.stdin)
        result = readback(request["root"], request["path"])
        json.dump({"ok": True, **result}, sys.stdout, sort_keys=True)
        return 0
    except Exception as exc:
        json.dump({"ok": False, "error": str(exc)}, sys.stdout, sort_keys=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
