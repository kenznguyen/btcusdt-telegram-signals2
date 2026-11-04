package com.kenznguyen.btclivealerts

data class NativeCanonicalIdentityRow(
    val singletonKey: Int,
    val roleId: String,
    val instanceId: String,
    val identityFormatVersion: Int,
    val provenance: String,
    val parentInstanceId: String?,
    val createdAtUtc: String,
)

data class NativeAppliedMigrationRow(
    val migrationId: String,
    val sequence: Int,
    val ownerDomain: String,
    val checksumSha256: String,
    val appliedAtUtc: String,
)

data class CanonicalReadSnapshotAssemblyResult(
    val verification: ReadSnapshotVerificationResult,
    val snapshot: CanonicalDatabaseReadSnapshot? = null,
)

object CanonicalReadSnapshotAssembler {
    fun assemble(
        nativeReply: NativeSqliteD5SnapshotReply,
        pinResult: IdentityPinParseResult,
        migrationCatalog: List<MigrationDescriptor>,
        expectedSchemaDigest: String,
    ): CanonicalReadSnapshotAssemblyResult {
        if (nativeReply.status != NativeSqliteD5ReadStatus.VERIFIED ||
            nativeReply.envelope == null || nativeReply.transactionToken.isBlank()
        ) return rejected(ReadSnapshotVerificationStatus.READ_UNCERTAIN)

        val pin = (pinResult as? IdentityPinParseResult.Valid)?.pin
            ?: return rejected(ReadSnapshotVerificationStatus.IDENTITY_MISSING)
        if (pin.state != IdentityPinLifecycleState.ACTIVE) {
            return rejected(ReadSnapshotVerificationStatus.IDENTITY_MISSING)
        }

        val rows = nativeReply.identityRows
        if (rows.size != 1) return rejected(ReadSnapshotVerificationStatus.INCOMPLETE_EVIDENCE)
        val identity = rows.single()
        if (identity.singletonKey != 1 || identity.identityFormatVersion != 1 ||
            identity.roleId.isBlank() || identity.createdAtUtc.isBlank() ||
            identity.provenance !in setOf("INITIAL_PROVISIONING", "LEGACY_ADOPTION", "CLONE_FORK") ||
            (identity.provenance == "CLONE_FORK") != (identity.parentInstanceId != null)
        ) return rejected(ReadSnapshotVerificationStatus.INCOMPLETE_EVIDENCE)

        val observedRole = try {
            CanonicalDatabaseRoleId.fromPersisted(identity.roleId)
        } catch (_: IllegalArgumentException) {
            return rejected(ReadSnapshotVerificationStatus.INCOMPLETE_EVIDENCE)
        }
        val observedInstance = CanonicalDatabaseInstanceId.tryFromPersisted(identity.instanceId)
            ?: return rejected(ReadSnapshotVerificationStatus.INCOMPLETE_EVIDENCE)
        if (pin.roleId != observedRole || pin.instanceId != observedInstance) {
            val schemaStatus = if (pin.roleId != observedRole) {
                SchemaVerificationStatus.ROLE_MISMATCH
            } else SchemaVerificationStatus.INSTANCE_MISMATCH
            return rejected(ReadSnapshotVerificationStatus.SCHEMA_REJECTED, schemaStatus)
        }
        if (identity.parentInstanceId != null &&
            CanonicalDatabaseInstanceId.tryFromPersisted(identity.parentInstanceId) == null
        ) return rejected(ReadSnapshotVerificationStatus.INCOMPLETE_EVIDENCE)

        val appliedRows = nativeReply.appliedMigrationRows
        if (appliedRows.any {
                it.migrationId.isBlank() || it.ownerDomain.isBlank() ||
                    it.appliedAtUtc.isBlank() || !it.checksumSha256.matches(Regex("[0-9a-f]{64}"))
            }
        ) return rejected(ReadSnapshotVerificationStatus.INCOMPLETE_EVIDENCE)

        val catalogById = migrationCatalog.associateBy { it.migrationId }
        if (catalogById.size != migrationCatalog.size ||
            appliedRows.any { catalogById[it.migrationId]?.ownerDomain != it.ownerDomain }
        ) return rejected(
            ReadSnapshotVerificationStatus.SCHEMA_REJECTED,
            SchemaVerificationStatus.UNKNOWN_MIGRATION,
        )
        val applied = appliedRows.map {
            AppliedMigration(it.migrationId, it.sequence, it.checksumSha256)
        }
        val observedDigest = try {
            CanonicalD5Serializer.sha256Hex(nativeReply.envelope)
        } catch (_: IllegalArgumentException) {
            return rejected(ReadSnapshotVerificationStatus.INCOMPLETE_EVIDENCE)
        }
        val snapshot = CanonicalDatabaseReadSnapshot.capture(
            readTransactionToken = nativeReply.transactionToken,
            databaseState = ReadSnapshotDatabaseState.COMPLETE,
            consistency = ReadSnapshotConsistency.SINGLE_SQLITE_READ_TRANSACTION,
            observedRoleId = observedRole,
            observedInstanceId = observedInstance,
            migrationCatalog = migrationCatalog,
            appliedMigrations = applied,
            expectedSchemaDigest = expectedSchemaDigest,
            observedSchemaDigest = observedDigest,
            sqliteVersion = nativeReply.envelope.runtime.sqliteVersion,
            sqliteSourceId = nativeReply.envelope.runtime.sqliteSourceId,
        )
        val verification = CanonicalDatabaseReadSnapshotVerifier.verify(
            snapshot, pin.roleId, pin.instanceId,
        )
        return if (verification.status == ReadSnapshotVerificationStatus.VERIFIED) {
            CanonicalReadSnapshotAssemblyResult(verification, snapshot)
        } else {
            CanonicalReadSnapshotAssemblyResult(verification, null)
        }
    }

    private fun rejected(
        status: ReadSnapshotVerificationStatus,
        schemaStatus: SchemaVerificationStatus? = null,
    ) = CanonicalReadSnapshotAssemblyResult(ReadSnapshotVerificationResult(status, schemaStatus))
}
