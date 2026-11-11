"""Contract tests for the P1 read-only Scaleway SSH preflight."""

from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import textwrap
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "ops" / "ssh" / "t0-readonly-preflight.sh"
WORKFLOW = SCRIPT.parents[2] / ".github" / "workflows" / "t0-manual-validation.yml"


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
        # Assert the parser's accepted case labels and fail-closed default,
        # without requiring a particular intermediate variable assignment.
        self.assertIn('LOOPBACK_LISTENER) api_state="LOOPBACK_LISTENER" ;;', self.source)
        self.assertIn('NON_LOOPBACK_LISTENER) api_state="NON_LOOPBACK_LISTENER" ;;', self.source)
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


    def run_preflight_with_stubs(
        self, *, include_awk=True, awk_exit=None, include_pgrep=True,
        pgrep_exit=1, include_ss=True, ss_exit=None,
        ss_address='127.0.0.1:8788'
    ):
        with tempfile.TemporaryDirectory() as directory:
            bin_dir = Path(directory)
            for command in ("hostname", "id"):
                resolved = shutil.which(command, path="/usr/bin:/bin")
                self.assertIsNotNone(resolved, command)
                (bin_dir / command).symlink_to(resolved)
            git = bin_dir / "git"
            git.write_text(
                "#!/bin/sh" + chr(10) + "printf '%s\\n' 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'" + chr(10),
                encoding="utf-8",
            )
            git.chmod(0o755)
            resolved_python = shutil.which("python3", path="/usr/bin:/bin")
            self.assertIsNotNone(resolved_python, "python3")
            (bin_dir / "python3").symlink_to(resolved_python)
            if include_ss:
                ss = bin_dir / "ss"
                if ss_exit is not None:
                    ss.write_text("#!/bin/sh" + chr(10) + f"exit {ss_exit}" + chr(10), encoding="utf-8")
                else:
                    ss.write_text(
                        "#!/bin/sh" + chr(10) + "printf '%s" + chr(92) + "n' 'LISTEN 0 128 " + ss_address + " 0.0.0.0:*'" + chr(10),
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
                    awk.write_text("#!/bin/sh" + chr(10) + f"exit {awk_exit}" + chr(10), encoding="utf-8")
                    awk.chmod(0o755)
            if include_pgrep:
                pgrep = bin_dir / "pgrep"
                pgrep.write_text("#!/bin/sh" + chr(10) + f"exit {pgrep_exit}" + chr(10), encoding="utf-8")
                pgrep.chmod(0o755)
            # Run an isolated copy of the preflight with a real temporary
            # SQLite database. The production script path remains unchanged.
            import sqlite3
            db_path = Path(directory) / "market-data.sqlite3"
            connection = sqlite3.connect(db_path)
            try:
                connection.execute("CREATE TABLE contract_fixture (value INTEGER)")
                connection.commit()
            finally:
                connection.close()

            isolated_script = Path(directory) / "t0-readonly-preflight.sh"
            script_text = self.source.replace(
                'readonly T0_DB_PATH="/home/ubuntu/t0/app/.data/market-data.sqlite3"',
                f'readonly T0_DB_PATH="{db_path}"',
            )
            self.assertNotEqual(script_text, self.source, "temporary DB path substitution must apply")
            isolated_script.write_text(script_text, encoding="utf-8")

            result = subprocess.run(
                ["/bin/bash", str(isolated_script)],
                env={**os.environ, "PATH": str(bin_dir)},
                text=True,
                capture_output=True,
                check=False,
            )
            return result


    def test_loopback_listener_is_classified_only_after_successful_parse(self):
        result = self.run_preflight_with_stubs()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("API_8788=LOOPBACK_LISTENER", result.stdout)
        self.assertIn("SQLITE_INTEGRITY=PASS", result.stdout)

    def test_missing_ss_fails_closed(self):
        result = self.run_preflight_with_stubs(include_ss=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("API_8788=CHECK_UNAVAILABLE", result.stdout)
        self.assertNotIn("API_8788=LOOPBACK_LISTENER", result.stdout)

    def test_failed_ss_fails_closed(self):
        result = self.run_preflight_with_stubs(ss_exit=2)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("API_8788=CHECK_FAILED", result.stdout)
        self.assertNotIn("API_8788=LOOPBACK_LISTENER", result.stdout)

    def test_workflow_ends_at_the_single_evidence_upload_block(self):
        workflow = (SCRIPT.parents[2] / ".github" / "workflows" / "t0-manual-validation.yml")
        text = workflow.read_text(encoding="utf-8")
        self.assertTrue(text.endswith("            preflight-ssh-exit-code.txt\n"))
        self.assertNotIn("\n preflight-remote.log; then", text)

    def test_non_loopback_listener_is_rejected(self):
        result = self.run_preflight_with_stubs(ss_address="0.0.0.0:8788")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("API_8788=NON_LOOPBACK_LISTENER", result.stdout)

    def test_successful_empty_pgrep_result_is_distinct_from_probe_failure(self):
        result = self.run_preflight_with_stubs(pgrep_exit=1)
        self.assertIn("FEEDER_PIDS=NONE", result.stdout)
        self.assertNotIn("FEEDER_PIDS=CHECK_FAILED", result.stdout)

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
            r"\b(rm|mv|cp|chmod|chown|kill|pkill|systemctl|service|reboot|shutdown|truncate)\b"
        )
        forbidden_sql = re.compile(
            r"\b(INSERT|UPDATE|DELETE|REPLACE|CREATE|DROP|ALTER|VACUUM)\b",
            re.IGNORECASE,
        )
        self.assertIsNone(forbidden_commands.search(self.source))
        self.assertIsNone(forbidden_sql.search(self.source))

    def test_only_expected_t0_paths_and_api_port_are_referenced(self):
        self.assertIn('/home/ubuntu/t0/app', self.source)
        self.assertIn('/home/ubuntu/t0/app/.data/market-data.sqlite3', self.source)
        self.assertIn('readonly API_PORT="8788"', self.source)


    def test_encrypted_private_key_is_unlocked_only_in_ephemeral_agent(self):
        workflow = WORKFLOW.read_text()
        self.assertIn("SCW_SSH_KEY_PASSPHRASE", workflow)
        self.assertIn("SSH_ASKPASS_REQUIRE=force", workflow)
        self.assertIn('ssh-add -t 300 "$key_file"', workflow)
        self.assertIn('eval "$(ssh-agent -s -t 300)"', workflow)
        self.assertIn("ssh-agent -k", workflow)
        self.assertIn('rm -f -- "$key_file" "$passphrase_file"', workflow)
        self.assertIn("SHA256:z6b+FNalGgXhZvT9dc9TszFeUjB3Z/1z5SiWCgWQq/w", workflow)
        self.assertIn('-i "$public_key_file"', workflow)
        self.assertNotIn('-i "$key_file"', workflow)
        self.assertNotIn('echo "$SCW_SSH_KEY_PASSPHRASE"', workflow)
        self.assertNotIn("ssh-add-stderr.log", workflow.rsplit("path: |", 1)[-1])
        self.assertNotIn("ssh-client-stderr.log", workflow.rsplit("path: |", 1)[-1])
        ssh_job = workflow.split("  ssh-preflight:\n", 1)[1]
        job_header = ssh_job.split("    steps:\n", 1)[0]
        self.assertNotIn("SCW_SSH_PRIVATE_KEY: ${{ secrets.SCW_SSH_PRIVATE_KEY }}", job_header)
        self.assertNotIn("SCW_SSH_KEY_PASSPHRASE: ${{ secrets.SCW_SSH_KEY_PASSPHRASE }}", job_header)
        self.assertIn("SCW_SSH_PRIVATE_KEY: ${{ secrets.SCW_SSH_PRIVATE_KEY }}", ssh_job)

    def test_pull_request_runs_contract_only_without_exposing_ssh_secrets(self):
        workflow = WORKFLOW.read_text()
        self.assertIn("pull_request:", workflow)
        self.assertIn("github.event_name == 'pull_request'", workflow)
        self.assertIn("github.event_name == 'workflow_dispatch' && inputs.gate == 'scaleway-ssh-preflight'", workflow)
        self.assertIn("SCW_SSH_KEY_PASSPHRASE", workflow)


    def test_verdict_requires_successful_ssh_exit_code(self):
        workflow = WORKFLOW.read_text()
        classifier = workflow.split("      - name: Classify preflight evidence\n", 1)[1].split(
            "      - name: Upload sanitized preflight evidence\n", 1
        )[0]
        self.assertIn("preflight-ssh-exit-code.txt", classifier)
        self.assertIn("grep -Fxq '0' preflight-ssh-exit-code.txt", classifier)
        self.assertLess(
            classifier.index("grep -Fxq '0' preflight-ssh-exit-code.txt"),
            classifier.index("P1_SSH_PREFLIGHT=PASS_READ_ONLY_PREFLIGHT"),
        )

    def test_verdict_requires_complete_framed_probe_evidence(self):
        workflow = WORKFLOW.read_text()
        classifier = workflow.split("      - name: Classify preflight evidence\n", 1)[1].split(
            "      - name: Upload sanitized preflight evidence\n", 1
        )[0]
        for required in (
            "P1_SSH_PREFLIGHT_VERSION=1",
            "P1_SSH_PREFLIGHT_END=1",
            "HOSTNAME=",
            "SSH_USER=",
            "SOURCE_SHA=",
            "FEEDER_PIDS=",
            "API_8788=",
            "SQLITE_INTEGRITY=PASS",
        ):
            self.assertIn(required, classifier)
        self.assertIn("P1_SSH_PREFLIGHT=PARTIAL_OR_BLOCKED_EVIDENCE", classifier)

    def test_verdict_artifact_includes_sanitized_ssh_diagnostics(self):
        workflow = WORKFLOW.read_text()
        artifact = workflow.split("      - name: Upload sanitized preflight evidence\n", 1)[1]
        for required in ("preflight-ssh-diagnostic.txt", "preflight-ssh-exit-code.txt"):
            self.assertIn(required, artifact)


    def run_classifier(self, *, ssh_exit_code="0", remote_log=None):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        step = workflow.split("      - name: Classify preflight evidence\n", 1)[1].split(
            "      - name: Upload sanitized preflight evidence\n", 1
        )[0]
        script = textwrap.dedent(step.split("        run: |\n", 1)[1])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            if ssh_exit_code is not None:
                (root / "preflight-ssh-exit-code.txt").write_text(
                    f"{ssh_exit_code}\n", encoding="utf-8"
                )
            if remote_log is not None:
                (root / "preflight-remote.log").write_text(remote_log, encoding="utf-8")
            result = subprocess.run(
                ["bash", "-c", script],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )
            verdict_path = root / "preflight-verdict.txt"
            verdict = verdict_path.read_text(encoding="utf-8") if verdict_path.exists() else ""
            return result, verdict

    @staticmethod
    def complete_remote_evidence():
        return "\n".join(
            (
                "P1_SSH_PREFLIGHT_VERSION=1",
                "HOSTNAME=btcquant-test",
                "SSH_USER=ubuntu",
                "SOURCE_SHA=" + "a" * 40,
                "FEEDER_PIDS=1234",
                "API_8788=LOOPBACK_LISTENER",
                "SQLITE_INTEGRITY=PASS",
                "P1_SSH_PREFLIGHT_END=1",
                "",
            )
        )

    def test_classifier_blocks_failed_ssh_even_when_valid_remote_log_exists(self):
        result, verdict = self.run_classifier(
            ssh_exit_code="255", remote_log=self.complete_remote_evidence()
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("P1_SSH_PREFLIGHT=BLOCKED_SSH_STEP_FAILED_OR_NOT_RUN", verdict)
        self.assertNotIn("P1_SSH_PREFLIGHT=PASS_READ_ONLY_PREFLIGHT", verdict)

    def test_classifier_blocks_incomplete_protocol_framing(self):
        evidence = self.complete_remote_evidence().replace(
            "P1_SSH_PREFLIGHT_END=1\n", ""
        )
        result, verdict = self.run_classifier(ssh_exit_code="0", remote_log=evidence)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("P1_SSH_PREFLIGHT=PARTIAL_OR_BLOCKED_EVIDENCE", verdict)
        self.assertNotIn("P1_SSH_PREFLIGHT=PASS_READ_ONLY_PREFLIGHT", verdict)

    def test_classifier_blocks_missing_required_probe_field(self):
        evidence = self.complete_remote_evidence().replace("HOSTNAME=btcquant-test\n", "")
        result, verdict = self.run_classifier(ssh_exit_code="0", remote_log=evidence)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("P1_SSH_PREFLIGHT=PARTIAL_OR_BLOCKED_EVIDENCE", verdict)

    def test_classifier_passes_only_complete_successful_loopback_evidence(self):
        result, verdict = self.run_classifier(
            ssh_exit_code="0", remote_log=self.complete_remote_evidence()
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("P1_SSH_PREFLIGHT=PASS_READ_ONLY_PREFLIGHT", verdict)

if __name__ == "__main__":
    unittest.main()
