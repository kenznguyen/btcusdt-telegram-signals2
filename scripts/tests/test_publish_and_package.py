"""Offline tests for Codemagic packaging and GitHub publisher safety."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

publisher = load("publisher", "publish_codemagic_release.py")
packager = load("packager", "package_codemagic_outputs.py")


class ReleasePublishTests(unittest.TestCase):
    def test_no_secret_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            file = Path(d) / "a.json";file.write_text("{}")
            with self.assertRaisesRegex(ValueError, "GH_RELEASE_TOKEN"):
                publisher.publish("kenznguyen/btcusdt-telegram-signals2",
                                  "freqai", "abcdef123456", "build-1", "", [str(file)])

    def test_required_asset_must_exist(self):
        with self.assertRaises(FileNotFoundError):
            publisher.inspect_assets(["/missing/build.zip"])

    def test_publish_records_checksum(self):
        with tempfile.TemporaryDirectory() as d:
            file = Path(d) / "a.json";file.write_text("{}")
            def fake_api(url, token, method="GET", body=None, content_type=None):
                if url.endswith("/releases"):
                    return {"upload_url":"https://uploads.github.com/something{?name,label}",
                            "html_url":"https://github.com/test/release"}
                return {"state":"uploaded","browser_download_url":"https://github.com/test/asset"}
            with patch.object(publisher, "github_api", side_effect=fake_api):
                result = publisher.publish("kenznguyen/btcusdt-telegram-signals2",
                                           "freqai", "abcdef123456", "build_1",
                                           "test-token", [str(file)])
            self.assertTrue(result["github_release_publish_verified"])
            self.assertEqual(publisher.sha256(file),result["assets"][0]["sha256"])

    def test_packaging_does_not_include_config(self):
        from zipfile import ZipFile
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            results = root / "freqai-research-results";results.mkdir()
            for name in ("run-manifest.json","freqai-research-report.json",
                         "freqai-research-predictions.csv"):
                (results/name).write_text("sample")
            (root/"config-with-secret.json").write_text("should never be included")
            output = root / "freqai.zip"
            packager.create_bundle("freqai",root,output)
            with ZipFile(output) as file:
                self.assertEqual(len(file.namelist()),3)
                self.assertTrue(all("config" not in name for name in file.namelist()))


if __name__ == "__main__":
    unittest.main()
