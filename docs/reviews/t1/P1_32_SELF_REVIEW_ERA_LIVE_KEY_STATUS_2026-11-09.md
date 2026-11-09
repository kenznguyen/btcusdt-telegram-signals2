# P1.32 — Adversarial self-review of live ERA key-status protocol

Date: 2026-11-09  
Review type: Same-session adversarial static self-review; NOT independent.  
Exact normative contract blob reviewed: 57f1d6a7126de56b4ccd4707d8039dc0032d7e7e  
Prior finding: P1.31 F02-R15 HIGH.  
Branch: feature/t0-centralized-data-feeder-p1-20261101

## Verdict

**REQUEST CHANGES — F02-R16 MEDIUM.**

P1.32 adds the missing `READ_ERA_KEY_STATUS` request/response, root-key signature requirement, local/remote split-brain handling and fail-closed behavior. The response schema has a closed-schema cardinality contradiction.

## F02-R16 — MEDIUM: ERA_KEY_STATUS_V1 schema says exactly seven keys but defines an eighth

Evidence:
- The text says `ERA_KEY_STATUS_V1` has exactly seven listed keys.
- It then says the response payload MUST also include `revocation_evidence_bundle_jcs_base64url` for REVOKED status and null for ACTIVE.
- That conditional field is therefore an eighth key, contradicting the exact seven-key schema.
- C188 refers to conditional null/non-null fields but does not resolve the schema cardinality.

Required correction:
- Define exactly eight keys, including `revocation_evidence_bundle_jcs_base64url`.
- Define its type and canonical unpadded base64url encoding, and require null for ACTIVE / non-null for REVOKED.
- Explicitly state all eight keys are always present; only values vary by status.
- Ensure digest is over exact decoded canonical bundle bytes and that the bundle digest equals the separately supplied digest.
- Add a fixture rejecting missing/extra status fields and malformed bundle encoding.

## Checks that passed at contract-text level

- Exact P1.32 contract blob re-fetched: `57f1d6a7126de56b4ccd4707d8039dc0032d7e7e`.
- READ_ERA_KEY_STATUS request and ERA_KEY_STATUS_V1 response are present.
- Response is nonce/operation/identity bound and signed by the separately pinned ERA root key.
- Remote REVOKED/local ACTIVE path validates evidence, updates trust and quarantines before next operation.
- Remote ACTIVE/local REVOKED or field mismatch causes split-brain quarantine; no automatic reactivation.
- C183–C188 are present and ordered.

Static checks do not prove ERA implementation, cryptographic verification, monotonicity, filesystem durability or runtime.

## Residual blockers

F07 filesystem/provider semantics NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C188 NOT IMPLEMENTED / NOT EXECUTED; ERA/root key/monotonic store NOT IMPLEMENTED / NOT VERIFIED.

## Required next action

Correct the closed schema cardinality, add a negative fixture, then self-review the exact new contract SHA. Retarget issue #138 only after a subsequent exact-SHA self-review passes.

## Authorization boundary

No implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, strategy/AI/ledger/risk changes, trading or destructive data operations are authorized.

T0 remains independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement. No destructive data operations without separate explicit approval.
