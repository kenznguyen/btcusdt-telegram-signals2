"""Prepare private local Docker settings or check the authenticated localhost API."""

import argparse
import json
import os
from pathlib import Path
import re
import secrets
import stat
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

from data_lake.client import _NoRedirect


DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / ".data/local-lake.env"
SECRET_KEYS = ("LAKE_OWNER_PASSWORD", "LAKE_READER_PASSWORD", "LAKE_WRITER_PASSWORD", "LAKE_READ_TOKEN")


def read_configuration(path):
    path = Path(path)
    with os.fdopen(os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)), "r", encoding="ascii") as source:
        info = os.fstat(source.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > 2048:
            raise ValueError("INVALID_LOCAL_CONFIG")
        if os.name != "nt" and stat.S_IMODE(info.st_mode) & 0o077:
            raise ValueError("LOCAL_CONFIG_MUST_BE_PRIVATE")
        values = {}
        for line in source.read(2049).splitlines():
            if not line or line.startswith("#"):
                continue
            key, separator, value = line.partition("=")
            if not separator or key in values:
                raise ValueError("INVALID_LOCAL_CONFIG")
            values[key] = value
    if set(values) != set(SECRET_KEYS) | {"LAKE_API_PORT"}:
        raise ValueError("INVALID_LOCAL_CONFIG")
    if any(not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", values[key]) for key in SECRET_KEYS):
        raise ValueError("INVALID_LOCAL_SECRET")
    if len({values[key] for key in SECRET_KEYS}) != len(SECRET_KEYS):
        raise ValueError("LOCAL_SECRETS_MUST_BE_DISTINCT")
    port = values["LAKE_API_PORT"]
    if not port.isascii() or not port.isdigit() or not 1 <= int(port) <= 65535:
        raise ValueError("INVALID_LOCAL_PORT")
    return values


def prepare_configuration(path=DEFAULT_CONFIG, port=None):
    path = Path(path)
    if port is not None and (type(port) is not int or not 1 <= port <= 65535):
        raise ValueError("INVALID_LOCAL_PORT")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        values = read_configuration(path)
        if port is not None and int(values["LAKE_API_PORT"]) != port:
            raise ValueError("LOCAL_PORT_ALREADY_CONFIGURED")
        return values
    with os.fdopen(descriptor, "w", encoding="ascii") as output:
        output.write("# Local-only credentials. Keep this file private and retain it with the database volume.\n")
        for key in SECRET_KEYS:
            output.write(key + "=" + secrets.token_urlsafe(32) + "\n")
        output.write("LAKE_API_PORT=" + str(8788 if port is None else port) + "\n")
        output.flush()
        os.fsync(output.fileno())
    return read_configuration(path)


def check_local(path=DEFAULT_CONFIG):
    settings = read_configuration(path)
    url = "http://127.0.0.1:" + settings["LAKE_API_PORT"] + "/ready"
    request = Request(url, headers={"Authorization": "Bearer " + settings["LAKE_READ_TOKEN"],
                                    "Accept": "application/json"})
    try:
        # This probe only targets the literal loopback address, never a remote URL.
        with build_opener(ProxyHandler({}), _NoRedirect()).open(request, timeout=5) as response:
            if response.status != 200 or response.headers.get_content_type() != "application/json":
                raise ValueError("INVALID_READY_RESPONSE")
            raw = response.read(65_537)
        if len(raw) > 65_536:
            raise ValueError("INVALID_READY_RESPONSE")
        result = json.loads(raw)
        if (not isinstance(result, dict) or result.get("service") != "canonical-data-lake" or
                type(result.get("ready")) is not bool or type(result.get("freshData")) is not bool):
            raise ValueError("INVALID_READY_RESPONSE")
        return {"service": result["service"], "ready": result["ready"], "freshData": result["freshData"]}
    except HTTPError as error:
        error.close()
        return {"ready": False, "reason": "AUTH_FAILED" if error.code == 401 else "API_NOT_READY"}
    except (URLError, OSError):
        return {"ready": False, "reason": "LOCAL_API_UNAVAILABLE"}
    except (ValueError, TypeError, UnicodeError, RecursionError):
        return {"ready": False, "reason": "INVALID_READY_RESPONSE"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--port", type=int)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.check:
            result = check_local(args.config)
            print(json.dumps(result))
            return 0 if result["ready"] else 1
        settings = prepare_configuration(args.config, args.port)
        print(json.dumps({"configured": True, "configFile": str(args.config),
                          "apiUrl": "http://127.0.0.1:" + settings["LAKE_API_PORT"]}))
        return 0
    except (OSError, ValueError, UnicodeError):
        print(json.dumps({"ready": False, "reason": "LOCAL_CONFIG_UNAVAILABLE_OR_INVALID"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
