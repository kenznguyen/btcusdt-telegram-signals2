package com.kenznguyen.btclivealerts

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

class ForecastPaperTrackerSettlementTest {
    private fun forecast() = ForecastSnapshot(
        generatedAtMs = 100_000L,
        targetAtMs = 400_000L,
        referencePrice = 100.0,
        probabilityUp = 0.4,
        probabilityDown = 0.4,
        probabilitySideways = 0.2,
        lowerPrice = 98.0,
        medianPrice = 100.0,
        upperPrice = 102.0,
        historicalSamples = 200,
        modelVersion = "test",
        validationStatus = "TEST"
    )

    @Test fun anyHigherFinalPriceIsUpEvenBelowLegacySidewaysThreshold() {
        val result = ForecastPaperTracker.settle(forecast(), 100.0001, 400_000L)
        assertNotNull(result)
        assertEquals(ForecastClass.UP, result!!.actualClass)
    }

    @Test fun anyLowerFinalPriceIsDownEvenBelowLegacySidewaysThreshold() {
        val result = ForecastPaperTracker.settle(forecast(), 99.9999, 400_000L)
        assertNotNull(result)
        assertEquals(ForecastClass.DOWN, result!!.actualClass)
    }

    @Test fun exactlyEqualFinalPriceIsTie() {
        val result = ForecastPaperTracker.settle(forecast(), 100.0, 400_000L)
        assertNotNull(result)
        assertEquals(ForecastClass.SIDEWAYS, result!!.actualClass)
    }

    @Test fun forecastCannotSettleBeforeTargetTime() {
        assertNull(ForecastPaperTracker.settle(forecast(), 101.0, 399_999L))
    }
}
