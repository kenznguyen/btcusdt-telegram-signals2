package com.kenznguyen.btclivealerts

import org.junit.Assert.assertEquals
import org.junit.Test

class D5ReadOnlyTransactionGateTest {
    private fun evidence(
        api: Int = 26,
        implementation: String = "androidx.sqlite.db.framework.FrameworkSQLiteDatabase",
        mode: D5ObservedTransactionMode = D5ObservedTransactionMode.DEFERRED,
        readOnly: Boolean = true,
        fallback: Boolean = false,
    ) = D5TransactionEvidence(api, implementation, mode, readOnly, fallback)

    @Test
    fun acceptsOnlyExplicitDeferredReadOnlyEvidenceWithoutFallback() {
        assertEquals(
            D5TransactionGateStatus.ACCEPTED,
            D5ReadOnlyTransactionGate.validate(evidence()),
        )
    }

    @Test
    fun rejectsEveryKnownUnsafeOrUnprovenPath() {
        assertEquals(D5TransactionGateStatus.API_BELOW_MINIMUM,
            D5ReadOnlyTransactionGate.validate(evidence(api = 25)))
        assertEquals(D5TransactionGateStatus.MISSING_IMPLEMENTATION,
            D5ReadOnlyTransactionGate.validate(evidence(implementation = " ")))
        assertEquals(D5TransactionGateStatus.MODE_NOT_DEFERRED,
            D5ReadOnlyTransactionGate.validate(evidence(mode = D5ObservedTransactionMode.EXCLUSIVE)))
        assertEquals(D5TransactionGateStatus.MODE_NOT_DEFERRED,
            D5ReadOnlyTransactionGate.validate(evidence(mode = D5ObservedTransactionMode.UNKNOWN)))
        assertEquals(D5TransactionGateStatus.READ_ONLY_NOT_ENFORCED,
            D5ReadOnlyTransactionGate.validate(evidence(readOnly = false)))
        assertEquals(D5TransactionGateStatus.FALLBACK_USED,
            D5ReadOnlyTransactionGate.validate(evidence(fallback = true)))
    }
}
