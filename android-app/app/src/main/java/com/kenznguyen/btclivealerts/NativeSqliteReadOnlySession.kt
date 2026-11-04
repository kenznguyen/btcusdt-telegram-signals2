package com.kenznguyen.btclivealerts

/** Result codes shared with the JNI implementation. Unknown native codes fail closed. */
enum class NativeSqliteStatus(val nativeCode: Int) {
    VERIFIED(0),
    INVALID_PATH(1),
    MISSING(2),
    UNREADABLE(3),
    WAL_SIDECARS_UNAVAILABLE(4),
    OPEN_FAILED(5),
    READ_ONLY_ENFORCEMENT_FAILED(6),
    READ_TRANSACTION_FAILED(7),
    SNAPSHOT_ANCHOR_FAILED(8),
    INCOMPLETE_EVIDENCE(9),
    CLOSE_FAILED(10),
    ALREADY_CLOSED(11),
    ENGINE_VERSION_UNSUPPORTED(12);

    companion object {
        fun fromNativeCode(code: Int): NativeSqliteStatus =
            entries.firstOrNull { it.nativeCode == code } ?: INCOMPLETE_EVIDENCE
    }
}

data class NativeSqliteOpenReply(
    val status: NativeSqliteStatus,
    val handle: Long,
)

internal interface NativeSqliteReadOnlyBridge {
    /** Opens an existing DB read-only and pins a DEFERRED snapshot before returning. */
    fun openPinnedSnapshot(path: String): NativeSqliteOpenReply
    /** Rolls back and closes the native connection associated with [handle]. */
    fun closeSnapshot(handle: Long): NativeSqliteStatus
}

sealed interface NativeSqliteSessionOpenResult {
    data class Opened(val session: NativeSqliteReadOnlySession) : NativeSqliteSessionOpenResult
    data class Rejected(val status: NativeSqliteStatus) : NativeSqliteSessionOpenResult
}

/**
 * Owns one native read-only connection whose DEFERRED transaction has already been
 * anchored by a database read. This deliberately exposes no SQL execution method.
 *
 * This is a low-level source boundary only; it is not wired to CanonicalRuntime or
 * the canonical writer. The writer must use the same pinned SQLite engine before
 * this session can be used against canonical storage.
 */
internal class NativeSqliteReadOnlySession private constructor(
    private val handle: Long,
    private val bridge: NativeSqliteReadOnlyBridge,
) : AutoCloseable {
    @Volatile
    var isClosed: Boolean = false
        private set

    val isOpen: Boolean
        get() = !isClosed

    @Synchronized
    fun closeAndGetStatus(): NativeSqliteStatus {
        if (isClosed) return NativeSqliteStatus.ALREADY_CLOSED
        isClosed = true
        return bridge.closeSnapshot(handle)
    }

    override fun close() {
        closeAndGetStatus()
    }

    companion object {
        fun open(
            path: String,
            bridge: NativeSqliteReadOnlyBridge,
        ): NativeSqliteSessionOpenResult {
            if (path.isBlank() || !path.startsWith("/") || path.contains('\u0000')) {
                return NativeSqliteSessionOpenResult.Rejected(NativeSqliteStatus.INVALID_PATH)
            }

            val reply = bridge.openPinnedSnapshot(path)
            if (reply.status != NativeSqliteStatus.VERIFIED) {
                return NativeSqliteSessionOpenResult.Rejected(reply.status)
            }
            if (reply.handle <= 0L) {
                return NativeSqliteSessionOpenResult.Rejected(NativeSqliteStatus.INCOMPLETE_EVIDENCE)
            }
            return NativeSqliteSessionOpenResult.Opened(NativeSqliteReadOnlySession(reply.handle, bridge))
        }
    }
}

/** JNI is loaded lazily; JVM unit tests can exercise the lifecycle through a fake bridge. */
internal object NativeSqliteReadOnlyJni {
    private val libraryLoaded: Unit by lazy { System.loadLibrary("canonical_sqlite") }

    fun openPinnedSnapshot(path: String): NativeSqliteOpenReply {
        libraryLoaded
        val result = nativeOpenPinnedSnapshot(path)
        if (result.size != 2) {
            return NativeSqliteOpenReply(NativeSqliteStatus.INCOMPLETE_EVIDENCE, 0L)
        }
        return NativeSqliteOpenReply(
            NativeSqliteStatus.fromNativeCode(result[0].toInt()),
            result[1],
        )
    }

    fun closeSnapshot(handle: Long): NativeSqliteStatus {
        libraryLoaded
        return NativeSqliteStatus.fromNativeCode(nativeCloseSnapshot(handle))
    }

    private external fun nativeOpenPinnedSnapshot(path: String): LongArray
    private external fun nativeCloseSnapshot(handle: Long): Int
}

internal object JniNativeSqliteReadOnlyBridge : NativeSqliteReadOnlyBridge {
    override fun openPinnedSnapshot(path: String): NativeSqliteOpenReply =
        NativeSqliteReadOnlyJni.openPinnedSnapshot(path)

    override fun closeSnapshot(handle: Long): NativeSqliteStatus =
        NativeSqliteReadOnlyJni.closeSnapshot(handle)
}
