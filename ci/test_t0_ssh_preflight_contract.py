"""Static contract tests for the P1 read-only Scaleway SSH preflight."""

from pathlib import Path
import re
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
        self.assertIn('api_state="NOT_LISTENING"', self.source)
        self.assertIn('api_state="NON_LOOPBACK_LISTENER"', self.source)
        self.assertIn('api_state="LOOPBACK_LISTENER"', self.source)
        self.assertIn('[[ "$api_state" != "NON_LOOPBACK_LISTENER" ]] || exit 1', self.source)

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


if __name__ == "__main__":
    unittest.main()
