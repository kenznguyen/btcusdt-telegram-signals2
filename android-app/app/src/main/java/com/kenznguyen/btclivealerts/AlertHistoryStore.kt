package com.kenznguyen.btclivealerts

import android.content.SharedPreferences
import org.json.JSONArray
import org.json.JSONObject

internal object AlertHistoryCodec {
    fun prepend(historyJson: String?, item: JSONObject, limit: Int = 100): String {
        require(limit > 0)
        val history = runCatching { JSONArray(historyJson ?: "[]") }.getOrDefault(JSONArray())
        val entries = mutableListOf(item)
        for (i in 0 until history.length()) history.optJSONObject(i)?.let(entries::add)
        // Sorting also repairs the order of history written by older app versions.
        val updated = JSONArray()
        entries.sortedByDescending { it.optLong("timestamp") }.take(limit).forEach { updated.put(it) }
        return updated.toString()
    }
}

internal fun appendAlertHistory(prefs: SharedPreferences, title: String, body: String, source: String) {
    synchronized(prefs) {
        val item = JSONObject().put("title", title).put("body", body)
            .put("timestamp", System.currentTimeMillis()).put("source", source)
        prefs.edit().putString("notification_history_json", AlertHistoryCodec.prepend(
            prefs.getString("notification_history_json", "[]"), item
        )).apply()
    }
}
