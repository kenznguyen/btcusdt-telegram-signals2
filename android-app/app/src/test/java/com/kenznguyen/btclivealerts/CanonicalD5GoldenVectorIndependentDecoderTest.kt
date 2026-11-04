package com.kenznguyen.btclivealerts

import java.io.ByteArrayInputStream
import java.io.DataInputStream
import java.security.MessageDigest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Test-only decoder intentionally independent from CanonicalD5Serializer.
 *
 * It consumes frozen bytes using DataInputStream and checks the wire contract
 * field-by-field. It must not call production serialization or hashing helpers.
 */
class CanonicalD5GoldenVectorIndependentDecoderTest {
    private data class Runtime(
        val id: String,
        val version: Int,
        val sqliteVersion: String,
        val sourceId: String,
        val probeVersion: String,
    )

    private data class Decoded(
        val runtime: Runtime,
        val catalogCount: Int,
        val tableColumnCount: Int,
        val indexCount: Int,
        val indexColumnCount: Int,
        val foreignKeyCount: Int,
        val catalogName: String? = null,
        val catalogSql: String? = null,
        val tableColumnName: String? = null,
        val tableColumnType: String? = null,
        val tableColumnDefault: String? = null,
        val indexName: String? = null,
        val indexUnique: Boolean? = null,
        val indexColumnName: String? = null,
        val indexColumnCollation: String? = null,
        val foreignKeyTable: String? = null,
        val foreignKeyFrom: String? = null,
        val foreignKeyTo: String? = null,
    )

    private val emptyBytesHex =
            "44355343000000010000001273716c6974652d64352d656e76656c6f7065" +
            "0000000100000006332e34352e310000000a736f757263652d616263" +
            "0000000d7461626c655f6c6973745f763100000007636174616c6f67" +
            "000000000000000b7461626c655f78696e666f000000000000000a" +
            "696e6465785f6c697374000000000000000b696e6465785f78696e666f" +
            "0000000000000010666f726569676e5f6b65795f6c69737400000000"

    private val populatedBytesHex =
            "44355343000000010000001273716c6974652d64352d656e76656c6f70650000" +
            "000100000006332e34352e310000000a736f757263652d6162630000000d7461" +
            "626c655f6c6973745f763100000007636174616c6f6700000001000000046d61" +
            "696e000000057461626c6500000009706f736974696f6e7300000009706f7369" +
            "74696f6e730000002e435245415445205441424c4520706f736974696f6e7328" +
            "696420494e5445474552205052494d415259204b4559290000000b7461626c65" +
            "5f78696e666f00000001000000046d61696e00000009706f736974696f6e7300" +
            "00000000000002696400000007494e544547455200000000ffffffff00000001" +
            "000000000000000a696e6465785f6c69737400000001000000046d61696e0000" +
            "0009706f736974696f6e7300000000000000156964785f706f736974696f6e73" +
            "5f63726561746564010000000163000000000b696e6465785f78696e666f0000" +
            "0001000000046d61696e00000009706f736974696f6e73000000156964785f70" +
            "6f736974696f6e735f6372656174656400000000000000010000000a63726561" +
            "7465645f6174000000000642494e4152590100000010666f726569676e5f6b65" +
            "795f6c69737400000001000000046d61696e00000009706f736974696f6e7300" +
            "00000000000000000000086163636f756e74730000000a6163636f756e745f69" +
            "64000000026964000000094e4f20414354494f4e000000074341534341444500" +
            "0000044e4f4e45"

    @Test
    fun emptyGoldenVectorIsDecodedWithoutProductionSerializer() {
        val bytes = emptyBytesHex.hexToBytes()
        assertEquals(170, bytes.size)
        assertEquals(
            "98f5c30f439b552ab7b04f7ae0f783abae13c2a6141cc5b1348da016a867b600",
            sha256Hex(bytes),
        )

        val decoded = decode(bytes)
        assertEquals(Runtime("sqlite-d5-envelope", 1, "3.45.1", "source-abc", "table_list_v1"), decoded.runtime)
        assertEquals(0, decoded.catalogCount)
        assertEquals(0, decoded.tableColumnCount)
        assertEquals(0, decoded.indexCount)
        assertEquals(0, decoded.indexColumnCount)
        assertEquals(0, decoded.foreignKeyCount)
    }

    @Test
    fun populatedGoldenVectorDecodesEverySectionAndNullSentinel() {
        val bytes = populatedBytesHex.hexToBytes()
        assertEquals(551, bytes.size)
        assertEquals(
            "b57bd29e67c869039d2ff5aa2f365d4f588c9a154054e5b6dc56837c491b0354",
            sha256Hex(bytes),
        )

        val decoded = decode(bytes)
        assertEquals(Runtime("sqlite-d5-envelope", 1, "3.45.1", "source-abc", "table_list_v1"), decoded.runtime)
        assertEquals(1, decoded.catalogCount)
        assertEquals("positions", decoded.catalogName)
        assertEquals("CREATE TABLE positions(id INTEGER PRIMARY KEY)", decoded.catalogSql)
        assertEquals(1, decoded.tableColumnCount)
        assertEquals("id", decoded.tableColumnName)
        assertEquals("INTEGER", decoded.tableColumnType)
        assertEquals(null, decoded.tableColumnDefault)
        assertEquals(1, decoded.indexCount)
        assertEquals("idx_positions_created", decoded.indexName)
        assertEquals(true, decoded.indexUnique)
        assertEquals(1, decoded.indexColumnCount)
        assertEquals("created_at", decoded.indexColumnName)
        assertEquals("BINARY", decoded.indexColumnCollation)
        assertEquals(1, decoded.foreignKeyCount)
        assertEquals("accounts", decoded.foreignKeyTable)
        assertEquals("account_id", decoded.foreignKeyFrom)
        assertEquals("id", decoded.foreignKeyTo)
    }

    private fun decode(bytes: ByteArray): Decoded {
        val input = DataInputStream(ByteArrayInputStream(bytes))
        val magic = ByteArray(4).also(input::readFully)
        assertEquals("44355343", magic.joinToString("") { "%02x".format(it) })
        assertEquals(1, input.readInt())

        val runtime = Runtime(
            readString(input),
            input.readInt(),
            readString(input),
            readString(input),
            readString(input),
        )

        assertEquals("catalog", readString(input))
        val catalogCount = readCount(input)
        var catalogName: String? = null
        var catalogSql: String? = null
        repeat(catalogCount) {
            readString(input) // schema
            readString(input) // type
            catalogName = readString(input)
            readString(input) // table name
            catalogSql = readNullableString(input)
        }

        assertEquals("table_xinfo", readString(input))
        val columnCount = readCount(input)
        var columnName: String? = null
        var columnType: String? = null
        var columnDefault: String? = null
        repeat(columnCount) {
            readString(input) // schema
            readString(input) // table
            input.readInt() // cid
            columnName = readString(input)
            columnType = readNullableString(input)
            input.readInt() // not null
            columnDefault = readNullableString(input)
            input.readInt() // primary key position
            input.readInt() // hidden
        }

        assertEquals("index_list", readString(input))
        val indexCount = readCount(input)
        var indexName: String? = null
        var indexUnique: Boolean? = null
        repeat(indexCount) {
            readString(input) // schema
            readString(input) // table
            input.readInt() // sequence
            indexName = readString(input)
            indexUnique = readBoolean(input)
            readString(input) // origin
            readBoolean(input) // partial
        }

        assertEquals("index_xinfo", readString(input))
        val indexColumnCount = readCount(input)
        var indexColumnName: String? = null
        var indexColumnCollation: String? = null
        repeat(indexColumnCount) {
            readString(input) // schema
            readString(input) // table
            readString(input) // index
            input.readInt() // sequence
            input.readInt() // cid
            indexColumnName = readNullableString(input)
            readBoolean(input) // descending
            indexColumnCollation = readNullableString(input)
            readBoolean(input) // key
        }

        assertEquals("foreign_key_list", readString(input))
        val foreignKeyCount = readCount(input)
        var foreignKeyTable: String? = null
        var foreignKeyFrom: String? = null
        var foreignKeyTo: String? = null
        repeat(foreignKeyCount) {
            readString(input) // schema
            readString(input) // table
            input.readInt() // id
            input.readInt() // sequence
            foreignKeyTable = readString(input)
            foreignKeyFrom = readNullableString(input)
            foreignKeyTo = readNullableString(input)
            readString(input) // on update
            readString(input) // on delete
            readString(input) // match
        }

        assertEquals("decoder consumed the complete canonical vector", 0, input.available())
        return Decoded(
            runtime,
            catalogCount,
            columnCount,
            indexCount,
            indexColumnCount,
            foreignKeyCount,
            catalogName,
            catalogSql,
            columnName,
            columnType,
            columnDefault,
            indexName,
            indexUnique,
            indexColumnName,
            indexColumnCollation,
            foreignKeyTable,
            foreignKeyFrom,
            foreignKeyTo,
        )
    }

    private fun readCount(input: DataInputStream): Int =
        input.readInt().also { assertTrue("negative section count", it >= 0) }

    private fun readString(input: DataInputStream): String {
        val length = input.readInt()
        assertTrue("negative non-null string length", length >= 0)
        val bytes = ByteArray(length).also(input::readFully)
        return Charsets.UTF_8.newDecoder().decode(java.nio.ByteBuffer.wrap(bytes)).toString()
    }

    private fun readNullableString(input: DataInputStream): String? {
        val length = input.readInt()
        if (length == -1) return null
        assertTrue("invalid nullable string length", length >= 0)
        val bytes = ByteArray(length).also(input::readFully)
        return Charsets.UTF_8.newDecoder().decode(java.nio.ByteBuffer.wrap(bytes)).toString()
    }

    private fun readBoolean(input: DataInputStream): Boolean =
        input.readUnsignedByte().also { assertTrue("boolean must be 0 or 1", it == 0 || it == 1) } == 1

    private fun sha256Hex(bytes: ByteArray): String =
        MessageDigest.getInstance("SHA-256").digest(bytes)
            .joinToString("") { "%02x".format(it) }

    private fun String.hexToBytes(): ByteArray {
        assertTrue("hex string must have even length", length % 2 == 0)
        return chunked(2).map { it.toInt(16).toByte() }.toByteArray()
    }
}
