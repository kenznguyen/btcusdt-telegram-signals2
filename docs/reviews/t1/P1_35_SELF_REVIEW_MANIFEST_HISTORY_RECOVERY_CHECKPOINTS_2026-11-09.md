# P1.35 — Exact-SHA adversarial self-review: manifest history versus recovery checkpoints

Date: 2026-11-09
Review type: Same-session adversarial static self-review; NOT independent.
Branch: feature/t0-centralized-data-feeder-p1-20261101
Exact normative contract blob reviewed: 0b4bef0ca9e0fdef7524dc3766cc32d897fa64ea
Prior self-review blob: 302939ee72397fa6893eaffb23f4042625b60edc

## Verdict

**REQUEST CHANGES — F02-R18 HIGH.**

The P1.34 review remains a limited DOCUMENTATION-LEVEL PASS for F02-R6 through F02-R17 and fixture inventory. It does not establish whole-contract consistency. This P1.35 review found a new contradiction in the publication-history and recovery-checkpoint contract.

## Finding

### F02-R18 HIGH — Earlier checkpoint manifests are overwritten but must remain retrievable

Evidence:

1. §21.5 defines one fixed manifest path, `manifest.json`, inside each generation directory.
2. §5.2 step 5 publishes each new manifest by atomically renaming the temporary manifest over that fixed manifest path. This replaces the previously visible manifest.
3. §22.11.1 defines an immutable recovery checkpoint for exactly one publication sequence and stores `manifest_sha256` for the exact manifest bytes associated with that publication.
4. §22.11.2 requires, for every checkpoint, that the exact referenced receipt and manifest still exist and validate.

Contradiction:

After publication sequence N+1 replaces `manifest.json`, the exact manifest bytes for sequence N are no longer available at the only manifest path specified by the contract. The checkpoint for N still binds the old manifest digest, while §22.11.2 requires the exact old manifest to exist and validate. The receipt directory stores commit receipts, not an explicitly specified immutable archive of prior manifest bytes. No alternate historical-manifest object path, retention rule, or checkpoint-embedded manifest is defined.

Consequences:

- A generation with more than one publication cannot satisfy the literal all-checkpoints validation rule after the manifest is replaced.
- Recovery can be forced to quarantine a valid multi-publication generation because historical manifest evidence is unavailable.
- An implementation that silently skips historical manifest verification would violate §22.11.2 and weaken the anti-ambiguity guarantee.

Required correction before another self-review:

Choose and specify one consistent immutable-history model, for example:
- persist each exact manifest version under a unique immutable per-publication path, with no-replace publication, file and parent-directory durability ordering, and checkpoint references to that object; or
- embed the exact canonical manifest bytes (or a fully sufficient immutable manifest record) in each checkpoint and define its digest/validation semantics.

Whichever model is selected must define:
- canonical path/object identity and exact digest input;
- publication ordering relative to receipt and checkpoint;
- no-replace/collision/orphan behavior;
- directory enumeration and completeness rules;
- crash points before/after each fsync/rename;
- retention/immutability requirements (no automatic cleanup);
- negative fixtures for missing, replaced, duplicate, mismatched and orphan historical manifests.

Add at least one negative/crash fixture covering publication N, checkpoint N, publication N+1 replacing the active manifest, followed by restart/recovery. The expected behavior must be deterministic and must not silently omit historical checkpoint validation.

## Scope and limits of this review

- Exact contract blob SHA was re-fetched from the active branch: `0b4bef0ca9e0fdef7524dc3766cc32d897fa64ea`.
- P1.34 self-review blob SHA: `302939ee72397fa6893eaffb23f4042625b60edc`.
- This is a same-session static review, not an independent review.
- No executable tests, GitHub Actions run/artifact, REST request, VPS/runtime, filesystem experiment or T1 activation was performed.
- No source implementation or contract correction was made in this review.

## Status and authorization

- P1.34 F02-R6–R17 / C146–C189: prior limited DOCUMENTATION-LEVEL PASS remains recorded, but whole-contract acceptance is blocked by F02-R18.
- P1.35: REQUEST CHANGES.
- Issue #138 must remain OPEN and must not be retargeted to a claimed passing revision on the basis of this review.
- F07 target filesystem/provider behavior: NOT VERIFIED.
- Binance REST completeness oracle: NOT ACCEPTED.
- Producer decimal defect (f64 conversion, fixed 12-decimal formatting, parse-error-to-zero): CONFIRMED / NOT FIXED.
- Producer FINAL_ONLY/product identity: NOT VERIFIED.
- ERA, root-key bootstrap, monotonic store and associated services: NOT IMPLEMENTED / NOT VERIFIED.
- C01–C189: NOT IMPLEMENTED / NOT EXECUTED.
- No implementation, executable tests, Actions dispatch, REST/VPS/runtime, T1 activation, T0/T2 changes, trading or destructive data operations are authorized.

T0 remains independent/canonical. No T1 writes to T0. Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.
