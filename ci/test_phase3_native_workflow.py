"""Codemagic regression: the install step must not use an unbound CI_PYTHON.

The installer writes CI_PYTHON to CM_ENV for *later* steps, not into the
currently running shell. A same-step command must export the path explicitly.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def sample_venue_manifest(exchange):
    import hashlib
    import json
    fields = {
        "exchange": exchange,
        "symbol": "BTC/USDT:USDT",
        "marketType": "USDT_PERPETUAL",
        "dataset_sha256": "sha256:" + "b" * 64,
        "detail_sha256": "sha256:" + "c" * 64,
    }
    digest = hashlib.sha256(json.dumps(
        fields, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    return {**fields, "provenance_sha256": "sha256:" + digest, "ohlcv_verified": True}


class Phase3NativeWorkflowTest(unittest.TestCase):
    def test_install_step_exports_python_before_invoking_it(self):
        yaml = (ROOT / "codemagic.yaml").read_text(encoding="utf-8")
        workflow = yaml.split("  dual-strategy-phase3-native-research:", 1)[1]
        install = workflow.split("      - name: Install pinned CPU Freqtrade and FreqAI runtime", 1)[1]
        install = install.split("      - name:", 1)[0]
        setup = 'bash ci/setup-python.sh requirements-freqai.txt requirements-market-data.txt'
        command = '"$CI_PYTHON" -m freqtrade --version'
        self.assertIn(setup, install)
        self.assertIn(command, install)
        self.assertIn('export CI_PYTHON="$CM_BUILD_DIR/.ci-tools/python-venv/bin/python"', install)
        self.assertLess(install.index(setup), install.index("export CI_PYTHON="))
        self.assertLess(install.index("export CI_PYTHON="), install.index(command))
        self.assertIn('test -x "$CI_PYTHON"', install)

    def test_download_uses_initialized_explicit_freqtrade_userdir(self):
        yaml = (ROOT / "codemagic.yaml").read_text(encoding="utf-8")
        workflow = yaml.split("  dual-strategy-phase3-native-research:", 1)[1]
        install = workflow.split("      - name: Install pinned CPU Freqtrade and FreqAI runtime", 1)[1]
        install = install.split("      - name:", 1)[0]
        download = workflow.split("      - name: Download genuine futures OHLCV plus exchange-managed funding and mark data", 1)[1]
        download = download.split("      - name:", 1)[0]
        userdir = '"$CM_BUILD_DIR/.ci-tools/phase3-freqtrade-userdata"'
        self.assertIn('freqtrade create-userdir --userdir ' + userdir, install)
        self.assertIn('--userdir ' + userdir, download)
        self.assertLess(
            install.index('freqtrade create-userdir'),
            install.index('test -d ' + userdir),
        )
        self.assertIn('test -d ' + userdir, install)

    def test_native_research_uses_same_explicit_userdir(self):
        yaml = (ROOT / "codemagic.yaml").read_text(encoding="utf-8")
        native = yaml.split("  dual-strategy-phase3-native-research:", 1)[1]
        research = native.split("      - name: Native Freqtrade and FreqAI research on the SAME audited candles", 1)[1]
        research = research.split("    artifacts:", 1)[0]
        self.assertIn('--userdir "$CM_BUILD_DIR/.ci-tools/phase3-freqtrade-userdata"', research)
        source = (ROOT / "quant_system/native_research.py").read_text(encoding="utf-8")
        self.assertIn('parser.add_argument("--userdir", required=True)', source)
        self.assertIn('userdir=args.userdir', source)

    def test_native_backtest_commands_share_initialized_directory(self):
        import json
        import tempfile
        from unittest.mock import patch
        from quant_system.native_research import research_commands

        with tempfile.TemporaryDirectory() as location:
            root = Path(location)
            userdir = root / "user-data"
            (root / "native-export-report.json").write_text(
                json.dumps(sample_venue_manifest("binance"))
            )
            with patch("quant_system.native_research.audit_history",
                       return_value={"ohlcv_verified": True, "start_ms": 1_700_000_040_000,
                                     "end_ms": 1_700_000_940_000,
                                     "dataset_sha256": "sha256:" + "b" * 64,
                                     "detail_sha256": "sha256:" + "c" * 64}), \
                 patch("quant_system.native_research.training_window",
                       return_value=(1_700_000_040_000, 1_700_000_940_000)):
                with self.assertRaisesRegex(ValueError, "MISSING_INITIALIZED_FREQTRADE_USERDIR"):
                    research_commands(
                        days=180, detail_minutes=5, dataset_dir=root,
                        native_datadir=root / "data", out_dir=root / "results",
                        userdir=userdir,
                    )
                (userdir / "strategies").mkdir(parents=True)
                audit, commands = research_commands(
                    days=180, detail_minutes=5, dataset_dir=root,
                    native_datadir=root / "data", out_dir=root / "results",
                    userdir=userdir,
                )
                self.assertEqual(len(commands), 2)
                for source, command in commands:
                    with self.subTest(source=source):
                        self.assertIn("--userdir", command)
                        self.assertEqual(command[command.index("--userdir")+1], str(userdir.resolve()))
                        self.assertIn("--timeframe-detail", command)
                        self.assertEqual(command[command.index("--timeframe-detail")+1], "5m")
                        self.assertEqual(command[command.index("--datadir")+1], str((root/"data").resolve()))
                        self.assertRegex(command[command.index("--timerange")+1],
                                         r"^\d{8}T\d{4}-\d{8}T\d{4}$")

    def test_research_provider_is_explicit_okx_and_not_binance(self):
        import json
        original = json.loads((ROOT / "freqai_bridge/config.research.json").read_text())
        config = json.loads((ROOT / "freqai_bridge/config.okx-research.json").read_text())
        self.assertEqual(original["exchange"]["name"], "binance")
        self.assertEqual(config["exchange"]["name"], "okx")
        self.assertEqual(config["exchange"]["pair_whitelist"], ["BTC/USDT:USDT"])
        self.assertEqual(config["trading_mode"], "futures")
        self.assertEqual(config["margin_mode"], "isolated")
        self.assertIs(config["dry_run"], True)
        self.assertIs(config["force_entry_enable"], False)
        self.assertNotEqual(
            config["freqai"]["identifier"], original["freqai"]["identifier"],
        )
        expected = dict(original)
        expected.pop("exchange")
        expected.pop("freqai")
        actual = dict(config)
        actual.pop("exchange")
        actual.pop("freqai")
        self.assertEqual(expected, actual)
        self.assertEqual(
            {k:v for k,v in original["freqai"].items() if k != "identifier"},
            {k:v for k,v in config["freqai"].items() if k != "identifier"},
        )

    def test_native_download_uses_okx_config_and_isolated_folder(self):
        yaml = (ROOT / "codemagic.yaml").read_text()
        native = yaml.split("  dual-strategy-phase3-native-research:", 1)[1]
        download = native.split(
            "      - name: Download genuine futures OHLCV plus exchange-managed funding and mark data",1
        )[1].split("      - name:",1)[0]
        self.assertIn("--config freqai_bridge/config.okx-research.json", download)
        self.assertIn("phase3-native-okx", download)
        self.assertNotIn("config.research.json", download)
        self.assertNotIn("phase3-native-binance", download)
        self.assertIn("--trading-mode futures", download)
        export = native.split(
            "      - name: Export exactly the native candles and audit 180 or 360 days",1
        )[1].split("      - name:",1)[0]
        self.assertIn("--exchange okx", export)
        research = native.split(
            "      - name: Native Freqtrade and FreqAI research on the SAME audited candles",1
        )[1].split("    artifacts:",1)[0]
        self.assertIn("--config-path freqai_bridge/config.okx-research.json", research)
        self.assertIn("--exchange okx", research)
        self.assertIn("phase3-native-okx", research)

    def test_native_commands_refuse_wrong_exchange_manifest(self):
        import json
        import tempfile
        from unittest.mock import patch
        from quant_system.native_research import research_commands
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "user-data" / "strategies").mkdir(parents=True)
            (root / "dataset").mkdir()
            report = root / "dataset" / "native-export-report.json"
            report.write_text(json.dumps(sample_venue_manifest("binance")))
            config = ROOT / "freqai_bridge/config.okx-research.json"
            with patch(
                "quant_system.native_research.audit_history",
                return_value={
                    "ohlcv_verified":True,"start_ms":1_700_000_040_000,
                    "end_ms":1_700_000_940_000,
                    "dataset_sha256":"sha256:"+"b"*64,
                    "detail_sha256":"sha256:"+"c"*64,
                },
            ), patch(
                "quant_system.native_research.training_window",
                return_value=(1_700_000_040_000,1_700_000_940_000),
            ):
                kwargs = dict(days=180, detail_minutes=5,
                    dataset_dir=root/"dataset",native_datadir=root/"native",
                    out_dir=root/"out", userdir=root/"user-data",
                    config_path=config, exchange="okx")
                with self.assertRaisesRegex(ValueError, "VENUE_MISMATCH"):
                    research_commands(**kwargs)
                report.write_text(json.dumps(sample_venue_manifest("okx")))
                manifest, commands = research_commands(**kwargs)
                self.assertEqual(len(commands),2)
                for _label, cmd in commands:
                    self.assertEqual(
                        cmd[cmd.index("--config")+1],str(config.resolve()),
                    )

    def test_installer_persists_python_for_following_steps(self):
        setup = (ROOT / "ci/setup-python.sh").read_text(encoding="utf-8")
        self.assertIn("printf 'CI_PYTHON=%s\\n' \"$ci_python\" >> \"$CM_ENV\"", setup)


if __name__ == "__main__":
    unittest.main()
