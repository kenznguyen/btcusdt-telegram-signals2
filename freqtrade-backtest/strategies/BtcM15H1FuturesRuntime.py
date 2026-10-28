"""Isolated Freqtrade FUTURES 13x backtest adapter; no real trading.

ENTRY uses closed M15/H1 Android indicators. Exits use explicit Android
priority EMERGENCY_SL > SOFT_SL > TP. Freqtrade fills, wallet accounting,
callback timing and same-candle precedence still require independent parity
validation against the Kotlin engine; this is not parity-certified.
"""
import sys
from pathlib import Path
from datetime import timedelta

from freqtrade.strategy import IStrategy
from freqtrade.persistence import Trade
from freqtrade.enums import RunMode
from pandas import DataFrame, Timestamp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from entry_frame import entry_diagnostics
from android_signal_predicates import exit_reason, dca_signal, roe_for


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
        # Initial margin is 50% of free + allocated simulated account equity.
        # The API's available stake is not Android's settled-balance accounting.
        desired = float(self.config.get("dry_run_wallet", 100)) * 0.50
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
        reason = evaluate_exit(side, candle, previous, float(trade.open_rate))
        # Freqtrade custom_exit is an order at engine fill price, not the
        # intrabar stopFillPrice used by Android; reconcile after export.
        return reason.lower() if reason is not None else None

    def adjust_trade_position(self, trade: Trade, current_time, current_rate,
                              current_profit, min_stake, max_stake,
                              current_entry_rate, current_exit_rate,
                              current_entry_profit, current_exit_profit, **kwargs):
        if trade.nr_of_successful_entries != 1 or trade.has_open_orders:
            return None
        candle, previous = self._closed_rows(trade.pair, current_time)
        if candle is None or previous is None:
            return None
        side = "SHORT" if trade.is_short else "LONG"
        avg_entry = float(trade.open_rate)
        # Never DCA if Android would first exit in this same candle.
        if evaluate_exit(side, candle, previous, avg_entry) is not None:
            return None
        rsi = candle.get("android_rsi")
        prev_rsi = candle.get("android_prev_rsi")
        adx = candle.get("android_adx")
        if any(v is None for v in (rsi, prev_rsi, adx)):
            return None
        roe = roe_for(side, avg_entry, float(candle["close"]))
        if not dca_signal(side, roe, adx, rsi, prev_rsi):
            return None
        added_margin = float(trade.stake_amount)
        if added_margin <= 0 or max_stake < added_margin:
            return None
        return added_margin, "android_dca"
