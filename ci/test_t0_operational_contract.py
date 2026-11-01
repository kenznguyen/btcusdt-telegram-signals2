"""Static release-gate tests for the T0 operational contract.

These tests inspect repository configuration and source only. They never start
the feeder or execute any T0 runtime, SIGKILL, or regression test suite.
"""
import unittest
from pathlib import Path

from ci.t0_operational_contract import audit_contract

ROOT = Path(__file__).resolve().parents[1]


class T0OperationalContractReleaseGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checks = {item["id"]: item for item in audit_contract(ROOT)}

    def assert_check_passes(self, check_id):
        self.assertIn(check_id, self.checks)
        self.assertEqual(
            self.checks[check_id]["status"],
            "PASS",
            self.checks[check_id]["detail"],
        )

    def test_codemagic_registers_all_green_t0_test_groups(self):
        self.assert_check_passes("green_test_inventory")

    def test_green_workflows_preserve_exact_source_sha_artifacts(self):
        self.assert_check_passes("source_sha_provenance")

    def test_release_gate_is_scoped_to_its_own_branch_and_files(self):
        self.assert_check_passes("release_gate_scope")

    def test_release_gate_does_not_execute_runtime_or_sigkill_suites(self):
        self.assert_check_passes("release_gate_is_static_only")

    def test_canonical_source_is_binance_usdm_closed_candles(self):
        self.assert_check_passes("canonical_market_contract")

    def test_production_feeder_requires_sqlite_atomic_fencing(self):
        self.assert_check_passes("sqlite_atomic_fencing_contract")


if __name__ == "__main__":
    unittest.main()
