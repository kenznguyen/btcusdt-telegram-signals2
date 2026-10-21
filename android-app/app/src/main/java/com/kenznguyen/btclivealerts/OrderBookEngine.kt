package com.kenznguyen.btclivealerts

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import org.json.JSONArray
import org.json.JSONObject
import java.io.Closeable
import java.util.TreeMap
import java.util.concurrent.TimeUnit

/**
 * Collects Binance USDⓈ-M Futures BTCUSDT diff-depth events and reconciles them
 * with a REST snapshot before publishing metrics. Analysis only; no order endpoints.
 */
class OrderBookEngine(
    private val onMetrics: (OrderBookMetrics) -> Unit,
    private val onStatus: (String) -> Unit
) : Closeable {
    private val client = OkHttpClient.Builder()
        .callTimeout(10, TimeUnit.SECONDS)
        .pingInterval(20, TimeUnit.SECONDS)
        .build()
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val lock = Any()
    private val bids = TreeMap<Double, Double>(compareByDescending { it })
    private val asks = TreeMap<Double, Double>()
    private val buffered = ArrayDeque<JSONObject>()
    private var socket: WebSocket? = null
    private var lastUpdateId = 0L
    private var snapshotInFlight = false
    private var synchronizedBook = false
    private var closed = false

    fun start() {
        synchronized(lock) {
            if (closed || socket != null) return
            onStatus("Đang kết nối Order Book Binance Futures…")
            socket = client.newWebSocket(
                Request.Builder().url("wss://fstream.binance.com/ws/btcusdt@depth@100ms").build(),
                object : WebSocketListener() {
                    override fun onOpen(webSocket: WebSocket, response: Response) {
                        onStatus("Order Book đã kết nối; đang đồng bộ snapshot…")
                        requestSnapshot()
                    }

                    override fun onMessage(webSocket: WebSocket, text: String) {
                        try {
                            val event = JSONObject(text)
                            synchronized(lock) {
                                if (closed) return
                                if (!synchronizedBook) {
                                    buffered.addLast(event)
                                    while (buffered.size > 2000) buffered.removeFirst()
                                    if (!snapshotInFlight) requestSnapshot()
                                } else if (applyEvent(event)) {
                                    publish()
                                } else {
                                    synchronizedBook = false
                                    buffered.clear()
                                    buffered.addLast(event)
                                    snapshotInFlight = false
                                    onStatus("Mất chuỗi cập nhật Order Book; đang đồng bộ lại…")
                                    requestSnapshot()
                                }
                            }
                        } catch (_: Exception) {
                            onStatus("Order Book nhận dữ liệu không hợp lệ")
                        }
                    }

                    override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                        synchronized(lock) {
                            socket = null
                            synchronizedBook = false
                            snapshotInFlight = false
                        }
                        onStatus("Order Book mất kết nối: ${t.message ?: "lỗi mạng"}")
                        scheduleReconnect()
                    }

                    override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                        synchronized(lock) {
                            socket = null
                            synchronizedBook = false
                        }
                        if (!closed) scheduleReconnect()
                    }
                }
            )
        }
    }

    private fun scheduleReconnect() {
        scope.launch {
            delay(2_000L)
            synchronized(lock) {
                if (!closed && socket == null) start()
            }
        }
    }

    private fun requestSnapshot() {
        if (snapshotInFlight || closed) return
        snapshotInFlight = true
        scope.launch {
            try {
                val request = Request.Builder()
                    .url("https://fapi.binance.com/fapi/v1/depth?symbol=BTCUSDT&limit=1000")
                    .build()
                val snapshot = client.newCall(request).execute().use { response ->
                    check(response.isSuccessful) { "Snapshot HTTP ${response.code}" }
                    JSONObject(response.body?.string() ?: error("Snapshot rỗng"))
                }
                synchronized(lock) {
                    if (closed) return@synchronized
                    bids.clear()
                    asks.clear()
                    loadSide(snapshot.optJSONArray("bids"), bids)
                    loadSide(snapshot.optJSONArray("asks"), asks)
                    val snapshotId = snapshot.getLong("lastUpdateId")
                    lastUpdateId = snapshotId
                    synchronizedBook = false

                    val events = buffered.toList()
                    buffered.clear()
                    var bridged = false
                    var valid = true
                    for (event in events) {
                        val first = event.optLong("U")
                        val last = event.optLong("u")
                        if (last < lastUpdateId) continue
                        if (!bridged) {
                            if (first <= lastUpdateId && last >= lastUpdateId) {
                                applyLevels(event)
                                lastUpdateId = last
                                bridged = true
                            } else if (first > lastUpdateId) {
                                valid = false
                                break
                            }
                        } else {
                            if (event.optLong("pu", lastUpdateId) != lastUpdateId) {
                                valid = false
                                break
                            }
                            applyLevels(event)
                            lastUpdateId = last
                        }
                    }
                    snapshotInFlight = false
                    if (!bridged || !valid) {
                        synchronizedBook = false
                        onStatus("Đang đồng bộ lại Order Book…")
                        requestSnapshot()
                    } else {
                        synchronizedBook = true
                        onStatus("Order Book đã đồng bộ")
                        publish()
                    }
                }
            } catch (e: Exception) {
                synchronized(lock) { snapshotInFlight = false }
                onStatus("Không tải được Order Book: ${e.message ?: "lỗi mạng"}")
                scheduleSnapshotRetry()
            }
        }
    }

    private fun scheduleSnapshotRetry() {
        scope.launch {
            delay(2_000L)
            synchronized(lock) {
                if (!closed && socket != null && !synchronizedBook && !snapshotInFlight) requestSnapshot()
            }
        }
    }

    private fun applyEvent(event: JSONObject): Boolean {
        val first = event.optLong("U")
        val last = event.optLong("u")
        if (last <= lastUpdateId) return true // stale/duplicate
        if (first > lastUpdateId + 1 && event.optLong("pu", lastUpdateId) != lastUpdateId) return false
        if (event.has("pu") && event.optLong("pu") != lastUpdateId) return false
        applyLevels(event)
        lastUpdateId = last
        return true
    }

    private fun applyLevels(event: JSONObject) {
        loadSide(event.optJSONArray("b"), bids)
        loadSide(event.optJSONArray("a"), asks)
    }

    private fun loadSide(rows: JSONArray?, side: TreeMap<Double, Double>) {
        if (rows == null) return
        for (i in 0 until rows.length()) {
            val row = rows.getJSONArray(i)
            val price = row.getString(0).toDouble()
            val qty = row.getString(1).toDouble()
            if (qty <= 0.0) side.remove(price) else side[price] = qty
        }
    }

    private fun publish() {
        if (!synchronizedBook) return
        val bidLevels = bids.entries.map { OrderBookLevel(it.key, it.value) }
        val askLevels = asks.entries.map { OrderBookLevel(it.key, it.value) }
        val metrics = OrderBookAnalytics.calculate(
            bids = bidLevels,
            asks = askLevels,
            updateId = lastUpdateId,
            updatedAtMs = System.currentTimeMillis(),
            synchronized = true
        )
        if (metrics == null) {
            onStatus("Order Book spread/depth không hợp lệ")
            return
        }
        onMetrics(metrics)
    }

    override fun close() {
        synchronized(lock) {
            closed = true
            socket?.close(1000, "monitor stopped")
            socket = null
            buffered.clear()
            bids.clear()
            asks.clear()
        }
        scope.cancel()
        client.dispatcher.cancelAll()
        client.connectionPool.evictAll()
    }
}
