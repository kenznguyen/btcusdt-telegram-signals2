"""Contract for 180-day paper replay, held-out FreqAI capture, and no live orders."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class Phase3PaperWorkflowTest(unittest.TestCase):
    def test_freqai_native_research_captures_real_prediction_rows(self):
        strategy=(ROOT/'freqai_bridge/ChartProFreqaiResearch.py').read_text()
        self.assertIn('PHASE3_PREDICTIONS_CSV',strategy)
        self.assertIn('capture_predictions(',strategy)
        self.assertIn('"backtest"',strategy)
        self.assertIn('dataframe["enter_long"] = 0',strategy)
        self.assertIn('dataframe["enter_short"] = 0',strategy)
        self.assertIn('return False',strategy)

    def test_native_runner_exports_real_freqai_capture(self):
        script=(ROOT/'quant_system/native_research.py').read_text()
        self.assertIn('PHASE3_PREDICTIONS_CSV',script)
        self.assertIn('freqai-native-predictions.csv',script)
        self.assertIn('prediction_capture_sha256',script)
        self.assertIn('NO_NATIVE_FREQAI_PREDICTIONS',script)

    def test_paper_mode_only_180_days_and_never_exchange_orders(self):
        code=(ROOT/'quant_system/paper_backtest.py').read_text()
        self.assertIn("choices=[180]",code)
        self.assertIn('full_core_parity_certified',code)
        self.assertIn('actual_fill_price',code)
        self.assertIn('expected_fill_price',code)
        self.assertIn('fill_difference',code)
        for token in ('ccxt.create_order','exchange.create_order','create_order(', 'ccxt.binance'):
            self.assertNotIn(token,code)

    def test_codemagic_gates_paper_after_native_and_publishes_csv(self):
        workflow=(ROOT/'codemagic.yaml').read_text().split('  dual-strategy-phase3-native-research:',1)[1]
        self.assertIn('quant_system.paper_backtest',workflow)
        self.assertIn('--days 180',workflow)
        self.assertIn('artifacts/phase3/paper/*.csv',workflow)
        self.assertIn('artifacts/phase3/native/freqai-native-predictions.csv',workflow)
        self.assertLess(workflow.index('quant_system.native_research'),workflow.index('quant_system.paper_backtest'))
        self.assertIn('PHASE3_DAYS',workflow)
        self.assertIn('requires completed 180-day',workflow)

if __name__=='__main__':unittest.main()