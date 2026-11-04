package com.kenznguyen.btclivealerts
import org.junit.Assert.*
import org.junit.Test
class NativeSqliteReadOnlySessionTest {
 private class FakeBridge(var openReply:NativeSqliteOpenReply=NativeSqliteOpenReply(NativeSqliteStatus.VERIFIED,41L),var closeStatus:NativeSqliteStatus=NativeSqliteStatus.VERIFIED):NativeSqliteReadOnlyBridge {
  var openCalls=0;var closeCalls=0;var openedPath:String?=null;var closedHandle:Long?=null
  override fun openPinnedSnapshot(path:String):NativeSqliteOpenReply{openCalls++;openedPath=path;return openReply}
  override fun closeSnapshot(handle:Long):NativeSqliteStatus{closeCalls++;closedHandle=handle;return closeStatus}
 }
 @Test fun opensAbsolutePathThroughPinnedSnapshotBridge(){val b=FakeBridge();val r=NativeSqliteReadOnlySession.open("/data/t0.sqlite",b);assertTrue(r is NativeSqliteSessionOpenResult.Opened);assertEquals(1,b.openCalls);assertEquals("/data/t0.sqlite",b.openedPath)}
 @Test fun rejectsBlankRelativeAndNulPathsBeforeNativeCode(){val b=FakeBridge();listOf(" ","files/t0.sqlite","/data/t0\u0000.sqlite").forEach{p->assertEquals(NativeSqliteStatus.INVALID_PATH,(NativeSqliteReadOnlySession.open(p,b) as NativeSqliteSessionOpenResult.Rejected).status)};assertEquals(0,b.openCalls)}
 @Test fun propagatesNativeOpenFailureWithoutFallback(){val b=FakeBridge(NativeSqliteOpenReply(NativeSqliteStatus.WAL_SIDECARS_UNAVAILABLE,0L));val r=NativeSqliteReadOnlySession.open("/existing/t0.sqlite",b);assertEquals(NativeSqliteStatus.WAL_SIDECARS_UNAVAILABLE,(r as NativeSqliteSessionOpenResult.Rejected).status);assertEquals(0,b.closeCalls)}
 @Test fun rejectsSuccessWithoutNativeHandle(){val b=FakeBridge(NativeSqliteOpenReply(NativeSqliteStatus.VERIFIED,0L));val r=NativeSqliteReadOnlySession.open("/existing/t0.sqlite",b);assertEquals(NativeSqliteStatus.INCOMPLETE_EVIDENCE,(r as NativeSqliteSessionOpenResult.Rejected).status)}
 @Test fun closeIsIdempotentAndClosesIssuedHandle(){val b=FakeBridge();val s=(NativeSqliteReadOnlySession.open("/existing/t0.sqlite",b) as NativeSqliteSessionOpenResult.Opened).session;assertEquals(NativeSqliteStatus.VERIFIED,s.closeAndGetStatus());assertEquals(NativeSqliteStatus.ALREADY_CLOSED,s.closeAndGetStatus());assertEquals(1,b.closeCalls);assertEquals(41L,b.closedHandle);assertTrue(s.isClosed)}
 @Test fun failedCloseRemainsRetryableUntilNativeCloseSucceeds(){val b=FakeBridge(closeStatus=NativeSqliteStatus.CLOSE_FAILED);val s=(NativeSqliteReadOnlySession.open("/existing/t0.sqlite",b) as NativeSqliteSessionOpenResult.Opened).session;assertEquals(NativeSqliteStatus.CLOSE_FAILED,s.closeAndGetStatus());assertFalse(s.isClosed);b.closeStatus=NativeSqliteStatus.VERIFIED;assertEquals(NativeSqliteStatus.VERIFIED,s.closeAndGetStatus());assertTrue(s.isClosed);assertEquals(2,b.closeCalls)}
 @Test fun unknownNativeCodesFailClosed(){assertEquals(NativeSqliteStatus.INCOMPLETE_EVIDENCE,NativeSqliteStatus.fromNativeCode(Int.MAX_VALUE))}
}
