"""FreqAI prediction-only strategy: this strategy never requests native orders."""

import logging
import os
import time

from freqtrade.strategy import IStrategy
from pandas import DataFrame

from freqai_bridge.exporter import TARGET, make_prediction, read_context, write_artifact
from freqai_bridge.context import canonical_context

logger = logging.getLogger(__name__)


class ChartProFreqaiResearch(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = True
    process_only_new_candles = True
    startup_candle_count = 64
    stoploss = -0.05
    minimal_roi = {"0": 10}

    def feature_engineering_expand_all(self, dataframe: DataFrame, period: int, metadata: dict, **kwargs):
        if period < 2:
            raise ValueError("Indicator period must be at least two")
        dataframe["%-relative-price"] = dataframe["close"] / dataframe["close"].rolling(period).mean()-1
        dataframe["%-relative-volume"] = dataframe["volume"] / dataframe["volume"].rolling(period).mean()
        return dataframe

    def feature_engineering_expand_basic(self, dataframe: DataFrame, metadata: dict, **kwargs):
        dataframe["%-pct-change"] = dataframe["close"].pct_change()
        dataframe["%-raw-volume"] = dataframe["volume"]
        return dataframe

    def feature_engineering_standard(self, dataframe: DataFrame, metadata: dict, **kwargs):
        dataframe["%-day-of-week"] = dataframe["date"].dt.dayofweek
        dataframe["%-hour-of-day"] = dataframe["date"].dt.hour
        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, metadata: dict, **kwargs):
        horizon = self.freqai_info["feature_parameters"]["label_period_candles"]
        dataframe[TARGET] = dataframe["close"].shift(-horizon) / dataframe["close"]-1
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict):
        if self.config.get("dry_run") is not True or metadata.get("pair") != "BTC/USDT:USDT":
            raise ValueError("Chart Pro FreqAI is restricted to BTCUSDT research dry-run")
        self.freqai_info = self.config["freqai"]
        dataframe = self.freqai.start(dataframe, metadata, self)
        mode = getattr(self.config.get("runmode"), "value", self.config.get("runmode"))
        if mode == "dry_run":
            self._publish_prediction(dataframe)
        if mode == "backtest":
            destination = os.environ.get("PHASE3_PREDICTIONS_CSV")
            if destination:
                # Only serialize actual FreqAI dataframe predictions during a
                # guarded OFFLINE native backtest. Do not enable native entries.
                from quant_system.native_prediction_capture import capture_predictions
                captured = capture_predictions(
                    dataframe, destination,
                    self.config["freqai"]["identifier"], pair=metadata["pair"],
                )
                logger.info("Phase 3 native FreqAI captured %d observed rows", captured)
        return dataframe

    def _publish_prediction(self, dataframe):
        context = self.config.get("freqai_bridge", {})
        paths = (context.get("canonical_db_path"), context.get("provenance_path"), context.get("output_path"))
        if not all(isinstance(path, str) and path for path in paths):
            return
        observed = time.time_ns() // 1_000_000
        try:
            canonical = canonical_context(paths[0], observed, context.get("candle_window_bars", 2))
            provenance = read_context(paths[1])
            if provenance.get("freqaiIdentifier") != self.config["freqai"]["identifier"]:
                raise ValueError("Model identifier mismatch")
            artifact = make_prediction(dataframe, canonical, provenance, observed)
        except (KeyError, ValueError, TypeError, OSError, OverflowError):
            artifact = {"available": False, "source": "freqai", "availableAtMs": observed,
                        "reason": "PREDICTION_OR_PROVENANCE_UNAVAILABLE"}
            logger.warning("Chart Pro prediction unavailable; native order signals remain disabled")
        write_artifact(paths[2], artifact)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict):
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict):
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe

    def confirm_trade_entry(self, *args, **kwargs):
        return False
