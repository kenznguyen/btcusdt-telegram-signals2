# G0.41 — One-Shot Measurement Result: Artifact Invalid

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

## 1. Exact source and event identity

- G0.42 implementation / measurement checkout SHA: `b337318f0e494f90ae2db0e7c5b711a55eaed3f0`.
- Exact parent SHA: `8f9f854cad4ec460ad10e850613af4d880d0c357`.
- Workflow blob: `5f42799b5b790b3916aea447812dd3f085e1ddf6`.
- D14 ratification blob: `427cd0caccabd5f255029860eab9d49fb43ab6b4`.
- Frozen source blobs:
  - Harness: `e8db71c11e0503ea6d9a2480d75470185c4d5100`.
  - Runner: `23a35aab7f7aeacd8a3f63d630a875fe76b1ff6a`.
  - Focused tests: `d06a5b533af14378ed284051e5b057cf57377876`.
- The three Python blobs were unchanged.

## 2. GitHub Actions execution

- Workflow run: [43052908975](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43052908975).
- Event: `push`; run attempt: 1; run number: 2.
- Head branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Head SHA: `b337318f0e494f90ae2db0e7c5b711a55eaed3f0`.
- Job ID: `130634571198`.
- Run conclusion: **SUCCESS**.
- Job conclusion: **SUCCESS**.
- Completed steps: exact checkout; exact source/branch/runtime guard; one frozen runner invocation; one artifact upload.
- Pre-measurement assertions passed: exact checkout SHA, exact branch, exact event parent, event head equals checkout SHA, run attempt 1, Python 3.14.4, and all three frozen Python Git blobs.

## 3. Runner result

The frozen `tools.s1_measurement_runner.prepare_preflight(...)` was invoked exactly once.

- Fixture count: 22.
- D10 synthetic fixture types: 11.
- Case counts: SYN-01=11; SYN-29=3; SYN-30=2; SYN-31=3; SYN-32=3.
- A-01 through A-13: all 13 assertions true.
- Two independently constructed/measured passes: equal.
- Runner's internal report readback: true.
- Execution trace: no payload persistence events; no external access events.
- Corpus SHA-256: `1c9a302d9df179322bfd7a00aa6db322a66b578a0609b9264481c3801b8a2d94`.

Observed aggregate values:

| Measurement | Observed value |
|---|---:|
| Fixture count | 22 |
| Total raw input bytes | 6,418 |
| Maximum nesting depth | 6 |
| Maximum object members | 8 |
| Maximum array items | 4 |
| Maximum UTF-8 string key bytes | 19 |
| Maximum UTF-8 string value bytes | 100 |
| Scalar nodes | 13 |

These values are recorded as diagnostic measurements only. They do not propose, ratify, or enforce D11 numeric ceilings.

## 4. Artifact verification and defect

Exactly one artifact was uploaded:

- Name: `g041-s1-single-measurement-report`.
- Artifact ID: `13869458648`.
- ZIP size: 1,664 bytes.
- Expiry: `2026-11-18T15:53:56Z`.
- GitHub digest: `sha256:14655e26eda4452f21e285ad27c7c3027538d4c796aaaa0c607e84bc8d018af2`.
- Independent local SHA-256 of downloaded ZIP: `14655e26eda4452f21e285ad27c7c3027538d4c796aaaa0c607e84bc8d018af2` — exact match.
- ZIP contains exactly one file: `g041-s1-measurement-report.json`.

**The report file is not valid JSON.** Its final two bytes are the literal characters backslash and `n` (`5c 6e`), not a newline whitespace byte. Strict JSON parsing fails with `Extra data`. A diagnostic local copy with only those two trailing bytes removed parses successfully and confirms the fields listed in section 3. The artifact itself was not altered, replaced, or re-uploaded.

This defect is in the workflow's report-writing suffix: the generated Python source appends a literal `\\n` sequence instead of an actual newline (or no suffix). The GitHub job still concludes SUCCESS because no strict JSON parser validates the uploaded file.

## 5. Final disposition and one-shot authorization

- Admission correction: PASS.
- Exact source/runtime preflight: PASS.
- Frozen runner invocation: PASS; exactly once.
- Runner internal assertions and readback: PASS.
- Artifact upload: PASS.
- Artifact JSON syntax: **FAIL**.
- Overall G0.41: **FAILED / INCOMPLETE** because the required report artifact is malformed.

The runner invocation has begun and completed; the G0.42 fresh one-shot authorization is therefore consumed. No rerun, retry, workflow edit, repair-and-rerun, second invocation, or replacement attempt is authorized. No further changes are made under G0.42.

A new owner decision package is required before any artifact-serialization correction or subsequent measurement attempt. The current artifact remains preserved as evidence of the failed attempt.

## 6. Unchanged boundaries

D11 numeric ceilings remain **OPEN / NOT RATIFIED**. No parser/verifier production implementation, cryptography, trust/key changes or S2 work. No T0/T1/T2, canonical market data, model/training, CORE_LEDGER, AI_LEDGER, Shared Risk Engine, Kill Switch, PostgreSQL, VPS/runtime, provider, database, external network, exchange or destructive lifecycle action occurred.

T0 remains independent/protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.
