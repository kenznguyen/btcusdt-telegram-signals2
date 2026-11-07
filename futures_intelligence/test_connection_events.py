import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from futures_intelligence.connection_events import load_and_validate_connection_events


SOURCE = "bc4f0ef633fbeee4a49defd72827f17162693805"
SESSION = "collector-session-001"
START = 1_700_000_020_000
END = START + 60_000
GAP = 30_000


class ConnectionEventContractTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

    def event(self, event_id, event_type, at, **extra):
        return {
            "schemaVersion": 1,
            "eventId": event_id,
            "sourceCommit": SOURCE,
            "sessionId": SESSION,
            "connectionId": "conn-1",
            "batchId": 0,
            "route": "market",
            "eventType": event_type,
            "eventAtMs": at,
            **extra,
        }

    def healthy_events(self):
        return [
            self.event("e1", "CONNECTED", START - 10_000),
            self.event("e2", "PING_SENT", START - 1_000, heartbeatId="hb-1"),
            self.event("e3", "PONG_RECEIVED", START, heartbeatId="hb-1"),
            self.event("e4", "PING_SENT", START + 20_000, heartbeatId="hb-2"),
            self.event("e5", "PONG_RECEIVED", START + 21_000, heartbeatId="hb-2"),
            self.event("e6", "PING_SENT", START + 40_000, heartbeatId="hb-3"),
            self.event("e7", "PONG_RECEIVED", START + 41_000, heartbeatId="hb-3"),
            self.event("e8", "PING_SENT", END - 5_000, heartbeatId="hb-4"),
            self.event("e9", "PONG_RECEIVED", END - 4_000, heartbeatId="hb-4"),
        ]

    def write(self, events, name="events.jsonl"):
        path = Path(self.directory.name, name)
        raw = "".join(json.dumps(item, sort_keys=True, separators=(",", ":")) + "\\n" for item in events).encode()
        path.write_bytes(raw)
        return path, hashlib.sha256(raw).hexdigest()

    def validate(self, events, **kwargs):
        path, digest = self.write(events)
        return load_and_validate_connection_events(
            path,
            expected_sha256=digest,
            expected_source_commit=SOURCE,
            expected_session_id=SESSION,
            window_start_ms=START,
            window_end_ms=END,
            max_heartbeat_gap_ms=GAP,
            **kwargs,
        )

    def test_healthy_connection_requires_paired_pongs_across_the_entire_window(self):
        result = self.validate(self.healthy_events())
        self.assertEqual(result["connectionStatus"], "VERIFIED_CONNECTED")
        self.assertEqual(result["verifiedConnections"], 1)
        self.assertEqual(result["connections"][0]["batchId"], 0)
        self.assertEqual(result["connections"][0]["route"], "market")

    def test_missing_pong_or_excessive_heartbeat_gap_fails_closed(self):
        events = self.healthy_events()
        events = [item for item in events if item["eventId"] != "e7"]
        result = self.validate(events)
        self.assertEqual(result["connectionStatus"], "HEARTBEAT_GAP")

    def test_remote_close_inside_half_open_window_is_disconnected(self):
        events = self.healthy_events()
        events.append(self.event("e10", "DISCONNECTED", START + 50_000, reason="REMOTE_CLOSE"))
        result = self.validate(events)
        self.assertEqual(result["connectionStatus"], "DISCONNECTED")

    def test_transport_error_is_recorded_as_disconnect_reason(self):
        events = self.healthy_events()
        events.append(self.event("e10", "DISCONNECTED", START + 50_000, reason="TRANSPORT_ERROR"))
        result = self.validate(events)
        self.assertEqual(result["connections"][0]["disconnectReason"], "TRANSPORT_ERROR")

    def test_reconnect_schedule_requires_increasing_attempt_and_bounded_delay(self):
        events = self.healthy_events()
        events.extend([
            self.event("e10", "DISCONNECTED", START + 50_000, reason="REMOTE_CLOSE"),
            self.event("e11", "RECONNECT_SCHEDULED", START + 51_000, attempt=1, delayMs=2_000),
        ])
        result = self.validate(events)
        self.assertEqual(result["connections"][0]["reconnectAttempt"], 1)
        self.assertEqual(result["connections"][0]["reconnectDelayMs"], 2_000)

    def test_new_connection_after_reconnect_is_a_distinct_connection_identity(self):
        events = self.healthy_events()
        events.extend([
            self.event("e10", "DISCONNECTED", START + 50_000, reason="REMOTE_CLOSE"),
            self.event("e11", "RECONNECT_SCHEDULED", START + 51_000, attempt=1, delayMs=2_000),
        ])
        recovered = self.event("e12", "CONNECTED", END + 1_000)
        recovered["connectionId"] = "conn-2"
        events.append(recovered)
        result = self.validate(events)
        self.assertEqual(result["connections"][0]["connectionId"], "conn-1")
        self.assertEqual(result["connections"][0]["connectionStatus"], "DISCONNECTED")
        self.assertEqual(result["connections"][1]["connectionId"], "conn-2")

    def test_session_restart_cannot_be_spliced_into_one_continuous_session(self):
        events = self.healthy_events()
        restarted = dict(events[-1])
        restarted["eventId"] = "restart"
        restarted["sessionId"] = "collector-session-002"
        events.append(restarted)
        with self.assertRaises(ValueError):
            self.validate(events)

    def test_rejects_out_of_order_or_duplicate_event_ids(self):
        events = self.healthy_events()
        events[4], events[5] = events[5], events[4]
        with self.assertRaises(ValueError):
            self.validate(events)
        duplicate = self.healthy_events()
        duplicate[-1]["eventId"] = duplicate[0]["eventId"]
        with self.assertRaises(ValueError):
            self.validate(duplicate)

    def test_rejects_unmatched_pong_and_duplicate_ping_identity(self):
        events = self.healthy_events()
        events[2]["heartbeatId"] = "unknown"
        with self.assertRaises(ValueError):
            self.validate(events)
        duplicate = self.healthy_events()
        duplicate[3]["heartbeatId"] = "hb-1"
        with self.assertRaises(ValueError):
            self.validate(duplicate)

    def test_rejects_tampered_event_file_checksum(self):
        path, digest = self.write(self.healthy_events())
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaises(ValueError):
            load_and_validate_connection_events(
                path, expected_sha256=digest, expected_source_commit=SOURCE,
                expected_session_id=SESSION, window_start_ms=START,
                window_end_ms=END, max_heartbeat_gap_ms=GAP,
            )

    def test_missing_expected_route_remains_unverifiable(self):
        result = self.validate(
            self.healthy_events(),
            expected_connections=[{"batchId": 0, "route": "public"}],
        )
        self.assertEqual(result["connectionStatus"], "UNVERIFIABLE")
        self.assertEqual(result["verifiedConnections"], 0)


if __name__ == "__main__":
    unittest.main()
