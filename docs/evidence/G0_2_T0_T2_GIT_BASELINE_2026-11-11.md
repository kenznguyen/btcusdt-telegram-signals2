# G0.2 — T0/T2 Git Baseline and Branch Reconciliation Evidence

- Date: 2026-11-11 (Asia/Ho_Chi_Minh)
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Scope: documentation-only baseline capture, approved by owner on 2026-11-11.
- Source state inspected: branch `feature/t0-centralized-data-feeder-p1-20261101` at `d1978d3606536bb6da2471ed6c94eaf20ffa7b6d`.
- No source code, workflow, test, T0 data, runtime, VPS, deployment, or PR content was changed by this task.

## 1. Exact branch topology

| Ref | Exact SHA | Relationship to merge base |
|---|---|---|
| Active T0/T2 branch `feature/t0-centralized-data-feeder-p1-20261101` | `d1978d3606536bb6da2471ed6c94eaf20ffa7b6d` | 3,015 commits ahead |
| `main` | `063f7a2eacd724f965a9723d0ae66cf95418c0fb` | 76 commits ahead |
| Merge base | `f5b74affb8777953fa66d241784965fbb0e577ba` | Common ancestor |

GitHub compare result for active branch against `main`:
- Status: `diverged`.
- Active branch ahead: 3,015 commits.
- Active branch behind: 76 commits.
- Merge base: `f5b74affb8777953fa66d241784965fbb0e577ba`.

This is a long-lived, materially diverged integration branch. It is not a small feature branch and must not be merged wholesale into `main`. No rebase, merge, reset, cherry-pick, force-push, or branch recreation is authorized by G0.2.

The 76 commits unique to `main` affect 13 paths in the GitHub compare response:
- `.github/workflows/t0-manual-validation.yml`
- `.github/workflows/t0-signature-a2-2-stage-i.yml`
- `ci/test_t0_ssh_preflight_contract.py`
- `docs/PROJECT_CONTRIBUTION_EFFORT_LEDGER.md`
- `docs/PROJECT_SESSION_HANDOFF.md`
- `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A1_2026-11-11.md`
- `docs/evidence/P1_SSH_PREFLIGHT_CONTRACT_RUN_42793921622.md`
- `docs/evidence/PR140_FAIL_CLOSED_PROBE_FIX_20261110.md`
- `docs/evidence/PR140_SOURCE_REVIEW_20261110.md`
- `docs/evidence/T0_SIGNATURE_CONTRACT_FINAL_CONSISTENCY_REVIEW_2026-11-11.md`
- `docs/evidence/T0_T2_DEPLOYMENT_PARITY_EVIDENCE_RECONCILIATION_2026-11-10.md`
- `docs/reviews/t1/P1_38_SECOND_PASS_ADVERSARIAL_REVIEW_P137_2026-11-09.md`
- `ops/ssh/t0-readonly-preflight.sh`

The paths above identify the diff surface, not an approval to copy or merge those changes. Commit-by-commit semantic classification is pending G0.3.

## 2. Handoff freshness

Before this update, `docs/PROJECT_SESSION_HANDOFF.md` declared `f58bf6a203e8dd663003eeff97ad7580dcbb9c57` as the latest repository HEAD. The actual branch HEAD observed for this G0.2 audit was `d1978d3606536bb6da2471ed6c94eaf20ffa7b6d`, a 214-commit / 59-file gap from the declared SHA as recorded in G0.1.

The handoff is being updated in this increment. The final commit SHA containing that update is recorded in the handoff's G0.2 section and in the task completion message. The source SHA above remains the immutable audit starting point; it is not represented as the resulting documentation commit.

## 3. PR #139 — separate SSH passphrase work

- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/139
- State: OPEN / DRAFT / NOT MERGED.
- Head branch: `fix/scaleway-ssh-passphrase-preflight-20261110`.
- Head SHA: `7e635a6462c29456f1adb2e7ddcd01443909a5ac`.
- Base branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Base SHA recorded by PR: `ff1f1768cab1b899494910df1b9ba0d98d35835f`.
- Commits: 7; changed files: 2.
- GitHub mergeable result: `false`.

PR #139 is not representative of the current active branch HEAD. Do not merge, retarget, rewrite, or otherwise alter it as part of G0.2/G0.3.

## 4. Exact-SHA CI evidence

- Query of GitHub Actions runs filtered by exact source SHA `d1978d3606536bb6da2471ed6c94eaf20ffa7b6d`: 0 runs returned.
- Query of commit-associated PR workflow runs for that SHA: 0 runs returned.
- Earlier run `42998929107` checked SHA `fe85a676753aac1ee308c24d4390ea4bac2ec58e`, not the current source SHA; its Repository-file inventory job failed with `GIT_BLOB_SHA_MISMATCH`, while lineage and artifact-manifest jobs succeeded. It cannot be used as an exact-HEAD PASS.
- No workflow was dispatched by G0.2. No workflow run or artifact was produced by this documentation-only increment.

CI status for the inspected source SHA: **NOT VERIFIED** (no exact-SHA run).

## 5. Prior G0.1 findings retained

- Read-only Git history diagnosis: PASS.
- Overall G0: PARTIAL.
- Branch reconciliation: BLOCKED pending classification and owner decision.
- Do not use PR #139 as the active T0/T2 branch baseline.
- Do not merge the active branch wholesale into `main`.
- The 76 `main)-only commits require semantic classification before any integration choice.
- No branch-history mutation was performed.

## 6. Work performed in G0.2

- Captured the exact active branch, `main`, merge-base, ahead/behind counts and diff paths.
- Reconciled PR #139 state and exact refs.
- Queried exact-SHA GitHub Actions metadata.
- Updated the session handoff and added this evidence report on the existing active branch.
- No source/test/workflow changes; no T0/T1/T2 runtime, DB, VPS, data, training, exchange or trading actions.

Verification: documentation content and GitHub metadata only. No automated tests were run because no executable behavior changed. No workflow/artifact was generated.

**G0.2 disposition: PASS — documentation-only baseline recorded.**  
**G0 branch reconciliation: BLOCKED** until G0.3 classifies the 76 `main)-only commits and the owner decides whether any specific changes should be adopted.

## 7. Next step and restrictions

Next: G0.3 read-only semantic classification of the 76 commits unique to `main`, grouped by source/workflow/docs/evidence impact, with exact commit SHAs and overlap/conflict analysis.

Until a separate decision:
- Do not merge, rebase, cherry-pick, reset, force-push, or recreate branches.
- Do not alter PR #139 or T1 PR #1.
- Do not change source code, tests, workflows, CI configuration, T0 canonical data, databases, VPS/runtime, or deployment.
- Preserve paper-only posture and `AI_EXECUTION_ENABLED=false`.
