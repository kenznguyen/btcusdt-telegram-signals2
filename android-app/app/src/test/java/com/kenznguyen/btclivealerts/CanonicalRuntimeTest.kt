package com.kenznguyen.btclivealerts

import java.io.File
import java.nio.file.Files
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
import org.junit.Test

class CanonicalRuntimeTest {
    @Test
    fun pathResolutionReturnsStableAppPrivateMetadataWithoutCreatingFiles() {
        val tempRoot = Files.createTempDirectory("t0-canonical-test").toFile()
        try {
            val appData = File(tempRoot, "not-created-app-data")
            val authority = AppPrivateCanonicalPathAuthority(appData)

            assertFalse(appData.exists())
            val first = authority.resolve()
            val second = authority.resolve()

            assertEquals(File(appData, "files/canonical/t0.sqlite"), first.candidateFile)
            assertEquals(first.identity, second.identity)
            assertFalse(appData.exists())
            assertFalse(first.candidateFile.exists())
        } finally {
            tempRoot.deleteRecursively()
        }
    }

    @Test
    fun regularHostCreatesExactlyOneRuntimeOnRepeatedAccess() {
        var factoryCalls = 0
        val expected = CanonicalRuntime(AppPrivateCanonicalPathAuthority(File("/unused")))
        val registry = CanonicalRuntimeRegistry(isCanonicalHost = true) {
            factoryCalls += 1
            expected
        }

        assertSame(expected, registry.runtime)
        assertSame(expected, registry.runtime)
        assertEquals(1, factoryCalls)
    }

    @Test
    fun parallelClientNeverCreatesOrOwnsCanonicalRuntime() {
        var factoryCalls = 0
        val registry = CanonicalRuntimeRegistry(isCanonicalHost = false) {
            factoryCalls += 1
            CanonicalRuntime(AppPrivateCanonicalPathAuthority(File("/unused")))
        }

        assertNull(registry.runtime)
        assertNull(registry.runtime)
        assertEquals(0, factoryCalls)
    }

    @Test
    fun runtimeConstructionDoesNotResolveOrTouchStorage() {
        var resolveCalls = 0
        val authority = CanonicalPathAuthority {
            resolveCalls += 1
            throw AssertionError("Runtime construction must not resolve the path")
        }

        CanonicalRuntime(authority)
        assertEquals(0, resolveCalls)
    }
}
