package com.kenznguyen.btclivealerts

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class OrderBookSequenceTest {
    @Test
    fun firstEventBridgesSnapshotWhenItContainsNextUpdateId() {
        assertTrue(OrderBookSequence.bridgesSnapshot(100L, 99L, 101L))
        assertTrue(OrderBookSequence.bridgesSnapshot(100L, 101L, 101L))
    }

    @Test
    fun eventThatEndsAtSnapshotIdIsNotAValidBridge() {
        assertFalse(OrderBookSequence.bridgesSnapshot(100L, 98L, 100L))
    }

    @Test
    fun gapAfterSnapshotRequiresResynchronization() {
        assertFalse(OrderBookSequence.bridgesSnapshot(100L, 102L, 103L))
    }

    @Test
    fun nextEventMustCoverNextIdAndLinkPreviousFinalId() {
        assertTrue(OrderBookSequence.isContiguous(101L, 102L, 103L, 101L))
        assertFalse(OrderBookSequence.isContiguous(101L, 103L, 104L, 101L))
        assertFalse(OrderBookSequence.isContiguous(101L, 102L, 103L, 100L))
    }

    @Test
    fun overlappingUpdateRangeIsAllowedWhenPreviousIdMatches() {
        assertTrue(OrderBookSequence.isContiguous(105L, 104L, 107L, 105L))
    }

    @Test
    fun malformedUpdateRangeIsRejected() {
        assertFalse(OrderBookSequence.isContiguous(105L, 108L, 107L, 105L))
    }
}
