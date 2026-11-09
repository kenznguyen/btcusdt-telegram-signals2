# Stage C.2 — Static Consumer/Dependency Crosswalk and Negative-Vector Test Mapping

Date: 2026-11-10  
Repository: kenznguyen/btcusdt-telegram-signals2  
Branch: feature/t0-centralized-data-feeder-p1-20261101  
Work type: read-only source/test/workflow inspection  
Frozen source commit: d82475036f4bb731ea8ae65a4338d814e2e1399b

## 1. Scope and method

Continued the owner-approved Stage C using read-only GitHub source retrieval and static inspection. Reviewed T0/T1/T2/T3/T4 candidate source paths, synthetic-evidence test modules, P1.8.90/P1.8.94 specifications, the P1.8 synthetic GitHub Actions workflow and CI ownership decision. No code was executed.

This is a source-declared dependency crosswalk, not proof of live runtime consumers or all copies. It does not authorize tests, workflow dispatch, source changes, permission changes, runtime/provider probes or destructive lifecycle operations. Option C remains controlling.

## 2. Exact source and evidence identities

Frozen baseline: commit `d82475036f4bb731ea8ae65a4338d814e2e1399b`.

| Source | Blob SHA |
|---|---|
| P1.8.90 executable negative-case specification | `8014ef15f347d255ee3d02f6f28847a02db27aff` |
| P1.8.94 negative-test traceability | `4588379d8e101ee496bcf8927186c6c989e6c6a6` |
| P1.8.141 lifecycle closure assessment | `c20616d79f6dcedde08128f589a5c0e04d6257f1` |
| P1.8.152 residual reconciliation | `e1a4d95af216e94a58fa5528850fcd0c1ff465f8` |
| P1.8 synthetic workflow | `bbe9361cbbeed4f881edc4ce4fbe727d6937ad78` |
| CI ownership/test denominator decision | `68c14033f32bdd8bbbd675ed58ea8157f95dcb3d` |
| Existing CI policy test | `f5ef5213c8356cacc441b59ec8e1a06ccd4a61da` |
| T0 feeder | `935d295ef42c94482a48ce6ccdc927ebfa4c7e22` |
| T0 storage facade | `13fe1ae01ebb5318b69e69eef3e512d207f74c49` |
| T0 SQLite write gateway | `b2029d9db15fe39dcbe575acfeb6df1b16e16acd` |
| T1 CSV importer | `5effe6540b86edcb190456c95b6bb11456aec099` |
| T2 FreqAI context | `9abe781340dc9b948c40c759d92f340da3e372c1` |
| T3 paper ledger | `0bc94ae0e704a69e253246a575991c1de436e0a4` |
| T3 pure replay reconciliation | `68a59b3938a28055e4d2b27733efcdb643127ea8` |
| T4 dashboard API client | `38cb5a464b05acd77914c7f333d377d8ac0535ad` |
| Synthetic cross-process atomicity tests | `e8907189d522085e2165df7cdc58cb0811d81fe6` |
| Synthetic durability/recovery tests | `593b1daab89d73a94566688cf480930488ab0374` |
| Synthetic event-signature tests | `c55f514f253a47b8dfa570112c99b2e20c1e077d` |
| Synthetic generator tests | `4a0b677b0260d1a167d515ee82de928774149ab4` |
| Synthetic provenance tests | `918636ec161bf8f874cd53009c0eeed07ceee41d` |
| Synthetic reservation lifecycle tests | `bb4772adb89c34e50e2eb7dea489809a96dd2fea` |
| Synthetic shared-risk tests | `a504786ccd0421ab64f58c20fb907acf8b96d250` |
| Synthetic T0 checkpoint contract tests | `beffd8c4a6cb2682c9fe0acb09cd2b182c2fde7c` |
| Synthetic trust-anchor tests | `d60c8c6b691f403442f459b2276b376cc48cda78` |
| Synthetic trust-lifecycle tests | `4ae921f7cea6a5f1752efa1cb197a8d092970821` |
| Synthetic trusted-root pin tests | `08b0d4f7e40f23edd5fe17868985fe4e45d5a905` |
| Synthetic workflow archive-contract tests | `f4f8a7c2c6c0203bf978fd6ebc16579e4b102858` |
| Durable Root B checkpoint tests | `059bcc56efc141ef92721499ab3414fbe4bcef13` |

## 3. Source-declared consumer/dependency crosswalk

| Layer | Producer / persisted surface | Consumer / read path | Static observation | Lifecycle gap |
|---|---|---|---|---|
| T0 | Binance USD-M feeder; fenced SQLite write gateway and lease | Read API/storage facade; T2 HTTP client | Feeder exposes scheduler, recovery, lease and health logic. Gateway validates current lease and writes canonical candles atomically with lease check. Storage facade defaults to SQLite; PostgreSQL is explicit opt-in. | Actual deployed readers, SQLite WAL/SHM, snapshots, filesystem copies, backup/replica/export graph and API client population NOT VERIFIED. |
| T1 | Collector CSV streams | `futures_intelligence/import_collector.py` | Importer reads bounded CSV inputs, validates stream/window/provenance, hashes files and writes a bounded JSON snapshot. | Actual CSV paths/rotation, producer schedules, downstream consumer registry, copied snapshots and external recipients NOT VERIFIED. |
| T2 | T0 candle HTTP contract; T1 intelligence snapshot is a separate input surface | `freqai_bridge/context.py` and exporter | Context obtains a bounded closed M15 window through `CandleHttpClient`; failures are explicit. It writes an inference input artifact. | Runtime model/feature/experiment outputs, training copies, model registry and downstream evidence consumers NOT VERIFIED. |
| T3 | Paper execution state and event/ledger records | `paper_execution/ledger.py`, account history and replay inputs | SQLite paper ledger holds account/strategy state, dual-ledger records, reservations, funding and audit-related data. Read snapshot opens database read-only. | Full deployed DB/copy/backup lineage, every signal-risk-order-fill-reservation dependency and all replay/audit consumers NOT VERIFIED by this static crosswalk. |
| T3 replay | Frozen replay input bundle | `paper_execution/replay_reconciliation.py` | Reconciliation function is pure and replays CORE and AI ledgers separately from supplied inputs. | The input bundle's complete source/copy graph and independent second-root availability are not established here. |
| T4 | API response models and bounded views | `control_dashboard/src/api.js` | Client uses token header, bounded response reading and API fetches. This file alone does not establish every server route or persisted side effect. | Polling-to-server side effects, browser exports/captures, build/deployment copies and operator downloads NOT VERIFIED in this pass. |

This crosswalk names code-level relationships only. It does not establish that any consumer is currently running, nor that the listed paths are exhaustive.

## 4. Existing synthetic tests — relevant but not lifecycle-vector qualification

Inspected test modules show existing synthetic tests in adjacent technical domains:

- Cross-process atomicity: concurrent shared-risk admission, reservation caps, crash-before/after atomic replace, corrupted/missing state fail-closed.
- Durability/recovery: synthetic file-backed risk-state crash points, restart, retry/idempotency and corrupt/missing-state refusal.
- Event signatures: exact-byte Ed25519 signature checks, unknown/expired/revoked key, unknown/unverified revocation and rotation boundary.
- Trust anchor / trust lifecycle / trusted-root pin: attestation subject binding, trusted-root digest pinning, snapshot chain, rotation history, revocation evidence and historical/offline semantics.
- T0 checkpoint contract and Root B checkpoint/store: canonical row encoding, partition completeness, event ACK quorum, durable checkpoint ordering, crash/reopen and tamper rejection.
- Reservation lifecycle/shared risk: concurrent admission, duplicate identity, reservation expiry/release, snapshot restore and CORE/AI shared admission.
- Generator/provenance: deterministic fixtures, replay integrity, fixture/source binding, archive digest and fault-catalog consistency.

These are meaningful tests of their own declared contracts. They do **not** by themselves qualify lifecycle NEG vectors for deletion eligibility, holds, consumer registry completeness, backup/copy lineage, adapter mutation/cascade behavior, independent mutation oracle, authorization races, no-mutation proof or effective GitHub permission enforcement.

### Exact vector mapping finding

P1.8.94 states that the combined catalogue contains **87 unique vector IDs**, all NOT_RUN in that specification. Static text extraction from that file yielded 70 distinct `NEG-*` identifiers; the document's 87-vector denominator is retained as authoritative rather than inferring a reduced denominator from this regex extraction.

No direct executable binding from the inspected synthetic test methods to the lifecycle vector IDs was established. A bounded GitHub code search for representative IDs (NEG-HOLD-01, NEG-ADP-01, NEG-RACE-01, NEG-STATE-10, NEG-INV-01) returned no indexed matches; GitHub code search is not exhaustive for this feature branch, so this is **NOT PROOF OF REPOSITORY-WIDE ABSENCE**.

| Vector group | Related existing tests | Direct lifecycle-vector mapping |
|---|---|---|
| Identity/manifest/authorization/holds/consumer registry | No specific matching lifecycle harness identified in inspected synthetic tests | NOT ESTABLISHED |
| Copy/backup/replica/export/retention floors | No copy-graph or retention-disposition negative harness identified | NOT ESTABLISHED |
| Adapter/cascade/partial mutation/no-mutation proof | Atomicity/recovery tests exercise different shared-risk state, not lifecycle storage adapters | NOT ESTABLISHED |
| Independent verifier/evidence residuals | Provenance and attestation tests cover artifact trust, not independent lifecycle mutation oracle | NOT ESTABLISHED |
| V07 time/revocation | Event signature, trust lifecycle and root pin tests cover some trust/revocation properties; no complete V07 contract qualification | PARTIAL DOMAIN OVERLAP ONLY |
| V08 checkpoint/seal | T0 checkpoint and Root B tests cover selected checkpoint/crash semantics; not full multi-partition watermark/seal/correction contract | PARTIAL DOMAIN OVERLAP ONLY |
| Restore/recovery | File-backed risk and Root B restart tests cover selected synthetic recovery cases; no full recovery-point manifest/oracle/failure-domain rehearsal | PARTIAL DOMAIN OVERLAP ONLY |
| GitHub LDA-08 enforcement | Workflow archive-contract tests assert selected workflow source/ancestry strings; they do not inspect effective repository/branch/environment/runner/OIDC/provider permissions | NOT ESTABLISHED |

**LDA-07 result: NOT RUN. No 87-vector lifecycle suite is evidenced by this static mapping.** No PASS, coverage percentage or execution count is inferred.

## 5. Existing GitHub Actions workflow — execution risk and suitability

The inspected `.github/workflows/p1-8-synthetic-evidence.yml` has:
- push trigger on the current feature branch for synthetic-evidence paths, plus `workflow_dispatch`;
- a synthetic-only preflight and explicit empty database/exchange credential environment variables, with `AI_EXECUTION_ENABLED=false`;
- compile and unittest discovery for `synthetic_evidence/test_*.py`;
- deterministic 1,000-event fixture generation, provenance verification and Sigstore trusted-root/attestation checks;
- `id-token: write` and `attestations: write` on the generator job;
- separate attestation verification job;
- artifact upload with seven-day retention;
- an append-only archive job that commits verified evidence into the repository.

It is a synthetic evidence generator/attestation/archive pipeline, **not a dedicated runner for the 87 lifecycle negative vectors**. Dispatch would retrieve current trust-root material and perform signed/attested evidence and repository archive actions; it is not a read-only inspection. No workflow was dispatched and no Actions run/artifact is claimed.

The existing `ci/test_ci_policy.py` includes a test asserting that no active GitHub Actions YAML exists, while this branch contains 14 workflow YAML files. The CI ownership decision records this as an unresolved policy contradiction and notes legacy Codemagic references. No edit or run was made.

## 6. Stage C.2 disposition

| Workstream | Result |
|---|---|
| RET-09 / LDA-06 | Static code-level crosswalk PARTIAL; runtime and copy completeness NOT VERIFIED |
| LDA-07 | 87-vector spec confirmed; no direct executable mapping established; NOT RUN |
| LDA-08 | Workflow source behavior inspected; effective branch/environment/runner/OIDC/provider permissions NOT VERIFIED; HOLD |
| V07/V08/Restore | Existing tests show adjacent-domain coverage only; qualification remains BLOCKED/NOT VERIFIED |
| Option C | PRESERVED |
| Protected T0, CORE_LEDGER, AI_LEDGER and required T3 evidence | UNCHANGED |

## 7. Execution record and next boundary

- GitHub source/test/workflow fetches and static text inspection: performed.
- Python tests, compile, dry-run or fault injection: NOT RUN.
- GitHub Actions: NOT DISPATCHED; no run ID/artifact.
- Secret values: NOT READ.
- Runtime/VPS/database/storage/provider/Codemagic/recipient/backup/replica probes: NOT PERFORMED.
- GitHub permissions, branch protection, rulesets, environments, runners, OIDC, secrets or credentials: NOT CHANGED.
- Source/schema/API/adapter/workflow/test code/runtime/data: NOT CHANGED.
- Destructive operations: NONE.

### Permission required to close a bounded LDA-08 evidence gap

The GitHub integration's branch-protection endpoint previously returned HTTP 403. The available read-only repository metadata is insufficient to establish effective branch protection. If the owner wants this specific gap resolved, grant the GitHub integration **repository Administration: read-only** (or equivalent read access to branch protection/rulesets) for this repository. Do not grant Administration write, Contents write, Secrets write or Actions write for this inspection. Until then, effective branch protection remains NOT VERIFIED.

Next bounded work, without elevated permission: complete the static path-level consumer crosswalk for remaining candidate modules and prepare a vector-by-vector mapping register using P1.8.90/P1.8.94 identifiers. Any test harness implementation, Actions execution, external/runtime inventory or permission mutation requires a separately scoped authorization and evidence of TEST-01–08 prerequisites.

**Status: STAGE C IN PROGRESS — LDA-06 PARTIAL / NOT VERIFIED; LDA-07 NOT RUN; LDA-08 HOLD / NOT VERIFIED.**
