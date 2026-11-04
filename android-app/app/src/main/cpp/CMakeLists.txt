cmake_minimum_required(VERSION 3.22.1)
project(canonical_sqlite LANGUAGES C CXX)

# The exact upstream SQLite amalgamation must be supplied and checksum-pinned
# by the build owner before this target is wired into Gradle. Never fall back
# to the Android framework SQLite engine or an unpinned system library.
set(SQLITE_AMALGAMATION_DIR "" CACHE PATH "Directory containing pinned sqlite3.c and sqlite3.h")
if(NOT EXISTS "${SQLITE_AMALGAMATION_DIR}/sqlite3.c" OR
   NOT EXISTS "${SQLITE_AMALGAMATION_DIR}/sqlite3.h")
    message(FATAL_ERROR "Pinned SQLite amalgamation is required; no system/framework fallback is allowed")
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
)
target_compile_features(canonical_sqlite PRIVATE cxx_std_17)
