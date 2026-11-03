import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "verify_android_release_pair",
    Path(__file__).with_name("verify-android-release-pair.py"),
)
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)

SOURCE = "a" * 40
CERTIFICATE = "b" * 64


class AndroidReleasePairVerificationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sdk = self.root / "sdk"
        tools = self.sdk / "build-tools" / "34.0.0"
        tools.mkdir(parents=True)
        (tools / "aapt").touch()
        (tools / "apksigner").touch()
        for variant, _, _, filename in VERIFY.VARIANTS:
            apk = self.root / "android-app/app/build/outputs/apk" / variant / filename
            apk.parent.mkdir(parents=True, exist_ok=True)
            apk.write_bytes(("fixture-" + variant).encode())
        self.wrong_package = False
        self.wrong_version = False
        self.different_certificate = False
        self.missing_certificate = False
        self.ambiguous_metadata = False

    def tool_output(self, command, **kwargs):
        self.assertTrue(kwargs["text"])
        if command[:5] == ["git", "-C", str(self.root), "rev-parse", "HEAD"]:
            return SOURCE + "\n"
        apk_path = Path(command[-1])
        parallel = apk_path.name == "app-parallel.apk"
        if Path(command[0]).name == "aapt":
            package = VERIFY.BASE_PACKAGE + (
                ".paper" if parallel and not self.wrong_package else ""
            )
            label = "BTC 5 Tầng Paper" if parallel else "BTCUSDT Chart Pro"
            version = "0.2.0" + ("-paper" if parallel and not self.wrong_version else "")
            output = (
                f"package: name='{package}' versionCode='2' versionName='{version}'\n"
                f"application-label:'{label}'\n"
                f"launchable-activity: name='{VERIFY.EXPECTED_ACTIVITY}' label='{label}'\n"
            )
            return output + output if self.ambiguous_metadata else output
        self.assertEqual("apksigner", Path(command[0]).name)
        if self.missing_certificate:
            return "Verifies\n"
        digest = "c" * 64 if parallel and self.different_certificate else CERTIFICATE
        return f"Verifies\nSigner #1 certificate SHA-256 digest: {digest}\n"

    def run_gate(self, source=SOURCE):
        with patch.object(VERIFY.subprocess, "check_output", side_effect=self.tool_output):
            return VERIFY.verify_pair(self.root, self.sdk, source)

    def test_release_pair_requires_same_signer_and_records_source_and_hashes(self):
        result = self.run_gate()
        self.assertEqual(SOURCE, result["sourceSha"])
        self.assertEqual("RELEASE", result["signing"])
        self.assertTrue(result["signerParity"])
        self.assertEqual([CERTIFICATE], result["apks"][0]["certificateSha256"])
        self.assertEqual([CERTIFICATE], result["apks"][1]["certificateSha256"])
        self.assertEqual(64, len(result["apks"][0]["sha256"]))
        self.assertEqual(64, len(result["apks"][1]["sha256"]))

    def test_mismatched_signer_is_rejected(self):
        self.different_certificate = True
        with self.assertRaisesRegex(ValueError, "certificates differ"):
            self.run_gate()

    def test_wrong_package_or_version_is_rejected(self):
        for flag in ("wrong_package", "wrong_version"):
            with self.subTest(flag=flag):
                setattr(self, flag, True)
                with self.assertRaises(ValueError):
                    self.run_gate()
                setattr(self, flag, False)

    def test_missing_signer_or_ambiguous_badging_is_rejected(self):
        self.missing_certificate = True
        with self.assertRaisesRegex(ValueError, "digest is missing"):
            self.run_gate()
        self.missing_certificate = False
        self.ambiguous_metadata = True
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            self.run_gate()

    def test_source_sha_must_be_exact_and_match_checkout(self):
        with self.assertRaisesRegex(ValueError, "full 40-character"):
            self.run_gate("not-a-sha")
        with self.assertRaisesRegex(ValueError, "does not match"):
            self.run_gate("c" * 40)


if __name__ == "__main__":
    unittest.main()
