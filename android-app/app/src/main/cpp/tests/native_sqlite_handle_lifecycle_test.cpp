#include "../native_sqlite_readonly.cpp"

#include <atomic>
#include <iostream>
#include <thread>
#include <vector>

namespace {
int failures = 0;

void expect(bool condition, const char* message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << "\n";
        ++failures;
    }
}

sqlite3* make_memory_database() {
    sqlite3* db = nullptr;
    if (sqlite3_open(":memory:", &db) != SQLITE_OK) {
        if (db != nullptr) sqlite3_close(db);
        return nullptr;
    }
    if (sqlite3_exec(db,
            "CREATE TABLE lifecycle_probe(id INTEGER PRIMARY KEY, value TEXT NOT NULL);"
            "INSERT INTO lifecycle_probe(value) VALUES('isolated');",
            nullptr, nullptr, nullptr) != SQLITE_OK) {
        sqlite3_close(db);
        return nullptr;
    }
    return db;
}

void test_register_read_close_lifecycle() {
    sqlite3* db = make_memory_database();
    expect(db != nullptr, "create isolated in-memory database");
    if (db == nullptr) return;

    const jlong handle = register_snapshot_handle(db);
    expect(handle > 0, "registry issues a positive opaque handle");
    if (handle <= 0) {
        sqlite3_close(db);
        return;
    }

    std::vector<uint8_t> payload;
    expect(read_registered_d5_snapshot(handle, payload) == D5_VERIFIED,
        "D5 read succeeds through the registered handle");
    expect(!payload.empty(), "successful handle read returns D5 wire payload");

    expect(close_registered_snapshot(handle) == VERIFIED,
        "registered handle closes successfully");
    expect(read_registered_d5_snapshot(handle, payload) == D5_INVALID_HANDLE,
        "closed handle cannot read D5");
    expect(close_registered_snapshot(handle) == ALREADY_CLOSED,
        "closing an already closed handle is reported idempotently");
}

void test_unknown_and_zero_handles_fail_closed() {
    std::vector<uint8_t> payload;
    expect(read_registered_d5_snapshot(0, payload) == D5_INVALID_HANDLE,
        "zero handle is rejected");
    expect(read_registered_d5_snapshot(0x7fffffff, payload) == D5_INVALID_HANDLE,
        "unknown handle is rejected");
    expect(close_registered_snapshot(0) == ALREADY_CLOSED,
        "zero handle cannot close a connection");
    expect(close_registered_snapshot(0x7fffffff) == ALREADY_CLOSED,
        "unknown handle cannot close a connection");
}

void test_handles_are_unique_and_independently_owned() {
    sqlite3* first_db = make_memory_database();
    sqlite3* second_db = make_memory_database();
    expect(first_db != nullptr && second_db != nullptr, "create two isolated databases");
    if (first_db == nullptr || second_db == nullptr) {
        if (first_db != nullptr) sqlite3_close(first_db);
        if (second_db != nullptr) sqlite3_close(second_db);
        return;
    }

    const jlong first = register_snapshot_handle(first_db);
    const jlong second = register_snapshot_handle(second_db);
    expect(first > 0 && second > 0 && first != second,
        "each registered connection receives a distinct handle");
    if (first > 0 && second > 0 && first != second) {
        expect(close_registered_snapshot(first) == VERIFIED,
            "closing first handle succeeds");
        std::vector<uint8_t> payload;
        expect(read_registered_d5_snapshot(second, payload) == D5_VERIFIED,
            "closing one handle does not affect another registered connection");
        expect(close_registered_snapshot(second) == VERIFIED,
            "second handle closes independently");
    } else {
        if (first > 0) close_registered_snapshot(first);
        if (second > 0) close_registered_snapshot(second);
        if (first <= 0) sqlite3_close(first_db);
        if (second <= 0) sqlite3_close(second_db);
    }
}

void test_concurrent_read_and_close_are_serialized() {
    sqlite3* db = make_memory_database();
    expect(db != nullptr, "create concurrency fixture database");
    if (db == nullptr) return;

    const jlong handle = register_snapshot_handle(db);
    expect(handle > 0, "register concurrency fixture handle");
    if (handle <= 0) {
        sqlite3_close(db);
        return;
    }

    std::atomic<bool> start{false};
    D5Status read_status = D5_QUERY_FAILED;
    Status close_status = CLOSE_FAILED;
    std::vector<uint8_t> payload;

    std::thread reader([&] {
        while (!start.load(std::memory_order_acquire)) std::this_thread::yield();
        read_status = read_registered_d5_snapshot(handle, payload);
    });
    std::thread closer([&] {
        while (!start.load(std::memory_order_acquire)) std::this_thread::yield();
        close_status = close_registered_snapshot(handle);
    });
    start.store(true, std::memory_order_release);
    reader.join();
    closer.join();

    expect(close_status == VERIFIED, "concurrent close succeeds exactly once");
    expect(read_status == D5_VERIFIED || read_status == D5_INVALID_HANDLE,
        "concurrent read either completes before close or observes invalid handle");
    expect(read_registered_d5_snapshot(handle, payload) == D5_INVALID_HANDLE,
        "handle remains invalid after concurrent close completes");
    expect(close_registered_snapshot(handle) == ALREADY_CLOSED,
        "concurrent lifecycle leaves no registered connection behind");
}
}  // namespace

int main() {
    test_register_read_close_lifecycle();
    test_unknown_and_zero_handles_fail_closed();
    test_handles_are_unique_and_independently_owned();
    test_concurrent_read_and_close_are_serialized();

    if (failures != 0) {
        std::cerr << "T0.7 JNI handle-registry lifecycle tests: "
                  << failures << " failure(s)\n";
        return 1;
    }
    std::cout << "T0.7 JNI handle-registry lifecycle tests: PASS (4 scenarios)\n";
    return 0;
}
