package com.kenznguyen.btclivealerts

import java.security.MessageDigest
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class CanonicalD5SerializerTest {
    private fun envelope(
        catalogName: String = "positions",
        sql: String? = "CREATE TABLE positions(id INTEGER PRIMARY KEY)",
        catalog: List<D5CatalogRecord> = listOf(
            D5CatalogRecord("main", "table", catalogName, catalogName, sql),
        ),
    ) = D5SchemaEnvelope(
        runtime = D5RuntimeIdentity("sqlite-d5-envelope", 1, "3.45.1", "source-abc", "table_list_v1"),
        catalog = catalog,
        tableColumns = listOf(
            D5TableColumnRecord("main", "positions", 0, "id", "INTEGER", 0, null, 1, 0),
        ),
        indexes = listOf(
            D5IndexRecord("main", "positions", 0, "idx_positions_created", true, "c", false),
        ),
        indexColumns = listOf(
            D5IndexColumnRecord("main", "positions", "idx_positions_created", 0, 1, "created_at", false, "BINARY", true),
        ),
        foreignKeys = listOf(
            D5ForeignKeyRecord("main", "positions", 0, 0, "accounts", "account_id", "id", "NO ACTION", "CASCADE", "NONE"),
        ),
    )

    private fun emptyEnvelope() = D5SchemaEnvelope(
        runtime = D5RuntimeIdentity("sqlite-d5-envelope", 1, "3.45.1", "source-abc", "table_list_v1"),
        catalog = emptyList(),
        tableColumns = emptyList(),
        indexes = emptyList(),
        indexColumns = emptyList(),
        foreignKeys = emptyList(),
    )

    @Test
    fun emptyEnvelopeMatchesFrozenCanonicalV1GoldenVector() {
        val expectedBytesHex = (
            "44355343000000010000001273716c6974652d64352d656e76656c6f7065" +
            "0000000100000006332e34352e310000000a736f757263652d616263" +
            "0000000d7461626c655f6c6973745f763100000007636174616c6f67" +
            "000000000000000b7461626c655f78696e666f000000000000000a" +
            "696e6465785f6c697374000000000000000b696e6465785f78696e666f" +
            "0000000000000010666f726569676e5f6b65795f6c69737400000000"
        )
        val envelope = emptyEnvelope()
        val bytes = CanonicalD5Serializer.serialize(envelope)
        val actualBytesHex = bytes.joinToString("") { "%02x".format(it) }

        assertEquals(170, bytes.size)
        assertEquals(expectedBytesHex, actualBytesHex)
        assertEquals(
            "98f5c30f439b552ab7b04f7ae0f783abae13c2a6141cc5b1348da016a867b600",
            CanonicalD5Serializer.sha256Hex(envelope),
        )
    }

    @Test
    fun populatedEnvelopeMatchesFrozenCanonicalV1GoldenVector() {
        val expectedBytesHex = (
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
        )
        val bytes = CanonicalD5Serializer.serialize(envelope())
        val actualBytesHex = bytes.joinToString("") { "%02x".format(it) }

        assertEquals(551, bytes.size)
        assertEquals(expectedBytesHex, actualBytesHex)
        assertEquals(
            "b57bd29e67c869039d2ff5aa2f365d4f588c9a154054e5b6dc56837c491b0354",
            CanonicalD5Serializer.sha256Hex(envelope()),
        )
    }

    @Test
    fun canonicalBytesAreIndependentOfInputCollectionOrder() {
        val first = envelope(
            catalog = listOf(
                D5CatalogRecord("main", "table", "positions", "positions", "CREATE TABLE positions(id)"),
                D5CatalogRecord("main", "view", "v_positions", "v_positions", "CREATE VIEW v_positions AS SELECT id FROM positions"),
            ),
        ).let { base ->
            base.copy(
                tableColumns = base.tableColumns + D5TableColumnRecord(
                    "main", "positions", 1, "created_at", "TEXT", 0, null, 0, 0,
                ),
                indexes = base.indexes + D5IndexRecord(
                    "main", "positions", 1, "idx_positions_id", false, "c", false,
                ),
                indexColumns = base.indexColumns + D5IndexColumnRecord(
                    "main", "positions", "idx_positions_created", 1, -1, null, true, "BINARY", false,
                ),
                foreignKeys = base.foreignKeys + D5ForeignKeyRecord(
                    "main", "positions", 1, 0, "users", "user_id", "id", "RESTRICT", "SET NULL", "NONE",
                ),
            )
        }
        val reordered = first.copy(
            catalog = first.catalog.reversed(),
            tableColumns = first.tableColumns.reversed(),
            indexes = first.indexes.reversed(),
            indexColumns = first.indexColumns.reversed(),
            foreignKeys = first.foreignKeys.reversed(),
        )
        assertArrayEquals(
            CanonicalD5Serializer.serialize(first),
            CanonicalD5Serializer.serialize(reordered),
        )
    }

    @Test
    fun sha256IsLowercaseHexOfCanonicalBytes() {
        val bytes = CanonicalD5Serializer.serialize(envelope())
        val expected = MessageDigest.getInstance("SHA-256").digest(bytes)
            .joinToString("") { "%02x".format(it) }
        assertEquals(expected, CanonicalD5Serializer.sha256Hex(envelope()))
        assertTrue(CanonicalD5Serializer.sha256Hex(envelope()).matches(Regex("^[0-9a-f]{64}$")))
    }

    @Test
    fun logicalSchemaChangesChangeDigest() {
        assertNotEquals(
            CanonicalD5Serializer.sha256Hex(envelope()),
            CanonicalD5Serializer.sha256Hex(envelope(catalogName = "orders")),
        )
    }

    @Test
    fun exactCatalogSqlIsNotTrimmedOrNormalized() {
        assertNotEquals(
            CanonicalD5Serializer.sha256Hex(envelope(sql = "CREATE TABLE positions(id INTEGER PRIMARY KEY)")),
            CanonicalD5Serializer.sha256Hex(envelope(sql = "CREATE TABLE positions (id INTEGER PRIMARY KEY)")),
        )
    }

    @Test
    fun nullAndEmptyTextHaveDifferentCanonicalEncodings() {
        assertNotEquals(
            CanonicalD5Serializer.sha256Hex(envelope(sql = null)),
            CanonicalD5Serializer.sha256Hex(envelope(sql = "")),
        )
    }

    @Test
    fun duplicateCatalogIdentityIsRejected() {
        val row = D5CatalogRecord("main", "table", "positions", "positions", "CREATE TABLE positions(id)")
        val invalid = envelope(catalog = listOf(row, row))
        assertEquals(
            "duplicate catalog identity",
            runCatching { CanonicalD5Serializer.serialize(invalid) }.exceptionOrNull()?.message,
        )
    }

    @Test
    fun duplicateTableColumnOrdinalIsRejected() {
        val valid = envelope()
        val invalid = valid.copy(tableColumns = valid.tableColumns + valid.tableColumns)
        assertEquals(
            "duplicate table column identity",
            runCatching { CanonicalD5Serializer.serialize(invalid) }.exceptionOrNull()?.message,
        )
    }

    @Test
    fun malformedUtf16IsRejectedInsteadOfSilentlyReplaced() {
        assertTrue(runCatching {
            CanonicalD5Serializer.serialize(envelope(catalogName = "invalid-\uD800-name"))
        }.isFailure)
    }

    @Test
    fun invalidRuntimeIdentityIsRejected() {
        assertTrue(runCatching {
            CanonicalD5Serializer.serialize(envelope().copy(
                runtime = D5RuntimeIdentity("", 1, "3.45.1", "source-abc", "table_list_v1"),
            ))
        }.isFailure)
        assertTrue(runCatching {
            CanonicalD5Serializer.serialize(envelope().copy(
                runtime = D5RuntimeIdentity("sqlite-d5-envelope", 2, "3.45.1", "source-abc", "table_list_v1"),
            ))
        }.isFailure)
    }
}
