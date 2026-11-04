package com.kenznguyen.btclivealerts

import java.io.ByteArrayOutputStream
import java.io.DataOutputStream
import java.nio.CharBuffer
import java.nio.charset.CodingErrorAction
import java.nio.charset.StandardCharsets
import java.security.MessageDigest

/** Runtime identity fields captured by the D5 read-only introspection adapter. */
data class D5RuntimeIdentity(
    val canonicalizationId: String,
    val canonicalizationVersion: Int,
    val sqliteVersion: String,
    val sqliteSourceId: String,
    val featureProbeSchemaVersion: String,
)

data class D5CatalogRecord(
    val schema: String,
    val type: String,
    val name: String,
    val tableName: String,
    /** Exact catalog SQL; null remains distinct from an empty SQL string. */
    val sqlUtf8Exact: String?,
)

data class D5TableColumnRecord(
    val schema: String,
    val tableName: String,
    val cid: Int,
    val name: String,
    val type: String?,
    val notNull: Int,
    val defaultValue: String?,
    val primaryKeyPosition: Int,
    val hidden: Int,
)

data class D5IndexRecord(
    val schema: String,
    val tableName: String,
    val sequence: Int,
    val name: String,
    val unique: Boolean,
    val origin: String,
    val partial: Boolean,
)

data class D5IndexColumnRecord(
    val schema: String,
    val tableName: String,
    val indexName: String,
    val sequence: Int,
    val columnId: Int,
    val name: String?,
    val descending: Boolean,
    val collation: String?,
    val isKey: Boolean,
)

data class D5ForeignKeyRecord(
    val schema: String,
    val tableName: String,
    val id: Int,
    val sequence: Int,
    val referencedTable: String,
    val fromColumn: String?,
    val toColumn: String?,
    val onUpdate: String,
    val onDelete: String,
    val match: String,
)

/**
 * Pure logical schema snapshot. The adapter must populate this from the exact
 * D5 envelope v1 inventory after its separately verified consistent read.
 */
data class D5SchemaEnvelope(
    val runtime: D5RuntimeIdentity,
    val catalog: List<D5CatalogRecord>,
    val tableColumns: List<D5TableColumnRecord>,
    val indexes: List<D5IndexRecord>,
    val indexColumns: List<D5IndexColumnRecord>,
    val foreignKeys: List<D5ForeignKeyRecord>,
)

/**
 * D5 canonical binary encoding v1.
 *
 * All integers are signed 32-bit big-endian. Strings are exact UTF-8 prefixed
 * by a 32-bit byte length; nullable strings use -1 for null, so null and empty
 * are different. Booleans are one byte (0 or 1). Sections are tagged and
 * count-prefixed. No locale formatting, Unicode normalization, SQL rewriting,
 * JSON serializer, SQLite access, or platform APIs participate.
 */
object CanonicalD5Serializer {
    private val magic = byteArrayOf(0x44, 0x35, 0x53, 0x43) // "D5SC"
    private const val FORMAT_VERSION = 1

    fun serialize(envelope: D5SchemaEnvelope): ByteArray {
        validateRuntime(envelope.runtime)
        validateUniqueIdentities(envelope)

        val buffer = ByteArrayOutputStream()
        DataOutputStream(buffer).use { out ->
            out.write(magic)
            out.writeInt(FORMAT_VERSION)
            out.writeString(envelope.runtime.canonicalizationId)
            out.writeInt(envelope.runtime.canonicalizationVersion)
            out.writeString(envelope.runtime.sqliteVersion)
            out.writeString(envelope.runtime.sqliteSourceId)
            out.writeString(envelope.runtime.featureProbeSchemaVersion)

            val catalog = envelope.catalog.sortedWith { a, b ->
                compareTuple(
                    listOf(a.schema, a.type, a.name, a.tableName),
                    listOf(b.schema, b.type, b.name, b.tableName),
                )
            }
            out.writeSection("catalog", catalog) { row ->
                writeString(row.schema)
                writeString(row.type)
                writeString(row.name)
                writeString(row.tableName)
                writeNullableString(row.sqlUtf8Exact)
            }

            val columns = envelope.tableColumns.sortedWith { a, b ->
                compareTuple(
                    listOf(a.schema, a.tableName),
                    listOf(b.schema, b.tableName),
                ).takeIf { it != 0 } ?: a.cid.compareTo(b.cid)
            }
            out.writeSection("table_xinfo", columns) { row ->
                writeString(row.schema)
                writeString(row.tableName)
                writeInt(row.cid)
                writeString(row.name)
                writeNullableString(row.type)
                writeInt(row.notNull)
                writeNullableString(row.defaultValue)
                writeInt(row.primaryKeyPosition)
                writeInt(row.hidden)
            }

            val indexes = envelope.indexes.sortedWith { a, b ->
                compareTuple(
                    listOf(a.schema, a.tableName),
                    listOf(b.schema, b.tableName),
                ).takeIf { it != 0 }
                    ?: a.sequence.compareTo(b.sequence).takeIf { it != 0 }
                    ?: compareUtf8(a.name, b.name)
            }
            out.writeSection("index_list", indexes) { row ->
                writeString(row.schema)
                writeString(row.tableName)
                writeInt(row.sequence)
                writeString(row.name)
                writeBoolean(row.unique)
                writeString(row.origin)
                writeBoolean(row.partial)
            }

            val indexColumns = envelope.indexColumns.sortedWith { a, b ->
                compareTuple(
                    listOf(a.schema, a.tableName, a.indexName),
                    listOf(b.schema, b.tableName, b.indexName),
                ).takeIf { it != 0 } ?: a.sequence.compareTo(b.sequence)
            }
            out.writeSection("index_xinfo", indexColumns) { row ->
                writeString(row.schema)
                writeString(row.tableName)
                writeString(row.indexName)
                writeInt(row.sequence)
                writeInt(row.columnId)
                writeNullableString(row.name)
                writeBoolean(row.descending)
                writeNullableString(row.collation)
                writeBoolean(row.isKey)
            }

            val foreignKeys = envelope.foreignKeys.sortedWith { a, b ->
                compareTuple(
                    listOf(a.schema, a.tableName),
                    listOf(b.schema, b.tableName),
                ).takeIf { it != 0 }
                    ?: a.id.compareTo(b.id).takeIf { it != 0 }
                    ?: a.sequence.compareTo(b.sequence)
            }
            out.writeSection("foreign_key_list", foreignKeys) { row ->
                writeString(row.schema)
                writeString(row.tableName)
                writeInt(row.id)
                writeInt(row.sequence)
                writeString(row.referencedTable)
                writeNullableString(row.fromColumn)
                writeNullableString(row.toColumn)
                writeString(row.onUpdate)
                writeString(row.onDelete)
                writeString(row.match)
            }
        }
        return buffer.toByteArray()
    }

    fun sha256(envelope: D5SchemaEnvelope): ByteArray =
        MessageDigest.getInstance("SHA-256").digest(serialize(envelope))

    fun sha256Hex(envelope: D5SchemaEnvelope): String =
        sha256(envelope).joinToString(separator = "") { byte ->
            val value = byte.toInt() and 0xff
            HEX[value ushr 4].toString() + HEX[value and 0x0f]
        }

    private fun validateRuntime(runtime: D5RuntimeIdentity) {
        require(runtime.canonicalizationId == CanonicalD5SchemaContract.CANONICALIZATION_ID) {
            "unsupported canonicalization id"
        }
        require(runtime.canonicalizationVersion == CanonicalD5SchemaContract.CANONICALIZATION_VERSION) {
            "unsupported canonicalization version"
        }
        require(runtime.sqliteVersion.isNotBlank()) { "missing SQLite version" }
        require(runtime.sqliteSourceId.isNotBlank()) { "missing SQLite source id" }
        require(runtime.featureProbeSchemaVersion.isNotBlank()) { "missing feature probe schema version" }
    }

    private fun validateUniqueIdentities(envelope: D5SchemaEnvelope) {
        require(envelope.catalog.all { it.schema.isNotBlank() && it.type.isNotBlank() && it.name.isNotBlank() }) {
            "blank catalog identity"
        }
        require(envelope.catalog.map { Triple(it.schema, it.type, it.name) }.toSet().size == envelope.catalog.size) {
            "duplicate catalog identity"
        }

        require(envelope.tableColumns.all { it.schema.isNotBlank() && it.tableName.isNotBlank() && it.name.isNotBlank() }) {
            "blank table column identity"
        }
        require(envelope.tableColumns.map { Triple(it.schema, it.tableName, it.cid) }.toSet().size == envelope.tableColumns.size) {
            "duplicate table column identity"
        }

        require(envelope.indexes.all { it.schema.isNotBlank() && it.tableName.isNotBlank() && it.name.isNotBlank() }) {
            "blank index identity"
        }
        require(envelope.indexes.map { Triple(it.schema, it.tableName, it.sequence) }.toSet().size == envelope.indexes.size) {
            "duplicate index sequence"
        }
        require(envelope.indexes.map { it.schema to it.name }.toSet().size == envelope.indexes.size) {
            "duplicate index name"
        }

        require(envelope.indexColumns.all {
            it.schema.isNotBlank() && it.tableName.isNotBlank() && it.indexName.isNotBlank()
        }) { "blank index column identity" }
        require(envelope.indexColumns.map {
            listOf(it.schema, it.tableName, it.indexName, it.sequence)
        }.toSet().size == envelope.indexColumns.size) { "duplicate index column sequence" }

        require(envelope.foreignKeys.all {
            it.schema.isNotBlank() && it.tableName.isNotBlank() && it.referencedTable.isNotBlank()
        }) { "blank foreign key identity" }
        require(envelope.foreignKeys.map {
            listOf(it.schema, it.tableName, it.id, it.sequence)
        }.toSet().size == envelope.foreignKeys.size) { "duplicate foreign key sequence" }
    }

    private fun compareTuple(left: List<String>, right: List<String>): Int {
        for (index in left.indices) {
            val result = compareUtf8(left[index], right[index])
            if (result != 0) return result
        }
        return 0
    }

    /** Unsigned lexicographic comparison of UTF-8 bytes, independent of locale. */
    private fun compareUtf8(left: String, right: String): Int {
        val a = encodeUtf8(left)
        val b = encodeUtf8(right)
        val limit = minOf(a.size, b.size)
        for (index in 0 until limit) {
            val difference = (a[index].toInt() and 0xff) - (b[index].toInt() and 0xff)
            if (difference != 0) return difference
        }
        return a.size.compareTo(b.size)
    }

    private fun <T> DataOutputStream.writeSection(
        name: String,
        rows: List<T>,
        writeRow: DataOutputStream.(T) -> Unit,
    ) {
        writeString(name)
        writeInt(rows.size)
        rows.forEach { writeRow(it) }
    }

    private fun encodeUtf8(value: String): ByteArray {
        val encoded = StandardCharsets.UTF_8.newEncoder()
            .onMalformedInput(CodingErrorAction.REPORT)
            .onUnmappableCharacter(CodingErrorAction.REPORT)
            .encode(CharBuffer.wrap(value))
        return ByteArray(encoded.remaining()).also { encoded.get(it) }
    }

    private fun DataOutputStream.writeString(value: String) {
        val bytes = encodeUtf8(value)
        writeInt(bytes.size)
        write(bytes)
    }

    private fun DataOutputStream.writeNullableString(value: String?) {
        if (value == null) {
            writeInt(-1)
        } else {
            writeString(value)
        }
    }

    private fun DataOutputStream.writeBoolean(value: Boolean) {
        writeByte(if (value) 1 else 0)
    }

    private const val HEX = "0123456789abcdef"
}
