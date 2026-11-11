# G0.33 — S1 Synthetic Corpus Creation and Measurement Authorization Package

Date: 2026-11-11 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Baseline HEAD: `58d76499cc824b065aad43c94bd60c12459785ea`
Baseline handoff blob: `573460697b31dc4b06cd0cfb0b195639ac6e016c`
Inputs: G0.30 owner decision package; G0.31 ratification; G0.32 measurement specification
Type: documentation-only owner authorization package
Disposition: **DECISION PACKAGE PASS — exact bounded measurement action presented for owner decision; corpus creation and measurement NOT AUTHORIZED/PERFORMED by G0.33**

## 1. Purpose and current authority

G0.32 specifies how a future synthetic corpus can be measured. G0.31 ratified a measurement-first policy but did not authorize corpus generation, file creation or measurement execution.

G0.33 converts that next step into a precise owner decision. This report does not itself authorize or perform the proposed action.

The requested decision is limited to synthetic data generation and resource measurement for the S1 parser contract. It does not authorize parser implementation, test module creation/execution, CI changes, cryptography, verifier work or any production/runtime action.

## 2. Recommended authorization

**Recommendation: approve one isolated, in-memory synthetic corpus generation and measurement run, with no persistent fixture files.**

The proposed action would:

1. Generate deterministic UTF-8 JSON byte strings entirely from fabricated data.
2. Cover the S1 subset specified by G0.32: SYN-01, SYN-29, SYN-30, SYN-31 and SYN-32, plus minimal structural coverage for each of the 11 ratified D10 fixture types.
3. Measure raw byte length and applicable structural dimensions independently of any future parser implementation.
4. Repeat the exact generation and measurement in the same isolated run to confirm identical per-fixture measurements.
5. Produce a documentation-only evidence report containing synthetic IDs, corpus recipe/version, measurements, aggregate maxima, repeatability result and a candidate numeric-ceiling table.
6. Stop before numeric ceilings become policy. A separate owner decision will still be required to ratify each proposed ceiling.

No parser-under-test is present or required for this measurement-only action.

## 3. Exact proposed scope

### 3.1 Included

- Synthetic payloads generated from scratch, with reserved `syn-` identifiers only.
- The exact 11-value D10 `fixture_type` allowlist:
  1. `SYNTHETIC_OBJECT`
  2. `SYNTHETIC_EVIDENCE`
  3. `SYNTHETIC_ISSUER_CLAIM`
  4. `SYNTHETIC_POLICY_CLAIM`
  5. `SYNTHETIC_INVENTORY_CLAIM`
  6. `SYNTHETIC_SENSITIVITY_CLAIM`
  7. `SYNTHETIC_HOLD_CLAIM`
  8. `SYNTHETIC_DEPENDENCY_CLAIM`
  9. `SYNTHETIC_COPY_LINEAGE_CLAIM`
  10. `SYNTHETIC_FRESHNESS_CLAIM`
  11. `SYNTHETIC_BINDING_CLAIM`
- S1 structural cases only: minimal valid-shape records, malformed UTF-8/JSON, duplicate keys, trailing data, unsupported schema/critical fields, required-field/type failures, and resource-boundary shapes.
- Measurement of:
  - raw input bytes;
  - maximum nesting depth;
  - maximum members in one object;
  - maximum items in one array;
  - maximum UTF-8 bytes for string values and keys separately;
  - scalar-node count;
  - diagnostic reason-code count, only if a fixed synthetic oracle is defined for the measurement record.
- Two deterministic passes over the same generated corpus.
- Documentation/evidence report and handoff update only, after the action is separately approved and completed.

### 3.2 Explicitly excluded

- Any real or production-derived data, including personal/account data, secrets, market data, T0/T1/T2 records, model/ledger records, provider evidence, VPS data or real artifact paths.
- SYN-02–28 and SYN-34–38 semantics, which concern identity, issuer authority, cryptographic integrity, provenance, inventory truth, sensitivity truth, policy authority, freshness/revocation, downstream use, rebuildability, verified-facts immutability and action authorization.
- SYN-33 unknown non-critical extension behavior, which remains unresolved.
- Parser/verifier implementation, production schema, API, adapter, registry, executor or lifecycle evaluator changes.
- Test module creation or test execution.
- CI workflow creation/change/dispatch, dependency changes or permission changes.
- Key generation, signing, trust-root configuration or cryptographic verification.
- Network/provider/GitHub API access beyond the approved documentation commit after the owner decision and completed work; database/storage/VPS/runtime access or inventory.
- Any action on T0 canonical data, T1/T2 datasets, CORE_LEDGER, AI_LEDGER or trading/execution systems.
- Archive, quarantine, cleanup, expiry, compaction, VACUUM, deletion or other lifecycle mutation.

## 4. Execution containment proposal

To minimize persistence and authority surface:

- Generate payload bytes in process memory only.
- Do not write corpus payloads or temporary fixture files to the repository, VPS, project data directories or persistent storage.
- Do not create standalone fixture artifacts.
- Do not access the network, databases, provider APIs, secrets, credentials, key stores, clocks or VPS.
- Do not import or invoke the lifecycle evaluator, verifier or any runtime trading/data component.
- Do not emit raw payload contents in logs or evidence. Report synthetic fixture IDs and measurements only.
- If the measurement method cannot safely handle malformed/oversized input within the isolated process, stop and report the case as BLOCKED; do not increase limits or switch to persistent staging.
- Do not run the parser implementation or infer parser correctness from these measurements.

The isolated execution environment and exact command/runtime should be recorded in the resulting evidence report. No environment or command is selected or invoked by G0.33.

## 5. Measurement output and acceptance criteria

A future G0.33 execution report must include:

1. Exact corpus case IDs and D10 type coverage.
2. Deterministic generation recipe and corpus revision identifier.
3. Per-fixture measurements for every applicable dimension.
4. Corpus count, total raw bytes and aggregate maxima.
5. Separate maxima for string keys and string values.
6. Repeated-pass equality for every fixture and every reported measurement.
7. Explicit exclusions and not-applicable dimensions.
8. Candidate ceiling table showing observed maximum, safety margin, proposed ceiling and rationale for each dimension.
9. Confirmation that no production data, real secrets, external evidence, persistent fixture files or external services were used.
10. Exact environment/runtime and command provenance, plus commit SHA for the final evidence report.

Acceptance requires complete coverage of the approved S1 subset and all D10 types, deterministic repeatability, no persistence of payload bytes, and no scope breach. Any accidental real/sensitive content, unexpected filesystem/network/database access or need to exceed the approved boundary is an immediate stop condition.

## 6. Numeric ceilings remain a separate owner decision

The measurement run may recommend ceilings but may not activate or enforce them.

| Resource | Current status | Required future evidence |
|---|---|---|
| Raw input bytes | OPEN | Observed maximum + margin |
| Nesting depth | OPEN | Observed maximum + margin |
| Object members | OPEN | Observed maximum + margin |
| Array items | OPEN | Observed maximum + margin |
| String value bytes | OPEN | Observed maximum + margin |
| String key bytes | OPEN | Observed maximum + margin |
| Scalar nodes | OPEN | Observed maximum + margin |
| Diagnostic reason codes | OPEN | Defined diagnostic corpus + observed maximum + margin |

The G0.30 candidate values (64 KiB, depth 8, 32 object members, 64 array items, 1 KiB/string, 512 scalar nodes and 16 reason codes) remain NOT RATIFIED and must not be treated as defaults or approved limits.

After measurement, a separate owner decision must approve or amend the exact numeric table. Only after that decision may parser enforcement be considered, under a separate implementation authorization.

## 7. Owner decision requested

Please explicitly approve or amend this exact action:

**G0.33-A — One isolated, deterministic, in-memory synthetic corpus generation and resource-measurement run, limited to the S1 scope and D10 vocabulary in Sections 2–5; no persistent fixture files; no parser or test implementation/execution; no CI/runtime/network/database/VPS access; documentation-only evidence output; no numeric ceilings ratified by the run.**

Approval of G0.33-A would authorize only that one measurement action. It would not authorize parser implementation, tests, CI, cryptographic verification, verifier integration, lifecycle decisions or destructive operations.

If the owner does not approve G0.33-A, no corpus generation or measurement may occur. The specification remains valid and the work is BLOCKED at the authorization gate.

## 8. Current status and verdict

- G0.30 D05/D10/D11 measurement-first/D14: OWNER-RATIFIED within the recorded S1 boundaries.
- G0.32 measurement specification: PASS.
- G0.33-A corpus creation/measurement: NOT AUTHORIZED.
- Numeric D11 ceilings: OPEN / NOT RATIFIED.
- Parser implementation and tests: NOT AUTHORIZED.
- D01–D04, D06–D09 and D12–D13: OPEN / NOT RATIFIED.
- G0.23 executable verifier cases: NOT RUN.
- TEST-01–07: 0/87; unchanged.
- Runtime/VPS inventory: NOT PERFORMED / NOT VERIFIED.
- Destructive authority: NOT GRANTED.

**G0.33: DECISION PACKAGE PASS — bounded owner decision prepared; execution remains NOT AUTHORIZED pending explicit approval of G0.33-A.**

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.
