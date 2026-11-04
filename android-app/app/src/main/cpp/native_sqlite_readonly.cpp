#include <jni.h>
#include <sqlite3.h>
#include <cerrno>
#include <cstdint>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <unistd.h>

namespace {
enum Status : jlong {
    VERIFIED=0, INVALID_PATH=1, MISSING=2, UNREADABLE=3,
    WAL_SIDECARS_UNAVAILABLE=4, OPEN_FAILED=5,
    READ_ONLY_ENFORCEMENT_FAILED=6, READ_TRANSACTION_FAILED=7,
    SNAPSHOT_ANCHOR_FAILED=8, INCOMPLETE_EVIDENCE=9,
    CLOSE_FAILED=10, ALREADY_CLOSED=11, ENGINE_VERSION_UNSUPPORTED=12
};
struct Connection { explicit Connection(sqlite3* value): db(value) {} sqlite3* db; };
std::mutex registry_mutex;
std::unordered_map<jlong,std::shared_ptr<Connection>> connections;
jlong next_handle=1;

bool readable_file(const std::string& path) {
    return access(path.c_str(),F_OK)==0 && access(path.c_str(),R_OK)==0;
}
jlongArray open_result(JNIEnv* env, Status status, jlong handle) {
    jlong values[2]={static_cast<jlong>(status),handle};
    jlongArray result=env->NewLongArray(2);
    if(result!=nullptr) env->SetLongArrayRegion(result,0,2,values);
    return result;
}
Status pin_deferred_snapshot(sqlite3* db) {
    if(sqlite3_libversion_number()<3037000) return ENGINE_VERSION_UNSUPPORTED;
    if(sqlite3_db_readonly(db,"main")!=1) return READ_ONLY_ENFORCEMENT_FAILED;

    sqlite3_stmt* journal_stmt=nullptr;
    const char* journal_sql="SELECT journal_mode FROM pragma_journal_mode";
    if(sqlite3_prepare_v2(db,journal_sql,-1,&journal_stmt,nullptr)!=SQLITE_OK ||
       journal_stmt==nullptr || sqlite3_stmt_readonly(journal_stmt)!=1) {
        if(journal_stmt!=nullptr) sqlite3_finalize(journal_stmt);
        return SNAPSHOT_ANCHOR_FAILED;
    }
    const int journal_step=sqlite3_step(journal_stmt);
    std::string journal_mode;
    if(journal_step==SQLITE_ROW) {
        const unsigned char* value=sqlite3_column_text(journal_stmt,0);
        if(value!=nullptr) journal_mode.assign(reinterpret_cast<const char*>(value));
    }
    sqlite3_finalize(journal_stmt);
    if(journal_step!=SQLITE_ROW || journal_mode.empty()) return SNAPSHOT_ANCHOR_FAILED;

    if(journal_mode=="wal" || journal_mode=="WAL") {
        const char* db_path=sqlite3_db_filename(db,"main");
        if(db_path==nullptr) return WAL_SIDECARS_UNAVAILABLE;
        const std::string base(db_path);
        if(!readable_file(base+"-wal") || !readable_file(base+"-shm"))
            return WAL_SIDECARS_UNAVAILABLE;
    }
    if(sqlite3_exec(db,"BEGIN DEFERRED",nullptr,nullptr,nullptr)!=SQLITE_OK)
        return READ_TRANSACTION_FAILED;

    sqlite3_stmt* anchor=nullptr;
    const char* anchor_sql="SELECT count(*) FROM sqlite_schema";
    if(sqlite3_prepare_v2(db,anchor_sql,-1,&anchor,nullptr)!=SQLITE_OK ||
       anchor==nullptr || sqlite3_stmt_readonly(anchor)!=1) {
        if(anchor!=nullptr) sqlite3_finalize(anchor);
        sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);
        return SNAPSHOT_ANCHOR_FAILED;
    }
    const int anchor_step=sqlite3_step(anchor);
    sqlite3_finalize(anchor);
    if(anchor_step!=SQLITE_ROW) {
        sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);
        return SNAPSHOT_ANCHOR_FAILED;
    }
    return VERIFIED;
}
} // namespace

extern "C" JNIEXPORT jlongArray JNICALL
Java_com_kenznguyen_btclivealerts_NativeSqliteReadOnlyJni_nativeOpenPinnedSnapshot(
    JNIEnv* env,jobject,jstring java_path) {
    if(java_path==nullptr) return open_result(env,INVALID_PATH,0);
    const char* chars=env->GetStringUTFChars(java_path,nullptr);
    if(chars==nullptr) return open_result(env,INCOMPLETE_EVIDENCE,0);
    const std::string path(chars);
    env->ReleaseStringUTFChars(java_path,chars);
    if(path.empty() || path[0]!='/' || path.find('\0')!=std::string::npos)
        return open_result(env,INVALID_PATH,0);
    if(access(path.c_str(),F_OK)!=0)
        return open_result(env,errno==ENOENT?MISSING:UNREADABLE,0);
    if(access(path.c_str(),R_OK)!=0) return open_result(env,UNREADABLE,0);

    sqlite3* db=nullptr;
    const int rc=sqlite3_open_v2(path.c_str(),&db,SQLITE_OPEN_READONLY|SQLITE_OPEN_FULLMUTEX,nullptr);
    if(rc!=SQLITE_OK || db==nullptr) {
        if(db!=nullptr) sqlite3_close_v2(db);
        return open_result(env,OPEN_FAILED,0);
    }
    const Status status=pin_deferred_snapshot(db);
    if(status!=VERIFIED) {
        sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);
        sqlite3_close_v2(db);
        return open_result(env,status,0);
    }
    auto connection=std::make_shared<Connection>(db);
    jlong handle=0;
    {
        std::lock_guard<std::mutex> guard(registry_mutex);
        handle=next_handle++;
        if(handle<=0) {
            sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);
            sqlite3_close_v2(db);
            return open_result(env,INCOMPLETE_EVIDENCE,0);
        }
        connections.emplace(handle,std::move(connection));
    }
    return open_result(env,VERIFIED,handle);
}

extern "C" JNIEXPORT jint JNICALL
Java_com_kenznguyen_btclivealerts_NativeSqliteReadOnlyJni_nativeCloseSnapshot(
    JNIEnv*,jobject,jlong handle) {
    std::lock_guard<std::mutex> guard(registry_mutex);
    const auto found=connections.find(handle);
    if(found==connections.end()) return ALREADY_CLOSED;
    sqlite3* db=found->second->db;
    const int rollback_rc=sqlite3_exec(db,"ROLLBACK",nullptr,nullptr,nullptr);
    if(rollback_rc!=SQLITE_OK && rollback_rc!=SQLITE_ERROR) return CLOSE_FAILED;
    const int close_rc=sqlite3_close_v2(db);
    if(close_rc!=SQLITE_OK) return CLOSE_FAILED;
    connections.erase(found);
    return VERIFIED;
}
