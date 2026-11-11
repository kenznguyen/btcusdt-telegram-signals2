# G0.21 — Lifecycle Evaluator Trust-Boundary Review

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Review baseline / starting HEAD: `aa83cea155b4543ed8779583a212fb0b68f3f206`  
Scope: documentation-only security and trust-boundary review of the pure lifecycle disposition evaluator and its ratified policy inputs.

## 1. Executive disposition

**Verdict: CONDITIONAL / TRUST NOT ESTABLISHED.**

The evaluator is correctly narrow as a deterministic, in-memory classifier with no filesystem, database, network, clock, process, registry or execution capability. It preserves the five dispositions and emits `mutation_performed=false` and `execution_authorized=false`.

However, its inputs are claims supplied by its caller. The evaluator validates shape and selected consistency rules; it does not authenticate the claimant, prove that the claimant is authorized to assert a fact, retrieve the referenced evidence, verify its signature, recompute the payload digest, or prove that an inventory is complete. Therefore its positive outputs are only as trustworthy as an upstream evidence-verification boundary that does not yet exist in this scope.

**The evaluator must not be treated as an evidence verifier, authorization decision, or deletion approval.** No positive disposition currently authorizes any mutation.

## 2. Exact reviewed baseline

- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Starting HEAD: `aa83cea155b4543ed8779583a212fb0b68f3f206`.
- Evaluator: `pipeline/lifecycle_disposition.py`, blob `cf22385a718c6b5b08cd50c2a45578b4180c2c4d`.
- Unit tests: `pipeline/test_lifecycle_disposition.py`, blob `d54d0523d6388df448cbec7c2fb9e2e092f72920`.
- G0.20 exact-source verification: run `43036222952`, job `130575627133`, SUCCESS; 32/32 focused tests and `py_compile` PASS. This establishes execution of those exact blobs, not authenticity of future runtime metadata.
- Sensitivity policy: G0.17 owner-ratified report, blob at the ratification evidence recorded in the handoff; vocabulary `PUBLIC < INTERNAL < CONFIDENTIAL < RESTRICTED`, with `UNCLASSIFIED`, `CONFLICTED`, `PENDING_OWNER_DECISION` as non-label states.
- Lifecycle precedence and reason-code specification: G0.12, as recorded in the handoff.

This review is source-based and documentary. It did not access production data, a VPS, database, provider, credentials, external evidence store or runtime inventory.

## 3. Trust-boundary map

| Boundary | Data / claimant | Current evaluator behavior | Trust status |
|---|---|---|---|
| Caller → evaluator | Entire `record` mapping | Checks Mapping and selected field types/values | Caller identity and authority NOT AUTHENTICATED |
| Identity claim | `identity_verified`, object/version/namespace | Accepts boolean `True` plus non-empty strings | Assertion only; no identity proof |
| Classification claim | `data_class`, sensitivity state/label | Checks supported values and minimum label | Semantics validated; classification authority/evidence NOT VERIFIED |
| Evidence references | `evidence_ref`, revisions, integrity digest | Checks non-empty refs and digest syntax/length | Does not retrieve, hash, sign or authenticate evidence |
| Provenance / lineage | `producer_provenance_verified`, lineage fields | Accepts booleans and supplied identifiers | Producer and transformation provenance NOT VERIFIED |
| Completeness claims | `holds.complete`, `dependencies.complete`, `copies.complete`, `lineage.complete` | Trusts supplied booleans and arrays | Cannot prove omitted records do not exist |
| Rebuildability / material use | `rebuildability.proven`, `material_decision_use` | Trusts supplied assertions after shape checks | No independent replay or decision-ledger reconciliation |
| Evaluator → caller | Disposition + reason codes | Returns deterministic classification and fixed false authority flags | Caller can ignore result; no authorization enforcement boundary |
| Caller → future executor | Any proposed action | No executor exists in reviewed module | Separate future security boundary; not in scope or authorized |

Trust follows the writer of each value, not the fact that it arrived as a Python mapping or from an internal process.

## 4. Findings

### F-01 — Caller-controlled identity and provenance booleans

**Severity: CRITICAL architectural trust gap before any positive eligibility use.**

The evaluator accepts `identity_verified is True` and, for T1, `producer_provenance_verified is True`. These booleans are not backed by a verifier, authenticated principal, signed producer attestation or immutable source binding inside this module. A caller able to construct a record can assert these values.

**Required boundary:** the evaluator must receive a verified-facts object produced only by an upstream verifier that authenticates the evidence issuer and binds the claim to the exact object ID, immutable version, namespace, producer identity and source commit/artifact. A caller-supplied boolean must never itself be the proof.

### F-02 — Evidence references and digest are not evidence verification

**Severity: HIGH.**

`_unknowns` checks that the digest algorithm is `sha256`, that the digest is 64 lowercase hexadecimal characters, and that byte length is a non-negative integer. It does not receive payload bytes, recompute the digest, resolve the evidence reference, or verify a signature. `evidence_revision` is only checked as non-empty text. Sensitivity evidence references/revisions are similarly not resolved or authenticated.

**Required boundary:** verify the exact bytes or canonical evidence envelope outside the pure evaluator; recompute the digest; bind digest, byte length, object/version, evidence revision, issuer, policy version and purpose; verify an authenticated signature/attestation before materializing the verified facts. The algorithm, canonical encoding, signature profile and key custody must be separately specified and approved; this review does not select them.

### F-03 — Completeness booleans do not prove inventory completeness

**Severity: HIGH.**

The evaluator treats `complete=True` plus a supplied list as complete hold, dependency, copy and lineage inventories. It can validate records that are present, but cannot prove that an omitted consumer, backup, replica, hold, writer, derived object or sibling copy does not exist. A malicious or incomplete producer can submit a self-consistent but truncated inventory.

**Required boundary:** inventories must be generated from an authoritative, scoped registry or independently reconciled source; include a signed snapshot/revision and scope definition; verify expected partitions/cursors/counts and closure evidence. Missing or inaccessible source registries must remain `BLOCKED_UNKNOWN`. A caller must not self-certify completeness.

### F-04 — Sensitivity labels and inheritance are caller assertions

**Severity: HIGH.**

The evaluator enforces ratified label ordering and minimums for the identifiers it supports. For `NONCANONICAL_COPY`, it compares the assigned label with caller-supplied `inherited_labels`. It does not resolve parent/source records, verify the parent chain, or authenticate the owner decision that assigned a label. Thus it proves only internal consistency of the supplied claims, not G0.17 inheritance compliance in the underlying data.

**Required boundary:** resolve exact source/parent versions from authenticated lineage; compute the effective label as the most restrictive applicable source/parent/content/policy context; bind the result to the verified lineage snapshot. Unknown, stale, contradictory or unauthenticated labels remain fail-closed and are handled as RESTRICTED pending resolution under G0.17. No automatic downgrade.

### F-05 — Steward and policy references lack authenticated authority

**Severity: HIGH.**

A non-empty `steward`, `policy_id` and `policy_version` are accepted when they match the hardcoded RET-01 B / RET-02 B set. The evaluator does not prove the steward is the accountable owner, that the record was issued by that steward, or that the policy revision is the current ratified one for the asserted scope.

**Required boundary:** authenticate the issuer/owner identity and authority for the exact data domain; bind the verified policy identifier/version and policy content digest to the decision record. Do not infer owner approval from a name string, repository write access or CI success.

### F-06 — Rebuildability and non-material-use assertions are not independently proven

**Severity: HIGH for reviewability decisions.**

The evaluator checks `rebuildability.proven`, a non-empty evidence reference and `material_decision_use` values. It does not reproduce the object from exact retained inputs/code/configuration or reconcile signals, risk decisions, ledgers, audit evidence and downstream claims. `material_decision_use=NO` is therefore a caller assertion.

**Required boundary:** require a reproducibility proof bound to exact input and transform versions, plus authoritative downstream-use reconciliation. For T2 inference outputs, absence of a known use is not proof of non-use. Unknown use remains `BLOCKED_UNKNOWN`; known material use remains retained until obligations close.

### F-07 — Pure output does not enforce downstream authorization

**Severity: CRITICAL if any future caller interprets reviewability as permission to delete.**

The evaluator has no executor capability, which is a valuable boundary. But `REVIEWABLE_NONCANONICAL` and `COPY_SPECIFIC_REVIEW` are review classifications only. A caller can ignore `execution_authorized=false` or treat the disposition as an action command.

**Required boundary:** maintain separate stages: (1) authenticated evidence verification, (2) pure disposition evaluation, (3) exact-object human/owner authorization, (4) independently guarded action executor with exact target, allowlisted scope, preconditions, revalidation immediately before action, audit evidence and recovery/rollback. No executor is approved by this review. No output from the evaluator may be translated directly into a delete/archive/cleanup command.

### F-08 — Supported class vocabulary is intentionally incomplete

**Severity: MEDIUM / integration blocker.**

The evaluator currently supports a finite set of protected and review classes. Its sensitivity minimum map covers the currently represented identifiers, not every G0.17 semantic domain (for example, distinct T1 sidecar/provenance evidence, T2 canonical snapshots/features/training datasets/model artifacts, and synthetic CI evidence). Unsupported classes fail closed, which is correct; however, consumers must not assume this module classifies every project data domain.

**Required boundary:** before any broader integration, ratify an exact machine-readable mapping for each additional identifier and its semantic domain. Do not alias a class based on similar naming or infer a minimum. No new enum or mapping is created in this gate.

### F-09 — Generic Mapping input is not a canonical authenticated record contract

**Severity: MEDIUM.**

The function accepts any `collections.abc.Mapping`, then calls mapping methods throughout. The source does not define a canonical serialized record schema, duplicate-key behavior, unknown-field policy, size limits, or a verifier-produced immutable type. The pure function is safe from its own I/O, but input construction and custom Mapping behavior are outside its guarantee.

**Required boundary:** define a versioned, bounded, exact-field evidence envelope at the future ingestion boundary; reject malformed/duplicate/unknown critical fields; parse into a plain immutable materialized value only after authenticity checks. Do not add such a schema in G0.21.

## 5. STRIDE summary

| Threat | Example against current boundary | Required control before integration |
|---|---|---|
| Spoofing | Caller sets `identity_verified=True` or invents steward | Authenticated issuer identity and scoped authority |
| Tampering | Payload changes while digest string remains unchanged | Recompute digest over exact bytes; authenticated signature/attestation |
| Repudiation | Steward denies classification or release assertion | Tamper-evident, attributable decision/audit record |
| Information disclosure | RESTRICTED metadata or secret values copied into CI artifacts | Field allowlists; never include secret values; sensitivity-aware evidence outputs |
| Denial of service | Oversized/deep records or pathological custom Mapping | Bounded serialized envelope, field/array/byte caps, time/resource limits at ingress |
| Elevation of privilege | Caller maps REVIEWABLE to deletion or forges completeness | Separate owner authorization and guarded executor; no evaluator-derived authority |

## 6. Recommended target architecture (design only)

1. **Claimant / source adapters:** collect raw facts and evidence references; treat every field as untrusted.
2. **Evidence verifier:** authenticate issuer and authority; resolve exact immutable evidence; recompute payload digest; validate signature/attestation; verify object/version/producer/policy bindings; verify inventory scope/completeness and freshness according to a separately approved policy.
3. **Verified-facts envelope:** materialize only verified, bounded, versioned facts with provenance to the verifier result. The caller cannot set a trusted boolean directly.
4. **Pure evaluator:** retain its current role; evaluate the verified facts deterministically. It must not perform evidence retrieval or cryptographic I/O.
5. **Owner authorization:** separate, explicit approval for an exact object/version and action. Reviewability is not authorization.
6. **Executor (future, separately approved):** independently enforce allowlisted root/target, exact object identity, minimum path depth, ownership evidence, symlink/race protections, precondition revalidation, immutable audit and recovery/rollback. This is not authorized or designed in implementation detail here.

No signature algorithm, key hierarchy, trust root, canonical byte format, timestamp/freshness window, revocation protocol, physical registry, schema or executor contract is selected by this review.

## 7. Gate and status matrix

| Area | G0.21 disposition |
|---|---|
| Pure evaluator boundary (no I/O/executor) | PASS by source inspection |
| Caller identity / issuer authentication | NOT ESTABLISHED |
| Evidence digest recomputation / signature validation | NOT IMPLEMENTED / NOT VERIFIED |
| Provenance and exact-version binding | NOT ESTABLISHED |
| Hold/dependency/copy inventory completeness | NOT ESTABLISHED |
| Sensitivity parent/source inheritance authentication | NOT ESTABLISHED |
| Steward/owner authority | NOT ESTABLISHED |
| Rebuildability and non-material-use proof | NOT ESTABLISHED |
| Downstream authorization separation | DESIGN REQUIREMENT; no executor |
| Full project data-class coverage | NOT ESTABLISHED; unsupported values fail closed |
| Canonical input envelope/schema | NOT DEFINED |
| TEST-01–07 | 0/87; no status promotion |
| Runtime/VPS inventory | NOT PERFORMED / NOT VERIFIED |
| Destructive authority | NOT GRANTED |

## 8. Required closure sequence

The following are separate future gates; this report does not authorize their implementation.

- **G0.22 — Verified-facts envelope and verifier contract:** define issuer identity/authority, exact evidence binding, digest/signature verification, inventory scope/completeness, policy/version binding, freshness/revocation semantics and failure behavior. Keep cryptographic and key-management choices explicit for owner decision.
- **G0.23 — Synthetic verifier contract tests:** use wholly synthetic fixtures only; include forged booleans, wrong issuer, tampered bytes, mismatched object/version, stale/revoked evidence, omitted inventory entries, conflicting sensitivity inheritance, untrusted steward and malformed/oversized input. Exact fixture paths, commands and CI permission must be separately approved.
- **G0.24 — Pure evaluator adapter review:** only after verified-facts contract is ratified, assess the smallest adapter that passes verified facts to the existing pure evaluator. No registry or runtime access by default.
- **TEST-01–07 / 87 vectors:** separate plan, implementation and approvals; current 0/87 remains.
- **Runtime inventory and any destructive executor:** separate bounded approvals. No deletion, archive, cleanup, expiry, compaction, vacuum or provider action is authorized.

## 9. Explicit non-actions

Documentation-only review. No source, test, fixture, schema, API, registry, adapter, runner, oracle, workflow, scheduler, permission, credential, database, storage, market data, model, ledger, VPS or runtime changes. No test or workflow dispatch. No inventory, secret scan, network/provider/database/VPS access. No archive, quarantine, cleanup, expiry, compaction, vacuum or deletion.

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.

## 10. Final verdict

**G0.21: CONDITIONAL PASS — trust gaps identified and target boundary specified; no evidence authentication or production trust established.**

The current evaluator is suitable only as a pure classifier over already-materialized claims. Until an authenticated evidence-verification boundary is separately designed, implemented and tested, every supplied identity, provenance, completeness, sensitivity, steward, rebuildability and material-use fact must be treated as untrusted. No lifecycle action may be authorized from its disposition alone.
