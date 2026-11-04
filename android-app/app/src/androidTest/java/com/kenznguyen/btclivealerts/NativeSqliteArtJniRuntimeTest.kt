package com.kenznguyen.btclivealerts

import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

/**
 * Runs inside Android ART. The native test hook opens only SQLite :memory:;
 * it never touches app storage, the canonical DB, or an exchange.
 */
@RunWith(AndroidJUnit4::class)
class NativeSqliteArtJniRuntimeTest {
    @Test
    fun artLoadsNativeLibraryAndInvokesOpenReadCloseExports() {
        val opened = NativeSqliteReadOnlyJni.openInMemoryForRuntimeTest()
        assertEquals(NativeSqliteStatus.VERIFIED, opened.status)
        assertTrue("JNI handle must be positive", opened.handle > 0L)

        try {
            val reply = NativeSqliteReadOnlyJni.readD5Snapshot(opened.handle)
            assertEquals(NativeSqliteD5ReadStatus.VERIFIED, reply.status)
            assertTrue("D5 envelope must be decoded", reply.envelope != null)
            assertEquals("3.54.1", reply.envelope?.sqliteVersion)
        } finally {
            assertEquals(
                NativeSqliteStatus.VERIFIED,
                NativeSqliteReadOnlyJni.closeSnapshot(opened.handle)
            )
        }

        assertEquals(
            NativeSqliteStatus.ALREADY_CLOSED,
            NativeSqliteReadOnlyJni.closeSnapshot(opened.handle)
        )
    }
}
