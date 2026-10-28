"""Actual Freqtrade BACKTEST-only ENTRY diagnostic adapter.

This is a separate, incomplete LONG-only SPOT diagnostic strategy; it does not
replace BtcM15H1ParityGate or claim 13x futures/DCA/TP/SL parity.
Never deploy this adapter for live or dry-run execution.
"""
import sys
from pathlib import Path

from freqtrade.strategy import IStrategy
from pandas import DataFrame

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from entry_frame import entry_diagnostics


class BtcM15H1EntryRuntime(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False
    process_only_new_candles = True
    startup_candle_count = 120
    minimal_roi = {"0": 0.05}  # Diagnostic exit only; NOT Android RSI TP.
    stoploss = -0.20  # Diagnostic risk cap only; NOT Android soft/emergency SL.
    use_exit_signal = False
    trailing_stop = False

    def informative_pairs(self):
        # Pair metadata is provided by the Freqtrade runtime during backtesting.
        return [(pair, "1h") for pair in self.dp.current_whitelist()] if self.dp else []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        if self.dp is None:
            raise RuntimeError("Real Freqtrade DataProvider required")
        h1 = self.dp.get_pair_dataframe(pair=metadata["pair"], timeframe="1h")
        if h1 is None or h1.empty:
            raise ValueError("Missing closed H1 OHLCV; refusing unfiltered entries")
        return entry_diagnostics(dataframe, h1)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = dataframe["android_entry_long"].fillna(0).astype(int)
        dataframe["enter_short"] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # No Android exit parity yet. Diagnostic ROI/stoploss in config above.
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe
