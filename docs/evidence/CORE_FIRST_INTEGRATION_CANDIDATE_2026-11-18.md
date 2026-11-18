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