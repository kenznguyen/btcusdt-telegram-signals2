package com.kenznguyen.btclivealerts

/**
 * Pure source-level description of the approved SQLite schema and read query families.
 *
 * This object does not open a database, execute SQL, inspect files, or start a transaction.
 * A future adapter must enforce the one-read-transaction boundary around every query here.
 */
enum class SqliteReadQueryId {
    RUNTIME_IDENTITY,
    CANONICAL_IDENTITY,
    MIGRATION_CHAIN,
    SCHEMA_CATALOG,
    SCHEMA_INTROSPECTION,
}

data class FixedSqliteReadQuery(
    val id: SqliteReadQueryId,
    val sql: String,
)

data class SqliteSchemaCatalogEntry(
    val type: String,
    val name: String,
    val tableName: String,
    val sql: String?,
)

object CanonicalSqliteReadContract {
    val bootstrapDdl: List<String> = listOf(
        """
        CREATE TABLE canonical_database_identity (
          singleton_key INTEGER PRIMARY KEY CHECK (singleton_key = 1),
          role_id TEXT NOT NULL,
          instance_id TEXT NOT NULL UNIQUE,
          identity_format_version INTEGER NOT NULL CHECK (identity_format_version = 1),
          provenance TEXT NOT NULL CHECK (provenance IN ('INITIAL_PROVISIONING', 'LEGACY_ADOPTION', 'CLONE_FORK')),
          parent_instance_id TEXT,
          created_at_utc TEXT NOT NULL,
          CHECK (
            (provenance = 'CLONE_FORK' AND parent_instance_id IS NOT NULL AND parent_instance_id <> instance_id)
            OR (provenance <> 'CLONE_FORK' AND parent_instance_id IS NULL)
          )
        );
        """.trimIndent(),
        """
        CREATE TABLE schema_migrations (
          migration_id TEXT PRIMARY KEY,
          sequence INTEGER NOT NULL UNIQUE CHECK (sequence > 0),
          owner_domain TEXT NOT NULL,
          checksum_sha256 TEXT NOT NULL CHECK (
            length(checksum_sha256) = 64 AND checksum_sha256 NOT GLOB '*[^0-9a-f]*'
          ),
          applied_at_utc TEXT NOT NULL
        );
        """.trimIndent(),
        immutableTrigger(
            name = "canonical_database_identity_no_update",
            table = "canonical_database_identity",
            operation = "UPDATE",
        ),
        immutableTrigger(
            name = "canonical_database_identity_no_delete",
            table = "canonical_database_identity",
            operation = "DELETE",
        ),
        immutableTrigger(
            name = "schema_migrations_no_update",
            table = "schema_migrations",
            operation = "UPDATE",
        ),
        immutableTrigger(
            name = "schema_migrations_no_delete",
            table = "schema_migrations",
            operation = "DELETE",
        ),
    )

    val fixedReadQueries: List<FixedSqliteReadQuery> = listOf(
        FixedSqliteReadQuery(
            SqliteReadQueryId.RUNTIME_IDENTITY,
            "SELECT sqlite_version(), sqlite_source_id()",
        ),
        FixedSqliteReadQuery(
            SqliteReadQueryId.CANONICAL_IDENTITY,
            """
            SELECT singleton_key, role_id, instance_id, identity_format_version,
                   provenance, parent_instance_id, created_at_utc
            FROM canonical_database_identity
            ORDER BY singleton_key
            """.trimIndent(),
        ),
        FixedSqliteReadQuery(
            SqliteReadQueryId.MIGRATION_CHAIN,
            """
            SELECT migration_id, sequence, owner_domain, checksum_sha256, applied_at_utc
            FROM schema_migrations
            ORDER BY sequence
            """.trimIndent(),
        ),
        FixedSqliteReadQuery(
            SqliteReadQueryId.SCHEMA_CATALOG,
            """
            SELECT type, name, tbl_name, sql
            FROM sqlite_schema
            WHERE substr(name, 1, 7) <> 'sqlite_'
            ORDER BY type, name, tbl_name, sql
            """.trimIndent(),
        ),
    )

    /**
     * Produces only the approved PRAGMA templates for table and index names observed
     * in the supplied schema catalog. The caller must pass the catalog read in the
     * same SQLite read transaction as the other evidence queries.
     */
    fun schemaIntrospectionQueries(
        catalog: List<SqliteSchemaCatalogEntry>,
    ): List<FixedSqliteReadQuery> {
        val supportedTypes = setOf("table", "index", "view", "trigger")
        catalog.forEach { entry ->
            require(entry.type.lowercase() in supportedTypes) {
                "Unsupported SQLite schema object type: ${entry.type}"
            }
        }

        val visibleObjects = catalog.filterNot { isInternalSqliteObject(it.name) }
        visibleObjects.forEach { entry ->
            require(!entry.sql.isNullOrBlank()) {
                "Missing SQLite schema SQL for ${entry.type} ${entry.name}"
            }
        }
        val tablesAndViews = visibleObjects.asSequence()
            .filter { it.type.equals("table", ignoreCase = true) || it.type.equals("view", ignoreCase = true) }
            .onEach { entry ->
                require(!entry.sql.isNullOrBlank()) {
                    "Missing SQLite schema SQL for ${entry.type} ${entry.name}"
                }
                if (entry.type.equals("table", ignoreCase = true)) {
                    require(!isVirtualTableDeclaration(entry.sql.orEmpty())) {
                        "Virtual table module provenance is not verified for ${entry.name}"
                    }
                }
            }
            .sortedBy { it.name }
            .toList()

        val indexes = visibleObjects.asSequence()
            .filter { it.type.equals("index", ignoreCase = true) }
            .onEach { entry ->
                require(!entry.sql.isNullOrBlank()) {
                    "Missing SQLite schema SQL for index ${entry.name}"
                }
            }
            .sortedBy { it.name }
            .toList()

        return buildList {
            tablesAndViews.forEach { entry ->
                val identifier = quoteIdentifier(entry.name)
                add(FixedSqliteReadQuery(
                    SqliteReadQueryId.SCHEMA_INTROSPECTION,
                    "PRAGMA table_xinfo($identifier)",
                ))
                if (entry.type.equals("table", ignoreCase = true)) {
                    add(FixedSqliteReadQuery(
                        SqliteReadQueryId.SCHEMA_INTROSPECTION,
                        "PRAGMA index_list($identifier)",
                    ))
                    add(FixedSqliteReadQuery(
                        SqliteReadQueryId.SCHEMA_INTROSPECTION,
                        "PRAGMA foreign_key_list($identifier)",
                    ))
                }
            }
            indexes.forEach { entry ->
                add(FixedSqliteReadQuery(
                    SqliteReadQueryId.SCHEMA_INTROSPECTION,
                    "PRAGMA index_xinfo(${quoteIdentifier(entry.name)})",
                ))
            }
        }
    }

    private fun isVirtualTableDeclaration(sql: String): Boolean {
        val withoutLeadingComments = sql.replace(
            Regex("""(?s)^\s*(?:(?:--[^\r\n]*(?:\r?\n|$))|(?:/\*.*?\*/\s*))*"""),
            "",
        )
        return Regex("""(?is)^CREATE\s+VIRTUAL\s+TABLE\b""")
            .containsMatchIn(withoutLeadingComments.trimStart())
    }

    /**
     * SQLite identifier quoting: embedded double quotes are doubled.
     * This is not a SQL-fragment sanitizer; it is only for identifiers obtained
     * from the just-read sqlite_schema catalog.
     */
    fun quoteIdentifier(identifier: String): String =
        "\"${identifier.replace("\"", "\"\"")}\""

    private fun isInternalSqliteObject(name: String): Boolean =
        name.startsWith("sqlite_", ignoreCase = true)

    private fun immutableTrigger(
        name: String,
        table: String,
        operation: String,
    ): String = """
        CREATE TRIGGER $name
        BEFORE $operation ON $table
        BEGIN
          SELECT RAISE(ABORT, '$table is immutable');
        END;
    """.trimIndent()
}
