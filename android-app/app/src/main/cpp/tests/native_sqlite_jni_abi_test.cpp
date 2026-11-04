#include "../native_sqlite_readonly.cpp"

#include <algorithm>
#include <iostream>
#include <vector>

namespace {
struct FakeLongArray { std::vector<jlong> values; };
struct FakeByteArray { std::vector<jbyte> values; };

int long_allocations = 0;
int byte_allocations = 0;
int long_region_writes = 0;
int byte_region_writes = 0;
bool fail_long_allocation = false;
bool fail_byte_allocation = false;

jlongArray JNICALL fake_new_long_array(JNIEnv*, jsize length) {
    ++long_allocations;
    if (fail_long_allocation) return nullptr;
    return reinterpret_cast<jlongArray>(
        new FakeLongArray{std::vector<jlong>(static_cast<size_t>(length))});
}
void JNICALL fake_set_long_array_region(
    JNIEnv*, jlongArray array, jsize start, jsize length, const jlong* values) {
    ++long_region_writes;
    auto* target = reinterpret_cast<FakeLongArray*>(array);
    std::copy(values, values + length, target->values.begin() + start);
}
jbyteArray JNICALL fake_new_byte_array(JNIEnv*, jsize length) {
    ++byte_allocations;
    if (fail_byte_allocation) return nullptr;
    return reinterpret_cast<jbyteArray>(
        new FakeByteArray{std::vector<jbyte>(static_cast<size_t>(length))});
}
void JNICALL fake_set_byte_array_region(
    JNIEnv*, jbyteArray array, jsize start, jsize length, const jbyte* values) {
    ++byte_region_writes;
    auto* target = reinterpret_cast<FakeByteArray*>(array);
    std::copy(values, values + length, target->values.begin() + start);
}

JNIEnv make_env(JNINativeInterface_& functions) {
    functions = JNINativeInterface_{};
    functions.NewLongArray = fake_new_long_array;
    functions.SetLongArrayRegion = fake_set_long_array_region;
    functions.NewByteArray = fake_new_byte_array;
    functions.SetByteArrayRegion = fake_set_byte_array_region;
    return JNIEnv{&functions};
}

void reset_counters() {
    long_allocations = 0;
    byte_allocations = 0;
    long_region_writes = 0;
    byte_region_writes = 0;
    fail_long_allocation = false;
    fail_byte_allocation = false;
}

int failures = 0;
void expect(bool condition, const char* message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << "\n";
        ++failures;
    }
}
void destroy(jlongArray value) {
    delete reinterpret_cast<FakeLongArray*>(value);
}
void destroy(jbyteArray value) {
    delete reinterpret_cast<FakeByteArray*>(value);
}

void test_null_path_uses_two_long_status_frame() {
    reset_counters();
    JNINativeInterface_ functions{};
    JNIEnv env = make_env(functions);

    jlongArray result =
        Java_com_kenznguyen_btclivealerts_NativeSqliteReadOnlyJni_nativeOpenPinnedSnapshot(
            &env, nullptr, nullptr);
    expect(result != nullptr, "null path returns a JNI long-array result");
    if (result == nullptr) return;
    const auto* frame = reinterpret_cast<FakeLongArray*>(result);
    expect(frame->values.size() == 2, "open result frame has exactly two jlong values");
    if (frame->values.size() == 2) {
        expect(frame->values[0] == INVALID_PATH, "null path maps to INVALID_PATH");
        expect(frame->values[1] == 0, "failed open never publishes a handle");
    }
    expect(long_allocations == 1 && long_region_writes == 1,
        "open result allocates and writes exactly one status frame");
    destroy(result);
}

void test_read_status_prefix_is_four_byte_big_endian() {
    reset_counters();
    JNINativeInterface_ functions{};
    JNIEnv env = make_env(functions);

    jbyteArray result =
        Java_com_kenznguyen_btclivealerts_NativeSqliteReadOnlyJni_nativeReadD5Snapshot(
            &env, nullptr, 0);
    expect(result != nullptr, "invalid handle read returns a JNI byte-array frame");
    if (result == nullptr) return;
    const auto* frame = reinterpret_cast<FakeByteArray*>(result);
    expect(frame->values.size() == 4, "non-verified read frame contains status only");
    if (frame->values.size() == 4) {
        const auto* bytes = reinterpret_cast<const uint8_t*>(frame->values.data());
        expect(bytes[0] == 0 && bytes[1] == 0 && bytes[2] == 0 &&
                   bytes[3] == D5_INVALID_HANDLE,
            "invalid-handle status is encoded as a four-byte big-endian prefix");
    }
    expect(byte_allocations == 1 && byte_region_writes == 1,
        "read result allocates and writes exactly one status frame");
    destroy(result);
}

void test_jni_array_allocation_failures_propagate_null() {
    reset_counters();
    JNINativeInterface_ functions{};
    JNIEnv env = make_env(functions);

    fail_long_allocation = true;
    jlongArray open_result_array =
        Java_com_kenznguyen_btclivealerts_NativeSqliteReadOnlyJni_nativeOpenPinnedSnapshot(
            &env, nullptr, nullptr);
    expect(open_result_array == nullptr, "open propagates NewLongArray allocation failure");
    expect(long_region_writes == 0, "open does not write through a null Java array");

    fail_long_allocation = false;
    fail_byte_allocation = true;
    jbyteArray read_result_array =
        Java_com_kenznguyen_btclivealerts_NativeSqliteReadOnlyJni_nativeReadD5Snapshot(
            &env, nullptr, 0);
    expect(read_result_array == nullptr, "read propagates NewByteArray allocation failure");
    expect(byte_region_writes == 0, "read does not write through a null Java array");
}

void test_exported_open_read_close_abi_round_trip() {
    reset_counters();
    JNINativeInterface_ functions{};
    JNIEnv env = make_env(functions);

    jlongArray opened =
        Java_com_kenznguyen_btclivealerts_NativeSqliteReadOnlyJni_nativeTestOpenInMemory(
            &env, nullptr);
    expect(opened != nullptr, "test-only open export returns a Java long array");
    if (opened == nullptr) return;
    const auto* open_frame = reinterpret_cast<FakeLongArray*>(opened);
    expect(open_frame->values.size() == 2, "test-only open uses the two-long ABI frame");
    if (open_frame->values.size() != 2) {
        destroy(opened);
        return;
    }
    const jlong status = open_frame->values[0];
    const jlong handle = open_frame->values[1];
    expect(status == VERIFIED && handle > 0, "test-only open returns VERIFIED and a positive handle");
    destroy(opened);
    if (status != VERIFIED || handle <= 0) return;

    jbyteArray read =
        Java_com_kenznguyen_btclivealerts_NativeSqliteReadOnlyJni_nativeReadD5Snapshot(
            &env, nullptr, handle);
    expect(read != nullptr, "read export returns a Java byte array");
    if (read != nullptr) {
        const auto* read_frame = reinterpret_cast<FakeByteArray*>(read);
        expect(read_frame->values.size() > 8, "verified read contains status and D5 body");
        if (read_frame->values.size() > 8) {
            const auto* bytes = reinterpret_cast<const uint8_t*>(read_frame->values.data());
            expect(bytes[0] == 0 && bytes[1] == 0 && bytes[2] == 0 &&
                       bytes[3] == D5_VERIFIED,
                "verified read has a zero big-endian status prefix");
            expect(bytes[4] == 0x44 && bytes[5] == 0x35 &&
                       bytes[6] == 0x57 && bytes[7] == 0x54,
                "verified read body begins with D5WT magic");
        }
        destroy(read);
    }
    expect(Java_com_kenznguyen_btclivealerts_NativeSqliteReadOnlyJni_nativeCloseSnapshot(
               &env, nullptr, handle) == VERIFIED,
        "close export returns VERIFIED");
    expect(Java_com_kenznguyen_btclivealerts_NativeSqliteReadOnlyJni_nativeCloseSnapshot(
               &env, nullptr, handle) == ALREADY_CLOSED,
        "repeated close export returns ALREADY_CLOSED");
}

}  // namespace

int main() {
    test_null_path_uses_two_long_status_frame();
    test_read_status_prefix_is_four_byte_big_endian();
    test_jni_array_allocation_failures_propagate_null();
    test_exported_open_read_close_abi_round_trip();

    if (failures != 0) {
        std::cerr << "T0.8 host JNI ABI tests: " << failures << " failure(s)\n";
        return 1;
    }
    std::cout << "T0.8 host JNI ABI tests: PASS (4 scenarios)\n";
    return 0;
}
