# P1.19 — Adversarial follow-up review of P1.18 rollback recovery semantics

Date: 2026-11-09
Review type: Same-session static adversarial self-review; NOT independent.
Exact normative contract blob SHA reviewed: `984f7669f4dae5902b852b6f6fa1c09d799f9957`
Contract commit: `d6610f571417873e4c0b74dd770f705c86b24a56`
Prior review: P1.18, blob `960016187f1311d9d540a8f0c20340c8df31151c`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

## Verdict

**REQUEST CHANGES — P1.18's F05-R2 and F02-R2 core clarifications are present, but a remaining restore/recovery-epoch ambiguity in §18.3 versus §22.11.2 and imprecise "independently trusted latest counter/checkpoint" wording in §21.5 leave the required post-restore identity transition underspecified.**

This review is same-session and is not an independent review. No contract or issue update is made in this review.

## Finding

### F02-R3 — Restore epoch requirement is not harmonized across §18.3, §21.5 and §22.11.2
Severity: MEDIUM
Disposition: OPEN — REQUIRED

Evidence:
- §18.3 line 464 says restoration of an older backup requires a separately recorded restore epoch/reconciliation decision and a **new generation**.
- §21.5 line 591 says restoring/copying a root without an independently trusted latest counter/checkpoint cannot claim continuity; it says assign a new `source_root_id` and quarantine/reconcile under a separately approved restore procedure.
- §22.11.2 line 810 says known/suspected full-root rollback requires quarantine and resumption through a separately approved new `source_root_id`/**recovery epoch** and fresh reconciliation.
- §22.11's precedence statement supersedes §§21.5, 22.5, 22.6.1 and 22.9, but does not expressly harmonize §18.3.

Risk:
An implementer following the older generic §18.3 sentence could treat a new generation plus restore marker as sufficient, while §22.11.2 requires a new source-root identity/recovery epoch for known or suspected full-root rollback. The stronger rule is present, but the cross-section operational instruction is not single and explicit. In addition, §21.5's phrase "independently trusted latest counter/checkpoint" can be misread as allowing a local checkpoint to qualify as independent, although §22.11.2 correctly says a checkpoint in the same root is not an independent anchor.

Required correction:
1. Amend §18.3 to distinguish ordinary generation recovery from a known/suspected full-root restore/clone/snapshot rollback. For the latter, explicitly require quarantine, a separately approved new `source_root_id` and recovery epoch, and fresh reconciliation; a new generation alone is insufficient.
2. Clarify §21.5 that only an independently controlled anchor outside the source-root rollback domain can establish latest-state continuity; local counter/checkpoint/receipt/manifest/data cannot.
3. Add a fixture for a known full-root restore where the operator proposes only a new generation under the old `source_root_id`; reject that recovery path and require the new-root/recovery-epoch procedure.
4. Re-review the corrected exact contract SHA before any further issue retarget.

## Rechecked P1.18 scope

- F05-R2: §21.5 field inventory and resolver point to Envelope-record ID; Raw-body object is reached through envelope `raw_body_sha256`; §22.11 precedence includes §21.5; C133 tests direct Raw-body reference rejection. No new contradiction found in the inspected resolver chain.
- F02-R2: §22.11.2 correctly states local checkpoint/counter do not detect/prevent full-root rollback; automatic detection is NOT PROVIDED; known/suspected rollback from an independent signal requires quarantine. The residual issue is the post-quarantine recovery identity transition and its consistency with §18.3/§21.5, not the stated detection limitation.
- F01: §22.1 explicitly supersedes §21 and prohibits current-profile `RECONCILED_COMPLETE` and `reconciliation_evidence_ref`; the older §21.5 inventory is therefore not the active completeness schema.
- C133–C135 are design specifications only, NOT IMPLEMENTED / NOT EXECUTED.
- F07 target filesystem/provider behavior remains NOT VERIFIED.
- Binance REST completeness oracle remains NOT ACCEPTED.
- Pinned producer f64 conversion, fixed 12-decimal formatting and parse-error-to-zero defect remains CONFIRMED / NOT FIXED.
- Producer FINAL_ONLY/product identity implementation remains NOT VERIFIED.

## Limits and authorization

No source implementation, tests, GitHub Actions dispatch, Binance REST, VPS/runtime, T1 activation, T0/T2 changes or destructive operations were performed. C01–C135 remain NOT IMPLEMENTED / NOT EXECUTED. This review does not establish implementation readiness or independent review.

T0 remains independent/canonical. No T1 writes to T0. Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement. No implementation or issue retarget is authorized by this review.
