package com.kenznguyen.btclivealerts

/**
 * Pure planning boundary for the two-resource identity bootstrap protocol.
 *
 * This planner performs no filesystem or SQLite operation, allocates no UUID, and cannot
 * promote a pin. Callers must execute only the explicit plan returned after checking
 * their maintenance authorization and platform-specific durability guarantees.
 */
data class IdentityProvisioningPreconditions(
    val explicitMaintenanceAuthorization: Boolean,
    val databasePathConfirmedAbsentOrApprovedEmpty: Boolean,
    val noActiveWriterOrLease: Boolean,
    val noAcceptedIdentity: Boolean,
    val noLegacyData: Boolean,
) {
    fun areSatisfied(): Boolean =
        explicitMaintenanceAuthorization &&
            databasePathConfirmedAbsentOrApprovedEmpty &&
            noActiveWriterOrLease &&
            noAcceptedIdentity &&
            noLegacyData
}

enum class ProvisioningPinState {
    MISSING,
    PENDING,
    ACTIVE,
    MALFORMED,
    UNSUPPORTED,
    UNREADABLE,
    PROMOTION_UNCERTAIN,
}

enum class ProvisioningDatabaseEvidence {
    MISSING,
    IDENTITY_MATCHES_PIN,
    IDENTITY_MISMATCH,
    LEGACY,
    UNVERIFIED,
    READ_UNCERTAIN,
}

enum class ProvisioningMaintenanceAction {
    NONE,
    START,
    RESUME_SAME_ID,
    FINALIZE_PENDING,
}

enum class IdentityProvisioningPlan {
    IDENTITY_ACTIVE,
    CREATE_PENDING_PIN,
    RESUME_BOOTSTRAP_WITH_SAME_PENDING_ID,
    PROMOTE_EXACT_PENDING_PIN_TO_ACTIVE,
    REQUIRE_READ_ONLY_RECONCILIATION,
    NO_AUTOMATIC_ACTION,
    BLOCKED_PRECONDITIONS,
    BLOCKED_EVIDENCE,
}

/**
 * Maps an observed two-resource state and an explicit maintenance intent to a safe next
 * action. It deliberately does not perform that action.
 */
object IdentityProvisioningPlanner {
    fun plan(
        pinState: ProvisioningPinState,
        databaseState: ProvisioningDatabaseEvidence,
        readOnlyVerified: Boolean,
        preconditions: IdentityProvisioningPreconditions,
        action: ProvisioningMaintenanceAction,
    ): IdentityProvisioningPlan {
        if (pinState == ProvisioningPinState.MALFORMED ||
            pinState == ProvisioningPinState.UNSUPPORTED ||
            pinState == ProvisioningPinState.UNREADABLE
        ) {
            return IdentityProvisioningPlan.BLOCKED_EVIDENCE
        }

        if (databaseState == ProvisioningDatabaseEvidence.LEGACY ||
            databaseState == ProvisioningDatabaseEvidence.IDENTITY_MISMATCH
        ) {
            return IdentityProvisioningPlan.BLOCKED_EVIDENCE
        }

        if (pinState == ProvisioningPinState.PROMOTION_UNCERTAIN ||
            databaseState == ProvisioningDatabaseEvidence.READ_UNCERTAIN
        ) {
            return IdentityProvisioningPlan.REQUIRE_READ_ONLY_RECONCILIATION
        }

        if (pinState == ProvisioningPinState.ACTIVE) {
            return if (databaseState == ProvisioningDatabaseEvidence.IDENTITY_MATCHES_PIN &&
                readOnlyVerified
            ) {
                IdentityProvisioningPlan.IDENTITY_ACTIVE
            } else if (databaseState == ProvisioningDatabaseEvidence.UNVERIFIED ||
                !readOnlyVerified
            ) {
                IdentityProvisioningPlan.REQUIRE_READ_ONLY_RECONCILIATION
            } else {
                IdentityProvisioningPlan.BLOCKED_EVIDENCE
            }
        }

        if (databaseState == ProvisioningDatabaseEvidence.UNVERIFIED) {
            return IdentityProvisioningPlan.REQUIRE_READ_ONLY_RECONCILIATION
        }

        if (!preconditions.areSatisfied()) {
            return if (action == ProvisioningMaintenanceAction.NONE) {
                IdentityProvisioningPlan.NO_AUTOMATIC_ACTION
            } else {
                IdentityProvisioningPlan.BLOCKED_PRECONDITIONS
            }
        }

        return when (action) {
            ProvisioningMaintenanceAction.NONE -> IdentityProvisioningPlan.NO_AUTOMATIC_ACTION

            ProvisioningMaintenanceAction.START -> {
                if (pinState == ProvisioningPinState.MISSING &&
                    databaseState == ProvisioningDatabaseEvidence.MISSING
                ) {
                    IdentityProvisioningPlan.CREATE_PENDING_PIN
                } else {
                    IdentityProvisioningPlan.BLOCKED_EVIDENCE
                }
            }

            ProvisioningMaintenanceAction.RESUME_SAME_ID -> {
                if (pinState == ProvisioningPinState.PENDING &&
                    databaseState == ProvisioningDatabaseEvidence.MISSING
                ) {
                    IdentityProvisioningPlan.RESUME_BOOTSTRAP_WITH_SAME_PENDING_ID
                } else {
                    IdentityProvisioningPlan.BLOCKED_EVIDENCE
                }
            }

            ProvisioningMaintenanceAction.FINALIZE_PENDING -> {
                if (pinState == ProvisioningPinState.PENDING &&
                    databaseState == ProvisioningDatabaseEvidence.IDENTITY_MATCHES_PIN &&
                    readOnlyVerified
                ) {
                    IdentityProvisioningPlan.PROMOTE_EXACT_PENDING_PIN_TO_ACTIVE
                } else if (pinState == ProvisioningPinState.PENDING &&
                    databaseState == ProvisioningDatabaseEvidence.IDENTITY_MATCHES_PIN
                ) {
                    IdentityProvisioningPlan.REQUIRE_READ_ONLY_RECONCILIATION
                } else {
                    IdentityProvisioningPlan.BLOCKED_EVIDENCE
                }
            }
        }
    }
}
