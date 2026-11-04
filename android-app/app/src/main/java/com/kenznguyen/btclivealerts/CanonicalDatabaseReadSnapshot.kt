package com.kenznguyen.btclivealerts

import java.util.Collections

enum class ReadSnapshotDatabaseState {
    COMPLETE,
    MISSING,
    LEGACY_UNVERSIONED,
    IDENTITY_MISSING,
    READ_UNCERTAIN,
}

enum class ReadSnapshotConsistency {
    SINGLE_SQLITE_READ_TRANSACTION,
    UNPROVEN,
    MULTIPLE_READ_TRANSACTIONS,
}

/**
 * Immutable evidence captured by one read-only SQLite snapshot operation.
 *
 * The consistency value is a claim made by the adapter boundary, not a cryptographic proof.
 * The actual SQLite adapter must populate every field from the same read transaction.
 */
class CanonicalDatabaseReadSnapshot private constructor(
    val readTransactionToken: String,
    val databaseState: ReadSnapshotDatabaseState,
    val consistency: ReadSnapshotConsistency,
    val observedRoleId: CanonicalDatabaseRoleId?,
    val observedInstanceId: CanonicalDatabaseInstanceId?,
    val migrationCatalog: List<MigrationDescriptor>,
    val appliedMigrations: List<AppliedMigration>,
    val expectedSchemaDigest: String?,
    val observedSchemaDigest: String?,
    val sqliteVersion: String?,
    val sqliteSourceId: String?,
) {
    companion object {
        fun capture(
            readTransactionToken: String,
            databaseState: ReadSnapshotDatabaseState,
            consistency: ReadSnapshotConsistency,
            observedRoleId: CanonicalDatabaseRoleId?,
            observedInstanceId: CanonicalDatabaseInstanceId?,
            migrationCatalog: List<MigrationDescriptor>,
            appliedMigrations: List<AppliedMigration>,
            expectedSchemaDigest: String?,
            observedSchemaDigest: String?,
            sqliteVersion: String?,
            sqliteSourceId: String?,
        ): CanonicalDatabaseReadSnapshot {
            require(readTransactionToken.isNotBlank()) { "Read transaction token is required" }
            return CanonicalDatabaseReadSnapshot(
                readTransactionToken = readTransactionToken,
                databaseState = databaseState,
                consistency = consistency,
                observedRoleId = observedRoleId,
                observedInstanceId = observedInstanceId,
                migrationCatalog = Collections.unmodifiableList(ArrayList(migrationCatalog)),
                appliedMigrations = Collections.unmodifiableList(ArrayList(appliedMigrations)),
                expectedSchemaDigest = expectedSchemaDigest,
                observedSchemaDigest = observedSchemaDigest,
                sqliteVersion = sqliteVersion,
                sqliteSourceId = sqliteSourceId,
            )
        }
    }
}

enum class ReadSnapshotVerificationStatus {
    VERIFIED,
    DATABASE_MISSING,
    LEGACY_UNVERSIONED,
    IDENTITY_MISSING,
    READ_UNCERTAIN,
    READ_TRANSACTION_NOT_PROVEN,
    INCOMPLETE_EVIDENCE,
    SCHEMA_REJECTED,
}

data class ReadSnapshotVerificationResult(
    val status: ReadSnapshotVerificationStatus,
    val schemaStatus: SchemaVerificationStatus? = null,
)

/**
 * Verifies a single immutable evidence value. It never opens SQLite, reads files, or repairs
 * schema state. A VERIFIED result only certifies the supplied evidence, not its runtime origin.
 */
object CanonicalDatabaseReadSnapshotVerifier {
    fun verify(
        snapshot: CanonicalDatabaseReadSnapshot,
        expectedRoleId: CanonicalDatabaseRoleId,
        expectedInstanceId: CanonicalDatabaseInstanceId,
    ): ReadSnapshotVerificationResult {
        when (snapshot.databaseState) {
            ReadSnapshotDatabaseState.MISSING ->
                return ReadSnapshotVerificationResult(ReadSnapshotVerificationStatus.DATABASE_MISSING)
            ReadSnapshotDatabaseState.LEGACY_UNVERSIONED ->
                return ReadSnapshotVerificationResult(ReadSnapshotVerificationStatus.LEGACY_UNVERSIONED)
            ReadSnapshotDatabaseState.IDENTITY_MISSING ->
                return ReadSnapshotVerificationResult(ReadSnapshotVerificationStatus.IDENTITY_MISSING)
            ReadSnapshotDatabaseState.READ_UNCERTAIN ->
                return ReadSnapshotVerificationResult(ReadSnapshotVerificationStatus.READ_UNCERTAIN)
            ReadSnapshotDatabaseState.COMPLETE -> Unit
        }

        if (snapshot.consistency != ReadSnapshotConsistency.SINGLE_SQLITE_READ_TRANSACTION) {
            return ReadSnapshotVerificationResult(
                ReadSnapshotVerificationStatus.READ_TRANSACTION_NOT_PROVEN,
            )
        }

        if (snapshot.readTransactionToken.isBlank() ||
            snapshot.observedRoleId == null ||
            snapshot.observedInstanceId == null ||
            snapshot.expectedSchemaDigest.isNullOrBlank() ||
            snapshot.observedSchemaDigest.isNullOrBlank() ||
            snapshot.sqliteVersion.isNullOrBlank() ||
            snapshot.sqliteSourceId.isNullOrBlank()
        ) {
            return ReadSnapshotVerificationResult(ReadSnapshotVerificationStatus.INCOMPLETE_EVIDENCE)
        }

        val schemaResult = ReadOnlySchemaVerifier.verify(
            expectedRoleId = expectedRoleId,
            observedRoleId = snapshot.observedRoleId,
            expectedInstanceId = expectedInstanceId,
            observedInstanceId = snapshot.observedInstanceId,
            catalog = snapshot.migrationCatalog,
            applied = snapshot.appliedMigrations,
            expectedSchemaDigest = snapshot.expectedSchemaDigest,
            observedSchemaDigest = snapshot.observedSchemaDigest,
        )
        return if (schemaResult.status == SchemaVerificationStatus.VERIFIED) {
            ReadSnapshotVerificationResult(
                status = ReadSnapshotVerificationStatus.VERIFIED,
                schemaStatus = schemaResult.status,
            )
        } else {
            ReadSnapshotVerificationResult(
                status = ReadSnapshotVerificationStatus.SCHEMA_REJECTED,
                schemaStatus = schemaResult.status,
            )
        }
    }
}
