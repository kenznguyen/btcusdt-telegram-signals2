package com.kenznguyen.btclivealerts

/**
 * Source-level D5 feature and schema contract.
 *
 * This contract is deliberately pure: it does not open SQLite, execute PRAGMAs,
 * inspect files, or claim that an adapter used a consistent read transaction.
 */
enum class D5RuntimeStatus {
    ACCEPTED,
    INVALID_VERSION,
    BELOW_MINIMUM,
    MISSING_SOURCE_ID,
    TABLE_LIST_UNAVAILABLE,
    RESULT_SHAPE_MISMATCH,
}

data class D5RuntimeValidation(
    val status: D5RuntimeStatus,
    val sqliteVersion: String?,
    val sqliteSourceId: String?,
)

data class D5TableListEntry(
    val schema: String,
    val name: String,
    val type: String,
    val columnCount: Int,
    val withoutRowId: Boolean,
    val strict: Boolean,
)

data class D5CatalogObjectIdentity(
    val schema: String,
    val type: String,
    val name: String,
    val tableName: String,
)

enum class D5SchemaStatus {
    ACCEPTED,
    UNSUPPORTED_OBJECT_TYPE,
    CATALOG_MISMATCH,
    DUPLICATE_OBJECT,
}

data class D5SchemaValidation(val status: D5SchemaStatus)

enum class D5PragmaKind {
    TABLE_XINFO,
    INDEX_LIST,
    INDEX_XINFO,
    FOREIGN_KEY_LIST,
}

object CanonicalD5SchemaContract {
    const val CANONICALIZATION_ID = "sqlite-d5-envelope"
    const val CANONICALIZATION_VERSION = 1
    const val MINIMUM_SQLITE_VERSION = "3.37.0"
    const val TABLE_LIST_QUERY = "SELECT * FROM pragma_table_list"

    val TABLE_LIST_COLUMNS = listOf("schema", "name", "type", "ncol", "wr", "strict")

    /**
     * Logical field inventory for envelope v1. Values are exact SQLite result
     * values; SQL text is UTF-8 encoded without whitespace or case normalization.
     * rootpage is intentionally absent because it is physical placement metadata.
     */
    val V1_FIELD_INVENTORY: Map<String, List<String>> = linkedMapOf(
        "runtime" to listOf(
            "canonicalization_id",
            "canonicalization_version",
            "sqlite_version",
            "sqlite_source_id",
            "feature_probe_schema_version",
        ),
        "catalog" to listOf("schema", "type", "name", "tbl_name", "sql_utf8_exact"),
        "table_xinfo" to listOf("cid", "name", "type", "notnull", "dflt_value", "pk", "hidden"),
        "index_list" to listOf("seq", "name", "unique", "origin", "partial"),
        "index_xinfo" to listOf("seqno", "cid", "name", "desc", "coll", "key"),
        "foreign_key_list" to listOf(
            "id", "seq", "table", "from", "to", "on_update", "on_delete", "match",
        ),
    )

    private val pragmaColumns: Map<D5PragmaKind, List<String>> = mapOf(
        D5PragmaKind.TABLE_XINFO to
            listOf("cid", "name", "type", "notnull", "dflt_value", "pk", "hidden"),
        D5PragmaKind.INDEX_LIST to
            listOf("seq", "name", "unique", "origin", "partial"),
        D5PragmaKind.INDEX_XINFO to
            listOf("seqno", "cid", "name", "desc", "coll", "key"),
        D5PragmaKind.FOREIGN_KEY_LIST to
            listOf("id", "seq", "table", "from", "to", "on_update", "on_delete", "match"),
    )

    fun validateRuntime(
        sqliteVersion: String,
        sqliteSourceId: String,
        tableListResultColumns: List<String>,
    ): D5RuntimeValidation {
        if (sqliteSourceId.isBlank()) {
            return D5RuntimeValidation(D5RuntimeStatus.MISSING_SOURCE_ID, sqliteVersion, sqliteSourceId)
        }
        val parsed = parseVersion(sqliteVersion)
            ?: return D5RuntimeValidation(D5RuntimeStatus.INVALID_VERSION, sqliteVersion, sqliteSourceId)
        val minimum = parseVersion(MINIMUM_SQLITE_VERSION)!!
        if (compareVersions(parsed, minimum) < 0) {
            return D5RuntimeValidation(D5RuntimeStatus.BELOW_MINIMUM, sqliteVersion, sqliteSourceId)
        }
        if (tableListResultColumns.isEmpty()) {
            return D5RuntimeValidation(D5RuntimeStatus.TABLE_LIST_UNAVAILABLE, sqliteVersion, sqliteSourceId)
        }
        if (tableListResultColumns != TABLE_LIST_COLUMNS) {
            return D5RuntimeValidation(D5RuntimeStatus.RESULT_SHAPE_MISMATCH, sqliteVersion, sqliteSourceId)
        }
        return D5RuntimeValidation(D5RuntimeStatus.ACCEPTED, sqliteVersion, sqliteSourceId)
    }

    /**
     * Reject virtual, shadow and unknown object kinds. Compare table/view identities
     * against sqlite_schema after applying only the versioned sqlite_* exclusion.
     */
    fun validateTableList(
        tableList: List<D5TableListEntry>,
        catalog: List<D5CatalogObjectIdentity>,
    ): D5SchemaValidation {
        val acceptedTypes = setOf("table", "view")
        if (tableList.any { it.type.lowercase() !in acceptedTypes }) {
            return D5SchemaValidation(D5SchemaStatus.UNSUPPORTED_OBJECT_TYPE)
        }

        val visibleTableList = tableList.filterNot { isInternalObject(it.name) }
        val visibleCatalog = catalog
            .filter { it.type.equals("table", true) || it.type.equals("view", true) }
            .filterNot { isInternalObject(it.name) }

        val tableKeys = visibleTableList.map { listOf(it.schema, it.type.lowercase(), it.name, it.name) }
        val catalogKeys = visibleCatalog.map {
            listOf(it.schema, it.type.lowercase(), it.name, it.tableName)
        }
        if (tableKeys.size != tableKeys.toSet().size ||
            catalogKeys.size != catalogKeys.toSet().size
        ) {
            return D5SchemaValidation(D5SchemaStatus.DUPLICATE_OBJECT)
        }
        return if (tableKeys.toSet() == catalogKeys.toSet()) {
            D5SchemaValidation(D5SchemaStatus.ACCEPTED)
        } else {
            D5SchemaValidation(D5SchemaStatus.CATALOG_MISMATCH)
        }
    }

    fun hasExactPragmaShape(kind: D5PragmaKind, resultColumns: List<String>): Boolean =
        pragmaColumns[kind] == resultColumns

    private fun isInternalObject(name: String): Boolean =
        name.startsWith("sqlite_", ignoreCase = true)

    private fun parseVersion(value: String): List<Int>? {
        val match = Regex("^(\\d+)\\.(\\d+)\\.(\\d+)$").matchEntire(value) ?: return null
        return match.groupValues.drop(1).map { it.toIntOrNull() ?: return null }
    }

    private fun compareVersions(left: List<Int>, right: List<Int>): Int {
        for (index in 0..2) {
            val comparison = left[index].compareTo(right[index])
            if (comparison != 0) return comparison
        }
        return 0
    }
}
