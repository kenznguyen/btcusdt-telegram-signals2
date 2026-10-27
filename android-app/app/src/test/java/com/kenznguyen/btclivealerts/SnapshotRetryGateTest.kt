package com.kenznguyen.btclivealerts

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

class SnapshotRetryGateTest {
    @Test fun depthEventsCannotBypassSnapshotFailureBackoff() {
        val gate = SnapshotRetryGate()
        val first = gate.tryStart(0L)!!
        assertEquals(2_000L, gate.failed(first, 0L))

        // A healthy depth stream keeps arriving every 100 ms while REST is failing.
        for (time in 0L until 2_000L step 100L) assertNull(gate.tryStart(time))
        val retry = gate.tryStart(2_000L)!!
        assertNull(gate.tryStart(2_001L)) // only one HTTP request may be active
        assertEquals(4_000L, gate.failed(retry, 2_010L))
        assertNull(gate.tryStart(6_009L))
        assertNotNull(gate.tryStart(6_010L))
    }

    @Test fun repeatedFailuresCapAtTwoMinutesAndSuccessResetsBackoff() {
        val gate = SnapshotRetryGate()
        var now = 0L
        for (expected in listOf(2_000L, 4_000L, 8_000L, 16_000L, 32_000L, 64_000L, 120_000L, 120_000L)) {
            val request = gate.tryStart(now)!!
            assertEquals(expected, gate.failed(request, now))
            now += expected
        }
        val recovered = gate.tryStart(now)!!
        gate.succeeded(recovered)
        val later = gate.tryStart(now)!!
        assertEquals(2_000L, gate.failed(later, now))
    }

    @Test fun reconnectPreservesBackoffAndRejectsOldHttpCompletions() {
        val gate = SnapshotRetryGate()
        val oldRequest = gate.tryStart(0L)!!
        gate.failed(oldRequest, 0L)
        gate.disconnect()
        assertNull(gate.tryStart(1_000L))
        val newRequest = gate.tryStart(2_000L)!!
        assertFalse(gate.succeeded(oldRequest))
        assertNull(gate.failed(oldRequest, 2_001L))
        assertNull(gate.tryStart(2_001L))
        gate.succeeded(newRequest)
        assertNotNull(gate.tryStart(2_002L))
    }

    @Test fun closePreventsRetryAndLateCompletion() {
        val gate = SnapshotRetryGate()
        val active = gate.tryStart(0L)!!
        gate.close()
        assertNull(gate.failed(active, 1L))
        assertFalse(gate.succeeded(active))
        assertNull(gate.tryStart(1_000_000L))
    }
}
