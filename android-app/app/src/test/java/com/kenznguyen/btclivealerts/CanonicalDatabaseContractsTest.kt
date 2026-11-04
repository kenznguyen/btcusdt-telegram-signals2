package com.kenznguyen.btclivealerts

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class CanonicalDatabaseContractsTest {
    @Test
    fun logicalRoleIdIsIndependentFromPhysicalInstanceId() {
        val role = CanonicalDatabaseRoleId.canonicalT0()
        val instance = CanonicalDatabaseInstanceId.fromPersisted("opaque-instance-001")

        assertEquals("t0-canonical-sqlite-v1", role.value)
        assertEquals("opaque-instance-001", instance.value)
        assertFalse(role.value == instance.value)
    }

    @Test
    fun persistedInstanceIdRejectsBlankOrUnsafeValuesWithoutGeneratingReplacement() {
        assertEquals(null, CanonicalDatabaseInstanceId.tryFromPersisted(" "))
        assertEquals(null, CanonicalDatabaseInstanceId.tryFromPersisted("bad\u0000id"))
        assertEquals(null, CanonicalDatabaseInstanceId.tryFromPersisted(null))
    }

    @Test
    fun backupRestorePreservesInstanceLineage() {
        val instance = CanonicalDatabaseInstanceId.fromPersisted("db-lineage-a")
        val restored = CanonicalDatabaseLineage.restored(instance)

        assertEquals(instance, restored.instanceId)
        assertEquals(null, restored.parentInstanceId)
    }

    @Test
    fun explicitCloneUsesNewInstanceAndRecordsParent() {
        val original = CanonicalDatabaseInstanceId.fromPersisted("db-original")
        val clone = CanonicalDatabaseInstanceId.fromPersisted("db-clone")

        val forked = CanonicalDatabaseLineage.fork(clone, original)

        assertEquals(clone, forked.instanceId)
        assertEquals(original, forked.parentInstanceId)
        assertFalse(forked.instanceId == original)
    }

    @Test
    fun identityEvidenceDomainsHaveDistinctTypes() {
        val backup = BackupId.fromPersisted("backup-1")
        val epoch = RestoreEpoch(4L)
        val lease = LeaseGeneration(8L)

        assertEquals("backup-1", backup.value)
        assertEquals(4L, epoch.value)
        assertEquals(8L, lease.value)
    }

    @Test
    fun migrationCatalogVerifiesExactBytesAndOneDatabaseWideSequence() {
        val firstBytes = "CREATE TABLE candles(id INTEGER);".toByteArray()
        val secondBytes = "CREATE TABLE ledger(id INTEGER);".toByteArray()
        val catalog = listOf(
            MigrationDescriptor.create("001-market", 1, "market_data", firstBytes),
            MigrationDescriptor.create("002-ledger", 2, "paper_ledger", secondBytes),
        )
        val applied = catalog.map { AppliedMigration(it.migrationId, it.sequence, it.checksumSha256) }

        val result = ReadOnlySchemaVerifier.verify(
            expectedRoleId = CanonicalDatabaseRoleId.canonicalT0(),
            observedRoleId = CanonicalDatabaseRoleId.canonicalT0(),
            expectedInstanceId = null,
            observedInstanceId = null,
            catalog = catalog,
            applied = applied,
            expectedSchemaDigest = "schema-v1",
            observedSchemaDigest = "schema-v1",
        )

        assertEquals(SchemaVerificationStatus.VERIFIED, result.status)
        assertEquals(listOf("001-market", "002-ledger"), result.appliedMigrationIds)
    }

    @Test
    fun migrationByteMutationIsRejected() {
        val bytes = "CREATE TABLE candles(id INTEGER);".toByteArray()
        val descriptor = MigrationDescriptor.create("001-market", 1, "market_data", bytes)
        val applied = listOf(AppliedMigration("001-market", 1, "0".repeat(64)))

        val result = ReadOnlySchemaVerifier.verify(
            expectedRoleId = CanonicalDatabaseRoleId.canonicalT0(),
            observedRoleId = CanonicalDatabaseRoleId.canonicalT0(),
            expectedInstanceId = null,
            observedInstanceId = null,
            catalog = listOf(descriptor),
            applied = applied,
            expectedSchemaDigest = "schema-v1",
            observedSchemaDigest = "schema-v1",
        )

        assertEquals(SchemaVerificationStatus.CHECKSUM_MISMATCH, result.status)
    }

    @Test
    fun roleOrInstanceMismatchFailsClosed() {
        val roleMismatch = ReadOnlySchemaVerifier.verify(
            expectedRoleId = CanonicalDatabaseRoleId.canonicalT0(),
            observedRoleId = CanonicalDatabaseRoleId.fromPersisted("other-role"),
            expectedInstanceId = null,
            observedInstanceId = null,
            catalog = emptyList(),
            applied = emptyList(),
            expectedSchemaDigest = "schema-v1",
            observedSchemaDigest = "schema-v1",
        )
        val instanceMismatch = ReadOnlySchemaVerifier.verify(
            expectedRoleId = CanonicalDatabaseRoleId.canonicalT0(),
            observedRoleId = CanonicalDatabaseRoleId.canonicalT0(),
            expectedInstanceId = CanonicalDatabaseInstanceId.fromPersisted("expected"),
            observedInstanceId = CanonicalDatabaseInstanceId.fromPersisted("observed"),
            catalog = emptyList(),
            applied = emptyList(),
            expectedSchemaDigest = "schema-v1",
            observedSchemaDigest = "schema-v1",
        )

        assertEquals(SchemaVerificationStatus.ROLE_MISMATCH, roleMismatch.status)
        assertEquals(SchemaVerificationStatus.INSTANCE_MISMATCH, instanceMismatch.status)
    }

    @Test
    fun unknownInstanceIdentityIsNotInventedAndDoesNotVerify() {
        val result = ReadOnlySchemaVerifier.verify(
            expectedRoleId = CanonicalDatabaseRoleId.canonicalT0(),
            observedRoleId = CanonicalDatabaseRoleId.canonicalT0(),
            expectedInstanceId = null,
            observedInstanceId = null,
            catalog = emptyList(),
            applied = emptyList(),
            expectedSchemaDigest = "schema-v1",
            observedSchemaDigest = "schema-v1",
        )

        assertTrue(result.instanceIdentityUnknown)
        assertEquals(SchemaVerificationStatus.IDENTITY_UNKNOWN, result.status)
    }

    @Test
    fun schemaDriftIsSeparateFromMigrationChainEvidence() {
        val result = ReadOnlySchemaVerifier.verify(
            expectedRoleId = CanonicalDatabaseRoleId.canonicalT0(),
            observedRoleId = CanonicalDatabaseRoleId.canonicalT0(),
            expectedInstanceId = null,
            observedInstanceId = null,
            catalog = emptyList(),
            applied = emptyList(),
            expectedSchemaDigest = "schema-expected",
            observedSchemaDigest = "schema-observed",
        )

        assertEquals(SchemaVerificationStatus.SCHEMA_DRIFT, result.status)
    }
}
