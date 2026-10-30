"""When a native research subprocess fails, preserve useful evidence.

No actual Freqtrade/FreqAI runtime is needed: this test simulates an exit-2
failure and asserts that its log survives in both the report and Codemagic.
"""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from quant_system.native_research import run_research


class NativeResearchFailureTest(TestCase):
    def test_core_exit_2_exposes_log_tail_without_claiming_ai_or_parity(self):
        with TemporaryDirectory() as location:
            root = Path(location)
            output = root / "research"
            command = ["python", "-m", "freqtrade", "backtesting"]
            calls = []

            def fake_run(args, stdout=None, **kwargs):
                calls.append(args)
                stdout.write("FREQTRADE_CORE_ERROR: strategy resolution failed\\n")
                return SimpleNamespace(returncode=2)

            buffer = StringIO()
            with patch(
                "quant_system.native_research.research_commands",
                return_value=(
                    {"dataset_sha256": "sha256:" + "a"*64,
                     "detail_sha256": "sha256:" + "b"*64},
                    [("core", command), ("freqai", command)],
                ),
            ), patch(
                "quant_system.native_research.subprocess.run",
                side_effect=fake_run,
            ), redirect_stdout(buffer):
                report = run_research(
                    days=180, detail_minutes=5, dataset_dir=root,
                    native_datadir=root, out_dir=output,
                    userdir=root, config_path=root / "config.json", exchange="okx",
                )

            self.assertEqual(len(calls), 1)
            self.assertEqual(report["core_native_exit_code"], 2)
            self.assertFalse(report["core_native_runtime_succeeded"])
            self.assertFalse(report["freqai_native_runtime_succeeded"])
            self.assertFalse(report["native_trade_parity_verified"])
            self.assertFalse(report["full_core_parity_certified"])
            self.assertIn("FREQTRADE_CORE_ERROR", report["failure_log_tail"])
            self.assertEqual(report["failure_source"], "core")
            self.assertIn("FREQTRADE_CORE_ERROR", buffer.getvalue())
            self.assertIn("core-native-180.log", report["failure_log_path"])
            self.assertTrue((output / "core-native-180.log").exists())
            written = json.loads((output / "native-research-180.json").read_text())
            self.assertEqual(written["core_native_exit_code"], 2)
            self.assertIn("FREQTRADE_CORE_ERROR", written["failure_log_tail"])

    def test_log_tail_is_bounded(self):
        from quant_system.native_research import native_failure_excerpt
        with TemporaryDirectory() as location:
            path = Path(location) / "native.log"
            path.write_text("".join(f"line:{i}\\n" for i in range(200)))
            tail = native_failure_excerpt(path, max_lines=20)
            self.assertNotIn("line:0\\n", tail)
            self.assertIn("line:199", tail)
            self.assertLessEqual(len(tail.splitlines()), 20)


if __name__ == "__main__":
    import unittest
    unittest.main()
