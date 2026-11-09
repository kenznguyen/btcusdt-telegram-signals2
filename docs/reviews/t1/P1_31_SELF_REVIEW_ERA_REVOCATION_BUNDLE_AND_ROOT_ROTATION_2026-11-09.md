# P1.31 — Adversarial self-review of ERA revocation evidence bundle and root boundary

Date: 2026-11-09  
Review type: Same-session adversarial static self-review; NOT independent.  
Exact normative contract blob reviewed: dcdd4d3aa1743b169c9ab3f3cf7e1a32627c616e  
Prior findings: P1.30 F02-R13 HIGH and F02-R14 MEDIUM.  
Branch: feature/t0-centralized-data-feeder-p1-20261101

## Verdict

**REQUEST CHANGES — F02-R15 HIGH.**

P1.31 closes the missing signed-envelope evidence binding for ERA key revocation and explicitly makes root-key rotation a separately approved offline operation with quarantine on compromise. However, the contract requires a fresh live ERA policy-head/revocation check before each gated operation and says an incomplete trust-file update must query the exact key status, but the ERA protocol defines no key-status read operation or response schema.

## F02-R15 — HIGH: live revocation status cannot be queried under the defined ERA protocol

Evidence:
- ERA response envelope operation enum contains `READ_POLICY_HEAD`, `ADVANCE_POLICY_HEAD`, `CONSUME_DECISION`, and `REVOKE_ERA_KEY`.
- The protocol defines `ERA_KEY_REVOCATION_RECEIPT_V1` for the mutation.
- It requires fresh live ERA policy-head/revocation checks before gated operations and querying exact revocation event/status when trust-file update is incomplete.
- No `READ_ERA_KEY_STATUS` request or signed status payload schema is defined.

Consequence:
An implementation cannot satisfy the mandatory fresh live revocation check or recover safely after ERA commits revocation but the local trust file update is interrupted. It might rely on stale local ACTIVE state or invent an undocumented API.

Required correction:
- Add `READ_ERA_KEY_STATUS` as an exact ERA operation and closed request schema bound to a fresh nonce and exact `era_key_id`.
- Add a root-key-signed status payload binding ERA identity, key ID, current status, effective revocation sequence, exact revocation event ID, receipt payload digest and revocation evidence-bundle digest.
- Require the client to verify the response envelope, nonce, operation, authority sequence and root-key signature, then compare the returned status to the local trust file.
- If ERA reports REVOKED while local trust says ACTIVE, block immediately and update the local trust file only from the verified revocation evidence bundle; if local trust says REVOKED but ERA says ACTIVE or values differ, quarantine as split-brain.
- Define behavior for ERA unavailable, unknown key, stale status and authority sequence regression; all fail closed.
- Add fixtures for local ACTIVE/remote REVOKED, local REVOKED/remote ACTIVE, wrong event/digest, stale response and unavailable status endpoint.

## Checks that passed at contract-text level

- Exact P1.31 contract blob re-fetched: `dcdd4d3aa1743b169c9ab3f3cf7e1a32627c616e`.
- Revocation evidence bundle includes exact request, receipt payload and signed response envelope with digests.
- Trust-file entry pins the exact bundle reference/digest; bundle is persisted before trust-file update and exact readback.
- Revocation receipt binds root key, key ID, prior/resulting state and effective authority sequence.
- Root-key rotation is explicitly offline and separately approved; compromise forces quarantine/manual re-provisioning; no old-root fallback.
- C180–C182 are present and ordered.
- Prior ERA consumption evidence bundle remains intact.

Static checks do not prove ERA implementation, root-key custody, monotonic store, filesystem durability or runtime.

## Residual blockers

F07 target filesystem/provider semantics NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C182 NOT IMPLEMENTED / NOT EXECUTED; ERA/root-key/monotonic store NOT IMPLEMENTED / NOT VERIFIED.

## Required next action

Define the signed live key-status operation and negative fixtures, then self-review the exact new contract SHA. Retarget issue #138 only after a subsequent exact-SHA self-review passes.

## Authorization boundary

No implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, strategy/AI/ledger/risk changes, trading or destructive data operations are authorized.

T0 remains independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement. No destructive data operations without separate explicit approval.
