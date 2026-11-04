#include <jni.h>
#include <sqlite3.h>

#include <algorithm>
#include <cerrno>
#include <cctype>
#include <cstdint>
#include <functional>
#include <limits>
#include <mutex>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include <unistd.h>

#ifndef CANONICAL_SQLITE_EXPECTED_SOURCE_ID
#error "Exact SQLite source ID must be pinned by CMake"
#endif

namespace {

enum Status : jlong {
    VERIFIED = 0,
    INVALID_PATH = 1,
    MISSING = 2,
    UNREADABLE = 3,
    WAL_SIDECARS_UNAVAILABLE = 4,
    OPEN_FAILED = 5,
    READ_ONLY_ENFORCEMENT_FAILED = 6,
    READ_TRANSACTION_FAILED = 7,
    SNAPSHOT_ANCHOR_FAILED = 8,
    INCOMPLETE_EVIDENCE = 9,
    CLOSE_FAILED = 10,
    ALREADY_CLOSED = 11,
    ENGINE_VERSION_UNSUPPORTED = 12,
    ENGINE_SOURCE_ID_MISMATCH = 13,
};

enum D5Status : int32_t {
    D5_VERIFIED = 0,
    D5_INVALID_HANDLE = 1,
    D5_QUERY_FAILED = 2,
    D5_UNSUPPORTED_SCHEMA = 3,
    D5_RESULT_SHAPE_MISMATCH = 4,
    D5_INCOMPLETE_EVIDENCE = 5,
    D5_PAYLOAD_TOO_LARGE = 6,
};

constexpr size_t kMaxRows = 100000;
constexpr size_t kMaxStringBytes = 4 * 1024 * 1024;
#ifndef CANONICAL_D5_MAX_PAYLOAD_BYTES
#define CANONICAL_D5_MAX_PAYLOAD_BYTES (32u * 1024u * 1024u)
#endif
constexpr size_t kMaxPayloadBytes = CANONICAL_D5_MAX_PAYLOAD_BYTES;
constexpr int32_t kWireVersion = 1;

std::mutex registry_mutex;
std::unordered_map<jlong, sqlite3*> connections;
jlong next_handle = 1;

bool readable_file(const std::string& path) {
    return access(path.c_str(), F_OK) == 0 && access(path.c_str(), R_OK) == 0;
}

jlongArray open_result(JNIEnv* env, Status status, jlong handle) {
    const jlong values[2] = {static_cast<jlong>(status), handle};
    jlongArray result = env->NewLongArray(2);
    if (result != nullptr) env->SetLongArrayRegion(result, 0, 2, values);
    return result;
}

class WireWriter {
public:
    bool write_int(int32_t value) {
        if (!reserve(4)) return false;
        const uint32_t v = static_cast<uint32_t>(value);
        bytes_.push_back(static_cast<uint8_t>((v >> 24) & 0xff));
        bytes_.push_back(static_cast<uint8_t>((v >> 16) & 0xff));
        bytes_.push_back(static_cast<uint8_t>((v >> 8) & 0xff));
        bytes_.push_back(static_cast<uint8_t>(v & 0xff));
        return true;
    }

    bool write_bool(bool value) { return write_int8(value ? 1 : 0); }

    bool write_string(const std::string& value) {
        if (value.size() > kMaxStringBytes || !write_int(static_cast<int32_t>(value.size()))) return false;
        return append(reinterpret_cast<const uint8_t*>(value.data()), value.size());
    }

    bool write_nullable(const std::optional<std::string>& value) {
        if (!value.has_value()) return write_int(-1);
        return write_string(*value);
    }

    bool write_raw(const std::vector<uint8_t>& value) {
        return append(value.data(), value.size());
    }

    bool patch_int(size_t offset, int32_t value) {
        if (offset + 4 > bytes_.size()) return false;
        const uint32_t v = static_cast<uint32_t>(value);
        bytes_[offset] = static_cast<uint8_t>((v >> 24) & 0xff);
        bytes_[offset + 1] = static_cast<uint8_t>((v >> 16) & 0xff);
        bytes_[offset + 2] = static_cast<uint8_t>((v >> 8) & 0xff);
        bytes_[offset + 3] = static_cast<uint8_t>(v & 0xff);
        return true;
    }

    size_t size() const { return bytes_.size(); }
    const std::vector<uint8_t>& bytes() const { return bytes_; }

private:
    bool write_int8(uint8_t value) {
        if (!reserve(1)) return false;
        bytes_.push_back(value);
        return true;
    }

    bool reserve(size_t amount) const {
        return amount <= kMaxPayloadBytes && bytes_.size() <= kMaxPayloadBytes - amount;
    }

    bool append(const uint8_t* data, size_t length) {
        if (!reserve(length)) return false;
        if (length != 0) bytes_.insert(bytes_.end(), data, data + length);
        return true;
    }

    std::vector<uint8_t> bytes_;
};

bool column_text(sqlite3_stmt* stmt, int column, std::string& out) {
    if (sqlite3_column_type(stmt, column) == SQLITE_NULL) return false;
    const auto* text = sqlite3_column_text(stmt, column);
    const int bytes = sqlite3_column_bytes(stmt, column);
    if (text == nullptr || bytes < 0 || static_cast<size_t>(bytes) > kMaxStringBytes) return false;
    out.assign(reinterpret_cast<const char*>(text), static_cast<size_t>(bytes));
    return true;
}

bool column_nullable_text(sqlite3_stmt* stmt, int column, std::optional<std::string>& out) {
    if (sqlite3_column_type(stmt, column) == SQLITE_NULL) {
        out.reset();
        return true;
    }
    std::string value;
    if (!column_text(stmt, column, value)) return false;
    out = std::move(value);
    return true;
}

bool column_int(sqlite3_stmt* stmt, int column, int32_t& out) {
    if (sqlite3_column_type(stmt, column) != SQLITE_INTEGER) return false;
    const sqlite3_int64 value = sqlite3_column_int64(stmt, column);
    if (value < std::numeric_limits<int32_t>::min() ||
        value > std::numeric_limits<int32_t>::max()) return false;
    out = static_cast<int32_t>(value);
    return true;
}

bool column_bool(sqlite3_stmt* stmt, int column, bool& out) {
    int32_t value = 0;
    if (!column_int(stmt, column, value) || (value != 0 && value != 1)) return false;
    out = value == 1;
    return true;
}

bool is_internal_name(const std::string& name) {
    if (name.size() < 7) return false;
    constexpr char prefix[] = "sqlite_";
    for (size_t i = 0; i < 7; ++i) {
        if (static_cast<char>(std::tolower(static_cast<unsigned char>(name[i]))) != prefix[i]) return false;
    }
    return true;
}

bool supported_catalog_type(const std::string& type) {
    return type == "table" || type == "index" || type == "view" || type == "trigger";
}

bool expected_columns(sqlite3_stmt* stmt, const std::vector<std::string>& expected) {
    if (sqlite3_column_count(stmt) != static_cast<int>(expected.size())) return false;
    for (size_t i = 0; i < expected.size(); ++i) {
        const char* actual = sqlite3_column_name(stmt, static_cast<int>(i));
        if (actual == nullptr || expected[i] != actual) return false;
    }
    return true;
}

bool prepare_fixed(
    sqlite3* db,
    const char* sql,
    const std::vector<std::string>& columns,
    sqlite3_stmt** stmt,
    D5Status& failure) {
    *stmt = nullptr;
    const int rc = sqlite3_prepare_v2(db, sql, -1, stmt, nullptr);
    if (rc != SQLITE_OK || *stmt == nullptr) {
        failure = D5_QUERY_FAILED;
        return false;
    }
    if (sqlite3_stmt_readonly(*stmt) != 1) {
        sqlite3_finalize(*stmt);
        *stmt = nullptr;
        failure = D5_QUERY_FAILED;
        return false;
    }
    if (!expected_columns(*stmt, columns)) {
        sqlite3_finalize(*stmt);
        *stmt = nullptr;
        failure = D5_RESULT_SHAPE_MISMATCH;
        return false;
    }
    return true;
}

using RowConsumer = std::function<bool(sqlite3_stmt*)>;

bool run_fixed(
    sqlite3* db,
    const char* sql,
    const std::vector<std::string>& columns,
    const std::string* bound_name,
    const RowConsumer& consume,
    D5Status& failure,
    size_t& row_count) {
    sqlite3_stmt* stmt = nullptr;
    if (!prepare_fixed(db, sql, columns, &stmt, failure)) return false;
    if (bound_name != nullptr) {
        const int bind_rc = sqlite3_bind_text(stmt, 1, bound_name->c_str(), -1, SQLITE_TRANSIENT);
        if (bind_rc != SQLITE_OK) {
            sqlite3_finalize(stmt);
            failure = D5_QUERY_FAILED;
            return false;
        }
    }
    row_count = 0;
    int rc = SQLITE_OK;
    while ((rc = sqlite3_step(stmt)) == SQLITE_ROW) {
        if (++row_count > kMaxRows || !consume(stmt)) {
            sqlite3_finalize(stmt);
            if (failure == D5_VERIFIED) failure = D5_INCOMPLETE_EVIDENCE;
            return false;
        }
    }
    sqlite3_finalize(stmt);
    if (rc != SQLITE_DONE) {
        failure = D5_QUERY_FAILED;
        return false;
    }
    return true;
}

struct CatalogRow {
    std::string schema;
    std::string type;
    std::string name;
    std::string table_name;
    std::string sql;
};

struct TableRow {
    std::string schema;
    std::string name;
    std::string type;
    int32_t column_count = 0;
    bool without_rowid = false;
    bool strict = false;
};

bool write_section_count(WireWriter& out, size_t& offset) {
    offset = out.size();
    return out.write_int(0);
}

bool increment_section(WireWriter& out, size_t offset, size_t& count) {
    if (++count > kMaxRows) return false;
    return out.patch_int(offset, static_cast<int32_t>(count));
}

D5Status read_d5_snapshot(sqlite3* db, std::vector<uint8_t>& payload) {
    WireWriter out;
    const uint8_t magic[] = {0x44, 0x35, 0x57, 0x54}; // D5WT
    std::vector<uint8_t> magic_vec(magic, magic + sizeof(magic));
    if (!out.write_raw(magic_vec) || !out.write_int(kWireVersion)) return D5_PAYLOAD_TOO_LARGE;

    std::string sqlite_version;
    std::string source_id;
    size_t rows = 0;
    D5Status failure = D5_VERIFIED;
    const char* runtime_sql = "SELECT sqlite_version(), sqlite_source_id()";
    if (!run_fixed(db, runtime_sql, {"sqlite_version()", "sqlite_source_id()"}, nullptr,
        [&](sqlite3_stmt* stmt) {
            if (!column_text(stmt, 0, sqlite_version) ||
                !column_text(stmt, 1, source_id)) return false;
            return true;
        }, failure, rows) || rows != 1) {
        return failure == D5_VERIFIED ? D5_INCOMPLETE_EVIDENCE : failure;
    }
    if (sqlite_version != "3.54.1" || source_id != CANONICAL_SQLITE_EXPECTED_SOURCE_ID) {
        return D5_INCOMPLETE_EVIDENCE;
    }
    if (!out.write_string(sqlite_version) || !out.write_string(source_id)) return D5_PAYLOAD_TOO_LARGE;

    std::vector<TableRow> tables;
    size_t section_offset = 0, section_count = 0;
    if (!write_section_count(out, section_offset)) return D5_PAYLOAD_TOO_LARGE;
    const char* table_list_sql =
        "SELECT * FROM pragma_table_list WHERE schema = 'main' AND lower(substr(name,1,7)) <> 'sqlite_' ORDER BY name";
    if (!run_fixed(db, table_list_sql,
        {"schema", "name", "type", "ncol", "wr", "strict"}, nullptr,
        [&](sqlite3_stmt* stmt) {
            TableRow row;
            if (!column_text(stmt, 0, row.schema) || !column_text(stmt, 1, row.name) ||
                !column_text(stmt, 2, row.type) || !column_int(stmt, 3, row.column_count) ||
                !column_bool(stmt, 4, row.without_rowid) || !column_bool(stmt, 5, row.strict)) {
                failure = D5_INCOMPLETE_EVIDENCE; return false;
            }
            if (row.schema != "main" || (row.type != "table" && row.type != "view")) {
                failure = D5_UNSUPPORTED_SCHEMA; return false;
            }
            if (!out.write_string(row.schema) || !out.write_string(row.name) ||
                !out.write_string(row.type) || !out.write_int(row.column_count) ||
                !out.write_bool(row.without_rowid) || !out.write_bool(row.strict)) {
                failure = D5_PAYLOAD_TOO_LARGE; return false;
            }
            tables.push_back(std::move(row));
            return increment_section(out, section_offset, section_count);
        }, failure, rows)) return failure;

    std::vector<CatalogRow> catalog;
    section_count = 0;
    if (!write_section_count(out, section_offset)) return D5_PAYLOAD_TOO_LARGE;
    const char* catalog_sql =
        "SELECT 'main' AS schema, type, name, tbl_name, sql FROM main.sqlite_schema "
        "WHERE lower(substr(name,1,7)) <> 'sqlite_' ORDER BY type, name, tbl_name, sql";
    if (!run_fixed(db, catalog_sql,
        {"schema", "type", "name", "tbl_name", "sql"}, nullptr,
        [&](sqlite3_stmt* stmt) {
            CatalogRow row;
            if (!column_text(stmt, 0, row.schema) || !column_text(stmt, 1, row.type) ||
                !column_text(stmt, 2, row.name) || !column_text(stmt, 3, row.table_name)) {
                failure = D5_INCOMPLETE_EVIDENCE; return false;
            }
            if (row.schema != "main" || !supported_catalog_type(row.type)) {
                failure = D5_UNSUPPORTED_SCHEMA; return false;
            }
            std::optional<std::string> sql;
            if (!column_nullable_text(stmt, 4, sql) || !sql.has_value() || sql->empty()) {
                failure = D5_UNSUPPORTED_SCHEMA; return false;
            }
            row.sql = *sql;
            if (!out.write_string(row.schema) || !out.write_string(row.type) ||
                !out.write_string(row.name) || !out.write_string(row.table_name) ||
                !out.write_nullable(row.sql)) {
                failure = D5_PAYLOAD_TOO_LARGE; return false;
            }
            catalog.push_back(std::move(row));
            return increment_section(out, section_offset, section_count);
        }, failure, rows)) return failure;

    // The table-list and catalog must describe the same persisted main-schema tables/views.
    std::vector<std::pair<std::string, std::string>> listed;
    std::vector<std::pair<std::string, std::string>> catalogued;
    for (const auto& row : tables) listed.emplace_back(row.type, row.name);
    for (const auto& row : catalog) {
        if (row.type == "table" || row.type == "view") {
            if (row.table_name != row.name) return D5_INCOMPLETE_EVIDENCE;
            catalogued.emplace_back(row.type, row.name);
        }
    }
    std::sort(listed.begin(), listed.end());
    std::sort(catalogued.begin(), catalogued.end());
    if (listed != catalogued) return D5_INCOMPLETE_EVIDENCE;

    // table_xinfo: exact documented seven-column result shape.
    section_count = 0;
    if (!write_section_count(out, section_offset)) return D5_PAYLOAD_TOO_LARGE;
    for (const auto& table : tables) {
        const char* sql = "SELECT * FROM pragma_table_xinfo(?1, 'main')";
        if (!run_fixed(db, sql, {"cid", "name", "type", "notnull", "dflt_value", "pk", "hidden"},
            &table.name, [&](sqlite3_stmt* stmt) {
                int32_t cid = 0, not_null = 0, pk = 0, hidden = 0;
                std::string name;
                std::optional<std::string> type, default_value;
                if (!column_int(stmt, 0, cid) || !column_text(stmt, 1, name) ||
                    !column_nullable_text(stmt, 2, type) || !column_int(stmt, 3, not_null) ||
                    !column_nullable_text(stmt, 4, default_value) || !column_int(stmt, 5, pk) ||
                    !column_int(stmt, 6, hidden)) {
                    failure = D5_INCOMPLETE_EVIDENCE; return false;
                }
                if (!out.write_string(table.schema) || !out.write_string(table.name) ||
                    !out.write_int(cid) || !out.write_string(name) || !out.write_nullable(type) ||
                    !out.write_int(not_null) || !out.write_nullable(default_value) ||
                    !out.write_int(pk) || !out.write_int(hidden)) {
                    failure = D5_PAYLOAD_TOO_LARGE; return false;
                }
                return increment_section(out, section_offset, section_count);
            }, failure, rows)) return failure;
    }

    std::vector<std::pair<std::string, std::string>> indexes;
    // index_list: only tables; omit SQLite-owned sqlite_* internal indexes.
    section_count = 0;
    if (!write_section_count(out, section_offset)) return D5_PAYLOAD_TOO_LARGE;
    for (const auto& table : tables) {
        if (table.type != "table") continue;
        const char* sql = "SELECT * FROM pragma_index_list(?1, 'main')";
        if (!run_fixed(db, sql, {"seq", "name", "unique", "origin", "partial"},
            &table.name, [&](sqlite3_stmt* stmt) {
                int32_t sequence = 0;
                std::string name, origin;
                bool unique = false, partial = false;
                if (!column_int(stmt, 0, sequence) || !column_text(stmt, 1, name) ||
                    !column_bool(stmt, 2, unique) || !column_text(stmt, 3, origin) ||
                    !column_bool(stmt, 4, partial)) {
                    failure = D5_INCOMPLETE_EVIDENCE; return false;
                }
                if (is_internal_name(name)) return true;
                if (!out.write_string(table.schema) || !out.write_string(table.name) ||
                    !out.write_int(sequence) || !out.write_string(name) ||
                    !out.write_bool(unique) || !out.write_string(origin) || !out.write_bool(partial)) {
                    failure = D5_PAYLOAD_TOO_LARGE; return false;
                }
                indexes.emplace_back(table.name, name);
                return increment_section(out, section_offset, section_count);
            }, failure, rows)) return failure;
    }

    // index_xinfo: includes key and auxiliary columns, expression/rowid markers and collation.
    section_count = 0;
    if (!write_section_count(out, section_offset)) return D5_PAYLOAD_TOO_LARGE;
    for (const auto& item : indexes) {
        const char* sql = "SELECT * FROM pragma_index_xinfo(?1, 'main')";
        if (!run_fixed(db, sql, {"seqno", "cid", "name", "desc", "coll", "key"},
            &item.second, [&](sqlite3_stmt* stmt) {
                int32_t sequence = 0, cid = 0;
                std::optional<std::string> name, collation;
                bool descending = false, key = false;
                if (!column_int(stmt, 0, sequence) || !column_int(stmt, 1, cid) ||
                    !column_nullable_text(stmt, 2, name) || !column_bool(stmt, 3, descending) ||
                    !column_nullable_text(stmt, 4, collation) || !column_bool(stmt, 5, key)) {
                    failure = D5_INCOMPLETE_EVIDENCE; return false;
                }
                if (!out.write_string("main") || !out.write_string(item.first) ||
                    !out.write_string(item.second) || !out.write_int(sequence) ||
                    !out.write_int(cid) || !out.write_nullable(name) ||
                    !out.write_bool(descending) || !out.write_nullable(collation) ||
                    !out.write_bool(key)) {
                    failure = D5_PAYLOAD_TOO_LARGE; return false;
                }
                return increment_section(out, section_offset, section_count);
            }, failure, rows)) return failure;
    }

    // foreign_key_list: only tables; preserve every documented field.
    section_count = 0;
    if (!write_section_count(out, section_offset)) return D5_PAYLOAD_TOO_LARGE;
    for (const auto& table : tables) {
        if (table.type != "table") continue;
        const char* sql = "SELECT * FROM pragma_foreign_key_list(?1, 'main')";
        if (!run_fixed(db, sql,
            {"id", "seq", "table", "from", "to", "on_update", "on_delete", "match"},
            &table.name, [&](sqlite3_stmt* stmt) {
                int32_t id = 0, sequence = 0;
                std::string referenced, on_update, on_delete, match;
                std::optional<std::string> from, to;
                if (!column_int(stmt, 0, id) || !column_int(stmt, 1, sequence) ||
                    !column_text(stmt, 2, referenced) || !column_nullable_text(stmt, 3, from) ||
                    !column_nullable_text(stmt, 4, to) || !column_text(stmt, 5, on_update) ||
                    !column_text(stmt, 6, on_delete) || !column_text(stmt, 7, match)) {
                    failure = D5_INCOMPLETE_EVIDENCE; return false;
                }
                if (!out.write_string(table.schema) || !out.write_string(table.name) ||
                    !out.write_int(id) || !out.write_int(sequence) ||
                    !out.write_string(referenced) || !out.write_nullable(from) ||
                    !out.write_nullable(to) || !out.write_string(on_update) ||
                    !out.write_string(on_delete) || !out.write_string(match)) {
                    failure = D5_PAYLOAD_TOO_LARGE; return false;
                }
                return increment_section(out, section_offset, section_count);
            }, failure, rows)) return failure;
    }

    if (out.size() > kMaxPayloadBytes) return D5_PAYLOAD_TOO_LARGE;
    payload = out.bytes();
    return D5_VERIFIED;
}

Status pin_deferred_snapshot(sqlite3* db) {
    if (sqlite3_libversion_number() < 3037000) return ENGINE_VERSION_UNSUPPORTED;
    const char* source_id = sqlite3_sourceid();
    if (source_id == nullptr || std::string(source_id) != CANONICAL_SQLITE_EXPECTED_SOURCE_ID) {
        return ENGINE_SOURCE_ID_MISMATCH;
    }
    if (sqlite3_db_readonly(db, "main") != 1) return READ_ONLY_ENFORCEMENT_FAILED;

    sqlite3_stmt* journal_stmt = nullptr;
    constexpr const char* journal_sql = "SELECT journal_mode FROM pragma_journal_mode";
    if (sqlite3_prepare_v2(db, journal_sql, -1, &journal_stmt, nullptr) != SQLITE_OK ||
        journal_stmt == nullptr || sqlite3_stmt_readonly(journal_stmt) != 1) {
        if (journal_stmt != nullptr) sqlite3_finalize(journal_stmt);
        return SNAPSHOT_ANCHOR_FAILED;
    }
    const int journal_step = sqlite3_step(journal_stmt);
    std::string journal_mode;
    if (journal_step == SQLITE_ROW) {
        const unsigned char* value = sqlite3_column_text(journal_stmt, 0);
        if (value != nullptr) journal_mode.assign(reinterpret_cast<const char*>(value));
    }
    sqlite3_finalize(journal_stmt);
    if (journal_step != SQLITE_ROW || journal_mode != "wal") return WAL_SIDECARS_UNAVAILABLE;

    const char* db_path = sqlite3_db_filename(db, "main");
    if (db_path == nullptr) return WAL_SIDECARS_UNAVAILABLE;
    const std::string base_path(db_path);
    if (!readable_file(base_path + "-wal") || !readable_file(base_path + "-shm")) {
        return WAL_SIDECARS_UNAVAILABLE;
    }
    if (sqlite3_exec(db, "BEGIN DEFERRED", nullptr, nullptr, nullptr) != SQLITE_OK) {
        return READ_TRANSACTION_FAILED;
    }

    sqlite3_stmt* anchor = nullptr;
    constexpr const char* anchor_sql = "SELECT count(*) FROM sqlite_schema";
    if (sqlite3_prepare_v2(db, anchor_sql, -1, &anchor, nullptr) != SQLITE_OK ||
        anchor == nullptr || sqlite3_stmt_readonly(anchor) != 1) {
        if (anchor != nullptr) sqlite3_finalize(anchor);
        sqlite3_exec(db, "ROLLBACK", nullptr, nullptr, nullptr);
        return SNAPSHOT_ANCHOR_FAILED;
    }
    const int anchor_step = sqlite3_step(anchor);
    sqlite3_finalize(anchor);
    if (anchor_step != SQLITE_ROW) {
        sqlite3_exec(db, "ROLLBACK", nullptr, nullptr, nullptr);
        return SNAPSHOT_ANCHOR_FAILED;
    }
    return VERIFIED;
}

}  // namespace

extern "C" JNIEXPORT jlongArray JNICALL
Java_com_kenznguyen_btclivealerts_NativeSqliteReadOnlyJni_nativeOpenPinnedSnapshot(
    JNIEnv* env, jobject /* thiz */, jstring java_path) {
    if (java_path == nullptr) return open_result(env, INVALID_PATH, 0);
    const char* chars = env->GetStringUTFChars(java_path, nullptr);
    if (chars == nullptr) return open_result(env, INCOMPLETE_EVIDENCE, 0);
    const std::string path(chars);
    env->ReleaseStringUTFChars(java_path, chars);

    if (path.empty() || path[0] != '/' || path.find('\0') != std::string::npos) {
        return open_result(env, INVALID_PATH, 0);
    }
    if (access(path.c_str(), F_OK) != 0) return open_result(env, errno == ENOENT ? MISSING : UNREADABLE, 0);
    if (access(path.c_str(), R_OK) != 0) return open_result(env, UNREADABLE, 0);
    if (!readable_file(path + "-wal") || !readable_file(path + "-shm")) {
        return open_result(env, WAL_SIDECARS_UNAVAILABLE, 0);
    }

    sqlite3* db = nullptr;
    const int open_rc = sqlite3_open_v2(
        path.c_str(), &db, SQLITE_OPEN_READONLY | SQLITE_OPEN_FULLMUTEX, nullptr);
    if (open_rc != SQLITE_OK || db == nullptr) {
        if (db != nullptr) sqlite3_close_v2(db);
        return open_result(env, OPEN_FAILED, 0);
    }
    const Status status = pin_deferred_snapshot(db);
    if (status != VERIFIED) {
        sqlite3_exec(db, "ROLLBACK", nullptr, nullptr, nullptr);
        sqlite3_close_v2(db);
        return open_result(env, status, 0);
    }

    std::lock_guard<std::mutex> guard(registry_mutex);
    if (next_handle <= 0 || next_handle == std::numeric_limits<jlong>::max()) {
        sqlite3_exec(db, "ROLLBACK", nullptr, nullptr, nullptr);
        sqlite3_close_v2(db);
        return open_result(env, INCOMPLETE_EVIDENCE, 0);
    }
    const jlong handle = next_handle++;
    connections.emplace(handle, db);
    return open_result(env, VERIFIED, handle);
}

extern "C" JNIEXPORT jbyteArray JNICALL
Java_com_kenznguyen_btclivealerts_NativeSqliteReadOnlyJni_nativeReadD5Snapshot(
    JNIEnv* env, jobject /* thiz */, jlong handle) {
    std::vector<uint8_t> body;
    D5Status status = D5_INVALID_HANDLE;
    {
        std::lock_guard<std::mutex> guard(registry_mutex);
        const auto found = connections.find(handle);
        if (found != connections.end()) status = read_d5_snapshot(found->second, body);
    }

    const size_t total = 4 + (status == D5_VERIFIED ? body.size() : 0);
    if (total > kMaxPayloadBytes || total > static_cast<size_t>(std::numeric_limits<jsize>::max())) {
        status = D5_PAYLOAD_TOO_LARGE;
    }
    const jsize output_size = static_cast<jsize>(4 + (status == D5_VERIFIED ? body.size() : 0));
    jbyteArray result = env->NewByteArray(output_size);
    if (result == nullptr) return nullptr;

    const uint32_t code = static_cast<uint32_t>(status);
    const jbyte prefix[4] = {
        static_cast<jbyte>((code >> 24) & 0xff),
        static_cast<jbyte>((code >> 16) & 0xff),
        static_cast<jbyte>((code >> 8) & 0xff),
        static_cast<jbyte>(code & 0xff),
    };
    env->SetByteArrayRegion(result, 0, 4, prefix);
    if (status == D5_VERIFIED && !body.empty()) {
        env->SetByteArrayRegion(result, 4, static_cast<jsize>(body.size()),
            reinterpret_cast<const jbyte*>(body.data()));
    }
    return result;
}

extern "C" JNIEXPORT jint JNICALL
Java_com_kenznguyen_btclivealerts_NativeSqliteReadOnlyJni_nativeCloseSnapshot(
    JNIEnv* /* env */, jobject /* thiz */, jlong handle) {
    std::lock_guard<std::mutex> guard(registry_mutex);
    const auto found = connections.find(handle);
    if (found == connections.end()) return ALREADY_CLOSED;

    sqlite3* db = found->second;
    const int rollback_rc = sqlite3_exec(db, "ROLLBACK", nullptr, nullptr, nullptr);
    if (rollback_rc != SQLITE_OK && rollback_rc != SQLITE_ERROR) return CLOSE_FAILED;
    const int close_rc = sqlite3_close_v2(db);
    if (close_rc != SQLITE_OK) return CLOSE_FAILED;
    connections.erase(found);
    return VERIFIED;
}
