"""Static GitHub Actions release-gate tests for the T0 operational contract.

These tests inspect repository configuration and source only. They never start
the feeder or execute T0 runtime/SIGKILL suites.
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

    def test_github_actions_registers_all_green_t0_test_groups(self):
        self.assert_check_passes("github_actions_green_test_inventory")

    def test_github_actions_preserves_exact_source_sha_artifacts(self):
        self.assert_check_passes("source_sha_provenance")

    def test_release_gate_is_scoped_to_its_own_branch_and_paths(self):
        self.assert_check_passes("release_gate_scope")

    def test_release_gate_does_not_execute_runtime_or_sigkill_suites(self):
        self.assert_check_passes("release_gate_is_static_only")

    def test_manual_t0_acceptance_gates_are_preserved(self):
        self.assert_check_passes("manual_gates_preserved")

    def test_t0_codemagic_workflows_are_retired(self):
        self.assert_check_passes("codemagic_t0_retirement")

    def test_canonical_source_is_binance_usdm_closed_candles(self):
        self.assert_check_passes("canonical_market_contract")

    def test_production_feeder_uses_sqlite_gateway_fencing(self):
        self.assert_check_passes("sqlite_gateway_fencing_contract")


    def test_sync_and_runtime_require_concrete_gateway(self):
        self.assert_check_passes("concrete_gateway_boundary")

    def test_observation_and_lease_runtime_clocks_are_independent(self):
        self.assert_check_passes("observation_and_lease_clock_separation")

    def test_runtime_storage_fails_closed_without_implicit_schema_creation(self):
        self.assert_check_passes("runtime_storage_fail_closed")


if __name__ == "__main__":
    unittest.main()
