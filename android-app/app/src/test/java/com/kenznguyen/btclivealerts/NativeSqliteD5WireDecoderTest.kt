package com.kenznguyen.btclivealerts

import java.io.ByteArrayOutputStream
import java.io.DataOutputStream
import org.junit.Assert.*
import org.junit.Test

class NativeSqliteD5WireDecoderTest {
    private fun validPayload(tableListName: String = "positions", tableType: String = "table"): ByteArray {
        val body = ByteArrayOutputStream()
        DataOutputStream(body).use { out ->
            out.write(byteArrayOf(0x44, 0x35, 0x57, 0x54)) // D5WT
            out.writeInt(1)
            out.string("3.54.1")
            out.string("2026-10-16 14:45:20 pinned-source-id")

            out.writeInt(1)
            out.string("main"); out.string(tableListName); out.string(tableType)
            out.writeInt(1); out.writeBoolean(false); out.writeBoolean(false)

            out.writeInt(1)
            out.string("main"); out.string("table"); out.string("positions")
            out.string("positions"); out.nullable("CREATE TABLE positions(id INTEGER PRIMARY KEY)")

            out.writeInt(1)
            out.string("main"); out.string("positions"); out.writeInt(0)
            out.string("id"); out.nullable("INTEGER"); out.writeInt(0)
            out.nullable(null); out.writeInt(1); out.writeInt(0)

            out.writeInt(0) // indexes
            out.writeInt(0) // index columns
            out.writeInt(0) // foreign keys
        }
        return ByteArrayOutputStream().also { result ->
            DataOutputStream(result).use { out ->
                out.writeInt(0) // native status VERIFIED
                out.write(body.toByteArray())
            }
        }.toByteArray()
    }

    @Test fun decodesAllD5SectionsAndPreservesNullableFields() {
        val reply = NativeSqliteD5WireDecoder.decode(validPayload())
        assertEquals(NativeSqliteD5ReadStatus.VERIFIED, reply.status)
        val envelope = requireNotNull(reply.envelope)
        assertEquals("3.54.1", envelope.runtime.sqliteVersion)
        assertEquals("positions", envelope.catalog.single().name)
        assertEquals(null, envelope.tableColumns.single().defaultValue)
        assertTrue(envelope.indexes.isEmpty())
        assertTrue(envelope.indexColumns.isEmpty())
        assertTrue(envelope.foreignKeys.isEmpty())
    }

    @Test fun rejectsUnexpectedNativeStatusWithoutPayload() {
        val bytes = byteArrayOf(0, 0, 0, 3)
        val reply = NativeSqliteD5WireDecoder.decode(bytes)
        assertEquals(NativeSqliteD5ReadStatus.UNSUPPORTED_SCHEMA, reply.status)
        assertNull(reply.envelope)
    }

    @Test fun rejectsUnknownNativeStatus() {
        val reply = NativeSqliteD5WireDecoder.decode(byteArrayOf(0, 0, 0, 99))
        assertEquals(NativeSqliteD5ReadStatus.INCOMPLETE_EVIDENCE, reply.status)
        assertNull(reply.envelope)
    }

    @Test fun rejectsTruncatedAndTrailingTransportBytes() {
        val valid = validPayload()
        assertEquals(
            NativeSqliteD5ReadStatus.INCOMPLETE_EVIDENCE,
            NativeSqliteD5WireDecoder.decode(valid.copyOf(valid.size - 1)).status,
        )
        assertEquals(
            NativeSqliteD5ReadStatus.INCOMPLETE_EVIDENCE,
            NativeSqliteD5WireDecoder.decode(valid + byteArrayOf(0)).status,
        )
    }

    @Test fun rejectsWrongMagicAndUnsupportedWireVersion() {
        val valid = validPayload()
        val wrongMagic = valid.copyOf().also { it[4] = 0 }
        assertEquals(NativeSqliteD5ReadStatus.INCOMPLETE_EVIDENCE, NativeSqliteD5WireDecoder.decode(wrongMagic).status)

        val wrongVersion = valid.copyOf().also { it[8] = 0; it[9] = 0; it[10] = 0; it[11] = 2 }
        assertEquals(NativeSqliteD5ReadStatus.INCOMPLETE_EVIDENCE, NativeSqliteD5WireDecoder.decode(wrongVersion).status)
    }

    @Test fun rejectsVirtualOrShadowObjectsBeforeReturningAnEnvelope() {
        val reply = NativeSqliteD5WireDecoder.decode(validPayload(tableType = "virtual"))
        assertEquals(NativeSqliteD5ReadStatus.UNSUPPORTED_SCHEMA, reply.status)
        assertNull(reply.envelope)
    }

    @Test fun rejectsCatalogAndTableListDisagreement() {
        val reply = NativeSqliteD5WireDecoder.decode(validPayload(tableListName = "accounts"))
        assertEquals(NativeSqliteD5ReadStatus.INCOMPLETE_EVIDENCE, reply.status)
        assertNull(reply.envelope)
    }

    private fun DataOutputStream.string(value: String) {
        val bytes = value.toByteArray(Charsets.UTF_8)
        writeInt(bytes.size); write(bytes)
    }

    private fun DataOutputStream.nullable(value: String?) {
        if (value == null) writeInt(-1) else string(value)
    }
}
