package com.kenznguyen.btclivealerts

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class AlertHistoryCodecTest {
    private fun item(timestamp: Long) = JSONObject().put("title", "event-$timestamp").put("timestamp", timestamp)

    @Test fun newAlertsKeepTheNewestHundredInDescendingOrder() {
        var history = "[]"
        for (timestamp in 1L..103L) history = AlertHistoryCodec.prepend(history, item(timestamp))
        val result = JSONArray(history)
        assertEquals(100, result.length())
        assertEquals((103L downTo 4L).toList(), (0 until result.length()).map { result.getJSONObject(it).getLong("timestamp") })
        assertEquals("event-102", result.getJSONObject(1).getString("title"))
    }

    @Test fun addingAlertRepairsOldReversedHistory() {
        val result = JSONArray(AlertHistoryCodec.prepend("[{\"timestamp\":3},{\"timestamp\":1},{\"timestamp\":2}]", item(4)))
        assertEquals(listOf(4L, 3L, 2L, 1L), (0 until result.length()).map { result.getJSONObject(it).getLong("timestamp") })
    }

    @Test fun sameTimestampPreservesNewestInsertionAndMalformedEntriesDoNotEraseGoodHistory() {
        val first = item(10).put("title", "first")
        val second = item(10).put("title", "second")
        val result = JSONArray(AlertHistoryCodec.prepend(JSONArray().put(first).put("bad entry").toString(), second))
        assertEquals(2, result.length())
        assertEquals("second", result.getJSONObject(0).getString("title"))
        assertEquals("first", result.getJSONObject(1).getString("title"))
        assertEquals(1, JSONArray(AlertHistoryCodec.prepend("broken JSON", item(11))).length())
    }
}
