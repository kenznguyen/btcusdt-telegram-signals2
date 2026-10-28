"""Isolated Freqtrade FUTURES 13x backtest adapter; no real trading.

ENTRY uses closed M15/H1 Android indicators. Exits use explicit Android
priority EMERGENCY_SL > SOFT_SL > TP. Freqtrade fills, wallet accounting,
callback timing and same-candle precedence still require independent parity
validation against the Kotlin engine; this is not parity-certified.
"""
import sys
import os
import json
import math
from pathlib import Path
from datetime import timedelta

from freqtrade.strategy import IStrategy
from freqtrade.persistence import Trade
from freqtrade.enums import RunMode
from pandas import DataFrame, Timestamp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from entry_frame import entry_diagnostics
from android_signal_predicates import (exit_reason, dca_signal, roe_for,
                                       threshold_price, stop_fill_price)


def evaluate_exit(side, candle, previous, avg_entry):
    """Single source of truth for priority, used by runtime and offline tests."""
    if not previous:
        previous = candle
    rsi = candle.get("android_rsi")
    roe = roe_for(side, avg_entry, float(candle["close"]))
    return exit_reason(
        side, float(candle["low"]), float(candle["high"]),
        float(candle["open"]), float(candle["close"]),
        float(previous["open"]), float(previous["close"]),
        candle.get("android_h1_plus_di"), candle.get("android_h1_minus_di"),
        candle.get("android_h1_adx"), avg_entry, rsi, roe
    )


def dca_diagnosis(side, candle, previous, avg_entry, entry_count, has_open_orders,
                  stake, max_stake):
    """Explain why the Freqtrade DCA callback did or did not propose an order."""
    result = {
        "reason": None, "dca_candidate": False, "roe_pct": None,
        "rsi": candle.get("android_rsi") if candle else None,
        "adx": candle.get("android_adx") if candle else None,
        "previous_rsi": candle.get("android_prev_rsi") if candle else None,
        "proposed_stake": float(stake),
        "max_stake": float(max_stake),
    }
    if entry_count != 1 or has_open_orders:
        result["reason"] = "position_already_adjusted_or_open_order"
    elif candle is None or previous is None:
        result["reason"] = "missing_closed_candles"
    elif evaluate_exit(side, candle, previous, avg_entry) is not None:
        result["reason"] = "exit_has_priority"
    elif any(v is None or not math.isfinite(float(v)) for v in (
        result["rsi"], result["adx"], result["previous_rsi"]
    )):
        result["reason"] = "indicator_not_ready"
    else:
        roe = roe_for(side, avg_entry, float(candle["close"]))
        result["roe_pct"] = roe
        result["dca_candidate"] = dca_signal(
            side, roe, result["adx"], result["rsi"], result["previous_rsi"]
        )
        if not result["dca_candidate"]:
            if roe > -20.0:
                result["reason"] = "roe_not_below_minus_20"
            elif result["adx"] <= 45.0:
                result["reason"] = "adx_not_above_45"
            else:
                result["reason"] = "rsi_direction_filter_not_met"
        elif stake <= 0 or max_stake < stake:
            result["reason"] = "insufficient_free_stake"
        else:
            result["reason"] = "dca_proposed"
    return result


def write_dca_trace(trace_file, record):
    """Append diagnostics only when opt-in path is supplied by CI."""
    if not trace_file:
        return
    with open(trace_file, "a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, allow_nan=False, default=str) + "\n")


class BtcM15H1FuturesRuntime(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = True
    process_only_new_candles = True
    startup_candle_count = 120
    minimal_roi = {"0": 1000}
    stoploss = -0.99
    use_exit_signal = True
    trailing_stop = False
    position_adjustment_enable = True
    max_entry_position_adjustment = 1

    def bot_start(self, **kwargs):
        if self.config.get("runmode") != RunMode.BACKTEST:
            raise RuntimeError("Futures parity adapter is BACKTEST-ONLY")
        if self.config.get("trading_mode") != "futures":
            raise RuntimeError("Requires futures trading_mode")

    def informative_pairs(self):
        return [(pair, "1h") for pair in self.dp.current_whitelist()] if self.dp else []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        if self.dp is None:
            raise RuntimeError("Freqtrade DataProvider missing")
        h1 = self.dp.get_pair_dataframe(metadata["pair"], "1h")
        if h1 is None or h1.empty:
            raise ValueError("H1 data unavailable")
        return entry_diagnostics(dataframe, h1)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = dataframe["android_entry_long"].fillna(0).astype(int)
        dataframe["enter_short"] = dataframe["android_entry_short"].fillna(0).astype(int)
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe

    def leverage(self, pair, current_time, current_rate, proposed_leverage,
                 max_leverage, entry_tag, side, **kwargs):
        if max_leverage < 13.0:
            raise ValueError("13x unavailable: do not silently change leverage")
        return 13.0

    def custom_stake_amount(self, pair, current_time, current_rate,
                            proposed_stake, min_stake, max_stake,
                            leverage, entry_tag, side, **kwargs):
        # Target 50% of dynamic simulated wallet value, not initial capital.
        # Wallet accounting may still differ from Android settled balance.
        if self.wallets is None:
            return 0.0
        # In Freqtrade backtesting, wallet total in callbacks reflects
        # realized balance and allocated stake; it is NOT assumed static.
        balance = float(self.wallets.get_total(self.config.get("stake_currency", "USDT")))
        if not math.isfinite(balance) or balance <= 0:
            return 0.0
        desired = balance * 0.50
        if max_stake < desired or (min_stake is not None and desired < min_stake):
            return 0.0
        return desired

    def _closed_rows(self, pair, current_time):
        """Use only fully closed M15 candle(s); avoid future candle access."""
        if self.dp is None:
            return None, None
        frame, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if frame is None or frame.empty:
            return None, None
        cutoff = Timestamp(current_time) - timedelta(minutes=15)
        eligible = frame.loc[frame["date"] <= cutoff]
        if eligible.empty:
            return None, None
        current = eligible.iloc[-1].to_dict()
        previous = eligible.iloc[-2].to_dict() if len(eligible) > 1 else None
        return current, previous

    def custom_exit(self, pair, trade: Trade, current_time, current_rate,
                    current_profit, **kwargs):
        candle, previous = self._closed_rows(pair, current_time)
        if candle is None:
            return None
        side = "SHORT" if trade.is_short else "LONG"
        avg_entry = float(trade.open_rate)
        reason = evaluate_exit(side, candle, previous, avg_entry)
        if reason is not None:
            abs_roe = 90.0 if reason == "EMERGENCY_SL" else 35.0 if reason == "SOFT_SL" else None
            threshold = threshold_price(side, avg_entry, abs_roe) if abs_roe else None
            android_stop_fill = stop_fill_price(side, threshold, float(candle["open"])) if threshold else None
            write_dca_trace(os.environ.get("FREQTRADE_EXIT_TRACE"), {
                "callback_time": current_time,
                "closed_candle_time": candle.get("date"),
                "pair": pair, "side": side, "reason": reason,
                "candle_open": float(candle["open"]), "candle_high": float(candle["high"]),
                "candle_low": float(candle["low"]), "candle_close": float(candle["close"]),
                "trade_avg_entry": avg_entry,
                "android_stop_threshold": threshold,
                "android_expected_stop_fill": android_stop_fill,
                "freqtrade_callback_rate": float(current_rate),
                "note": "Expected price is diagnostic only; actual Freqtrade fill is in exported trade JSON."
            })
        # A custom_exit return requests a Freqtrade fill, not an Android
        # intrabar stop order. Do not label this as fill-level parity.
        return reason.lower() if reason is not None else None

    def adjust_trade_position(self, trade: Trade, current_time, current_rate,
                              current_profit, min_stake, max_stake,
                              current_entry_rate, current_exit_rate,
                              current_entry_profit, current_exit_profit, **kwargs):
        candle, previous = self._closed_rows(trade.pair, current_time)
        side = "SHORT" if trade.is_short else "LONG"
        proposed_margin = float(trade.stake_amount)
        result = dca_diagnosis(
            side, candle, previous, float(trade.open_rate),
            trade.nr_of_successful_entries, trade.has_open_orders,
            proposed_margin, max_stake
        )
        write_dca_trace(os.environ.get("FREQTRADE_DCA_TRACE"), {
            "callback_time": current_time,
            "closed_candle_time": candle.get("date") if candle else None,
            "pair": trade.pair,
            "side": side,
            "position_entries": trade.nr_of_successful_entries,
            "rate": float(current_rate),
            **result,
        })
        if result["reason"] == "dca_proposed":
            return proposed_margin, "android_dca"
        return None
