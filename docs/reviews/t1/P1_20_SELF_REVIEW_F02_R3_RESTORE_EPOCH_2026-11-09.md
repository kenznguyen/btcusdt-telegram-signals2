# P1.20 — Self-review of F02-R3 restore-epoch harmonization

Date: 2026-11-09
Review type: Same-session static adversarial self-review; NOT independent.
Exact normative contract blob SHA reviewed: `77457a11aaf5b91f11aa8ea66cbf1414f7d9723a`
Contract commit: `22dc3cde9a709197e84c7524d5fec076f10c9d7e`
Prior review: P1.19, blob `5a6724a3d4f4876e31a166f7c8b6ff962ddf50a2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

## Verdict

**DOCUMENTATION-LEVEL PASS for F02-R3 restore-epoch harmonization and C136 specification. IMPLEMENTATION READINESS NOT ESTABLISHED. F07 NOT VERIFIED. INDEPENDENT REVIEW REQUIRED.**

This is a same-session self-review. It does not establish filesystem behavior, implementation correctness, runtime readiness or independent approval.

## Exact correction verified

1. §18.3 now separates an ordinary, separately approved older-backup restore from a known/suspected full-root snapshot/copy/clone/restore rollback.
2. For a known/suspected full-root rollback reported by an independent operational signal, §18.3 requires immediate quarantine. A new generation under the old `source_root_id` is explicitly insufficient and must be rejected.
3. Resumption requires a separately approved new `source_root_id`, a new recovery epoch and fresh reconciliation. Local checkpoint/counter/receipt/manifest/data objects in the restored root cannot establish latest-state continuity.
4. §21.5 now explicitly says local counter, checkpoint, receipt, manifest and data are not independent anchors. Only an independently controlled monotonic anchor outside the source-root rollback/failure domain could establish latest-state continuity; none is provided by this profile.
5. §22.11 precedence expressly includes §18.3 and states that the new-root/recovery-epoch rule is authoritative for known/suspected full-root rollback.
6. C136 rejects the proposed recovery path that creates only a new generation while retaining the old `source_root_id`; it requires a separately approved new root ID, recovery epoch and fresh reconciliation.
7. C136 is explicitly a fail-closed response fixture, not a test of automatic rollback detection. C135 still states automatic full-root rollback detection is NOT PROVIDED.

## Adversarial consistency checks

- No remaining §18.3 instruction permits a new generation under the old root ID after an independently known/suspected full-root rollback.
- §21.5 no longer describes a local checkpoint/counter as independently trusted.
- §22.11 precedence now explicitly harmonizes §18.3, §21.5 and §22.11.2.
- §22.11.2 still disclaims automatic detection of an unobserved, internally consistent full-root rollback.
- F05-R2 remains consistent: manifest reference → Envelope-record ID → Raw-body via envelope `raw_body_sha256`; direct Raw-body reference is invalid.
- F01 remains controlled by §22.1: current-profile `RECONCILED_COMPLETE` and `reconciliation_evidence_ref` are forbidden; watermark is non-authoritative progress only.
- C133–C136 remain design specifications only, NOT IMPLEMENTED / NOT EXECUTED.

## Remaining blockers

- F07 target filesystem/mount/device/provider identity and actual `flock`, `renameat2(RENAME_NOREPLACE)`, file-fsync and directory-fsync behavior: NOT VERIFIED.
- Binance REST no-trade, boundary, pagination, finality and correction semantics: NOT ACCEPTED.
- Pinned producer f64 conversion, fixed 12-decimal formatting and parse-error-to-zero defect: CONFIRMED / NOT FIXED.
- Producer FINAL_ONLY/product identity implementation: NOT VERIFIED.
- Manifest, receipt, publication counter, recovery checkpoint, ExchangeInfo evidence store and adapter: NOT IMPLEMENTED.
- C01–C136: design scenarios only; NOT IMPLEMENTED / NOT EXECUTED.
- No GitHub Actions run/artifact, source implementation, REST request, VPS/runtime or T1 activation is claimed.

## Required next step

Retarget issue #138 to exact contract blob SHA `77457a11aaf5b91f11aa8ea66cbf1414f7d9723a` and request genuinely independent adversarial review. The reviewer must assess F01–F06, F02-R1/R2/R3, F05-R1/R2, F07, restore semantics and implementation feasibility. This self-review is not independent.

## Authorization boundary

Documentation and review only. No T1 source edits, adapter implementation, test execution, GitHub Actions dispatch, Binance REST, VPS/runtime, T1 activation, T0/T2 changes, strategy/AI/ledger/risk/trading changes, deletion, archive, cleanup, vacuum, compaction, backup expiry, restore or destructive operation.

T0 remains independent/canonical. No T1 writes to T0. Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.
