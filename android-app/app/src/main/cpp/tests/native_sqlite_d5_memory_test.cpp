#include "../native_sqlite_readonly.cpp"

#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>

namespace {
int failures = 0;

void expect(bool condition, const char* message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << "\n";
        ++failures;
    }
}

sqlite3* memory_db() {
    sqlite3* db = nullptr;
    if (sqlite3_open(":memory:", &db) != SQLITE_OK) {
        if (db != nullptr) sqlite3_close(db);
        return nullptr;
    }
    sqlite3_exec(db, "PRAGMA foreign_keys=ON", nullptr, nullptr, nullptr);
    return db;
}

bool exec_sql(sqlite3* db, const std::string& sql) {
    char* error = nullptr;
    const int rc = sqlite3_exec(db, sql.c_str(), nullptr, nullptr, &error);
    if (rc != SQLITE_OK) {
        std::cerr << "SQLite fixture error: " << (error == nullptr ? "unknown" : error) << "\n";
        sqlite3_free(error);
        return false;
    }
    return true;
}

int deny_select(void*, int action, const char*, const char*, const char*, const char*) {
    return action == SQLITE_SELECT ? SQLITE_DENY : SQLITE_OK;
}

void test_populated_memory_schema(const std::string& fixture_path) {
    sqlite3* db = memory_db();
    expect(db != nullptr, "open isolated :memory: database");
    if (db == nullptr) return;

    const bool schema_ok = exec_sql(db,
        "CREATE TABLE parent(id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE) STRICT;"
        "CREATE TABLE child("
        " id INTEGER PRIMARY KEY,"
        " parent_id INTEGER NOT NULL REFERENCES parent(id) ON DELETE CASCADE,"
        " value TEXT,"
        " generated TEXT GENERATED ALWAYS AS (value || '-g') STORED"
        ") STRICT;"
        "CREATE INDEX idx_child_value ON child(value DESC) WHERE value IS NOT NULL;"
        "CREATE VIEW child_view AS SELECT id,parent_id FROM child;");
    expect(schema_ok, "create strict tables, generated column, partial descending index, view and foreign key");
    if (schema_ok) {
        std::vector<uint8_t> payload;
        const D5Status status = read_d5_snapshot(db, payload);
        expect(status == D5_VERIFIED, "fixed D5 query families succeed on the same in-memory connection");
        expect(!payload.empty(), "D5 query produces a non-empty D5WT envelope");
        if (status == D5_VERIFIED) {
            std::ofstream out(fixture_path, std::ios::binary | std::ios::trunc);
            const uint32_t code = static_cast<uint32_t>(D5_VERIFIED);
            const char prefix[4] = {
                static_cast<char>((code >> 24) & 0xff),
                static_cast<char>((code >> 16) & 0xff),
                static_cast<char>((code >> 8) & 0xff),
                static_cast<char>(code & 0xff),
            };
            out.write(prefix, sizeof(prefix));
            out.write(reinterpret_cast<const char*>(payload.data()), static_cast<std::streamsize>(payload.size()));
            expect(out.good(), "write native D5 wire fixture for Kotlin decoder parity test");
        }
    }
    sqlite3_close(db);
}

void test_virtual_table_is_rejected() {
    sqlite3* db = memory_db();
    expect(db != nullptr, "open virtual-table fixture database");
    if (db == nullptr) return;
    const bool created = exec_sql(db, "CREATE VIRTUAL TABLE search_docs USING fts5(content)");
    expect(created, "create FTS5 virtual table in isolated test database");
    if (created) {
        std::vector<uint8_t> payload;
        expect(read_d5_snapshot(db, payload) == D5_UNSUPPORTED_SCHEMA,
            "reject virtual-table schema instead of serializing incomplete evidence");
    }
    sqlite3_close(db);
}

void test_fixed_query_failure_is_fail_closed() {
    sqlite3* db = memory_db();
    expect(db != nullptr, "open query-failure fixture database");
    if (db == nullptr) return;
    sqlite3_set_authorizer(db, deny_select, nullptr);
    std::vector<uint8_t> payload;
    expect(read_d5_snapshot(db, payload) == D5_QUERY_FAILED,
        "propagate fixed-query preparation denial as D5_QUERY_FAILED");
    sqlite3_set_authorizer(db, nullptr, nullptr);
    sqlite3_close(db);
}

void test_oversized_payload_is_rejected() {
    sqlite3* db = memory_db();
    expect(db != nullptr, "open oversized-payload fixture database");
    if (db == nullptr) return;
    const std::string filler(512, 'x');
    bool created = true;
    for (int i = 0; i < 220 && created; ++i) {
        std::ostringstream sql;
        sql << "CREATE TABLE payload_" << i << "(value TEXT DEFAULT '" << filler << "')";
        created = exec_sql(db, sql.str());
    }
    expect(created, "create deterministic schema larger than the test payload ceiling");
    if (created) {
        std::vector<uint8_t> payload;
        expect(read_d5_snapshot(db, payload) == D5_PAYLOAD_TOO_LARGE,
            "reject D5 envelope that exceeds the configured payload ceiling");
    }
    sqlite3_close(db);
}
}  // namespace

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: native_sqlite_d5_memory_test <fixture-output-path>\n";
        return 2;
    }
    test_populated_memory_schema(argv[1]);
    test_virtual_table_is_rejected();
    test_fixed_query_failure_is_fail_closed();
    test_oversized_payload_is_rejected();
    if (failures != 0) {
        std::cerr << "T0.6 native in-memory D5 tests: " << failures << " failure(s)\n";
        return 1;
    }
    std::cout << "T0.6 native in-memory D5 tests: PASS (4 scenarios)\n";
    return 0;
}
