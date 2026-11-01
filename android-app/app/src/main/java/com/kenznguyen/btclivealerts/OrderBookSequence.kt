package com.kenznguyen.btclivealerts

/**
 * Pure validation helpers for Binance USDⓈ-M Futures diff-depth update ranges.
 * A depth event covers the inclusive update-ID range [U, u], and pu (when
 * present) must point to the preceding event's final update ID.
 */
internal object OrderBookSequence {
    fun bridgesSnapshot(snapshotUpdateId: Long, firstUpdateId: Long, finalUpdateId: Long): Boolean {
        if (snapshotUpdateId < 0L || firstUpdateId <= 0L || finalUpdateId < firstUpdateId) return false
        val nextUpdateId = snapshotUpdateId + 1L
        return firstUpdateId <= nextUpdateId && finalUpdateId >= nextUpdateId
    }

    fun isContiguous(
        previousUpdateId: Long,
        firstUpdateId: Long,
        finalUpdateId: Long,
        previousFinalUpdateId: Long?
    ): Boolean {
        if (previousUpdateId < 0L || firstUpdateId <= 0L || finalUpdateId < firstUpdateId) return false
        val nextUpdateId = previousUpdateId + 1L
        if (firstUpdateId > nextUpdateId || finalUpdateId < nextUpdateId) return false
        return previousFinalUpdateId == null || previousFinalUpdateId == previousUpdateId
    }
}

