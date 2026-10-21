package com.kenznguyen.btclivealerts

import kotlin.math.abs

data class OrderBookLevel(val price: Double, val quantity: Double)

data class OrderBookMetrics(
    val bestBid: Double,
    val bestAsk: Double,
    val spreadBps: Double,
    val bidDepth: Double,
    val askDepth: Double,
    val imbalance: Double,
    val weightedImbalance: Double,
    val updateId: Long,
    val updatedAtMs: Long,
    val synchronized: Boolean
) {
    val midPrice: Double get() = (bestBid + bestAsk) / 2.0
}

/** Pure calculations for a synchronized Binance USDⓈ-M Futures BTCUSDT order book. */
object OrderBookAnalytics {
    fun calculate(
        bids: List<OrderBookLevel>,
        asks: List<OrderBookLevel>,
        updateId: Long,
        updatedAtMs: Long,
        synchronized: Boolean,
        depthLevels: Int = 20
    ): OrderBookMetrics? {
        if (!synchronized || bids.isEmpty() || asks.isEmpty() || depthLevels <= 0) return null
        val bestBid = bids.maxOf { it.price }
        val bestAsk = asks.minOf { it.price }
        if (bestBid <= 0.0 || bestAsk <= bestBid) return null

        val selectedBids = bids.sortedByDescending { it.price }.take(depthLevels)
        val selectedAsks = asks.sortedBy { it.price }.take(depthLevels)
        val bidDepth = selectedBids.sumOf { it.quantity.coerceAtLeast(0.0) }
        val askDepth = selectedAsks.sumOf { it.quantity.coerceAtLeast(0.0) }
        val total = bidDepth + askDepth
        val imbalance = if (total == 0.0) 0.0 else (bidDepth - askDepth) / total
        val mid = (bestBid + bestAsk) / 2.0

        fun weighted(levels: List<OrderBookLevel>): Double =
            levels.sumOf { level ->
                val distanceBps = abs(level.price - mid) / mid * 10_000.0
                level.quantity.coerceAtLeast(0.0) / (1.0 + distanceBps)
            }

        val weightedBid = weighted(selectedBids)
        val weightedAsk = weighted(selectedAsks)
        val weightedTotal = weightedBid + weightedAsk
        val weightedImbalance =
            if (weightedTotal == 0.0) 0.0 else (weightedBid - weightedAsk) / weightedTotal

        return OrderBookMetrics(
            bestBid = bestBid,
            bestAsk = bestAsk,
            spreadBps = (bestAsk - bestBid) / mid * 10_000.0,
            bidDepth = bidDepth,
            askDepth = askDepth,
            imbalance = imbalance.coerceIn(-1.0, 1.0),
            weightedImbalance = weightedImbalance.coerceIn(-1.0, 1.0),
            updateId = updateId,
            updatedAtMs = updatedAtMs,
            synchronized = true
        )
    }
}
