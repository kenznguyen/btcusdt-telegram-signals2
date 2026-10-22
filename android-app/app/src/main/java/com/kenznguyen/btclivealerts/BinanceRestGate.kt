package com.kenznguyen.btclivealerts

import kotlinx.coroutines.delay
import okhttp3.Response
import java.util.concurrent.TimeUnit

/**
 * Process-wide Binance Futures REST pacing and ban circuit breaker.
 * A 418 defaults to a conservative 15-minute pause; Retry-After is honored when present.
 */
internal object BinanceRestGate {
    private const val MIN_SPACING_MS = 500L
    private const val DEFAULT_418_COOLDOWN_MS = 15L * 60L * 1000L
    private const val MAX_RETRY_AFTER_MS = 24L * 60L * 60L * 1000L
    private val lock = Any()
    private var blockedUntilMs = 0L
    private var nextRequestAtMs = 0L
    private var lastBlockReason: String? = null

    suspend fun awaitPermit() {
        val waitMs = synchronized(lock) {
            val now = System.currentTimeMillis()
            val permittedAt = maxOf(now, blockedUntilMs, nextRequestAtMs)
            nextRequestAtMs = permittedAt + MIN_SPACING_MS
            permittedAt - now
        }
        if (waitMs > 0) delay(waitMs)
        // A 418/429 may have arrived while this caller was waiting; re-check before proceeding.
        val remaining = synchronized(lock) { (blockedUntilMs - System.currentTimeMillis()).coerceAtLeast(0L) }
        if (remaining > 0L) {
            delay(remaining)
            awaitPermit()
        }
    }

    fun observe(response: Response) {
        if (response.code != 418 && response.code != 429) return
        val now = System.currentTimeMillis()
        val retryAfterMs = response.header("Retry-After")?.trim()?.toLongOrNull()
            ?.let { TimeUnit.SECONDS.toMillis(it.coerceAtLeast(0L)) }
            ?.coerceAtMost(MAX_RETRY_AFTER_MS)
        val cooldown = when (response.code) {
            418 -> maxOf(DEFAULT_418_COOLDOWN_MS, retryAfterMs ?: 0L)
            else -> maxOf(60_000L, retryAfterMs ?: 0L)
        }
        synchronized(lock) {
            blockedUntilMs = maxOf(blockedUntilMs, now + cooldown)
            lastBlockReason = "HTTP ${response.code}"
            nextRequestAtMs = maxOf(nextRequestAtMs, blockedUntilMs)
        }
    }

    fun currentBlockReason(): String? = synchronized(lock) {
        if (System.currentTimeMillis() < blockedUntilMs) lastBlockReason else null
    }

    fun blockedUntil(): Long = synchronized(lock) { blockedUntilMs }

    // Test-only reset for deterministic unit tests.
    internal fun resetForTests() = synchronized(lock) {
        blockedUntilMs = 0L
        nextRequestAtMs = 0L
        lastBlockReason = null
    }
}
