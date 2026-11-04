package com.kenznguyen.btclivealerts

import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
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
            val envelope = requireNotNull(reply.envelope) { "D5 envelope must be decoded" }
            assertEquals("3.54.1", envelope.runtime.sqliteVersion)
            assertTrue(envelope.catalog.any { it.type == "table" && it.name == "parent" })
            assertTrue(envelope.catalog.any { it.type == "table" && it.name == "child" })
            assertTrue(envelope.catalog.any { it.type == "view" && it.name == "child_view" })
            assertTrue(envelope.tableColumns.any {
                it.tableName == "child" && it.name == "generated" && it.hidden == 3
            })
            assertTrue(envelope.indexes.any { it.name == "idx_child_value" && it.partial })
            assertTrue(envelope.indexColumns.any {
                it.indexName == "idx_child_value" && it.descending && it.isKey
            })
            assertTrue(envelope.foreignKeys.any {
                it.tableName == "child" && it.referencedTable == "parent" && it.onDelete == "CASCADE"
            })
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
