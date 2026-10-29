"""Start a local Docker trial, with optional one-pass candle loading and API verification."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import urlsplit

from data_lake.local_setup import DEFAULT_CONFIG, SECRET_KEYS, check_local, prepare_configuration


ROOT = Path(__file__).resolve().parents[1]
COMPOSE_FILE = ROOT / "deploy/data-lake/compose.yaml"
DOCKER_SELECTORS = ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH")


class TrialFailure(Exception):
    def __init__(self, reason):
        self.reason = reason


def _local_endpoint(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 4096 or any(ord(char) < 32 or ord(char) == 127 for char in value):
        return False
    try:
        parts = urlsplit(value)
    except ValueError:
        return False
    if parts.netloc or parts.query or parts.fragment:
        return False
    return ((value.startswith("unix://") and parts.scheme == "unix" and parts.path.startswith("/")) or
            (value.startswith("npipe://") and parts.scheme == "npipe" and parts.path.lower().startswith("//./pipe/")))


def _child_environment(source):
    result = dict(source)
    for key in (*DOCKER_SELECTORS, *SECRET_KEYS, "LAKE_API_PORT", "COMPOSE_PROFILES"):
        result.pop(key, None)
    return result


def _capture(arguments, environment, failure):
    try:
        result = subprocess.run(arguments, cwd=ROOT, env=environment, timeout=10,
                                capture_output=True, text=True, check=False)
    except (OSError, subprocess.SubprocessError):
        raise TrialFailure(failure) from None
    if result.returncode or len(result.stdout) > 4096:
        raise TrialFailure(failure)
    return result.stdout.strip()


def _docker_target(source, environment):
    # Docker's explicit context selector has priority over DOCKER_HOST.
    context = source.get("DOCKER_CONTEXT")
    host = source.get("DOCKER_HOST")
    if context or not host:
        context = context or _capture(["docker", "context", "show"], environment, "DOCKER_UNAVAILABLE")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", context):
            raise TrialFailure("INVALID_DOCKER_CONTEXT")
        raw = _capture(["docker", "--context", context, "context", "inspect", context,
                        "--format", "{{json .Endpoints.docker.Host}}"],
                       environment, "DOCKER_CONTEXT_UNAVAILABLE")
        try:
            endpoint = json.loads(raw)
        except ValueError:
            raise TrialFailure("INVALID_DOCKER_CONTEXT") from None
        prefix = ["docker", "--context", context]
    else:
        endpoint = host
        prefix = ["docker", "--host", host]
    if not _local_endpoint(endpoint):
        raise TrialFailure("LOCAL_DOCKER_REQUIRED")
    raw = _capture([*prefix, "info", "--format", "{{json .OSType}}"], environment, "DOCKER_UNAVAILABLE")
    try:
        operating_system = json.loads(raw)
    except ValueError:
        raise TrialFailure("DOCKER_UNAVAILABLE") from None
    if operating_system != "linux":
        raise TrialFailure("LINUX_CONTAINERS_REQUIRED")
    version = _capture([*prefix, "compose", "version", "--short"], environment, "COMPOSE_V2_REQUIRED")
    match = re.fullmatch(r"v?(\d+)\.\d+(?:[.\-+].*)?", version)
    if not match or int(match.group(1)) < 2:
        raise TrialFailure("COMPOSE_V2_REQUIRED")
    return prefix


def _docker_step(arguments, environment, failure, timeout, *, quiet=False):
    try:
        result = subprocess.run(arguments, cwd=ROOT, env=environment, timeout=timeout, text=True, check=False,
                                stdout=subprocess.DEVNULL if quiet else sys.stderr, stderr=sys.stderr)
    except subprocess.TimeoutExpired:
        raise TrialFailure(failure + "_TIMEOUT") from None
    except (OSError, subprocess.SubprocessError):
        raise TrialFailure(failure) from None
    if result.returncode:
        raise TrialFailure(failure)


def _wait_ready(config, seconds):
    deadline = time.monotonic() + seconds
    while True:
        status = check_local(config)
        if status.get("ready") is True:
            return status
        if status.get("reason") == "AUTH_FAILED":
            raise TrialFailure("LOCAL_API_AUTH_FAILED")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TrialFailure("LOCAL_API_READY_TIMEOUT")
        time.sleep(min(2, remaining))


def _verify(config, bars):
    from data_lake.local_verify import verify_local
    return verify_local(config, bars=bars)


def run_trial(config=DEFAULT_CONFIG, *, load_candles=False, bars=20, port=None,
              wait_seconds=120, project_name="chart-lake-local"):
    report = {"ok": False, "dataRequested": bool(load_candles)}
    try:
        if (type(load_candles) is not bool or type(bars) is not int or not 2 <= bars <= 2000 or
                type(wait_seconds) is not int or not 1 <= wait_seconds <= 300 or
                not isinstance(project_name, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,62}", project_name) or
                (port is not None and (type(port) is not int or not 1 <= port <= 65535))):
            raise TrialFailure("INVALID_TRIAL_OPTIONS")
        environment = _child_environment(os.environ)
        docker = _docker_target(os.environ, environment)
        config = Path(config).absolute()
        settings = prepare_configuration(config, port)
        report["apiUrl"] = "http://127.0.0.1:" + settings["LAKE_API_PORT"]
        compose = [*docker, "compose", "--project-name", project_name, "--env-file", str(config), "-f", str(COMPOSE_FILE)]
        _docker_step([*compose, "config", "--quiet"], environment, "COMPOSE_CONFIG_FAILED", 10, quiet=True)
        print("Starting the local PostgreSQL and API trial...", file=sys.stderr, flush=True)
        _docker_step([*compose, "up", "-d", "--build", "api"], environment, "COMPOSE_START_FAILED", 900)
        report["api"] = _wait_ready(config, wait_seconds)
        if load_candles:
            print("Loading one bounded candle window...", file=sys.stderr, flush=True)
            _docker_step([*compose, "run", "--rm", "collector", "refresh", "--bars", str(bars)],
                         environment, "COLLECTOR_REFRESH_FAILED", 300)
            report["api"] = check_local(config)
            if report["api"].get("ready") is not True:
                raise TrialFailure("LOCAL_API_NOT_READY_AFTER_REFRESH")
            report["verification"] = _verify(config, bars)
            if report["verification"].get("verified") is not True:
                raise TrialFailure("CANDLE_VERIFICATION_INCOMPLETE")
            if report["api"].get("freshData") is not True:
                raise TrialFailure("CANDLES_NOT_FRESH")
        report["ok"] = True
    except TrialFailure as error:
        report["reason"] = error.reason
    except KeyboardInterrupt:
        report["reason"] = "LOCAL_TRIAL_INTERRUPTED"
    except Exception:
        report["reason"] = "LOCAL_TRIAL_UNAVAILABLE_OR_INVALID"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--load-candles", action="store_true", help="Explicitly fetch one window, then verify it through the API")
    parser.add_argument("--bars", type=int, default=20)
    parser.add_argument("--port", type=int)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--wait-seconds", type=int, default=120, help="Readiness polling budget; each probe is bounded to five seconds")
    parser.add_argument("--project-name", default="chart-lake-local")
    args = parser.parse_args(argv)
    report = run_trial(args.config, load_candles=args.load_candles, bars=args.bars, port=args.port,
                       wait_seconds=args.wait_seconds, project_name=args.project_name)
    print(json.dumps(report, allow_nan=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
