# P1.18 — Self-review of F05-R2 and F02-R2 contract corrections

Date: 2026-11-09
Review type: Same-session static adversarial self-review; NOT independent.
Exact normative contract blob SHA reviewed: `984f7669f4dae5902b852b6f6fa1c09d799f9957`
Contract commit: `d6610f571417873e4c0b74dd770f705c86b24a56`
Prior review: P1.17, blob `93d1fe0f2010058f2a2f4e106d5813ce532c901c`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

## Verdict

**DOCUMENTATION-LEVEL PASS for the scoped F05-R2 manifest namespace correction, F02-R2 rollback capability-boundary clarification, and C133–C135 fixture specifications. IMPLEMENTATION READINESS NOT ESTABLISHED. F07 NOT VERIFIED. INDEPENDENT REVIEW REQUIRED.**

This is a same-session self-review and does not satisfy issue #138.

## Exact changes verified

### F05-R2 — manifest reference namespace consistency

- §21.5 manifest field inventory now explicitly defines `exchange_info_evidence_ref` as the Envelope-record ID from §22.11.4 and prohibits direct Raw-body object references.
- §21.5 manifest resolver paragraph now resolves manifest reference → immutable Envelope-record → Raw-body object through envelope `raw_body_sha256` → exact BTCUSDT raw symbol-record byte slice.
- §21.5 explicitly rejects a direct manifest reference to a correctly hashed Raw-body object.
- §22.11 precedence statement now expressly includes §21.5 and says it cannot authorize a Raw-body reference.
- §22.11.4 independently retains the deterministic Envelope-record digest projection (JCS object with `evidence_id` omitted), raw-body exact-byte digest, and strict resolution order.
- C133 explicitly rejects a manifest that points directly to a valid, correctly hashed Raw-body object.

Assessment: the manifest's reference target and resolver now agree across §21.5, §22.11 precedence and §22.11.4. The two ID namespaces remain distinct by both storage path and resolution procedure. F05-R2 is closed at documentation-contract level.

### F02-R2 — full-root rollback capability boundary

- §22.11.2 now states local checkpoints are crash-recovery evidence only and neither detect nor prevent full-root rollback.
- It explains why a same-filesystem full-root snapshot can restore the local checkpoint, counter, receipts, manifests, initialization record, data and local identities into a mutually consistent older state.
- It explicitly says automatic full-root rollback detection is NOT PROVIDED and prohibits implementation/test/operator claims that local checkpoint/counter provide it.
- Crash-recovery validity is conditional on the operational assumption that the root was not rolled back/cloned/restored.
- Known or suspected restore/clone/snapshot rollback, when indicated by an independent operational signal, requires immediate quarantine and separately approved new-root/recovery-epoch handling.
- §22.11.2 and §22.11.3 do not imply an external anchor exists; any future anchor requires a separate design, semantics, versioned contract and independent review.
- §22.11.2/§22.11.3 language was checked against §22.11.2's rollback paragraph and §22.11.3 recovery ordering. §22.11.2 no longer treats an unobservable copy as locally detectable.
- §22.11.2's follow-up paragraph now distinguishes missing/corrupt/inconsistent local state (locally detectable and quarantine) from a copy/rollback event (quarantine only when independently known/suspected).
- C130/C134 test the fail-closed response when an independent restore indication is supplied. C135 explicitly records that a self-consistent old snapshot without an external signal is indistinguishable locally and automatic detection is NOT PROVIDED.

Assessment: the contract now accurately describes the boundary between local crash recovery and anti-rollback detection. F02-R2 is closed as a documentation ambiguity, not as a technical anti-rollback capability. No anti-rollback capability is claimed.

## Adversarial consistency checks

1. §21.5 no longer contains the old description "reference to the exact raw ExchangeInfo snapshot".
2. §21.5 field inventory and resolver both point to Envelope-record ID; §22.11 precedence expressly covers §21.5.
3. §22.11.4 still binds envelope ID to the JCS projection excluding `evidence_id`, and binds raw bytes separately through `raw_body_sha256`.
4. A correct Raw-body digest cannot satisfy the manifest's Envelope-record reference; C131 and C133 cover namespace confusion.
5. No sentence in the revised §22.11 claims local checkpoint/counter detects or prevents full-root rollback.
6. The "known/suspected rollback" quarantine rule is tied to an independent operational signal; the text explicitly forbids inferring an unobserved rollback from internally consistent local files.
7. C130 and C134 do not pretend to test automatic detection; C135 explicitly records the NOT PROVIDED capability boundary.
8. Existing §18.3 rollback language already disclaims adversarial rollback detection without an independent prior anchor and remains consistent with the clarified full-root limitation.
9. F01 remains controlled by §22.1 precedence: current-profile `RECONCILED_COMPLETE` and `reconciliation_evidence_ref` remain forbidden; the retained watermark is non-authoritative progress only.
10. No source/runtime/test/REST/Actions evidence is inferred from documentation changes.

## Remaining blockers and limits

- F07 target filesystem/mount/device/provider identity and actual `flock`, `renameat2(RENAME_NOREPLACE)`, file fsync and directory fsync behavior: NOT VERIFIED.
- Binance REST no-trade, boundary, pagination, finality and correction semantics: NOT ACCEPTED; current profile still forbids `RECONCILED_COMPLETE`.
- Pinned producer decimal defect (f64 conversion, fixed 12-decimal formatting, parse-error-to-zero): CONFIRMED / NOT FIXED.
- Producer FINAL_ONLY/product identity implementation: NOT VERIFIED.
- Manifest, receipt, publication counter, recovery checkpoint, ExchangeInfo evidence store and adapter: NOT IMPLEMENTED.
- C01–C135: design scenarios only; NOT IMPLEMENTED / NOT EXECUTED.
- No GitHub Actions run/artifact, source implementation, Binance REST request, VPS/runtime, or T1 activation is claimed.

## Required next step

Retarget issue #138 to this exact contract blob SHA `984f7669f4dae5902b852b6f6fa1c09d799f9957` and request genuinely independent adversarial review. The reviewer must assess F01–F06, F02-R1/R2, F05-R1/R2, F07 and implementation feasibility. This self-review is not independent.

## Authorization boundary

Documentation and review only. No T1 source edits, adapter implementation, test execution, GitHub Actions dispatch, Binance REST, VPS/runtime, T1 activation, T0/T2 changes, strategy/AI/ledger/risk/trading changes, deletion, archive, cleanup, vacuum, compaction, backup expiry, restore or destructive operation.

T0 remains independent/canonical. No T1 writes to T0. Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.
