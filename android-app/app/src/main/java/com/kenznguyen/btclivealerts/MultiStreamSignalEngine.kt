package com.kenznguyen.btclivealerts

/**
 * Combines already-computed technical features and a synchronized, fresh order book.
 * This produces an analysis candidate only; it never submits or manages orders.
 */
data class TechnicalSignalInput(
    val directionScore: Double, // -1.0 = bearish, +1.0 = bullish
    val confidence: Double,     // 0.0..1.0
    val candleTimeMs: Long,
    val timeframe: String
)

data class MultiStreamSignal(
    val direction: String, // UP, DOWN, NEUTRAL
    val score: Double,
    val technicalScore: Double,
    val orderBookScore: Double?,
    val confidence: Double,
    val dataComplete: Boolean,
    val reason: String,
    val evaluatedAtMs: Long
)

class MultiStreamSignalEngine(
    private val technicalWeight: Double = 0.70,
    private val orderBookWeight: Double = 0.30,
    private val threshold: Double = 0.35,
    private val maxOrderBookAgeMs: Long = 2_000L,
    private val maxTechnicalAgeMs: Long = 20 * 60_000L
) {
    init {
        require(technicalWeight >= 0.0 && orderBookWeight >= 0.0)
        require(technicalWeight + orderBookWeight > 0.0)
        require(threshold in 0.0..1.0)
    }

    fun evaluate(
        technical: TechnicalSignalInput,
        orderBook: OrderBookMetrics?,
        nowMs: Long = System.currentTimeMillis()
    ): MultiStreamSignal {
        val techScore = technical.directionScore.coerceIn(-1.0, 1.0)
        val techConfidence = technical.confidence.coerceIn(0.0, 1.0)
        val technicalFresh = technical.candleTimeMs <= nowMs &&
            nowMs - technical.candleTimeMs <= maxTechnicalAgeMs
        val bookFresh = orderBook != null && orderBook.synchronized &&
            orderBook.updatedAtMs <= nowMs && nowMs - orderBook.updatedAtMs <= maxOrderBookAgeMs &&
            orderBook.spreadBps.isFinite() && orderBook.spreadBps >= 0.0

        if (!technicalFresh) {
            return MultiStreamSignal("NEUTRAL", 0.0, techScore, null, 0.0, false,
                "Dữ liệu kỹ thuật cũ hoặc timestamp không hợp lệ", nowMs)
        }

        val bookScore = if (bookFresh) {
            // Blend raw and proximity-weighted depth imbalance.
            (0.4 * orderBook!!.imbalance + 0.6 * orderBook.weightedImbalance).coerceIn(-1.0, 1.0)
        } else null

        val score: Double
        val confidence: Double
        val complete: Boolean
        val reason: String
        if (bookScore != null) {
            val totalWeight = technicalWeight + orderBookWeight
            score = ((techScore * technicalWeight) + (bookScore * orderBookWeight)) / totalWeight
            confidence = (techConfidence * 0.75 + (1.0 - kotlin.math.abs(bookScore - techScore) / 2.0) * 0.25)
                .coerceIn(0.0, 1.0)
            complete = true
            reason = "Đủ dữ liệu kỹ thuật + Order Book"
        } else {
            // Graceful degradation is visible: score uses technical data only, but
            // result remains explicitly incomplete and confidence is discounted.
            score = techScore
            confidence = techConfidence * 0.65
            complete = false
            reason = "Thiếu Order Book mới/đã đồng bộ; chỉ dùng kỹ thuật"
        }

        val direction = when {
            score >= threshold -> "UP"
            score <= -threshold -> "DOWN"
            else -> "NEUTRAL"
        }
        return MultiStreamSignal(direction, score, techScore, bookScore, confidence, complete, reason, nowMs)
    }
}
