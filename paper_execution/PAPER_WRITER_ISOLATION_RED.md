# SWG-F — Paper Writer Isolation RED Contract

Baseline: `a58b6163a78861ecf5bb7d2c8fc11aa420142837`

Phase: SWG-F RED contracts frozen; P1 gate primitive and P2 PaperLedger writer integration implemented. P3/P4 and all T0 code remain outside this scope.

## Required lifecycle

The Paper DB has an independent writer-admission gate. It is not the T0 Lease and does not grant T0 write authority.

States:
- `OPEN`: new Paper writes may enter.
- `DRAINING`: reject new admissions; existing admitted writers may finish.
- `DRAINED`: in-flight writer count is zero and the Paper writer barrier is complete. This state grants no migration permission.
- Reopening is a transition from `DRAINED` to `OPEN` only after the prior operation is explicitly settled; generation advances atomically. `REOPEN` is not a persistent state.

## SWG-F contracts

1. Admission succeeds only in OPEN and returns a unique, generation-bound writer token.
2. Drain atomically closes admission before waiting for in-flight writers.
3. Drain reaches DRAINED only when every admitted writer has exited.
4. Timeout returns a fail-closed result; state remains non-OPEN and no migration permission is granted.
5. A stale token from an earlier generation cannot commit, release another writer, or decrement the current generation's in-flight count.
6. Reopen requires zero in-flight writers and a settled migration outcome; it advances generation so old tokens remain stale.
7. Duplicate release is safe and cannot underflow the in-flight count.
8. The Paper gate is independent of T0 Lease ownership and cannot be used to authorize T0 writes.

## Process-level GREEN acceptance contract (required before P1 completion)

The RED suite above freezes the initial API gaps. Any GREEN implementation must additionally satisfy these cross-process invariants; a thread-only test or process-local mutex is insufficient.

1. **Durable admission ordering**
   - Writer admission acquires the platform lock and, in one coordinator transaction, checks `OPEN` and records its generation-bound token.
   - `begin_drain()` commits `DRAINING` before waiting for the exclusive platform lock.
   - An admission that has not committed its token before `DRAINING` is persisted must be rejected. A writer whose token was committed before `DRAINING` may finish.
   - No admission may touch/create `PAPER_DB` before it has been admitted.

2. **Cross-process barrier**
   - Separate OS processes must hold concurrent writer locks and share the same coordinator state.
   - Drain must not report `DRAINED` while any admitted process retains its lock.
   - After `DRAINED`, a new process must be rejected before opening the Paper DB.
   - Use deterministic IPC barriers/events, not sleep-only timing assertions.

3. **Crash and stale-token recovery**
   - Kill a writer process after admission and before release. The OS must release its lock.
   - A drain process must then acquire the exclusive lock, reconcile orphan token rows and reach `DRAINED`.
   - A serialized/captured old token must not be usable in a new process or after generation advancement.
   - Crash after DB commit but before token cleanup must not leave the gate permanently busy or allow a second commit with the same token.

4. **Timeout and settlement**
   - A bounded drain timeout leaves persisted state `DRAINING`; it never claims `DRAINED` and never reopens automatically.
   - After the writer exits, a later explicit wait may complete the drain.
   - Reopen is denied until `DRAINED`, zero active token rows and an explicit settled outcome (`ABORTED/NOT_STARTED`, `COMPLETED`, or `FAILED_ROLLED_BACK`) are all present.
   - Reopen advances generation atomically; all old tokens remain invalid.

5. **Platform and storage isolation**
   - Exercise the POSIX lock adapter on Linux and verify Android-compatible file-lock behavior; exercise the Windows adapter on Windows. Unsupported/unverifiable locking fails closed.
   - All coordinator and Paper DB tests use unique `TemporaryDirectory` paths. No canonical DB, environment-configured DB, Feeder or exchange endpoint is accessed.
   - Verify the Paper gate cannot authorize T0 writes and T0 lease capability cannot authorize Paper writes.

Required named runtime tests:
- `test_multiprocess_admission_is_atomic_with_drain_transition`
- `test_drain_waits_for_admitted_writer_in_another_process`
- `test_new_process_is_rejected_after_draining_is_persisted`
- `test_sigkill_releases_writer_lock_and_orphan_token_is_reconciled`
- `test_crash_after_commit_before_release_recovers_without_duplicate_commit`
- `test_drain_timeout_remains_draining_until_explicit_wait`
- `test_reopen_requires_settled_outcome_and_advances_generation`
- `test_old_process_token_cannot_commit_or_release_after_reopen`
- `test_denied_admission_does_not_create_or_open_paper_db`
- `test_platform_lock_adapters_fail_closed_when_unsupported`

The ten process-level runtime tests execute P1 gate behavior on Linux using disposable TemporaryDirectory paths and synthetic SQLite data. P2 adds ten PaperLedger tests for side-effect-free construction, explicit schema initialization, same-path/symlink/hardlink protection, environment path revalidation, and mutation admission. P2 routes submit, record_equity, pause/kill/reset and cancel through the gate; read APIs use read-only connections. Android and Windows runtime lock semantics remain NOT VERIFIED. Equity/Risk Control calculations are unchanged; P3 pipeline and broader application integration remain outside scope.


## Test isolation

All P1/P2 acceptance tests use unique temporary Paper DB and coordinator paths. CI leaves database path variables and exchange credentials empty. P2 path identity tests cover normalized equality, symlink, hardlink, and a MARKET_DATA_DB environment change between object construction and explicit initialization. No canonical DB, Feeder, exchange, sync, migration or live order is accessed.

The legacy static RED contract module remains historical evidence and is intentionally excluded from the GREEN regression command because its assertions encode pre-implementation gaps. The shadow-migration contract suite also remains a separate NOT VERIFIED workstream and is not used as a P2 acceptance gate.

## P1 GREEN implementation record

- Implementation: `paper_execution/writer_gate.py`
- Scope: durable Paper-only coordinator SQLite sidecar, platform lock adapter (POSIX shared/exclusive; Windows exclusive serialization), generation-bound non-serializable token, admission/release, drain timeout/wait, explicit settled reopen, and admitted existing-file writer transaction.
- The coordinator and lock files are separate from the Paper DB. Gate initialization/admission do not create or open the Paper data DB.
- P1 runtime acceptance runs on GitHub Actions/Linux. This does not certify Windows or Android runtime lock behavior.
- P2 integrates PaperLedger schema initialization and the known mutator entrypoints with the gate. This does not certify unreviewed external consumers or P3 pipeline integration.
- No canonical T0 DB, Feeder, exchange, market-data sync, migration, deployment, or live order was accessed.
- `ai_execution_enabled=false`; PR remains unmerged.

- P1 runtime suite expanded to 12 named tests, including successful commit and exception rollback through `writer_transaction()`.
- P1 Linux acceptance: 12/12 PASS, 0 failures, 0 errors, 0 skipped on Ubuntu 24.04 / Python 3.12.
- Windows and Android lock-adapter runtime tests remain NOT VERIFIED.

## P2 GREEN PaperLedger integration record

- Constructor is configuration-only: no parent directory, Paper DB, schema or gate sidecar is created.
- Explicit PaperLedger.initialize() creates the Paper DB schema under an admitted Paper writer token.
- PAPER_DB is checked against explicit market_data_db_path or MARKET_DATA_DB environment configuration. Equality, symlink and hardlink aliases are rejected; the identity check repeats immediately before initialization.
- submit(), record_equity(), set_paused(), set_killed(), reset_kill() and cancel() use PaperWriterGate.writer_transaction().
- Read paths use read-only SQLite connections and do not reopen the gate or mutate schema.
- Existing PaperLedger unit tests, explicit local CLI and disposable shadow-migration fixture setup now call initialize() explicitly.
- P2 acceptance: 10/10 tests PASS, 0 failures, 0 errors, 0 skipped on Ubuntu 24.04 / Python 3.12.
- Paper execution regression selection: 56 tests PASS. Intentionally RED SWG-F source contracts and the separate shadow-migration certification suite are excluded and remain separate.
- No canonical T0 DB, Feeder, exchange, migration, deployment, or live order was accessed.
- ai_execution_enabled=false; PR remains unmerged.