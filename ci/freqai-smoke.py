"""Native strategy-load smoke test; never starts training or an exchange client."""

import json
from pathlib import Path

from freqtrade.enums import RunMode
from freqtrade.resolvers import StrategyResolver

root = Path(__file__).resolve().parents[1]
config = json.loads((root / "freqai_bridge/config.research.json").read_text())
config.update(strategy="ChartProFreqaiResearch", strategy_path=str(root / "freqai_bridge"),
              freqaimodel="LightGBMRegressor", runmode=RunMode.DRY_RUN,
              user_data_dir=root / ".ci-tools/freqtrade-user-data")
config["user_data_dir"].mkdir(parents=True, exist_ok=True)
strategy = StrategyResolver.load_strategy(config)
assert strategy.__class__.__name__ == "ChartProFreqaiResearch"
assert strategy.INTERFACE_VERSION == 3
assert config["dry_run"] is True
assert strategy.confirm_trade_entry() is False
print("Freqtrade 2026.9 strategy loaded; native entry remains disabled")
