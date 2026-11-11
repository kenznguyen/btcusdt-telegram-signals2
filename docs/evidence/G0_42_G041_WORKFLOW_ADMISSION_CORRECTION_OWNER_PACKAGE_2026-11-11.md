# G0.42 — G0.41 Workflow Admission Correction Owner Decision Package

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Baseline HEAD before this package: `bc40ef62a27548af7dd7804e71ed126d69ad6b73`  
Type: documentation-only owner decision package  
Disposition: **READY FOR OWNER DECISION — NO WORKFLOW EDIT OR MEASUREMENT AUTHORIZED**

## 1. Context and verified failure

G0.41 package was explicitly approved, D14 was amended, and the exact workflow path was added. The first workflow run:

- Run: [43052133091](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43052133091)
- Event: `push`, run attempt 1
- Event checkout SHA: `168d06fbd46348ae23fb21d61e05fb6930c00e10`
- Job: `130631821560`
- Run and job conclusion: `SKIPPED`
- No steps reported; no artifact
- `prepare_preflight(...)`: **NOT INVOKED**

The job-level condition included:
```yaml
if: ${{ github.event_name == 'push' && contains(github.event.head_commit.added, '.github/workflows/g041-s1-single-measurement.yml') && github.run_attempt == 1 }}
```

GitHub's REST commit metadata reports the workflow file as `added`, but the run/job metadata does not expose the evaluated value of each expression. Therefore the precise false sub-expression and root cause are **NOT VERIFIED**. The `contains(github.event.head_commit.added, ...)` clause is a plausible admission-gate fault and should be removed rather than asserted as proven root cause.

## 2. Exact owner decision requested

Approve or reject the following indivisible, one-time correction and fresh-attempt scope:

1. Modify only the existing file `.github/workflows/g041-s1-single-measurement.yml` to replace the current admission condition with an exact-parent guard.
2. Apply one narrow D14 amendment allowing that one correction to the already-approved workflow path and one fresh push-triggered G0.41 measurement attempt.
3. The implementation commit must be the next push after this package and its handoff are recorded. The workflow must admit only a push where:
   - event is `push`;
   - ref is exactly `refs/heads/feature/t0-centralized-data-feeder-p1-20261101`;
   - `github.event.before` equals the exact branch HEAD recorded in the handoff as the immediate parent of the implementation commit;
   - `github.event.head_commit.id == github.sha`;
   - `github.run_attempt == 1`.
4. Keep the existing branch/path trigger, so only a push that modifies this exact workflow file can create a run. Do not use `contains(github.event.head_commit.added, ...)`.
5. Before measurement, assert exact checkout SHA, branch, Python 3.14.4 and the same three frozen source Git blobs.
6. If every pre-invocation guard passes, allow exactly one call to the existing frozen `tools.s1_measurement_runner.prepare_preflight(...)`, with one report-only JSON artifact and seven-day retention.
7. Record the new exact workflow blob, implementation checkout SHA, parent SHA, run/job, report outcome and artifact metadata.

The D14 correction must not change any Python source, dependency, other workflow or application code. No standalone test command may call the measurement runner.

## 3. Admission guard design

The revised job condition should be equivalent to:

```yaml
if: ${{ github.event_name == 'push' && github.ref == 'refs/heads/feature/t0-centralized-data-feeder-p1-20261101' && github.event.before == '<EXACT_HANDOFF_HEAD_SHA>' && github.event.head_commit.id == github.sha && github.run_attempt == 1 }}
```

Replace `<EXACT_HANDOFF_HEAD_SHA>` with the immutable SHA recorded after this package and its handoff have been committed. Do not use a wildcard, branch-tip comparison, `always()`, manual dispatch or an added retry path.

Why this is narrower and more observable:
- The existing workflow `paths` trigger already restricts workflow activation to changes of the exact workflow path.
- The exact `before` SHA limits admission to the single next commit after the owner-decision package/handoff.
- `head_commit.id == github.sha` binds the push event's head to the checked-out event SHA.
- `run_attempt == 1` prevents a GitHub rerun attempt from entering the job.
- Later workflow modifications have a different parent SHA and must skip before any step.

This is a proposed guard design, not a claim about the cause of run 43052133091. If the event does not satisfy the exact parent/head constraints, the job must skip; no fallback expression is allowed.

## 4. Frozen source identities and workflow boundaries

The three Python source blobs must remain exact:

| Path | Required Git blob |
|---|---|
| `tools/s1_measurement_harness.py` | `e8db71c11e0503ea6d9a2480d75470185c4d5100` |
| `tools/s1_measurement_runner.py` | `23a35aab7f7aeacd8a3f63d630a875fe76b1ff6a` |
| `tools/test_s1_measurement_runner.py` | `d06a5b533af14378ed284051e5b057cf57377876` |

Existing workflow baseline blob: `c2b0227429a9858860f7b2aef9a8b94f06bca57c`.

The corrected workflow must preserve:
- `permissions: contents: read` only;
- pinned checkout and upload-artifact actions already present;
- checkout exact `github.sha`, shallow and `persist-credentials: false`;
- Python 3.14.4; timeout at most five minutes;
- no secrets, package installation, network, provider, database, VPS, exchange or market data;
- no retry; `run_attempt != 1` skips before steps;
- one runner invocation, with its two internal deterministic passes;
- one bounded JSON report artifact only; no raw parser inputs, oracle values, fixture files, caches or extra artifacts;
- no standalone test suite in the measurement job.

The workflow must not be modified to weaken or bypass any frozen source check or report assertion.

## 5. Measurement contract retained without change

If preflight succeeds, the one call must use actual checked-out bytes for the frozen harness and runner, recompute their SHA-256 values, bind the exact checkout SHA as both source and expected source commit, and record the exact command.

The runner's existing 22-fixture synthetic recipe, 11 D10 types, five SYN case IDs, D05 checks, two deterministic construction/measurement passes, A-01–A-13 assertions and report readback remain unchanged. The result must fail closed if any assertion is absent/false or any trace is non-empty.

The report artifact may contain the bounded measurement rows/aggregates, corpus digest, provenance, assertion results, readback status and empty execution trace. It must not contain payload bytes or oracle metadata.

## 6. One-shot and stop rules

This is a request for one fresh measurement attempt because the previous attempt never entered the job and never invoked the runner.

- Before the runner invocation: any checkout, parent/head, branch, runtime or source-blob guard failure means **NOT RUN**; stop and request another owner decision. Do not repair or push again under this approval.
- Once the runner invocation begins: any exception, failed assertion, mismatch, report failure or artifact failure consumes this fresh one-shot authorization and results in **FAILED/INCOMPLETE**. No rerun, retry, repair-and-rerun or replacement attempt.
- GitHub rerun attempt greater than 1 must skip before any step.
- No manual dispatch, schedule, PR, tag, other branch or later workflow modification may enter the job.
- If the exact-parent guard cannot be implemented or verified, stop before measurement and return to owner.

## 7. Explicit exclusions

Not authorized:
- Any change to harness, runner, focused tests, dependencies or files other than the existing workflow and the D14 ratification record required for this exact correction.
- Any additional workflow, broad CI change, secret, write permission, deployment, package installation or external access.
- More than one call to `prepare_preflight`, any standalone test run that calls it, retries or reruns.
- Additional artifacts or persistence of raw parser/oracle/corpus/fixture bytes.
- Numeric D11 ceiling proposal, ratification, default, enforcement or diagnostic-output dimension invention.
- Production parser/verifier, crypto/trust, S2 or executor work.
- T0/T1/T2, canonical market data, model/training, CORE_LEDGER, AI_LEDGER, Shared Risk Engine, Kill Switch, PostgreSQL, VPS/runtime, provider, database, external network, exchange or destructive lifecycle operation.

T0 remains independent/protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged. D11 numeric ceilings remain **OPEN / NOT RATIFIED**.

## 8. Owner decision register

| Decision | Requested disposition |
|---|---|
| One edit to existing G0.41 workflow admission condition | PENDING EXPLICIT APPROVAL |
| Exact-parent/head/branch/run-attempt guard | PENDING EXPLICIT APPROVAL |
| Narrow D14 amendment for one correction and one fresh attempt | PENDING EXPLICIT APPROVAL |
| One fresh 22-fixture measurement invocation after guards pass | PENDING EXPLICIT APPROVAL |
| One report-only JSON artifact | Included only within the approved one-shot attempt |
| Frozen Python source changes | NOT AUTHORIZED |
| Other workflow/CI changes | NOT AUTHORIZED |
| Retry/rerun/second fresh attempt | NOT AUTHORIZED |
| D11 numeric ceilings | OPEN / NOT RATIFIED |
| T0/T1/T2, ledgers, runtime/VPS, providers, databases, external network or destructive operations | NOT AUTHORIZED |

**Current disposition: G0.42 READY FOR OWNER DECISION. No workflow edit, measurement invocation or runtime operation has been performed in this milestone.**
