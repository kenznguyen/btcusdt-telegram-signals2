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
