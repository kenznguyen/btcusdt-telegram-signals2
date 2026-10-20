package com.kenznguyen.btclivealerts

import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray
import java.io.IOException
import java.util.concurrent.TimeUnit

/**
 * Public Binance Spot klines used as a clearly-labelled proxy for experimental
 * five-minute forecast paper evaluation. This is NOT Chainlink Data Streams data.
 */
internal class BinanceSpotForecastSource(
    private val client: OkHttpClient = OkHttpClient.Builder()
        .callTimeout(15, TimeUnit.SECONDS)
        .build()
) {
    fun fetchClosedOneMinuteCandles(limit: Int = 1500, nowMs: Long = System.currentTimeMillis()): List<Candle> {
        require(limit in 1..1500)
        val url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=$limit"
        val request = Request.Builder()
            .url(url)
            .header("Accept", "application/json")
            .build()
        val response = client.newCall(request).execute()
        response.use {
            if (!it.isSuccessful) throw IOException("Binance Spot HTTP ${it.code}")
            val body = it.body?.string() ?: throw IOException("Binance Spot trả về dữ liệu rỗng")
            val rows = JSONArray(body)
            val candles = ArrayList<Candle>(rows.length())
            for (i in 0 until rows.length()) {
                val row = rows.getJSONArray(i)
                val openTime = row.getLong(0)
                val closeTime = row.getLong(6)
                // Binance kline closeTime is inclusive; only consume candles whose interval ended.
                val closed = closeTime < nowMs
                if (!closed) continue
                candles += Candle(
                    openTime = openTime,
                    open = row.getString(1).toDouble(),
                    high = row.getString(2).toDouble(),
                    low = row.getString(3).toDouble(),
                    close = row.getString(4).toDouble(),
                    volume = row.getString(5).toDouble(),
                    closed = true
                )
            }
            return candles.distinctBy { it.openTime }.sortedBy { it.openTime }
        }
    }
}
