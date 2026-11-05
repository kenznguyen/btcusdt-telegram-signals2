# SWG-F — Paper Writer Isolation RED Contract

Baseline: `a58b6163a78861ecf5bb7d2c8fc11aa420142837`

Phase: RED specification only. No production Paper Ledger or T0 code is modified.

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
   - Writer admission acquires the platform lock and, in one coordinator transaction, checks \`OPEN\` and records its generation-bound token.
   - \`begin_drain()\` commits \`DRAINING\` before waiting for the exclusive platform lock.
   - An admission that has not committed its token before \`DRAINING\` is persisted must be rejected. A writer whose token was committed before \`DRAINING\` may finish.
   - No admission may touch/create \`PAPER_DB\` before it has been admitted.

2. **Cross-process barrier**
   - Separate OS processes must hold concurrent writer locks and share the same coordinator state.
   - Drain must not report \`DRAINED\` while any admitted process retains its lock.
   - After \`DRAINED\`, a new process must be rejected before opening the Paper DB.
   - Use deterministic IPC barriers/events, not sleep-only timing assertions.

3. **Crash and stale-token recovery**
   - Kill a writer process after admission and before release. The OS must release its lock.
   - A drain process must then acquire the exclusive lock, reconcile orphan token rows and reach \`DRAINED\`.
   - A serialized/captured old token must not be usable in a new process or after generation advancement.
   - Crash after DB commit but before token cleanup must not leave the gate permanently busy or allow a second commit with the same token.

4. **Timeout and settlement**
   - A bounded drain timeout leaves persisted state \`DRAINING\`; it never claims \`DRAINED\` and never reopens automatically.
   - After the writer exits, a later explicit wait may complete the drain.
   - Reopen is denied until \`DRAINED\`, zero active token rows and an explicit settled outcome (\`ABORTED/NOT_STARTED\`, \`COMPLETED\`, or \`FAILED_ROLLED_BACK\`) are all present.
   - Reopen advances generation atomically; all old tokens remain invalid.

5. **Platform and storage isolation**
   - Exercise the POSIX lock adapter on Linux and verify Android-compatible file-lock behavior; exercise the Windows adapter on Windows. Unsupported/unverifiable locking fails closed.
   - All coordinator and Paper DB tests use unique \`TemporaryDirectory\` paths. No canonical DB, environment-configured DB, Feeder or exchange endpoint is accessed.
   - Verify the Paper gate cannot authorize T0 writes and T0 lease capability cannot authorize Paper writes.

Required named runtime tests:
- \`test_multiprocess_admission_is_atomic_with_drain_transition\`
- \`test_drain_waits_for_admitted_writer_in_another_process\`
- \`test_new_process_is_rejected_after_draining_is_persisted\`
- \`test_sigkill_releases_writer_lock_and_orphan_token_is_reconciled\`
- \`test_crash_after_commit_before_release_recovers_without_duplicate_commit\`
- \`test_drain_timeout_remains_draining_until_explicit_wait\`
- \`test_reopen_requires_settled_outcome_and_advances_generation\`
- \`test_old_process_token_cannot_commit_or_release_after_reopen\`
- \`test_denied_admission_does_not_create_or_open_paper_db\`
- \`test_platform_lock_adapters_fail_closed_when_unsupported\`

These runtime tests do not exist in the current RED branch yet. Their names are acceptance requirements, not a claim that they have run. Do not add a runtime implementation in this RED-only PR.


## Test isolation

The frozen RED tests inspect the source contract statically. They do not import or instantiate runtime services, open SQLite databases, access environment-configured paths, start Feeder, or contact exchanges. GitHub Actions runs the static contract workflow with all database paths and exchange credentials unset. Process-level runtime acceptance is a separate future test suite and must use temporary databases and synthetic fixtures only.

A valid RED is a set of assertion failures proving missing contracts. Syntax/import/infrastructure errors are invalid RED evidence. No GREEN implementation, canonical DB, Feeder, exchange, sync, or live order is authorized by this PR.
