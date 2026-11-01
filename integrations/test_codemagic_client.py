import http.client
import io
import json
import os
import traceback
import unittest
import urllib.error
from unittest.mock import patch

from integrations import codemagic_client as client


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class CodemagicClientTest(unittest.TestCase):
    def setUp(self):
        self.config = {"CODEMAGIC_API_TOKEN": "private-token", "CODEMAGIC_APP_ID": "app123", "CODEMAGIC_BRANCH": "main"}
        self.environment = patch.dict(os.environ, self.config, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.build = {"_id": "build123", "appId": "app123", "workflowId": "dashboard-backtest",
                      "branch": "main", "status": "finished", "startedAt": "2026-10-29T01:00:00Z",
                      "finishedAt": "2026-10-29T01:10:00Z", "artefacts": []}

    def test_dispatch_uses_documented_payload_without_exposing_api_token(self):
        with patch.object(client.OPENER, "open", return_value=Response(b'{"buildId":"build123"}')) as send:
            self.assertEqual(client.start_build("telegram-command", {"TELEGRAM_COMMAND": "help"}), "build123")
        request = send.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.codemagic.io/builds")
        self.assertEqual(json.loads(request.data), {"appId": "app123", "workflowId": "telegram-command", "branch": "main",
                         "environment": {"variables": {"TELEGRAM_COMMAND": "help"}}})
        self.assertEqual(request.get_header("X-auth-token"), "private-token")
        self.assertNotIn("private-token", request.full_url)

    def test_configuration_and_command_allowlist_fail_before_network(self):
        with patch.object(client.OPENER, "open") as send:
            for workflow, variables in (("release", {}), ("telegram-command", {"TELEGRAM_COMMAND": "shell"}),
                                        ("telegram-command", {"TELEGRAM_COMMAND": "help", "API_TOKEN": "x"})):
                with self.assertRaises(client.CodemagicError):
                    client.start_build(workflow, variables)
            with patch.dict(os.environ, {"CODEMAGIC_API_TOKEN": ""}):
                self.assertFalse(client.configured())
                with self.assertRaises(client.CodemagicError):
                    client.list_builds("signal-scan")
            send.assert_not_called()

    def test_history_preserves_workflow_branch_and_existing_dashboard_schema(self):
        ignored = {**self.build, "branch": "other"}
        with patch.object(client.OPENER, "open", return_value=Response(json.dumps({"builds": [ignored, self.build]}).encode())) as send:
            builds = client.list_builds("dashboard-backtest")
        self.assertEqual(builds, [self.build])
        self.assertIn("appId=app123", send.call_args.args[0].full_url)
        run = client.normalize_build(builds[0])
        self.assertEqual(run["status"], "completed")
        self.assertEqual(run["conclusion"], "success")
        self.assertEqual(run["html_url"], "https://codemagic.io/app/app123/build/build123")
        self.assertEqual(client.normalize_build({**self.build, "status": "queued"})["status"], "queued")
        self.assertEqual(client.normalize_build({**self.build, "status": "failed"})["conclusion"], "failure")

    def test_http_protocol_and_schema_errors_fail_closed_without_secret_text(self):
        failures = [OSError("private-token"), http.client.IncompleteRead(b"private-token", 2)]
        for failure in failures:
            with patch.object(client.OPENER, "open", side_effect=failure), self.assertRaises(client.CodemagicError) as caught:
                client.list_builds("signal-scan")
            self.assertNotIn("private-token", str(caught.exception))
            self.assertNotIn("private-token", "".join(traceback.format_exception(caught.exception)))
        for payload in ({"data": []}, {"builds": [{}]}):
            with patch.object(client.OPENER, "open", return_value=Response(json.dumps(payload).encode())):
                with self.assertRaises(client.CodemagicError):
                    client.list_builds("signal-scan")

    def test_report_files_come_from_one_finished_build(self):
        build = {**self.build, "artefacts": [
            {"name": "dashboard_backtest_last_result.json", "url": "https://api.codemagic.io/artifacts/a/result.json"},
            {"name": "dashboard_backtest_status.json", "url": "https://api.codemagic.io/artifacts/a/status.json"},
            {"name": "unrelated.log", "url": "https://evil.example/private-token"}]}
        with patch.object(client, "list_builds", return_value=[build]), patch.object(client.OPENER, "open", side_effect=[
            Response(b'{"run_id":"r1","trade_count":2}'), Response(b'{"run_id":"r1","status":"completed"}')]):
            report = client.latest_report()
        self.assertTrue(report["available"])
        self.assertEqual(set(report["files"]), {"backtest_last_result.json", "backtest_status.json"})
        self.assertEqual(report["run"]["id"], "build123")
        with patch.object(client, "list_builds", return_value=[]):
            self.assertFalse(client.latest_report()["available"])

    def test_mixed_report_runs_are_rejected(self):
        build = {**self.build, "artefacts": [
            {"name": "backtest_last_result.json", "url": "https://api.codemagic.io/artifacts/a/result.json"},
            {"name": "backtest_status.json", "url": "https://api.codemagic.io/artifacts/a/status.json"}]}
        with patch.object(client, "list_builds", return_value=[build]), patch.object(client.OPENER, "open", side_effect=[
            Response(b'{"run_id":"r1"}'), Response(b'{"run_id":"r2"}')]):
            with self.assertRaises(client.CodemagicError):
                client.latest_report()

    def test_artifact_redirect_drops_auth_on_trusted_storage(self):
        redirect = urllib.error.HTTPError("https://api.codemagic.io/artifacts/a/file", 302, "redirect",
                                         {"Location": "https://bucket.s3.eu-west-1.amazonaws.com/report?signature=x"}, None)
        with patch.object(client.OPENER, "open", side_effect=[redirect, Response(b"report")]) as send:
            self.assertEqual(client.download_artifact("https://api.codemagic.io/artifacts/a/file"), "report")
        requests = [call.args[0] for call in send.call_args_list]
        self.assertEqual(requests[0].get_header("X-auth-token"), "private-token")
        self.assertIsNone(requests[1].get_header("X-auth-token"))

    def test_artifact_urls_size_and_redirects_are_bounded(self):
        bad_urls = ("http://api.codemagic.io/artifacts/a", "https://evil.example/a", "https://api.codemagic.io/builds",
                    "https://api.codemagic.io/artifacts/../builds", "https://user@api.codemagic.io/artifacts/a",
                    "https://api.codemagic.io:bad/artifacts/a", "https://storage.googleapis.com/bucket/report")
        with patch.object(client.OPENER, "open") as send:
            for url in bad_urls:
                with self.subTest(url=url), self.assertRaises(client.CodemagicError):
                    client.download_artifact(url)
            send.assert_not_called()
        with patch.object(client.OPENER, "open", return_value=Response(b"x"*(client.MAX_ARTIFACT+1))):
            with self.assertRaises(client.CodemagicError):
                client.download_artifact("https://api.codemagic.io/artifacts/a/file")


if __name__ == "__main__":
    unittest.main()
