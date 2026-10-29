package com.kenznguyen.btclivealerts

/**
 * Read-only comparison. FreqAI and futures intelligence are observational inputs:
 * they never change StrategyEngine state, event lists, risk settings or alert decisions.
 */
internal data class StrategyShadowObservation(
    val baseAction: String,
    val freqaiAction: String?,
    val intelligenceStatus: String?,
    val alignment: String,
    val candleTimeMs: Long
)
internal data class StrategyShadowResult(
    val state: StrategyState,
    val events: List<StrategyEvent>,
    val observation: StrategyShadowObservation
)
internal object StrategyShadow {
    fun observe(state: StrategyState, events: List<StrategyEvent>,
                freqaiAction: String?, intelligenceStatus: String?, candleTimeMs: Long,
                validUntilMs: Long? = null, modelCandleTimeMs: Long? = null): StrategyShadowResult {
        val latest = events.lastOrNull()
        val base = latest?.kind ?: "NONE"
        val baseSide = when (latest?.side) {
            "LONG" -> "BUY"
            "SHORT" -> "SELL"
            else -> null
        }
        val model = freqaiAction?.takeIf { it in setOf("BUY", "SELL", "WAIT") }
        val status = intelligenceStatus?.takeIf { it in setOf("OBSERVED", "MISSING", "NO_ROWS") }
        val alignment = when {
            model == null || status == null -> "UNAVAILABLE"
            validUntilMs != null && validUntilMs < candleTimeMs -> "EXPIRED"
            model == "WAIT" || baseSide == null -> "NOT_COMPARABLE"
            modelCandleTimeMs == null || modelCandleTimeMs != latest?.candleTime -> "UNVERIFIED_TIME"
            model == baseSide -> "AGREE"
            else -> "DISAGREE"
        }
        return StrategyShadowResult(state, events,
            StrategyShadowObservation(base, model, status, alignment, candleTimeMs))
    }
}
