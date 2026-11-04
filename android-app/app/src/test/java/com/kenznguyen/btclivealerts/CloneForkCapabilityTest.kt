package com.kenznguyen.btclivealerts

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class CloneForkCapabilityTest {
    @Test
    fun cloneIsRejectedAsUnsupported() {
        val result = CloneForkCapability.evaluate(CloneForkRequest.CLONE)

        assertEquals(CloneForkDecision.REJECT_UNSUPPORTED, result.decision)
        assertEquals(CloneForkRejectionReason.CAPABILITY_DISABLED, result.reason)
    }

    @Test
    fun forkIsRejectedAsUnsupported() {
        val result = CloneForkCapability.evaluate(CloneForkRequest.FORK)

        assertEquals(CloneForkDecision.REJECT_UNSUPPORTED, result.decision)
        assertEquals(CloneForkRejectionReason.CAPABILITY_DISABLED, result.reason)
    }

    @Test
    fun capabilityIsExplicitlyDisabled() {
        assertFalse(CloneForkCapability.isEnabled)
    }

    @Test
    fun rejectionNeverCarriesChildIdentityOrWriterAdmission() {
        for (request in CloneForkRequest.values()) {
            val result = CloneForkCapability.evaluate(request)

            assertTrue(result.childInstanceId == null)
            assertFalse(result.writerAdmissionGranted)
        }
    }

    @Test
    fun rejectionReasonIsStableAndNonBlank() {
        val result = CloneForkCapability.evaluate(CloneForkRequest.FORK)

        assertTrue(result.reason.name.isNotBlank())
        assertTrue(result.message.isNotBlank())
    }
}
