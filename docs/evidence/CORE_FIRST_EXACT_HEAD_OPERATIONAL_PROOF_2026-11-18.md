# Core First exact-HEAD operational proof — 2026-11-18

## Scope and provenance

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/core-operational-proof-20261112`
- Tested source SHA: `ea8dc9159782a3da83cab2b84409698922bd281d`
- Workflow: **Core-First code-level operational proof**
- Run: [44272495963](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/44272495963)
- Event / attempt: `workflow_dispatch` / 1
- Workflow result: **SUCCESS**
- Job: `operational-proof`, job ID `134692333311`, **SUCCESS**
- Started: `2026-11-18T09:04:27Z`; completed: `2026-11-18T09:08:23Z`
- Branch ref was independently checked after completion and still pointed to the tested SHA above.
- Artifact: [ID 14413755795](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/44272495963/artifacts/14413755795), `core-first-code-operational-proof-44272495963`
- Artifact size: 19,317 bytes; unexpired at inspection.
- GitHub artifact digest: `sha256:86370ed99fb0895e560d60469334fd5f765c40c10c2ac764912041002e2e09d6`
- Downloaded ZIP SHA-256 independently recomputed: `86370ed99fb0895e560d60469334fd5f765c40c10c2ac764912041002e2e09d6` — **MATCH**.
- ZIP integrity: `unzip -t` completed with no errors; 33 files extracted and inspected.
- Embedded `core-operational-source-sha.txt` matches the workflow branch SHA exactly.

## Workflow and test evidence

All 38 operational steps completed successfully. This includes:

- Isolated disposable paper-only environment enforcement and module compilation.
- Live-data probe, T0/Paper storage isolation, T0 Candle HTTP client and Common API T0 HTTP boundary contracts.
- Dual Ledger bootstrap fixture and Kill Reset RED-to-GREEN regression.
- Common API + isolated Paper storage regressions.
- Strategy Core/signal, Core paper preflight, one-shot runner, runner hardening, continuous cadence, durable journal, orchestration and no-side-effect dry-run contracts.
- Read-only PaperLedger readiness preflight.
- Core decision input bundle validation, normalization, provider orchestration and authoritative Common API facade.
- Continuous Core runtime factory and producer adapter contracts.
- Core-First end-to-end paper operational proof.
- Partial-fill process-crash checkpoint diagnostics and disposable SQLite ledger integration.
- Account-wide risk snapshot read-only/fail-closed verification.
- Shared Risk Engine / Paper Ledger regressions and scoped reservation-expiry ownership.
- T1/T2 order-book contract, HTTP reader and integration tests.
- Exact-SHA evidence publication and artifact upload.

Selected artifact log summaries (each reported `OK`):

| Suite | Tests |
|---|---:|
| Common API + Paper storage | 45 |
| Common API T0 HTTP boundary | 3 |
| T0 Candle HTTP client | 51 |
| Paper storage isolation | 7 |
| Dual Ledger bootstrap fixture | 13 |
| Core strategy | 12 |
| Core runtime contract / preflight | 5 + 5 |
| Core input bundle validator | 19 |
| Bundle normalization / provider | 6 + 6 |
| Continuous Core cadence / journal / runner / dry-run | 5 + 15 + 53 + 10 |
| Core end-to-end operational | 50 |
| Shared Risk / Paper Ledger | 37 |
| T1/T2 order-book | 49 |
| Scoped reservation expiry | 4 |

Other isolated logs in the artifact also report successful test completion. Do not sum suite counts as unique tests: overlap between suites is not excluded, and the partial-fill checkpoint logs include separately recorded checkpoint runs.

## Recorded operational verdict

The artifact's `core-operational-verdict.txt` records:

- `T1_T2_ORDERBOOK_V1=PASS`; 32 tests PASS.
- `T2_ORDERBOOK_HTTP_READER=PASS`; 16 tests PASS.
- `T1_T2_ORDERBOOK_HTTP_INTEGRATION=PASS`.
- `T0_PAPER_STORAGE_ISOLATION=PASS`; 7 tests PASS.
- `SCOPED_RESERVATION_EXPIRY=PASS`; 4 tests PASS.
- `CORE_RUNTIME_PREFLIGHT=PASS`; 5 tests PASS.
- Continuous Core cadence, journal and orchestration: PASS.
- Core runtime one-shot, adapter and input bundle/provider contracts: PASS.
- Core entry paper flow, DCA end-to-end, position and short-position lifecycle: PASS.
- Entry and DCA margin budget each within 1% as recorded by the test evidence.
- Mixed-writer and repeated mixed-writer stress: PASS.

## Safety boundary

Artifact records:

- `PAPER_ONLY=PASS`
- `AI_EXECUTION_ENABLED=false`
- `CANONICAL_T0_TOUCHED=false`
- `EXCHANGE_CREDENTIALS_USED=false`
- `REAL_ORDERS_SENT=false`
- `VPS_OR_PERSISTENT_RUNTIME_USED=false`

The artifact contains test logs and status files only; no raw candle database was uploaded.

## Verdict and limits

- **Exact-current-HEAD CI: PASS** for source SHA `ea8dc9159782a3da83cab2b84409698922bd281d`.
- **Core-First code-level operational proof: PASS** within the workflow's stated test boundary.
- **Artifact payload integrity: PASS** — downloaded ZIP SHA-256 matches GitHub's artifact digest and ZIP integrity test passed.
- This does not establish real-market out-of-sample profitability, production/runtime readiness, live-trading readiness, or permission to execute real orders.
- Branch integration remains **MERGE BLOCKED** pending full semantic review of the divergent main-side history and merged-tree validation. CI success does not authorize merge.
- Dual-Strategy Intelligence remains deferred; AI paper execution remains disabled/deferred.
- No merge, deployment, VPS/runtime activation, canonical T0 mutation, exchange connection, AI execution or real order was performed.

## Next action

Preserve this evidence on the existing branch. Continue the bounded integration review and closeout documentation only. Any merge, runtime activation, Dual-Strategy implementation or live execution requires its own explicit approval gate.
