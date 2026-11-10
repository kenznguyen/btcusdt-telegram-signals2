"""Contract tests for the P1 read-only Scaleway SSH preflight."""

from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "ops" / "ssh" / "t0-readonly-preflight.sh"


class T0SSHPreflightContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SCRIPT.read_text(encoding="utf-8")

    def test_emits_framed_machine_readable_evidence(self):
        for marker in (
            "P1_SSH_PREFLIGHT_VERSION=1",
            "P1_SSH_PREFLIGHT_END=1",
            'emit "HOSTNAME"',
            'emit "SSH_USER"',
            'emit "SOURCE_SHA"',
            'emit "FEEDER_PIDS"',
            'emit "API_8788"',
            'emit "SQLITE_INTEGRITY"',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.source)

    def test_sqlite_integrity_check_is_strictly_read_only(self):
        self.assertIn("mode=ro", self.source)
        self.assertIn("PRAGMA query_only=ON", self.source)
        self.assertIn("PRAGMA integrity_check", self.source)

    def test_api_listener_classification_fails_closed_for_non_loopback(self):
        for state in ("NOT_LISTENING", "NON_LOOPBACK_LISTENER", "LOOPBACK_LISTENER"):
            self.assertIn(f'api_state="{state}"', self.source)
        self.assertIn('[[ "$api_state" != "NON_LOOPBACK_LISTENER" ]] || exit 1', self.source)

    def test_listener_parser_unavailable_or_failed_is_not_loopback(self):
        self.assertIn('api_state="CHECK_UNAVAILABLE"', self.source)
        self.assertIn('command -v awk', self.source)
        self.assertIn('api_state="CHECK_FAILED"', self.source)
        self.assertIn('[[ "$api_state" != "CHECK_UNAVAILABLE" ]] || exit 1', self.source)
        self.assertIn('[[ "$api_state" != "CHECK_FAILED" ]] || exit 1', self.source)
        self.assertIn('parser_result="', self.source)

    def test_listener_parser_accepts_only_positive_loopback_classification(self):
        self.assertIn('parser_result="LOOPBACK_LISTENER"', self.source)
        self.assertIn('parser_result="NON_LOOPBACK_LISTENER"', self.source)
        self.assertIn('*) api_state="CHECK_FAILED" ;;', self.source)

    def test_feeder_regex_matches_expected_module_and_not_unrelated_process(self):
        pattern = re.search(r"pgrep -f '([^']+)'", self.source)
        self.assertIsNotNone(pattern)
        expression = pattern.group(1)
        self.assertIsNotNone(re.search(expression, "python -m market_data.feeder"))
        self.assertIsNone(re.search(expression, "python -m market_data.api"))
        self.assertIsNone(re.search(expression, "pgrep -f '[m]arket_data\\.feeder'"))

    def test_feeder_probe_distinguishes_empty_unavailable_and_failed(self):
        for token in (
            'feeder_pids="CHECK_UNAVAILABLE"',
            'feeder_pids="CHECK_FAILED"',
            'feeder_pids="NONE"',
            'command -v pgrep',
            '[[ "$feeder_pids" != "CHECK_UNAVAILABLE" ]] || exit 1',
            '[[ "$feeder_pids" != "CHECK_FAILED" ]] || exit 1',
        ):
            self.assertIn(token, self.source)

    def test_workflow_does_not_treat_unavailable_feeder_probe_as_absent(self):
        workflow = (SCRIPT.parents[2] / ".github" / "workflows" / "t0-manual-validation.yml")
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("CHECK_(UNAVAILABLE|FAILED)", text)
        self.assertIn("PARTIAL_OR_BLOCKED_PROBE_UNAVAILABLE", text)


    def run_preflight_with_stubs(self, *, include_awk=True, awk_exit=None, include_pgrep=True, pgrep_exit=1):
        with tempfile.TemporaryDirectory() as directory:
            bin_dir = Path(directory)
            for command in ("hostname", "id", "git"):
                resolved = shutil.which(command, path="/usr/bin:/bin")
                self.assertIsNotNone(resolved, command)
                (bin_dir / command).symlink_to(resolved)
            ss = bin_dir / "ss"
            ss.write_text(
                "#!/bin/sh\\nprintf '%s\\\\n' 'LISTEN 0 128 127.0.0.1:8788 0.0.0.0:*'\\n",
                encoding="utf-8",
            )
            ss.chmod(0o755)
            if include_awk:
                awk = bin_dir / "awk"
                if awk_exit is None:
                    resolved = shutil.which("awk", path="/usr/bin:/bin")
                    self.assertIsNotNone(resolved, "awk")
                    awk.symlink_to(resolved)
                else:
                    awk.write_text(f"#!/bin/sh\\nexit {awk_exit}\\n", encoding="utf-8")
                    awk.chmod(0o755)
            if include_pgrep:
                pgrep = bin_dir / "pgrep"
                pgrep.write_text(f"#!/bin/sh\\nexit {pgrep_exit}\\n", encoding="utf-8")
                pgrep.chmod(0o755)
            result = subprocess.run(
                ["/bin/bash", str(SCRIPT)],
                env={**os.environ, "PATH": str(bin_dir)},
                text=True,
                capture_output=True,
                check=False,
            )
            return result

    def test_missing_awk_fails_closed(self):
        result = self.run_preflight_with_stubs(include_awk=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("API_8788=CHECK_UNAVAILABLE", result.stdout)
        self.assertNotIn("API_8788=LOOPBACK_LISTENER", result.stdout)

    def test_failed_awk_fails_closed(self):
        result = self.run_preflight_with_stubs(awk_exit=2)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("API_8788=CHECK_FAILED", result.stdout)
        self.assertNotIn("API_8788=LOOPBACK_LISTENER", result.stdout)

    def test_missing_pgrep_fails_closed(self):
        result = self.run_preflight_with_stubs(include_pgrep=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FEEDER_PIDS=CHECK_UNAVAILABLE", result.stdout)

    def test_failed_pgrep_fails_closed(self):
        result = self.run_preflight_with_stubs(pgrep_exit=2)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FEEDER_PIDS=CHECK_FAILED", result.stdout)

    def test_no_mutating_host_or_database_commands_are_present(self):
        forbidden_commands = re.compile(
            r"\b(rm|mv|cp|chmod|chown|kill|pkill|systemctl|service|reboot|shutdown|truncate)\\b"
        )
        forbidden_sql = re.compile(
            r"\\b(INSERT|UPDATE|DELETE|REPLACE|CREATE|DROP|ALTER|VACUUM)\\b",
            re.IGNORECASE,
        )
        self.assertIsNone(forbidden_commands.search(self.source))
        self.assertIsNone(forbidden_sql.search(self.source))

    def test_only_expected_t0_paths_and_api_port_are_referenced(self):
        self.assertIn('/home/ubuntu/t0/app', self.source)
        self.assertIn('/home/ubuntu/t0/app/.data/market-data.sqlite3', self.source)
        self.assertIn('readonly API_PORT="8788"', self.source)


if __name__ == "__main__":
    unittest.main()
