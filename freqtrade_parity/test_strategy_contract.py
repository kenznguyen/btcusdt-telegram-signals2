"""Static safety contract: no live entries, and informative H1 is declared."""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent
class StrategyContractTest(unittest.TestCase):
    def test_h1_is_declared_for_data_provider(self):
        source=(ROOT/"ChartProParityDryRun.py").read_text()
        self.assertIn("def informative_pairs(self):",source)
        self.assertIn('return [(pair, "1h") for pair in pairs]',source)
    def test_resolver_compatible_absolute_imports(self):
        source=(ROOT/"ChartProParityDryRun.py").read_text()
        self.assertIn("from freqtrade_parity.callbacks import PaperCallbackCore",source)
        self.assertIn("from freqtrade_parity.context import enrich_closed_m15",source)
        self.assertNotIn("from .callbacks import",source)
        self.assertNotIn("from .context import",source)
    def test_entries_remain_disabled(self):
        source=(ROOT/"ChartProParityDryRun.py").read_text()
        self.assertIn('dataframe["enter_long"]=0',source)
        self.assertIn('dataframe["enter_short"]=0',source)
        self.assertIn("return False",source)
        ast.parse(source)

if __name__=="__main__":unittest.main()
