from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "android-app" / "app"
manifest = (APP / "src/main/AndroidManifest.xml").read_text()
application = (APP / "src/main/java/com/kenznguyen/btclivealerts/CanonicalApplication.kt").read_text()
runtime = (APP / "src/main/java/com/kenznguyen/btclivealerts/CanonicalRuntime.kt").read_text()
contracts = (APP / "src/main/java/com/kenznguyen/btclivealerts/CanonicalDatabaseContracts.kt").read_text()
gradle = (APP / "build.gradle.kts").read_text()
assert 'android:name=".CanonicalApplication"' in manifest
assert "BuildConfig.PARALLEL_INSTALL" in application
assert "applicationContext.dataDir" in application
assert "files/canonical/t0.sqlite" in runtime
assert 'buildConfigField("boolean", "PARALLEL_INSTALL", "true")' in gradle
assert "CanonicalDatabaseRoleId" in runtime
assert "CanonicalDatabaseInstanceId" in contracts
assert "object ReadOnlySchemaVerifier" in contracts
for forbidden in ("SQLiteDatabase","openOrCreateDatabase","getDatabasePath(",".mkdir()",".mkdirs()","startService(","startForegroundService(","CREATE TABLE","ALTER TABLE","INSERT INTO","UPDATE ","DELETE FROM"):
    assert forbidden not in application + runtime + contracts, f"Forbidden side effect found: {forbidden}"
native = (APP / "src/main/cpp/native_sqlite_readonly.cpp").read_text()
cmake = (APP / "src/main/cpp/CMakeLists.txt").read_text()
jni = (APP / "src/main/java/com/kenznguyen/btclivealerts/NativeSqliteReadOnlySession.kt").read_text()
for required in ("SQLITE_OPEN_READONLY | SQLITE_OPEN_FULLMUTEX",'sqlite3_db_readonly(db, "main") != 1','"BEGIN DEFERRED"',"sqlite3_stmt_readonly(anchor) != 1",'"SELECT count(*) FROM sqlite_schema"','"ROLLBACK"',"WAL_SIDECARS_UNAVAILABLE"):
    assert required in native, f"Native read-only contract missing: {required}"
for forbidden in ("SQLITE_OPEN_CREATE","SQLITE_OPEN_READWRITE","immutable=1","sqlite3_exec(db, sql"):
    assert forbidden not in native, f"Forbidden native SQLite capability found: {forbidden}"
assert "SQLITE_AMALGAMATION_DIR" in cmake
assert "no system/framework fallback" in cmake
assert "external fun nativeOpenPinnedSnapshot" in jni
assert "fun openPinnedSnapshot(path: String)" in jni
assert "fun closeSnapshot(handle: Long)" in jni
assert "fun executeSql" not in jni
print("ANDROID_T0_FOUNDATION_STATIC_AUDIT=PASS")
