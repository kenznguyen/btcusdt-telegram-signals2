package com.kenznguyen.btc5mforecast

import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray
import java.io.IOException
import java.util.concurrent.TimeUnit

class BinanceSpotApi(
    private val client: OkHttpClient = OkHttpClient.Builder()
        .callTimeout(15, TimeUnit.SECONDS)
        .build()
) {
    fun fetchOneMinute(limit: Int = 1500, now: Long = System.currentTimeMillis()): List<Candle> {
        require(limit in 10..1000)
        val request = Request.Builder()
            .url("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=$limit")
            .header("Accept", "application/json").build()
        client.newCall(request).execute().use { response ->
            if (!response.isSuccessful) throw IOException("Binance Spot HTTP ${response.code}")
            val rows = JSONArray(response.body?.string() ?: throw IOException("Empty response"))
            return (0 until rows.length()).mapNotNull { i ->
                val r = rows.getJSONArray(i)
                val openTime = r.getLong(0)
                val closeTime = r.getLong(6)
                if (closeTime >= now) null else Candle(
                    openTime, r.getString(1).toDouble(), r.getString(2).toDouble(),
                    r.getString(3).toDouble(), r.getString(4).toDouble(),
                    r.getString(5).toDouble(), closeTime
                )
            }.distinctBy { it.openTime }.sortedBy { it.openTime }
        }
    }
}
