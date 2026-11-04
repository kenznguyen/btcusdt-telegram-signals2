package com.kenznguyen.btclivealerts

import java.io.File

/** Stable logical role; it is not a physical database or installation identity. */
@JvmInline
value class CanonicalDatabaseRoleId internal constructor(val value: String) {
    companion object {
        private const val CANONICAL_T0 = "t0-canonical-sqlite-v1"

        fun canonicalT0(): CanonicalDatabaseRoleId = CanonicalDatabaseRoleId(CANONICAL_T0)

        fun fromPersisted(value: String): CanonicalDatabaseRoleId {
            require(value.isNotBlank() && value.length <= 128 && value.none(Char::isISOControl)) {
                "Invalid canonical database role ID"
            }
            return CanonicalDatabaseRoleId(value)
        }
    }
}

data class CanonicalDatabaseLocation internal constructor(
    val candidateFile: File,
    val roleId: CanonicalDatabaseRoleId,
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
        roleId = CanonicalDatabaseRoleId.canonicalT0(),
    )

    private companion object {
        const val CANONICAL_DATABASE_RELATIVE_PATH = "files/canonical/t0.sqlite"
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
