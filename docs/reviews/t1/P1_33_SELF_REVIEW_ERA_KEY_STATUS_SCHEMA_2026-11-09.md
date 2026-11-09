# P1.33 — Adversarial self-review of ERA key-status schema closure

Date: 2026-11-09  
Review type: Same-session adversarial static self-review; NOT independent.  
Exact normative contract blob reviewed: bcf78f3a70233aeb666fee468897f162405d03a0  
Prior finding: P1.32 F02-R16 MEDIUM.  
Branch: feature/t0-centralized-data-feeder-p1-20261101

## Verdict

**REQUEST CHANGES — F02-R17 LOW.**

P1.33 resolves the ERA_KEY_STATUS_V1 schema cardinality defect by defining exactly eight always-present keys, conditional nullability and bundle digest verification. The follow-up cross-document scan found that the appended negative fixtures are not numerically ordered: C171–C189 appear before C166–C170, and C179 appears after C189. This does not create a demonstrated runtime false-PASS, but it weakens deterministic fixture inventory and makes independent traceability/error checking ambiguous.

## F02-R17 — LOW: negative fixture sequence is out of numerical order

Evidence:
- C146–C165 are followed by C171–C178 and C180–C189.
- C179 appears after C189.
- C166–C170 appear after C179.
- The contract labels the fixture set as C137–C189, but the actual sequence is not ascending.

Required correction:
- Reorder the contiguous C146–C189 fixture block in strict numeric order without changing fixture semantics.
- Verify every ID C146 through C189 appears exactly once, with no omissions or duplicates.
- Confirm the terminal fixture range statement remains C137–C189.

## Checks that passed at contract-text level

- Exact P1.33 contract blob re-fetched: `bcf78f3a70233aeb666fee468897f162405d03a0`.
- F02-R6 through F02-R16 corrective requirements are present in the current contract text.
- ERA_KEY_STATUS_V1 now defines exactly eight always-present fields, explicit types/nullability and bundle digest verification.
- READ_ERA_KEY_STATUS is root-key signed and nonce/operation/identity/sequence bound.
- Local/remote status mismatch quarantines; no automatic key reactivation.
- C189 is present and targets missing/extra/malformed status fields.

Static checks do not prove implementation, ERA service durability, cryptographic verification, filesystem behavior or runtime.

## Residual blockers

F07 target filesystem/provider semantics NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C189 NOT IMPLEMENTED / NOT EXECUTED; ERA/root key/monotonic store NOT IMPLEMENTED / NOT VERIFIED.

## Required next action

Reorder and mechanically verify C146–C189, then self-review the exact new contract SHA. Retarget issue #138 only after a subsequent exact-SHA self-review passes.

## Authorization boundary

No implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, strategy/AI/ledger/risk changes, trading or destructive data operations are authorized.

T0 remains independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement. No destructive data operations without separate explicit approval.
