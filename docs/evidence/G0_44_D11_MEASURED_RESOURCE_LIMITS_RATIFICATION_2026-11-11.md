# G0.44 — D11 Measured Resource Limits and Ratification

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Evidence baseline: `61f88ab0fdc8fec9aed63477c3fabe9f6e47ea41`  
Decision basis: user's standing bounded authorization to approve G0 work automatically through D11 completion (2026-11-11)

## 1. D11 measurement evidence accepted

The G0.43 one-shot synthetic measurement is the accepted D11 evidence source:

- Measurement checkout: `93ac905a3b8afb5bebb7c841140c0bccb9f1a47c`.
- GitHub Actions run [43053648998](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43053648998), job `130637223760`, attempt 1, SUCCESS.
- Frozen runner invocation: exactly once.
- Frozen harness/runner/tests Git blobs unchanged: `e8db71c11e0503ea6d9a2480d75470185c4d5100`, `23a35aab7f7aeacd8a3f63d630a875fe76b1ff6a`, `d06a5b533af14378ed284051e5b057cf57377876`.
- Report artifact ID `13870492247`; ZIP SHA-256 independently matched GitHub digest `4cdefc2ed049bd49b1092fb8cf113f92b411c08281f9f7c8db0137e36a85fcca`.
- ZIP contains exactly one JSON file; strict JSON parse, exact 13-field top-level inventory and persisted-byte readback PASS.
- Corpus revision: `S1-SYNTHETIC-PREFLIGHT-RECIPE-V1`; corpus SHA-256 `1c9a302d9df179322bfd7a00aa6db322a66b578a0609b9264481c3801b8a2d94`.
- 22 fixtures; all 11 D10 fixture types; case counts SYN-01=11, SYN-29=3, SYN-30=2, SYN-31=3, SYN-32=3.
- A-01–A-13 all true; two measurement passes equal; runner internal report readback true; execution trace empty.

### Observed maxima

| D11 dimension | Observed maximum | Measurement interpretation |
|---|---:|---|
| Raw input bytes | 501 bytes per fixture | Largest of 22 raw parser inputs |
| Nesting depth | 6 levels | Root JSON container counts as level 1 |
| Object members | 8 | Maximum key/value pairs in one object |
| Array items | 4 | Maximum elements in one array |
| String value | 100 UTF-8 bytes | Longest JSON string value |
| String key | 19 UTF-8 bytes | Longest JSON object key |
| Scalar nodes | 13 | Strings, numbers, booleans and null; keys excluded |
| Diagnostic reason codes | 1 per invalid fixture | Frozen parser/validator returns one scalar reason code per result; A-02 validates all 22 oracle outcomes. Parser-invalid rows also show at most one `parse_reason_code`. |

The frozen harness measures nesting by starting at depth 0 and incrementing once for each JSON object or array; therefore the root object is depth 1. Malformed UTF-8/JSON fixtures contribute raw byte size only when structural dimensions are not applicable. Duplicate-key inputs are measured from their original bytes.

Diagnostic limitation: the JSON artifact records parser-level `parse_reason_code` per row; schema-validation expected outcomes are validated by A-02 against the frozen oracle but are not separately emitted as a per-row diagnostic field. The maximum one-code cardinality is also bounded by the frozen API's scalar `reason_code` return, not by a multi-code diagnostic list. No raw-input or oracle payload was persisted.

## 2. Ratified D11 ceilings

Under the user's standing bounded authorization through D11 completion, the following exact table is ratified for the S1 Synthetic Contract Fixture v1 parser boundary:

| Resource | Observed maximum | Ratified ceiling | Headroom / rationale |
|---|---:|---:|---|
| Raw input bytes | 501 | **8,192 bytes** | 16.35× measured maximum; bounded 8 KiB input |
| Nesting depth | 6 | **8 levels** | Two additional container levels; root counts as level 1 |
| Object members | 8 | **32 members/object** | 4× measured maximum |
| Array items | 4 | **64 items/array** | 16× measured maximum |
| String value bytes | 100 | **1,024 bytes/value** | 10.24× measured maximum |
| String key bytes | 19 | **256 bytes/key** | 13.47× measured maximum |
| Scalar nodes | 13 | **256 nodes/fixture** | 19.69× measured maximum |
| Diagnostic reason codes | 1 | **1 code/invalid fixture** | Matches frozen scalar reason-code contract; no multi-code diagnostic expansion |

These are per-input/per-fixture limits. The measured corpus total of 6,418 bytes is evidence metadata, not a per-input ceiling.

## 3. Enforcement policy ratified for a future implementation

1. Reject an input if any one of the ratified limits is exceeded; do not truncate, normalize, silently drop fields, or partially accept it.
2. Enforce the raw byte ceiling before UTF-8 decoding or JSON parsing.
3. Apply strict UTF-8 decoding. For malformed UTF-8 or malformed JSON, report raw byte size only; structural dimensions are not applicable.
4. Count root object/array depth as 1. Count maximum members in one object and maximum items in one array, not cumulative totals.
5. Count UTF-8 encoded bytes separately for string keys and string values. Count scalar values but not object keys.
6. Duplicate-key detection and measurement must use the original input bytes; do not measure a normalized mapping that has discarded duplicates.
7. Fail closed on any resource-limit violation. Emit no raw input, secret, oracle payload or arbitrary parser excerpt. At most one fixed reason code is returned for an invalid fixture.
8. Do not infer trust, issuer authenticity, evidence truth, lifecycle eligibility, owner authorization or execution permission from passing these structural limits.

The exact spelling of a future resource-limit reason code, parser algorithm, implementation strategy and runtime behavior beyond these requirements are not selected by this D11 ratification.

## 4. Decision and boundary

- D11 measurement-first requirement: **SATISFIED**.
- Evidence quality for bounded synthetic corpus: **PASS**.
- Numeric resource ceilings: **RATIFIED** as the exact table in section 2.
- Fail-closed parser boundary requirements: **RATIFIED** as section 3.
- Runtime enforcement: **NOT IMPLEMENTED / NOT VERIFIED**.
- Production parser/verifier: **NOT AUTHORIZED by this D11 decision**.
- S1 implementation scope remains governed by the separately ratified D14 boundary; no source, test, CI or runtime implementation was performed here.
- No new measurement, fixture generation, workflow invocation, retry or artifact was performed in G0.44.
- D01–D04, D06–D09 and D12–D13 remain OPEN / NOT RATIFIED. G0.44 does not ratify cryptography, trust roots, key lifecycle, issuer authority, freshness, revocation, owner authorization or verified-facts semantics.
- No T0/T1/T2, canonical market data, model/training, CORE_LEDGER, AI_LEDGER, Shared Risk Engine, Kill Switch, PostgreSQL, VPS/runtime, external provider/database/network/exchange or destructive lifecycle operation occurred.

**G0.44 verdict: D11 COMPLETE — MEASUREMENT EVIDENCE ACCEPTED; EXACT NUMERIC CEILINGS AND FAIL-CLOSED STRUCTURAL POLICY RATIFIED. Enforcement remains unimplemented and unverified.**
