"""Compare pre-normalized funding observations without asserting source independence.

This module is offline-only. It does not acquire, parse, authenticate, or persist
provider data. Both inputs must already be mapped to the strict comparison
contract documented in D07.7.
"""

from decimal import Decimal, InvalidOperation


_IDENTITY_FIELDS = (
    "venue",
    "instrument",
    "market_type",
    "contract_type",
    "margin_asset",
    "settlement_asset",
)


def _validate_observations(rows, expected_venue):
    if not isinstance(rows, (list, tuple)):
        raise ValueError("FUNDING_OBSERVATIONS_INVALID")
    normalized = {}
    identity = None

    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("FUNDING_OBSERVATION_INVALID")
        if any(key not in row for key in (*_IDENTITY_FIELDS, "funding_time_ms", "funding_rate")):
            raise ValueError("FUNDING_OBSERVATION_FIELDS_INVALID")

        current_identity = tuple(row[key] for key in _IDENTITY_FIELDS)
        if any(not isinstance(value, str) or not value.strip() for value in current_identity):
            raise ValueError("FUNDING_INSTRUMENT_INVALID")
        if current_identity[0] != expected_venue:
            raise ValueError("FUNDING_VENUE_MISMATCH")
        if identity is None:
            identity = current_identity
        elif current_identity != identity:
            raise ValueError("FUNDING_INSTRUMENT_MISMATCH")

        timestamp = row["funding_time_ms"]
        if type(timestamp) is not int or timestamp < 0:
            raise ValueError("FUNDING_TIMESTAMP_INVALID")
        if not isinstance(row["funding_rate"], str) or not row["funding_rate"].strip():
            raise ValueError("FUNDING_RATE_INVALID")
        try:
            rate = Decimal(row["funding_rate"])
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError("FUNDING_RATE_INVALID") from None
        if not rate.is_finite():
            raise ValueError("FUNDING_RATE_INVALID")
        if timestamp in normalized:
            raise ValueError("FUNDING_OBSERVATION_DUPLICATE")
        normalized[timestamp] = rate

    return identity, normalized


def compare_funding_observations(
    binance_observations,
    tardis_observations,
    *,
    shared_collector_lineage=False,
):
    """Compare Binance venue observations over their exact settlement overlap.

    tardis_observations is a caller-normalized offline fixture/input, not a
    Tardis file parser. A match corroborates values only within the supplied
    overlap; it does not prove issuer authenticity or population completeness.
    """
    if type(shared_collector_lineage) is not bool:
        raise ValueError("FUNDING_COLLECTOR_LINEAGE_INVALID")

    binance_identity, binance = _validate_observations(binance_observations, "BINANCE")
    tardis_identity, tardis = _validate_observations(tardis_observations, "BINANCE")

    if binance_identity is not None and tardis_identity is not None:
        if binance_identity != tardis_identity:
            raise ValueError("FUNDING_INSTRUMENT_MISMATCH")

    overlap = set(binance).intersection(tardis)
    mismatches = sum(binance[timestamp] != tardis[timestamp] for timestamp in overlap)
    unmatched_binance = len(set(binance) - overlap)
    unmatched_tardis = len(set(tardis) - overlap)

    if not overlap:
        corroboration = "NOT_VERIFIED_NO_OVERLAP"
    elif mismatches:
        corroboration = "MISMATCH"
    else:
        corroboration = "PASS_WITHIN_OVERLAP"

    return {
        "issuerIndependence": "NOT_VERIFIED_SAME_ISSUER",
        "collectorIndependence": (
            "BLOCKED_SHARED_COLLECTOR_LINEAGE"
            if shared_collector_lineage
            else "NOT_VERIFIED"
        ),
        "observationCorroboration": corroboration,
        "matchedCount": len(overlap),
        "mismatchCount": mismatches,
        "unmatchedBinanceCount": unmatched_binance,
        "unmatchedTardisCount": unmatched_tardis,
        "enumerationCompleteness": "NOT_VERIFIED",
        "globalCompleteness": "NOT_VERIFIED",
        "issuerAuthenticity": "NOT_VERIFIED",
        "freshness": "NOT_VERIFIED",
        "factualTruth": "NOT_VERIFIED",
    }
