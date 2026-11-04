package com.kenznguyen.btclivealerts

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class CanonicalDatabaseContractsTest {
    private val role = CanonicalDatabaseRoleId.canonicalT0()
    private val instance = CanonicalDatabaseInstanceId.fromPersisted("550e8400-e29b-41d4-a716-446655440000")

    @Test
    fun generatedVariantFlagMatchesParallelApplicationId() {
        assertEquals(BuildConfig.APPLICATION_ID.endsWith(".paper"), BuildConfig.PARALLEL_INSTALL)
    }

    @Test
    fun logicalRoleIdIsIndependentFromPhysicalInstanceId() {
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
        val restored = CanonicalDatabaseLineage.restored(instance)
        assertEquals(instance, restored.instanceId)
        assertEquals(null, restored.parentInstanceId)
    }

    @Test
    fun explicitCloneUsesNewInstanceAndRecordsParent() {
        val original = CanonicalDatabaseInstanceId.fromPersisted("550e8400-e29b-41d4-a716-446655440001")
        val clone = CanonicalDatabaseInstanceId.fromPersisted("550e8400-e29b-41d4-a716-446655440002")
        val forked = CanonicalDatabaseLineage.fork(clone, original)
        assertEquals(clone, forked.instanceId)
        assertEquals(original, forked.parentInstanceId)
        assertFalse(forked.instanceId == original)
    }

    @Test(expected = IllegalArgumentException::class)
    fun cloneCannotReuseParentInstanceId() {
        CanonicalDatabaseLineage.fork(instance, instance)
    }

    @Test
    fun identityEvidenceDomainsHaveDistinctTypes() {
        assertEquals("backup-1", BackupId.fromPersisted("backup-1").value)
        assertEquals(4L, RestoreEpoch(4L).value)
        assertEquals(8L, LeaseGeneration(8L).value)
    }

    @Test
    fun migrationCatalogVerifiesExactBytesAndOneDatabaseWideSequence() {
        val catalog = listOf(
            MigrationDescriptor.create("001-market", 1, "market_data", "CREATE TABLE candles(id INTEGER);".toByteArray()),
            MigrationDescriptor.create("002-ledger", 2, "paper_ledger", "CREATE TABLE ledger(id INTEGER);".toByteArray()),
        )
        val applied = catalog.map { AppliedMigration(it.migrationId, it.sequence, it.checksumSha256) }
        val result = verify(catalog, applied)
        assertEquals(SchemaVerificationStatus.VERIFIED, result.status)
        assertEquals(listOf("001-market", "002-ledger"), result.appliedMigrationIds)
    }

    @Test
    fun migrationByteMutationIsRejected() {
        val descriptor = MigrationDescriptor.create(
            "001-market", 1, "market_data", "CREATE TABLE candles(id INTEGER);".toByteArray(),
        )
        val applied = listOf(AppliedMigration("001-market", 1, "0".repeat(64)))
        assertEquals(SchemaVerificationStatus.CHECKSUM_MISMATCH, verify(listOf(descriptor), applied).status)
    }

    @Test
    fun roleOrInstanceMismatchFailsClosed() {
        val catalog = emptyList<MigrationDescriptor>()
        val applied = emptyList<AppliedMigration>()
        val roleMismatch = ReadOnlySchemaVerifier.verify(
            role, CanonicalDatabaseRoleId.fromPersisted("other-role"), instance, instance,
            catalog, applied, "schema-v1", "schema-v1",
        )
        val instanceMismatch = ReadOnlySchemaVerifier.verify(
            role, role, instance, CanonicalDatabaseInstanceId.fromPersisted("550e8400-e29b-41d4-a716-446655440003"),
            catalog, applied, "schema-v1", "schema-v1",
        )
        assertEquals(SchemaVerificationStatus.ROLE_MISMATCH, roleMismatch.status)
        assertEquals(SchemaVerificationStatus.INSTANCE_MISMATCH, instanceMismatch.status)
    }

    @Test
    fun unknownInstanceIdentityIsNotInventedAndDoesNotVerify() {
        val result = ReadOnlySchemaVerifier.verify(
            role, role, null, null, emptyList(), emptyList(), "schema-v1", "schema-v1",
        )
        assertTrue(result.instanceIdentityUnknown)
        assertEquals(SchemaVerificationStatus.IDENTITY_UNKNOWN, result.status)
    }

    @Test
    fun schemaDriftIsSeparateFromMigrationChainEvidence() {
        val result = verify(emptyList(), emptyList(), observedSchemaDigest = "schema-observed")
        assertEquals(SchemaVerificationStatus.SCHEMA_DRIFT, result.status)
    }

    @Test
    fun missingAppliedMigrationIsNotTreatedAsVerified() {
        val catalog = listOf(
            MigrationDescriptor.create("001-market", 1, "market_data", byteArrayOf(1)),
        )
        assertEquals(
            SchemaVerificationStatus.INCOMPLETE_OR_UNCERTAIN,
            verify(catalog, emptyList()).status,
        )
    }

    @Test
    fun migrationSequenceGapIsRejected() {
        val catalog = listOf(
            MigrationDescriptor.create("001-market", 1, "market_data", byteArrayOf(1)),
            MigrationDescriptor.create("003-risk", 3, "risk", byteArrayOf(3)),
        )
        val applied = catalog.map { AppliedMigration(it.migrationId, it.sequence, it.checksumSha256) }
        assertEquals(
            SchemaVerificationStatus.SEQUENCE_GAP_OR_DUPLICATE,
            verify(catalog, applied).status,
        )
    }

    @Test
    fun unknownAppliedMigrationIsRejected() {
        val applied = listOf(AppliedMigration("unknown", 1, "0".repeat(64)))
        assertEquals(
            SchemaVerificationStatus.UNKNOWN_MIGRATION,
            verify(emptyList(), applied).status,
        )
    }

    private fun verify(
        catalog: List<MigrationDescriptor>,
        applied: List<AppliedMigration>,
        observedSchemaDigest: String = "schema-v1",
    ) = ReadOnlySchemaVerifier.verify(
        expectedRoleId = role,
        observedRoleId = role,
        expectedInstanceId = instance,
        observedInstanceId = instance,
        catalog = catalog,
        applied = applied,
        expectedSchemaDigest = "schema-v1",
        observedSchemaDigest = observedSchemaDigest,
    )
}
