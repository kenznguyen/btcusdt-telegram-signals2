import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile


SPEC = importlib.util.spec_from_file_location(
    "verify_five_layer_android_apk",
    Path(__file__).with_name("verify-five-layer-android-apk.py"),
)
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)

SOURCE = "a" * 40
CERTIFICATE = "b" * 64


class FiveLayerApkVerificationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "android-source-sha.txt").write_text(SOURCE + "\n")
        self.apk = self.root / "android-app/app/build/outputs/apk/debug/app-debug.apk"
        self.apk.parent.mkdir(parents=True)
        self.dex = b"five-layer-paper-only"
        self.write_apk()
        self.wrong_package = False
        self.wrong_label = False
        self.chart_pro_dex = False
        self.chart_pro_manifest = False
        self.chart_pro_permission = False
        self.signing_failure = False
        self.stale_source = False

    def write_apk(self):
        with zipfile.ZipFile(self.apk, "w") as archive:
            archive.writestr("classes.dex", self.dex)

    def tool_output(self, command, **kwargs):
        self.assertTrue(kwargs["text"])
        name = Path(command[0]).name
        if name == "git":
            return ("c" if self.stale_source else SOURCE) + "\n"
        if name == "aapt" and command[1:3] == ["dump", "badging"]:
            package = "com.wrong.app" if self.wrong_package else VERIFY.EXPECTED_PACKAGE
            label = "BTCUSDT Chart Pro" if self.wrong_label else VERIFY.EXPECTED_LABEL
            return (
                f"package: name='{package}' versionCode='2' versionName='0.2.0'\n"
                f"application-label:'{label}'\n"
                f"launchable-activity: name='{VERIFY.EXPECTED_ACTIVITY}' label='{label}'\n"
            )
        if name == "aapt" and command[1:3] == ["dump", "permissions"]:
            return "uses-permission: name='android.permission.INTERNET'\n" + (
                "uses-permission: name='android.permission.FOREGROUND_SERVICE'\n"
                if self.chart_pro_permission else ""
            )
        if name == "aapt" and command[1:3] == ["dump", "xmltree"]:
            return "E: manifest\n  E: application\n    E: activity\n" + (
                "    E: service (StrategyMonitorService)\n" if self.chart_pro_manifest else ""
            )
        self.assertEqual("apksigner", name)
        if self.signing_failure:
            raise subprocess.CalledProcessError(1, command)
        return f"Verifies\nSigner #1 certificate SHA-256 digest: {CERTIFICATE}\n"

    def run_gate(self):
        with patch.object(VERIFY.subprocess, "check_output", side_effect=self.tool_output):
            return VERIFY.verify_apk(self.root, self.root / "sdk")

    def test_publishes_single_verified_five_layer_apk(self):
        report = self.run_gate()
        self.assertEqual(SOURCE, report["sourceSha"])
        self.assertEqual(VERIFY.EXPECTED_PACKAGE, report["apk"]["package"])
        self.assertEqual([CERTIFICATE], report["apk"]["certificateSha256"])
        self.assertEqual(self.apk.read_bytes(), (self.root / report["apk"]["artifact"]).read_bytes())
        self.assertEqual(report, json.loads((self.root / "android-apk.json").read_text()))

    def test_rejects_chart_pro_dex_payload(self):
        self.dex = b"payload:CompleteDashboard"
        self.write_apk()
        with self.assertRaisesRegex(ValueError, "DEX"):
            self.run_gate()
        self.assertFalse((self.root / "android-apk.json").exists())

    def test_rejects_chart_pro_manifest_or_permissions(self):
        for attr in ("chart_pro_manifest", "chart_pro_permission"):
            with self.subTest(attr=attr):
                setattr(self, attr, True)
                with self.assertRaises(ValueError):
                    self.run_gate()
                self.assertFalse((self.root / "android-apk.json").exists())
                setattr(self, attr, False)

    def test_rejects_wrong_package_or_label(self):
        for attr in ("wrong_package", "wrong_label"):
            with self.subTest(attr=attr):
                setattr(self, attr, True)
                with self.assertRaises(ValueError):
                    self.run_gate()
                self.assertFalse((self.root / "android-apk.json").exists())
                setattr(self, attr, False)

    def test_rejects_unsigned_or_stale_source_apk(self):
        self.signing_failure = True
        with self.assertRaises(subprocess.CalledProcessError):
            self.run_gate()
        self.signing_failure = False
        self.stale_source = True
        with self.assertRaisesRegex(ValueError, "source SHA"):
            self.run_gate()
        self.assertFalse((self.root / "android-apk.json").exists())


if __name__ == "__main__":
    unittest.main()
