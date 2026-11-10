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

if __name__ == "__main__":
    unittest.main()
