"""Provenance-aware parity gate. Never certify matching synthetic traces as Kotlin parity."""
from quant_engine.parity import compare_traces


def verify_bundle(kotlin, python):
    failed = lambda reason: dict(parity_verified=False, reason=reason, compared_events=0)
    if not isinstance(kotlin, dict) or not isinstance(python, dict):
        return failed("MISSING_TRACE_BUNDLE")
    if kotlin.get("producer") != "KOTLIN" or python.get("producer") != "PYTHON":
        return failed("INVALID_PRODUCER")
    for item in (kotlin, python):
        if item.get("schema_version") != 1:
            return failed("UNSUPPORTED_SCHEMA")
        if item.get("closed_candles_only") is not True:
            return failed("OPEN_OR_UNVERIFIED_CANDLES")
        if not isinstance(item.get("engine_commit"), str) or not item["engine_commit"].strip():
            return failed("MISSING_ENGINE_COMMIT")
        digest = item.get("candle_sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            return failed("INVALID_CANDLE_DIGEST")
    if kotlin["candle_sha256"] != python["candle_sha256"]:
        return failed("CANDLE_CHECKSUM_MISMATCH")
    result = compare_traces(kotlin.get("events"), python.get("events"))
    return dict(parity_verified=result.parity_verified, reason=result.reason,
                compared_events=result.compared_events)
