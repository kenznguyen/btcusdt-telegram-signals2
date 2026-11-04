package com.kenznguyen.btclivealerts

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class CanonicalD5SchemaContractTest {
    @Test
    fun runtimeRequiresSqlite337AndExactTableListShape() {
        assertEquals("3.37.0", CanonicalD5SchemaContract.MINIMUM_SQLITE_VERSION)
        assertEquals(
            D5RuntimeStatus.ACCEPTED,
            CanonicalD5SchemaContract.validateRuntime(
                "3.45.1", "source-id",
                CanonicalD5SchemaContract.TABLE_LIST_COLUMNS,
            ).status,
        )
        assertEquals(
            D5RuntimeStatus.BELOW_MINIMUM,
            CanonicalD5SchemaContract.validateRuntime(
                "3.36.0", "source-id",
                CanonicalD5SchemaContract.TABLE_LIST_COLUMNS,
            ).status,
        )
        assertEquals(
            D5RuntimeStatus.TABLE_LIST_UNAVAILABLE,
            CanonicalD5SchemaContract.validateRuntime("3.45.1", "source-id", emptyList()).status,
        )
        assertEquals(
            D5RuntimeStatus.RESULT_SHAPE_MISMATCH,
            CanonicalD5SchemaContract.validateRuntime(
                "3.45.1", "source-id",
                CanonicalD5SchemaContract.TABLE_LIST_COLUMNS + "future_column",
            ).status,
        )
    }

    @Test
    fun runtimeRequiresAndPreservesExactSourceId() {
        val missing = CanonicalD5SchemaContract.validateRuntime(
            "3.45.1", " ", CanonicalD5SchemaContract.TABLE_LIST_COLUMNS,
        )
        assertEquals(D5RuntimeStatus.MISSING_SOURCE_ID, missing.status)
        val valid = CanonicalD5SchemaContract.validateRuntime(
            "3.45.1", "vendor-build-identity", CanonicalD5SchemaContract.TABLE_LIST_COLUMNS,
        )
        assertEquals("vendor-build-identity", valid.sqliteSourceId)
    }

    @Test
    fun tableListRejectsVirtualAndShadowObjectsAndUnknownTypes() {
        for (type in listOf("virtual", "shadow", "future")) {
            val result = CanonicalD5SchemaContract.validateTableList(
                listOf(D5TableListEntry("main", "objects", type, 1, false, false)),
                emptyList(),
            )
            assertEquals(D5SchemaStatus.UNSUPPORTED_OBJECT_TYPE, result.status)
        }
    }

    @Test
    fun tableListAndCatalogMustMatchAfterInternalObjectExclusion() {
        val tableList = listOf(
            D5TableListEntry("main", "positions", "table", 3, false, false),
            D5TableListEntry("main", "sqlite_sequence", "table", 2, false, false),
            D5TableListEntry("main", "active_positions", "view", 3, false, false),
        )
        val catalog = listOf(
            D5CatalogObjectIdentity("main", "table", "positions", "positions"),
            D5CatalogObjectIdentity("main", "table", "sqlite_sequence", "sqlite_sequence"),
            D5CatalogObjectIdentity("main", "view", "active_positions", "active_positions"),
        )
        assertEquals(
            D5SchemaStatus.ACCEPTED,
            CanonicalD5SchemaContract.validateTableList(tableList, catalog).status,
        )
        assertEquals(
            D5SchemaStatus.CATALOG_MISMATCH,
            CanonicalD5SchemaContract.validateTableList(
                tableList,
                catalog.filterNot { it.name == "positions" },
            ).status,
        )
    }

    @Test
    fun pragmaResultShapesAreExactAndUnknownColumnsFailClosed() {
        assertTrue(CanonicalD5SchemaContract.hasExactPragmaShape(
            D5PragmaKind.TABLE_XINFO,
            listOf("cid", "name", "type", "notnull", "dflt_value", "pk", "hidden"),
        ))
        assertFalse(CanonicalD5SchemaContract.hasExactPragmaShape(
            D5PragmaKind.TABLE_XINFO,
            listOf("cid", "name", "type", "notnull", "dflt_value", "pk", "hidden", "future"),
        ))
        assertTrue(CanonicalD5SchemaContract.hasExactPragmaShape(
            D5PragmaKind.INDEX_XINFO,
            listOf("seqno", "cid", "name", "desc", "coll", "key"),
        ))
    }

    @Test
    fun v1InventoryCapturesLogicalSchemaAndExcludesPhysicalRootpage() {
        val inventory = CanonicalD5SchemaContract.V1_FIELD_INVENTORY
        assertTrue(inventory.getValue("catalog").containsAll(listOf("schema", "type", "name", "tbl_name", "sql_utf8_exact")))
        assertTrue(inventory.getValue("table_xinfo").containsAll(listOf("cid", "name", "type", "notnull", "dflt_value", "pk", "hidden")))
        assertTrue(inventory.getValue("index_xinfo").containsAll(listOf("seqno", "cid", "name", "desc", "coll", "key")))
        assertTrue(inventory.getValue("foreign_key_list").containsAll(listOf("id", "seq", "table", "from", "to", "on_update", "on_delete", "match")))
        assertFalse(inventory.values.flatten().contains("rootpage"))
    }
}
