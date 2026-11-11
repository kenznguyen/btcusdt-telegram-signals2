# G0.50 — D12/D13/D14 Audit Custody, Verified-Facts Binding and Stage-Gate Owner Decision Package

Date: 2026-11-11 (Asia/Ho_Chi_Minh)
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/t0-centralized-data-feeder-p1-20261101
Baseline: 2b4e59a59faebb34b0d62a658d08fa95ece68ffa
Related decisions: G0.26, G0.28, G0.31, G0.44, G0.45, G0.47, G0.49
Type: documentation-only owner decision package
Disposition: **PACKAGE PREPARED — D12/D13/D14 OPEN / NOT RATIFIED; S2 IMPLEMENTATION NOT AUTHORIZED**

## 1. Purpose and controlling decisions

G0.49 recorded D07-A, D08-A and D09-A as initial-phase Owner decisions. D06 remains manual Owner attestation only; D01–D04 retain their selected minimal/conditional/deferred posture. G0.44 ratified S1 parser resource ceilings and G0.45 implemented only the synthetic parser contract.

This package presents bounded options for the remaining D12, D13 and D14 decisions. Recommendations are not decisions. No implementation or stage-transition authority is granted.

Controlling distinctions remain:
- integrity is not authenticity;
- platform-attributed Owner action is not cryptographic signature;
- Owner review is not privileged-action authorization;
- inventory completeness is not freshness;
- verified facts are not execution authority;
- CI success is not production/runtime acceptance.

## 2. D12 — Audit custody, retention, redaction and readback

### Problem and claim boundary

A record existing in GitHub or an Actions artifact does not, by itself, prove durable custody, independent recoverability, complete audit history, or tamper-evident ordering. Artifact metadata is not independent payload readback. Retention and redaction must not erase the evidence needed to explain a prior decision.

### Candidate minimum contract

1. Define the audit record classes and the claims each class supports: decision record, evidence manifest, verification result, authorization, supersession/revocation, custody/readback receipt, and operational diagnostic.
2. Bind each record to an immutable identifier, exact bytes/digest, schema/version, subject/scope, decision or event type, and references to preceding/superseded records where applicable.
3. Distinguish storage location, custodian, retention rule, integrity mechanism, ordering/sequence claim, retrieval procedure and independent readback evidence. Do not infer one from another.
4. Record redaction as a separate, attributable event that identifies the affected record/version, redaction reason/category and retained digest/reference. Never silently rewrite historical evidence.
5. Keep secrets and RESTRICTED values out of ordinary evidence and CI output. Preserve the G0.17 most-restrictive inheritance and no-auto-downgrade policy.
6. Do not claim durable custody or recoverability until exact bytes have been retrieved and independently re-hashed/read back from the claimed custody domain.
7. Retention expiry or deletion requires a separate exact-scope Owner authorization, preconditions, impact analysis, verification and recovery plan. D12 alone must not authorize cleanup or deletion.

### Owner options

- **D12-A (recommended initial policy):** maintain an append-only logical audit history in the existing approved GitHub repository/commit history for decision records; record artifact IDs/digests and expiry metadata where applicable; independently read back and hash any artifact before making a custody/readability claim. State clearly that this is GitHub-domain custody only, not independent backup or disaster recovery. No automated retention deletion or redaction rewrite.
- D12-B: introduce a separately approved second custody domain and periodic independent readback. This adds cost, credentials and operational responsibility; defer until a concrete recovery requirement exists.
- D12-C: claim durable custody based on GitHub commit/artifact metadata alone. Not recommended and must not support independent custody/recoverability claims.

### Questions to ratify

- Is D12-A acceptable as the initial audit-custody posture, with GitHub-domain limitation stated?
- Must every custody/readability claim require exact payload readback and digest verification? Recommended: yes.
- Should retention durations, automatic expiry/deletion and a second custody domain remain unratified? Recommended: yes.
- Should redaction be represented by a new linked event rather than rewriting prior decision evidence? Recommended: yes.

No retention period, backup cadence, recovery-point objective, recovery-time objective or deletion schedule is proposed or ratified.

## 3. D13 — Verified-facts binding and process boundary

### Problem and claim boundary

G0.21 found that caller-controlled booleans and generic mappings could assert identity, provenance, completeness, rebuildability and authorization without independent verification. A plain object passed from one function/process to another is not a trust boundary. A verified-facts envelope must not be forgeable, detached from its source subject, replayed for a different evaluation, or mistaken for execution permission.

### Candidate minimum contract

1. Bind facts to exact subject identifier/type/version, source identity/reference, immutable evidence digest(s), evidence class, claim type and declared scope.
2. Bind the verification result to verifier contract/schema version, policy/profile version, verifier build/source identity, evaluation identifier and the exact set of evidence references consumed.
3. Carry separate claim dimensions: byte integrity, issuer authenticity (only if required and verified), Owner attribution/authorization, inventory completeness, freshness level and custody/readback. Unknown or inapplicable dimensions must be explicit; never collapse them into a single trusted boolean.
4. Prevent caller construction or mutation of a verified-facts result across the trust boundary. The verifier alone creates the result after validating exact inputs; consumers validate provenance and binding before use.
5. Define immutability and serialization rules. If the envelope crosses a process boundary, authenticate/bind exact serialized bytes and reject unknown fields, duplicate keys, schema drift and malformed representations.
6. Define evaluation binding and reuse semantics: a result is valid only for its named subject, evidence set, policy, purpose and evaluation context. Cross-subject, cross-purpose or stale-policy reuse must fail closed.
7. Define freshness revalidation separately under D08. A verified-facts envelope cannot manufacture a trusted time anchor or override FRESHNESS_UNKNOWN.
8. State explicitly that the result is descriptive verified evidence only. It cannot authorize deletion, retention changes, key operations, deployment, trading or any other action.

### Owner options

- **D13-A (recommended):** require a versioned, immutable, exact-subject/evidence/policy/evaluation-bound envelope; verifier-only construction; consumers reject mismatches and unknown claim states; no generic trusted boolean; no execution authority.
- D13-B: keep a process-local opaque verifier result for the first synthetic-only test milestone and defer cross-process serialization. This is simpler but must be explicitly limited to one process and cannot support real adapters or process-to-process trust claims.
- D13-C: pass generic dictionaries/mappings with caller-supplied trust booleans. Reject; this recreates the G0.21 trust-boundary findings.

### Questions to ratify

- Is D13-A the required target contract for any future verified-facts consumer?
- May D13-B be used only for a separately approved synthetic-only, single-process test milestone, with no production/trust claims?
- Must verifier-only construction and exact subject/evidence/policy/evaluation binding be mandatory? Recommended: yes.
- Must verified facts remain non-authorizing and freshness be independently evaluated? Recommended: yes.

No serialization format, schema, constructor capability, IPC protocol, cryptographic envelope, process isolation mechanism or production adapter is selected here.

## 4. D14 — Review, implementation, verification and release gates

### Problem and claim boundary

D14 must prevent a documentation decision, a successful unit test, or a CI run from silently authorizing a larger stage. Each stage needs its own exact scope, evidence, source pin, side-effect limits and explicit transition decision.

### Candidate gate model

For every future executable increment, require a pre-implementation owner package that states:
- stage and exact objective;
- exact allowed and forbidden paths;
- baseline commit and required source/blob pins;
- exact commands, test matrix and expected outcomes;
- runtime, filesystem, network, credential and provider permissions;
- test data classification and synthetic/production boundary;
- resource ceilings and failure/stop conditions;
- evidence artifacts and required independent payload readback;
- claims the result may and may not support;
- rollback/recovery and next-stage boundary.

After implementation, record:
- exact source SHA and changed paths;
- exact workflow run, event, checkout SHA, jobs and test counts;
- artifact ID/name/size/expiry and payload digest/readback status;
- PASS/BLOCKED/NOT VERIFIED per gate;
- deviations, failed attempts and residual risks;
- explicit next step and non-authorizations.

A successful gate closes only its named scope. The next stage requires a separate explicit Owner decision. No approval is inferred from “continue”, CI success or a previous stage's approval.

### Owner options

- **D14-A (recommended):** strict per-increment owner approval. Docs-only preparation may proceed within its explicit scope; any executable S2 work, workflow/permission change, real evidence adapter, provider/runtime operation or lifecycle action requires a separate exact-scope approval. CI and source checks are necessary evidence but never substitute for Owner authorization.
- D14-B: pre-authorize a bounded sequence of synthetic-only S2 substeps with fixed paths, commands and stop conditions, but only after D01–D05, D10–D13 dependencies are closed and the Owner explicitly approves the complete sequence.
- D14-C: allow automatic progression from a passing test/workflow to the next stage. Reject; it collapses verification into authorization and permits scope escalation.

### Questions to ratify

- Is D14-A the default stage-transition rule?
- Must every executable stage and every real-source/runtime operation receive separate exact-scope Owner approval? Recommended: yes.
- May a bounded standing authorization ever be used only when exact paths, commands, source pins, stop conditions and expiry/completion boundary are fixed in advance? Recommended: possible, but only by explicit separate approval.
- Must CI PASS never be treated as owner acceptance, production trust, custody proof or runtime acceptance? Recommended: yes.

## 5. Cross-decision consistency

- D06/D09: initial Owner attestation is manual and platform-attributed; no autonomous issuer key or cryptographic Owner signature.
- D07: inventory completeness requires independent expected/observed reconciliation.
- D08: no global freshness claim without a trusted anchor; freshness-dependent uses fail closed.
- D12: custody/recoverability claims require exact readback; GitHub-only evidence remains within the GitHub failure domain.
- D13: verified facts bind exact evidence and policy but do not confer authorization.
- D14: no automatic stage transition; each executable/operational scope needs explicit approval.
- D05/D10/D11 and the S1 parser remain synthetic-only. D11 limits are ratified, but do not imply production verifier limits or authorize implementation.
- G1 A remains unsigned proof-of-existence; A1 remains a separate extension.

## 6. Proposed owner selections (not ratified)

| Decision | Recommended initial selection | Status |
|---|---|---|
| D12 | A: GitHub-domain append-only logical history; exact artifact readback/hash before custody claims; no automatic deletion or silent rewrite. | OPEN |
| D13 | A: immutable exact-subject/evidence/policy/evaluation-bound verified-facts envelope; verifier-only construction; no generic trust boolean; no execution authority. | OPEN |
| D14 | A: strict per-increment Owner approval; each executable stage/real-source/runtime operation separately approved; CI never substitutes for authorization. | OPEN |

## 7. Explicit non-authorizations

This package authorizes documentation preparation only. It does not authorize:
- any source, parser, verifier, schema, fixture, test, API, adapter, registry, serialization, IPC, workflow or CI permission change;
- synthetic cryptographic test keys, real keys, signing, verification, trust roots, anchor or revocation services;
- inventory collection from GitHub beyond the repository documentation read needed to prepare this package, or from VPS/T0/T1/T2/databases/providers;
- artifact retention changes, deletion, archive, cleanup, expiry, compaction, VACUUM, redaction execution or other destructive lifecycle action;
- second custody-domain provisioning, backup service, provider or external network access;
- T0/T1/T2, CORE_LEDGER, AI_LEDGER, Shared Risk Engine, Kill Switch or trading runtime changes;
- deployment, exchange connection, live trading or real orders.

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged. VPS remains absent; no runtime state is inferred.

## 8. Verification and disposition

- Scope: documentation-only owner decision package.
- Tests/compile/CI: NOT RUN; no executable code changed.
- Runtime/VPS/database/provider/key operations: NOT PERFORMED.
- Independent reviewer sign-off: not mandatory under the existing Owner waiver; no independent assurance claim is made.

**G0.50: PACKAGE PREPARED — D12/D13/D14 RECOMMENDATIONS READY FOR OWNER DECISION; ALL THREE OPEN / NOT RATIFIED; S2 IMPLEMENTATION NOT AUTHORIZED.**

Next: Owner selects or amends D12, D13 and D14. Record explicit decisions before preparing any implementation package. No automatic progression to S2.
