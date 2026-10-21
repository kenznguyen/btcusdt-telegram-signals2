package com.kenznguyen.btclivealerts

import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.abs
import kotlin.math.max

data class StrategyPosition(
    val side: String, val qty: Double, val avgEntry: Double,
    val initialMargin: Double, val dcaMargin: Double, val entryNotional: Double,
    val entryTime: Long, val dcaUsed: Boolean
) { val reservedMargin: Double get() = initialMargin + dcaMargin }

data class StrategyEvent(
    val kind: String, val side: String?, val price: Double, val candleTime: Long,
    val roePct: Double? = null, val note: String = ""
) { val dedupeKey: String get() = kind + ":" + candleTime }

data class StrategyState(
    val balance: Double = 100.0,
    val position: StrategyPosition? = null,
    val lastProcessedOpenTime: Long = 0L,
    val recentEvents: List<StrategyEvent> = emptyList()
) {
    fun toJson(): String {
        val root = JSONObject().put("balance", balance).put("lastProcessedOpenTime", lastProcessedOpenTime)
        val p = position
        root.put("position", if (p == null) JSONObject.NULL else JSONObject()
            .put("side", p.side).put("qty", p.qty).put("avgEntry", p.avgEntry)
            .put("initialMargin", p.initialMargin).put("dcaMargin", p.dcaMargin)
            .put("entryNotional", p.entryNotional).put("entryTime", p.entryTime).put("dcaUsed", p.dcaUsed))
        val events = JSONArray()
        recentEvents.take(30).forEach { e ->
            events.put(JSONObject().put("kind", e.kind).put("side", e.side ?: JSONObject.NULL)
                .put("price", e.price).put("candleTime", e.candleTime)
                .put("roePct", e.roePct ?: JSONObject.NULL).put("note", e.note))
        }
        return root.put("recentEvents", events).toString()
    }

    companion object {
        fun fromJson(raw: String?): StrategyState = try {
            if (raw.isNullOrBlank()) StrategyState() else {
                val root = JSONObject(raw)
                val p = root.optJSONObject("position")?.let { x ->
                    StrategyPosition(x.getString("side"), x.getDouble("qty"), x.getDouble("avgEntry"),
                        x.getDouble("initialMargin"), x.optDouble("dcaMargin", 0.0),
                        x.getDouble("entryNotional"), x.getLong("entryTime"), x.optBoolean("dcaUsed", false))
                }
                val arr = root.optJSONArray("recentEvents") ?: JSONArray()
                val events = (0 until arr.length()).mapNotNull { i ->
                    val e = arr.optJSONObject(i) ?: return@mapNotNull null
                    StrategyEvent(e.optString("kind"), e.optString("side").takeUnless { it == "null" || it.isBlank() },
                        e.optDouble("price"), e.optLong("candleTime"),
                        if (e.isNull("roePct")) null else e.optDouble("roePct"), e.optString("note"))
                }
                StrategyState(root.optDouble("balance", 100.0), p, root.optLong("lastProcessedOpenTime", 0L), events)
            }
        } catch (_: Exception) { StrategyState() }
    }
}

data class IndicatorPoint(
    val rsi: Double? = null,
    val adx: Double? = null,
    val plusDi: Double? = null,
    val minusDi: Double? = null,
    val rsiPercentB: Double? = null,
    val rsiPercentBSignal: Double? = null,
    val mfiScaled: Double? = null,
    val pricePercentB: Double? = null,
    val mfiBProduct: Double? = null
)

data class StrategyConfig(
    val leverage: Double = 13.0, val rsiLength: Int = 14, val dmiLength: Int = 14,
    val adxSmoothing: Int = 14, val h1AdxEntry: Double = 20.0,
    val longRsiEntry: Double = 30.0, val shortRsiEntry: Double = 70.0,
    val longRsiTp: Double = 76.0, val shortRsiTp: Double = 24.0, val tpRoe: Double = 5.0,
    val dcaRoe: Double = -20.0, val dcaAdx: Double = 45.0,
    val shortDcaRsi: Double = 80.0, val longDcaRsi: Double = 20.0,
    val softSlRoe: Double = -35.0, val emergencySlRoe: Double = -90.0,
    val softSlAdx: Double = 35.0, val entryMarginPct: Double = 0.50,
    val dcaMarginRatio: Double = 1.00, val feeRate: Double = 0.0005,
    val slippageBps: Double = 5.0
)

/** Signal-only implementation of the Python bot/backtest rules. Never places orders. */
class StrategyEngine(val config: StrategyConfig = StrategyConfig()) {
    fun indicatorSeries(candles: List<Candle>): List<IndicatorPoint> {
        val n = candles.size
        if (n == 0) return emptyList()
        val delta = (0 until n).map { if (it == 0) null else candles[it].close - candles[it - 1].close }
        val gain = delta.map { it?.let { v -> max(v, 0.0) } }
        val loss = delta.map { it?.let { v -> max(-v, 0.0) } }
        val avgGain = rma(gain, config.rsiLength)
        val avgLoss = rma(loss, config.rsiLength)
        val rsi = (0 until n).map { i ->
            val g = avgGain[i]; val l = avgLoss[i]
            if (g == null || l == null) null else if (l == 0.0 && g > 0.0) 100.0
            else if (l == 0.0 && g == 0.0) 50.0 else 100.0 - 100.0 / (1.0 + g / l)
        }
        val tr = (0 until n).map { i ->
            val c = candles[i]
            if (i == 0) c.high - c.low else {
                val pc = candles[i - 1].close
                max(c.high - c.low, max(abs(c.high - pc), abs(c.low - pc)))
            }
        }
        val plusDm = (0 until n).map { i ->
            if (i == 0) 0.0 else {
                val up = candles[i].high - candles[i - 1].high
                val down = candles[i - 1].low - candles[i].low
                if (up > down && up > 0.0) up else 0.0
            }
        }
        val minusDm = (0 until n).map { i ->
            if (i == 0) 0.0 else {
                val up = candles[i].high - candles[i - 1].high
                val down = candles[i - 1].low - candles[i].low
                if (down > up && down > 0.0) down else 0.0
            }
        }
        val atr = rma(tr, config.dmiLength)
        val sp = rma(plusDm, config.dmiLength)
        val sm = rma(minusDm, config.dmiLength)
        val pdi = (0 until n).map { i ->
            val a = atr[i]; val p = sp[i]
            if (a == null || p == null || a == 0.0) null else 100.0 * p / a
        }
        val mdi = (0 until n).map { i ->
            val a = atr[i]; val m = sm[i]
            if (a == null || m == null || a == 0.0) null else 100.0 * m / a
        }
        val dx = (0 until n).map { i ->
            val p = pdi[i]; val m = mdi[i]
            if (p == null || m == null || p + m == 0.0) null else 100.0 * abs(p - m) / (p + m)
        }
        val adx = rma(dx, config.adxSmoothing)

        // Bollinger %B applied to RSI(14): 20-period SMA, 2 standard deviations.
        // Signal line is a 5-period EMA of %B. These are chart-only indicators;
        // strategy entry/exit rules continue using the existing RSI/ADX series.
        val percentB = MutableList<Double?>(n) { null }
        for (i in 19 until n) {
            val window = (i - 19..i).mapNotNull { rsi[it] }
            if (window.size != 20) continue
            val mean = window.average()
            val variance = window.map { (it - mean) * (it - mean) }.average()
            val deviation = kotlin.math.sqrt(variance)
            val upper = mean + 2.0 * deviation
            val lower = mean - 2.0 * deviation
            percentB[i] = if (upper - lower <= 1e-12) 0.5 else ((rsi[i]!! - lower) / (upper - lower)).coerceIn(-2.0, 3.0)
        }
        val percentBSignal = MutableList<Double?>(n) { null }
        var ema: Double? = null
        val alpha = 2.0 / 6.0
        percentB.indices.forEach { i ->
            val value = percentB[i]
            if (value != null) {
                ema = if (ema == null) value else alpha * value + (1.0 - alpha) * ema!!
                percentBSignal[i] = ema
            }
        }

        // MFI & %B [seiglerj] port for the chart pane only.
        // source = HLC3; MFI length 14; Bollinger length 20 and 2 population standard deviations.
        // Keep the original RSI-%B series above for compatibility, but the UI now plots this combined indicator.
        val source = candles.map { (it.high + it.low + it.close) / 3.0 }
        val mfiScaled = MutableList<Double?>(n) { null }
        for (i in 13 until n) {
            var positiveFlow = 0.0
            var negativeFlow = 0.0
            for (j in (i - 13)..i) {
                if (j == 0) continue
                val flow = source[j] * candles[j].volume
                when {
                    source[j] > source[j - 1] -> positiveFlow += flow
                    source[j] < source[j - 1] -> negativeFlow += flow
                }
            }
            val totalFlow = positiveFlow + negativeFlow
            val mfi = if (totalFlow <= 0.0) 50.0 else 100.0 * positiveFlow / totalFlow
            mfiScaled[i] = (mfi - 20.0) / (80.0 - 20.0)
        }

        val pricePercentB = MutableList<Double?>(n) { null }
        for (i in 19 until n) {
            val window = source.subList(i - 19, i + 1)
            val mean = window.average()
            val variance = window.map { (it - mean) * (it - mean) }.average()
            val deviation = 2.0 * kotlin.math.sqrt(variance)
            val upper = mean + deviation
            val lower = mean - deviation
            pricePercentB[i] = if (upper - lower <= 1e-12) 0.5 else (source[i] - lower) / (upper - lower)
        }

        val mfiBProduct = MutableList<Double?>(n) { i ->
            val mfi = mfiScaled[i]
            val bbp = pricePercentB[i]
            if (mfi == null || bbp == null) null
            else when {
                mfi > 0.5 && bbp > 0.5 -> minOf(mfi, bbp)
                mfi < 0.5 && bbp < 0.5 -> maxOf(mfi, bbp)
                else -> (mfi + bbp) / 2.0
            }
        }
        return (0 until n).map {
            IndicatorPoint(rsi[it], adx[it], pdi[it], mdi[it], percentB[it], percentBSignal[it],
                mfiScaled[it], pricePercentB[it], mfiBProduct[it])
        }
    }

    fun processClosedCandles(m15: List<Candle>, h1: List<Candle>, oldState: StrategyState, onCandle: ((Candle, StrategyState) -> Unit)? = null): Pair<StrategyState, List<StrategyEvent>> {
        val candles = m15.filter { it.closed }.sortedBy { it.openTime }
        val hours = h1.filter { it.closed }.sortedBy { it.openTime }
        if (candles.size < 2) return oldState to emptyList()
        val mi = indicatorSeries(candles)
        val hi = indicatorSeries(hours)
        var state = oldState
        val emitted = mutableListOf<StrategyEvent>()
        // H1 candles are sorted. Advance a cursor instead of scanning the entire H1 list for every M15 candle.
        var hidx = 0
        for (i in candles.indices) {
            val c = candles[i]
            if (c.openTime <= state.lastProcessedOpenTime || i == 0) continue
            val prevRsi = mi[i - 1].rsi
            val rsi = mi[i].rsi
            val adx = mi[i].adx

            val hasRsi = prevRsi != null && rsi != null
            // Warm-up candles cannot create RSI-dependent entries or exits, but price-based
            // emergency stops must still be evaluated for an already-open position.
            if (!hasRsi && state.position == null) {
                state = state.copy(lastProcessedOpenTime = c.openTime)
                onCandle?.invoke(c, state)
                continue
            }

            val hourBucket = c.openTime - c.openTime % 3_600_000L
            while (hidx + 1 < hours.size && hours[hidx + 1].openTime < hourBucket) hidx++
            val hasPriorClosedHour = hours.getOrNull(hidx)?.openTime?.let { it < hourBucket } == true
            val hp = if (hasPriorClosedHour) hi.getOrNull(hidx)?.plusDi else null
            val hm = if (hasPriorClosedHour) hi.getOrNull(hidx)?.minusDi else null
            val ha = if (hasPriorClosedHour) hi.getOrNull(hidx)?.adx else null
            val hasHourIndicators = hp != null && hm != null && ha != null
            val goLong = hasRsi && hasHourIndicators && adx != null && longEntrySignal(prevRsi!!, rsi!!, hp!!, hm!!, ha!!)
            val goShort = hasRsi && hasHourIndicators && adx != null && shortEntrySignal(prevRsi!!, rsi!!, hp!!, hm!!, ha!!)
            val pos = state.position
            var exited = false
            if (pos != null) {
                val roe = roeFor(pos.side, pos.avgEntry, c.close)
                val emergencyPrice = thresholdPrice(pos.side, pos.avgEntry, abs(config.emergencySlRoe))
                val softPrice = thresholdPrice(pos.side, pos.avgEntry, abs(config.softSlRoe))
                val emergency = emergencyStopTriggered(pos.side, c.low, c.high, pos.avgEntry)
                val prev = candles[i - 1]
                val soft = hasHourIndicators && softStopTriggered(
                    pos.side, c.low, c.high, c.open, c.close, prev.open, prev.close,
                    hp!!, hm!!, ha!!, pos.avgEntry
                )
                val tp = rsi != null && takeProfitSignal(pos.side, rsi, roe)
                val reason = when { emergency -> "EMERGENCY SL"; soft -> "SOFT SL"; tp -> "TAKE PROFIT"; else -> null }
                if (reason != null) {
                    val exit = when (reason) {
                        "EMERGENCY SL" -> stopFillPrice(pos.side, emergencyPrice, c.open)
                        "SOFT SL" -> stopFillPrice(pos.side, softPrice, c.open)
                        else -> executionFillPrice(c.close, if (pos.side == "LONG") "SELL" else "BUY")
                    }
                    val gross = if (pos.side == "LONG") (exit - pos.avgEntry) * pos.qty else (pos.avgEntry - exit) * pos.qty
                    val fees = (pos.entryNotional + exit * pos.qty) * config.feeRate
                    val net = gross - fees
                    val closedRoe = if (pos.reservedMargin > 0.0) net / pos.reservedMargin * 100.0 else 0.0
                    state = state.copy(balance = state.balance + net, position = null)
                    val ev = StrategyEvent(reason, pos.side, exit, c.openTime, roe,
                        "PnL ròng ước tính " + "%.4f".format(net) + " USDT; phí " + "%.4f".format(fees) +
                            " USDT; ROE sau phí " + "%.2f".format(closedRoe) + "%")
                    emitted += ev; state = addEvent(state, ev); exited = true
                }
            }
            if (state.position == null && !exited && state.balance > 0.0 && (goLong || goShort)) {
                val side = if (goLong) "LONG" else "SHORT"
                val margin = state.balance * config.entryMarginPct
                val action = if (side == "LONG") "BUY" else "SELL"
                val fillPrice = executionFillPrice(c.close, action)
                val qty = margin * config.leverage / fillPrice
                state = state.copy(position = StrategyPosition(side, qty, fillPrice, margin, 0.0, qty * fillPrice, c.openTime, false))
                val ev = StrategyEvent(if (side == "LONG") "LONG ENTRY" else "SHORT ENTRY", side, fillPrice, c.openTime,
                    note = "Margin mô phỏng " + "%.2f".format(margin) + " USDT; giá khớp đã tính trượt giá; khối lượng " + "%.8f".format(qty) + " BTC")
                emitted += ev; state = addEvent(state, ev)
            } else if (state.position != null && !exited) {
                val p = state.position!!
                if (!p.dcaUsed) {
                    val currentRoe = roeFor(p.side, p.avgEntry, c.close)
                    val condition = adx != null && rsi != null && prevRsi != null && dcaSignal(p.side, currentRoe, adx, rsi, prevRsi)
                    if (condition) {
                        val addMargin = p.initialMargin * config.dcaMarginRatio
                        val available = max(0.0, state.balance - p.reservedMargin)
                        if (addMargin > 0.0 && addMargin <= available + 1e-9) {
                            val action = if (p.side == "LONG") "BUY" else "SELL"
                            val fillPrice = executionFillPrice(c.close, action)
                            val addQty = addMargin * config.leverage / fillPrice
                            val qty = p.qty + addQty
                            val avg = (p.avgEntry * p.qty + fillPrice * addQty) / qty
                            state = state.copy(position = p.copy(qty = qty, avgEntry = avg,
                                dcaMargin = p.dcaMargin + addMargin, entryNotional = p.entryNotional + fillPrice * addQty, dcaUsed = true))
                            val ev = StrategyEvent("DCA", p.side, fillPrice, c.openTime, currentRoe,
                                "DCA margin " + "%.2f".format(addMargin) + " USDT; đã tính trượt giá; giá vốn TB " + "%.2f".format(avg))
                            emitted += ev; state = addEvent(state, ev)
                        }
                    }
                }
            }
            state = state.copy(lastProcessedOpenTime = c.openTime)
            onCandle?.invoke(c, state)
        }
        return state to emitted
    }


    /**
     * Returns an entry candidate only when the latest CLOSED M15 candle satisfies
     * the same entry rules used by processClosedCandles. Analysis only.
     */
    fun latestClosedEntryCandidate(m15: List<Candle>, h1: List<Candle>): String? {
        val candles = m15.filter { it.closed }.sortedBy { it.openTime }
        val hours = h1.filter { it.closed }.sortedBy { it.openTime }
        if (candles.size < 2 || hours.isEmpty()) return null
        val m15Points = indicatorSeries(candles)
        val h1Points = indicatorSeries(hours)
        val i = candles.lastIndex
        val previousRsi = m15Points[i - 1].rsi ?: return null
        val rsi = m15Points[i].rsi ?: return null
        if (m15Points[i].adx == null) return null
        val hourBucket = candles[i].openTime - candles[i].openTime % 3_600_000L
        val hourIndex = hours.indexOfLast { it.openTime < hourBucket }
        if (hourIndex < 0) return null
        val h1Point = h1Points[hourIndex]
        val plus = h1Point.plusDi ?: return null
        val minus = h1Point.minusDi ?: return null
        val adx = h1Point.adx ?: return null
        if (longEntrySignal(previousRsi, rsi, plus, minus, adx)) return "BUY"
        if (shortEntrySignal(previousRsi, rsi, plus, minus, adx)) return "SELL"
        return null
    }
    /** Intrabar candidate for EARLY WARNING only. Never used to create strategy positions. */
    fun earlyEntryCandidate(m15: List<Candle>, h1: List<Candle>): String? {
        val closed = m15.filter { it.closed }.sortedBy { it.openTime }
        val forming = m15.filterNot { it.closed }.maxByOrNull { it.openTime } ?: return null
        val hours = h1.filter { it.closed }.sortedBy { it.openTime }
        if (closed.size < 2 || hours.isEmpty()) return null
        if (forming.openTime <= closed.last().openTime) return null
        val series = indicatorSeries(closed + forming)
        val previousRsi = series[closed.lastIndex].rsi ?: return null
        val currentRsi = series.last().rsi ?: return null
        val hourBucket = forming.openTime - forming.openTime % 3_600_000L
        val hourIndex = hours.indexOfLast { it.openTime < hourBucket }
        if (hourIndex < 0) return null
        val hp = indicatorSeries(hours)[hourIndex]
        val plus = hp.plusDi ?: return null
        val minus = hp.minusDi ?: return null
        val adx = hp.adx ?: return null
        // Early warnings use proximity to the entry threshold, not a confirmed cross.
        return when {
            plus > minus && adx > config.h1AdxEntry &&
                previousRsi > config.longRsiEntry && currentRsi <= config.longRsiEntry + 3.0 -> "EARLY BUY"
            minus > plus && adx > config.h1AdxEntry &&
                previousRsi < config.shortRsiEntry && currentRsi >= config.shortRsiEntry - 3.0 -> "EARLY SELL"
            else -> null
        }
    }

    fun longEntrySignal(previousRsi: Double, rsi: Double, h1PlusDi: Double, h1MinusDi: Double, h1Adx: Double): Boolean =
        h1PlusDi > h1MinusDi && h1Adx > config.h1AdxEntry &&
            previousRsi <= config.longRsiEntry && rsi > config.longRsiEntry

    fun shortEntrySignal(previousRsi: Double, rsi: Double, h1PlusDi: Double, h1MinusDi: Double, h1Adx: Double): Boolean =
        h1MinusDi > h1PlusDi && h1Adx > config.h1AdxEntry &&
            previousRsi >= config.shortRsiEntry && rsi < config.shortRsiEntry

    fun takeProfitSignal(side: String, rsi: Double, roePct: Double): Boolean =
        if (side == "LONG") rsi >= config.longRsiTp && roePct >= config.tpRoe
        else rsi <= config.shortRsiTp && roePct >= config.tpRoe

    fun dcaSignal(side: String, roePct: Double, adx: Double, rsi: Double, previousRsi: Double): Boolean =
        roePct <= config.dcaRoe && adx > config.dcaAdx &&
            (if (side == "LONG") rsi > config.longDcaRsi && rsi > previousRsi
             else rsi < config.shortDcaRsi && rsi < previousRsi)

    fun emergencyStopTriggered(side: String, low: Double, high: Double, avgEntry: Double): Boolean {
        val threshold = thresholdPrice(side, avgEntry, abs(config.emergencySlRoe))
        return if (side == "LONG") low <= threshold else high >= threshold
    }

    fun softStopTriggered(side: String, low: Double, high: Double, candleOpen: Double, candleClose: Double,
                          previousOpen: Double, previousClose: Double, h1PlusDi: Double, h1MinusDi: Double,
                          h1Adx: Double, avgEntry: Double): Boolean {
        val threshold = thresholdPrice(side, avgEntry, abs(config.softSlRoe))
        val reversal = (if (side == "LONG") h1MinusDi > h1PlusDi else h1PlusDi > h1MinusDi) && h1Adx > config.softSlAdx
        return if (side == "LONG") low <= threshold && reversal && candleOpen > candleClose && previousClose < previousOpen
        else high >= threshold && reversal && candleClose > candleOpen && previousClose > previousOpen
    }

    /** Mark-to-market equity includes accumulated entry notional (including DCA),
     * estimated exit notional, exit slippage and both sides' fees. No state is mutated. */
    fun markToMarketEquity(state: StrategyState, markPrice: Double): Double {
        val position = state.position ?: return state.balance
        if (!markPrice.isFinite() || markPrice <= 0.0) return state.balance
        val exitAction = if (position.side == "LONG") "SELL" else "BUY"
        val exitFill = executionFillPrice(markPrice, exitAction)
        val gross = if (position.side == "LONG")
            (exitFill - position.avgEntry) * position.qty
        else (position.avgEntry - exitFill) * position.qty
        val fees = (position.entryNotional + exitFill * position.qty) * config.feeRate
        return state.balance + gross - fees
    }

    fun roeFor(side: String, avg: Double, price: Double): Double =
        if (side == "LONG") (price - avg) / avg * config.leverage * 100.0
        else (avg - price) / avg * config.leverage * 100.0

    fun thresholdPrice(side: String, avg: Double, absRoe: Double): Double {
        val move = abs(absRoe) / (100.0 * config.leverage)
        return if (side == "LONG") avg * (1.0 - move) else avg * (1.0 + move)
    }

    fun stopFillPrice(side: String, stop: Double, open: Double): Double {
        val reference = if (side == "LONG") { if (open <= stop) open else stop }
                        else { if (open >= stop) open else stop }
        return executionFillPrice(reference, if (side == "LONG") "SELL" else "BUY")
    }

    fun executionFillPrice(price: Double, action: String): Double {
        val slip = max(0.0, config.slippageBps) / 10000.0
        return price * if (action.uppercase() == "BUY") 1.0 + slip else 1.0 - slip
    }

    private fun addEvent(state: StrategyState, e: StrategyEvent) =
        state.copy(recentEvents = (listOf(e) + state.recentEvents.filterNot { it.dedupeKey == e.dedupeKey }).take(30))

    private fun rma(values: List<Double?>, length: Int): List<Double?> {
        val out = MutableList<Double?>(values.size) { null }
        val valid = values.indices.filter { values[it] != null }
        if (valid.size < length) return out
        val first = valid[length - 1]
        var prev = valid.take(length).mapNotNull { values[it] }.average()
        out[first] = prev
        for (i in (first + 1) until values.size) {
            val v = values[i]
            if (v != null) prev = (prev * (length - 1) + v) / length
            out[i] = prev
        }
        return out
    }
}
