"""Fail-closed common API adapter for the authoritative Core Bundle-v1 path."""

import os
import re
import tempfile
from pathlib import Path

import rfc8785

from core_runtime.continuous_cadence import latest_eligible_m15_open_ms
from core_runtime.runtime_factory import (
    build_continuous_runtime,
    build_core_bundle_provider,
)


class CoreApiFacadeError(RuntimeError):
    """Stable, credential-safe failure at the common Core API boundary."""


_REQUIRED_ENV = (
    "CORE_RUNTIME_CONFIG_PATH",
    "CORE_RUNTIME_JOURNAL_PATH",
    "CORE_RUNTIME_BUNDLE_STORE_DIR",
    "CORE_RUNTIME_SOURCE_SHA",
    "T0_CANDLE_API_BASE_URL",
    "T0_CANDLE_API_TOKEN",
    "T0_CANDLE_MAX_LAG_MS",
    "T1_ORDERBOOK_API_BASE_URL",
    "T1_ORDERBOOK_API_TOKEN",
)
_SOURCE_SHA = re.compile(r"[0-9a-f]{40}\Z")


def _runtime_options(environ):
    values = {}
    for key in _REQUIRED_ENV:
        value = environ.get(key)
        if not isinstance(value, str) or not value.strip():
            raise CoreApiFacadeError("CORE_RUNTIME_CONFIG_REQUIRED")
        values[key] = value.strip()
    if not _SOURCE_SHA.fullmatch(values["CORE_RUNTIME_SOURCE_SHA"]):
        raise CoreApiFacadeError("CORE_RUNTIME_SOURCE_SHA_INVALID")
    try:
        max_lag = int(values["T0_CANDLE_MAX_LAG_MS"], 10)
    except (TypeError, ValueError):
        raise CoreApiFacadeError("CORE_RUNTIME_T0_LAG_INVALID") from None
    if max_lag <= 0 or str(max_lag) != values["T0_CANDLE_MAX_LAG_MS"]:
        raise CoreApiFacadeError("CORE_RUNTIME_T0_LAG_INVALID")
    return values


def _runtime(now_ms, environ):
    if type(now_ms) is not int or now_ms < 0:
        raise CoreApiFacadeError("CORE_RUNTIME_TIMESTAMP_INVALID")
    env = os.environ if environ is None else environ
    if not hasattr(env, "get"):
        raise CoreApiFacadeError("CORE_RUNTIME_CONFIG_INVALID")
    values = _runtime_options(env)
    try:
        return build_continuous_runtime(
            config_path=values["CORE_RUNTIME_CONFIG_PATH"],
            journal_path=values["CORE_RUNTIME_JOURNAL_PATH"],
            bundle_store_dir=values["CORE_RUNTIME_BUNDLE_STORE_DIR"],
            source_sha=values["CORE_RUNTIME_SOURCE_SHA"],
            environ=env,
            clock_ms=lambda: now_ms,
        )
    except Exception:
        raise CoreApiFacadeError("CORE_RUNTIME_PREFLIGHT_FAILED") from None


def _bundle_path(runtime, now_ms):
    try:
        candle_open_ms = latest_eligible_m15_open_ms(
            now_ms, settlement_ms=0
        )
        return runtime.bundle_provider(candle_open_ms)
    except Exception:
        raise CoreApiFacadeError("CORE_BUNDLE_UNAVAILABLE") from None


def preview_core(*, now_ms, environ=None):
    """Validate a Bundle v1 preview without journal or durable bundle writes."""
    env = os.environ if environ is None else environ
    values = _runtime_options(env)
    if type(now_ms) is not int or now_ms < 0:
        raise CoreApiFacadeError("CORE_RUNTIME_TIMESTAMP_INVALID")
    try:
        provider = build_core_bundle_provider(
            config_path=values["CORE_RUNTIME_CONFIG_PATH"],
            journal_path=values["CORE_RUNTIME_JOURNAL_PATH"],
            bundle_store_dir=values["CORE_RUNTIME_BUNDLE_STORE_DIR"],
            environ=env,
            clock_ms=lambda: now_ms,
        )
        candle_open_ms = latest_eligible_m15_open_ms(
            now_ms, settlement_ms=0
        )
        bundle = provider(candle_open_ms, persist=False)
        if not isinstance(bundle, dict):
            raise CoreApiFacadeError("CORE_PREVIEW_BUNDLE_INVALID")
        from core_runtime.one_shot import run_once
        with tempfile.TemporaryDirectory(prefix="core-api-preview-") as directory:
            bundle_path = Path(directory) / "bundle.json"
            bundle_path.write_bytes(rfc8785.dumps(bundle))
            result = run_once(
                values["CORE_RUNTIME_CONFIG_PATH"],
                bundle_path,
                now_ms=now_ms,
                submit=False,
            )
    except CoreApiFacadeError:
        raise
    except Exception:
        raise CoreApiFacadeError("CORE_PREVIEW_FAILED") from None
    if not isinstance(result, dict):
        raise CoreApiFacadeError("CORE_PREVIEW_RESULT_INVALID")
    return result


def evaluate_core(*, now_ms, environ=None):
    """Recover and execute one authoritative, immutable Bundle-v1 Core cycle."""
    runtime = _runtime(now_ms, environ)
    try:
        recovered = runtime.runner.recover_incomplete(now_ms=now_ms)
    except Exception:
        raise CoreApiFacadeError("CORE_RECOVERY_FAILED") from None
    if not isinstance(recovered, list) or any(
        not isinstance(item, dict)
        or item.get("status") in {
            "BLOCKED", "FAILED", "UNKNOWN_REQUIRES_RECONCILIATION",
        }
        for item in recovered
    ):
        raise CoreApiFacadeError("CORE_RECOVERY_REQUIRES_RECONCILIATION")
    bundle_path = _bundle_path(runtime, now_ms)
    try:
        result = runtime.runner.process_bundle(
            bundle_path, now_ms=now_ms
        )
    except Exception:
        raise CoreApiFacadeError("CORE_CYCLE_FAILED") from None
    if not isinstance(result, dict):
        raise CoreApiFacadeError("CORE_CYCLE_RESULT_INVALID")
    return result
