package com.kenznguyen.btclivealerts

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray
import java.util.concurrent.TimeUnit
import kotlin.math.abs
import kotlin.math.max

data class Candle(
    val openTime: Long,
    val open: Double,
    val high: Double,
    val low: Double,
    val close: Double,
    val volume: Double,
    val closed: Boolean
)

data class Indicators(val rsi: Double?, val adx: Double?, val plusDi: Double?, val minusDi: Double?)

class MarketEngine {
    private val client = OkHttpClient.Builder()
        .callTimeout(12, TimeUnit.SECONDS)
        .build()

    suspend fun fetchCandles(interval: String, limit: Int = 200): List<Candle> =
        withContext(Dispatchers.IO) {
            val url = "https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=$interval&limit=$limit"
            val request = Request.Builder().url(url).build()
            client.newCall(request).execute().use { response ->
                check(response.isSuccessful) { "Binance Futures HTTP ${response.code}" }
                val array = JSONArray(response.body?.string() ?: "[]")
                (0 until array.length()).map { i ->
                    val row = array.getJSONArray(i)
                    Candle(
                        openTime = row.getLong(0),
                        open = row.getDouble(1),
                        high = row.getDouble(2),
                        low = row.getDouble(3),
                        close = row.getDouble(4),
                        volume = row.getDouble(5),
                        closed = row.getLong(6) < System.currentTimeMillis()
                    )
                }
            }
        }

    suspend fun fetchHistory(interval: String, days: Int): List<Candle> = withContext(Dispatchers.IO) {
        require(days in setOf(7, 30, 90, 180)) { "Chọn 7, 30, 90 hoặc 180 ngày" }
        val step = when (interval) { "15m" -> 900000L; "1h" -> 3600000L; else -> error("Khung thời gian không hỗ trợ") }
        val end = System.currentTimeMillis()
        val start = end - days.toLong() * 86400000L
        val candles = sortedMapOf<Long, Candle>()
        var cursor = start
        var pages = 0
        while (cursor < end && pages < 40) {
            val url = "https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=" + interval + "&limit=1500&startTime=" + cursor + "&endTime=" + end
            val request = Request.Builder().url(url).build()
            val page = client.newCall(request).execute().use { response ->
                check(response.isSuccessful) { "Binance Futures HTTP " + response.code }
                val array = JSONArray(response.body?.string() ?: "[]")
                (0 until array.length()).map { i ->
                    val row = array.getJSONArray(i)
                    Candle(row.getLong(0), row.getDouble(1), row.getDouble(2), row.getDouble(3), row.getDouble(4), row.getDouble(5), row.getLong(6) < System.currentTimeMillis())
                }
            }
            if (page.isEmpty()) break
            page.forEach { candles[it.openTime] = it }
            val next = page.last().openTime + step
            if (next <= cursor) break
            cursor = next
            pages++
            if (page.size < 1500) break
        }
        candles.values.filter { it.closed }
    }
    suspend fun fetchMarkPrice(): Double = withContext(Dispatchers.IO) {
        val request = Request.Builder()
            .url("https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT")
            .build()
        client.newCall(request).execute().use { response ->
            check(response.isSuccessful) { "Binance Futures HTTP ${response.code}" }
            org.json.JSONObject(response.body?.string() ?: "{}").getString("markPrice").toDouble()
        }
    }

    // Wilder-style RSI. ADX is computed from directional movement and Wilder smoothing.
    fun indicators(candles: List<Candle>, period: Int = 14): Indicators {
        if (candles.size < period * 2 + 2) return Indicators(null, null, null, null)
        val closes = candles.map { it.close }
        var gain = 0.0
        var loss = 0.0
        for (i in 1..period) {
            val change = closes[i] - closes[i - 1]
            if (change >= 0) gain += change else loss -= change
        }
        var avgGain = gain / period
        var avgLoss = loss / period
        for (i in period + 1 until closes.size) {
            val change = closes[i] - closes[i - 1]
            avgGain = (avgGain * (period - 1) + max(change, 0.0)) / period
            avgLoss = (avgLoss * (period - 1) + max(-change, 0.0)) / period
        }
        val rsi = if (avgLoss == 0.0) 100.0 else 100.0 - 100.0 / (1.0 + avgGain / avgLoss)

        val tr = mutableListOf<Double>()
        val plusDm = mutableListOf<Double>()
        val minusDm = mutableListOf<Double>()
        for (i in 1 until candles.size) {
            val c = candles[i]
            val p = candles[i - 1]
            tr += max(c.high - c.low, max(abs(c.high - p.close), abs(c.low - p.close)))
            val up = c.high - p.high
            val down = p.low - c.low
            plusDm += if (up > down && up > 0) up else 0.0
            minusDm += if (down > up && down > 0) down else 0.0
        }
        var smTr = tr.take(period).sum()
        var smPlus = plusDm.take(period).sum()
        var smMinus = minusDm.take(period).sum()
        val dx = mutableListOf<Double>()
        fun appendDx() {
            val pdi = if (smTr == 0.0) 0.0 else 100.0 * smPlus / smTr
            val mdi = if (smTr == 0.0) 0.0 else 100.0 * smMinus / smTr
            dx += if (pdi + mdi == 0.0) 0.0 else 100.0 * abs(pdi - mdi) / (pdi + mdi)
        }
        appendDx()
        for (i in period until tr.size) {
            smTr = smTr - smTr / period + tr[i]
            smPlus = smPlus - smPlus / period + plusDm[i]
            smMinus = smMinus - smMinus / period + minusDm[i]
            appendDx()
        }
        if (dx.size < period) return Indicators(rsi, null, null, null)
        var adx = dx.take(period).average()
        for (i in period until dx.size) adx = (adx * (period - 1) + dx[i]) / period
        val pdi = if (smTr == 0.0) 0.0 else 100.0 * smPlus / smTr
        val mdi = if (smTr == 0.0) 0.0 else 100.0 * smMinus / smTr
        return Indicators(rsi, adx, pdi, mdi)
    }
}
