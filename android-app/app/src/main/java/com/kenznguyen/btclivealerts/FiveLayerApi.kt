package com.kenznguyen.btclivealerts

import kotlinx.coroutines.suspendCancellableCoroutine
import okhttp3.Call
import okhttp3.Callback
import okhttp3.HttpUrl
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import org.json.JSONObject
import java.io.IOException
import java.io.InterruptedIOException
import java.math.BigDecimal
import java.util.concurrent.TimeUnit

internal data class LayerView(val level: Int, val name: String, val status: String, val detail: String)
internal data class SystemView(val layers: List<LayerView>)
internal data class FeedCoverage(val name: String, val status: String, val rows: Long,
    val lastEventAtMs: Long?, val tradeIdGaps: Long?)
internal data class IntelligenceView(
    val available: Boolean, val reason: String? = null,
    val availableAtMs: Long? = null, val windowStartMs: Long? = null, val windowEndMs: Long? = null,
    val fundingRate: String? = null, val fundingAtMs: Long? = null,
    val openInterestBase: String? = null, val openInterestChangeBase: String? = null,
    val takerBuyQuote: String? = null, val takerSellQuote: String? = null, val netTakerQuote: String? = null,
    val largeTradeQuote: String? = null, val observedLiquidationBuyQuote: String? = null,
    val observedLiquidationSellQuote: String? = null, val coverage: List<FeedCoverage> = emptyList()
)
internal data class IntentView(val targetPositionBase: String, val limitPrice: String,
    val modelVersion: String, val strategyVersion: String, val datasetVersion: String,
    val decisionAtMs: Long, val validUntilMs: Long)
internal data class DecisionView(val action: String, val reason: String, val intent: IntentView?)
internal data class PaperOrderView(val orderId: String, val intentId: String, val status: String, val side: String,
    val quantityBase: String, val filledBase: String, val remainingBase: String,
    val averagePrice: String?, val feeQuote: String, val createdAtMs: Long, val updatedAtMs: Long,
    val reason: String)
internal data class PaperView(val paused: Boolean, val positionBase: String, val averageEntryPrice: String,
    val realizedPnlQuote: String, val feesQuote: String, val netRealizedPnlQuote: String,
    val orders: List<PaperOrderView>)
internal data class PaperEvaluationView(val decision: DecisionView, val order: PaperOrderView?)
internal data class CanonicalCandle(val openTimeMs: Long, val closeTimeMs: Long,
    val open: String, val high: String, val low: String, val close: String, val volume: String,
    val availableAtMs: Long)
internal data class CandleGap(val startMs: Long, val endMs: Long)
internal data class CandleWindowView(val startMs: Long, val endMs: Long, val generatedAtMs: Long?,
    val datasetVersion: String, val expected: Int, val returned: Int, val complete: Boolean,
    val gaps: List<CandleGap>, val candles: List<CanonicalCandle>)

internal enum class FiveLayerFailure(val messageVi: String) {
    AUTH("Mã truy cập không hợp lệ hoặc không đủ quyền"),
    ENDPOINT("Máy chủ chưa cung cấp API này; kiểm tra địa chỉ và phiên bản máy chủ"),
    RATE_LIMIT("Đã vượt giới hạn yêu cầu; chờ rồi làm mới"),
    UNAVAILABLE("Dữ liệu hoặc cấu hình máy chủ chưa sẵn sàng"),
    HTTP("Máy chủ từ chối yêu cầu"),
    NETWORK("Không kết nối được máy chủ; kiểm tra mạng và địa chỉ HTTPS"),
    TIMEOUT("Máy chủ phản hồi quá chậm; thử làm mới dữ liệu"),
    INVALID_RESPONSE("Dữ liệu máy chủ không hợp lệ hoặc không đúng hợp đồng API")
}

/** Contains only fixed messages and status codes, never a response body, URL or token. */
internal class FiveLayerApiException(val code: FiveLayerFailure, val httpStatus: Int? = null) :
    IOException(code.messageVi)

internal fun fiveLayerHttpFailure(status: Int): FiveLayerApiException = FiveLayerApiException(when (status) {
    401, 403 -> FiveLayerFailure.AUTH
    404 -> FiveLayerFailure.ENDPOINT
    429 -> FiveLayerFailure.RATE_LIMIT
    503 -> FiveLayerFailure.UNAVAILABLE
    else -> FiveLayerFailure.HTTP
}, status)

internal fun fiveLayerNetworkFailure(error: IOException): FiveLayerApiException = FiveLayerApiException(
    if (error is InterruptedIOException) FiveLayerFailure.TIMEOUT else FiveLayerFailure.NETWORK)

/** Values stay decimal strings: displaying money must not lose precision through Double. */
internal object FiveLayerJson {
    private fun text(json: JSONObject, key: String, limit: Int = 300): String {
        val value = json.get(key)
        require(value is String && value.length in 1..limit && value.none { it.isISOControl() })
        return value
    }
    private fun integer(json: JSONObject, key: String): Long {
        val value = json.get(key)
        require(value is Int || value is Long)
        return (value as Number).toLong().also { require(it >= 0) }
    }
    private fun stamp(json: JSONObject, key: String, nowMs: Long): Long =
        integer(json, key).also { require(it <= nowMs + 5_000L) }
    private fun bool(json: JSONObject, key: String): Boolean =
        json.get(key).let { require(it is Boolean); it }
    private fun decimal(json: JSONObject, key: String, signed: Boolean = false): String {
        val raw = text(json, key, 256)
        require(Regex("-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?(?:[eE][+-]?[0-9]+)?").matches(raw))
        val value = BigDecimal(raw)
        require(value.scale() in -200..200 && value.precision() <= 256 && value.precision() - value.scale() <= 201)
        require(signed || value.signum() >= 0)
        return raw
    }
    private fun optionalDecimal(json: JSONObject, key: String, signed: Boolean = false): String? {
        require(json.has(key))
        return if (json.isNull(key)) null else decimal(json, key, signed)
    }
    private fun market(json: JSONObject) {
        require(text(json, "symbol") == "BTCUSDT" && text(json, "exchange") == "binance" &&
            text(json, "marketType") == "USDT_PERPETUAL")
    }
    private fun paper(json: JSONObject) { require(text(json, "mode") == "PAPER") }
    private fun envelope(json: JSONObject) { paper(json); require(!bool(json, "liveTradingSupported")) }

    fun system(json: JSONObject): SystemView {
        envelope(json)
        val rows = json.getJSONArray("layers")
        require(rows.length() == 5)
        val layers = (0 until rows.length()).map { index ->
            val row = rows.getJSONObject(index)
            val level = integer(row, "level").also { require(it in 0L..4L) }.toInt()
            val status = text(row, "status")
            require(status in setOf("READY", "WAIT", "OBSERVED", "ARTIFACT_AVAILABLE", "CONFIGURED", "API_ONLY"))
            LayerView(level, text(row, "name"), status, text(row, "detail"))
        }
        require(layers.map { it.level }.toSet() == (0..4).toSet())
        return SystemView(layers.sortedBy { it.level })
    }

    fun intelligence(json: JSONObject, nowMs: Long): IntelligenceView {
        if (json.has("available")) {
            require(!bool(json, "available"))
            return IntelligenceView(false, text(json, "reason"))
        }
        market(json)
        require(integer(json, "schemaVersion") == 1L && text(json, "quality") == "OBSERVED_ONLY")
        require(text(json, "source") == "binance-futures-collector@bc4f0ef633fbeee4a49defd72827f17162693805")
        val start = stamp(json, "windowStartMs", nowMs)
        val end = stamp(json, "windowEndMs", nowMs)
        val available = stamp(json, "availableAtMs", nowMs)
        require(end > start && end - start <= 86_400_000L && available >= end)
        val coverageJson = json.getJSONObject("coverage")
        val coverage = listOf("trades", "funding", "openInterest", "liquidations").map { name ->
            val row = coverageJson.getJSONObject(name)
            val status = text(row, "status")
            val rows = integer(row, "rows").also { require(it <= 100_000) }
            require(status in setOf("OBSERVED", "MISSING", "NO_ROWS") && !bool(row, "complete"))
            require((status == "OBSERVED") == (rows > 0))
            val event = if (row.isNull("lastEventAtMs")) null else stamp(row, "lastEventAtMs", nowMs)
            require(if (status == "OBSERVED") event != null && event >= start && event < end else event == null)
            val gaps = if (name == "trades") integer(row, "tradeIdGaps") else null
            FeedCoverage(name, status, rows, event, gaps)
        }
        fun metric(key: String, feed: String, signed: Boolean = false, optional: Boolean = false): String? {
            val value = optionalDecimal(json, key, signed)
            val observed = coverage.first { it.name == feed }.status == "OBSERVED"
            require(if (observed) optional || value != null else value == null)
            return value
        }
        val fundingAt = if (json.isNull("fundingAtMs")) null else stamp(json, "fundingAtMs", nowMs)
        require(fundingAt == coverage.first { it.name == "funding" }.lastEventAtMs)
        return IntelligenceView(true, availableAtMs = available, windowStartMs = start, windowEndMs = end,
            fundingRate = metric("fundingRate", "funding", signed = true), fundingAtMs = fundingAt,
            openInterestBase = metric("openInterestBase", "openInterest"),
            openInterestChangeBase = metric("openInterestChangeBase", "openInterest", signed = true, optional = true),
            takerBuyQuote = metric("takerBuyQuote", "trades"), takerSellQuote = metric("takerSellQuote", "trades"),
            netTakerQuote = metric("netTakerQuote", "trades", signed = true),
            largeTradeQuote = metric("largeTradeQuote", "trades"),
            observedLiquidationBuyQuote = metric("observedLiquidationBuyQuote", "liquidations"),
            observedLiquidationSellQuote = metric("observedLiquidationSellQuote", "liquidations"), coverage = coverage)
    }

    fun decision(json: JSONObject, nowMs: Long): DecisionView {
        val action = text(json, "action")
        require(action in setOf("WAIT", "BUY", "SELL") && json.has("intent"))
        val intent = if (json.isNull("intent")) null else {
            val row = json.getJSONObject("intent")
            paper(row); market(row)
            val created = stamp(row, "decisionAtMs", nowMs)
            val expires = integer(row, "validUntilMs")
            require(expires > created && expires - created <= 30_000L)
            val target = decimal(row, "targetPositionBase", signed = true)
            require((action == "BUY" && BigDecimal(target).signum() > 0) ||
                (action == "SELL" && BigDecimal(target).signum() < 0))
            val price = decimal(row, "limitPrice").also { require(BigDecimal(it).signum() > 0) }
            IntentView(target, price, text(row, "modelVersion"), text(row, "strategyVersion"),
                text(row, "datasetVersion"), created, expires)
        }
        require((action == "WAIT") == (intent == null))
        return DecisionView(action, text(json, "reason"), intent)
    }

    fun order(json: JSONObject, nowMs: Long): PaperOrderView {
        paper(json)
        val status = text(json, "status")
        val side = text(json, "side")
        require(status in setOf("REJECTED", "OPEN", "PARTIALLY_FILLED", "FILLED", "CANCELED"))
        require(side in setOf("BUY", "SELL", "NONE"))
        val quantity = decimal(json, "quantityBase")
        val filled = decimal(json, "filledBase")
        val remaining = decimal(json, "remainingBase")
        val quantityValue = BigDecimal(quantity)
        val filledValue = BigDecimal(filled)
        val remainingValue = BigDecimal(remaining)
        require(quantityValue.compareTo(filledValue + remainingValue) == 0)
        require((side == "NONE") == (quantityValue.signum() == 0))
        val average = optionalDecimal(json, "averagePrice")
        val fee = decimal(json, "feeQuote")
        require(if (filledValue.signum() == 0) average == null && BigDecimal(fee).signum() == 0
            else average != null && BigDecimal(average).signum() > 0)
        require(when (status) {
            "OPEN" -> quantityValue.signum() > 0 && filledValue.signum() == 0
            "PARTIALLY_FILLED" -> filledValue.signum() > 0 && remainingValue.signum() > 0
            "FILLED" -> remainingValue.signum() == 0
            "REJECTED" -> filledValue.signum() == 0
            "CANCELED" -> remainingValue.signum() > 0
            else -> false
        })
        val created = stamp(json, "createdAtMs", nowMs)
        val updated = stamp(json, "updatedAtMs", nowMs)
        require(updated >= created)
        val intentId = text(json, "intentId", 200).also { require(it.isNotBlank()) }
        return PaperOrderView(text(json, "orderId", 100), intentId, status, side, quantity, filled, remaining,
            average, fee, created, updated, text(json, "reason"))
    }

    fun ledger(json: JSONObject, nowMs: Long): PaperView {
        envelope(json)
        require(text(json, "simulationModel") == "VISIBLE_DEPTH_LIMIT_SNAPSHOT")
        val rows = json.getJSONArray("orders")
        require(rows.length() <= 100)
        val orders = (0 until rows.length()).map { order(rows.getJSONObject(it), nowMs) }
        require(orders.map { it.orderId }.distinct().size == orders.size)
        val position = decimal(json, "positionBase", signed = true)
        val average = decimal(json, "averageEntryPrice")
        require((BigDecimal(position).signum() == 0) == (BigDecimal(average).signum() == 0))
        val realized = decimal(json, "realizedPnlQuote", signed = true)
        val fees = decimal(json, "feesQuote")
        val net = decimal(json, "netRealizedPnlQuote", signed = true)
        return PaperView(bool(json, "paused"), position, average, realized, fees, net, orders)
    }

    fun evaluation(json: JSONObject, nowMs: Long): PaperEvaluationView {
        require(json.has("order"))
        return PaperEvaluationView(decision(json.getJSONObject("decision"), nowMs),
            if (json.isNull("order")) null else order(json.getJSONObject("order"), nowMs))
    }

    fun candles(json: JSONObject, startMs: Long, endMs: Long, nowMs: Long): CandleWindowView {
        val step = 900_000L
        require(startMs >= 0 && endMs - startMs == 20 * step && startMs % step == 0L && endMs <= nowMs)
        market(json)
        require(text(json, "timeframe") == "15m" && integer(json, "startMs") == startMs && integer(json, "endMs") == endMs)
        require(json.has("asOfMs") && json.isNull("asOfMs"))
        val generated = if (json.has("generatedAtMs"))
            stamp(json, "generatedAtMs", nowMs).also { require(it <= nowMs && it >= endMs) } else null
        val version = text(json, "datasetVersion", 71)
        require(Regex("sha256:[a-f0-9]{64}").matches(version))
        val rows = json.getJSONArray("candles")
        require(rows.length() <= 20)
        val candles = (0 until rows.length()).map { index ->
            val row = rows.getJSONObject(index)
            market(row)
            require(text(row, "timeframe") == "15m" && bool(row, "isClosed"))
            require(text(row, "source") == "ccxt.binanceusdm" && text(row, "quality") == "VALIDATED" &&
                text(row, "availabilityKind") == "FIRST_OBSERVED")
            val opening = integer(row, "openTimeMs")
            val closing = integer(row, "closeTimeMs")
            val available = stamp(row, "availableAtMs", nowMs)
            require(opening >= startMs && opening < endMs && opening % step == 0L && closing == opening + step)
            require(closing <= nowMs && available >= closing && available <= (generated ?: nowMs))
            fun amount(key: String): String = decimal(row, key).also {
                val value = BigDecimal(it)
                require(it.length <= 128 && value.precision() <= 40 && value.scale() in -30..30 &&
                    value.precision() - value.scale() <= 31 && (key == "volume" || value.signum() > 0))
            }
            val open = amount("open"); val high = amount("high"); val low = amount("low"); val close = amount("close")
            require(BigDecimal(low) <= BigDecimal(high) && BigDecimal(open) >= BigDecimal(low) &&
                BigDecimal(open) <= BigDecimal(high) && BigDecimal(close) >= BigDecimal(low) && BigDecimal(close) <= BigDecimal(high))
            CanonicalCandle(opening, closing, open, high, low, close, amount("volume"), available)
        }
        require(candles.zipWithNext().all { (left, right) -> left.openTimeMs < right.openTimeMs })
        val gaps = mutableListOf<CandleGap>()
        var cursor = startMs
        candles.forEach { candle ->
            if (cursor < candle.openTimeMs) gaps += CandleGap(cursor, candle.openTimeMs)
            cursor = candle.closeTimeMs
        }
        if (cursor < endMs) gaps += CandleGap(cursor, endMs)
        val coverage = json.getJSONObject("coverage")
        require(integer(coverage, "expected") == 20L && integer(coverage, "returned") == candles.size.toLong())
        require(bool(coverage, "complete") == gaps.isEmpty())
        val reportedGaps = coverage.getJSONArray("gaps")
        require(reportedGaps.length() == gaps.size)
        gaps.forEachIndexed { index, gap ->
            val reported = reportedGaps.getJSONObject(index)
            require(integer(reported, "startMs") == gap.startMs && integer(reported, "endMs") == gap.endMs)
        }
        return CandleWindowView(startMs, endMs, generated, version, 20, candles.size, gaps.isEmpty(), gaps, candles)
    }
}

internal fun fiveLayerEndpoint(baseUrl: String, path: String): HttpUrl {
    require(path in setOf("system", "intelligence", "decision", "paper", "paper/evaluate", "paper/pause", "paper/cancel", "candles", "order-book"))
    val base = baseUrl.trim().toHttpUrl()
    require(base.isHttps && base.username.isEmpty() && base.password.isEmpty() &&
        base.query == null && base.fragment == null) { "Cần URL HTTPS không chứa mã truy cập" }
    return base.newBuilder().addPathSegments("v1/$path").build()
}

/** Last twenty already closed M15 slots; no moving asOfMs enters the dataset identity. */
internal fun fiveLayerCandleEndpoint(baseUrl: String, nowMs: Long): HttpUrl {
    require(nowMs >= 20 * 900_000L)
    val end = nowMs / 900_000L * 900_000L
    return fiveLayerEndpoint(baseUrl, "candles").newBuilder()
        .addQueryParameter("symbol", "BTCUSDT").addQueryParameter("timeframe", "15m")
        .addQueryParameter("startMs", (end - 20 * 900_000L).toString())
        .addQueryParameter("endMs", end.toString()).build()
}

internal object FiveLayerClient {
    // A POST may commit before its response is lost. Never automatically retry controls.
    private val client = OkHttpClient.Builder().callTimeout(10, TimeUnit.SECONDS)
        .retryOnConnectionFailure(false).followRedirects(false).followSslRedirects(false).build()
    private fun <T> decode(json: JSONObject, parser: (JSONObject, Long) -> T): T =
        try { parser(json, System.currentTimeMillis()) }
        catch (_: Exception) { throw FiveLayerApiException(FiveLayerFailure.INVALID_RESPONSE) }
    suspend fun getSystem(baseUrl: String, token: String): SystemView =
        decode(request(baseUrl, token, "system")) { json, _ -> FiveLayerJson.system(json) }
    suspend fun getIntelligence(baseUrl: String, token: String): IntelligenceView =
        decode(request(baseUrl, token, "intelligence"), FiveLayerJson::intelligence)
    suspend fun getDecision(baseUrl: String, token: String): DecisionView =
        decode(request(baseUrl, token, "decision"), FiveLayerJson::decision)
    suspend fun getPaper(baseUrl: String, token: String): PaperView =
        decode(request(baseUrl, token, "paper"), FiveLayerJson::ledger)
    suspend fun getCandles(baseUrl: String, token: String, nowMs: Long = System.currentTimeMillis()): CandleWindowView {
        val endpoint = fiveLayerCandleEndpoint(baseUrl, nowMs)
        val end = nowMs / 900_000L * 900_000L
        return decode(request(baseUrl, token, "candles", endpoint = endpoint)) { json, receivedAt ->
            FiveLayerJson.candles(json, end - 20 * 900_000L, end, receivedAt)
        }
    }
    suspend fun getOrderBook(baseUrl: String, token: String): HummingbotSnapshot =
        decode(request(baseUrl, token, "order-book", endpoint = fiveLayerEndpoint(baseUrl, "order-book")
            .newBuilder().addQueryParameter("symbol", "BTCUSDT").build())) { json, now ->
            HummingbotSnapshot.parse(json, "BTCUSDT", now)
        }
    suspend fun evaluate(baseUrl: String, token: String): PaperEvaluationView =
        decode(request(baseUrl, token, "paper/evaluate", JSONObject()), FiveLayerJson::evaluation)
    suspend fun setPaused(baseUrl: String, token: String, paused: Boolean): PaperView =
        decode(request(baseUrl, token, "paper/pause", JSONObject().put("paused", paused)), FiveLayerJson::ledger)
    suspend fun cancel(baseUrl: String, token: String, orderId: String): PaperOrderView {
        require(orderId.length in 1..100 && orderId.none { it.isISOControl() })
        return decode(request(baseUrl, token, "paper/cancel", JSONObject().put("orderId", orderId)), FiveLayerJson::order)
    }

    private suspend fun request(baseUrl: String, token: String, path: String, payload: JSONObject? = null,
        endpoint: HttpUrl = fiveLayerEndpoint(baseUrl, path)): JSONObject {
        require(token.length in 1..4096 && token.all { it.code in 33..126 }) { "Cần mã truy cập hợp lệ" }
        val builder = Request.Builder().url(endpoint)
            .header("Authorization", "Bearer $token").header("Accept", "application/json")
        if (payload != null) builder.post(payload.toString().toRequestBody("application/json; charset=utf-8".toMediaType()))
        val request = builder.build()
        return suspendCancellableCoroutine { continuation ->
            val call = client.newCall(request)
            continuation.invokeOnCancellation { call.cancel() }
            call.enqueue(object : Callback {
                override fun onFailure(call: Call, e: IOException) {
                    if (continuation.isActive) continuation.resumeWith(Result.failure(fiveLayerNetworkFailure(e)))
                }
                override fun onResponse(call: Call, response: Response) {
                    val result = runCatching {
                        response.use {
                            if (!it.isSuccessful) throw fiveLayerHttpFailure(it.code)
                            val source = (it.body ?: throw FiveLayerApiException(FiveLayerFailure.INVALID_RESPONSE)).source()
                            if (source.request(1_048_577L)) throw FiveLayerApiException(FiveLayerFailure.INVALID_RESPONSE)
                            try { JSONObject(source.readUtf8()) }
                            catch (_: Exception) { throw FiveLayerApiException(FiveLayerFailure.INVALID_RESPONSE) }
                        }
                    }.recoverCatching { error ->
                        throw when (error) {
                            is FiveLayerApiException -> error
                            is IOException -> fiveLayerNetworkFailure(error)
                            else -> FiveLayerApiException(FiveLayerFailure.INVALID_RESPONSE)
                        }
                    }
                    if (continuation.isActive) continuation.resumeWith(result)
                }
            })
        }
    }
}
