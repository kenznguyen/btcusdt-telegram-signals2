from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/"android-app"/"app"
manifest=(APP/"src/main/AndroidManifest.xml").read_text()
application=(APP/"src/main/java/com/kenznguyen/btclivealerts/CanonicalApplication.kt").read_text()
runtime=(APP/"src/main/java/com/kenznguyen/btclivealerts/CanonicalRuntime.kt").read_text()
contracts=(APP/"src/main/java/com/kenznguyen/btclivealerts/CanonicalDatabaseContracts.kt").read_text()
gradle=(APP/"build.gradle.kts").read_text()
assert 'android:name=".CanonicalApplication"' in manifest
assert "BuildConfig.PARALLEL_INSTALL" in application and "applicationContext.dataDir" in application
assert "files/canonical/t0.sqlite" in runtime
assert 'buildConfigField("boolean", "PARALLEL_INSTALL", "true")' in gradle
assert "CanonicalDatabaseRoleId" in runtime and "CanonicalDatabaseInstanceId" in contracts
assert "object ReadOnlySchemaVerifier" in contracts
for forbidden in ("SQLiteDatabase","openOrCreateDatabase","getDatabasePath(",".mkdir()",".mkdirs()","startService(","startForegroundService(","CREATE TABLE","ALTER TABLE","INSERT INTO","UPDATE ","DELETE FROM"):
 assert forbidden not in application+runtime+contracts,f"Forbidden side effect: {forbidden}"
native_path=APP/"src/main/cpp/native_sqlite_readonly.cpp"
native=native_path.read_text().replace(" ","")
cmake=(APP/"src/main/cpp/CMakeLists.txt").read_text()
preparer=(ROOT/"ci/prepare_pinned_sqlite.py").read_text()
workflow=(ROOT/".github/workflows/android-t0-foundation.yml").read_text()
jni=(APP/"src/main/java/com/kenznguyen/btclivealerts/NativeSqliteReadOnlySession.kt").read_text()
for required in ("SQLITE_OPEN_READONLY|SQLITE_OPEN_FULLMUTEX",'sqlite3_db_readonly(db,"main")!=1','"BEGINDEFERRED"',"sqlite3_stmt_readonly(anchor)!=1",'"SELECTcount(*)FROMsqlite_schema"','"ROLLBACK"',"WAL_SIDECARS_UNAVAILABLE","sqlite3_sourceid()","CANONICAL_SQLITE_EXPECTED_SOURCE_ID"):
 assert required.replace(" ","") in native,f"Native contract missing: {required}"
for forbidden in ("SQLITE_OPEN_CREATE","SQLITE_OPEN_READWRITE","immutable=1","sqlite3_exec(db,sql"):
 assert forbidden not in native,f"Forbidden native capability: {forbidden}"
assert native.index("readable_file(path+\"-wal\")") < native.index("sqlite3_open_v2("), "WAL sidecars must be preflighted before SQLite opens the file"
for required in ("SQLITE_EXPECTED_VERSION_NUMBER","SQLITE_EXPECTED_SOURCE_ID","SQLITE_EXPECTED_C_SHA256","SQLITE_EXPECTED_H_SHA256","file(SHA256","no system/framework fallback"):
 assert required in cmake,f"SQLite pinning requirement missing: {required}"
assert "external fun nativeOpenPinnedSnapshot" in jni and "fun executeSql" not in jni
assert 'ndkVersion = "27.2.12479018"' in gradle
assert 'version = "3.22.1"' in gradle
assert 'abiFilters += listOf("arm64-v8a", "armeabi-v7a", "x86", "x86_64")' in gradle
assert "-DSQLITE_AMALGAMATION_DIR=" in gradle and "-DSQLITE_PIN_FILE=" in gradle
assert 'SQLITE_VERSION = "3.54.1"' in preparer
assert 'SQLITE_VERSION_NUMBER = "3054001"' in preparer
assert "92281c86e2957f9b9305890f9ac04204caa7b677cc868dc326d942689df28e30" in preparer
assert "2026-10-16 14:45:20" in preparer and "555e07ef33f69a0957d24d8e555b702464a131d6f1607f4c3c1e4551e8e6ca76" in preparer
assert "verify_archive_digest(payload)" in preparer
assert "gradle :app:externalNativeBuildDebug" in workflow
assert "ndk;27.2.12479018" in workflow and "cmake;3.22.1" in workflow
assert "sqlite-amalgamation-3540100.zip" in workflow
assert "assembleRelease" not in workflow and "assembleDebug" not in workflow

d5_wire=(APP/"src/main/java/com/kenznguyen/btclivealerts/NativeSqliteD5WireDecoder.kt").read_text()
session_tests=(ROOT/"android-app/app/src/test/java/com/kenznguyen/btclivealerts/NativeSqliteD5WireDecoderTest.kt").read_text()
for required in (
 "sqlite3_stmt_readonly(*stmt)!=1",
 "sqlite3_bind_text(stmt,1,bound_name->c_str()",
 "SELECTsqlite_version(),sqlite_source_id()",
 "pragma_table_list",
 "pragma_table_xinfo(?1,'main')",
 "pragma_index_list(?1,'main')",
 "pragma_index_xinfo(?1,'main')",
 "pragma_foreign_key_list(?1,'main')",
 "D5_PAYLOAD_TOO_LARGE",
 "D5_UNSUPPORTED_SCHEMA",
):
 assert required.replace(" ","") in native,f"Fixed D5 native query guard missing: {required}"
assert "SQLITE_OPEN_CREATE" not in native and "SQLITE_OPEN_READWRITE" not in native
assert "sqlite3_exec(db,sql" not in native
assert "nativeReadD5Snapshot" in jni and "fun readD5Snapshot()" in jni
assert "fun executeSql" not in jni and "nativeExecuteSql" not in jni
for required in ("D5WT","readBooleanStrict","MAX_ROWS_PER_SECTION","MAX_STRING_BYTES","validateTableList","schemaIntrospectionQueries"):
 assert required in d5_wire,f"D5 wire validation missing: {required}"
for required in ("decodesAllD5Sections","rejectsTruncatedAndTrailingTransportBytes","rejectsWrongMagicAndUnsupportedWireVersion","rejectsVirtualOrShadowObjectsBeforeReturningAnEnvelope","rejectsCatalogAndTableListDisagreement"):
 assert required in session_tests,f"D5 decoder test missing: {required}"
print("ANDROID_T0_FOUNDATION_STATIC_AUDIT=PASS")
