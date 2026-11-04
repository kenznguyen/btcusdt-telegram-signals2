package com.kenznguyen.btclivealerts

import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class NativeSqliteD5MemoryFixtureParityTest {
    @Test
    fun nativeInMemoryWireFixtureDecodesAndPassesCanonicalSerializer() {
        val fixturePath = System.getProperty("d5.native.fixture.path").orEmpty()
        val required = System.getProperty("d5.native.fixture.required").toBoolean()
        if (fixturePath.isBlank()) {
            check(!required) { "CI requires the native :memory: D5 fixture path" }
            return
        }

        val wire = File(fixturePath)
        check(wire.isFile && wire.length() > 4L) { "Native D5 fixture is missing or empty: $fixturePath" }
        val reply = NativeSqliteD5WireDecoder.decode(wire.readBytes())
        assertEquals(NativeSqliteD5ReadStatus.VERIFIED, reply.status)
        val envelope = assertNotNullAndReturn(reply.envelope)

        assertEquals("3.54.1", envelope.runtime.sqliteVersion)
        assertTrue(envelope.runtime.sqliteSourceId.isNotBlank())
        assertTrue(envelope.catalog.any { it.type == "table" && it.name == "parent" })
        assertTrue(envelope.catalog.any { it.type == "table" && it.name == "child" })
        assertTrue(envelope.catalog.any { it.type == "view" && it.name == "child_view" })
        assertTrue(envelope.tableColumns.any { it.tableName == "child" && it.name == "generated" && it.hidden == 3 })
        assertTrue(envelope.indexes.any { it.name == "idx_child_value" && it.partial })
        assertTrue(envelope.indexColumns.any { it.indexName == "idx_child_value" && it.descending && it.isKey })
        assertTrue(envelope.foreignKeys.any {
            it.tableName == "child" && it.referencedTable == "parent" && it.onDelete == "CASCADE"
        })

        val canonicalBytes = CanonicalD5Serializer.serialize(envelope)
        assertTrue(canonicalBytes.isNotEmpty())
        assertEquals(64, CanonicalD5Serializer.sha256Hex(envelope).length)
    }

    private fun <T : Any> assertNotNullAndReturn(value: T?): T {
        assertNotNull(value)
        return requireNotNull(value)
    }
}
