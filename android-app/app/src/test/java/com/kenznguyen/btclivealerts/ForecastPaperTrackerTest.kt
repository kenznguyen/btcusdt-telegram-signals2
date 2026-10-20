package com.kenznguyen.btclivealerts

import org.junit.Assert.*
import org.junit.Test

class ForecastPaperTrackerTest {
    private fun sampleForecast() = ForecastSnapshot(
        generatedAtMs = 1_000L,
        targetAtMs = 301_000L,
        referencePrice = 100.0,
        probabilityUp = 0.6,
        probabilityDown = 0.2,
        probabilitySideways = 0.2,
        lowerPrice = 98.0,
        medianPrice = 101.0,
        upperPrice = 103.0,
        historicalSamples = 200
    )

    @Test fun doesNotSettleBeforeTargetTime() {
        assertNull(ForecastPaperTracker.settle(sampleForecast(), 102.0, 300_999L))
    }

    @Test fun settlesDirectionAndMetricsAfterTargetTime() {
        val result = ForecastPaperTracker.settle(sampleForecast(), 102.0, 301_000L)
        assertNotNull(result)
        assertEquals(ForecastClass.UP, result!!.actualClass)
        assertEquals(ForecastClass.UP, result.predictedClass)
        assertEquals(1.0, result.absolutePriceError, 1e-9)
        assertTrue(result.intervalCovered)
        assertEquals(0.24, result.multiclassBrierScore, 1e-9)
    }

    @Test fun rejectsInvalidPricesAndProbabilities() {
        assertNull(ForecastPaperTracker.settle(sampleForecast(), Double.NaN, 301_000L))
        val invalid = sampleForecast().copy(probabilityUp = 1.2)
        assertNull(ForecastPaperTracker.settle(invalid, 102.0, 301_000L))
    }
}
