package com.kenznguyen.btclivealerts

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class CanonicalIdentityPinTest {
    private val role = CanonicalDatabaseRoleId.canonicalT0()
    private val instanceId = CanonicalDatabaseInstanceId.fromPersisted(
        "550e8400-e29b-41d4-a716-446655440000",
    )
    private val otherInstanceId = CanonicalDatabaseInstanceId.fromPersisted(
        "550e8400-e29b-41d4-a716-446655440001",
    )

    @Test
    fun instanceIdentityAcceptsOnlyCanonicalUuidV4() {
        assertEquals(
            instanceId,
            CanonicalDatabaseInstanceId.tryFromPersisted("550e8400-e29b-41d4-a716-446655440000"),
        )
        assertEquals(null, CanonicalDatabaseInstanceId.tryFromPersisted("opaque-instance-001"))
        assertEquals(null, CanonicalDatabaseInstanceId.tryFromPersisted("550E8400-E29B-41D4-A716-446655440000"))
        assertEquals(null, CanonicalDatabaseInstanceId.tryFromPersisted("550e8400-e29b-11d4-a716-446655440000"))
        assertEquals(null, CanonicalDatabaseInstanceId.tryFromPersisted("550e8400-e29b-41d4-7716-446655440000"))
    }

    @Test
    fun pinCodecUsesCanonicalVersionedRepresentationAndRoundTrips() {
        val pin = CanonicalDatabaseIdentityPin(role, instanceId, IdentityPinLifecycleState.PENDING)
        val encoded = CanonicalIdentityPinCodec.encode(pin)

        assertEquals(
            "format_version=1\nrole_id=t0-canonical-sqlite-v1\n" +
                "instance_id=550e8400-e29b-41d4-a716-446655440000\nstate=PENDING\n",
            encoded,
        )
        val parsed = CanonicalIdentityPinCodec.parse(encoded)
        assertTrue(parsed is IdentityPinParseResult.Valid)
        assertEquals(pin, (parsed as IdentityPinParseResult.Valid).pin)
    }

    @Test
    fun pinCodecDistinguishesMissingMalformedAndUnsupportedVersion() {
        assertEquals(IdentityPinParseResult.Missing, CanonicalIdentityPinCodec.parse(null))
        assertEquals(IdentityPinParseResult.Malformed, CanonicalIdentityPinCodec.parse(""))
        assertEquals(
            IdentityPinParseResult.UnsupportedVersion(2),
            CanonicalIdentityPinCodec.parse(
                "format_version=2\nrole_id=t0-canonical-sqlite-v1\n" +
                    "instance_id=550e8400-e29b-41d4-a716-446655440000\nstate=ACTIVE\n",
            ),
        )
    }

    @Test
    fun pinCodecRejectsDuplicateUnknownNonCanonicalAndExtraFields() {
        val valid = CanonicalIdentityPinCodec.encode(
            CanonicalDatabaseIdentityPin(role, instanceId, IdentityPinLifecycleState.ACTIVE),
        )
        assertEquals(IdentityPinParseResult.Malformed, CanonicalIdentityPinCodec.parse(valid + "state=PENDING\n"))
        assertEquals(
            IdentityPinParseResult.Malformed,
            CanonicalIdentityPinCodec.parse(valid.replace("state=ACTIVE", "unknown=x\nstate=ACTIVE")),
        )
        assertEquals(
            IdentityPinParseResult.Malformed,
            CanonicalIdentityPinCodec.parse(valid.replace("550e8400-e29b-41d4-a716-446655440000", "550E8400-E29B-41D4-A716-446655440000")),
        )
        assertEquals(IdentityPinParseResult.Malformed, CanonicalIdentityPinCodec.parse(valid.dropLast(1)))
    }

    @Test
    fun missingDatabaseAndLegacyDatabaseAlwaysFailClosed() {
        assertEquals(
            CanonicalIdentityStatus.MISSING_DATABASE,
            classify(CanonicalIdentityDatabaseState.MISSING, activePin()),
        )
        assertEquals(
            CanonicalIdentityStatus.LEGACY_UNVERSIONED,
            classify(CanonicalIdentityDatabaseState.LEGACY_UNVERSIONED, activePin()),
        )
    }

    @Test
    fun missingIdentityAndMissingPinNeverCreateOrInferAnIdentity() {
        assertEquals(
            CanonicalIdentityStatus.IDENTITY_UNKNOWN,
            classify(CanonicalIdentityDatabaseState.IDENTITY_MISSING, IdentityPinParseResult.Missing),
        )
        assertEquals(
            CanonicalIdentityStatus.IDENTITY_UNCONFIRMED,
            classify(CanonicalIdentityDatabaseState.IDENTITY_PRESENT, IdentityPinParseResult.Missing),
        )
    }

    @Test
    fun malformedAndUnsupportedPinsFailClosed() {
        assertEquals(
            CanonicalIdentityStatus.PIN_INVALID,
            classify(CanonicalIdentityDatabaseState.IDENTITY_PRESENT, IdentityPinParseResult.Malformed),
        )
        assertEquals(
            CanonicalIdentityStatus.UNSUPPORTED_PIN_VERSION,
            classify(
                CanonicalIdentityDatabaseState.IDENTITY_PRESENT,
                IdentityPinParseResult.UnsupportedVersion(2),
            ),
        )
    }

    @Test
    fun pendingPinRequiresExplicitFinalizationEvenWhenDatabaseMatches() {
        assertEquals(
            CanonicalIdentityStatus.PROVISIONING_FINALIZATION_REQUIRED,
            classify(
                CanonicalIdentityDatabaseState.IDENTITY_PRESENT,
                validPin(IdentityPinLifecycleState.PENDING),
            ),
        )
    }

    @Test
    fun pendingPinWithNoDatabaseIdentityIsInterruptedAndMismatchIsConflict() {
        assertEquals(
            CanonicalIdentityStatus.PROVISIONING_INTERRUPTED,
            classify(
                CanonicalIdentityDatabaseState.IDENTITY_MISSING,
                validPin(IdentityPinLifecycleState.PENDING),
            ),
        )
        assertEquals(
            CanonicalIdentityStatus.PROVISIONING_CONFLICT,
            CanonicalIdentityStateClassifier.classify(
                CanonicalIdentityDatabaseState.IDENTITY_PRESENT,
                role,
                otherInstanceId,
                validPin(IdentityPinLifecycleState.PENDING),
            ),
        )
    }

    @Test
    fun activePinRequiresBothRoleAndInstanceToMatch() {
        assertEquals(
            CanonicalIdentityStatus.IDENTITY_MATCH,
            classify(CanonicalIdentityDatabaseState.IDENTITY_PRESENT, activePin()),
        )
        assertEquals(
            CanonicalIdentityStatus.ROLE_MISMATCH,
            CanonicalIdentityStateClassifier.classify(
                CanonicalIdentityDatabaseState.IDENTITY_PRESENT,
                CanonicalDatabaseRoleId.fromPersisted("other-role"),
                instanceId,
                activePin(),
            ),
        )
        assertEquals(
            CanonicalIdentityStatus.INSTANCE_MISMATCH,
            CanonicalIdentityStateClassifier.classify(
                CanonicalIdentityDatabaseState.IDENTITY_PRESENT,
                role,
                otherInstanceId,
                activePin(),
            ),
        )
    }

    private fun activePin() = validPin(IdentityPinLifecycleState.ACTIVE)

    private fun validPin(state: IdentityPinLifecycleState) =
        IdentityPinParseResult.Valid(CanonicalDatabaseIdentityPin(role, instanceId, state))

    private fun classify(
        databaseState: CanonicalIdentityDatabaseState,
        pin: IdentityPinParseResult,
    ) = CanonicalIdentityStateClassifier.classify(
        databaseState,
        role,
        instanceId,
        pin,
    )
}
