"""Load native Freqtrade strategy without creating exchange, trades or models."""
import json
from pathlib import Path
from freqtrade.enums import RunMode
from freqtrade.resolvers import StrategyResolver

root=Path(__file__).resolve().parents[1]
config=json.loads((root/"freqai_bridge/config.research.json").read_text())
config["freqai"]["enabled"]=False
config.update(strategy="ChartProParityDryRun",strategy_path=str(root/"freqtrade_parity"),
              runmode=RunMode.DRY_RUN,user_data_dir=root/".ci-tools/freqtrade-user-data")
config["user_data_dir"].mkdir(parents=True,exist_ok=True)
assert config["dry_run"] is True
assert config["trading_mode"]=="futures"
strategy=StrategyResolver.load_strategy(config)
assert strategy.__class__.__name__=="ChartProParityDryRun"
assert strategy.INTERFACE_VERSION==3
assert strategy.can_short is True
assert strategy.confirm_trade_entry() is False
assert strategy.position_adjustment_enable is True
assert strategy.max_entry_position_adjustment==1
assert callable(strategy.adjust_trade_position)
assert callable(strategy.custom_exit)
assert callable(strategy.informative_pairs)
print("PASS: guarded Freqtrade strategy loads; native entries stay disabled")
