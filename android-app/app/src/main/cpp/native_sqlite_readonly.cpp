#include <jni.h>
#include <sqlite3.h>
#include <cerrno>
#include <cstdint>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <unistd.h>
#ifndef CANONICAL_SQLITE_EXPECTED_SOURCE_ID
#error "Exact SQLite source ID must be pinned by CMake"
#endif
namespace {
enum Status:jlong{VERIFIED=0,INVALID_PATH=1,MISSING=2,UNREADABLE=3,WAL_SIDECARS_UNAVAILABLE=4,OPEN_FAILED=5,READ_ONLY_ENFORCEMENT_FAILED=6,READ_TRANSACTION_FAILED=7,SNAPSHOT_ANCHOR_FAILED=8,INCOMPLETE_EVIDENCE=9,CLOSE_FAILED=10,ALREADY_CLOSED=11,ENGINE_VERSION_UNSUPPORTED=12,ENGINE_SOURCE_ID_MISMATCH=13};
struct Connection{explicit Connection(sqlite3* p):db(p){}sqlite3* db;};
std::mutex registry_mutex;std::unordered_map<jlong,std::shared_ptr<Connection>> connections;jlong next_handle=1;
bool readable_file(const std::string& p){return access(p.c_str(),F_OK)==0&&access(p.c_str(),R_OK)==0;}
jlongArray open_result(JNIEnv* e,Status s,jlong h){jlong v[2]={static_cast<jlong>(s),h};jlongArray a=e->NewLongArray(2);if(a!=nullptr)e->SetLongArrayRegion(a,0,2,v);return a;}
Status pin_deferred_snapshot(sqlite3* db){
 if(sqlite3_libversion_number()<3037000)return ENGINE_VERSION_UNSUPPORTED;
 const char* sid=sqlite3_sourceid();if(sid==nullptr||std::string(sid)!=CANONICAL_SQLITE_EXPECTED_SOURCE_ID)return ENGINE_SOURCE_ID_MISMATCH;
 if(sqlite3_db_readonly(db,"main")!=1)return READ_ONLY_ENFORCEMENT_FAILED;
 sqlite3_stmt* js=nullptr;const char* jq="SELECT journal_mode FROM pragma_journal_mode";
 if(sqlite3_prepare_v2(db,jq,-1,&js,nullptr)!=SQLITE_OK||js==nullptr||sqlite3_stmt_readonly(js)!=1){if(js!=nullptr)sqlite3_finalize(js);return SNAPSHOT_ANCHOR_FAILED;}
 int step=sqlite3_step(js);std::string mode;if(step==SQLITE_ROW){const unsigned char* v=sqlite3_column_text(js,0);if(v!=nullptr)mode.assign(reinterpret_cast<const char*>(v));}sqlite3_finalize(js);
 if(step!=SQLITE_ROW||mode.empty())return SNAPSHOT_ANCHOR_FAILED;
 if(mode=="wal"||mode=="WAL"){const char* p=sqlite3_db_filename(db,"main");if(p==nullptr)return WAL_SIDECARS_UNAVAILABLE;const std::string base(p);if(!readable_file(base+"-wal")||!readable_file(base+"-shm"))return WAL_SIDECARS_UNAVAILABLE;}
 if(sqlite3_exec(db,"BEGIN DEFERRED",nullptr,nullptr,nullptr)!=SQLITE_OK)return READ_TRANSACTION_FAILED;
 sqlite3_stmt* anchor=nullptr;const char* aq="SELECT count(*) FROM sqlite_schema";
 if(sqlite3_prepare_v2(db,aq,-1,&anchor,nullptr)!=SQLITE_OK||anchor==nullptr||sqlite3_stmt_readonly(anchor)!=1){if(anchor!=nullptr)sqlite3_finalize(anchor);sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);return SNAPSHOT_ANCHOR_FAILED;}
 step=sqlite3_step(anchor);sqlite3_finalize(anchor);if(step!=SQLITE_ROW){sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);return SNAPSHOT_ANCHOR_FAILED;}return VERIFIED;
}
}
extern "C" JNIEXPORT jlongArray JNICALL Java_com_kenznguyen_btclivealerts_NativeSqliteReadOnlyJni_nativeOpenPinnedSnapshot(JNIEnv* e,jobject,jstring jp){
 if(jp==nullptr)return open_result(e,INVALID_PATH,0);const char* c=e->GetStringUTFChars(jp,nullptr);if(c==nullptr)return open_result(e,INCOMPLETE_EVIDENCE,0);std::string p(c);e->ReleaseStringUTFChars(jp,c);
 if(p.empty()||p[0]!='/'||p.find('\0')!=std::string::npos)return open_result(e,INVALID_PATH,0);
 if(access(p.c_str(),F_OK)!=0)return open_result(e,errno==ENOENT?MISSING:UNREADABLE,0);if(access(p.c_str(),R_OK)!=0)return open_result(e,UNREADABLE,0);
 sqlite3* db=nullptr;int rc=sqlite3_open_v2(p.c_str(),&db,SQLITE_OPEN_READONLY|SQLITE_OPEN_FULLMUTEX,nullptr);if(rc!=SQLITE_OK||db==nullptr){if(db!=nullptr)sqlite3_close_v2(db);return open_result(e,OPEN_FAILED,0);}
 Status s=pin_deferred_snapshot(db);if(s!=VERIFIED){sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);sqlite3_close_v2(db);return open_result(e,s,0);}
 auto conn=std::make_shared<Connection>(db);jlong h=0;{std::lock_guard<std::mutex> g(registry_mutex);h=next_handle++;if(h<=0){sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);sqlite3_close_v2(db);return open_result(e,INCOMPLETE_EVIDENCE,0);}connections.emplace(h,std::move(conn));}return open_result(e,VERIFIED,h);
}
extern "C" JNIEXPORT jint JNICALL Java_com_kenznguyen_btclivealerts_NativeSqliteReadOnlyJni_nativeCloseSnapshot(JNIEnv*,jobject,jlong h){
 std::lock_guard<std::mutex> g(registry_mutex);auto it=connections.find(h);if(it==connections.end())return ALREADY_CLOSED;sqlite3* db=it->second->db;
 int rr=sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);if(rr!=SQLITE_OK&&rr!=SQLITE_ERROR)return CLOSE_FAILED;int cr=sqlite3_close_v2(db);if(cr!=SQLITE_OK)return CLOSE_FAILED;connections.erase(it);return VERIFIED;
}
