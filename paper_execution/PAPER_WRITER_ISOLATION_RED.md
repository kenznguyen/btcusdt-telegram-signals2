# SWG-F — Paper Writer Isolation RED Contract

Baseline: `a58b6163a78861ecf5bb7d2c8fc11aa420142837`

Phase: SWG-F RED contracts frozen; P1 GREEN gate primitive implemented. PaperLedger integration (P2/P3) and all T0 code remain unchanged.

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

All ten named runtime test cases now exist in `paper_execution/test_writer_gate_runtime.py`. The production `paper_execution.writer_gate` module is now implemented for P1. The ten process-level tests execute the gate on Linux using disposable TemporaryDirectory paths and synthetic SQLite data. P1 does not integrate PaperLedger constructors/mutators, Equity, Risk Control, pipeline API, PAPER_DB/T0 path isolation, Android runtime, or Windows runtime; those remain NOT RUN / NOT VERIFIED and require their own implementation slices and evidence.


## Test isolation

The original ten RED contracts inspect source statically. The ten process-level test cases are present, but currently stop at the missing-module assertion before spawning processes or opening their temporary SQLite fixtures. GitHub Actions runs both suites with all database paths and exchange credentials unset. Once the gate module exists under separate approval, the process-level tests must remain restricted to unique temporary databases and synthetic fixtures; no canonical DB, Feeder, or exchange is permitted.

A valid RED is a set of assertion failures proving missing contracts. Syntax/import/infrastructure errors are invalid RED evidence. No GREEN implementation, canonical DB, Feeder, exchange, sync, or live order is authorized by this PR.


## P1 GREEN implementation record

- Implementation: `paper_execution/writer_gate.py`
- Scope: durable Paper-only coordinator SQLite sidecar, platform lock adapter (POSIX shared/exclusive; Windows exclusive serialization), generation-bound non-serializable token, admission/release, drain timeout/wait, explicit settled reopen, and admitted existing-file writer transaction.
- The coordinator and lock files are separate from the Paper DB. Gate initialization/admission do not create or open the Paper data DB.
- P1 runtime acceptance runs on GitHub Actions/Linux. This does not certify Windows or Android runtime lock behavior.
- PaperLedger and other Paper mutation paths are intentionally not integrated in P1; no P2/P3 behavior is claimed.
- No canonical T0 DB, Feeder, exchange, market-data sync, migration, deployment, or live order was accessed.
- `ai_execution_enabled=false`; PR remains unmerged.
