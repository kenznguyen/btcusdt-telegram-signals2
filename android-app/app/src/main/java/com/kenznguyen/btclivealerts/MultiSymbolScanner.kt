package com.kenznguyen.btclivealerts

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.isActive
import kotlinx.coroutines.selects.select
import kotlinx.coroutines.withTimeoutOrNull
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.io.Closeable
import java.util.concurrent.ConcurrentHashMap
import java.io.IOException

/** Observe-only scanner. Each symbol owns candle caches and an independent order book. */
class MultiSymbolScanner internal constructor(
    private val feed: ScannerMarketFeed,
    private val onUpdate: (List<SymbolScanResult>) -> Unit,
    private val onStatus: (String) -> Unit,
    private val scope: CoroutineScope,
    private val createBook: ScannerBookFactory,
    private val nowMs: () -> Long = System::currentTimeMillis
) : Closeable {
    constructor(
        market: MarketEngine = MarketEngine(),
        onUpdate: (List<SymbolScanResult>) -> Unit,
        onStatus: (String) -> Unit
    ) : this(BinanceScannerMarketFeed(market), onUpdate, onStatus,
        CoroutineScope(SupervisorJob() + Dispatchers.IO),
        { symbol, metrics, status -> OrderBookEngine(metrics, status, symbol).also { it.start() } })

    private val strategy = StrategyEngine()
    private val lifecycleLock = Any()
    private val books = ConcurrentHashMap<String, OrderBookMetrics>()
    private val latestResults = ConcurrentHashMap<String, SymbolScanResult>()
    private val states = ConcurrentHashMap<String, SymbolState>()
    private val bookEngines = ConcurrentHashMap<String, Closeable>()
    private var connection: Closeable? = null
    private var closed = false
    private var ready = false
    private var generation = 0L
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

    fun start() = synchronized(lifecycleLock) {
        if (closed || startupJob?.isActive == true) return@synchronized
        startupJob = scope.launch {
            var failures = 0
            while (isActive) {
                try {
                    runSession { failures = 0 }
                } catch (e: CancellationException) { throw e }
                catch (e: Exception) {
                    synchronized(lifecycleLock) {
                        if (!closed) onStatus("Scanner đang kết nối lại: ${e.message ?: "lỗi mạng"}")
                    }
                }
                // Includes bootstrap failures: a failed REST call must not leave an inert scanner.
                val waitMs = minOf(60_000L, 2_000L * (1L shl failures.coerceAtMost(5)))
                failures++
                delay(waitMs)
            }
        }
    }

    private suspend fun runSession(onReady: () -> Unit): Unit = coroutineScope {
        val token = synchronized(lifecycleLock) {
            if (closed) throw CancellationException("Scanner closed")
            generation++
            ready = false
            states.clear()
            books.clear()
            latestResults.clear()
            onUpdate(emptyList())
            generation
        }
        val connected = CompletableDeferred<Unit>()
        val disconnected = CompletableDeferred<String>()
        var sessionConnection: Closeable? = null
        try {
            emitStatus(token, "Đang chọn 20 hợp đồng USDT Perpetual có thanh khoản cao…")
            val symbols = feed.symbols()
            check(symbols.isNotEmpty()) { "Binance không trả về danh sách symbol hợp lệ" }
            synchronized(lifecycleLock) {
                if (!isCurrent(token)) throw CancellationException("Scanner session retired")
                symbols.forEach { states[it] = SymbolState() }
            }
            // Subscribe before REST backfill so candles closing during synchronization are buffered.
            val newConnection = feed.connect(symbols,
                onConnected = { if (isCurrent(token)) connected.complete(Unit) },
                onDisconnected = { reason ->
                    synchronized(lifecycleLock) {
                        if (isCurrent(token)) {
                            ready = false
                            latestResults.clear()
                            onUpdate(emptyList())
                            disconnected.complete(reason)
                        }
                    }
                },
                onCandle = { symbol, interval, candle ->
                    val state = synchronized(lifecycleLock) {
                        if (isCurrent(token) && !disconnected.isCompleted) states[symbol] else null
                    }
                    state?.let {
                        synchronized(state) {
                            val cache = when (interval) { "15m" -> state.m15; "1h" -> state.h1; else -> null }
                            if (cache != null) mergeCandle(cache, candle, fromRest = false)
                        }
                        if (interval == "15m" && candle.closed) evaluate(symbol, token)
                    }
                },
                onMarkPrice = { symbol, price ->
                    val state = synchronized(lifecycleLock) {
                        if (isCurrent(token) && !disconnected.isCompleted) states[symbol] else null
                    }
                    state?.let { synchronized(it) { it.markPrice = price } }
                },
                onStatus = { emitStatus(token, it) })
            sessionConnection = newConnection
            val keepConnection = synchronized(lifecycleLock) {
                if (isCurrent(token)) { connection = newConnection; true } else false
            }
            if (!keepConnection) newConnection.close()
            withTimeoutOrNull(30_000L) {
                select<Unit> {
                    connected.onAwait { }
                    disconnected.onAwait { throw IOException(it) }
                }
                true
            } ?: throw IOException("Scanner WebSocket kết nối quá hạn")
            val bootstrap = async {
                for (symbol in symbols) {
                    val m15 = feed.candles(symbol, "15m")
                    val h1 = feed.candles(symbol, "1h")
                    check(m15.isNotEmpty() && h1.isNotEmpty()) { "$symbol: dữ liệu nến rỗng" }
                    val state = states.getValue(symbol)
                    synchronized(state) {
                        m15.forEach { mergeCandle(state.m15, it, fromRest = true) }
                        h1.forEach { mergeCandle(state.h1, it, fromRest = true) }
                    }
                }
                for (symbol in symbols) {
                    val book = createBook(symbol,
                        { metrics ->
                            synchronized(lifecycleLock) {
                                if (isCurrent(token)) books[symbol] = metrics
                            }
                            evaluate(symbol, token, allowSameCandle = true)
                        },
                        { emitStatus(token, "$symbol Order Book: $it") })
                    val keepBook = synchronized(lifecycleLock) {
                        if (isCurrent(token)) { bookEngines[symbol] = book; true } else false
                    }
                    if (!keepBook) book.close()
                    delay(500L)
                }
            }
            select<Unit> {
                bootstrap.onAwait { }
                disconnected.onAwait { throw IOException(it) }
            }
            synchronized(lifecycleLock) {
                if (isCurrent(token) && !disconnected.isCompleted) {
                    ready = true
                    onReady()
                    onStatus("Scanner đang theo dõi ${symbols.size} symbol; chỉ đọc, không đặt lệnh")
                }
            }
            symbols.forEach { evaluate(it, token) }
            throw IOException(disconnected.await())
        } finally {
            val retiredBooks = synchronized(lifecycleLock) {
                if (generation == token) {
                    ready = false
                    generation++ // Ignore late callbacks from the retired WebSocket and depth books.
                    connection = null
                    latestResults.clear()
                    if (!closed) onUpdate(emptyList())
                }
                bookEngines.values.toList().also { bookEngines.clear() }
            }
            // Depth callbacks run under the book lock: never close a book while holding our lock.
            retiredBooks.forEach { runCatching { it.close() } }
            sessionConnection?.close()
        }
    }

    private fun isCurrent(token: Long): Boolean = synchronized(lifecycleLock) { !closed && generation == token }

    private fun emitStatus(token: Long, message: String) = synchronized(lifecycleLock) {
        if (isCurrent(token)) onStatus(message)
    }

    private fun mergeCandle(cache: java.util.TreeMap<Long, Candle>, candle: Candle, fromRest: Boolean) {
        val existing = cache[candle.openTime]
        // A delayed forming update must never turn a finalized candle back into an open candle.
        // Buffered WebSocket updates also take precedence over an older REST response.
        if (existing == null || (!existing.closed && candle.closed) || (!fromRest && !existing.closed)) {
            cache[candle.openTime] = candle
        }
        trim(cache, 500)
    }

    private fun evaluate(symbol: String, token: Long, allowSameCandle: Boolean = false) {
        val state = synchronized(lifecycleLock) {
            if (isCurrent(token) && ready) states[symbol] else null
        } ?: return
        val snapshot = synchronized(state) {
            val m15 = state.m15.values.toList()
            val h1 = state.h1.values.toList()
            val latest = m15.lastOrNull { it.closed } ?: return
            if (!allowSameCandle && latest.openTime <= state.lastEvaluatedM15Open) return
            if (latest.openTime > state.lastEvaluatedM15Open) state.lastEvaluatedM15Open = latest.openTime
            Triple(m15, h1, latest)
        }
        val (m15, h1, candle) = snapshot
        val candidate = strategy.latestClosedEntryCandidate(m15, h1)
        val evaluatedAt = nowMs()
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
        synchronized(lifecycleLock) {
            if (!isCurrent(token) || !ready) return
            // A slower book-triggered evaluation must not overwrite a newer closed candle.
            if ((latestResults[symbol]?.m15CloseTime ?: Long.MIN_VALUE) > closeTime) return
            latestResults[symbol] = SymbolScanResult(symbol, candidate, confirmed, reason, closeTime, evaluatedAt, age)
            onUpdate(latestResults.values.sortedBy { it.symbol })
        }
    }

    private fun trim(cache: java.util.TreeMap<Long, Candle>, max: Int) {
        while (cache.size > max) cache.pollFirstEntry()
    }

    override fun close() {
        val resources = synchronized(lifecycleLock) {
            if (closed) return
            closed = true
            ready = false
            generation++
            startupJob?.cancel()
            val retired = bookEngines.values.toList() + listOfNotNull(connection)
            connection = null
            bookEngines.clear()
            latestResults.clear()
            onUpdate(emptyList())
            states.clear()
            books.clear()
            retired
        }
        resources.forEach { runCatching { it.close() } }
        scope.cancel()
    }
}
