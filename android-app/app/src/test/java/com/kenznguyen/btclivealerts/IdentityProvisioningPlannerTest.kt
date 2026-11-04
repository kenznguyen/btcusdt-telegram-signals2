package com.kenznguyen.btclivealerts

import org.junit.Assert.assertEquals
import org.junit.Test

class IdentityProvisioningPlannerTest {
    private val allPreconditions = IdentityProvisioningPreconditions(
        explicitMaintenanceAuthorization = true,
        databasePathConfirmedAbsentOrApprovedEmpty = true,
        noActiveWriterOrLease = true,
        noAcceptedIdentity = true,
        noLegacyData = true,
    )

    @Test
    fun initialProvisioningCreatesOnlyPendingPinPlan() {
        assertEquals(
            IdentityProvisioningPlan.CREATE_PENDING_PIN,
            IdentityProvisioningPlanner.plan(
                pinState = ProvisioningPinState.MISSING,
                databaseState = ProvisioningDatabaseEvidence.MISSING,
                readOnlyVerified = false,
                preconditions = allPreconditions,
                action = ProvisioningMaintenanceAction.START,
            ),
        )
    }

    @Test
    fun startWithoutExplicitMaintenanceAuthorizationIsBlocked() {
        assertEquals(
            IdentityProvisioningPlan.BLOCKED_PRECONDITIONS,
            IdentityProvisioningPlanner.plan(
                ProvisioningPinState.MISSING,
                ProvisioningDatabaseEvidence.MISSING,
                false,
                allPreconditions.copy(explicitMaintenanceAuthorization = false),
                ProvisioningMaintenanceAction.START,
            ),
        )
    }

    @Test
    fun startWithLegacyDataIsBlocked() {
        assertEquals(
            IdentityProvisioningPlan.BLOCKED_PRECONDITIONS,
            IdentityProvisioningPlanner.plan(
                ProvisioningPinState.MISSING,
                ProvisioningDatabaseEvidence.LEGACY,
                false,
                allPreconditions,
                ProvisioningMaintenanceAction.START,
            ),
        )
    }

    @Test
    fun pendingPinAndMissingDatabaseNeedsExplicitSameIdResume() {
        assertEquals(
            IdentityProvisioningPlan.RESUME_BOOTSTRAP_WITH_SAME_PENDING_ID,
            IdentityProvisioningPlanner.plan(
                ProvisioningPinState.PENDING,
                ProvisioningDatabaseEvidence.MISSING,
                false,
                allPreconditions,
                ProvisioningMaintenanceAction.RESUME_SAME_ID,
            ),
        )
    }

    @Test
    fun pendingPinAndMissingDatabaseNeverResumesAutomatically() {
        assertEquals(
            IdentityProvisioningPlan.NO_AUTOMATIC_ACTION,
            IdentityProvisioningPlanner.plan(
                ProvisioningPinState.PENDING,
                ProvisioningDatabaseEvidence.MISSING,
                false,
                allPreconditions,
                ProvisioningMaintenanceAction.NONE,
            ),
        )
    }

    @Test
    fun uncertainCommitRequiresReadOnlyReconciliationBeforeAnyRetry() {
        assertEquals(
            IdentityProvisioningPlan.REQUIRE_READ_ONLY_RECONCILIATION,
            IdentityProvisioningPlanner.plan(
                ProvisioningPinState.PENDING,
                ProvisioningDatabaseEvidence.READ_UNCERTAIN,
                false,
                allPreconditions,
                ProvisioningMaintenanceAction.RESUME_SAME_ID,
            ),
        )
    }

    @Test
    fun matchingVerifiedDatabaseRequiresExplicitFinalizeBeforePinPromotion() {
        assertEquals(
            IdentityProvisioningPlan.PROMOTE_EXACT_PENDING_PIN_TO_ACTIVE,
            IdentityProvisioningPlanner.plan(
                ProvisioningPinState.PENDING,
                ProvisioningDatabaseEvidence.IDENTITY_MATCHES_PIN,
                true,
                allPreconditions,
                ProvisioningMaintenanceAction.FINALIZE_PENDING,
            ),
        )
    }

    @Test
    fun matchingVerifiedDatabaseDoesNotAutoPromotePendingPin() {
        assertEquals(
            IdentityProvisioningPlan.NO_AUTOMATIC_ACTION,
            IdentityProvisioningPlanner.plan(
                ProvisioningPinState.PENDING,
                ProvisioningDatabaseEvidence.IDENTITY_MATCHES_PIN,
                true,
                allPreconditions,
                ProvisioningMaintenanceAction.NONE,
            ),
        )
    }

    @Test
    fun mismatchedDatabaseIdentityIsAlwaysBlocked() {
        assertEquals(
            IdentityProvisioningPlan.BLOCKED_EVIDENCE,
            IdentityProvisioningPlanner.plan(
                ProvisioningPinState.PENDING,
                ProvisioningDatabaseEvidence.IDENTITY_MISMATCH,
                true,
                allPreconditions,
                ProvisioningMaintenanceAction.FINALIZE_PENDING,
            ),
        )
    }

    @Test
    fun unsupportedOrUnreadablePinIsNeverReplaced() {
        assertEquals(
            IdentityProvisioningPlan.BLOCKED_EVIDENCE,
            IdentityProvisioningPlanner.plan(
                ProvisioningPinState.UNREADABLE,
                ProvisioningDatabaseEvidence.MISSING,
                false,
                allPreconditions,
                ProvisioningMaintenanceAction.START,
            ),
        )
        assertEquals(
            IdentityProvisioningPlan.BLOCKED_EVIDENCE,
            IdentityProvisioningPlanner.plan(
                ProvisioningPinState.UNSUPPORTED,
                ProvisioningDatabaseEvidence.MISSING,
                false,
                allPreconditions,
                ProvisioningMaintenanceAction.START,
            ),
        )
    }

    @Test
    fun activePinRequiresMatchingVerifiedDatabaseForIdentityMatch() {
        assertEquals(
            IdentityProvisioningPlan.IDENTITY_ACTIVE,
            IdentityProvisioningPlanner.plan(
                ProvisioningPinState.ACTIVE,
                ProvisioningDatabaseEvidence.IDENTITY_MATCHES_PIN,
                true,
                allPreconditions,
                ProvisioningMaintenanceAction.NONE,
            ),
        )
        assertEquals(
            IdentityProvisioningPlan.BLOCKED_EVIDENCE,
            IdentityProvisioningPlanner.plan(
                ProvisioningPinState.ACTIVE,
                ProvisioningDatabaseEvidence.IDENTITY_MATCHES_PIN,
                false,
                allPreconditions,
                ProvisioningMaintenanceAction.NONE,
            ),
        )
    }
}
