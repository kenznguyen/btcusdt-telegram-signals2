package com.kenznguyen.btclivealerts

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class CanonicalSqliteReadContractTest {
    @Test
    fun bootstrapDdlDefinesIdentityAndAppendOnlyMigrationRegistry() {
        val ddl = CanonicalSqliteReadContract.bootstrapDdl

        assertEquals(6, ddl.size)
        assertTrue(ddl.any { it.contains("CREATE TABLE canonical_database_identity") })
        assertTrue(ddl.any { it.contains("singleton_key INTEGER PRIMARY KEY CHECK (singleton_key = 1)") })
        assertTrue(ddl.any { it.contains("CREATE TABLE schema_migrations") })
        assertTrue(ddl.any { it.contains("checksum_sha256") && it.contains("length(checksum_sha256) = 64") })
        assertEquals(4, ddl.count { it.contains("CREATE TRIGGER") })
        assertTrue(ddl.all { it.trim().endsWith(";") })
    }

    @Test
    fun identityAndMigrationRowsCannotBeUpdatedOrDeletedByTheDeclaredTriggers() {
        val ddl = CanonicalSqliteReadContract.bootstrapDdl.joinToString("\n")

        assertTrue(ddl.contains("BEFORE UPDATE ON canonical_database_identity"))
        assertTrue(ddl.contains("BEFORE DELETE ON canonical_database_identity"))
        assertTrue(ddl.contains("BEFORE UPDATE ON schema_migrations"))
        assertTrue(ddl.contains("BEFORE DELETE ON schema_migrations"))
        assertEquals(4, Regex("RAISE\\(ABORT").findAll(ddl).count())
    }

    @Test
    fun fixedReadQueriesReadAllEvidenceInDeterministicOrder() {
        val queries = CanonicalSqliteReadContract.fixedReadQueries.associateBy { it.id }

        assertEquals(4, queries.size)
        assertEquals(
            "SELECT sqlite_version(), sqlite_source_id()",
            queries.getValue(SqliteReadQueryId.RUNTIME_IDENTITY).sql,
        )
        assertTrue(queries.getValue(SqliteReadQueryId.CANONICAL_IDENTITY).sql.contains("ORDER BY singleton_key"))
        assertFalse(queries.getValue(SqliteReadQueryId.CANONICAL_IDENTITY).sql.contains("LIMIT"))
        assertTrue(queries.getValue(SqliteReadQueryId.MIGRATION_CHAIN).sql.contains("ORDER BY sequence"))
        assertFalse(queries.getValue(SqliteReadQueryId.MIGRATION_CHAIN).sql.contains("LIMIT"))
        assertTrue(queries.getValue(SqliteReadQueryId.SCHEMA_CATALOG).sql.contains("sqlite_schema"))
        assertTrue(queries.getValue(SqliteReadQueryId.SCHEMA_CATALOG).sql.contains("ORDER BY type, name, tbl_name, sql"))
    }

    @Test
    fun schemaIntrospectionUsesOnlyCatalogTablesAndIndexesInStableOrder() {
        val catalog = listOf(
            SqliteSchemaCatalogEntry("table", "z_table", "z_table", "CREATE TABLE z_table(id INTEGER)"),
            SqliteSchemaCatalogEntry("index", "idx_z", "z_table", "CREATE INDEX idx_z ON z_table(id)"),
            SqliteSchemaCatalogEntry("view", "v_secret", "v_secret", "CREATE VIEW v_secret AS SELECT 1"),
            SqliteSchemaCatalogEntry("table", "a_table", "a_table", "CREATE TABLE a_table(id INTEGER)"),
        )

        val queries = CanonicalSqliteReadContract.schemaIntrospectionQueries(catalog)

        assertEquals(
            listOf("PRAGMA table_xinfo(\"a_table\")", "PRAGMA index_list(\"a_table\")",
                "PRAGMA foreign_key_list(\"a_table\")", "PRAGMA table_xinfo(\"z_table\")",
                "PRAGMA index_list(\"z_table\")", "PRAGMA foreign_key_list(\"z_table\")",
                "PRAGMA index_xinfo(\"idx_z\")"),
            queries.map { it.sql },
        )
        assertTrue(queries.all { it.id == SqliteReadQueryId.SCHEMA_INTROSPECTION })
    }

    @Test
    fun schemaIntrospectionIncludesViewColumnsAndFullIndexMetadata() {
        val catalog = listOf(
            SqliteSchemaCatalogEntry("view", "v_positions", "v_positions", "CREATE VIEW v_positions AS SELECT id FROM positions"),
            SqliteSchemaCatalogEntry("index", "idx_positions_expr", "positions", "CREATE INDEX idx_positions_expr ON positions(lower(symbol))"),
        )

        assertEquals(
            listOf("PRAGMA table_xinfo(\"v_positions\")", "PRAGMA index_xinfo(\"idx_positions_expr\")"),
            CanonicalSqliteReadContract.schemaIntrospectionQueries(catalog).map { it.sql },
        )
    }

    @Test
    fun schemaIntrospectionRejectsUnknownCatalogObjectTypesInsteadOfSilentlyDroppingThem() {
        val catalog = listOf(SqliteSchemaCatalogEntry("unknown_future_type", "future_obj", "future_obj", null))
        try {
            CanonicalSqliteReadContract.schemaIntrospectionQueries(catalog)
            throw AssertionError("unknown schema object type must fail closed")
        } catch (expected: IllegalArgumentException) {
            assertTrue(expected.message.orEmpty().contains("unknown_future_type"))
        }
    }

    @Test
    fun virtualTableDeclarationsFailClosedUntilModuleProvenanceIsVerified() {
        val catalog = listOf(
            SqliteSchemaCatalogEntry("table", "external_content", "external_content",
                "CREATE VIRTUAL TABLE external_content USING fts5(body)"),
        )
        try {
            CanonicalSqliteReadContract.schemaIntrospectionQueries(catalog)
            throw AssertionError("virtual tables must not be accepted without module provenance")
        } catch (expected: IllegalArgumentException) {
            assertTrue(expected.message.orEmpty().contains("virtual"))
        }
    }

    @Test
    fun identifierQuotingEscapesEmbeddedQuotesWithoutRewritingTheIdentifier() {
        assertEquals("\"table\"\"name\"", CanonicalSqliteReadContract.quoteIdentifier("table\"name"))
    }

    @Test
    fun schemaIntrospectionNeverAcceptsSqlFragmentsAsCatalogNames() {
        val catalog = listOf(
            SqliteSchemaCatalogEntry("table", "safe\"; DROP TABLE x;--", "t", null),
        )

        val queries = CanonicalSqliteReadContract.schemaIntrospectionQueries(catalog)

        assertEquals(3, queries.size)
        assertTrue(queries.all { it.sql.startsWith("PRAGMA ") })
        assertEquals("PRAGMA table_xinfo(\"safe\"\"; DROP TABLE x;--\")", queries.first().sql)
    }

    @Test
    fun internalSqliteObjectsAndUnsupportedCatalogTypesAreExcluded() {
        val catalog = listOf(
            SqliteSchemaCatalogEntry("table", "sqlite_sequence", "sqlite_sequence", null),
            SqliteSchemaCatalogEntry("trigger", "trg", "t", null),
            SqliteSchemaCatalogEntry("view", "v", "v", null),
        )

        assertTrue(CanonicalSqliteReadContract.schemaIntrospectionQueries(catalog).isEmpty())
    }
}
