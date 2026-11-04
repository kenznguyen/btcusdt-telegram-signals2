package com.kenznguyen.btclivealerts
enum class NativeSqliteStatus(val nativeCode:Int) {
 VERIFIED(0), INVALID_PATH(1), MISSING(2), UNREADABLE(3), WAL_SIDECARS_UNAVAILABLE(4),
 OPEN_FAILED(5), READ_ONLY_ENFORCEMENT_FAILED(6), READ_TRANSACTION_FAILED(7),
 SNAPSHOT_ANCHOR_FAILED(8), INCOMPLETE_EVIDENCE(9), CLOSE_FAILED(10), ALREADY_CLOSED(11),
 ENGINE_VERSION_UNSUPPORTED(12), ENGINE_SOURCE_ID_MISMATCH(13);
 companion object { fun fromNativeCode(code:Int)=entries.firstOrNull{it.nativeCode==code}?:INCOMPLETE_EVIDENCE }
}
data class NativeSqliteOpenReply(val status:NativeSqliteStatus,val handle:Long)
internal interface NativeSqliteReadOnlyBridge {
 fun openPinnedSnapshot(path:String):NativeSqliteOpenReply
 fun closeSnapshot(handle:Long):NativeSqliteStatus
}
internal sealed interface NativeSqliteSessionOpenResult {
 data class Opened(val session:NativeSqliteReadOnlySession):NativeSqliteSessionOpenResult
 data class Rejected(val status:NativeSqliteStatus):NativeSqliteSessionOpenResult
}
internal class NativeSqliteReadOnlySession private constructor(private val handle:Long,private val bridge:NativeSqliteReadOnlyBridge):AutoCloseable {
 @Volatile var isClosed=false
  private set
 val isOpen:Boolean get()=!isClosed
 @Synchronized fun closeAndGetStatus():NativeSqliteStatus {
  if(isClosed)return NativeSqliteStatus.ALREADY_CLOSED
  val status=try{bridge.closeSnapshot(handle)}catch(_:Exception){NativeSqliteStatus.CLOSE_FAILED}
  if(status==NativeSqliteStatus.VERIFIED||status==NativeSqliteStatus.ALREADY_CLOSED)isClosed=true
  return status
 }
 override fun close(){closeAndGetStatus()}
 companion object {
  fun open(path:String,bridge:NativeSqliteReadOnlyBridge):NativeSqliteSessionOpenResult {
   if(path.isBlank()||!path.startsWith("/")||path.contains('\u0000'))return NativeSqliteSessionOpenResult.Rejected(NativeSqliteStatus.INVALID_PATH)
   val reply=try{bridge.openPinnedSnapshot(path)}catch(_:Exception){return NativeSqliteSessionOpenResult.Rejected(NativeSqliteStatus.OPEN_FAILED)}
   if(reply.status!=NativeSqliteStatus.VERIFIED)return NativeSqliteSessionOpenResult.Rejected(reply.status)
   if(reply.handle<=0L)return NativeSqliteSessionOpenResult.Rejected(NativeSqliteStatus.INCOMPLETE_EVIDENCE)
   return NativeSqliteSessionOpenResult.Opened(NativeSqliteReadOnlySession(reply.handle,bridge))
  }
 }
}
/** JNI loads lazily; JVM tests use a fake bridge. */
internal object NativeSqliteReadOnlyJni {
 private val libraryLoaded:Unit by lazy{System.loadLibrary("canonical_sqlite")}
 fun openPinnedSnapshot(path:String):NativeSqliteOpenReply {
  libraryLoaded
  val result=nativeOpenPinnedSnapshot(path)
  if(result.size!=2)return NativeSqliteOpenReply(NativeSqliteStatus.INCOMPLETE_EVIDENCE,0L)
  return NativeSqliteOpenReply(NativeSqliteStatus.fromNativeCode(result[0].toInt()),result[1])
 }
 fun closeSnapshot(handle:Long):NativeSqliteStatus {libraryLoaded;return NativeSqliteStatus.fromNativeCode(nativeCloseSnapshot(handle))}
 private external fun nativeOpenPinnedSnapshot(path:String):LongArray
 private external fun nativeCloseSnapshot(handle:Long):Int
}
internal object JniNativeSqliteReadOnlyBridge:NativeSqliteReadOnlyBridge {
 override fun openPinnedSnapshot(path:String)=NativeSqliteReadOnlyJni.openPinnedSnapshot(path)
 override fun closeSnapshot(handle:Long)=NativeSqliteReadOnlyJni.closeSnapshot(handle)
}
