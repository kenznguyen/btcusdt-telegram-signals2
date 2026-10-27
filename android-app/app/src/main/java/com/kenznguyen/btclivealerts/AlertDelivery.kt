package com.kenznguyen.btclivealerts

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.content.SharedPreferences
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import java.util.Calendar

internal fun alertAllowed(prefs: SharedPreferences, direction: String?, enabledPreference: String?): Boolean =
    AlertPolicy.allows(prefs.getBoolean("alerts_enabled", true),
        enabledPreference == null || prefs.getBoolean(enabledPreference, true), direction,
        prefs.getBoolean("alert_long", true), prefs.getBoolean("alert_short", true))

private fun quietHours(prefs: SharedPreferences): Boolean = AlertPolicy.isQuietHour(
    prefs.getBoolean("quiet_hours_enabled", false), Calendar.getInstance().get(Calendar.HOUR_OF_DAY),
    prefs.getInt("quiet_start_hour", 23), prefs.getInt("quiet_end_hour", 7))

/** Returns true when accepted (including queued/suppressed during quiet hours). */
internal fun deliverAlert(
    context: Context, prefs: SharedPreferences, key: String, title: String, body: String, source: String,
    direction: String? = null, enabledPreference: String? = null, recordHistory: Boolean = true
): Boolean {
    if (!alertAllowed(prefs, direction, enabledPreference)) return false
    if (recordHistory) appendAlertHistory(prefs, title, body, source)
    if (quietHours(prefs)) {
        if (prefs.getBoolean("alert_catch_up_after_quiet", true)) synchronized(prefs) {
            val queue = prefs.getStringSet("quiet_alert_queue", emptySet())?.toMutableSet() ?: mutableSetOf()
            queue.add(QueuedAlert(key, title, body, source, direction, enabledPreference).encode())
            prefs.edit().putStringSet("quiet_alert_queue", queue).apply()
        }
        return true
    }
    val manager = NotificationManagerCompat.from(context)
    if (!manager.areNotificationsEnabled()) return true
    val sound = prefs.getBoolean("alert_sound", true)
    val vibration = prefs.getBoolean("alert_vibration", true)
    // On API 26+, channel settings control sound/vibration, not builder setters.
    val channelId = "strategy_alerts_s${if (sound) 1 else 0}_v${if (vibration) 1 else 0}"
    val channel = NotificationChannel(channelId,
        "Cảnh báo · ${if (sound) "có âm" else "không âm"} · ${if (vibration) "rung" else "không rung"}",
        NotificationManager.IMPORTANCE_HIGH)
    if (!sound) channel.setSound(null, null)
    if (vibration) channel.vibrationPattern = longArrayOf(0, 250, 120, 250)
    channel.enableVibration(vibration)
    (context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager).createNotificationChannel(channel)
    val notification = NotificationCompat.Builder(context, channelId)
        .setSmallIcon(android.R.drawable.ic_dialog_info).setContentTitle(title).setContentText(body)
        .setStyle(NotificationCompat.BigTextStyle().bigText(body))
        .setPriority(NotificationCompat.PRIORITY_HIGH).setAutoCancel(true).build()
    try { manager.notify(key.hashCode() and 0x7fffffff, notification) } catch (_: SecurityException) { }
    return true
}

internal fun flushQueuedAlerts(context: Context, prefs: SharedPreferences) {
    if (!prefs.getBoolean("alerts_enabled", true) || quietHours(prefs) ||
        !prefs.getBoolean("alert_catch_up_after_quiet", true)) return
    val pending = synchronized(prefs) { prefs.getStringSet("quiet_alert_queue", emptySet())?.toSet() ?: emptySet() }
    val processed = mutableSetOf<String>()
    for (value in pending) {
        if (!prefs.getBoolean("alerts_enabled", true) || quietHours(prefs) ||
            !prefs.getBoolean("alert_catch_up_after_quiet", true)) break
        val alert = QueuedAlert.decode(value)
        if (alert == null) {
            processed.add(value)
            continue
        }
        deliverAlert(context, prefs, alert.key, "Cảnh báo gửi bù · " + alert.title, alert.body, alert.source,
            alert.direction, alert.enabledPreference, recordHistory = !alert.historyRecorded)
        processed.add(value)
    }
    synchronized(prefs) {
        val remaining = prefs.getStringSet("quiet_alert_queue", emptySet())?.toMutableSet() ?: mutableSetOf()
        remaining.removeAll(processed)
        prefs.edit().putStringSet("quiet_alert_queue", remaining).apply()
    }
}
