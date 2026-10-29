import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
from email.message import Message
from urllib.error import HTTPError, URLError

from data_lake.local_setup import SECRET_KEYS, check_local, main, prepare_configuration, read_configuration


class LocalSetupTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "local.env"

    def test_private_distinct_settings_survive_repeated_setup_without_rotation(self):
        first = prepare_configuration(self.path, 8899)
        self.assertEqual(len({first[key] for key in SECRET_KEYS}), 4)
        self.assertTrue(all(len(first[key]) >= 32 for key in SECRET_KEYS))
        original = self.path.read_bytes()
        self.assertEqual(prepare_configuration(self.path), first)
        self.assertEqual(self.path.read_bytes(), original)
        if os.name != "nt":
            self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)
        with self.assertRaises(ValueError):
            prepare_configuration(self.path, 8900)
        self.assertEqual(self.path.read_bytes(), original)

    def test_invalid_and_symlink_configuration_is_not_replaced_or_followed(self):
        self.path.write_text("MARKET_DATA_TOKEN=do-not-overwrite\n")
        self.path.chmod(0o600)
        with self.assertRaises(ValueError):
            prepare_configuration(self.path)
        self.assertEqual(self.path.read_text(), "MARKET_DATA_TOKEN=do-not-overwrite\n")
        self.path.unlink()
        destination = self.path.with_name("untouched")
        destination.write_text("keep")
        self.path.symlink_to(destination)
        with self.assertRaises((ValueError, OSError)):
            prepare_configuration(self.path)
        self.assertEqual(destination.read_text(), "keep")

    def test_cli_prints_no_secrets_and_checks_do_not_create_config(self):
        output = io.StringIO()
        with patch("sys.stdout", output):
            self.assertEqual(main(["--config", str(self.path), "--check"]), 1)
        self.assertFalse(self.path.exists())
        output = io.StringIO()
        with patch("sys.stdout", output):
            self.assertEqual(main(["--config", str(self.path)]), 0)
        values = read_configuration(self.path)
        self.assertTrue(json.loads(output.getvalue())["configured"])
        for key in SECRET_KEYS:
            self.assertNotIn(values[key], output.getvalue())

    def test_probe_uses_header_token_and_does_not_report_missing_data_as_storage_failure(self):
        values = prepare_configuration(self.path)
        headers = Message()
        headers["Content-Type"] = "application/json"
        body = io.BytesIO(json.dumps({"service": "canonical-data-lake", "ready": True, "freshData": False}).encode())
        body.status, body.headers = 200, headers
        with patch("data_lake.local_setup.build_opener") as opener:
            opener.return_value.open.return_value = body
            result = check_local(self.path)
            request = opener.return_value.open.call_args.args[0]
        self.assertTrue(result["ready"])
        self.assertFalse(result["freshData"])
        self.assertEqual(request.get_header("Authorization"), "Bearer " + values["LAKE_READ_TOKEN"])
        self.assertNotIn(values["LAKE_READ_TOKEN"], request.full_url)
        self.assertNotIn(values["LAKE_READ_TOKEN"], json.dumps(result))

    def test_probe_failures_are_bounded_safe_results(self):
        values = prepare_configuration(self.path)
        for error, expected in ((URLError(values["LAKE_READ_TOKEN"]), "LOCAL_API_UNAVAILABLE"),
                                (HTTPError("http://127.0.0.1", 401, values["LAKE_READ_TOKEN"], {}, None), "AUTH_FAILED")):
            with patch("data_lake.local_setup.build_opener") as opener:
                opener.return_value.open.side_effect = error
                result = check_local(self.path)
            self.assertFalse(result["ready"])
            self.assertEqual(result["reason"], expected)
            self.assertNotIn(values["LAKE_READ_TOKEN"], json.dumps(result))


if __name__ == "__main__":
    unittest.main()
