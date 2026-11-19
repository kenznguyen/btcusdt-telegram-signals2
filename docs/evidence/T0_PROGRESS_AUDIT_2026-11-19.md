# T0 Progress Audit — 2026-11-19

## Scope and safety

Read-only audit of GitHub repository content, branch refs, source blobs, workflow definitions, recorded evidence and available commit status.

No workflow was dispatched. No tests were run. No VPS/SSH, runtime, SQLite/canonical database, network, exchange, deployment, service, secret, data, schema or trading action was performed. T0 remains independent and protected. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.

## Repository and exact source identity

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Audited branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact branch HEAD: `eb91528bab2b994f283dbe34cd7b0bcbfe406cb5`
- HEAD commit: `docs: update handoff with core-first readiness plan`, 2026-11-12T09:53:41Z.
- Handoff file blob at audited HEAD: `d9d87b4b1198a4b9f73ea8283b829abccb8e296a`.

### Branch divergence — material limitation

GitHub compare, base = audited T0 branch and head = `main`:

- Merge base: `f5b74affb8777953fa66d241784965fbb0e577ba`.
- `main` is 129 commits ahead of the T0 branch.
- The T0 branch contains 3,437 commits not contained in `main`.
- Compare status: `diverged`.

This is not a safe basis for merging the T0 branch into main or assuming that the branch represents current main-line code. The comparison also shows path-level drift, including `market_data/test_write_gateway.py` removed on main while retained on the T0 branch. No merge, rebase, cherry-pick, reset, force-push or branch deletion is recommended in this audit.

## Static source inventory

Exact blobs read from the audited branch:

| Path | Blob SHA |
|---|---|
| `market_data/feeder.py` | `299a9b5a8b1ebd581eb620d5ee860d9f9ff5dc5c` |
| `market_data/storage.py` | `13fe1ae01ebb5318b69e69eef3e512d207f74c49` |
| `market_data/api.py` | `81733c9b6de811cbebb2f5d472d41f37f337990c` |
| `market_data/test_feeder_recovery.py` | `034c9e8f157b0750aaf856c122b00ef96c808ee8` |
| `market_data/test_feeder_lease.py` | `9e3cef256ed55c9784d02e21f9ac30cf723c31b0` |
| `market_data/test_write_gateway.py` | `131880b9110f5bb5780b411d348eae19acb6e14e` |

Static observations:
- SQLite remains the default storage backend; PostgreSQL is opt-in and requires an explicit DSN.
- The API source describes a read-only canonical candle API; ingestion is separate.
- Feeder, lease, recovery and write-gateway test modules are present on this branch.
- These observations prove repository contents only, not that the code was executed successfully or is deployed.

## T0 workflow inventory

Nine T0-related workflow definitions were read at the exact branch ref:

| Workflow | Blob SHA | Static scope |
|---|---|---|
| `t0-manual-validation.yml` | `e298db15ce16f1deb72dbce466513037319b0f6f` | Push + manual gates; isolated lease, recovery, data-flow and G4 contract jobs |
| `t0-binance-connectivity-probe.yml` | `42050b37282d81c21149d3a25d0eb3ba6d99771b` | Offline connectivity contracts; manual dispatch |
| `t0-evidence-contract-g2.yml` | `5e22648c38fd3c6e631f912010de1489bb78f9b5` | Synthetic evidence contract |
| `t0-l4-minimum-validation.yml` | `816e9fefe0784757db13d2c903afc894f62ac97f` | Lineage, manifest, inventory, claim-discipline and aggregate readiness |
| `t0-postgres16-grantor-repro.yml` | `c7bc589ca8240edb25a9c33cce5b9a76e6193271` | Disposable PostgreSQL grantor reproduction |
| `t0-signature-a2-2-stage-i.yml` | `5fa94939181af5f1f33686c3444bc6f8a0326962` | Workflow-dispatch synthetic-only contract tests |
| `t0-single-writer-gateway-red.yml` | `2d836c6c835f414efa62137abf7b97b7bcd6d5ec` | Shadow/write-gateway and related isolated regression jobs |
| `t0-sqlite-readonly-sandbox.yml` | `a41e63cc7581606c6fb1bea264c1340d6448355d` | Disposable systemd/WAL sandbox |
| `t0-systemd-feeder-api-integration.yml` | `64476a3dd281eb69b92d29f3783570107c4ab48e` | Disposable two-service systemd/Feeder/API integration |

### Workflow execution evidence

- Exact-HEAD workflow-run lookup for `eb91528...` returned no PR-associated workflow runs.
- Combined commit status lookup returned an empty status list.
- The available workflow-run lookup is documented as PR-triggered-run-only; an empty response does not prove that no push/workflow-dispatch run exists.
- The 2026-11-12 handoff entry for the Core-First readiness plan explicitly records workflows NOT RUN and no run IDs/artifacts for that documentation-only increment.
- No current exact-HEAD run, job log, artifact ID, artifact digest or artifact payload was verified in this audit.

**Result: workflow definitions inventoried — PASS (static only); latest exact-HEAD CI result and artifacts — NOT VERIFIED.**

## Runtime and canonical data evidence

- The newest specific T0 runtime report located in the audited branch is `docs/evidence/T0_FEEDER_RUNTIME_VERIFICATION_20261109.md`, blob `ef632a53490e85d709026651c0af9a22d28883fb`.
- That report is explicitly **PARTIAL PASS** for observations made on 2026-11-09 and source SHA `9ae2eeae4ece3d657781b68e96b6f4509cd95f24). It records bounded process/lease/restart/coverage observations, while scheduler window completion and full recovery-history coverage remain NOT VERIFIED.
- The report is historical evidence, not proof of current runtime state. The later deployment-parity reconciliation records that the former VPS was deleted on 2026-11-11 and current deployed checkout/process identity was NOT VERIFIED.
- The 2026-11-12 historical-data inventory records no canonical `T0_M15_H1_DATASET_BUNDLE_V1` payload/producer or recoverable raw market-data payload in the inspected GitHub tree/artifacts. Historical ingestion evidence is not an OOS dataset.
- The 2026-11-12 Core-First readiness plan keeps T0 data recovery/re-acquisition as R1, requiring a separate owner decision. It explicitly records T0 reacquisition BLOCKED and runtime paper NOT AUTHORIZED.

## Verdict

| Area | Status | Basis |
|---|---|---|
| Exact branch identity | PASS | Branch ref comparison resolved HEAD SHA |
| Static source inventory | PASS (static only) | Exact blob hashes recorded above |
| T0 workflow definition inventory | PASS (static only) | Nine workflow files read and hashed |
| Latest exact-HEAD CI/jobs | NOT VERIFIED | No PR-associated runs/status; push/dispatch coverage not established |
| Current workflow artifacts | NOT VERIFIED | No current exact-HEAD artifact readback |
| Current VPS/Feeder/API runtime | NOT VERIFIED | No current runtime evidence; historical VPS was deleted |
| Canonical historical data/OOS bundle | BLOCKED | No canonical payload/producer identified in inspected GitHub evidence |
| Production readiness | NOT CERTIFIED | Runtime, current CI evidence and canonical data availability remain unproven |

**Overall T0: PARTIAL / NOT VERIFIED.** The source and workflow inventory is complete for the bounded scope, but this audit does not certify operational readiness, data continuity, current CI health or production readiness.

## Next permitted steps

1. Preserve the audited T0 branch and its history. Do not merge it into main while the 129/3,437 divergence and path drift remain unresolved.
2. Keep runtime, VPS/SSH, canonical SQLite, collection and data export untouched. Any new runtime/data inspection or reacquisition requires a separate bounded owner approval.
3. Before any T0 integration decision, perform a controlled source/path reconciliation against current main and establish which T0 components are still authoritative. Do not silently transplant or delete T0 history.
4. If CI verification is later authorized, run only the selected isolated contract gates against an explicitly recorded exact SHA; capture job logs, source SHA and artifacts. Do not interpret synthetic/disposable tests as canonical-data or runtime proof.
5. Keep T0 independent; no T1 activation, T2 production connection, deployment, exchange order or live trading is authorized by this audit.
