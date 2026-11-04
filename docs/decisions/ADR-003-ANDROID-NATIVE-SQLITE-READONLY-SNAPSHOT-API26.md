# ADR-003 — Android Native SQLite Read-only Snapshot for API 26+

Date: 2026-11-04 (Asia/Ho_Chi_Minh)
Status: **PROPOSED — OWNER DESIGN DECISION RECORDED; IMPLEMENTATION NOT AUTHORIZED**
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/p5-4-1-post-merge-validation-20261103`

## Context

The canonical Android database must support one consistent, read-only SQLite snapshot on minSdk 26. Every schema, runtime identity, migration registry and D5 introspection query must execute on the same SQLite connection and within one DEFERRED read transaction. The adapter must never create a missing database and must fail closed when it cannot prove the required behavior.

The existing source spike P5.4.98 correctly rejected AndroidX's reflection/fallback path. Android's public `SQLiteDatabase.beginTransactionReadOnly()` was added in API 35, so it cannot satisfy minSdk 26 by itself. AndroidX's `SupportSQLiteDatabase.beginTransactionReadOnly()` API contract is not sufficient evidence that the concrete framework implementation on API 26–34 avoids fallback.

## Decision

**Select a pinned SQLite amalgamation built with Android NDK and exposed through a narrow JNI adapter as the single SQLite engine for every connection to the canonical database on all supported Android API levels (26+).**

Do not mix Android framework SQLite for canonical writes with a separately bundled SQLite engine for canonical reads. The canonical host's writer and read-only snapshot connections must use the same bundled SQLite build, VFS, compile options and connection policy. Other unrelated app databases may continue using Android framework APIs, but they must never point at the canonical file.

This decision is a design selection only. It does not authorize source implementation, dependency changes, NDK setup, database opening/creation, device tests, Feeder activation or runtime operations.

## Required native connection contract

1. Kotlin resolves and validates the existing canonical path under the regular host's app-private directory. It must be an existing regular file. Missing path returns `MISSING`; do not create directories, DB, WAL or SHM.
2. Native code opens the existing database using `sqlite3_open_v2(path, &db, SQLITE_OPEN_READONLY | SQLITE_OPEN_FULLMUTEX, nullptr)`. Never pass `SQLITE_OPEN_CREATE` or `SQLITE_OPEN_READWRITE` to the read-only connection.
3. Verify `sqlite3_db_readonly(db, "main") == 1`. Any other result fails closed.
4. Start exactly `BEGIN DEFERRED` on that connection. Do not use `BEGIN IMMEDIATE`, `BEGIN EXCLUSIVE`, Android `beginTransactionNonExclusive()`, or a framework transaction wrapper.
5. A DEFERRED transaction is lazy. Immediately execute and consume a database-backed anchor read (for example, a bounded read of `sqlite_schema`) to establish the snapshot before collecting any evidence. A SELECT that only evaluates constants/functions is not a snapshot anchor.
6. Execute all runtime, identity, migration, catalog and PRAGMA introspection statements on the same `sqlite3*` connection and inside that same transaction. Do not return a connection to a pool between queries.
7. Prepare only fixed, reviewed read statements. Require `sqlite3_stmt_readonly(stmt) == 1` for every prepared statement before stepping it. Do not expose arbitrary SQL execution through the Kotlin API.
8. Keep the transaction open until all rows and cursors have been fully consumed. End it with `ROLLBACK` (there are no writes to commit), finalize statements, then close the connection on every success/error path.
9. Do not set `immutable=1` for the live canonical database. It bypasses normal locking/change observation and cannot establish a valid live concurrent-writer snapshot.
10. Do not treat `PRAGMA query_only=ON` alone as the read-only security boundary. The OS-level read-only open flag, `sqlite3_db_readonly`, fixed query allowlist and `sqlite3_stmt_readonly` checks are required together.

## WAL policy and sidecar behavior

SQLite read-only WAL access has explicit prerequisites. SQLite documents read-only WAL access when the `-wal` and `-shm` files already exist and are readable, or when the directory permits creating them, or when immutable mode is used. Immutable mode is rejected for a live canonical database.

For this design:
- Do not let the read-only adapter create WAL/SHM sidecars. If the database is in WAL mode and the required sidecars are absent/unreadable, return a distinct fail-closed status such as `WAL_SIDECARS_UNAVAILABLE`.
- The regular canonical host must own startup ordering and writer lifecycle. If a writer connection is required to establish the WAL sidecars before a reader can attach, that is a host lifecycle responsibility and must be covered by separately authorized runtime design/testing; it is not permission for this read-only adapter to create or initialize anything.
- SQLite uses the WAL shared-memory region for reader/writer coordination. Lock acquisition/release may touch transient SHM lock state. Therefore the invariant is: the read-only connection never writes database pages, appends WAL frames, changes schema/data, or creates/deletes sidecars. Do not claim that every byte of the SHM file remains unchanged while a concurrent reader is active; SHM lock coordination is part of normal WAL operation.
- Do not delete, rename, copy, truncate or manually create WAL/SHM files from application code.
- If the WAL mode or sidecar state cannot be established safely, fail closed. Do not switch journal mode to make the reader work.

SQLite WAL readers use a stable snapshot identified by the WAL end mark captured when the read transaction begins; later committed writer frames are invisible to that reader until its transaction ends. All metadata reads must remain on that snapshot.

## SQLite build and version policy

- Pin one upstream SQLite amalgamation release and record upstream source URL, release identifier, source SHA-256, compile options, NDK version, ABIs and resulting native library hashes.
- Minimum runtime SQLite version remains **3.37.0**, matching the existing D5 `pragma_table_list` contract. The bundled engine must be at least this version and kept current through explicit security updates.
- Record `sqlite3_libversion()`, `sqlite3_sourceid()` and `PRAGMA compile_options` at runtime. Fail closed for versions below the floor or missing required compile capabilities.
- Build/package native libraries for the supported app ABIs. Do not silently narrow ABI support; verify APK split/universal packaging policy before implementation.
- Keep canonical schema and migration ownership in Kotlin contracts; native code is a narrow storage/transaction adapter, not a second schema authority.
- Do not add SQLCipher or a second database format as part of this decision.

## Kotlin/JNI boundary (proposed)

Expose a narrow API, conceptually:

```kotlin
interface CanonicalReadSnapshotAdapter {
    fun capture(expectedPath: CanonicalDatabasePath): ReadSnapshotResult
}
```

The implementation owns one native handle for the entire capture. Kotlin receives typed evidence and immutable rows only; it never receives a general-purpose native SQL handle or arbitrary SQL execution method.

Required result statuses include:
- `VERIFIED`
- `MISSING`
- `UNREADABLE`
- `WAL_SIDECARS_UNAVAILABLE`
- `ENGINE_VERSION_UNSUPPORTED`
- `READ_ONLY_ENFORCEMENT_FAILED`
- `READ_TRANSACTION_FAILED`
- `SNAPSHOT_ANCHOR_FAILED`
- `INCOMPLETE_EVIDENCE`
- `SCHEMA_REJECTED`

Evidence must include the engine version/source ID, canonical path identity (without leaking sensitive absolute paths to logs), main database read-only status, transaction mode DEFERRED, same-connection/same-transaction token, successful snapshot-anchor result, journal mode, WAL sidecar availability, fixed query inventory, and schema/migration/D5 digest results.

## Rejected alternatives

| Alternative | Rejection reason |
|---|---|
| Framework `SQLiteDatabase.beginTransactionReadOnly()` | Public API is API 35+, not minSdk 26. |
| AndroidX `SupportSQLiteDatabase.beginTransactionReadOnly()` | Concrete framework implementation uses a compatibility-sensitive reflection path and can fall back to the ordinary transaction path; not accepted without proof. |
| `beginTransactionNonExclusive()` | Not a DEFERRED read-only transaction contract. |
| `beginTransaction()` / EXCLUSIVE | Wrong lock/transaction mode and can interfere with concurrent writers. |
| Raw `BEGIN DEFERRED` via framework `execSQL()` | Does not prove transaction ownership/binding to the same pooled connection used by subsequent queries. |
| `PRAGMA query_only=ON` alone | Connection setting, not a sufficient boundary against later toggling or arbitrary SQL execution. |
| URI `immutable=1` | Not valid for a live database with concurrent WAL writers. |
| Two different SQLite engines for canonical reader and writer | Adds VFS/WAL/locking/version interoperability risk without benefit; one pinned engine is simpler to reason about. |

## Verification plan — not yet run

Implementation must be test-first and separately authorized. Required gates:

### JVM/native contract tests
- Open missing path without creating DB, parent directories, WAL or SHM.
- Existing DB opens with read-only flag only; `sqlite3_db_readonly(main)` is true.
- Every allowed statement passes `sqlite3_stmt_readonly`; write/DDL/PRAGMA assignment statements are rejected before execution.
- DEFERRED transaction begins, a real database-backed anchor read pins the snapshot, and every query uses the same native connection/transaction token.
- Inject failures at open, begin, anchor, prepare, step, row decode, rollback and close; ensure cleanup and no false VERIFIED.
- Verify engine version/source ID/compile options and unsupported-version fail-closed behavior.

### WAL concurrency tests
- Writer commits after reader's snapshot anchor; reader continues seeing the pre-commit snapshot across all later queries.
- A new reader after writer commit sees the new committed state.
- Reader does not append WAL frames or modify main database pages.
- Existing readable WAL/SHM sidecars permit read-only attachment.
- Missing/unreadable required sidecars fail closed; adapter does not create them.
- Multiple readers and a writer obey SQLite snapshot isolation and bounded busy handling.
- Do not assert byte-for-byte SHM immutability while lock coordination is active; verify no sidecar creation/deletion and no DB/WAL data writes by the reader.

### Android device/instrumentation matrix
- API 26 emulator/device (minimum supported).
- API 33 physical Android device (recorded project environment).
- API 35+ device/emulator.
- Each supported ABI used by release builds.
- Verify exact packaged native library hash, actual engine source ID, read-only enforcement, WAL concurrency, no-create behavior, process death cleanup and repeatability.
- Any unsupported device/VFS/filesystem combination returns a typed failure; no fallback to framework transaction modes.

### Acceptance criteria
- All required native/JVM and device tests pass on exact source SHA.
- Same bundled engine is used by canonical writer and reader.
- One DEFERRED snapshot is proven by runtime evidence, not adapter-supplied claims alone.
- No missing DB or sidecars are silently created by the reader.
- No database pages or WAL frames are written by the reader.
- No framework/AndroidX fallback, EXCLUSIVE or IMMEDIATE substitution exists.
- CI artifact includes exact source SHA, native library hashes, test XML/logs and ABI/device matrix.

## Current disposition

**DESIGN: PROPOSED / TECHNICALLY SELECTED. IMPLEMENTATION: NOT AUTHORIZED. RUNTIME: NOT VERIFIED.**

This ADR resolves the API-level design gap but does not promote T0-B or T0-E. No source, dependency, NDK, build configuration, database, device, Feeder, exchange or trading behavior is changed by this decision.
