"""Isolated regression for the Core quality projection ordering defect.

T0 and the rest of the five-layer runtime are intentionally outside this test.
Only import-time adapters are stubbed; the projection function itself is real.
"""
import sys
import types
import unittest
from unittest.mock import patch


def _module(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


# Main currently carries the common API facade without the independent T0
# implementation package. Stub only import-time adapter symbols so this
# projection-only test does not copy, start, or connect to T0.
_module("market_data.api", candle_query=lambda *args, **kwargs: None)
_module("market_data.postgres", StoreUnavailable=type("StoreUnavailable", (Exception,), {}))
_module("market_data.storage", create_store_from_env=lambda *args, **kwargs: None)
_module("pipeline.values", stamp=lambda value: int(value) if value is not None else None)

paper_execution = types.ModuleType("paper_execution")
paper_execution.__path__ = []
sys.modules["paper_execution"] = paper_execution
_module("paper_execution.equity", parse_limits=lambda environ: None)

import pipeline.api as common_api  # noqa: E402


NOW = 1_800_000_000_000


class CoreApiQualitySnapshotRegressionTest(unittest.TestCase):
    def test_quality_projection_uses_bundle_preview_and_t1_book_evidence(self):
        window = {
            "coverage": {"complete": True},
            "candles": [{} for _ in range(500)],
            "datasetVersion": "dataset-v1",
        }
        preview = {
            "action": "WAIT",
            "reason": "CORE_NO_ENTRY",
            "indicators": {
                "rsiM15": "45",
                "adxM15": "20",
                "plusDiH1": "22",
                "minusDiH1": "18",
                "adxH1": "25",
            },
            "sourceEvidence": {"t1SnapshotId": "sha256:" + "b" * 64},
        }
        with (
            patch.object(
                common_api,
                "context",
                return_value={
                    "intelligence": None,
                    "book": None,
                    "prediction": None,
                    "errors": {},
                },
            ),
            patch.object(common_api, "market_window", return_value=window),
            patch.object(common_api, "core_runtime_preview", return_value=preview) as core_preview,
        ):
            result = common_api.quality_snapshot(NOW)

        streams = {item["name"]: item for item in result["streams"]}
        self.assertEqual(streams["Strategy Core producer"]["status"], "READY")
        self.assertEqual(streams["T1 Order Book V1"]["status"], "READY")
        self.assertEqual(
            streams["T1 Order Book V1"]["snapshotId"],
            preview["sourceEvidence"]["t1SnapshotId"],
        )
        core_preview.assert_called_once_with(NOW)


if __name__ == "__main__":
    unittest.main(verbosity=2)
