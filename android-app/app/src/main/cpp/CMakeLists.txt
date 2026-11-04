cmake_minimum_required(VERSION 3.22.1)
project(canonical_sqlite LANGUAGES C CXX)

set(SQLITE_AMALGAMATION_DIR "" CACHE PATH "Directory containing verified sqlite3.c and sqlite3.h")
set(SQLITE_PIN_FILE "" CACHE FILEPATH "Generated SQLite release and file-hash pins")
if(NOT EXISTS "${SQLITE_PIN_FILE}")
    message(FATAL_ERROR "Verified SQLite pin file is required; run ci/prepare_pinned_sqlite.py first")
endif()
include("${SQLITE_PIN_FILE}")

set(SQLITE_REQUIRED_VERSION_NUMBER "3054001")
set(SQLITE_REQUIRED_SOURCE_ID "2026-10-16 14:45:20 555e07ef33f69a0957d24d8e555b702464a131d6f1607f4c3c1e4551e8e6ca76")
set(SQLITE_REQUIRED_ARCHIVE_SHA3_256 "92281c86e2957f9b9305890f9ac04204caa7b677cc868dc326d942689df28e30")
if(NOT SQLITE_EXPECTED_VERSION_NUMBER STREQUAL SQLITE_REQUIRED_VERSION_NUMBER)
    message(FATAL_ERROR "SQLite version pin mismatch")
endif()
if(NOT SQLITE_EXPECTED_SOURCE_ID STREQUAL SQLITE_REQUIRED_SOURCE_ID)
    message(FATAL_ERROR "SQLite source ID pin mismatch")
endif()
if(NOT SQLITE_EXPECTED_ARCHIVE_SHA3_256 STREQUAL SQLITE_REQUIRED_ARCHIVE_SHA3_256)
    message(FATAL_ERROR "SQLite archive SHA3-256 pin mismatch")
endif()
foreach(required SQLITE_EXPECTED_C_SHA256 SQLITE_EXPECTED_H_SHA256)
    if("${${required}}" STREQUAL "")
        message(FATAL_ERROR "${required} must be generated from the verified official archive")
    endif()
endforeach()

if(NOT EXISTS "${SQLITE_AMALGAMATION_DIR}/sqlite3.c" OR NOT EXISTS "${SQLITE_AMALGAMATION_DIR}/sqlite3.h")
    message(FATAL_ERROR "Pinned SQLite amalgamation is required; no system/framework fallback is allowed")
endif()
file(SHA256 "${SQLITE_AMALGAMATION_DIR}/sqlite3.c" ACTUAL_SQLITE_C_SHA256)
file(SHA256 "${SQLITE_AMALGAMATION_DIR}/sqlite3.h" ACTUAL_SQLITE_H_SHA256)
if(NOT ACTUAL_SQLITE_C_SHA256 STREQUAL SQLITE_EXPECTED_C_SHA256 OR NOT ACTUAL_SQLITE_H_SHA256 STREQUAL SQLITE_EXPECTED_H_SHA256)
    message(FATAL_ERROR "SQLite amalgamation SHA-256 mismatch")
endif()

file(STRINGS "${SQLITE_AMALGAMATION_DIR}/sqlite3.h" SQLITE_VERSION_LINE REGEX "^#define SQLITE_VERSION_NUMBER[ \\t]+[0-9]+")
string(REGEX REPLACE ".*SQLITE_VERSION_NUMBER[ \\t]+([0-9]+).*" "\\1" ACTUAL_SQLITE_VERSION_NUMBER "${SQLITE_VERSION_LINE}")
if(NOT ACTUAL_SQLITE_VERSION_NUMBER STREQUAL SQLITE_REQUIRED_VERSION_NUMBER)
    message(FATAL_ERROR "SQLite header version does not match the pinned release")
endif()

add_library(canonical_sqlite SHARED
    native_sqlite_readonly.cpp
    "${SQLITE_AMALGAMATION_DIR}/sqlite3.c"
)
target_include_directories(canonical_sqlite PRIVATE "${SQLITE_AMALGAMATION_DIR}")
target_compile_definitions(canonical_sqlite PRIVATE
    SQLITE_THREADSAFE=1
    SQLITE_OMIT_LOAD_EXTENSION=1
    SQLITE_DQS=0
    CANONICAL_SQLITE_EXPECTED_SOURCE_ID="${SQLITE_EXPECTED_SOURCE_ID}"
    $<$<CONFIG:Debug>:CANONICAL_SQLITE_TEST_HOOKS=1>
)
target_compile_features(canonical_sqlite PRIVATE cxx_std_17)
