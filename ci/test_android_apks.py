import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("verify_android_apks", Path(__file__).with_name("verify-android-apks.py"))
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)
SOURCE = "a" * 40
CERTIFICATE = "b" * 64


class AndroidApkVerificationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "android-source-sha.txt").write_text(SOURCE + "\n")
        for variant in ("debug", "parallel"):
            apk = self.root / "android-app/app/build/outputs/apk" / variant / f"app-{variant}.apk"
            apk.parent.mkdir(parents=True)
            apk.write_bytes(("fixture-" + variant).encode())
        self.wrong_package = False
        self.wrong_version = False
        self.signing_failure = False
        self.different_certificate = False

    def tool_output(self, command, **kwargs):
        self.assertTrue(kwargs["text"])
        if command[0] == "git":
            return SOURCE + "\n"
        parallel = command[-1].endswith("app-parallel.apk")
        if Path(command[0]).name == "aapt":
            package = VERIFY.BASE_PACKAGE + (".paper" if parallel and not self.wrong_package else "")
            label = "BTC 5 Tầng Paper" if parallel else "BTCUSDT Chart Pro"
            version = "0.2.0" + ("-paper" if parallel and not self.wrong_version else "")
            return (f"package: name='{package}' versionCode='2' versionName='{version}' platformBuildVersionName='15'\n"
                    f"application-label:'{label}'\nlaunchable-activity: name='{VERIFY.BASE_PACKAGE}.MainActivity' label='{label}'\n")
        self.assertEqual("apksigner", Path(command[0]).name)
        self.assertEqual(["verify", "--verbose", "--print-certs"], command[1:4])
        if self.signing_failure:
            raise subprocess.CalledProcessError(1, command)
        certificate = "c" * 64 if parallel and self.different_certificate else CERTIFICATE
        return f"Verifies\nSigner #1 certificate SHA-256 digest: {certificate}\n"

    def run_gate(self):
        with patch.object(VERIFY.subprocess, "check_output", side_effect=self.tool_output):
            return VERIFY.verify_apks(self.root, self.root / "sdk")

    def test_verified_artifact_has_distinct_identity_source_hash_and_identical_bytes(self):
        report = self.run_gate()
        self.assertEqual(SOURCE, report["sourceSha"])
        parallel = report["apks"][1]
        self.assertEqual(VERIFY.BASE_PACKAGE + ".paper", parallel["package"])
        self.assertEqual([CERTIFICATE], parallel["certificateSha256"])
        self.assertEqual(b"fixture-parallel", (self.root / parallel["artifact"]).read_bytes())
        self.assertEqual(64, len(parallel["sha256"]))
        self.assertEqual(report, json.loads((self.root / "android-apks.json").read_text()))

    def test_wrong_package_or_version_never_publishes_verified_copy(self):
        for flag in ("wrong_package", "wrong_version", "different_certificate"):
            with self.subTest(flag=flag):
                setattr(self, flag, True)
                with self.assertRaises(ValueError):
                    self.run_gate()
                self.assertFalse((self.root / "android-apks.json").exists())
                self.assertFalse(list((self.root / "artifacts").glob("*.apk")))
                setattr(self, flag, False)

    def test_unsigned_apk_or_stale_checkout_fails(self):
        self.signing_failure = True
        with self.assertRaises(subprocess.CalledProcessError):
            self.run_gate()
        self.signing_failure = False
        self.run_gate()
        (self.root / "android-source-sha.txt").write_text("d" * 40)
        with self.assertRaises(ValueError):
            self.run_gate()
        self.assertFalse((self.root / "android-apks.json").exists())
        self.assertFalse(list((self.root / "artifacts").glob("*.apk")))

    def test_missing_or_ambiguous_badging_is_rejected(self):
        with self.assertRaises(ValueError):
            VERIFY.badging("package: name='wrong'\n")
        output = self.tool_output(["aapt", "dump", "badging", "app-parallel.apk"], text=True)
        with self.assertRaises(ValueError):
            VERIFY.badging(output + output)


if __name__ == "__main__":
    unittest.main()
