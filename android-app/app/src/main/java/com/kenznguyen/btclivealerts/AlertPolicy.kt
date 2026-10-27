package com.kenznguyen.btclivealerts

import org.json.JSONObject

internal object AlertPolicy {
    fun allows(masterEnabled: Boolean, typeEnabled: Boolean, direction: String?, longEnabled: Boolean, shortEnabled: Boolean): Boolean {
        if (!masterEnabled || !typeEnabled) return false
        return when (direction?.uppercase()) {
            "BUY", "LONG", "EARLY BUY" -> longEnabled
            "SELL", "SHORT", "EARLY SELL" -> shortEnabled
            else -> true
        }
    }

    fun isQuietHour(enabled: Boolean, hour: Int, start: Int, end: Int): Boolean {
        if (!enabled) return false
        return if (start == end) true else if (start < end) hour >= start && hour < end else hour >= start || hour < end
    }
}

internal data class QueuedAlert(
    val key: String,
    val title: String,
    val body: String,
    val source: String,
    val direction: String? = null,
    val enabledPreference: String? = null,
    val historyRecorded: Boolean = true
) {
    fun encode(): String = JSONObject().put("key", key).put("title", title).put("body", body)
        .put("source", source).put("direction", direction ?: JSONObject.NULL)
        .put("enabledPreference", enabledPreference ?: JSONObject.NULL)
        .put("historyRecorded", historyRecorded).toString()

    companion object {
        fun decode(value: String): QueuedAlert? {
            if (value.startsWith("{")) return runCatching {
                val item = JSONObject(value)
                QueuedAlert(item.getString("key"), item.getString("title"), item.getString("body"),
                    item.optString("source", "Chiến lược"),
                    if (item.isNull("direction")) null else item.optString("direction").takeIf { it.isNotBlank() },
                    if (item.isNull("enabledPreference")) null else item.optString("enabledPreference").takeIf { it.isNotBlank() },
                    item.optBoolean("historyRecorded", false))
            }.getOrNull()
            // Preserve catch-up entries saved by previous app versions.
            val parts = value.split("|", limit = 3)
            if (parts.size != 3) return null
            val direction = when {
                parts[2].startsWith("LONG") -> "LONG"
                parts[2].startsWith("SHORT") -> "SHORT"
                else -> null
            }
            val preference = when {
                parts[1].contains("ENTRY") -> "alert_entry"
                parts[1].contains("DCA") -> "alert_dca"
                parts[1].contains("TAKE PROFIT") -> "alert_take_profit"
                parts[1].contains("SOFT SL") -> "alert_soft_sl"
                parts[1].contains("EMERGENCY SL") -> "alert_emergency_sl"
                else -> null
            }
            return QueuedAlert(parts[0], parts[1], parts[2], "Chiến lược", direction, preference,
                historyRecorded = parts[0].startsWith("chart:"))
        }
    }
}
