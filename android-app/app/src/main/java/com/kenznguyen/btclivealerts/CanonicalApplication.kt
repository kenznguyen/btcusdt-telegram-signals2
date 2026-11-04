package com.kenznguyen.btclivealerts

import android.app.Application

/** Composition root for the regular host. The parallel `.paper` variant remains a client. */
class CanonicalApplication : Application() {
    private val runtimeRegistry: CanonicalRuntimeRegistry by lazy(LazyThreadSafetyMode.SYNCHRONIZED) {
        CanonicalRuntimeRegistry(
            isCanonicalHost = !BuildConfig.PARALLEL_INSTALL,
            runtimeFactory = {
                CanonicalRuntime(
                    pathAuthority = AppPrivateCanonicalPathAuthority(
                        applicationContext.dataDir,
                    ),
                )
            },
        )
    }

    /** Null in the `.paper` variant; accessing this property never opens or creates storage. */
    val canonicalRuntime: CanonicalRuntime?
        get() = runtimeRegistry.runtime
}
