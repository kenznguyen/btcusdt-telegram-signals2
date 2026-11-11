# G0.4 — Main-only Delta and Repository Topology Refresh

- Date: 2026-11-11 (Asia/Ho_Chi_Minh)
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Active branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Default branch: `main`
- Work type: read-only topology/evidence reconciliation followed by documentation-only recording
- Owner authorization: explicit approval in conversation on 2026-11-11 for documentation-only G0.4; no source/runtime/branch integration
- Baseline active branch HEAD: `ba8569e704fc256b7743abf0163116878e06e89c`
- Baseline `main` HEAD: `b9b938b4c78f143ca63330d047a8a799ef450a13`
- Merge base: `f5b74affb8777953fa66d241784965fbb0e577ba`

## 1. Current branch topology

GitHub compare was run with `base=main` and `head=feature/t0-centralized-data-feeder-p1-20261101`.

- Status: **DIVERGED**.
- Active branch ahead of `main`: **3,215 commits**.
- Active branch behind `main`: **82 commits**.
- Merge base: `f5b74affb8777953fa66d241784965fbb0e577ba`.
- The current comparison reports a large, material change surface across workflows, Python, Android, dashboard, docs, tests and operational tooling. It is not safe to infer merge readiness from commit counts or file-path presence.

Historical G0.3 checkpoint:
- Active branch HEAD: `b06111235f8830676433b3a1279de65bc09b3c75`.
- `main` HEAD: `063f7a2eacd724f965a9723d0ae66cf95418c0fb`.
- At that checkpoint, 76 commits were unique to `main`; the G0.3 report classified all 76.
- The current `main` has advanced by exactly six commits from the G0.3 `main` checkpoint. The six-commit compare returned `ahead=6`, `behind=0`, `total=6`.

## 2. Six-commit main-only delta after G0.3

The following six commits are the complete delta between the G0.3 `main` checkpoint and current `main` HEAD. Their subjects and file-level diffs were read from GitHub.

| Commit | Subject / classification | Changed path |
|---|---|---|
| `88c83ae69024369c8894da367a1ff006cfcdfac2` | Retire SSH Preflight workflow jobs/triggers | `.github/workflows/t0-manual-validation.yml` |
| `8571261993ba9050ea18be566f967d9cd59f9aad` | Remove retired SSH Preflight script | `ops/ssh/t0-readonly-preflight.sh` |
| `a4e3a625c84dcc2130f1642b6e2abf60aef66384` | Remove retired SSH Preflight contract tests | `ci/test_t0_ssh_preflight_contract.py` |
| `5a950eeaf7b2bf138774cfad3b7daa18c884a0e7` | Add SSH Preflight retirement evidence | `docs/evidence/SSH_PREFLIGHT_RETIREMENT_2026-11-11.md` |
| `7021e0e1a7183c201652a0168eaffc4deb798f10` | Update controlling handoff for retirement | `docs/PROJECT_SESSION_HANDOFF.md` |
| `b9b938b4c78f143ca63330d047a8a799ef450a13` | Add D01–D14 closure/S2 readiness audit | `docs/evidence/G0_52_D01_D14_CLOSURE_AUDIT_AND_S2_READINESS_2026-11-11.md` |

### Semantic reconciliation

- The first three commits retire repository-managed SSH Preflight implementation and its dedicated contract test/workflow surface.
- The next two commits preserve the retirement decision/evidence and update the handoff.
- The final commit records the G0.52 D01–D14 documentary audit. Its disposition is audit PASS, but S2 remains BLOCKED / NOT READY and no implementation is authorized.
- This is a classification of the six-commit delta, not a full code review or a recommendation to cherry-pick any commit.

## 3. Active-branch retirement readback

Exact-path reads on the active branch at `ba8569e704fc256b7743abf0163116878e06e89c` established:

- `ops/ssh/t0-readonly-preflight.sh`: absent (GitHub contents API 404).
- `ci/test_t0_ssh_preflight_contract.py`: absent (GitHub contents API 404).
- `.github/workflows/t0-manual-validation.yml`: blob `eda43deee000f138690b1a15c8db46dd2fe97d99`; no SSH Preflight/script/test references found in the fetched content.
- `docs/evidence/SSH_PREFLIGHT_RETIREMENT_2026-11-11.md`: present, blob `b0320bf7e0cfec7c27384b432c55ba4293e5f216`.
- `docs/evidence/G0_52_D01_D14_S2_READINESS_AUDIT_RECORD_2026-11-11.md`: present, blob `9e716bd4903892ec338c37b6c59987204d42f6b4`.

Disposition: active-branch source/path readback for the retired feature **PASS**. This does not establish Actions execution, runtime/VPS state, or any deployment behavior.

## 4. PR and issue snapshot

Read-only GitHub search snapshot:

- Open PRs: **39**.
- Open Draft PRs: **39**.
- Open issues: **2**.
- Issue #138: T1 P1.42 independent adversarial review / fixture traceability blocker.
- Issue #91: five-layer control-plane Dashboard integration.
- PR #139: CLOSED / NOT MERGED.
- PR #144: MERGED into `main`; subsequent repository-wide SSH Preflight retirement is recorded separately.

This is an inventory count, not an approval to merge, close, retarget, rebase or delete any PR/branch. Individual PR source compatibility and mergeability remain separate questions.

## 5. Evidence source pins

Exact active-branch file readbacks used for this reconciliation:

| Path | Git blob SHA |
|---|---|
| `docs/PROJECT_SESSION_HANDOFF.md` | `deb153d1da26d854d87db843664cf79b3253923a` |
| `docs/COMPLETE_ROADMAP.md` | `4a66ccb1cda3805ea0f0b716e1e4f4708a947e51` |
| `docs/evidence/G0_3_MAIN_ONLY_76_COMMITS_CLASSIFICATION_2026-11-11.md` | `29fd346a980a4d67dfd2f23211cea0f04e338b60` |
| `docs/evidence/SSH_PREFLIGHT_RETIREMENT_2026-11-11.md` | `b0320bf7e0cfec7c27384b432c55ba4293e5f216` |
| `docs/evidence/G0_52_D01_D14_S2_READINESS_AUDIT_RECORD_2026-11-11.md` | `9e716bd4903892ec338c37b6c59987204d42f6b4` |
| `docs/evidence/T0_L4_MINIMUM_AUTOMATION_PLAN_2026-11-10.md` | `5d8f59074334e2540d3b96f7704434abf90db11b` |
| `docs/evidence/T0_L4_MINIMUM_NINE_CONTROL_EVIDENCE_ACQUISITION_REGISTER_2026-11-10.md` | `56f36428375527e5f421543b815177449435ce51` |

The Evidence Register and Automation Plan report the current L4 source inventory as a bounded 40-file repository-source inventory, with reference reconciliation PARTIAL PASS. The aggregate L4-Minimum remains BLOCKED / NOT VERIFIED; the inventory does not promote any control or establish owner custody, signer separation, authenticated freshness, offline verification or L4M-10 acceptance.

## 6. Documentation reconciliation findings

1. The active branch already contains the SSH Preflight retirement result, but the G0.3 report remains a historical snapshot at the earlier 76-commit checkpoint. Preserve it unchanged and record this delta in G0.4.
2. The roadmap Evidence Index currently names the G0.52 audit using an incorrect filename. The exact existing path is `docs/evidence/G0_52_D01_D14_S2_READINESS_AUDIT_RECORD_2026-11-11.md`. G0.4 corrects only this reference.
3. The roadmap's old branch divergence figures and statement that a complete PR inventory has not yet been produced are stale. G0.4 records the current exact compare and aggregate PR/issue counts, without asserting integration readiness.
4. Handoff L4 evidence records and Automation Plan/Register agree that the 40-file inventory is bounded and reference reconciliation is PARTIAL PASS. No L4 control or aggregate status is promoted.

## 7. Disposition and verification

| Check | Result |
|---|---|
| Exact six-commit delta from G0.3 `main` checkpoint | **PASS — 6/6** |
| Six-commit semantic classification and changed-path mapping | **PASS — 6/6** |
| Active-branch SSH Preflight exact-path/workflow readback | **PASS** |
| Current branch topology | **DIVERGED — integration BLOCKED** |
| PR/issue inventory counts | **PASS — 39 open Draft PRs / 2 open issues at query time** |
| L4 reference reconciliation | **PARTIAL PASS** |
| Aggregate L4-Minimum | **BLOCKED / NOT VERIFIED** |
| S2 implementation readiness | **BLOCKED / NOT READY; NOT AUTHORIZED** |
| Source tests, compile, CI/workflow | **NOT RUN** |
| Runtime/VPS/database/T0/T1/T2/trading | **NOT PERFORMED** |
| Independent reviewer assurance | **NOT CLAIMED; mandatory independent review gate remains waived** |

## 8. Non-authorizations

This increment does not authorize or perform branch merge/rebase/cherry-pick/reset/force-push, branch deletion, PR closure, source/workflow/test changes, S2 implementation, key/trust/provider operations, T1 activation, PostgreSQL canonical migration, AI model training, strategy/risk/ledger changes, VPS provisioning or runtime work, data cleanup/deletion, exchange connectivity, live trading or real orders.

Preserve T0 as an independent canonical data foundation, separate CORE_LEDGER and AI_LEDGER, paper-only posture, and `AI_EXECUTION_ENABLED=false`.

## 9. Next permitted step

Keep the active branch and current divergence intact. The next safe increment is a separately scoped read-only review of the highest-priority integration candidate(s), starting with the T0/T2 branch compatibility and PR dependency graph. No integration operation is permitted until the exact target, source SHAs, tests, evidence and Owner decision are recorded.
