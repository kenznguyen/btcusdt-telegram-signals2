package com.kenznguyen.btclivealerts

import kotlinx.coroutines.suspendCancellableCoroutine
import okhttp3.Call
import okhttp3.Callback
import okhttp3.HttpUrl
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

/** A retrieved snapshot, never a claim about exchange sequence synchronization. */
data class HummingbotSnapshot(
    val observedAtMs: Long,
    val bids: List<OrderBookLevel>,
    val asks: List<OrderBookLevel>,
    val metrics: OrderBookMetrics
) {
    companion object {
        fun parse(json: JSONObject, symbol: String, nowMs: Long): HummingbotSnapshot {
            require(json.getString("symbol") == symbol) { "Sai cặp giao dịch" }
            require(json.getString("source") == "hummingbot") { "Sai nguồn dữ liệu" }
            require(json.getString("connector") == "binance_perpetual") { "Sai thị trường futures" }
            val timestamp = json.getDouble("observedAtMs")
            require(timestamp.isFinite() && timestamp > 0 && timestamp <= Long.MAX_VALUE.toDouble())
            val observedAt = timestamp.toLong()
            require(nowMs - observedAt in -5_000L..30_000L) { "Snapshot đã cũ hoặc sai thời gian" }
            fun levels(name: String): List<OrderBookLevel> {
                val rows = json.getJSONArray(name)
                require(rows.length() in 1..20) { "Độ sâu không hợp lệ" }
                val levels = (0 until rows.length()).map { index ->
                    val row = rows.getJSONObject(index)
                    val price = row.getDouble("price")
                    val quantity = row.getDouble("quantity")
                    require(price.isFinite() && price > 0 && quantity.isFinite() && quantity > 0)
                    OrderBookLevel(price, quantity)
                }
                require(levels.map { it.price }.distinct().size == levels.size) { "Mức giá bị trùng" }
                require(levels.sumOf { it.quantity }.isFinite()) { "Độ sâu vượt giới hạn" }
                return levels
            }
            val bids = levels("bids").sortedByDescending { it.price }
            val asks = levels("asks").sortedBy { it.price }
            // Reuse the calculator only. Hummingbot snapshots never enter the scanner's
            // synchronized diff-depth stream or its trading-strategy confirmation gate.
            val metrics = requireNotNull(OrderBookAnalytics.calculate(
                bids, asks, updateId = 0L, updatedAtMs = observedAt, synchronized = true
            )) { "Order Book bị chéo hoặc rỗng" }.copy(synchronized = false)
            require(metrics.spreadBps.isFinite() && metrics.weightedImbalance.isFinite())
            return HummingbotSnapshot(observedAt, bids, asks, metrics)
        }
    }
}

internal fun hummingbotEndpoint(baseUrl: String, symbol: String): HttpUrl {
    require(Regex("[A-Z0-9]{2,16}USDT").matches(symbol)) { "Cặp giao dịch không hợp lệ" }
    val base = baseUrl.trim().toHttpUrl()
    require(base.isHttps && base.username.isEmpty() && base.password.isEmpty() &&
        base.query == null && base.fragment == null) { "Cần URL HTTPS không chứa mã truy cập" }
    return base.newBuilder().addPathSegments("v1/order-book").addQueryParameter("symbol", symbol).build()
}

internal object HummingbotClient {
    private val client = OkHttpClient.Builder()
        .callTimeout(10, TimeUnit.SECONDS)
        .followRedirects(false).followSslRedirects(false).build()

    suspend fun fetch(baseUrl: String, token: String, symbol: String): HummingbotSnapshot {
        require(token.isNotBlank() && token.all { it.code in 33..126 }) { "Cần mã truy cập hợp lệ" }
        val request = Request.Builder().url(hummingbotEndpoint(baseUrl, symbol))
            .header("Authorization", "Bearer $token").header("Accept", "application/json").build()
        return suspendCancellableCoroutine { continuation ->
            val call = client.newCall(request)
            continuation.invokeOnCancellation { call.cancel() }
            call.enqueue(object : Callback {
                override fun onFailure(call: Call, e: IOException) {
                    if (continuation.isActive) continuation.resumeWith(Result.failure(IOException("Không kết nối được máy chủ")))
                }
                override fun onResponse(call: Call, response: Response) {
                    val result = runCatching {
                        response.use {
                            check(it.isSuccessful) { when (it.code) {
                                401 -> "Mã truy cập không hợp lệ"
                                400 -> "Máy chủ chưa hỗ trợ cặp này"
                                503 -> "Máy chủ chưa cấu hình Hummingbot"
                                else -> "Không lấy được snapshot Hummingbot (HTTP ${it.code})"
                            } }
                            val body = checkNotNull(it.body)
                            val source = body.source()
                            check(!source.request(1_048_577L)) { "Snapshot vượt giới hạn" }
                            HummingbotSnapshot.parse(JSONObject(source.readUtf8()), symbol, System.currentTimeMillis())
                        }
                    }
                    if (continuation.isActive) continuation.resumeWith(result)
                }
            })
        }
    }
}
