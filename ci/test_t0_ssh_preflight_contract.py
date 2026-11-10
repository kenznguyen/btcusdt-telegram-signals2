import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/t0-manual-validation.yml"
SCRIPT = ROOT / "ops/ssh/t0-readonly-preflight.sh"

class T0SSHPreflightContractTests(unittest.TestCase):
    def test_workflow_uses_manual_allowlisted_gate_and_protected_environment(self):
        workflow = WORKFLOW.read_text()
        self.assertIn("scaleway-ssh-preflight", workflow)
        self.assertIn("environment:", workflow)
        self.assertIn("scaleway-preflight", workflow)
        self.assertIn("StrictHostKeyChecking=yes", workflow)
        self.assertIn("UserKnownHostsFile=", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("HostKeyAlgorithms=ssh-ed25519", workflow)
        self.assertIn('"$SCW_SSH_USER@$SCW_SSH_HOST" 2>', workflow)
        self.assertNotIn("ssh-keyscan", workflow)

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
        ssh_job = workflow.split("  ssh-preflight:", 1)[1]
        job_header = ssh_job.split("    steps:", 1)[0]
        self.assertNotIn("SCW_SSH_PRIVATE_KEY: ${{ secrets.SCW_SSH_PRIVATE_KEY }}", job_header)
        self.assertNotIn("SCW_SSH_KEY_PASSPHRASE: ${{ secrets.SCW_SSH_KEY_PASSPHRASE }}", job_header)
        self.assertIn("SCW_SSH_PRIVATE_KEY: ${{ secrets.SCW_SSH_PRIVATE_KEY }}", ssh_job)

    def test_pull_request_runs_contract_only_without_exposing_ssh_secrets(self):
        workflow = WORKFLOW.read_text()
        self.assertIn("pull_request:", workflow)
        self.assertIn("scaleway-ssh-contract-only", workflow)
        self.assertIn("inputs.gate == 'scaleway-ssh-contract-only'", workflow)
        self.assertIn("github.event_name == 'pull_request'", workflow)
        self.assertIn("github.event_name == 'workflow_dispatch' && inputs.gate == 'scaleway-ssh-preflight'", workflow)
        self.assertIn("SCW_SSH_KEY_PASSPHRASE", workflow)


    def test_sqlite_lease_fencing_auto_trigger_is_path_scoped(self):
        workflow = WORKFLOW.read_text()
        self.assertIn("push:", workflow)
        self.assertIn("branches:", workflow)
        self.assertIn("feature/t0-centralized-data-feeder-p1-20261101", workflow)
        for path in (
            ".github/workflows/t0-manual-validation.yml",
            "ci/test_t0_ssh_preflight_contract.py",
            "market_data/feeder.py",
            "market_data/store.py",
            "market_data/write_gateway.py",
            "market_data/test_feeder_lease.py",
            "market_data/test_write_gateway.py",
            "market_data/test_feeder_lifecycle.py",
        ):
            self.assertIn(path, workflow)

    def test_sqlite_lease_fencing_auto_job_isolated_and_evidence_backed(self):
        workflow = WORKFLOW.read_text()
        self.assertIn("  sqlite-lease-fencing-auto:", workflow)
        auto_job = workflow.split("  sqlite-lease-fencing-auto:", 1)[1].split("  manual-gate:", 1)[0]
        self.assertIn("github.event_name == 'push' || github.event_name == 'pull_request'", auto_job)
        self.assertIn("permissions:", auto_job)
        self.assertIn("contents: read", auto_job)
        self.assertIn("ref: ${{ github.sha }}", auto_job)
        self.assertIn("persist-credentials: false", auto_job)
        self.assertIn("python -m unittest market_data.test_feeder_lease market_data.test_write_gateway market_data.test_feeder_lifecycle -v", auto_job)
        self.assertIn("sqlite-lease-fencing-tests.log", auto_job)
        self.assertIn("sqlite-lease-fencing-verdict.txt", auto_job)
        self.assertIn("ci-source-sha.txt", auto_job)
        self.assertIn("actions/upload-artifact@v4", auto_job)
        self.assertNotIn("secrets.", auto_job)
        self.assertNotIn("ssh ", auto_job)
        self.assertNotIn("environment:", auto_job)


    def test_sqlite_recovery_auto_trigger_is_path_scoped(self):
        workflow = WORKFLOW.read_text()
        for path in (
            ".github/workflows/t0-manual-validation.yml",
            "market_data/feeder.py",
            "market_data/feeder_service.py",
            "market_data/test_feeder_recovery.py",
            "market_data/test_feeder_scheduler.py",
            "market_data/test_feeder_lifecycle.py",
        ):
            self.assertIn(path, workflow)

    def test_sqlite_recovery_scope_detects_only_recovery_changes(self):
        workflow = WORKFLOW.read_text()
        scope_job = workflow.split("  recovery-change-scope:", 1)[1].split("  sqlite-recovery-auto:", 1)[0]
        self.assertIn("fetch-depth: 0", scope_job)
        self.assertIn("git diff --name-only", scope_job)
        for path in (
            "ci/test_t0_ssh_preflight_contract.py",
            "market_data/feeder.py",
            "market_data/feeder_service.py",
            "market_data/test_feeder_recovery.py",
            "market_data/test_feeder_scheduler.py",
            "market_data/test_feeder_lifecycle.py",
        ):
            self.assertIn(path, scope_job)

    def test_sqlite_recovery_auto_requires_g1_pass_and_uploads_evidence(self):
        workflow = WORKFLOW.read_text()
        recovery_job = workflow.split("  sqlite-recovery-auto:", 1)[1].split("  manual-gate:", 1)[0]
        self.assertIn("sqlite-lease-fencing-auto", recovery_job)
        self.assertIn("recovery-change-scope", recovery_job)
        self.assertIn("needs.sqlite-lease-fencing-auto.result == 'success'", recovery_job)
        self.assertIn("needs.recovery-change-scope.outputs.changed == 'true'", recovery_job)
        self.assertIn("contents: read", recovery_job)
        self.assertIn("persist-credentials: false", recovery_job)
        self.assertIn("python -m unittest market_data.test_feeder_recovery market_data.test_feeder_scheduler market_data.test_feeder_lifecycle -v", recovery_job)
        self.assertIn("sqlite-recovery-tests.log", recovery_job)
        self.assertIn("sqlite-recovery-verdict.txt", recovery_job)
        self.assertIn("recovery-source-sha.txt", recovery_job)
        self.assertIn("actions/upload-artifact@v4", recovery_job)
        self.assertNotIn("secrets.", recovery_job)
        self.assertNotIn("ssh ", recovery_job)
        self.assertNotIn("environment:", recovery_job)

    def test_g3_data_flow_paths_trigger_push_and_pull_request(self):
        workflow = WORKFLOW.read_text()
        paths = (
            "market_data/sync.py", "market_data/api.py", "market_data/storage.py",
            "market_data/test_sync.py", "market_data/test_api.py",
            "market_data/test_e2e_data_flow.py", "freqai_bridge/context.py",
            "freqai_bridge/http_candles.py", "freqai_bridge/test_http_candles.py",
        )
        for event in ("push:", "pull_request:"):
            event_block = workflow.split("  " + event, 1)[1].split("\n\n", 1)[0]
            for path in paths:
                with self.subTest(event=event, path=path):
                    self.assertIn(path, event_block)

    def test_g2_is_rerun_as_a_required_prerequisite_for_g3_source_changes(self):
        workflow = WORKFLOW.read_text()
        recovery_scope = workflow.split("  recovery-change-scope:", 1)[1].split("  sqlite-recovery-auto:", 1)[0]
        for path in (
            "market_data/sync.py", "market_data/api.py", "market_data/storage.py",
            "market_data/test_sync.py", "market_data/test_api.py",
            "market_data/test_e2e_data_flow.py", "freqai_bridge/context.py",
            "freqai_bridge/http_candles.py", "freqai_bridge/test_http_candles.py",
        ):
            self.assertIn(path, recovery_scope)

    def test_g3_scope_detects_the_end_to_end_data_flow_surface(self):
        workflow = WORKFLOW.read_text()
        scope_job = workflow.split("  data-flow-change-scope:", 1)[1].split("  sqlite-data-flow-auto:", 1)[0]
        self.assertIn("fetch-depth: 0", scope_job)
        self.assertIn("git diff --name-only", scope_job)
        for path in (
            "market_data/sync.py", "market_data/store.py", "market_data/write_gateway.py",
            "market_data/api.py", "market_data/storage.py", "market_data/test_e2e_data_flow.py",
            "freqai_bridge/context.py", "freqai_bridge/http_candles.py",
        ):
            self.assertIn(path, scope_job)

    def test_g3_requires_g1_and_g2_pass_and_uploads_isolated_evidence(self):
        workflow = WORKFLOW.read_text()
        data_flow_job = workflow.split("  sqlite-data-flow-auto:", 1)[1].split("  manual-gate:", 1)[0]
        self.assertIn("sqlite-lease-fencing-auto", data_flow_job)
        self.assertIn("sqlite-recovery-auto", data_flow_job)
        self.assertIn("data-flow-change-scope", data_flow_job)
        self.assertIn("needs.sqlite-lease-fencing-auto.result == 'success'", data_flow_job)
        self.assertIn("needs.sqlite-recovery-auto.result == 'success'", data_flow_job)
        self.assertIn("needs.data-flow-change-scope.outputs.changed == 'true'", data_flow_job)
        self.assertIn("contents: read", data_flow_job)
        self.assertIn("persist-credentials: false", data_flow_job)
        self.assertIn("MARKET_DATA_DB: \"\"", data_flow_job)
        self.assertIn("MARKET_DATA_TOKEN: \"\"", data_flow_job)
        self.assertIn("T0_CANDLE_API_TOKEN: \"\"", data_flow_job)
        self.assertIn("python -m unittest ci.test_t0_ssh_preflight_contract market_data.test_e2e_data_flow market_data.test_sync market_data.test_api freqai_bridge.test_http_candles -v", data_flow_job)
        self.assertIn("sqlite-data-flow-tests.log", data_flow_job)
        self.assertIn("sqlite-data-flow-verdict.txt", data_flow_job)
        self.assertIn("data-flow-source-sha.txt", data_flow_job)
        self.assertIn("actions/upload-artifact@v4", data_flow_job)
        self.assertNotIn("secrets.", data_flow_job)
        self.assertNotIn("ssh ", data_flow_job)
        self.assertNotIn("environment:", data_flow_job)

    def test_g3_integration_uses_only_synthetic_exchange_and_loopback_http(self):
        source = (ROOT / "market_data/test_e2e_data_flow.py").read_text()
        self.assertIn("class SyntheticBinanceUsdM", source)
        self.assertIn("sync_window(", source)
        self.assertIn("make_server(\"127.0.0.1\", 0, application)", source)
        self.assertIn("canonical_context(", source)
        self.assertIn("COVERAGE_INCOMPLETE", source)
        self.assertNotIn("ccxt.binanceusdm(", source)
        self.assertNotIn("BINANCE_API_KEY", source)

    def test_remote_script_is_forced_command_compatible_and_read_only(self):
        script = SCRIPT.read_text()
        self.assertIn("P1_SSH_PREFLIGHT_VERSION=1", script)
        self.assertIn('mode=ro', script)
        self.assertIn("PRAGMA query_only=ON", script)
        self.assertIn("PRAGMA integrity_check", script)
        forbidden = ("systemctl restart", "systemctl start", "systemctl stop",
                     "kill ", "rm -", "sqlite3 ")
        for token in forbidden:
            self.assertNotIn(token, script)

    def test_remote_script_does_not_accept_remote_arguments(self):
        script = SCRIPT.read_text()
        self.assertNotIn('"$@"', script)
        self.assertNotIn("${{", script)


    def test_g4_probe_uses_read_only_sqlite_and_never_mutates_lease(self):
        probe = (ROOT / "ci/t0_runtime_acceptance.py").read_text()
        self.assertIn("?mode=ro", probe)
        self.assertIn("PRAGMA query_only=ON", probe)
        self.assertIn("PRAGMA integrity_check", probe)
        self.assertIn("SELECT owner, generation, expires_at_ms", probe)
        self.assertIn("SELECT open_time_ms, available_at_ms", probe)
        for forbidden in ("BEGIN IMMEDIATE", "INSERT INTO", "UPDATE feeder_leases",
                          "DELETE FROM", ".acquire(", ".heartbeat(", ".release("):
            self.assertNotIn(forbidden, probe)

    def test_g4_runtime_contract_is_path_scoped_and_requires_g1_g2_g3(self):
        workflow = WORKFLOW.read_text()
        for event in ("push:", "pull_request:"):
            event_block = workflow.split("  " + event, 1)[1].split("\n\n", 1)[0]
            self.assertIn("ci/t0_runtime_acceptance.py", event_block)
            self.assertIn("ci/test_t0_runtime_acceptance.py", event_block)

        scope = workflow.split("  g4-runtime-contract-change-scope:", 1)[1].split(
            "  sqlite-g4-runtime-contract-auto:", 1
        )[0]
        self.assertIn("fetch-depth: 0", scope)
        self.assertIn("git diff --name-only", scope)

        job = workflow.split("  sqlite-g4-runtime-contract-auto:", 1)[1].split(
            "  manual-gate:", 1
        )[0]
        for prerequisite in (
            "sqlite-lease-fencing-auto", "sqlite-recovery-auto",
            "sqlite-data-flow-auto",
        ):
            self.assertIn(prerequisite, job)
        self.assertIn("needs.sqlite-lease-fencing-auto.result == 'success'", job)
        self.assertIn("needs.sqlite-recovery-auto.result == 'success'", job)
        self.assertIn("needs.sqlite-data-flow-auto.result == 'success'", job)
        self.assertIn("contents: read", job)
        self.assertIn("persist-credentials: false", job)
        self.assertIn("python -m unittest ci.test_t0_ssh_preflight_contract ci.test_t0_runtime_acceptance -v", job)
        self.assertIn("g4-runtime-contract-tests.log", job)
        self.assertIn("g4-verdict.txt", job)
        self.assertIn("actions/upload-artifact@v4", job)
        self.assertNotIn("secrets.", job)
        self.assertNotIn("ssh ", job)
        self.assertNotIn("environment:", job)
        self.assertIn("G4_SQLITE_PROBE=DISPOSABLE_FIXTURE_ONLY", job)

        recovery_scope = workflow.split("  recovery-change-scope:", 1)[1].split(
            "  sqlite-recovery-auto:", 1
        )[0]
        data_flow_scope = workflow.split("  data-flow-change-scope:", 1)[1].split(
            "  sqlite-data-flow-auto:", 1
        )[0]
        for probe_path in ("ci/t0_runtime_acceptance.py", "ci/test_t0_runtime_acceptance.py"):
            self.assertIn(probe_path, recovery_scope)
            self.assertIn(probe_path, data_flow_scope)

if __name__ == "__main__":
    unittest.main()
