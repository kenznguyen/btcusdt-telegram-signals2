package com.kenznguyen.btclivealerts.analytics

import com.kenznguyen.btclivealerts.Candle
import com.kenznguyen.btclivealerts.StrategyEngine
import com.kenznguyen.btclivealerts.StrategyState

/**
 * Offline-only replay. Never connects to an exchange or places orders.
 * Captures each event immediately from the engine's per-closed-candle callback,
 * before its rolling recentEvents buffer can discard historical events.
 */
object StrategyTraceReplay {
    data class Result(
        val finalState: StrategyState,
        val transitions: List<StrategyTraceExporter.Transition>,
        val json: String
    )

    fun run(
        engine: StrategyEngine,
        m15: List<Candle>,
        h1: List<Candle>,
        symbol: String,
        initialState: StrategyState = StrategyState()
    ): Result {
        require(symbol.isNotBlank()) { "Missing symbol" }
        val transitions = mutableListOf<StrategyTraceExporter.Transition>()
        val (finalState, emitted) = engine.processClosedCandles(m15, h1, initialState) { candle, before, after ->
            val previousKeys = before.recentEvents.map { it.dedupeKey }.toSet()
            val added = after.recentEvents.filterNot { it.dedupeKey in previousKeys }
            require(added.size <= 1) { "Multiple events in one candle: cannot reconstruct transitions" }
            for (event in added) {
                require(event.candleTime == candle.openTime) { "Event timestamp differs from closed candle" }
                transitions.add(StrategyTraceExporter.Transition(event, before, after))
            }
        }
        // Fail closed if rolling-state deduplication hid an emitted event.
        require(transitions.size == emitted.size &&
            transitions.map { it.event } == emitted) { "Replay event capture is incomplete" }
        return Result(finalState, transitions, StrategyTraceExporter.exportTransitions(transitions, symbol))
    }
}
