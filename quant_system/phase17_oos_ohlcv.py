"""Pure offline cross-timeframe OHLCV guard for the original frozen OOS.

Never fetches data, trains a model, mutates input candles, or certifies OOS.
read_closed_csv and verify_exact_closed_timebase remain responsible for
complete, closed and aligned individual timeframe series.
"""
from __future__ import annotations

import math


class OOSMarketIntegrityError(ValueError):
    """An OHLCV disagreement prevents any OOS prediction or paper replay."""


def _close(a: object, b: object) -> bool:
    try:
        a, b = float(a), float(b)
    except (ValueError, TypeError, OverflowError):
        return False
    return math.isfinite(a) and math.isfinite(b) and math.isclose(
        a, b, rel_tol=5e-8, abs_tol=1e-8)


def _verify_aggregation(big: list[dict], small: list[dict], ratio: int,
                        error: str) -> None:
    if ratio < 1 or len(small) != len(big) * ratio:
        raise OOSMarketIntegrityError(error)
    for i, bar in enumerate(big):
        chunk = small[i*ratio:(i+1)*ratio]
        if not chunk or bar.get('open_time') != chunk[0].get('open_time'):
            raise OOSMarketIntegrityError(error)
        try:
            checks = (
                _close(bar['open'], chunk[0]['open']),
                _close(bar['close'], chunk[-1]['close']),
                _close(bar['high'], max(float(x['high']) for x in chunk)),
                _close(bar['low'], min(float(x['low']) for x in chunk)),
                _close(bar['volume'], math.fsum(float(x['volume']) for x in chunk)),
            )
        except (KeyError, ValueError, TypeError, OverflowError) as exc:
            raise OOSMarketIntegrityError(error) from exc
        if not all(checks):
            raise OOSMarketIntegrityError(error)


def verify_oos_ohlcv_integrity(warm1h: list[dict], h1: list[dict],
                                warm15: list[dict], m15: list[dict],
                                fine5m: list[dict]) -> bool:
    """Validate holdout and the overlapping pre-holdout H1/M15 warmup.

    The first 68 H1 warmup candles have no corresponding M15 warmup
    by pre-registered protocol; only their final 32 hours overlap.
    Earlier independent candle provenance must be audited separately.
    """
    overlap = len(warm15) // 4
    if (not warm15 or len(warm15) % 4 != 0 or
            len(warm1h) < overlap):
        raise OOSMarketIntegrityError('OOS_PREHISTORY_H1_M15_INCONSISTENT')
    _verify_aggregation(warm1h[-overlap:], warm15, 4,
                        'OOS_PREHISTORY_H1_M15_INCONSISTENT')
    _verify_aggregation(h1, m15, 4,
                        'OOS_TIMEFRAME_OHLCV_INCONSISTENT')
    _verify_aggregation(m15, fine5m, 3,
                        'OOS_TIMEFRAME_OHLCV_INCONSISTENT')
    return True
