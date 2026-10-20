"""Telegram webhook delivery and restart-deduplication regression tests."""
import json
import os
import tempfile
import unittest
from unittest.mock import patch

import app as bridge


class TelegramBridgeRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.state_path = os.path.join(self.tempdir.name, "telegram_seen_updates.json")
        self.original_updates = set(bridge._seen_updates)
        self.original_order = list(bridge._seen_order)
        self.original_processing = set(bridge._processing_updates)
        bridge._seen_updates.clear()
        bridge._seen_order.clear()
        bridge._processing_updates.clear()
        self.addCleanup(self._restore_seen)

    def _restore_seen(self):
        bridge._seen_updates.clear()
        bridge._seen_updates.update(self.original_updates)
        bridge._seen_order.clear()
        bridge._seen_order.extend(self.original_order)
        bridge._processing_updates.clear()
        bridge._processing_updates.update(self.original_processing)

    def _post(self, update_id=8675309, text="/status", secret="test-secret"):
        return bridge.app.test_client().post(
            "/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": secret},
            json={
                "update_id": update_id,
                "message": {"chat": {"id": "12345"}, "text": text},
            },
        )

    def test_dispatch_failure_is_not_marked_handled_and_can_retry(self):
        with patch.object(bridge, "TELEGRAM_WEBHOOK_SECRET", "test-secret"), \
             patch.object(bridge, "TELEGRAM_CHAT_ID", "12345"), \
             patch.object(bridge, "BOT_STATE_DIR", self.tempdir.name), \
             patch.object(bridge, "TELEGRAM_UPDATE_STATE_FILE", self.state_path), \
             patch.object(bridge, "dispatch_github",
                          side_effect=[RuntimeError("temporary API failure"), None]) as dispatch, \
             patch.object(bridge, "telegram_send", return_value=None):
            failed = self._post()
            self.assertEqual(failed.status_code, 503)
            self.assertNotIn("8675309", bridge._seen_updates)
            retried = self._post()
            self.assertEqual(retried.status_code, 200)
            self.assertEqual(dispatch.call_count, 2)
            self.assertIn("8675309", bridge._seen_updates)

    def test_successful_dispatch_is_persistently_deduplicated(self):
        with patch.object(bridge, "TELEGRAM_WEBHOOK_SECRET", "test-secret"), \
             patch.object(bridge, "TELEGRAM_CHAT_ID", "12345"), \
             patch.object(bridge, "BOT_STATE_DIR", self.tempdir.name), \
             patch.object(bridge, "TELEGRAM_UPDATE_STATE_FILE", self.state_path), \
             patch.object(bridge, "dispatch_github", return_value=None) as dispatch, \
             patch.object(bridge, "telegram_send", return_value=None):
            first = self._post()
            self.assertEqual(first.status_code, 200)
            self.assertEqual(dispatch.call_count, 1)
            self.assertTrue(os.path.exists(self.state_path))
            self.assertIn("8675309", json.loads(open(self.state_path, encoding="utf-8").read()))
            duplicate = self._post()
            self.assertEqual(duplicate.status_code, 200)
            self.assertTrue(duplicate.get_json()["duplicate"])
            self.assertEqual(dispatch.call_count, 1)

    def test_concurrent_duplicate_update_cannot_claim_twice(self):
        self.assertTrue(bridge.claim_update("same-update"))
        self.assertFalse(bridge.claim_update("same-update"))
        bridge.release_update("same-update")
        self.assertTrue(bridge.claim_update("same-update"))
        bridge.release_update("same-update")

    def test_invalid_webhook_secret_is_rejected(self):
        with patch.object(bridge, "TELEGRAM_WEBHOOK_SECRET", "expected-secret"):
            response = self._post(secret="wrong-secret")
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main(verbosity=2)
