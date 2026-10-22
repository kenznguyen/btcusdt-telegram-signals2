package com.kenznguyen.btclivealerts

import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.io.Closeable
import java.util.concurrent.ConcurrentHashMap
import okhttp3.WebSocket

/** Observe-only scanner. Each symbol owns candle caches and an independent order book. */
class MultiSymbolScanner(
    private val market: MarketEngine = MarketEngine(),
    private val onUpdate: (List<SymbolScanResult>) -> Unit,
    private val onStatus: (String) -> Unit
) : Closeable {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val strategy = StrategyEngine()
    private val books = ConcurrentHashMap<String, OrderBookMetrics>()
    private val states = ConcurrentHashMap<String, SymbolState>()
    private val bookEngines = ConcurrentHashMap<String, OrderBookEngine>()
    @Volatile private var socket: WebSocket? = null
    @Volatile private var closed = false
    private var startupJob: Job? = null

    data class SymbolScanResult(
        val symbol: String,
        val candidate: String?,
        val confirmed: String?,
        val reason: String,
        val m15CloseTime: Long,
        val evaluatedAt: Long,
        val orderBookAgeMs: Long?
    )

    private data class SymbolState(
        val m15: java.util.TreeMap<Long, Candle> = java.util.TreeMap(),
        val h1: java.util.TreeMap<Long, Candle> = java.util.TreeMap(),
        var lastEvaluatedM15Open: Long = 0L,
        var markPrice: Double? = null
    )

    fun start() {
        if (closed || startupJob?.isActive == true) return
        startupJob = scope.launch {
            try {
                onStatus("Đang chọn 20 hợp đồng USDT Perpetual có thanh khoản cao…")
                val symbols = market.fetchTopPerpetualSymbols(20)
                if (symbols.isEmpty()) error("Binance không trả về danh sách symbol hợp lệ")
                symbols.forEach { states.putIfAbsent(it, SymbolState()) }
                // Seed in a paced sequence to avoid a burst of REST kline requests.
                for (symbol in symbols) {
                    if (closed) return@launch
                    try {
                        val m15 = market.fetchCandles("15m", 150, symbol)
                        val h1 = market.fetchCandles("1h", 150, symbol)
                        val state = states.getValue(symbol)
                        synchronized(state) {
                            m15.filter { it.closed }.forEach { state.m15[it.openTime] = it }
                            h1.filter { it.closed }.forEach { state.h1[it.openTime] = it }
                            trim(state.m15, 500); trim(state.h1, 500)
                        }
                    } catch (e: CancellationException) { throw e }
                    catch (e: Exception) { onStatus("$symbol: chưa tải được nến ban đầu (${e.message ?: "lỗi REST"})") }
                    delay(350L)
                }
                symbols.forEach { symbol ->
                    bookEngines.computeIfAbsent(symbol) {
                        OrderBookEngine(
                            onMetrics = { metrics -> books[symbol] = metrics; evaluate(symbol) },
                            onStatus = { status -> if (status.contains("lỗi", true) || status.contains("đồng bộ lại", true)) onStatus("$symbol Order Book: $status") },
                            symbol = symbol
                        ).also { it.start() }
                    }
                }
                socket = market.connectMultiplex(
                    symbols = symbols,
                    onCandle = { symbol, interval, candle ->
                        val state = states[symbol] ?: return@connectMultiplex
                        synchronized(state) {
                            val cache = if (interval == "15m") state.m15 else if (interval == "1h") state.h1 else return@synchronized
                            cache[candle.openTime] = candle
                            trim(cache, 500)
                        }
                        if (interval == "15m" && candle.closed) evaluate(symbol)
                    },
                    onMarkPrice = { symbol, price -> states[symbol]?.let { synchronized(it) { it.markPrice = price } } },
                    onStatus = onStatus
                )
                onStatus("Scanner đang theo dõi ${symbols.size} symbol; chỉ đọc, không đặt lệnh")
            } catch (e: CancellationException) { throw e }
            catch (e: Exception) { onStatus("Không khởi động được scanner: ${e.message ?: "lỗi không xác định"}") }
        }
    }

    private fun evaluate(symbol: String) {
        val state = states[symbol] ?: return
        val snapshot = synchronized(state) {
            val m15 = state.m15.values.toList()
            val h1 = state.h1.values.toList()
            val latest = m15.lastOrNull { it.closed } ?: return
            if (latest.openTime <= state.lastEvaluatedM15Open) return
            state.lastEvaluatedM15Open = latest.openTime
            Triple(m15, h1, latest)
        }
        val (m15, h1, candle) = snapshot
        val candidate = strategy.entryCandidate(m15, h1)
        val evaluatedAt = System.currentTimeMillis()
        val book = books[symbol]
        val age = book?.let { evaluatedAt - it.updatedAtMs }
        val closeTime = candle.openTime + 15L * 60_000L
        val technicalScore = when (candidate) { "BUY" -> 1.0; "SELL" -> -1.0; else -> 0.0 }
        val confirmedResult = MultiStreamSignalEngine().evaluate(
            TechnicalSignalInput(technicalScore, if (candidate == null) 0.0 else 1.0, closeTime - 1L, "M15+H1"),
            book,
            evaluatedAt
        )
        val agrees = when (candidate) {
            "BUY" -> confirmedResult.orderBookScore != null && confirmedResult.orderBookScore > 0.0
            "SELL" -> confirmedResult.orderBookScore != null && confirmedResult.orderBookScore < 0.0
            else -> false
        }
        val confirmed = candidate?.takeIf { confirmedResult.dataComplete && agrees && confirmedResult.signal == it }
        val reason = when {
            candidate == null -> "NO_TECHNICAL_CANDIDATE"
            book == null -> "ORDERBOOK_MISSING"
            !book.synchronized -> "ORDERBOOK_UNSYNCED"
            age == null || age < 0L -> "ORDERBOOK_FUTURE_TIMESTAMP"
            age > 2_000L -> "ORDERBOOK_STALE"
            !confirmedResult.dataComplete -> "DATA_INCOMPLETE"
            !agrees -> "ORDERBOOK_DIRECTION_MISMATCH"
            confirmedResult.signal != candidate -> "COMBINED_SCORE_REJECTED"
            else -> "CONFIRMED"
        }
        onUpdate(listOf(SymbolScanResult(symbol, candidate, confirmed, reason, closeTime, evaluatedAt, age)))
    }

    private fun trim(cache: java.util.TreeMap<Long, Candle>, max: Int) {
        while (cache.size > max) cache.pollFirstEntry()
    }

    override fun close() {
        closed = true
        startupJob?.cancel()
        socket?.close(1000, "scanner stopped")
        socket = null
        bookEngines.values.forEach { runCatching { it.close() } }
        bookEngines.clear()
        states.clear()
        books.clear()
        scope.cancel()
    }
}
