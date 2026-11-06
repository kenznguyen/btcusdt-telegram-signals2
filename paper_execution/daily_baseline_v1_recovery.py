"""Pure, read-only assessment of evidence for legacy daily baseline v1 recovery.

This module never opens a database, writes data, upgrades an audit, or authorizes
migration. A positive result means manual review may begin, not that migration
or risk admission is approved.
"""
from collections.abc import Mapping
from decimal import Decimal, DecimalException

DAY_MS = 86_400_000
LEDGER_IDS = ("STRATEGY_CORE", "AI_FREQAI", "LEGACY_UNATTRIBUTED")


def _mapping(value):
    return value if isinstance(value, Mapping) else {}


def _positive_amount(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 256:
        return False
    try:
        amount = Decimal(value)
    except (DecimalException, TypeError, ValueError):
        return False
    return amount.is_finite() and amount > 0


def _digest(value):
    return (
        isinstance(value, str) and len(value) == 71
        and value.startswith("sha256:")
        and all(char in "0123456789abcdef" for char in value[7:])
    )


def _timestamp(value):
    return type(value) is int and value >= 0


def assess_daily_baseline_v1_recovery_manifest(manifest):
    """Return BLOCKED or ELIGIBLE_FOR_MANUAL_REVIEW without mutating input."""
    missing = set()
    contradictions = set()
    root = _mapping(manifest)

    sections = {}
    for name in (
        "baseline", "audit", "cutover", "execution", "funding", "mark",
        "risk_state",
    ):
        value = root.get(name)
        if not isinstance(value, Mapping):
            missing.add(f"{name}.section")
            sections[name] = {}
        else:
            sections[name] = value

    baseline = sections["baseline"]
    audit = sections["audit"]
    cutover = sections["cutover"]
    execution = sections["execution"]
    funding = sections["funding"]
    mark = sections["mark"]
    risk = sections["risk_state"]

    for name in ("baseline_id", "mark_id", "cutover_id", "algorithm_version"):
        if not isinstance(baseline.get(name), str) or not baseline[name].strip():
            missing.add(f"baseline.{name}")
    boundary = baseline.get("utc_day_ms")
    if not _timestamp(boundary) or boundary % DAY_MS:
        contradictions.add("baseline.utc_day_ms is not a UTC day boundary")
    equity = baseline.get("equity_quote")
    if not _positive_amount(equity):
        missing.add("baseline.equity_quote")
    baseline_digest = baseline.get("replay_digest")
    if not _digest(baseline_digest):
        missing.add("baseline.replay_digest")

    for name in ("audit_id", "event_type", "replay_digest", "replay_equity_quote",
                 "mark_id", "cutover_id", "algorithm_version"):
        if not isinstance(audit.get(name), str) or not audit[name].strip():
            missing.add(f"audit.{name}")
    if audit.get("event_type") != "DAILY_BASELINE_CREATED":
        missing.add("audit.event_type")
    for name in ("canonical", "digest_verified"):
        if audit.get(name) is not True:
            missing.add(f"audit.{name}")
    if not _digest(audit.get("replay_digest")):
        missing.add("audit.replay_digest")
    if baseline_digest and audit.get("replay_digest") and baseline_digest != audit["replay_digest"]:
        contradictions.add("audit.replay_digest != baseline.replay_digest")
    if equity and audit.get("replay_equity_quote") and equity != audit["replay_equity_quote"]:
        contradictions.add("audit.replay_equity_quote != baseline.equity_quote")
    if baseline.get("mark_id") and audit.get("mark_id") and baseline["mark_id"] != audit["mark_id"]:
        contradictions.add("audit.mark_id != baseline.mark_id")
    if baseline.get("cutover_id") and audit.get("cutover_id") and baseline["cutover_id"] != audit["cutover_id"]:
        contradictions.add("audit.cutover_id != baseline.cutover_id")
    if baseline.get("algorithm_version") and audit.get("algorithm_version") and baseline["algorithm_version"] != audit["algorithm_version"]:
        contradictions.add("audit.algorithm_version != baseline.algorithm_version")

    for name in ("cutover_id",):
        if not isinstance(cutover.get(name), str) or not cutover[name].strip():
            missing.add(f"cutover.{name}")
    for name in ("verified", "immutable"):
        if cutover.get(name) is not True:
            missing.add(f"cutover.{name}")
    cutover_at = cutover.get("cutover_at_ms")
    if not _timestamp(cutover_at):
        missing.add("cutover.cutover_at_ms")
    elif _timestamp(boundary) and cutover_at >= boundary:
        contradictions.add("cutover.cutover_at_ms must precede baseline.utc_day_ms")
    if baseline.get("cutover_id") and cutover.get("cutover_id") and baseline["cutover_id"] != cutover["cutover_id"]:
        contradictions.add("cutover.cutover_id != baseline.cutover_id")
    snapshots = _mapping(cutover.get("ledger_snapshots"))
    for ledger_id in LEDGER_IDS:
        if snapshots.get(ledger_id) is not True:
            missing.add(f"cutover.ledger_snapshots.{ledger_id}")

    for section_name, section in (("execution", execution), ("funding", funding)):
        if section.get("status") != "VERIFIED":
            missing.add(f"{section_name}.status")
        start = section.get("start_at_ms")
        end = section.get("end_at_ms")
        if not _timestamp(start):
            missing.add(f"{section_name}.start_at_ms")
        if not _timestamp(end):
            missing.add(f"{section_name}.end_at_ms")
        if _timestamp(cutover_at) and _timestamp(start) and start != cutover_at:
            contradictions.add(f"{section_name}.start_at_ms != cutover.cutover_at_ms")
        if _timestamp(boundary) and _timestamp(end) and end != boundary:
            contradictions.add(f"{section_name}.end_at_ms != baseline.utc_day_ms")

    for name in ("all_events_provenanced", "all_fees_explicit_usdt",
                 "no_late_events", "all_ledgers_complete"):
        if execution.get(name) is not True:
            missing.add(f"execution.{name}")
    for name in ("all_events_provenanced", "no_unknown_amounts"):
        if funding.get(name) is not True:
            missing.add(f"funding.{name}")

    if mark.get("verified") is not True:
        missing.add("mark.verified")
    if not isinstance(mark.get("mark_id"), str) or not mark["mark_id"].strip():
        missing.add("mark.mark_id")
    elif baseline.get("mark_id") and mark["mark_id"] != baseline["mark_id"]:
        contradictions.add("mark.mark_id != baseline.mark_id")
    if mark.get("effective_at_ms") != boundary or not _timestamp(mark.get("effective_at_ms")):
        contradictions.add("mark.effective_at_ms != baseline.utc_day_ms")
    for name in ("source_snapshot_id", "dataset_version"):
        if not isinstance(mark.get(name), str) or not mark[name].strip():
            missing.add(f"mark.{name}")
    if not _digest(mark.get("payload_hash")):
        missing.add("mark.payload_hash")
    if mark.get("raw_payload_bytes_rehashed") is not True:
        missing.add("mark.raw_payload_bytes_rehashed")

    if risk.get("independently_verified") is not True:
        missing.add("risk_state.independently_verified")
    if risk.get("utc_day_ms") != boundary or not _timestamp(risk.get("utc_day_ms")):
        contradictions.add("risk_state.utc_day_ms != baseline.utc_day_ms")
    if risk.get("equity_quote") != equity or not _positive_amount(risk.get("equity_quote")):
        contradictions.add("risk_state.equity_quote != baseline.equity_quote")
    hwm = risk.get("high_water_mark_quote")
    if not _positive_amount(hwm):
        missing.add("risk_state.high_water_mark_quote")
    elif risk.get("risk_ready") is True and _positive_amount(equity) and Decimal(hwm) < Decimal(equity):
        contradictions.add("risk_state.high_water_mark_quote < baseline.equity_quote")
    version = risk.get("version")
    if type(version) is not int or version < 1:
        missing.add("risk_state.version")
    if type(risk.get("risk_ready")) is not bool:
        missing.add("risk_state.risk_ready")
    if not isinstance(risk.get("mark_id"), str) or not risk["mark_id"].strip():
        missing.add("risk_state.mark_id")
    elif mark.get("mark_id") and risk["mark_id"] != mark["mark_id"]:
        contradictions.add("risk_state.mark_id != mark.mark_id")
    for name in ("source_snapshot_id",):
        if not isinstance(risk.get(name), str) or not risk[name].strip():
            missing.add(f"risk_state.{name}")
    if not _digest(risk.get("payload_hash")):
        missing.add("risk_state.payload_hash")
    if risk.get("raw_payload_bytes_rehashed") is not True:
        missing.add("risk_state.raw_payload_bytes_rehashed")

    blocked = bool(missing or contradictions)
    return {
        "status": "BLOCKED" if blocked else "ELIGIBLE_FOR_MANUAL_REVIEW",
        "eligible_for_manual_review": not blocked,
        "migration_authorized": False,
        "automatic_upgrade_authorized": False,
        "mutation_performed": False,
        "missing_evidence": sorted(missing),
        "contradictions": sorted(contradictions),
    }
