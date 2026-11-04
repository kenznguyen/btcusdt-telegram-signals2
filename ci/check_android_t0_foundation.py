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

for forbidden in (
    "SQLiteDatabase",
    "openOrCreateDatabase",
    "getDatabasePath(",
    ".mkdir()",
    ".mkdirs()",
    "startService(",
    "startForegroundService(",
    "CREATE TABLE",
    "ALTER TABLE",
    "INSERT INTO",
    "UPDATE ",
    "DELETE FROM",
):
    assert forbidden not in application + runtime + contracts, f"Forbidden side effect found: {forbidden}"

print("ANDROID_T0_FOUNDATION_STATIC_AUDIT=PASS")
