cmake_minimum_required(VERSION 3.22.1)
project(t0_6_native_sqlite_d5_memory_tests LANGUAGES C CXX)

set(SQLITE_AMALGAMATION_DIR "" CACHE PATH "Directory containing verified sqlite3.c and sqlite3.h")
set(SQLITE_EXPECTED_SOURCE_ID "2026-10-16 14:45:20 555e07ef33f69a0957d24d8e555b702464a131d6f1607f4c3c1e4551e8e6ca76")
if(NOT EXISTS "${SQLITE_AMALGAMATION_DIR}/sqlite3.c" OR NOT EXISTS "${SQLITE_AMALGAMATION_DIR}/sqlite3.h")
    message(FATAL_ERROR "T0.6/T0.7 require the verified pinned SQLite amalgamation")
endif()

find_package(JNI REQUIRED)
set(T0_NATIVE_SQLITE_TEST_INCLUDE_DIRS "${SQLITE_AMALGAMATION_DIR}" ${JNI_INCLUDE_DIRS})
set(T0_NATIVE_SQLITE_TEST_DEFINITIONS
    SQLITE_THREADSAFE=1
    SQLITE_OMIT_LOAD_EXTENSION=1
    SQLITE_DQS=0
    CANONICAL_SQLITE_EXPECTED_SOURCE_ID="${SQLITE_EXPECTED_SOURCE_ID}"
)

add_executable(native_sqlite_d5_memory_test
    native_sqlite_d5_memory_test.cpp
    "${SQLITE_AMALGAMATION_DIR}/sqlite3.c"
)
target_include_directories(native_sqlite_d5_memory_test PRIVATE ${T0_NATIVE_SQLITE_TEST_INCLUDE_DIRS})
target_compile_definitions(native_sqlite_d5_memory_test PRIVATE
    ${T0_NATIVE_SQLITE_TEST_DEFINITIONS}
    SQLITE_ENABLE_FTS5
    CANONICAL_D5_MAX_PAYLOAD_BYTES=65536
)
target_compile_features(native_sqlite_d5_memory_test PRIVATE cxx_std_17)

add_executable(native_sqlite_handle_lifecycle_test
    native_sqlite_handle_lifecycle_test.cpp
    "${SQLITE_AMALGAMATION_DIR}/sqlite3.c"
)
target_include_directories(native_sqlite_handle_lifecycle_test PRIVATE ${T0_NATIVE_SQLITE_TEST_INCLUDE_DIRS})
target_compile_definitions(native_sqlite_handle_lifecycle_test PRIVATE ${T0_NATIVE_SQLITE_TEST_DEFINITIONS})
target_compile_features(native_sqlite_handle_lifecycle_test PRIVATE cxx_std_17)

if(UNIX)
    target_link_libraries(native_sqlite_d5_memory_test PRIVATE pthread dl m)
    target_link_libraries(native_sqlite_handle_lifecycle_test PRIVATE pthread dl m)
endif()

enable_testing()
add_test(
    NAME t0_6_native_sqlite_d5_memory
    COMMAND native_sqlite_d5_memory_test "${CMAKE_CURRENT_BINARY_DIR}/d5-native-memory-fixture.bin"
)
add_test(
    NAME t0_7_native_sqlite_handle_lifecycle
    COMMAND native_sqlite_handle_lifecycle_test
)
