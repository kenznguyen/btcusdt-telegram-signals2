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
native=(APP/"src/main/cpp/native_sqlite_readonly.cpp").read_text().replace(" ","")
cmake=(APP/"src/main/cpp/CMakeLists.txt").read_text()
jni=(APP/"src/main/java/com/kenznguyen/btclivealerts/NativeSqliteReadOnlySession.kt").read_text()
for required in ("SQLITE_OPEN_READONLY|SQLITE_OPEN_FULLMUTEX",'sqlite3_db_readonly(db,"main")!=1','"BEGINDEFERRED"',"sqlite3_stmt_readonly(anchor)!=1",'"SELECTcount(*)FROMsqlite_schema"','"ROLLBACK"',"WAL_SIDECARS_UNAVAILABLE","sqlite3_sourceid()","CANONICAL_SQLITE_EXPECTED_SOURCE_ID"):
 assert required.replace(" ","") in native,f"Native contract missing: {required}"
for forbidden in ("SQLITE_OPEN_CREATE","SQLITE_OPEN_READWRITE","immutable=1","sqlite3_exec(db,sql"):
 assert forbidden not in native,f"Forbidden native capability: {forbidden}"
for required in ("SQLITE_EXPECTED_VERSION_NUMBER","SQLITE_EXPECTED_SOURCE_ID","SQLITE_EXPECTED_C_SHA256","SQLITE_EXPECTED_H_SHA256","file(SHA256","no system/framework fallback"):
 assert required in cmake,f"SQLite pinning requirement missing: {required}"
assert "external fun nativeOpenPinnedSnapshot" in jni and "fun executeSql" not in jni
print("ANDROID_T0_FOUNDATION_STATIC_AUDIT=PASS")
