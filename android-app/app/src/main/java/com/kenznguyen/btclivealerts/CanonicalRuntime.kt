package com.kenznguyen.btclivealerts

import java.io.File

/** A stable identifier for the canonical database; deliberately not a path or SQL capability. */
@JvmInline
value class CanonicalDatabaseIdentity internal constructor(internal val token: String)

data class CanonicalDatabaseLocation internal constructor(
    val candidateFile: File,
    val identity: CanonicalDatabaseIdentity,
)

fun interface CanonicalPathAuthority {
    /** Returns metadata only. Implementations must not create, open, or inspect the target. */
    fun resolve(): CanonicalDatabaseLocation
}

/** Resolves one app-private candidate path without touching the filesystem. */
class AppPrivateCanonicalPathAuthority(
    private val appDataDirectory: File,
) : CanonicalPathAuthority {
    override fun resolve(): CanonicalDatabaseLocation = CanonicalDatabaseLocation(
        candidateFile = File(appDataDirectory, CANONICAL_DATABASE_RELATIVE_PATH),
        identity = CANONICAL_DATABASE_IDENTITY,
    )

    private companion object {
        const val CANONICAL_DATABASE_RELATIVE_PATH = "files/canonical/t0.sqlite"
        val CANONICAL_DATABASE_IDENTITY = CanonicalDatabaseIdentity("t0-canonical-sqlite-v1")
    }
}

/** Side-effect-free holder; this class does not open SQLite or start any worker/service. */
class CanonicalRuntime internal constructor(
    val pathAuthority: CanonicalPathAuthority,
)

/** Thread-safe, application-scoped, lazy owner. Non-host variants never invoke the factory. */
class CanonicalRuntimeRegistry(
    private val isCanonicalHost: Boolean,
    runtimeFactory: () -> CanonicalRuntime,
) {
    private val runtimeDelegate = lazy(LazyThreadSafetyMode.SYNCHRONIZED) {
        if (isCanonicalHost) runtimeFactory() else null
    }

    val runtime: CanonicalRuntime?
        get() = runtimeDelegate.value
}
