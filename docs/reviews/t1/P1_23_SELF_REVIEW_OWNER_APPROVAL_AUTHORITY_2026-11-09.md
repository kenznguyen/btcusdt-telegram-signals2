# P1.23 — Adversarial self-review of P1.22 owner-approval authority

Date: 2026-11-09  
Review type: Same-session static adversarial self-review; NOT independent.  
Exact normative contract blob reviewed: 20e8b31db364a15b73359810664f7e079aa86bc7  
Prior review: P1.22 blob f3fca61dfd5d139e97a8b25fb34023c7e2f629ed  
Branch: feature/t0-centralized-data-feeder-p1-20261101

## Verdict

**REQUEST CHANGES — F02-R5 HIGH: the rollback-recovery owner-approval record is content-pinned but its authority/authenticity is not verifiable under the current contract.**

The P1.22 correction establishes a closed approval-record schema, commit-pinned repository path, exact-byte SHA-256 binding, and scope restrictions. It does not establish that the person named by `approver_github_login` is an authorized owner/approver or that the record was approved by that identity.

## Finding F02-R5 — HIGH

### Evidence in the exact contract

Section §22.9 defines:
- `owner_approval_record_ref` as a GitHub repository path pinned to a commit SHA;
- `owner_approval_record_sha256` as the digest of the exact approval-record bytes;
- `approver_github_login` as a non-empty exact GitHub login;
- an approval decision and exact isolated-only v1.1 scope.

The same section explicitly says GitHub commit/blob immutability and recorded account metadata are governance evidence only, not a cryptographic signature, independent monotonic anchor, or proof against repository-owner compromise.

### Adversarial path

A repository writer who is not an authorized recovery approver can create a new commit containing an approval JSON record, set `approver_github_login` to the owner's login, choose the required decision/scope, and compute the matching blob SHA-256. The record is then immutable and internally consistent, but the contract provides no mandatory check that:
1. the named login actually authored/approved this exact decision;
2. that login was in an owner-controlled allowlist or had the required repository authority at approval time;
3. the approval was an actual GitHub review/approval event rather than self-asserted JSON;
4. the record has not been committed by another account with write access.

A commit SHA pins content; it does not by itself authenticate the human approval represented by a JSON field. The exact-byte digest proves integrity of the selected file, not authority of its author. This weakness exists even without compromising the repository owner account if another principal can write to the repository.

### Required correction before claiming an enforceable approval gate

Define a verifiable approver-authority mechanism and its failure semantics. At minimum, choose and specify one auditable mechanism, for example:
- a cryptographically signed approval payload verified against an owner-controlled public key pinned outside the source-root rollback domain; or
- a GitHub approval/review record whose actor identity, exact reviewed commit/path/blob, approval state, and authority at approval time are retrieved and verified through an explicitly trusted GitHub API/evidence process, with unavailable or ambiguous evidence failing closed.

The contract must define the trusted authority source, approver allowlist/role, exact bytes or object IDs being approved, revocation/rotation behavior, API/key unavailability, replay prevention, and how the approval evidence is retained and verified. Do not describe a self-asserted `approver_github_login` field as sufficient owner approval.

This correction must not introduce a false claim that GitHub is an independent anti-rollback anchor. The approval-authority mechanism and the anti-rollback continuity anchor are separate concerns.

## Other checks

- P1.22 exact contract blob was re-fetched: `20e8b31db364a15b73359810664f7e079aa86bc7`.
- Root initialization has twelve keys and binds a distinct recovery_epoch_id.
- Recovery-epoch record has eight keys; the rollback approval record has ten keys.
- Publication counter has six keys; checkpoint and historical counter snapshots bind the epoch.
- Current v1.1 post-recovery state remains limited to separately approved UNKNOWN/unsealed/non-canonical isolated collection.
- F01 prohibition on RECONCILED_COMPLETE, reconciliation_evidence_ref, canonical sealing, completeness watermark, T0 promotion and aggregation remains explicit.
- C137–C140 remain design-only negative fixture specifications.
- F05 Envelope-record vs Raw-body namespace rule remains intact.
- Automatic detection of an unobserved internally consistent full-root rollback remains NOT PROVIDED.

## Disposition and authorization

- F02-R5: REQUEST CHANGES.
- P1.22 F02-R4/F01-R2 corrections remain documentation-level PASS within their narrower scope; they do not close F02-R5.
- Do NOT claim the full-root rollback approval gate is enforceable until F02-R5 is corrected and re-reviewed.
- Keep issue #138 OPEN and pointed at the exact P1.22 contract SHA for genuinely independent review; add F02-R5 to its review questions. Do not retarget to a new contract SHA until a separately approved correction and exact-SHA self-review pass.
- No implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, trading or destructive data operations are authorized or claimed.

T0 remains independent/canonical. No T1 writes to T0. Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.
