# P1.17 — Follow-up adversarial self-review of P1.15/P1.16 contract

Date: 2026-11-09
Review type: Same-session static adversarial self-review; NOT independent.
Exact normative contract blob SHA reviewed: `f78dc4410db61755149cb6a7e0c440330bc80741`
Contract commit: `69559bb0363934158351d794a48e17555f0222a8`
Prior self-review: P1.16, blob `aa26ad804d151b07ceae1c2731b65fc121b9a197`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

## Verdict

**REQUEST CHANGES — P1.16's F02-R1 and F05-R1 additions are materially clearer, but a remaining manifest-to-envelope reference conflict and an operationally unresolvable full-root rollback condition remain. F05-R1 is not fully closed across the complete contract. F02-R1 only provides local crash-recovery evidence; it does not provide full-root rollback detection.**

This review is same-session and does not satisfy issue #138.

## Findings

### F05-R2 — Manifest evidence reference remains ambiguous in §21.5
Severity: HIGH
Disposition: OPEN — REQUIRED

§22.11.4 now states that `exchange_info_evidence_ref` MUST reference the Envelope-record ID, not the Raw-body object ID. However, the earlier authoritative manifest field inventory in §21.5 still describes the same field as an "immutable retrievable reference to the exact raw ExchangeInfo snapshot" (§21.5, field inventory), and §21.5's following paragraph says the reference resolves to the immutable ExchangeInfo snapshot. Neither sentence identifies the referenced object as the envelope record.

§22.11's precedence statement says it supersedes ambiguous ExchangeInfo identifier wording in §§22.5, 22.6.1 and 22.9, but it does not expressly list §21.5. The exact manifest schema is still anchored to §21.5 through §22.4. A strict implementer can therefore reasonably interpret the manifest reference as a raw snapshot object while another follows §22.11.4 and resolves an envelope record.

Required correction: explicitly amend §21.5's field definition and resolver paragraph to say that `exchange_info_evidence_ref` is the Envelope-record ID; the envelope resolves to the Raw-body object using `raw_body_sha256`. Add §21.5 to §22.11's supersession/precedence statement and add a fixture that rejects a manifest reference to the raw-body object even when both objects independently hash correctly.

### F02-R2 — Full-root rollback cannot be detected by the local checkpoint/counter design
Severity: HIGH (capability boundary)
Disposition: OPEN — REQUIRED CLARIFICATION

§22.11.2 correctly states that the checkpoint, counter, receipts, manifests and data share one rollback/failure domain and that no protection is claimed against full-root snapshot rollback. It then says that if the root "may have been copied or restored together" without an external monotonic anchor, continuity is NOT PROVEN and the root MUST be quarantined.

The local design has no independent signal that tells the process whether such a copy/restore occurred. A byte-for-byte snapshot rollback on the same filesystem can preserve root ID, filesystem/device identity, lock-file identity, checkpoint history and counter consistency. The local checks can therefore see a self-consistent older state and cannot know it is older than a previously accepted state. The current wording describes the correct response if rollback is known or suspected, but does not define how suspicion is established; it must not be read as an automatic rollback detector.

Required correction: explicitly separate (a) crash recovery under the stated no-full-root-rollback assumption from (b) full-root rollback detection, which is NOT PROVIDED without an independently trusted external monotonic anchor. State that known or suspected restore/clone/snapshot rollback MUST quarantine and require a separately approved new root/recovery epoch. Do not claim the local checkpoint "prevents" or "detects" full-root rollback. If automatic detection is a requirement, define a separately controlled external anchor and its failure/availability semantics in a new approved design; do not invent one in this revision.

## Rechecked items

- F01: §22.1 explicitly supersedes conflicting clauses in §§4.2–4.3 and §21, forbids `RECONCILED_COMPLETE`, and limits the retained watermark to a non-authoritative progress cursor. The earlier inventories remain textually stale, but the precedence clause is explicit. No current-profile completeness PASS is authorized.
- F02-R1: closed 17-key checkpoint schema, immutable per-sequence path, counter snapshot binding, no-replace publication and restart directory barriers are specified. This is local crash-recovery design only. Full-root rollback detection remains unavailable as detailed in F02-R2.
- F05-R1: raw-body and envelope identities are separately defined; projection digest omits `evidence_id`; manifest reference target is clear in §22.11.4 but not reconciled with §21.5, so not closed across the full contract.
- F04: §22.9 is the sole initialization/evidence-envelope schema inventory; §§22.10 and 22.11 provide precedence. Parser implementation remains absent.
- F03/F06/F07: local Linux/flock/no-replace/fsync design requirements exist; actual target filesystem/provider behavior remains NOT VERIFIED.
- C125–C132: scenarios are present as design text only. C131 does not explicitly state that a raw-body ID must be rejected when used in the manifest even if the raw-body object exists and hashes correctly; add that exact assertion with F05-R2.
- REST completeness oracle remains NOT ACCEPTED; producer decimal conversion defect remains CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity remains NOT VERIFIED.

## Evidence and limits

- Exact reviewed contract blob: `f78dc4410db61755149cb6a7e0c440330bc80741`.
- P1.16 self-review remains same-session; this P1.17 review is also same-session.
- C01–C132 remain NOT IMPLEMENTED / NOT EXECUTED.
- No source implementation, tests, GitHub Actions run, artifact, Binance REST, VPS/runtime or T1 activation is evidenced.
- No claim is made that this review proves filesystem durability or market-data completeness.

## Required next actions

1. Fix F05-R2 in §21.5 and the §22.11 precedence statement; add a negative fixture for a manifest that points directly to a valid Raw-body object instead of the Envelope-record object.
2. Clarify F02-R2: local checkpoints support crash recovery only under an explicit no-full-root-rollback assumption; automatic full-root rollback detection is unavailable without an independent monotonic anchor. Add a fixture for the known/suspected restore decision and keep automatic detection NOT PROVIDED.
3. Self-review the corrected exact contract SHA.
4. Only then retarget/update issue #138 for independent review.

## Authorization boundary

Review only. No T1 source edits, adapter implementation, test execution, GitHub Actions dispatch, Binance REST, VPS/runtime, T1 activation, T0/T2 changes, strategy/AI/ledger/risk/trading changes, deletion, archive, cleanup, vacuum, compaction, backup expiry, restore or destructive operation.

T0 remains independent/canonical. No T1 writes to T0. Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.
