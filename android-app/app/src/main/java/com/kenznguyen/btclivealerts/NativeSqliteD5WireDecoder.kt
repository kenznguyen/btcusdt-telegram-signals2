package com.kenznguyen.btclivealerts

import java.io.ByteArrayInputStream
import java.io.DataInputStream
import java.nio.ByteBuffer
import java.nio.charset.CodingErrorAction
import java.nio.charset.StandardCharsets

enum class NativeSqliteD5ReadStatus(val nativeCode: Int) {
    VERIFIED(0),
    INVALID_HANDLE(1),
    QUERY_FAILED(2),
    UNSUPPORTED_SCHEMA(3),
    RESULT_SHAPE_MISMATCH(4),
    INCOMPLETE_EVIDENCE(5),
    PAYLOAD_TOO_LARGE(6);

    companion object {
        fun fromNativeCode(code: Int): NativeSqliteD5ReadStatus =
            entries.firstOrNull { it.nativeCode == code } ?: INCOMPLETE_EVIDENCE
    }
}

data class NativeSqliteD5SnapshotReply(
    val status: NativeSqliteD5ReadStatus,
    val envelope: D5SchemaEnvelope? = null,
)

private data class D5WireTableListEntry(
    val schema: String,
    val name: String,
    val type: String,
    val columnCount: Int,
    val withoutRowId: Boolean,
    val strict: Boolean,
)

/**
 * Strict decoder for the private JNI transport. This wire format is not the
 * canonical D5 digest format; the decoded rows are passed to CanonicalD5Serializer.
 */
internal object NativeSqliteD5WireDecoder {
    private const val WIRE_VERSION = 1
    private const val MAX_PAYLOAD_BYTES = 32 * 1024 * 1024
    private const val MAX_ROWS_PER_SECTION = 100_000
    private const val MAX_STRING_BYTES = 4 * 1024 * 1024
    private val MAGIC = byteArrayOf(0x44, 0x35, 0x57, 0x54) // D5WT

    fun decode(nativeBytes: ByteArray): NativeSqliteD5SnapshotReply {
        if (nativeBytes.size < 4 || nativeBytes.size > MAX_PAYLOAD_BYTES) {
            return NativeSqliteD5SnapshotReply(NativeSqliteD5ReadStatus.INCOMPLETE_EVIDENCE)
        }
        return try {
            val input = DataInputStream(ByteArrayInputStream(nativeBytes))
            val status = NativeSqliteD5ReadStatus.fromNativeCode(input.readInt())
            if (status != NativeSqliteD5ReadStatus.VERIFIED) {
                if (input.available() != 0) return incomplete()
                return NativeSqliteD5SnapshotReply(status)
            }
            val envelope = decodeEnvelope(input)
            if (input.available() != 0) return incomplete()
            NativeSqliteD5SnapshotReply(NativeSqliteD5ReadStatus.VERIFIED, envelope)
        } catch (rejected: D5WireRejected) {
            NativeSqliteD5SnapshotReply(rejected.status)
        } catch (_: Exception) {
            incomplete()
        }
    }

    private class D5WireRejected(val status: NativeSqliteD5ReadStatus) : Exception()

    private fun decodeEnvelope(input: DataInputStream): D5SchemaEnvelope {
        val magic = ByteArray(4).also(input::readFully)
        require(magic.contentEquals(MAGIC)) { "Invalid D5 wire magic" }
        require(input.readInt() == WIRE_VERSION) { "Unsupported D5 wire version" }

        val sqliteVersion = input.readString()
        val sqliteSourceId = input.readString()
        val tableList = List(input.readCount()) {
            D5WireTableListEntry(
                schema = input.readString(),
                name = input.readString(),
                type = input.readString(),
                columnCount = input.readInt().also { require(it >= 0) },
                withoutRowId = input.readBooleanStrict(),
                strict = input.readBooleanStrict(),
            )
        }

        val catalog = List(input.readCount()) {
            D5CatalogRecord(
                schema = input.readString(),
                type = input.readString(),
                name = input.readString(),
                tableName = input.readString(),
                sqlUtf8Exact = input.readNullableString(),
            )
        }
        val tableColumns = List(input.readCount()) {
            D5TableColumnRecord(
                schema = input.readString(),
                tableName = input.readString(),
                cid = input.readInt(),
                name = input.readString(),
                type = input.readNullableString(),
                notNull = input.readInt(),
                defaultValue = input.readNullableString(),
                primaryKeyPosition = input.readInt(),
                hidden = input.readInt(),
            )
        }
        val indexes = List(input.readCount()) {
            D5IndexRecord(
                schema = input.readString(),
                tableName = input.readString(),
                sequence = input.readInt(),
                name = input.readString(),
                unique = input.readBooleanStrict(),
                origin = input.readString(),
                partial = input.readBooleanStrict(),
            )
        }
        val indexColumns = List(input.readCount()) {
            D5IndexColumnRecord(
                schema = input.readString(),
                tableName = input.readString(),
                indexName = input.readString(),
                sequence = input.readInt(),
                columnId = input.readInt(),
                name = input.readNullableString(),
                descending = input.readBooleanStrict(),
                collation = input.readNullableString(),
                isKey = input.readBooleanStrict(),
            )
        }
        val foreignKeys = List(input.readCount()) {
            D5ForeignKeyRecord(
                schema = input.readString(),
                tableName = input.readString(),
                id = input.readInt(),
                sequence = input.readInt(),
                referencedTable = input.readString(),
                fromColumn = input.readNullableString(),
                toColumn = input.readNullableString(),
                onUpdate = input.readString(),
                onDelete = input.readString(),
                match = input.readString(),
            )
        }

        val runtime = CanonicalD5SchemaContract.validateRuntime(
            sqliteVersion = sqliteVersion,
            sqliteSourceId = sqliteSourceId,
            tableListResultColumns = CanonicalD5SchemaContract.TABLE_LIST_COLUMNS,
        )
        when (runtime.status) {
            D5RuntimeStatus.ACCEPTED -> Unit
            D5RuntimeStatus.RESULT_SHAPE_MISMATCH ->
                throw D5WireRejected(NativeSqliteD5ReadStatus.RESULT_SHAPE_MISMATCH)
            D5RuntimeStatus.TABLE_LIST_UNAVAILABLE, D5RuntimeStatus.BELOW_MINIMUM ->
                throw D5WireRejected(NativeSqliteD5ReadStatus.UNSUPPORTED_SCHEMA)
            else -> throw D5WireRejected(NativeSqliteD5ReadStatus.INCOMPLETE_EVIDENCE)
        }

        val catalogIdentities = catalog.map {
            D5CatalogObjectIdentity(it.schema, it.type, it.name, it.tableName)
        }
        val schemaValidation = CanonicalD5SchemaContract.validateTableList(
            tableList.map {
                D5TableListEntry(it.schema, it.name, it.type, it.columnCount, it.withoutRowId, it.strict)
            },
            catalogIdentities,
        )
        when (schemaValidation.status) {
            D5SchemaStatus.ACCEPTED -> Unit
            D5SchemaStatus.UNSUPPORTED_OBJECT_TYPE ->
                throw D5WireRejected(NativeSqliteD5ReadStatus.UNSUPPORTED_SCHEMA)
            else -> throw D5WireRejected(NativeSqliteD5ReadStatus.INCOMPLETE_EVIDENCE)
        }
        require(tableList.all { table ->
            tableColumns.count { it.schema == table.schema && it.tableName == table.name } == table.columnCount
        }) { "table_xinfo row count does not match table_list" }

        val catalogIndexKeys = catalog.filter { it.type == "index" }
            .map { Triple(it.schema, it.tableName, it.name) }.toSet()
        val indexListKeys = indexes.map { Triple(it.schema, it.tableName, it.name) }.toSet()
        require(catalogIndexKeys == indexListKeys) { "index_list and catalog disagree" }
        require(indexColumns.map { Triple(it.schema, it.tableName, it.indexName) }.toSet() == indexListKeys) {
            "index_xinfo coverage is incomplete"
        }
        require(foreignKeys.all { fk ->
            tableList.any { it.schema == fk.schema && it.name == fk.tableName && it.type == "table" }
        }) { "foreign_key_list references an unknown table" }

        // Reuse the reviewed pure contract to reject unknown types, virtual tables
        // and catalog rows without exact SQL metadata. Native queries remain fixed
        // and bind every table/index identifier as a value.
        try {
            CanonicalSqliteReadContract.schemaIntrospectionQueries(
                catalog.map { SqliteSchemaCatalogEntry(it.type, it.name, it.tableName, it.sqlUtf8Exact) },
            )
        } catch (_: IllegalArgumentException) {
            throw D5WireRejected(NativeSqliteD5ReadStatus.UNSUPPORTED_SCHEMA)
        }

        return D5SchemaEnvelope(
            runtime = D5RuntimeIdentity(
                canonicalizationId = CanonicalD5SchemaContract.CANONICALIZATION_ID,
                canonicalizationVersion = CanonicalD5SchemaContract.CANONICALIZATION_VERSION,
                sqliteVersion = sqliteVersion,
                sqliteSourceId = sqliteSourceId,
                featureProbeSchemaVersion = "table_list_v1",
            ),
            catalog = catalog,
            tableColumns = tableColumns,
            indexes = indexes,
            indexColumns = indexColumns,
            foreignKeys = foreignKeys,
        )
    }

    private fun DataInputStream.readCount(): Int =
        readInt().also { require(it in 0..MAX_ROWS_PER_SECTION) { "Invalid D5 section count" } }

    private fun DataInputStream.readString(): String =
        readUtf8(readLength())

    private fun DataInputStream.readNullableString(): String? {
        val length = readInt()
        if (length == -1) return null
        require(length in 0..MAX_STRING_BYTES) { "Invalid nullable string length" }
        return readUtf8(length)
    }

    private fun DataInputStream.readLength(): Int =
        readInt().also { require(it in 0..MAX_STRING_BYTES) { "Invalid string length" } }

    private fun DataInputStream.readUtf8(length: Int): String {
        val bytes = ByteArray(length).also(::readFully)
        return StandardCharsets.UTF_8.newDecoder()
            .onMalformedInput(CodingErrorAction.REPORT)
            .onUnmappableCharacter(CodingErrorAction.REPORT)
            .decode(ByteBuffer.wrap(bytes))
            .toString()
    }

    private fun DataInputStream.readBooleanStrict(): Boolean =
        when (val value = readUnsignedByte()) {
            0 -> false
            1 -> true
            else -> throw IllegalArgumentException("Invalid D5 boolean: $value")
        }

    private fun incomplete() =
        NativeSqliteD5SnapshotReply(NativeSqliteD5ReadStatus.INCOMPLETE_EVIDENCE)
}
