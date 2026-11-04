package com.kenznguyen.btclivealerts

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class NativeSqliteReadOnlySessionTest {
    private class FakeBridge(
        var openReply: NativeSqliteOpenReply = NativeSqliteOpenReply(
            NativeSqliteStatus.VERIFIED,
            41L,
        ),
        var closeStatus: NativeSqliteStatus = NativeSqliteStatus.VERIFIED,
    ) : NativeSqliteReadOnlyBridge {
        var openCalls = 0
        var closeCalls = 0
        var openedPath: String? = null
        var closedHandle: Long? = null

        override fun openPinnedSnapshot(path: String): NativeSqliteOpenReply {
            openCalls += 1
            openedPath = path
            return openReply
        }

        override fun closeSnapshot(handle: Long): NativeSqliteStatus {
            closeCalls += 1
            closedHandle = handle
            return closeStatus
        }
    }

    @Test
    fun opensOnlyAnAbsoluteExistingPathThroughThePinnedSnapshotBridge() {
        val bridge = FakeBridge()

        val result = NativeSqliteReadOnlySession.open("/data/user/0/app/files/canonical/t0.sqlite", bridge)

        assertTrue(result is NativeSqliteSessionOpenResult.Opened)
        assertEquals(1, bridge.openCalls)
        assertEquals("/data/user/0/app/files/canonical/t0.sqlite", bridge.openedPath)
    }

    @Test
    fun rejectsBlankAndRelativePathsBeforeCallingNativeCode() {
        val bridge = FakeBridge()

        assertEquals(
            NativeSqliteStatus.INVALID_PATH,
            (NativeSqliteReadOnlySession.open(" ", bridge) as NativeSqliteSessionOpenResult.Rejected).status,
        )
        assertEquals(
            NativeSqliteStatus.INVALID_PATH,
            (NativeSqliteReadOnlySession.open("files/t0.sqlite", bridge) as NativeSqliteSessionOpenResult.Rejected).status,
        )
        assertEquals(0, bridge.openCalls)
    }

    @Test
    fun propagatesNativeOpenFailuresAndNeverCreatesAFallbackSession() {
        val bridge = FakeBridge(
            openReply = NativeSqliteOpenReply(NativeSqliteStatus.WAL_SIDECARS_UNAVAILABLE, 0L),
        )

        val result = NativeSqliteReadOnlySession.open("/existing/t0.sqlite", bridge)

        assertEquals(
            NativeSqliteStatus.WAL_SIDECARS_UNAVAILABLE,
            (result as NativeSqliteSessionOpenResult.Rejected).status,
        )
        assertEquals(0, bridge.closeCalls)
    }

    @Test
    fun rejectsSuccessWithoutAValidNativeHandle() {
        val bridge = FakeBridge(
            openReply = NativeSqliteOpenReply(NativeSqliteStatus.VERIFIED, 0L),
        )

        val result = NativeSqliteReadOnlySession.open("/existing/t0.sqlite", bridge)

        assertEquals(
            NativeSqliteStatus.INCOMPLETE_EVIDENCE,
            (result as NativeSqliteSessionOpenResult.Rejected).status,
        )
    }

    @Test
    fun closeIsIdempotentAndClosesOnlyTheIssuedHandle() {
        val bridge = FakeBridge()
        val opened = NativeSqliteReadOnlySession.open("/existing/t0.sqlite", bridge)
            as NativeSqliteSessionOpenResult.Opened

        assertEquals(NativeSqliteStatus.VERIFIED, opened.session.closeAndGetStatus())
        assertEquals(NativeSqliteStatus.ALREADY_CLOSED, opened.session.closeAndGetStatus())
        assertEquals(1, bridge.closeCalls)
        assertEquals(41L, bridge.closedHandle)
        assertTrue(opened.session.isClosed)
    }

    @Test
    fun nativeCloseFailureIsReportedAndSessionStillBecomesClosed() {
        val bridge = FakeBridge(closeStatus = NativeSqliteStatus.CLOSE_FAILED)
        val opened = NativeSqliteReadOnlySession.open("/existing/t0.sqlite", bridge)
            as NativeSqliteSessionOpenResult.Opened

        assertEquals(NativeSqliteStatus.CLOSE_FAILED, opened.session.closeAndGetStatus())
        assertTrue(opened.session.isClosed)
        assertFalse(opened.session.isOpen)
        assertEquals(1, bridge.closeCalls)
    }
}
