# G0.43 — G0.41 Report Serialization Correction Results

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

## 1. Exact source and authorization

- G0.43 implementation / measurement checkout: `93ac905a3b8afb5bebb7c841140c0bccb9f1a47c`.
- Exact parent / event-before: `66a2f9fc70c09ffbe073dfc98acfb500df5aeb42`.
- Workflow blob: `dcfcb09f865ddfc280a4c7368f5ba68036ad9bac`.
- D14 amendment blob: `c9793430e8a92f66ad1fa3d783cade5ff5481104`.
- Frozen Python blobs unchanged:
  - Harness `e8db71c11e0503ea6d9a2480d75470185c4d5100`.
  - Runner `23a35aab7f7aeacd8a3f63d630a875fe76b1ff6a`.
  - Tests `d06a5b533af14378ed284051e5b057cf57377876`.

## 2. GitHub Actions

- Run [43053648998](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43053648998), run number 3, push event, attempt 1.
- Job `130637223760`.
- Run/job conclusion: **SUCCESS**.
- Exact checkout, exact parent, branch, event head, Python 3.14.4 and all three frozen source blob assertions passed.
- Frozen `prepare_preflight(...)` invoked exactly once.
- One artifact upload step completed successfully.

## 3. Strict JSON artifact verification

- Artifact: `g041-s1-single-measurement-report`.
- Artifact ID: `13870492247`.
- ZIP size: 1,661 bytes.
- Expiry: `2026-11-18T15:58:31Z`.
- GitHub digest: `sha256:4cdefc2ed049bd49b1092fb8cf113f92b411c08281f9f7c8db0137e36a85fcca`.
- Independently downloaded ZIP SHA-256: `4cdefc2ed049bd49b1092fb8cf113f92b411c08281f9f7c8db0137e36a85fcca` — exact match.
- ZIP member inventory: exactly one file, `g041-s1-measurement-report.json`.
- Strict `json.loads(raw_bytes)`: PASS.
- Exact expected top-level field inventory: PASS (13 fields).
- Persisted file ends with the JSON closing byte; no literal backslash-n suffix or trailing non-whitespace data.
- JSON object readback and report assertions: PASS.

## 4. Measurement results

- Fixture count: 22.
- Synthetic D10 fixture types: 11.
- Case counts: SYN-01=11; SYN-29=3; SYN-30=2; SYN-31=3; SYN-32=3.
- A-01 through A-13: 13/13 true.
- Measurement pass 1 equals pass 2.
- Runner internal report readback: true.
- Execution trace: payload persistence events empty; external access events empty.
- Corpus SHA-256: `1c9a302d9df179322bfd7a00aa6db322a66b578a0609b9264481c3801b8a2d94`.

Observed diagnostic aggregates (not yet ratified as D11 ceilings):

| Measurement | Observed |
|---|---:|
| Total raw parser-input bytes | 6,418 |
| Maximum nesting depth | 6 |
| Maximum object members | 8 |
| Maximum array items | 4 |
| Maximum UTF-8 string key bytes | 19 |
| Maximum UTF-8 string value bytes | 100 |
| Scalar nodes | 13 |

## 5. Disposition

- G0.43 workflow correction: **PASS**.
- Exact-parent/source/runtime admission: **PASS**.
- One frozen measurement invocation: **PASS**.
- Report serialization and persisted-byte readback: **PASS**.
- Artifact integrity (ZIP digest and one-file inventory): **PASS**.
- G0.41 single synthetic measurement: **PASS for this bounded measurement contract**.
- D11 numeric ceilings: **OPEN / NOT RATIFIED** pending a separate measured-limit proposal/decision step. Observed maxima above are not enforcement limits.
- Repo-wide tests, production parser/verifier implementation, runtime deployment and broader T0/T1/T2 certification are not covered.

No T0/T1/T2, canonical market data, model/training, CORE_LEDGER, AI_LEDGER, Shared Risk Engine, Kill Switch, PostgreSQL, VPS/runtime, provider/database/exchange, external network or destructive lifecycle operation occurred. T0 remains independent/protected; ledgers remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.
