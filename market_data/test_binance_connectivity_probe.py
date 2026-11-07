"""Offline contracts for the read-only Binance USD-M connectivity probe."""
import base64
import hashlib
import unittest
from unittest.mock import Mock, patch
from urllib.error import URLError

from market_data.binance_connectivity_probe import (
    classify_http_status, parse_http_upgrade, parse_server_frame,
    _receive_kline_event, _rest_request, probe_websocket, validate_exchange_info,
    validate_kline_event, validate_klines, validate_server_time,
)


class HttpStatusClassificationTests(unittest.TestCase):
    def test_success_is_reported_as_reachable(self):
        self.assertEqual(classify_http_status(200), "REACHABLE")

    def test_http_451_is_reported_as_network_policy_block(self):
        self.assertEqual(classify_http_status(451), "NETWORK_POLICY_BLOCKED")

    def test_rate_limit_is_not_misreported_as_network_unreachable(self):
        self.assertEqual(classify_http_status(429), "RATE_LIMITED")

    def test_authentication_and_server_errors_remain_distinct(self):
        self.assertEqual(classify_http_status(401), "AUTH_OR_PERMISSION_ERROR")
        self.assertEqual(classify_http_status(503), "REMOTE_SERVER_ERROR")


class RestPayloadContractTests(unittest.TestCase):
    def test_exchange_time_requires_integer_milliseconds(self):
        self.assertTrue(validate_server_time({"serverTime": 1793999700000}))
        self.assertFalse(validate_server_time({"serverTime": "1793999700000"}))
        self.assertFalse(validate_server_time({"serverTime": -1}))

    def test_exchange_info_requires_active_linear_usdt_btcusdt_perpetual(self):
        payload = {"symbols": [{
            "symbol": "BTCUSDT", "status": "TRADING", "contractType": "PERPETUAL",
            "baseAsset": "BTC", "quoteAsset": "USDT", "marginAsset": "USDT",
        }]}
        self.assertTrue(validate_exchange_info(payload))
        payload["symbols"][0]["contractType"] = "CURRENT_QUARTER"
        self.assertFalse(validate_exchange_info(payload))

    def test_kline_requires_valid_closed_ohlcv_row(self):
        row = [1793999700000, "100", "110", "90", "105", "2",
               1794000599999, "200", 3, "1", "100", "0"]
        self.assertTrue(validate_klines([row], now_ms=1794000600000, interval_ms=900000))
        self.assertFalse(validate_klines([row], now_ms=1794000500000, interval_ms=900000))
        invalid = list(row)
        invalid[2] = "80"
        self.assertFalse(validate_klines([invalid], now_ms=1794000600000, interval_ms=900000))
        h1 = [1793998800000, "100", "110", "90", "105", "2",
              1794002399999, "200", 3, "1", "100", "0"]
        self.assertTrue(validate_klines([h1], now_ms=1794002400000, interval_ms=3600000))


class WebSocketHandshakeTests(unittest.TestCase):
    def test_event_must_be_btcusdt_15m_kline(self):
        event = {"e": "kline", "s": "BTCUSDT", "k": {"s": "BTCUSDT", "i": "15m"}}
        self.assertTrue(validate_kline_event(event))
        event["k"]["i"] = "1m"
        self.assertFalse(validate_kline_event(event))

    def test_valid_upgrade_requires_correct_accept_digest(self):
        key = base64.b64encode(b"probe-key-123456").decode("ascii")
        expected = base64.b64encode(
            hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()
        ).decode("ascii")
        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {expected}\r\n\r\n"
        ).encode()
        self.assertTrue(parse_http_upgrade(response, key)[0])

    def test_invalid_upgrade_is_rejected(self):
        response = b"HTTP/1.1 451 Unavailable For Legal Reasons\r\n\r\n"
        self.assertFalse(parse_http_upgrade(response, "dGhlIHNhbXBsZSBub25jZQ==")[0])

    def test_server_text_frame_is_decoded_without_accepting_masked_frames(self):
        payload = b'{"e":"kline","s":"BTCUSDT"}'
        frame = bytes([0x81, len(payload)]) + payload
        opcode, decoded, consumed = parse_server_frame(frame)
        self.assertEqual(opcode, 1)
        self.assertEqual(decoded, payload)
        self.assertEqual(consumed, len(frame))
        with self.assertRaises(ValueError):
            parse_server_frame(bytes([0x81, 0x80 | len(payload)]) + payload)


class WebSocketControlFrameTests(unittest.TestCase):
    def test_ping_is_answered_with_masked_pong_before_kline_event(self):
        ping_payload = b"server-heartbeat"
        event_payload = b'{"e":"kline","s":"BTCUSDT","k":{"s":"BTCUSDT","i":"15m"}}'
        ping_frame = bytes([0x89, len(ping_payload)]) + ping_payload
        event_frame = bytes([0x81, len(event_payload)]) + event_payload

        class FakeSocket:
            def __init__(self):
                self.chunks = [ping_frame, event_frame]
                self.sent = []

            def recv(self, _size):
                return self.chunks.pop(0) if self.chunks else b""

            def sendall(self, data):
                self.sent.append(data)

        secure = FakeSocket()
        result = _receive_kline_event(secure)

        self.assertEqual(result, event_payload)
        self.assertEqual(len(secure.sent), 1)
        frame = secure.sent[0]
        self.assertEqual(frame[0], 0x8A)
        self.assertTrue(frame[1] & 0x80)
        mask = frame[2:6]
        length = frame[1] & 0x7F
        decoded = bytes(value ^ mask[index % 4]
                        for index, value in enumerate(frame[6:6 + length]))
        self.assertEqual(decoded, ping_payload)

    def test_pong_is_ignored_while_waiting_for_kline_event(self):
        event_payload = b'{"e":"kline","s":"BTCUSDT","k":{"s":"BTCUSDT","i":"15m"}}'
        pong_frame = bytes([0x8A, 0])
        event_frame = bytes([0x81, len(event_payload)]) + event_payload

        class FakeSocket:
            def __init__(self):
                self.chunks = [pong_frame + event_frame]

            def recv(self, _size):
                return self.chunks.pop(0) if self.chunks else b""

            def sendall(self, _data):
                raise AssertionError("Pong must not trigger a response")

        self.assertEqual(_receive_kline_event(FakeSocket()), event_payload)

    def test_close_frame_before_kline_is_reported(self):
        class FakeSocket:
            def recv(self, _size):
                return bytes([0x88, 0])

            def sendall(self, _data):
                raise AssertionError("Close must not trigger a response")

        with self.assertRaisesRegex(ConnectionError, "closed before first event"):
            _receive_kline_event(FakeSocket())


class RestErrorDiagnosticsTests(unittest.TestCase):
    def test_url_error_reason_is_preserved_without_hiding_classification(self):
        opener = Mock()
        opener.open.side_effect = URLError(ConnectionResetError("connection reset by peer"))

        result, payload = _rest_request(opener, "exchange_info", "/fapi/v1/exchangeInfo", 5)

        self.assertIsNone(payload)
        self.assertEqual(result["classification"], "CONNECTION_ERROR")
        self.assertEqual(result["error_type"], "URLError")
        self.assertEqual(result["error_reason_type"], "ConnectionResetError")
        self.assertIn("connection reset by peer", result["error_detail"])


if __name__ == "__main__":
    unittest.main()
