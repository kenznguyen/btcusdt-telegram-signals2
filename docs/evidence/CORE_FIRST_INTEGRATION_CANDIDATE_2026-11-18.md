# Core First Integration Candidate — 2026-11-18

## Candidate identity

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Active branch: `feature/core-operational-proof-20261112`
- Candidate snapshot SHA: `44fe5d2b8d18cbbe2afe21042dbcb49a181eac4a`
- Candidate commit: https://github.com/kenznguyen/btcusdt-telegram-signals2/commit/44fe5d2b8d18cbbe2afe21042dbcb49a181eac4a
- Candidate method: immutable existing branch HEAD; no additional branch or PR created.
- Branch identity check: GitHub compare of `feature/core-operational-proof-20261112` against candidate SHA returned `identical`, ahead 0 / behind 0.
- Candidate snapshot is not a merge commit and does not include main-side changes.

## Scope and source provenance

The candidate SHA is three commits ahead of the previously GREEN-tested code SHA `3fba2a9f72b0d1ab8efad0ced604afe7e8506bc9`. GitHub compare reports exactly four changed paths, all documentation:

| Path | Change |
|---|---|
| `docs/PROJECT_SESSION_HANDOFF.md` | Updated handoff and integration disposition |
| `docs/architecture/CORE_FIRST_ARCHITECTURE_DECISION_2026-11-12.md` | Reconciled decision status/evidence |
| `docs/architecture/CORE_FIRST_READINESS_PLAN_2026-11-12.md` | Reconciled readiness status/evidence |
| `docs/evidence/CORE_FIRST_INDEPENDENT_REVIEW_2026-11-18.md` | Added API deferral follow-up evidence |

No application source, tests, workflow, dependency, schema, or runtime configuration differs between the GREEN-tested code SHA and this candidate snapshot, according to the bounded GitHub commit comparison.

## Existing verification evidence

- GREEN workflow: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/44258935215
- Exact checked-out/tested source SHA: `3fba2a9f72b0d1ab8efad0ced604afe7e8506bc9`
- Workflow conclusion: SUCCESS.
- Artifact: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/44258935215/artifacts/14407801013
- Artifact ID: `14407801013`
- Artifact name: `core-first-code-operational-proof-44258935215`
- Recorded SHA-256: `3c34a50eebff9aa39a1098286f4483ec339cc41b10957eac7856cde589bfa695`
- Common API + Paper Storage regression: 45 tests PASS.
- Full Core-First operational proof: PASS for the exact tested source SHA above.

Important boundary: these workflow results apply directly to SHA `3fba2a9...`, not to candidate SHA `44fe5d2...`. Candidate source-code equivalence is supported by the GitHub compare showing documentation-only changes; a workflow run checking out the exact candidate SHA was NOT RUN / NOT VERIFIED in this step.

## Independent review and integration boundary

- B2 (AI paper submission reachable during Core First): RESOLVED by API guard, regression tests, and GREEN workflow evidence recorded in the independent review follow-up.
- B1 (large branch-history divergence against main): OPEN / MERGE BLOCKED.
- The prior bounded compare recorded main at `6bff2aff91657238297848ef644a0cb4112ab428`, merge base `f5b74affb8777953fa66d241784965fbb0e577ba`, and branch divergence of 4,568 ahead / 85 behind after the handoff commit. Compare metadata is not a complete review of the 85 main-side commits or the merged tree.
- No complete merged-tree validation or independent approval of integration with main is claimed.

## Safety and non-goals

- Strategy Core remains RSI + ADX + Smart DCA and the only paper-executable strategy in this phase.
- AI paper submission remains deferred; `AI_EXECUTION_ENABLED=false`.
- Shared Risk Engine remains the common final risk authority.
- No Dual-Strategy Intelligence implementation.
- No merge, rebase, reset, force-push, default-branch change, deployment, VPS/runtime activation, T0 canonical database access/mutation, exchange connection, or real order.
- Real-market OOS profitability, production readiness, and live-trading readiness remain NOT VERIFIED / NOT AUTHORIZED.

## Candidate disposition

| Gate | Status |
|---|---|
| Candidate SHA identity and active branch match | PASS |
| Source equivalence to GREEN-tested code SHA (docs-only delta) | PASS — bounded GitHub compare |
| Existing Core-First operational CI on ancestor code SHA | PASS |
| CI run on exact candidate SHA | NOT RUN / NOT VERIFIED |
| AI paper-submit deferral (B2) | RESOLVED |
| Full main-side divergence / merged-tree review (B1) | BLOCKED |
| Merge authorization | NOT GRANTED |

Overall: **CONTROLLED CANDIDATE SNAPSHOT CREATED — CONDITIONAL / NOT MERGE-READY**.

## Next permitted step

Run or independently arrange exact-candidate-SHA CI when a supported workflow dispatch path is available, then perform a bounded, auditable review of the 85 main-side commits and merged-tree behavior. Keep the current branch unchanged and do not merge or deploy.

## Follow-up — bounded review of main-side divergence (2026-11-18)

### Exact history inventory

- Current branch HEAD before this follow-up: `ecb8476ab7d1f5c3ed229762632d64445d788734`.
- Main HEAD: `6bff2aff91657238297848ef644a0cb4112ab428`.
- Merge base: `f5b74affb8777953fa66d241784965fbb0e577ba`.
- GitHub compare: branch ahead 4,569 / behind 85; main-side range enumerated from merge base contains exactly 85 commits.
- Commit-message classification of the 85 main-side commits:
  - 57 SSH preflight / PR #140 / retirement / related tests and evidence.
  - 3 T0 signature / A2.2 workflow and contract documentation.
  - 3 Core API / Core operational workflow commits.
  - 4 project handoff, contribution ledger and D01-D14 documentation commits.
  - 3 P1.8/P1.38 audit and traceability commits.
  - 15 other T0/CI/PR evidence and maintenance commits.
- This is a history inventory by commit metadata and bounded path inspection, not a complete semantic review of every commit patch.

### Bounded changed-path disposition

The compare exposes 16 paths. Key dispositions:

1. `pipeline/api.py`: **KEEP FEATURE BRANCH VERSION**. Main blob `fe5b9ffc8a95001f5b1a9734da67a1cb8d23a31b`; branch blob `bb89b0bdf196f64b3ab9d9ac15b6597f333c583e`. Main version uses `MARKET_DATA_DB` as its Paper Ledger path and reads market candles through local `create_store_from_env()`. Branch version requires a separate `PAPER_DB`, validates it is not the T0 SQLite file, and obtains T0 candles through the authenticated HTTP client. Branch version also enforces `AI_PAPER_EXECUTION_DEFERRED` at the API boundary.
2. `core_runtime/api_facade.py`: present on the feature branch (blob `98dfc38008480a5bc686e9f03e4e09041b5ad54e`); GitHub contents lookup on main returned 404. The main-side `core_runtime/test_api_facade.py` imports this module, so main's test/source pairing appears incomplete at the inspected ref. **Do not import main's test file without its implementation and full dependency/path review.**
3. `core_runtime/test_api_facade.py`: both sides contain a test file but different blobs (main `e41f374afee2b3b2be5c70f12c441218367d7f70`; branch `f860d32c4047374dec4f574605a1c1b21ba1a58b`). Branch tests additionally assert T0 HTTP and isolated Paper DB boundaries. Preserve branch version pending complete test diff review.
4. `.github/workflows/core-live-data-operational-proof.yml`: branch blob `0c2d86d76d4d3281e3d7ffb9904a820cf30df547`; main blob `1c0d9e7b6c8355264aa509342175d72931b64cc4`. Both expose `workflow_dispatch`; branch version contains additional path filters and focused Core/Kill Reset contracts. The existing GREEN run validates the branch workflow at its logged exact source SHA, not the main copy.
5. `.github/workflows/t0-manual-validation.yml`: preserve branch version `e298db15ce16f1deb72dbce466513037319b0f6f` over main `e4d5ecc712bf590d5b4f7587fa649cbc94d4f8e2` for its branch-specific automatic SQLite lease/fencing and recovery gates. No T0 runtime was run.
6. T0 Signature workflow was previously confirmed identical in the inspected snapshot; keep Trust Policy A1 separate as DRAFT / contract-only, not implementation approval.
7. Historical SSH preflight/PR #140 commits and evidence are not bulk-imported or discarded by this assessment. Preserve provenance and evaluate their individual applicability separately.
8. Contribution ledger, handoff, historical audit, and T0/T1 evidence documents remain documentation/history items; do not use them to overwrite newer branch evidence.

### Review limits and result

- The 85 commit SHAs/messages were enumerated and grouped. The 16 changed paths were inspected at bounded depth; not every individual commit patch, every historical workflow run, or every merged-tree interaction was reviewed.
- No merged tree was constructed or tested. No source file or workflow was modified in this review.
- Preliminary integration disposition: preserve the feature branch's API, Core facade, facade tests and Core operational workflow; do not bulk-merge the 85 main-side commits.
- Main-side history review: **PARTIAL / NOT MERGE-READY**.
- Branch divergence B1: **OPEN / MERGE BLOCKED**.

### Exact-candidate CI dispatch

- Current branch HEAD at the time of handoff reconciliation: `ecb8476ab7d1f5c3ed229762632d64445d788734`.
- The feature workflow includes `workflow_dispatch`, and main contains the workflow needed to expose the Actions dispatch entry point.
- The connected GitHub action set in this session has no workflow-dispatch operation. No workflow was triggered. CI on the exact current HEAD remains **NOT RUN / NOT VERIFIED**.
- Required owner action: GitHub → Actions → **Core-First code-level operational proof** → Run workflow → select branch `feature/core-operational-proof-20261112`. Confirm the run's checkout/source SHA equals the then-current branch HEAD before treating results as exact-HEAD evidence. If branch HEAD changes before dispatch, use the new SHA and update this record.
- No merge, rebase, reset, force-push, new branch/PR, deployment, runtime activation, canonical T0 access, exchange connection or real order.


## Final source identity check after documentation updates

- Verified current branch HEAD: `8bae34dc8727012ab21b41520cdc99da00b4468a`.
- Verified handoff blob: `ba7c6c1dc6f502be2d1acc9ad4583bdbd5f32347`.
- Verified this evidence report blob before this final note: `7ae2a390d86878458b1512c456f57fcc4a7b204c`.
- Latest compare against main: 4,572 ahead / 85 behind; merge base `f5b74affb8777953fa66d241784965fbb0e577ba`.
- Exact HEAD CI: **NOT RUN / NOT VERIFIED**. No workflow-dispatch action is exposed in the connected GitHub tools. Do not treat the prior GREEN run on `3fba2a9...` as an exact-current-HEAD run.
- Next user action: manually dispatch the existing workflow on `feature/core-operational-proof-20261112`; verify checkout SHA `8bae34dc8727012ab21b41520cdc99da00b4468a` before evaluating PASS.
