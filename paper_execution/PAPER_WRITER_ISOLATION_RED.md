# SWG-F — Paper Writer Isolation RED Contract

Baseline: `a58b6163a78861ecf5bb7d2c8fc11aa420142837`

Phase: RED specification only. No production Paper Ledger or T0 code is modified.

## Required lifecycle

The Paper DB has an independent writer-admission gate. It is not the T0 Lease and does not grant T0 write authority.

States:
- `OPEN`: new Paper writes may enter.
- `DRAINING`: reject new admissions; existing admitted writers may finish.
- `DRAINED`: in-flight writer count is zero; migration may proceed.
- `REOPEN`: return to `OPEN` only after migration abort/rollback or successful completion is fully settled.

## SWG-F contracts

1. Admission succeeds only in OPEN and returns a unique, generation-bound writer token.
2. Drain atomically closes admission before waiting for in-flight writers.
3. Drain reaches DRAINED only when every admitted writer has exited.
4. Timeout returns a fail-closed result; state remains non-OPEN and no migration permission is granted.
5. A stale token from an earlier generation cannot commit, release another writer, or decrement the current generation's in-flight count.
6. Reopen requires zero in-flight writers and a settled migration outcome; it advances generation so old tokens remain stale.
7. Duplicate release is safe and cannot underflow the in-flight count.
8. The Paper gate is independent of T0 Lease ownership and cannot be used to authorize T0 writes.

## Test isolation

The tests inspect the source contract statically. They do not import or instantiate runtime services, open SQLite databases, access environment-configured paths, start Feeder, or contact exchanges. Codemagic must run manually with all database paths and exchange credentials unset.

A valid RED is a set of assertion failures proving missing contracts. Syntax/import/infrastructure errors are invalid RED evidence. No GREEN implementation, canonical DB, Feeder, exchange, sync, or live order is authorized by this PR.
