package com.kenznguyen.btclivealerts

/** Snapshot request state; callers serialize access and supply a monotonic clock. */
internal class SnapshotRetryGate {
    private var requestId = 0L
    private var inFlight = false
    private var closed = false
    private var failures = 0
    private var retryAtMs: Long? = null

    fun tryStart(nowMs: Long): Long? {
        if (closed || inFlight || remainingDelay(nowMs) > 0L) return null
        inFlight = true
        return ++requestId
    }

    fun isCurrent(id: Long): Boolean = !closed && inFlight && id == requestId

    fun remainingDelay(nowMs: Long): Long = retryAtMs?.let { (it - nowMs).coerceAtLeast(0L) } ?: 0L

    fun failed(id: Long, nowMs: Long): Long? {
        if (!isCurrent(id)) return null
        inFlight = false
        failures = (failures + 1).coerceAtMost(8)
        val delayMs = minOf(120_000L, 2_000L * (1L shl (failures - 1)))
        retryAtMs = nowMs + delayMs
        return delayMs
    }

    fun succeeded(id: Long): Boolean {
        if (!isCurrent(id)) return false
        inFlight = false
        failures = 0
        retryAtMs = null
        return true
    }

    /** An old HTTP completion must not replace the new connection's snapshot. */
    fun disconnect() {
        requestId++
        inFlight = false
    }

    fun close() {
        closed = true
        disconnect()
    }
}
