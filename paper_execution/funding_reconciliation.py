"""Deterministic D07 funding population reconciliation.

This module compares two caller-supplied, bounded populations. It does not
authenticate either issuer, prove that the populations are truly independent,
or establish global completeness/freshness.
"""

from collections import Counter
from decimal import Decimal, DecimalException
import hashlib
import json
import re


_POPULATION_FIELDS = {
    "schemaVersion", "populationType", "populationDefinitionId",
    "snapshotId", "source", "startAtMs", "endAtMs", "currency", "events",
}
_EVENT_FIELDS = {"eventId", "eventAtMs", "amountQuote", "payloadHash"}
_HASH = re.compile(r"^sha256:[0-9a-f]{64}$")


def _text(value, code, limit=200):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(code)
    return value


def _timestamp(value, code):
    if type(value) is not int or value < 0:
        raise ValueError(code)
    return value


def _population(document, expected_type):
    if not isinstance(document, dict) or set(document) != _POPULATION_FIELDS:
        raise ValueError("FUNDING_POPULATION_FIELDS_INVALID")
    if type(document["schemaVersion"]) is not int or document["schemaVersion"] != 1:
        raise ValueError("FUNDING_POPULATION_VERSION_INVALID")
    if document["populationType"] != expected_type:
        raise ValueError("FUNDING_POPULATION_TYPE_INVALID")
    definition_id = _text(
        document["populationDefinitionId"], "FUNDING_POPULATION_DEFINITION_INVALID"
    )
    snapshot_id = _text(document["snapshotId"], "FUNDING_POPULATION_SNAPSHOT_INVALID")
    source = _text(document["source"], "FUNDING_POPULATION_SOURCE_INVALID")
    start = _timestamp(document["startAtMs"], "FUNDING_POPULATION_START_INVALID")
    end = _timestamp(document["endAtMs"], "FUNDING_POPULATION_END_INVALID")
    if start >= end:
        raise ValueError("FUNDING_POPULATION_INTERVAL_INVALID")
    currency = _text(document["currency"], "FUNDING_POPULATION_CURRENCY_INVALID", 16)
    events = document["events"]
    if not isinstance(events, list):
        raise ValueError("FUNDING_POPULATION_EVENTS_INVALID")

    normalized = []
    for item in events:
        if not isinstance(item, dict) or set(item) != _EVENT_FIELDS:
            raise ValueError("FUNDING_EVENT_FIELDS_INVALID")
        event_id = _text(item["eventId"], "FUNDING_EVENT_ID_INVALID")
        at_ms = _timestamp(item["eventAtMs"], "FUNDING_EVENT_TIMESTAMP_INVALID")
        if not start <= at_ms < end:
            raise ValueError("FUNDING_EVENT_OUTSIDE_SCOPE")
        try:
            amount = Decimal(str(item["amountQuote"]))
        except (DecimalException, TypeError, ValueError):
            raise ValueError("FUNDING_EVENT_AMOUNT_INVALID") from None
        if not amount.is_finite():
            raise ValueError("FUNDING_EVENT_AMOUNT_INVALID")
        digest = item["payloadHash"]
        if not isinstance(digest, str) or not _HASH.fullmatch(digest):
            raise ValueError("FUNDING_EVENT_PAYLOAD_HASH_INVALID")
        normalized.append({
            "eventId": event_id,
            "eventAtMs": at_ms,
            "amountQuote": format(amount, "f"),
            "payloadHash": digest,
        })

    return {
        "populationDefinitionId": definition_id,
        "snapshotId": snapshot_id,
        "source": source,
        "startAtMs": start,
        "endAtMs": end,
        "currency": currency,
        "events": normalized,
    }


def reconcile_funding_population(expected_document, observed_document):
    """Reconcile independent-by-declaration event inventories without I/O."""
    expected = _population(expected_document, "EXPECTED_FUNDING_EVENTS")
    observed = _population(observed_document, "OBSERVED_FUNDING_EVENTS")

    if expected["populationDefinitionId"] == observed["populationDefinitionId"]:
        raise ValueError("FUNDING_POPULATION_DEFINITION_NOT_INDEPENDENT")
    if expected["snapshotId"] == observed["snapshotId"] or expected["source"] == observed["source"]:
        raise ValueError("FUNDING_POPULATION_SOURCE_NOT_DISTINCT")
    scope = ("startAtMs", "endAtMs", "currency")
    if any(expected[key] != observed[key] for key in scope):
        raise ValueError("FUNDING_POPULATION_SCOPE_MISMATCH")

    def duplicates(events):
        ids = Counter(event["eventId"] for event in events)
        hashes = Counter(event["payloadHash"] for event in events)
        return sorted({
            event["eventId"] for event in events
            if ids[event["eventId"]] > 1 or hashes[event["payloadHash"]] > 1
        })

    duplicate_ids = sorted(set(duplicates(expected["events"]) + duplicates(observed["events"])))
    expected_dupes = set(duplicates(expected["events"]))
    observed_dupes = set(duplicates(observed["events"]))
    expected_unique = {
        item["eventId"]: item for item in expected["events"]
        if item["eventId"] not in expected_dupes
    }
    observed_unique = {
        item["eventId"]: item for item in observed["events"]
        if item["eventId"] not in observed_dupes
    }

    matched = []
    missing = []
    unexpected = []
    for event_id, item in expected_unique.items():
        actual = observed_unique.get(event_id)
        if actual is None:
            missing.append(event_id)
        elif actual == item:
            matched.append(event_id)
        else:
            missing.append(event_id)
            unexpected.append(event_id)
    for event_id in observed_unique:
        if event_id not in expected_unique:
            unexpected.append(event_id)

    matched.sort()
    missing = sorted(set(missing))
    unexpected = sorted(set(unexpected))
    complete = not (missing or unexpected or duplicate_ids)

    canonical = json.dumps(
        {"expected": expected, "observed": observed},
        sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    reconciliation_id = "sha256:" + hashlib.sha256(canonical).hexdigest()

    return {
        "schemaVersion": 1,
        "reconciliationId": reconciliation_id,
        "reconciliationStatus": (
            "COMPLETE_WITHIN_DECLARED_POPULATION" if complete else "BLOCKED"
        ),
        "scope": {
            "startAtMs": expected["startAtMs"],
            "endAtMs": expected["endAtMs"],
            "currency": expected["currency"],
        },
        "expectedSnapshotId": expected["snapshotId"],
        "observedSnapshotId": observed["snapshotId"],
        "counts": {
            "expected": len(expected["events"]),
            "observed": len(observed["events"]),
            "matched": len(matched),
            "missing": len(missing),
            "unexpected": len(unexpected),
            "duplicate": len(duplicate_ids),
        },
        "matched": matched,
        "missing": missing,
        "unexpected": unexpected,
        "duplicate": duplicate_ids,
        "independence": "DECLARED_NOT_VERIFIED",
        "globalCompleteness": "NOT_VERIFIED",
        "freshness": "NOT_VERIFIED",
        "issuerAuthenticity": "NOT_VERIFIED",
    }
