# P1.21 — Adversarial self-review of P1.20 recovery semantics

Date: 2026-11-09  
Review type: Same-session static adversarial self-review; NOT independent.  
Exact normative contract blob SHA reviewed: `77457a11aaf5b91f11aa8ea66cbf1414f7d9723a`  
Contract commit: `22dc3cde9a709197e84c7524d5fec076f10c9d7e`  
Prior self-review: P1.20, blob `8866b9e2397f3323cf1303c287ccac0ac788b32a`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

## Verdict

**REQUEST CHANGES — two residual contract-level ambiguities remain in recovery resumption.**

This is a same-session static review, not an independent review. It does not establish implementation correctness, target-filesystem behavior, runtime readiness or approval to implement.

## Findings

### F02-R4 — HIGH: recovery epoch has no authoritative identity or persistence contract

Evidence:
- §18.3 (lines 459–466) requires a separately approved new `source_root_id`, a new recovery epoch and fresh reconciliation after a known/suspected full-root rollback.
- §21.5 (lines 592–594) repeats the new-root/recovery-epoch requirement.
- §22.11 precedence (line 771) makes the new-root plus recovery-epoch requirement authoritative; C136 (line 856) requires both.
- The source-root initialization schema in §22.9 (line 750) defines eleven keys and contains `source_root_id`, but no recovery-epoch field.
- The generation counter and recovery-checkpoint schemas in §§22.2 and 22.11.1 likewise contain no recovery-epoch identity or binding.

Impact:
An implementer cannot determine what constitutes the required new recovery epoch, where it is durably recorded, how it is uniquely identified, who authorizes it, or how the new root/generation/checkpoint are bound to it. C136 asks for an epoch but the normative schemas do not provide a verifiable representation. Treating `source_root_id` as the epoch would collapse two separately stated requirements without authorization.

Required correction:
Define whether recovery epoch is a distinct identity or explicitly the new `source_root_id`; if distinct, specify its closed schema, canonical encoding, authority/approval evidence, durable location, lifecycle, and bindings to root initialization, generation/counter and recovery checkpoint. Add negative fixtures for missing, reused, mismatched and unauthorized epoch identities. Do not invent a runtime or external anchor.

### F01-R2 — HIGH: “fresh reconciliation” is not actionable under the current v1.1 profile

Evidence:
- §18.3 and §21.5 require fresh reconciliation before resumption after known/suspected full-root rollback.
- §22.1 expressly forbids `RECONCILED_COMPLETE` and `reconciliation_evidence_ref` throughout the current v1.1 profile, and says canonical eligibility/completeness-watermark advancement are unavailable.
- §22.1 permits future completeness only through a new versioned evidence profile with independent review and owner approval.
- The pinned Binance REST reconciliation candidate remains unaccepted; the contract records that the current source-health profile cannot establish completeness.

Impact:
The recovery clauses can be read as promising that a new root plus fresh reconciliation permits resumption within v1.1, while the current profile prohibits the only named completeness state and evidence reference. Fail-closed behavior is preserved, but the permitted post-recovery state and whether canonical resumption is possible are not explicit.

Required correction:
State expressly that under current v1.1, a new root/recovery epoch may at most resume isolated collection/staging with `UNKNOWN`/unsealed health; it MUST NOT regain canonical eligibility, seal windows or advance a completeness watermark. Canonical resumption requires a separately versioned completeness profile, accepted oracle, independent review and explicit owner approval. Clarify what “fresh reconciliation” means when no current-profile reconciliation can produce `RECONCILED_COMPLETE`; do not relax §22.1.

## Checks that remain consistent

- F02-R3: known/suspected full-root rollback requires quarantine; a new generation under the old `source_root_id` is insufficient.
- F02-R2: automatic detection of an unobserved, internally consistent full-root rollback remains explicitly NOT PROVIDED.
- F05-R2: manifest reference resolves to Envelope-record ID; envelope `raw_body_sha256` resolves to Raw-body object; direct Raw-body manifest reference is invalid.
- F01 current-profile prohibition in §22.1 is explicit and fail-closed.
- C136 is a rejection fixture for insufficient recovery identity, not a rollback-detection test.

## Evidence and authorization limits

- F07 target filesystem/mount/device/provider identity and actual `flock`, `renameat2(RENAME_NOREPLACE)`, file-fsync and directory-fsync behavior: NOT VERIFIED.
- Binance REST no-trade, boundary, pagination, finality and correction semantics: NOT ACCEPTED.
- Pinned producer f64 conversion, fixed 12-decimal formatting and parse-error-to-zero defect: CONFIRMED / NOT FIXED.
- Producer FINAL_ONLY/product identity implementation: NOT VERIFIED.
- Manifest, receipt, publication counter, recovery checkpoint, ExchangeInfo evidence store and adapter: NOT IMPLEMENTED.
- C01–C136: design scenarios only; NOT IMPLEMENTED / NOT EXECUTED.
- No GitHub Actions run/artifact, source implementation, REST request, VPS/runtime or T1 activation is claimed.

## Required next step

Documentation-only correction of F02-R4 and F01-R2, add negative fixtures, then a fresh same-session adversarial review of the exact resulting contract blob. Only after that review may issue #138 be retargeted for independent review. This review does not authorize implementation, tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes or destructive operations.

T0 remains independent/canonical. No T1 writes to T0. Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.
