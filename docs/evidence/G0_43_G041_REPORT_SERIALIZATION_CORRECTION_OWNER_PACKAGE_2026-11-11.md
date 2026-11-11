# G0.43 — G0.41 Report Serialization Correction Owner Decision Package

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Baseline HEAD: `a3ceac0cd4558bd75a5987ab377a9e6e31e7dfc6`  
Type: documentation-only owner decision package  
Disposition: **READY FOR OWNER DECISION — NO WORKFLOW EDIT OR MEASUREMENT AUTHORIZED**

## 1. G0.42 outcome

G0.42 corrected the workflow admission gate and the single approved measurement invocation completed. The exact run:

- Workflow run: [43052908975](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43052908975)
- Job: `130634571198`
- Run attempt: 1; conclusion SUCCESS.
- Measurement checkout: `b337318f0e494f90ae2db0e7c5b711a55eaed3f0`.
- Frozen runner `prepare_preflight(...)` was invoked exactly once.
- 22 fixtures; A-01–A-13 all true; two measurement passes equal; runner internal report readback true; execution trace empty.

However, the single uploaded report artifact is not valid JSON. The workflow writes a literal backslash-n suffix (`5c 6e`) after the JSON object. Strict JSON parsing fails with extra data. The artifact itself was preserved and not modified.

Artifact:
- ID: `13869458648`
- Name: `g041-s1-single-measurement-report`
- GitHub-reported SHA-256: `14655e26eda4452f21e285ad27c7c3027538d4c796aaaa0c607e84bc8d018af2`
- Independently downloaded ZIP SHA-256: exact match.
- Exactly one file in ZIP: `g041-s1-measurement-report.json`.
- Expiry: `2026-11-18T15:53:56Z`.

G0.41 overall disposition: **FAILED / INCOMPLETE — artifact serialization failure after runner invocation**. The G0.42 one-shot authorization is consumed. No retry, rerun, repair or replacement attempt is permitted under G0.42.

Evidence report: `docs/evidence/G0_41_S1_MEASUREMENT_RESULT_ARTIFACT_INVALID_2026-11-11.md`; commit `a3ceac0cd4558bd75a5987ab377a9e6e31e7dfc6`.

## 2. Exact owner decision requested

Approve or reject this indivisible, one-time G0.43 scope:

1. Modify only the existing `.github/workflows/g041-s1-single-measurement.yml`.
2. Amend D14 in `docs/evidence/G0_31_OWNER_RATIFICATION_S1_DECISIONS_2026-11-11.md` for one report-serialization correction and one fresh G0.41 attempt.
3. Bind the one implementation push to exact parent SHA `a3ceac0cd4558bd75a5987ab377a9e6e31e7dfc6`, exact branch, `head_commit.id == github.sha`, and `run_attempt == 1`. Keep the existing exact workflow-path push trigger. Do not add dispatch/schedule/PR/tag/other branch triggers.
4. Keep all three frozen Python source blobs unchanged.
5. If pre-invocation guards pass, execute exactly one call to the existing frozen `prepare_preflight(...)` runner and upload exactly one JSON report artifact (seven-day retention).

No measurement, workflow edit or execution is authorized by this package until separately approved.

## 3. Required serialization correction

The workflow's Python source currently appends a literal two-character sequence `\\n` to the report file. The approved correction must:
- serialize the report object once using `json.dumps(report, sort_keys=True, separators=(",", ":"))`;
- encode UTF-8 and write the exact serialized bytes without appending a literal escape sequence;
- parse the exact bytes back with `json.loads(report_bytes)` before upload;
- require parsed object equality with the original report object;
- reject any trailing non-whitespace data and reject any unexpected report top-level fields;
- upload exactly that validated report file as the sole artifact.

The strict JSON validation must not call `prepare_preflight` again, rebuild fixtures, inspect parser inputs, or create another artifact. It is a report serialization/readback check after the one runner invocation, not a second measurement.

The report must preserve the existing G0.41 fields and provenance, including checkout SHA, four Git blobs, Python version, workflow run/job, 22 fixture measurements, two-pass equality, A-01–A-13, corpus digest, internal readback and empty execution trace. Do not add raw parser inputs, oracle payloads, fixture files, caches or additional artifact files.

## 4. Frozen source and workflow constraints

The three Python source Git blobs must remain exact:

| Path | Required blob |
|---|---|
| `tools/s1_measurement_harness.py` | `e8db71c11e0503ea6d9a2480d75470185c4d5100` |
| `tools/s1_measurement_runner.py` | `23a35aab7f7aeacd8a3f63d630a875fe76b1ff6a` |
| `tools/test_s1_measurement_runner.py` | `d06a5b533af14378ed284051e5b057cf57377876` |

Keep:
- `permissions: contents: read` only;
- existing pinned checkout and upload-artifact actions;
- exact event SHA checkout, shallow clone, `persist-credentials: false`;
- Python 3.14.4, timeout at most five minutes;
- no package installation, secrets, external network, providers, databases, VPS, exchange or market-data access;
- no retry; any run attempt greater than one skips before steps;
- one runner invocation, one JSON report, one artifact, seven-day retention;
- no standalone test suite and no other workflow/CI changes.

## 5. One-shot stop rules

This package requests one fresh attempt because the G0.42 runner completed but its required artifact was malformed.

- Before the runner invocation: any exact-parent, branch, event-head, checkout, runtime or source-blob guard failure means **NOT RUN**. Stop and request a new owner decision; no repair/push under this approval.
- Once the runner invocation begins: any exception, failed assertion, report serialization/readback failure or artifact upload failure consumes the new one-shot authorization and is **FAILED / INCOMPLETE**. No rerun, retry, repair-and-rerun or replacement attempt.
- GitHub rerun attempt greater than one must skip before any step.
- No additional workflow trigger, manual dispatch, schedule, PR, tag, branch or later workflow edit may enter the job.

## 6. Explicit exclusions

Not authorized:
- Changes to harness, runner, focused tests, dependencies, any other workflow or application code.
- More than one `prepare_preflight(...)` invocation.
- Extra artifact, raw parser/oracle/corpus/fixture persistence, caches or diagnostic payloads.
- D11 numeric ceiling proposal, ratification, default or enforcement.
- Parser/verifier production implementation, cryptography, trust/key changes, S2 or executor work.
- T0/T1/T2, canonical market data, model/training, CORE_LEDGER, AI_LEDGER, Shared Risk Engine, Kill Switch, PostgreSQL, VPS/runtime, provider/database/network/exchange or destructive lifecycle operation.

T0 remains independent/protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged. D11 numeric ceilings remain **OPEN / NOT RATIFIED**.

## 7. Owner decision register

| Decision | Requested disposition |
|---|---|
| One report serialization/readback correction in existing workflow | PENDING EXPLICIT APPROVAL |
| Exact-parent guard using `a3ceac0cd4558bd75a5987ab377a9e6e31e7dfc6` | PENDING EXPLICIT APPROVAL |
| Narrow D14 amendment | PENDING EXPLICIT APPROVAL |
| One fresh 22-fixture runner invocation after guards pass | PENDING EXPLICIT APPROVAL |
| One validated JSON report artifact | Included only within approved one-shot attempt |
| Frozen Python source changes | NOT AUTHORIZED |
| Other workflow/CI changes | NOT AUTHORIZED |
| Retry/rerun/second attempt | NOT AUTHORIZED |
| D11 numeric ceilings | OPEN / NOT RATIFIED |
| T0/T1/T2, ledgers, runtime/VPS, external services or destructive operations | NOT AUTHORIZED |

**Current disposition: G0.43 READY FOR OWNER DECISION. No workflow edit, measurement invocation or runtime operation has been performed.**
