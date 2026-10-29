"""Orchestration boundary tests; these do not run Docker or validate PostgreSQL."""

import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from data_lake import local_trial
from data_lake.local_setup import SECRET_KEYS, read_configuration


READY_EMPTY = {"service": "canonical-data-lake", "ready": True, "freshData": False}
READY_FRESH = {**READY_EMPTY, "freshData": True}


class LocalTrialTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "local.env"
        self.environment = {"DOCKER_HOST": "unix:///var/run/docker.sock"}
        self.environment_patch = patch.dict(os.environ, self.environment, clear=True)
        self.environment_patch.start()
        self.addCleanup(self.environment_patch.stop)
        self.stderr = io.StringIO()
        self.stderr_patch = patch("sys.stderr", self.stderr)
        self.stderr_patch.start()
        self.addCleanup(self.stderr_patch.stop)
        self.commands = []
        self.context_endpoint = "unix:///var/run/docker.sock"
        self.operating_system = "linux"
        self.compose_version = "2.39.1"

    def docker(self, arguments, **options):
        self.commands.append((arguments, options))
        if arguments[-2:] == ["context", "show"]:
            output = "desktop-linux\n"
        elif "inspect" in arguments:
            output = json.dumps(self.context_endpoint)
        elif "info" in arguments:
            output = json.dumps(self.operating_system)
        elif "version" in arguments:
            output = self.compose_version
        else:
            output = ""
        return subprocess.CompletedProcess(arguments, 0, output, "")

    def run_trial(self, **options):
        with patch("data_lake.local_trial.subprocess.run", side_effect=self.docker), \
                patch("data_lake.local_trial.check_local", return_value=READY_EMPTY):
            return local_trial.run_trial(self.path, **options)

    def test_default_starts_only_api_dependencies_and_accepts_ready_empty_storage(self):
        with patch("data_lake.local_trial._verify") as verify:
            result = self.run_trial()
        self.assertEqual(result, {"ok": True, "dataRequested": False, "apiUrl": "http://127.0.0.1:8788",
                                  "api": READY_EMPTY})
        verify.assert_not_called()
        self.assertTrue(self.path.exists())
        commands = [command for command, _ in self.commands]
        self.assertEqual(commands[-1][-4:], ["up", "-d", "--build", "api"])
        self.assertTrue(any(command[-2:] == ["config", "--quiet"] for command in commands))
        self.assertFalse(any("collector" in command for command in commands))
        self.assertFalse(any("down" in command or "--volumes" in command for command in commands))
        self.assertEqual(self.commands[-1][1]["timeout"], 900)

    def test_validated_local_host_is_pinned_and_environment_cannot_override_private_file(self):
        inherited = {"DOCKER_CONTEXT": "local", "DOCKER_HOST": "tcp://remote:2375",
                     "DOCKER_TLS": "1", "DOCKER_TLS_VERIFY": "1", "DOCKER_CERT_PATH": "/private/certs",
                     "DOCKER_CONFIG": "/private/registry-auth", "HTTP_PROXY": "http://proxy:8080",
                     "HTTPS_PROXY": "http://proxy:8080", "COMPOSE_PROFILES": "collector",
                     "LAKE_API_PORT": "9999", **{key: "inherited-private-canary" for key in SECRET_KEYS}}
        with patch.dict(os.environ, inherited, clear=True):
            result = self.run_trial(port=8881)
            self.assertEqual(os.environ["DOCKER_HOST"], "tcp://remote:2375")
        self.assertTrue(result["ok"])
        self.assertEqual(result["apiUrl"], "http://127.0.0.1:8881")
        for command, options in self.commands:
            self.assertEqual(command[:3], ["docker", "--context", "local"])
            self.assertNotIn("shell", options)
            child = options["env"]
            for key in (*local_trial.DOCKER_SELECTORS, *SECRET_KEYS, "LAKE_API_PORT", "COMPOSE_PROFILES"):
                self.assertNotIn(key, child)
            for key in ("DOCKER_CONFIG", "HTTP_PROXY", "HTTPS_PROXY"):
                self.assertEqual(child[key], inherited[key])
            self.assertNotIn("inherited-private-canary", " ".join(command))
        self.assertEqual(self.commands[0][0][-2:], ["--format", "{{json .Endpoints.docker.Host}}"])
        config = read_configuration(self.path)
        for key in SECRET_KEYS:
            self.assertNotIn(config[key], json.dumps(result) + self.stderr.getvalue())
        self.assertIs(self.commands[-1][1]["stdout"], self.stderr)
        self.assertIs(self.commands[-1][1]["stderr"], self.stderr)

    def test_explicit_host_takes_precedence_over_saved_context_and_is_always_pinned(self):
        result = self.run_trial()
        self.assertTrue(result["ok"])
        for command, _ in self.commands:
            self.assertEqual(command[:3], ["docker", "--host", self.environment["DOCKER_HOST"]])
        self.assertFalse(any("context" in command for command, _ in self.commands))

    def test_saved_context_is_inspected_before_private_config_is_created(self):
        with patch.dict(os.environ, {}, clear=True):
            result = self.run_trial()
        self.assertTrue(result["ok"])
        self.assertEqual(self.commands[0][0], ["docker", "context", "show"])
        for command, _ in self.commands[1:]:
            self.assertEqual(command[:3], ["docker", "--context", "desktop-linux"])

    def test_remote_context_refuses_before_configuration_or_daemon_access(self):
        self.context_endpoint = "ssh://remote.example"
        with patch.dict(os.environ, {"DOCKER_CONTEXT": "remote"}, clear=True), \
                patch("data_lake.local_trial.prepare_configuration") as prepare:
            result = self.run_trial()
        self.assertEqual(result, {"ok": False, "dataRequested": False, "reason": "LOCAL_DOCKER_REQUIRED"})
        prepare.assert_not_called()
        self.assertFalse(self.path.exists())
        self.assertEqual(len(self.commands), 1)
        self.assertIn("inspect", self.commands[0][0])

    def test_remote_or_malformed_endpoints_fail_before_configuration(self):
        for endpoint in ("tcp://127.0.0.1:2375", "ssh://localhost", "unix://remote/docker.sock",
                         "unix:/var/run/docker.sock", "unix:///sock?redirect=yes",
                         "npipe:////remote/pipe/docker_engine", "npipe://remote/pipe/docker_engine"):
            with self.subTest(endpoint=endpoint), patch.dict(os.environ, {"DOCKER_HOST": endpoint}, clear=True):
                result = self.run_trial()
            self.assertEqual(result["reason"], "LOCAL_DOCKER_REQUIRED")
            self.assertFalse(self.path.exists())
        self.assertEqual(self.commands, [])

    def test_local_windows_pipe_is_allowed_but_requires_linux_containers(self):
        with patch.dict(os.environ, {"DOCKER_HOST": "npipe:////./pipe/docker_engine"}, clear=True):
            self.operating_system = "windows"
            result = self.run_trial()
        self.assertEqual(result["reason"], "LINUX_CONTAINERS_REQUIRED")
        self.assertFalse(self.path.exists())
        self.assertEqual(self.commands[0][0][:3], ["docker", "--host", "npipe:////./pipe/docker_engine"])

    def test_missing_daemon_and_compose_v1_fail_before_configuration(self):
        self.compose_version = "1.29.2"
        result = self.run_trial()
        self.assertEqual(result["reason"], "COMPOSE_V2_REQUIRED")
        self.assertFalse(self.path.exists())
        with patch("data_lake.local_trial.subprocess.run", side_effect=FileNotFoundError("secret-canary")):
            result = local_trial.run_trial(self.path)
        self.assertEqual(result["reason"], "DOCKER_UNAVAILABLE")
        self.assertNotIn("secret-canary", json.dumps(result) + self.stderr.getvalue())
        self.assertFalse(self.path.exists())

    def test_invalid_options_do_not_invoke_docker_or_prepare_configuration(self):
        for options in ({"bars": 1}, {"bars": 2001}, {"wait_seconds": 0}, {"wait_seconds": 301},
                        {"project_name": "--bad"}, {"project_name": "A"}, {"project_name": "x" * 64},
                        {"port": 0}, {"load_candles": "true"}, {"bars": True}):
            with self.subTest(options=options):
                self.assertEqual(self.run_trial(**options)["reason"], "INVALID_TRIAL_OPTIONS")
        self.assertEqual(self.commands, [])
        self.assertFalse(self.path.exists())

    def test_existing_configuration_is_retained_and_port_conflict_does_not_start_compose(self):
        self.assertTrue(self.run_trial(port=8899)["ok"])
        original = self.path.read_bytes()
        self.assertTrue(self.run_trial()["ok"])
        self.assertEqual(self.path.read_bytes(), original)
        self.commands.clear()
        result = self.run_trial(port=8900)
        self.assertFalse(result["ok"])
        self.assertEqual(self.path.read_bytes(), original)
        self.assertFalse(any("up" in command for command, _ in self.commands))

    def test_explicit_load_runs_one_bounded_refresh_then_verifies_actual_api_windows(self):
        verification = {"verified": True, "timeframes": {"15m": {"returned": 20}, "1h": {"returned": 20}}}
        calls = []

        def probe(path):
            calls.append("ready")
            return READY_EMPTY if len(calls) == 1 else READY_FRESH

        def verify(path, bars):
            self.assertEqual(path, self.path)
            self.assertEqual(bars, 20)
            calls.append("verify")
            return verification

        with patch("data_lake.local_trial.subprocess.run", side_effect=self.docker), \
                patch("data_lake.local_trial.check_local", side_effect=probe), \
                patch("data_lake.local_trial._verify", side_effect=verify):
            result = local_trial.run_trial(self.path, load_candles=True)
        self.assertEqual(calls, ["ready", "ready", "verify"])
        self.assertTrue(result["ok"])
        self.assertTrue(result["dataRequested"])
        self.assertEqual(result["verification"], verification)
        refreshes = [(command, options) for command, options in self.commands if "collector" in command]
        self.assertEqual(len(refreshes), 1)
        self.assertEqual(refreshes[0][0][-6:], ["run", "--rm", "collector", "refresh", "--bars", "20"])
        self.assertEqual(refreshes[0][1]["timeout"], 300)

    def test_incomplete_or_stale_candles_are_reported_without_retry_or_cleanup(self):
        incomplete = {"verified": False, "timeframes": {"15m": {"returned": 0}, "1h": {"returned": None}}}
        for ready, verification, reason in ((READY_FRESH, incomplete, "CANDLE_VERIFICATION_INCOMPLETE"),
                                           (READY_EMPTY, {"verified": True}, "CANDLES_NOT_FRESH")):
            with self.subTest(reason=reason), \
                    patch("data_lake.local_trial.subprocess.run", side_effect=self.docker), \
                    patch("data_lake.local_trial.check_local", return_value=ready), \
                    patch("data_lake.local_trial._verify", return_value=verification):
                self.commands.clear()
                result = local_trial.run_trial(self.path, load_candles=True)
            self.assertFalse(result["ok"])
            self.assertEqual(result["reason"], reason)
            self.assertEqual(result["verification"], verification)
            self.assertEqual(sum("collector" in command for command, _ in self.commands), 1)
            self.assertFalse(any("down" in command or "--volumes" in command for command, _ in self.commands))

    def test_failed_refresh_stops_before_verification_and_retains_ready_status(self):
        def docker(arguments, **options):
            response = self.docker(arguments, **options)
            if "collector" in arguments:
                response.returncode = 1
            return response

        with patch("data_lake.local_trial.subprocess.run", side_effect=docker), \
                patch("data_lake.local_trial.check_local", return_value=READY_EMPTY), \
                patch("data_lake.local_trial._verify") as verify:
            result = local_trial.run_trial(self.path, load_candles=True)
        self.assertEqual(result["reason"], "COLLECTOR_REFRESH_FAILED")
        self.assertEqual(result["api"], READY_EMPTY)
        verify.assert_not_called()
        self.assertEqual(sum("collector" in command for command, _ in self.commands), 1)

    def test_build_timeout_has_fixed_code_and_preserves_configuration_without_cleanup(self):
        def docker(arguments, **options):
            if "up" in arguments:
                self.commands.append((arguments, options))
                raise subprocess.TimeoutExpired(arguments, options["timeout"], output="secret-canary")
            return self.docker(arguments, **options)

        with patch("data_lake.local_trial.subprocess.run", side_effect=docker):
            result = local_trial.run_trial(self.path)
        self.assertEqual(result["reason"], "COMPOSE_START_FAILED_TIMEOUT")
        self.assertTrue(self.path.exists())
        self.assertNotIn("secret-canary", json.dumps(result) + self.stderr.getvalue())
        self.assertFalse(any("down" in command or "--volumes" in command for command, _ in self.commands))

    def test_readiness_timeout_and_auth_failure_are_fixed_safe_codes(self):
        for status, reason in (({"ready": False, "reason": "LOCAL_API_UNAVAILABLE"}, "LOCAL_API_READY_TIMEOUT"),
                               ({"ready": False, "reason": "AUTH_FAILED"}, "LOCAL_API_AUTH_FAILED")):
            with self.subTest(reason=reason), \
                    patch("data_lake.local_trial.subprocess.run", side_effect=self.docker), \
                    patch("data_lake.local_trial.check_local", return_value=status), \
                    patch("data_lake.local_trial.time.monotonic", side_effect=[0, 1]), \
                    patch("data_lake.local_trial.time.sleep") as sleep:
                result = local_trial.run_trial(self.path, wait_seconds=1)
            self.assertEqual(result["reason"], reason)
            self.assertNotIn("api", result)
            sleep.assert_not_called()

    def test_cli_stdout_is_one_safe_json_document_on_success_or_failure(self):
        for failure in (False, True):
            stdout = io.StringIO()
            action = FileNotFoundError("secret-canary") if failure else self.docker
            with self.subTest(failure=failure), patch("sys.stdout", stdout), \
                    patch("data_lake.local_trial.subprocess.run", side_effect=action), \
                    patch("data_lake.local_trial.check_local", return_value=READY_EMPTY):
                code = local_trial.main(["--config", str(self.path), "--project-name", "chart-lake-smoke",
                                         "--port", "8788", "--wait-seconds", "120"])
            report = json.loads(stdout.getvalue())
            self.assertEqual(report["ok"], not failure)
            self.assertEqual(code, 1 if failure else 0)
            self.assertNotIn("secret-canary", stdout.getvalue() + self.stderr.getvalue())
            self.assertEqual(len(stdout.getvalue().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
