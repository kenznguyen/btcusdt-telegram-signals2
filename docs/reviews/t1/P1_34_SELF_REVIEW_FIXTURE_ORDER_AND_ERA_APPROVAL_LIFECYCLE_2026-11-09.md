# P1.34 — Exact-SHA adversarial self-review of ERA approval lifecycle and fixture inventory

Date: 2026-11-09  
Review type: Same-session adversarial static self-review; NOT independent.  
Exact normative contract blob reviewed: 0b4bef0ca9e0fdef7524dc3766cc32d897fa64ea  
Prior finding: P1.33 F02-R17 LOW.  
Branch: feature/t0-centralized-data-feeder-p1-20261101

## Verdict

**DOCUMENTATION-LEVEL PASS for F02-R6 through F02-R17 corrections and C146–C189 fixture specifications.**

This PASS is limited to static contract consistency and fixture inventory. It is not independent review and does not establish implementation readiness, cryptographic correctness, ERA service existence/durability, target filesystem behavior, Binance completeness or runtime safety.

## Exact-SHA verification

The normative contract was re-fetched from the active branch after the P1.34 update. Exact blob SHA: `0b4bef0ca9e0fdef7524dc3766cc32d897fa64ea`.

### P1.25–P1.34 finding closure matrix

| Finding | Required correction | Static result |
|---|---|---|
| F02-R6 HIGH | Monotonic external policy head; stale policy restore rejected; no self-digest freshness claim | PASS |
| F02-R7 MEDIUM | One-time tuple-bound decision consumption; exact retry idempotency; no reuse | PASS |
| F02-R8 MEDIUM | Revalidation gates and post-revocation quarantine/preservation semantics | PASS |
| F02-R9 HIGH | Versioned ERA protocol, signed envelope, bootstrap, payload schemas and role boundaries | PASS |
| F02-R10 HIGH | Immutable bundle binds exact consume request, receipt payload and signed response envelope | PASS |
| F02-R11 MEDIUM | Revocation-effective sequence; historical signature vs current authorization separated | PASS |
| F02-R12 MEDIUM | Root-key-signed REVOKE_ERA_KEY operation and trust-file binding | PASS |
| F02-R13 HIGH | Immutable revocation evidence bundle binds request, payload and signed root-key envelope | PASS |
| F02-R14 MEDIUM | Root-key rotation explicitly offline/separately approved; compromise quarantines; no old-root fallback | PASS |
| F02-R15 HIGH | READ_ERA_KEY_STATUS operation, root-key-signed status and split-brain handling | PASS |
| F02-R16 MEDIUM | ERA_KEY_STATUS_V1 exactly eight always-present keys, types and nullability | PASS |
| F02-R17 LOW | C146–C189 reordered and mechanically checked for exact ascending sequence/no omissions/duplicates | PASS |

### Adversarial checks

| Check | Result |
|---|---|
| Policy revision and previous-digest binding; live monotonic ERA policy head | PASS |
| Policy update compare-and-advance, durable readback and fail-closed stale policy handling | PASS |
| Decision ID consumption bound to approval digest, predecessor/new root, recovery epoch and scopes | PASS |
| Exact-tuple retry returns same immutable receipt; changed tuple cannot reuse decision ID | PASS |
| Recovery epoch binds immutable request/receipt/envelope evidence bundle and digest | PASS |
| Offline verification of retained signed consumption evidence after restart | PASS |
| Fresh live ERA policy/key-status checks at open/read/write/transition gates | PASS |
| ERA response envelope binds operation, ERA identity, fresh nonce, authority sequence, payload digest and signature | PASS |
| Distinct operational ERA key and separately pinned root key | PASS |
| Revocation receipt binds key ID, prior/resulting state and effective authority sequence | PASS |
| Revocation evidence bundle is pinned by trust file and durably published before trust update | PASS |
| Historical pre-revocation signature remains evidence only; revoked key cannot authorize new operation | PASS |
| READ_ERA_KEY_STATUS handles local/remote mismatch, unavailable/stale status and no automatic reactivation | PASS |
| Root-key compromise/rotation boundary is explicit and fail-closed | PASS |
| F01 v1.1 canonical resumption prohibition and no seal/watermark/promotion remain intact | PASS |
| F05 Raw-body vs Envelope-record namespace distinction remains intact | PASS |

### Fixture inventory verification

- The contiguous C146–C189 block contains exactly 44 fixture lines.
- Every integer ID from C146 through C189 appears exactly once.
- IDs are strictly ascending.
- No omissions or duplicates were found.
- Terminal range statement is C137–C189.
- Fixtures remain design-only; NOT IMPLEMENTED / NOT EXECUTED.

## Residual blockers — unchanged

- F07: target filesystem/mount/device/provider identity and actual `flock`, `renameat2(RENAME_NOREPLACE)`, file-fsync and directory-fsync behavior: NOT VERIFIED.
- Binance REST no-trade, boundary, pagination, finality and correction semantics: NOT ACCEPTED as completeness oracle.
- Pinned producer f64 conversion, fixed 12-decimal formatting and parse-error-to-zero defect: CONFIRMED / NOT FIXED.
- Producer FINAL_ONLY/product identity implementation: NOT VERIFIED.
- ERA service, root-key bootstrap, monotonic store, caller authentication, receipt persistence and revocation service: NOT IMPLEMENTED / NOT VERIFIED.
- C01–C189: NOT IMPLEMENTED / NOT EXECUTED.
- No cryptographic keypair/signature/ERA service was generated or verified; no executable tests, GitHub Actions run/artifact, REST request, VPS/runtime or T1 activation was performed.

## Retarget authorization boundary

This documentation-level PASS permits retargeting issue #138 to this exact contract blob for genuinely independent review. It does not close issue #138, authorize implementation, or supersede F07/REST/producer blockers. Independent review must examine F01–F06, F02-R1–R17, F05-R1/R2, ERA protocol and trust boundaries, C01–C189, and all residual blockers.

T0 remains independent/canonical. No T1 writes to T0. Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement. No T0/T2 changes, T1 activation, trading or destructive data operations.
