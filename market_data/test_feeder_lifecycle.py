import unittest
from unittest.mock import Mock
from market_data.feeder import FeederConfig, FeederRuntime

class RuntimeLifecycleTest(unittest.TestCase):
    def test_stop_stops_scheduler_and_releases_lease(self):
        scheduler, leases = Mock(), Mock()
        runtime = FeederRuntime(config=FeederConfig(), scheduler=scheduler, lease_store=leases, owner_id='worker-A')
        runtime.lease_generation = 4
        runtime.stop()
        scheduler.stop.assert_called_once()
        leases.release.assert_called_once_with('worker-A', 4)
