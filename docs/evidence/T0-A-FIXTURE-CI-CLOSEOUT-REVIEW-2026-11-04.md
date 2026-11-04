# T0-A — Fixture CI Closeout Review

## Decision
**PASS — T0-A fixture and static-contract CI closeout only.** This does not close P1/T0 as a deployed Data Foundation.

## Review basis
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Active branch: `feature/p5-4-1-post-merge-validation-20261103`
- Tested source SHA: `81252f3e954216d638d3655623d765c38b6f960b`
- T0 workflow: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41747057849 — SUCCESS.
- Integrated workflow: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41747057869 — SUCCESS, 5/5 jobs.
- Detailed P5.4.63 evidence: [P5.4.63 report](P5.4.63-RECOVERY-COORDINATOR-PARTIAL-WINDOW-RETRY-2026-11-04.md).

## Coverage review

| Contract area | Source evidence | Review |
|---|---|---|
| Scheduler / candle closure | `test_feeder_scheduler.py` — 15 methods | PASS in T0 CI |
| Retry / backoff | `test_feeder_retry.py` — 12 methods | PASS in T0 CI |
| Recovery planning and coordinator | `test_feeder_recovery.py` — 22 methods | PASS in T0 CI; includes malformed snapshots, overlap, partial progress, callback failure, retry and final recheck |
| Lease / generation fencing | `test_feeder_lease.py` — 11 methods; `test_feeder_atomic_fencing.py` — 9 methods | PASS in T0 CI |
| Health / readiness | `test_feeder_health.py` — 11; `test_feeder_health_api.py` — 9; `test_feeder_health_runtime_api.py` — 6 | PASS in T0 CI |
| Lifecycle / restart contracts | `test_feeder_lifecycle.py` — 23 methods; `test_feeder_sigkill_recovery.py` — 1 method | PASS in T0 CI; isolated fixture only |
| Gateway transaction boundary | `test_gateway_runtime.py` — 16 methods | PASS in T0 and integrated G1 |
| Static source and CI policy | `ci.test_t0_operational_contract` — 11 checks; `ci.test_ci_policy` | PASS in T0 and integrated G2 |

The ten feeder regression modules contain 119 test methods. The three CI regression invocations report 112 / 119 / 113 tests; they overlap and must not be added together. The standalone T0 run confirms all three counts and the static operational audit. Integrated G1/G2/T0 and combined publication also pass on the same SHA.

## Gateway and fail-closed review
- Gateway tests cover valid lease commit, expired lease, wrong owner, stale generation, takeover ordering, invalid candle rejection, SQL rollback, duplicate replay/conflict, unavailable DB no-create behavior, side-effect-free constructor/read, empty batch no-op and lease expiry at final admission.
- Atomic fencing tests cover stale/expired/missing lease rejection, same-transaction lease validation and batch write, rollback, takeover serialization and fenced recovery sync.
- Runtime health/readiness tests keep startup, incomplete recovery, storage failure, lost lease and stale generation from becoming ready.
- RecoveryPlanner/RecoveryCoordinator tests reject malformed/contradictory/overlapping snapshots and do not report complete while gaps remain.
- Static operational audit checks GitHub Actions registration, source-SHA provenance, release-gate boundaries, manual-only gates, Codemagic retirement, canonical closed-candle source, concrete Gateway boundary, separated observation/lease clocks and fail-closed SQLite runtime storage.
- These are source and fixture CI proofs. They do not prove production process wiring or actual writes to the future canonical PC database.

## CI isolation and provenance
- T0 runner has canonical DB, lease DB, paper DB and exchange credential environment variables empty; `AI_EXECUTION_ENABLED=false`.
- T0 standalone run 41747057849 completed all 19 substantive steps.
- Integrated run 41747057869 completed preflight, G1, G2, T0 and combined publication (5/5).
- Exact source SHA `81252f3e954216d638d3655623d765c38b6f960b` is present in the workflow/job evidence.
- Artifact IDs and GitHub metadata digests are recorded in the P5.4.63 report. Payload-byte SHA-256 recomputation was not performed; it remains NOT VERIFIED.

## Documentation correction
- `docs/T0_FEEDER_TEST_CONTRACT.md` has been aligned to GitHub Actions, current test inventory, exact-SHA evidence and present gate boundaries.
- Its earlier Codemagic verification instructions were stale and are superseded. Codemagic is not a T0 runner.

## Remaining T0 gates

| Gate | Status | Why |
|---|---|---|
| T0-A — fixture contracts, static audit and GitHub Actions evidence | **PASS** | Exact-SHA T0 + integrated workflow succeeded |
| T0-B — Windows PC canonical path and SQLite integrity | **BLOCKED / DEFERRED** | PC use is currently deferred; canonical path is not selected |
| T0-C — controlled Feeder runtime acceptance | **NOT RUN** | No PC deployment, production composition, lease/runtime start, M15/H1 ingestion or restart test |
| T0-D — production backup/restore and continuity | **NOT RUN / NOT VERIFIED** | No canonical database or production backup/restore exercise |
| T0-E — overall T0 acceptance / P1 close | **BLOCKED** | Requires T0-B through T0-D evidence |

## Approved storage target and current constraint
The recorded target is Windows PC + SQLite, with the Lease in the same physical database and daily backup. The canonical filesystem path remains undecided. The user has deferred PC use for now; this review therefore does not inspect or create any PC database.

## Next permitted action
When PC use is explicitly reopened, resolve the canonical path and perform a read-only storage identity/integrity preflight before any Feeder startup. Do not start the Feeder, connect an exchange, sync market data, or create/modify the canonical DB as part of that preflight without separate authorization.

## Safety boundary
Paper/signals only. No live orders or exchange execution. Keep `AI_EXECUTION_ENABLED=false`. No PC, canonical DB, production Feeder, exchange or market-data sync was used for this review.
