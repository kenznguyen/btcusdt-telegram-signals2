package com.kenznguyen.btclivealerts

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class CanonicalDatabaseReadSnapshotTest {
    private val role = CanonicalDatabaseRoleId.canonicalT0()
    private val instance = CanonicalDatabaseInstanceId.fromPersisted(
        "550e8400-e29b-41d4-a716-446655440000",
    )
    private val migration = MigrationDescriptor.create(
        migrationId = "t0.bootstrap.v1",
        sequence = 1,
        ownerDomain = "T0",
        exactMigrationBytes = byteArrayOf(1, 2, 3),
    )
    private val applied = AppliedMigration(
        migrationId = migration.migrationId,
        sequence = migration.sequence,
        checksumSha256 = migration.checksumSha256,
    )

    private fun completeSnapshot(
        consistency: ReadSnapshotConsistency = ReadSnapshotConsistency.SINGLE_SQLITE_READ_TRANSACTION,
        state: ReadSnapshotDatabaseState = ReadSnapshotDatabaseState.COMPLETE,
        observedRole: CanonicalDatabaseRoleId? = role,
        observedInstance: CanonicalDatabaseInstanceId? = instance,
        catalog: List<MigrationDescriptor> = listOf(migration),
        appliedMigrations: List<AppliedMigration> = listOf(applied),
        expectedDigest: String? = "schema-digest-v1",
        observedDigest: String? = "schema-digest-v1",
        sqliteVersion: String? = "3.45.1",
        sqliteSourceId: String? = "source-id-v1",
    ) = CanonicalDatabaseReadSnapshot.capture(
        readTransactionToken = "capture-001",
        databaseState = state,
        consistency = consistency,
        observedRoleId = observedRole,
        observedInstanceId = observedInstance,
        migrationCatalog = catalog,
        appliedMigrations = appliedMigrations,
        expectedSchemaDigest = expectedDigest,
        observedSchemaDigest = observedDigest,
        sqliteVersion = sqliteVersion,
        sqliteSourceId = sqliteSourceId,
    )

    @Test
    fun completeSingleTransactionSnapshotVerifies() {
        val result = CanonicalDatabaseReadSnapshotVerifier.verify(
            completeSnapshot(),
            expectedRoleId = role,
            expectedInstanceId = instance,
        )

        assertEquals(ReadSnapshotVerificationStatus.VERIFIED, result.status)
        assertEquals(SchemaVerificationStatus.VERIFIED, result.schemaStatus)
    }

    @Test
    fun unprovenOrMultipleTransactionEvidenceIsRejected() {
        for (consistency in listOf(
            ReadSnapshotConsistency.UNPROVEN,
            ReadSnapshotConsistency.MULTIPLE_READ_TRANSACTIONS,
        )) {
            val result = CanonicalDatabaseReadSnapshotVerifier.verify(
                completeSnapshot(consistency = consistency),
                role,
                instance,
            )
            assertEquals(ReadSnapshotVerificationStatus.READ_TRANSACTION_NOT_PROVEN, result.status)
        }
    }

    @Test
    fun missingDatabaseIsNotTreatedAsAnEmptyDatabase() {
        val result = CanonicalDatabaseReadSnapshotVerifier.verify(
            completeSnapshot(state = ReadSnapshotDatabaseState.MISSING),
            role,
            instance,
        )
        assertEquals(ReadSnapshotVerificationStatus.DATABASE_MISSING, result.status)
    }

    @Test
    fun legacyDatabaseIsRejectedWithoutInferringAnIdentity() {
        val result = CanonicalDatabaseReadSnapshotVerifier.verify(
            completeSnapshot(state = ReadSnapshotDatabaseState.LEGACY_UNVERSIONED),
            role,
            instance,
        )
        assertEquals(ReadSnapshotVerificationStatus.LEGACY_UNVERSIONED, result.status)
    }

    @Test
    fun missingIdentityIsRejected() {
        val result = CanonicalDatabaseReadSnapshotVerifier.verify(
            completeSnapshot(state = ReadSnapshotDatabaseState.IDENTITY_MISSING),
            role,
            instance,
        )
        assertEquals(ReadSnapshotVerificationStatus.IDENTITY_MISSING, result.status)
    }

    @Test
    fun uncertainReadIsRejected() {
        val result = CanonicalDatabaseReadSnapshotVerifier.verify(
            completeSnapshot(state = ReadSnapshotDatabaseState.READ_UNCERTAIN),
            role,
            instance,
        )
        assertEquals(ReadSnapshotVerificationStatus.READ_UNCERTAIN, result.status)
    }

    @Test
    fun roleAndInstanceMismatchesAreReportedBySchemaVerifier() {
        val wrongRole = CanonicalDatabaseRoleId.fromPersisted("another-role")
        val wrongInstance = CanonicalDatabaseInstanceId.fromPersisted(
            "550e8400-e29b-41d4-a716-446655440001",
        )
        val roleResult = CanonicalDatabaseReadSnapshotVerifier.verify(
            completeSnapshot(observedRole = wrongRole),
            role,
            instance,
        )
        val instanceResult = CanonicalDatabaseReadSnapshotVerifier.verify(
            completeSnapshot(observedInstance = wrongInstance),
            role,
            instance,
        )

        assertEquals(ReadSnapshotVerificationStatus.SCHEMA_REJECTED, roleResult.status)
        assertEquals(SchemaVerificationStatus.ROLE_MISMATCH, roleResult.schemaStatus)
        assertEquals(SchemaVerificationStatus.INSTANCE_MISMATCH, instanceResult.schemaStatus)
    }

    @Test
    fun missingRequiredEvidenceIsRejected() {
        val result = CanonicalDatabaseReadSnapshotVerifier.verify(
            completeSnapshot(
                observedRole = null,
                expectedDigest = null,
                sqliteSourceId = null,
            ),
            role,
            instance,
        )
        assertEquals(ReadSnapshotVerificationStatus.INCOMPLETE_EVIDENCE, result.status)
    }

    @Test
    fun schemaDigestMismatchIsRejected() {
        val result = CanonicalDatabaseReadSnapshotVerifier.verify(
            completeSnapshot(observedDigest = "different-schema-digest"),
            role,
            instance,
        )
        assertEquals(ReadSnapshotVerificationStatus.SCHEMA_REJECTED, result.status)
        assertEquals(SchemaVerificationStatus.SCHEMA_DRIFT, result.schemaStatus)
    }

    @Test
    fun snapshotDefensivelyCopiesAndProtectsEvidenceLists() {
        val mutableCatalog = mutableListOf(migration)
        val mutableApplied = mutableListOf(applied)
        val snapshot = completeSnapshot(
            catalog = mutableCatalog,
            appliedMigrations = mutableApplied,
        )

        mutableCatalog.clear()
        mutableApplied.clear()
        assertEquals(1, snapshot.migrationCatalog.size)
        assertEquals(1, snapshot.appliedMigrations.size)

        var catalogMutationRejected = false
        try {
            (snapshot.migrationCatalog as MutableList<MigrationDescriptor>).add(migration)
        } catch (_: UnsupportedOperationException) {
            catalogMutationRejected = true
        }
        assertTrue(catalogMutationRejected)
        assertFalse(snapshot.readTransactionToken.isBlank())
    }
}
