package com.kenznguyen.btclivealerts

import java.util.Locale
import java.util.TreeMap

/** Every initial load and reconciliation is bound to one chart selection. */
internal class ChartMarketSession(
    val symbol: String,
    val timeframe: String,
    private val fetchCandles: suspend (String, Int, String) -> List<Candle>,
    private val fetchMarkPrice: suspend (String) -> Double
) {
    constructor(symbol: String, timeframe: String, market: MarketEngine) : this(
        symbol.uppercase(Locale.ROOT), timeframe,
        { interval, limit, selected -> market.fetchCandles(interval, limit, selected) },
        { selected -> market.fetchMarkPrice(selected) }
    )

    data class Snapshot(val candles: List<Candle>, val otherCandles: List<Candle>, val markPrice: Double)

    suspend fun snapshot(otherLimit: Int = 500): Snapshot {
        val candles = fetchCandles(timeframe, 1500, symbol)
        val other = fetchCandles(if (timeframe == "15m") "1h" else "15m", otherLimit, symbol)
        return Snapshot(candles, other, fetchMarkPrice(symbol))
    }
}

/** Invalidates callbacks already queued by a replaced connection or disposed chart. */
internal class ChartConnectionGeneration {
    private var generation = 0L
    private var closed = false

    @Synchronized fun next(): Long = ++generation
    @Synchronized fun accepts(token: Long): Boolean = !closed && token == generation
    @Synchronized fun close() { closed = true; generation++ }
}

internal class ChartCandleCache(private val capacity: Int = 1500) {
    private val candles = TreeMap<Long, Candle>()

    fun merge(candle: Candle) {
        // A late REST snapshot or live update cannot reopen a confirmed candle.
        if (candles[candle.openTime]?.closed == true && !candle.closed) return
        candles[candle.openTime] = candle
        while (candles.size > capacity) candles.pollFirstEntry()
    }

    fun mergeAll(incoming: List<Candle>) = incoming.forEach(::merge)
    fun snapshot(): List<Candle> = candles.values.toList()
}

internal data class ChartAlertIdentity(
    val symbol: String,
    val timeframe: String,
    val condition: String,
    val candleOpenTime: Long
) {
    private val normalizedSymbol = symbol.uppercase(Locale.ROOT)
    val eventKey: String get() = "$normalizedSymbol:$timeframe:$condition:$candleOpenTime"
    val preferenceKey: String get() = "chart_alert_last_${normalizedSymbol}_${timeframe}_$condition"
    val notificationKey: String get() = "chart:$eventKey"
}
