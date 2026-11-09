# P1.22 — Adversarial self-review of recovery epoch identity and v1.1 resumption

Date: 2026-11-09  
Review type: Same-session static adversarial self-review; NOT independent.  
Exact normative contract blob SHA reviewed: 20e8b31db364a15b73359810664f7e079aa86bc7  
Contract correction commits: d2faa88f0af30adabf898483dbf039420b78d5a6, b1ddb3fe4b588a6adb7d751b43ccc6f9caa328ba, 542e7c80d0a3fd5b933645f2eb6af58ae3d143b2, 98ea1474800ff81bba50f47e8636326baaacd628  
Prior review: P1.21 blob f8a7b4ef6cb810204af1fdc613aaaadbd7985aba  
Branch: feature/t0-centralized-data-feeder-p1-20261101

## Verdict

**DOCUMENTATION-LEVEL PASS** for F02-R4 recovery-epoch identity/persistence/binding, F01-R2 v1.1 post-recovery resumption limits, and C137–C140 negative-fixture specifications.

This is a same-session static self-review, not independent review. It does not establish implementation correctness, runtime readiness, target-filesystem durability, Binance completeness, or authorization to implement or activate T1.

## P1.21 findings and closure

### F02-R4 — HIGH: recovery epoch lacked authoritative identity and persistence

**Closed at contract level:**
- recovery_epoch_id is a distinct canonical UUIDv4; it is not source_root_id or generation_sequence.
- The source-root initialization schema is now exactly twelve keys and binds recovery_epoch_id.
- Immutable recovery-epoch.json has a closed eight-key schema, binds the epoch to the new root, distinguishes INITIALIZATION from FULL_ROOT_ROLLBACK_RECOVERY, and is installed no-replace with file and parent-directory fsync requirements.
- A full-root rollback recovery requires an immutable, commit-pinned GitHub owner-approval record with a closed ten-key schema, exact new/predecessor root and epoch binding, and isolated-only v1.1 scope. The approval record is explicitly governance evidence only—not a cryptographic signature or independent monotonic anchor.
- The generation publication counter is now a closed six-key schema including recovery_epoch_id.
- The recovery checkpoint now binds recovery_epoch_id; its counter snapshot uses the six-key counter schema. Current and historical counters/checkpoints must match the initialization and epoch record.
- Normative precedence and §22.4 schema counts are aligned.

### F01-R2 — HIGH: “fresh reconciliation” conflicted with v1.1 prohibition

**Closed at contract level:**
- The ambiguous phrase is replaced with fresh post-recovery structural/source-identity validation.
- Current v1.1 may resume only separately approved isolated collection with source_health=UNKNOWN, unsealed and non-canonical.
- It cannot set RECONCILED_COMPLETE, populate reconciliation_evidence_ref, seal windows, advance a completeness watermark, promote to T0/canonical consumption, or authorize aggregation.
- Canonical resumption requires a separately versioned completeness profile, accepted completeness/no-trade oracle, genuinely independent review and explicit owner approval.

## Adversarial consistency checks

The exact contract blob 20e8b31db364a15b73359810664f7e079aa86bc7 was re-fetched and checked after the final contract update.

| Check | Result |
|---|---|
| Initialization schema count and epoch field | PASS |
| Closed recovery-epoch record and distinct identity | PASS |
| Closed owner-approval record and immutable commit-pinned reference | PASS |
| Six-key publication counter and epoch binding | PASS |
| Recovery checkpoint and counter-snapshot epoch binding | PASS |
| §22.4 / §22.9 / §22.10 schema precedence | PASS |
| §18.3 / §21.5 / §22.11 rollback and epoch semantics | PASS |
| v1.1 UNKNOWN/unsealed-only resumption; canonical path forbidden | PASS |
| C136 plus C137–C140 rejection scenarios | PASS |
| Automatic full-root rollback detection remains NOT PROVIDED | PASS |
| F05 Envelope-record vs Raw-body reference rule preserved | PASS |
| No obsolete five-key/eleven-key schema or “fresh reconciliation” wording remains | PASS |

These are static text/contract consistency checks, not executable tests. C01–C140 remain design specifications only; none was implemented or executed.

## Residual limitations and evidence

- F07 target filesystem/mount/device/provider identity and actual flock, renameat2(RENAME_NOREPLACE), file-fsync and directory-fsync behavior: NOT VERIFIED.
- Binance REST no-trade, boundary, pagination, finality and correction semantics: NOT ACCEPTED.
- Pinned producer f64 conversion, fixed 12-decimal formatting and parse-error-to-zero defect: CONFIRMED / NOT FIXED.
- Producer FINAL_ONLY/product identity implementation: NOT VERIFIED.
- Manifest, receipt, publication counter, recovery checkpoint, epoch/approval record verifier, ExchangeInfo evidence store and adapter: NOT IMPLEMENTED.
- C01–C140: NOT IMPLEMENTED / NOT EXECUTED.
- No GitHub Actions run/artifact, source implementation, REST request, VPS/runtime or T1 activation is claimed.

## Authorization boundary

This review authorizes only retargeting issue #138 to the exact contract blob for genuinely independent review. It does not authorize implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, strategy/AI/ledger/risk changes, trading, or destructive data operations.

T0 remains independent/canonical. No T1 writes to T0. Paper-only; AI_EXECUTION_ENABLED=false; no live orders; no OKX fallback/replacement. No destructive data operations without separate explicit approval.
