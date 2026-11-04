package com.kenznguyen.btclivealerts

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class CanonicalReadSnapshotAssemblerTest {
    private val role = CanonicalDatabaseRoleId.canonicalT0()
    private val instance = CanonicalDatabaseInstanceId.fromPersisted("550e8400-e29b-41d4-a716-446655440000")
    private val pin = CanonicalDatabaseIdentityPin(role, instance, IdentityPinLifecycleState.ACTIVE)
    private val migration = MigrationDescriptor.create("t0.bootstrap.v1", 1, "T0", byteArrayOf(1, 2, 3))
    private val envelope = D5SchemaEnvelope(
        runtime = D5RuntimeIdentity(
            canonicalizationId = CanonicalD5SchemaContract.CANONICALIZATION_ID,
            canonicalizationVersion = CanonicalD5SchemaContract.CANONICALIZATION_VERSION,
            sqliteVersion = "3.54.1",
            sqliteSourceId = "2026-10-16 14:45:20 555e07ef33f69a0957d24d8e555b702464a131d6f1607f4c3c1e4551e8e6ca76",
            featureProbeSchemaVersion = "table_list_v1",
        ),
        catalog = emptyList(), tableColumns = emptyList(), indexes = emptyList(),
        indexColumns = emptyList(), foreignKeys = emptyList(),
    )
    private fun evidence(
        identityRows: List<NativeCanonicalIdentityRow> = listOf(
            NativeCanonicalIdentityRow(1, role.value, instance.value, 1, "INITIAL_PROVISIONING", null, "2026-11-04T00:00:00Z"),
        ),
        migrations: List<NativeAppliedMigrationRow> = listOf(
            NativeAppliedMigrationRow(migration.migrationId, 1, "T0", migration.checksumSha256, "2026-11-04T00:00:00Z"),
        ),
    ) = NativeSqliteD5SnapshotReply(
        status = NativeSqliteD5ReadStatus.VERIFIED,
        envelope = envelope,
        identityRows = identityRows,
        appliedMigrationRows = migrations,
        transactionToken = "native-handle:7",
    )

    @Test fun activePinAndSameTransactionIdentityMigrationAndD5ProduceVerifiedSnapshot() {
        val result = CanonicalReadSnapshotAssembler.assemble(
            evidence(), IdentityPinParseResult.Valid(pin), listOf(migration),
            CanonicalD5Serializer.sha256Hex(envelope),
        )
        assertEquals(ReadSnapshotVerificationStatus.VERIFIED, result.verification.status)
        assertTrue(result.snapshot != null)
        assertEquals("native-handle:7", result.snapshot?.readTransactionToken)
    }

    @Test fun pendingPinNeverProducesVerifiedSnapshot() {
        val pending = CanonicalDatabaseIdentityPin(role, instance, IdentityPinLifecycleState.PENDING)
        val result = CanonicalReadSnapshotAssembler.assemble(
            evidence(), IdentityPinParseResult.Valid(pending), listOf(migration),
            CanonicalD5Serializer.sha256Hex(envelope),
        )
        assertEquals(ReadSnapshotVerificationStatus.IDENTITY_MISSING, result.verification.status)
        assertFalse(result.snapshot != null)
    }

    @Test fun duplicateIdentityRowsAreRejected() {
        val row = evidence().identityRows.single()
        val result = CanonicalReadSnapshotAssembler.assemble(
            evidence(identityRows = listOf(row, row)), IdentityPinParseResult.Valid(pin),
            listOf(migration), CanonicalD5Serializer.sha256Hex(envelope),
        )
        assertEquals(ReadSnapshotVerificationStatus.INCOMPLETE_EVIDENCE, result.verification.status)
        assertFalse(result.snapshot != null)
    }

    @Test fun pinMismatchIsRejected() {
        val wrong = CanonicalDatabaseIdentityPin(
            role, CanonicalDatabaseInstanceId.fromPersisted("550e8400-e29b-41d4-a716-446655440001"),
            IdentityPinLifecycleState.ACTIVE,
        )
        val result = CanonicalReadSnapshotAssembler.assemble(
            evidence(), IdentityPinParseResult.Valid(wrong), listOf(migration),
            CanonicalD5Serializer.sha256Hex(envelope),
        )
        assertEquals(ReadSnapshotVerificationStatus.SCHEMA_REJECTED, result.verification.status)
        assertEquals(SchemaVerificationStatus.INSTANCE_MISMATCH, result.verification.schemaStatus)
    }

    @Test fun migrationChecksumMismatchIsRejected() {
        val bad = evidence(migrations = listOf(
            NativeAppliedMigrationRow(migration.migrationId, 1, "T0", "0".repeat(64), "2026-11-04T00:00:00Z"),
        ))
        val result = CanonicalReadSnapshotAssembler.assemble(
            bad, IdentityPinParseResult.Valid(pin), listOf(migration),
            CanonicalD5Serializer.sha256Hex(envelope),
        )
        assertEquals(SchemaVerificationStatus.CHECKSUM_MISMATCH, result.verification.schemaStatus)
    }

    @Test fun callerCannotSupplyObservedDigestAsEvidence() {
        val result = CanonicalReadSnapshotAssembler.assemble(
            evidence(), IdentityPinParseResult.Valid(pin), listOf(migration), "wrong-digest",
        )
        assertEquals(SchemaVerificationStatus.SCHEMA_DRIFT, result.verification.schemaStatus)
    }

    @Test fun nonVerifiedNativeReplyReturnsNoPartialSnapshot() {
        val result = CanonicalReadSnapshotAssembler.assemble(
            NativeSqliteD5SnapshotReply(NativeSqliteD5ReadStatus.QUERY_FAILED),
            IdentityPinParseResult.Valid(pin), listOf(migration), CanonicalD5Serializer.sha256Hex(envelope),
        )
        assertEquals(ReadSnapshotVerificationStatus.READ_UNCERTAIN, result.verification.status)
        assertFalse(result.snapshot != null)
    }
}
