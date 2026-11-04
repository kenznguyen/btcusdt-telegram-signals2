#include "../native_sqlite_readonly.cpp"

#include <atomic>
#include <iostream>
#include <thread>
#include <vector>

namespace {
int failures = 0;

struct FakeLongArray { std::vector<jlong> values; };
struct FakeByteArray { std::vector<jbyte> values; };

jlongArray JNICALL fake_new_long_array(JNIEnv*, jsize length) {
    return reinterpret_cast<jlongArray>(new FakeLongArray{std::vector<jlong>(static_cast<size_t>(length))});
}
void JNICALL fake_set_long_array_region(JNIEnv*, jlongArray array, jsize start, jsize length, const jlong* values) {
    auto* target = reinterpret_cast<FakeLongArray*>(array);
    std::copy(values, values + length, target->values.begin() + start);
}
jbyteArray JNICALL fake_new_byte_array(JNIEnv*, jsize length) {
    return reinterpret_cast<jbyteArray>(new FakeByteArray{std::vector<jbyte>(static_cast<size_t>(length))});
}
void JNICALL fake_set_byte_array_region(JNIEnv*, jbyteArray array, jsize start, jsize length, const jbyte* values) {
    auto* target = reinterpret_cast<FakeByteArray*>(array);
    std::copy(values, values + length, target->values.begin() + start);
}
JNIEnv make_test_jni_env(JNINativeInterface_& functions) {
    functions = JNINativeInterface_{};
    functions.NewLongArray = fake_new_long_array;
    functions.SetLongArrayRegion = fake_set_long_array_region;
    functions.NewByteArray = fake_new_byte_array;
    functions.SetByteArrayRegion = fake_set_byte_array_region;
    return JNIEnv{&functions};
}


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
            "CREATE TABLE canonical_database_identity(singleton_key INTEGER PRIMARY KEY, role_id TEXT NOT NULL, instance_id TEXT NOT NULL, identity_format_version INTEGER NOT NULL, provenance TEXT NOT NULL, parent_instance_id TEXT, created_at_utc TEXT NOT NULL);"
            "INSERT INTO canonical_database_identity VALUES(1, 't0-canonical-sqlite-v1', '550e8400-e29b-41d4-a716-446655440000', 1, 'INITIAL_PROVISIONING', NULL, '2026-11-04T00:00:00Z');"
            "CREATE TABLE schema_migrations(migration_id TEXT PRIMARY KEY, sequence INTEGER NOT NULL, owner_domain TEXT NOT NULL, checksum_sha256 TEXT NOT NULL, applied_at_utc TEXT NOT NULL);"
            "INSERT INTO schema_migrations VALUES('t0.bootstrap.v1', 1, 'T0', '0000000000000000000000000000000000000000000000000000000000000000', '2026-11-04T00:00:00Z');"
            "CREATE TABLE lifecycle_probe(id INTEGER PRIMARY KEY, value TEXT NOT NULL);"
            "INSERT INTO lifecycle_probe(value) VALUES('isolated');",
            nullptr, nullptr, nullptr) != SQLITE_OK) {
        sqlite3_close(db);
        return nullptr;
    }
    return db;
}

void test_exported_jni_open_read_close_exports() {
    JNINativeInterface_ functions{};
    JNIEnv env = make_test_jni_env(functions);

    jlongArray opened = Java_com_kenznguyen_btclivealerts_NativeSqliteReadOnlyJni_nativeTestOpenInMemory(&env, nullptr);
    expect(opened != nullptr, "test-only JNI open returns a Java long array");
    if (opened == nullptr) return;
    const auto* open_values = reinterpret_cast<FakeLongArray*>(opened);
    expect(open_values->values.size() == 2, "JNI open reply contains status and handle");
    if (open_values->values.size() != 2) {
        delete open_values;
        return;
    }
    const jlong status = open_values->values[0];
    const jlong handle = open_values->values[1];
    expect(status == VERIFIED && handle > 0, "JNI open registers an isolated in-memory connection");
    delete open_values;
    if (status != VERIFIED || handle <= 0) return;

    jbyteArray read = Java_com_kenznguyen_btclivealerts_NativeSqliteReadOnlyJni_nativeReadD5Snapshot(
        &env, nullptr, handle);
    expect(read != nullptr, "JNI D5 read returns a Java byte array");
    if (read != nullptr) {
        const auto* bytes = reinterpret_cast<FakeByteArray*>(read);
        expect(bytes->values.size() > 8, "JNI D5 read returns status-prefixed D5 wire bytes");
        if (bytes->values.size() > 8) {
            const auto* raw = reinterpret_cast<const uint8_t*>(bytes->values.data());
            expect(raw[0] == 0 && raw[1] == 0 && raw[2] == 0 && raw[3] == D5_VERIFIED,
                "JNI D5 read status prefix is VERIFIED");
            expect(raw[4] == 0x44 && raw[5] == 0x35 && raw[6] == 0x57 && raw[7] == 0x54,
                "JNI D5 read body starts with D5WT wire magic");
        }
        delete bytes;
    }

    expect(Java_com_kenznguyen_btclivealerts_NativeSqliteReadOnlyJni_nativeCloseSnapshot(
        &env, nullptr, handle) == VERIFIED, "JNI close export closes the registered connection");
    jbyteArray after_close = Java_com_kenznguyen_btclivealerts_NativeSqliteReadOnlyJni_nativeReadD5Snapshot(
        &env, nullptr, handle);
    expect(after_close != nullptr, "JNI read after close returns a status array");
    if (after_close != nullptr) {
        const auto* bytes = reinterpret_cast<FakeByteArray*>(after_close);
        const auto* raw = reinterpret_cast<const uint8_t*>(bytes->values.data());
        expect(bytes->values.size() == 4 && raw[3] == D5_INVALID_HANDLE,
            "JNI read after close fails closed with INVALID_HANDLE");
        delete bytes;
    }
    expect(Java_com_kenznguyen_btclivealerts_NativeSqliteReadOnlyJni_nativeCloseSnapshot(
        &env, nullptr, handle) == ALREADY_CLOSED, "JNI repeated close is idempotently rejected");
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
    test_exported_jni_open_read_close_exports();
    test_register_read_close_lifecycle();
    test_unknown_and_zero_handles_fail_closed();
    test_handles_are_unique_and_independently_owned();
    test_concurrent_read_and_close_are_serialized();

    if (failures != 0) {
        std::cerr << "T0.7 JNI handle-registry lifecycle tests: "
                  << failures << " failure(s)\n";
        return 1;
    }
    std::cout << "T0.7 JNI handle-registry lifecycle tests: PASS (5 scenarios)\n";
    return 0;
}
