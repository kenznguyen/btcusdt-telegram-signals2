"""Pure callback regression: 50% dynamic wallet, no Freqtrade installation required."""
import ast
import math
import unittest
from pathlib import Path
from types import SimpleNamespace

STRATEGY = Path(__file__).resolve().parents[1] / "strategies" / "BtcM15H1FuturesRuntime.py"


def get_callback():
    tree = ast.parse(STRATEGY.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == "BtcM15H1FuturesRuntime")
    callback = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
                    and n.name == "custom_stake_amount")
    module = ast.fix_missing_locations(ast.Module(body=[callback], type_ignores=[]))
    namespace = {"math": math}
    exec(compile(module, str(STRATEGY), "exec"), namespace)
    return namespace["custom_stake_amount"]


class Wallet:
    def __init__(self, balance):
        self.balance = balance

    def get_total(self, currency):
        assert currency == "USDT"
        return self.balance


def invoke(balance, min_stake=1, max_stake=1000):
    obj = SimpleNamespace(
        wallets=Wallet(balance),
        config={"dry_run_wallet": 100, "stake_currency": "USDT"}
    )
    return get_callback()(obj, "BTC/USDT:USDT", None, 100, 50,
                          min_stake, max_stake, 13, None, "long")


class FuturesDynamicStakeTest(unittest.TestCase):
    def test_initial_wallet_100_uses_50(self):
        self.assertEqual(50, invoke(100))

    def test_wallet_down_to_80_uses_40(self):
        self.assertEqual(40, invoke(80))

    def test_wallet_up_to_120_uses_60(self):
        self.assertEqual(60, invoke(120))

    def test_wallet_not_enough_for_50_percent_returns_zero(self):
        self.assertEqual(0, invoke(100, max_stake=40))

    def test_below_exchange_minimum_returns_zero(self):
        self.assertEqual(0, invoke(80, min_stake=45))


if __name__ == "__main__":
    unittest.main()
