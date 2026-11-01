import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("legacy_runner", Path(__file__).with_name("run-legacy.py"))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class LegacyRunnerTest(unittest.TestCase):
    def test_invalid_task_and_parameters_never_execute(self):
        with patch.object(runner.subprocess, "run") as run:
            for mode, env in (("shell", {}), ("telegram", {"TELEGRAM_COMMAND": "$(touch x)"}),
                              ("dashboard", {"BACKTEST_DAYS": "0"}),
                              ("dashboard", {"BACKTEST_INITIAL_CAPITAL": "nan"}),
                              ("dashboard", {"DCA_MARGIN_RATIO": "501"}), ("scanner", {})):
                with self.subTest(mode=mode, env=env), self.assertRaises(ValueError):
                    runner.run_task(mode, env)
            run.assert_not_called()

    def test_percent_inputs_are_converted_without_boundary_ambiguity(self):
        default = runner.backtest_environment({})
        self.assertEqual(default["ENTRY_MARGIN_PCT"], "0.5")
        self.assertEqual(default["DCA_MARGIN_RATIO"], "1")
        small = runner.backtest_environment({"ENTRY_MARGIN_PCT": "1", "DCA_MARGIN_RATIO": "5"})
        self.assertEqual(small["ENTRY_MARGIN_PCT"], "0.01")
        self.assertEqual(small["DCA_MARGIN_RATIO"], "0.05")

    def test_scanner_uses_explicit_snapshot_and_emits_provenance(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runner.subprocess, "run") as run:
            env = {"LEGACY_STATE_JSON": '{"side":"LONG","qty":0.01,"avg_entry":100,"account_balance":100}', "CM_BUILD_ID": "build-1"}
            runner.run_task("scanner", env, directory)
            self.assertEqual(json.loads(Path(directory, "state.json").read_text())["side"], "LONG")
            provenance = json.loads(Path(directory, "state-provenance.json").read_text())
            self.assertEqual(provenance["mode"], "MANUAL_SNAPSHOT")
            self.assertEqual(provenance["buildId"], "build-1")
            self.assertEqual(len(provenance["inputSha256"]), 64)
            self.assertEqual(run.call_args.kwargs["env"]["BACKTEST_RUN_ID"], "build-1")
            self.assertTrue(run.call_args.args[0][-1].endswith("bot.py"))

    def test_invalid_state_is_not_written_or_executed(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runner.subprocess, "run") as run:
            for value in ('[]', '{}', '{"side":null}', '{"side":"UNKNOWN"}', '{"qty":NaN}', '{"side":"LONG","qty":1}',
                          '{"side":null,"qty":1}', '{"side":null,"qty":"0","avg_entry":0,"account_balance":100}',
                          'x'*1_048_577):
                with self.subTest(value=value[:30]), self.assertRaises(ValueError):
                    runner.run_task("scanner", {"LEGACY_STATE_JSON": value}, directory)
            self.assertFalse(Path(directory, "state.json").exists())
            run.assert_not_called()

    def test_telegram_help_uses_an_argument_list_and_no_shell(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runner.subprocess, "run") as run:
            runner.run_task("telegram", {"TELEGRAM_COMMAND": "help"}, directory)
            self.assertEqual(run.call_args.args[0][-1], "help")
            self.assertNotIn("shell", run.call_args.kwargs)

    def test_zero_exit_does_not_hide_failed_missing_or_stale_backtest_status(self):
        with tempfile.TemporaryDirectory() as directory:
            status_file = Path(directory, "backtest_status.json")
            env = {"TELEGRAM_COMMAND": "backtest", "CM_BUILD_ID": "build-1"}
            for status in (None, {"status": "failed", "run_id": "build-1"},
                           {"status": "completed", "run_id": "older-build"}):
                if status is not None:
                    status_file.write_text(json.dumps(status))
                with self.subTest(status=status), patch.object(runner.subprocess, "run"), self.assertRaises(RuntimeError):
                    runner.run_task("telegram", env, directory)
            status_file.write_text(json.dumps({"status": "completed", "run_id": "build-1"}))
            with patch.object(runner.subprocess, "run"):
                runner.run_task("telegram", env, directory)


if __name__ == "__main__":
    unittest.main()
