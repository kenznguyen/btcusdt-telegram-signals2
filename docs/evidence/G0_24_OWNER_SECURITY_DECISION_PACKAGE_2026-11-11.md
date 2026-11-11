# G0.24 — Owner/Security Decision Package for Lifecycle Evidence Verification

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Baseline HEAD: `9d46abb937fa553523e2f5c2dc564826f7a96b74`  
Scope: documentation-only decision worksheet. No policy choice is ratified by this report.

## 1. Executive disposition

**G0.24: DECISION PACKAGE DRAFTED — owner/security decisions remain OPEN; no cryptographic or operational trust profile is ratified.**

G0.21 identified trust-boundary weaknesses; G0.22 specified the logical verified-facts envelope and verifier contract; G0.23 defined 38 synthetic logical test cases. The next dependency is an explicit owner/security decision on the trust profile and evidence authorities before any verifier implementation.

This report converts the G0.22 open items into bounded decision records. It provides candidate directions and the consequences of each choice, but does not select a profile on the owner's behalf. Blank decisions remain blockers.

## 2. Authority and non-goals

### Included
- Enumerate the decisions required before a verifier can be implemented safely.
- Present candidate approaches, decision criteria, dependencies and fail-closed defaults.
- Separate owner decisions from security/engineering feasibility assessments.
- Define the evidence needed to record a ratified decision.

### Not approved or performed
- No signature/hash/canonical-encoding choice is ratified.
- No trust root, issuer, key, credential, secret, provider, registry or evidence store is created or changed.
- No physical schema, parser, verifier, verified-facts type, adapter, API, registry, test fixture or source code is implemented.
- No executable G0.23 tests, CI workflow, workflow dispatch, TEST-01–07 or G0.24 adapter work.
- No inventory of production data, provider/network/database/VPS/runtime access or secret scan.
- No T0/T1/T2, ledger, model, market-data or trading change.
- No archive, quarantine, cleanup, expiry, compaction, VACUUM, deletion or other mutation.

A decision recorded here cannot authorize implementation, key operations, runtime access, lifecycle actions or an executor. Those remain separate approval gates.

## 3. Decision principles

1. **Fail closed:** missing, stale, contradictory, unauthenticated or unavailable mandatory evidence cannot yield VERIFIED.
2. **Exact binding:** every attestation and decision binds the exact subject, immutable version, evidence digest, purpose and policy revision.
3. **Least authority:** issuer permissions are narrow by domain, claim type, subject scope and validity period.
4. **No self-asserted trust:** claimant booleans, names, paths, counts and `complete=true` are claims, not proof.
5. **Independent authorization:** VERIFIED and REVIEWABLE are not owner approval and never grant execution permission.
6. **No secret exposure:** private keys, tokens and trust-root material never enter ordinary evidence, logs or CI artifacts.
7. **T0 protection:** canonical T0 data and lease/fencing state remain outside any lifecycle mutation scope.
8. **No default by convention:** an implementation/library default is not an owner decision.

## 4. Owner/security decision register

Each decision must be recorded with: selected option and version; rationale; rejected alternatives; owner approval; security assessment; exact scope; effective date; evidence/reference; and conditions for review or revocation. Until then, status is OPEN.

### D01 — Cryptographic integrity and authenticity profile

**Question:** Which exact cryptographic profile authenticates evidence and binds it to its subject and purpose?

Candidate profiles:
- **A. Digest plus detached signature:** SHA-256 content digest; Ed25519 detached signature over a precisely specified statement.
- **B. Standardized attestation envelope:** DSSE-style envelope with an explicitly selected payload type, signature algorithm and canonical payload rules.
- **C. Other approved profile:** requires a documented interoperability, security and maintenance rationale.

Decision criteria:
- Mature, maintained implementations; deterministic verification; explicit domain separation; algorithm identifiers and migration plan.
- Signature covers issuer identity/key ID, subject namespace/object/version, payload digest and length, evidence revision, purpose, policy revision, issuance time and expiry where applicable.
- No algorithm fallback or downgrade; unsupported algorithms fail closed.
- Digest and signature verification are distinct checks.

**Not decided:** hash, signature scheme, attestation format, signed field set, domain separation, algorithm agility or migration policy.

### D02 — Canonical representation and signed bytes

**Question:** Which canonical byte representation is signed and hashed?

Candidate approaches:
- **A. JSON Canonicalization Scheme (JCS):** readable JSON with deterministic canonicalization; parser must reject duplicate keys and invalid/ambiguous representations before canonicalization.
- **B. Deterministic CBOR:** compact typed representation; requires a strict deterministic-encoding profile and compatible tooling.
- **C. Other specified encoding:** only with a normative byte-level specification and cross-implementation test vectors.

Required decision details:
- UTF-8/Unicode normalization behavior; number and timestamp representation; duplicate-key behavior; field ordering; unknown-field and extension policy; null/omission semantics.
- Canonicalization must be versioned and covered by test vectors.
- No parser may silently normalize ambiguous input into a trusted statement.

**Not decided:** encoding, canonicalization standard, schema serialization, extension compatibility or test vectors.

### D03 — Trust roots, issuer identity and delegation

**Question:** Who is trusted to issue claims, and how is authority delegated?

Candidate model:
- Owner-controlled offline trust root; narrowly scoped delegated issuer keys for specific claim categories and data domains.
- Separate issuer roles for producer provenance, inventory closure, policy/sensitivity and owner approvals; no issuer may self-grant authority.
- Alternative model requires equivalent separation, custody and revocation guarantees.

Required controls:
- Stable principal identity and key-to-principal binding.
- Scope-limited delegation, validity intervals and auditable issuance.
- Root/issuer separation; no private trust-root key in application runtime or CI.
- Explicit compromise response, emergency revocation and recovery procedure.

**Not decided:** root count, custody location, hardware/software protection, issuer registry, delegation format, key rotation, compromise response or revocation authority.

### D04 — Key lifecycle and signing operations

**Question:** Where and how are signing keys created, stored, used, rotated and revoked?

Decision must specify:
- Key generation boundary and approved entropy source.
- Custodian and access control; whether hardware-backed custody is required.
- Signing service/process boundary and audit events.
- Rotation cadence or trigger, overlap, retirement and compromise procedure.
- Backup/recovery and destruction rules, without exposing key material.
- Separation of test-only synthetic keys from any future real trust configuration.

**Hard constraint:** no real key generation, import, signing, rotation, revocation or custody change is authorized by G0.24.

### D05 — Envelope schema, versioning and extension rules

**Question:** What exact schema and compatibility model will the verifier accept?

Candidate rules for owner/security consideration:
- Explicit schema identifier and major/minor version.
- Closed set of required fields; unknown critical fields rejected.
- Duplicate keys/logical fields rejected.
- Unknown non-critical extensions either rejected or accepted only under an explicit namespaced extension policy.
- No implicit defaults for security-relevant fields.
- Major-version mismatch rejected; minor compatibility rules must be deterministic and tested.
- Typed timestamps, immutable object/version identifiers and bounded arrays.

**Not decided:** schema, field names/types, extension namespace, compatibility matrix, parser implementation or migration policy.

### D06 — Authoritative evidence stores and immutable version resolution

**Question:** Which system is authoritative for each evidence category, and how is an exact immutable version resolved?

Required evidence classes to map:
- Producer source/build/artifact provenance.
- Payload bytes and digest.
- Inventory snapshots and terminal pagination/cursor proofs.
- Policy revisions and sensitivity lineage.
- Owner/steward approvals.
- Downstream consumers, holds, dependencies, copies, replicas and backups.

For each source, record:
- Authority/owner and API/read boundary.
- Immutable identity/version semantics.
- Consistency guarantees and snapshot behavior.
- Completeness/terminal-cursor proof.
- Availability failure behavior and evidence export/readback.
- Retention/custody responsibility.

**Not decided:** any concrete GitHub artifact, object store, database, provider, registry or production source is designated authoritative.

### D07 — Inventory registries and closure proofs

**Question:** Which registries prove that all applicable holds, dependencies, consumers, copies, backups, replicas and lineage edges have been enumerated?

Required controls:
- Explicit inventory namespace and exact query scope.
- Snapshot ID/generation and consistency boundary.
- Partition/cursor enumeration with terminal closure proof.
- Reconciliation of counts and cross-registry references.
- Detection of unknown consumers and unresolved lineage.
- Fail closed when any mandatory source is unavailable or incomplete.

**Not decided:** registry owners, authoritative source list, closure protocol, cross-source reconciliation or completeness thresholds.

### D08 — Freshness, clock, expiry and revocation policy

**Question:** How fresh must each evidence category be, and what happens when time or revocation status cannot be established?

Freshness must be class-specific rather than one global TTL. At minimum, decide separately for:
- Issuer authority and trust metadata.
- Evidence attestations and payload versions.
- Inventory/consumer/hold snapshots.
- Policy and sensitivity decisions.
- Owner approvals.
- Revocation status.

Also decide:
- Maximum clock skew and trusted time source.
- Issuance/expiry semantics and maximum validity.
- Revocation source, update frequency and effective-time handling.
- Network outage behavior; whether offline verification is prohibited or permitted under a narrowly defined signed snapshot.
- Cache lifetime and invalidation rules.

**Required fail-closed baseline:** unknown revocation status, expired authority, stale inventory or unavailable mandatory trust source cannot be treated as current/valid.

**Not decided:** any numeric duration, skew, expiry, cache lifetime or offline grace period.

### D09 — Owner/steward authentication and exact-scope approval

**Question:** What proves that an owner decision is authentic and applies to the exact object and action?

Approval statement must bind:
- Authenticated owner/steward principal and delegated authority.
- Exact object ID and immutable version.
- Exact action and data class.
- Scope, conditions, expiry and any required review.
- Applicable policy revision and supporting evidence references.
- Decision outcome and unique decision ID.

Decision must also define separation of duties, re-approval after object/version change, revocation and audit custody. A GitHub comment, display name or repository permission alone must not silently become an authorization credential.

**Not decided:** owner identity mechanism, approval signature profile, custody, delegation or approval interface.

### D10 — Supported data-class vocabulary and mapping

**Question:** Which lifecycle object classes are supported, and how are they mapped to sensitivity and obligation rules?

Requirements:
- Explicit versioned allowlist; unknown classes remain unsupported and fail closed.
- No inferred aliases or broad wildcard mappings.
- Preserve G0.17 sensitivity ordering and most-restrictive inheritance.
- Credentials, tokens, keys and trust-root secrets remain RESTRICTED.
- T0 canonical candles, lease/fencing, ledgers, audit/reconstruction/recovery and owner custody/trust evidence remain protected unless a separate exact-scope approval changes that status.
- Derived outputs inherit the most restrictive applicable source classification.

**Not decided:** final class vocabulary, aliases, mapping table or class-specific lifecycle predicates.

### D11 — Resource limits and denial-of-service controls

**Question:** What hard bounds apply before and during parsing and evidence verification?

Parameters requiring explicit values:
- Maximum envelope bytes and evidence-item bytes.
- Maximum evidence count, lineage depth, parent count and array length.
- Maximum pagination pages/items and total inventory size per evaluation.
- Parser depth/string limits and duplicate-key detection.
- Per-source timeout, total verification deadline and bounded retry count.
- Memory/CPU budget and concurrency.
- Maximum diagnostic output and safe reason-code size.

No unbounded retries, recursive traversal, unbounded buffering or caller-controlled resource expansion. Numeric values must be based on measured expected evidence size and tested upper bounds.

**Not decided:** numeric limits, timeouts, retry counts, concurrency or performance budget.

### D12 — Audit custody, retention and redaction

**Question:** Where is the verification and owner-decision audit trail kept, and how is tampering detected?

Audit requirements:
- Correlation ID and exact subject/version.
- Verifier build/version and policy/trust-profile revision.
- Evidence references and digests, not secret payloads.
- Issuer/authority and verification outcomes.
- Owner decision ID, scope, expiry and revocation state.
- Stable reason codes and timestamps with trusted-time provenance.
- Tamper-evident ordering/checkpointing and independent readback.
- Retention and access policy consistent with sensitivity classification.

Do not log private keys, tokens, RESTRICTED payloads or unrestricted evidence excerpts. Audit retention is not an authorization to delete old audit records.

**Not decided:** audit store, tamper-evidence mechanism, retention period, custodians or independent readback procedure.

### D13 — Verified-facts binding and process boundary

**Question:** How is a verified-facts result prevented from being forged, altered, replayed or reused for another evaluation?

Options to assess:
- Process-local immutable typed value created only by verifier-owned constructors.
- Opaque verification handle backed by a verifier-owned registry.
- Signed/attested result with strict process and evaluation binding.

Required properties:
- Bind exact object/version, purpose, evaluation ID, verifier build, policy/trust revision and evidence snapshot.
- Reject caller construction and mutation.
- Define single-use versus bounded reuse and replay protection.
- Revalidate freshness/revocation where required.
- Never treat serialization/deserialization by an untrusted caller as proof of verification.

**Not decided:** type/API boundary, process boundary, replay semantics or verifier-to-evaluator interface.

### D14 — Review, implementation and release gates

**Question:** What evidence is required before moving from decisions to implementation and later operational use?

Proposed separate gates:
1. Owner/security ratification of D01–D14, with unresolved items explicitly BLOCKED.
2. Contract/schema and verifier-interface design review.
3. Synthetic executable tests based on G0.23, including real cryptographic verification with test-only synthetic keys once the profile is approved.
4. Bounded verifier implementation and focused CI with read-only permissions.
5. Independent security/code review of the implemented trust boundary.
6. G0.24 pure evaluator adapter assessment only after the verified-facts type exists.
7. Separate approval for any real evidence-source adapter or runtime integration.
8. Separate exact-scope approval for owner authorization workflow and any future executor.

No gate automatically authorizes the next one.

**Not decided:** reviewers, required evidence thresholds, workflow, implementation owner or release criteria.

## 5. Decision record template

For every D01–D14, complete:

| Field | Required value |
|---|---|
| Decision ID | D01–D14 |
| Status | OPEN / APPROVED / REJECTED / DEFERRED |
| Selected option | Exact profile and version; no ambiguous prose |
| Rationale | Security, ownership, interoperability and operational reasons |
| Rejected alternatives | Options considered and why rejected |
| Owner approval | Authenticated approver and exact scope |
| Security assessment | Risks, residual risks and required controls |
| Evidence | Immutable reference, revision and digest |
| Effective date | Explicit timestamp and timezone |
| Review/revocation | Trigger and authorized party |
| Downstream gates | What this decision unblocks; what remains blocked |

An approval must be explicit and exact. Silence, “continue”, CI success or a draft recommendation does not ratify cryptographic/trust decisions.

## 6. Dependency order

The decisions are related; do not implement around unresolved dependencies.

1. D01–D04 establish authenticity, trust roots and key lifecycle.
2. D02 and D05 establish canonical bytes and schema/version semantics; they must agree with D01's signed statement.
3. D06–D07 establish evidence authorities and inventory closure.
4. D08 establishes freshness/revocation semantics across D03, D06 and D07.
5. D09 establishes owner decision authentication and authorization evidence.
6. D10 maps supported classes and G0.17 policy semantics.
7. D11 bounds all parser, evidence and inventory work.
8. D12 defines audit custody and safe evidence.
9. D13 binds verifier output to one evaluation and prevents caller bypass/replay.
10. D14 defines independent review and staged implementation gates.

A dependent decision cannot be marked APPROVED while its required upstream profile remains unresolved.

## 7. Current status matrix

| Decision | Status | Blocks |
|---|---|---|
| D01 Cryptographic profile | OPEN | Signature/digest implementation |
| D02 Canonical representation | OPEN | Signed bytes and parser |
| D03 Trust roots/delegation | OPEN | Issuer authentication |
| D04 Key lifecycle | OPEN | Any real signing operation |
| D05 Envelope schema | OPEN | Parser and physical contract |
| D06 Evidence authorities | OPEN | Evidence resolution |
| D07 Inventory closure | OPEN | Completeness verification |
| D08 Freshness/revocation | OPEN | Time and revocation checks |
| D09 Owner authentication | OPEN | Owner approval verification |
| D10 Data-class vocabulary | OPEN | Supported-class mapping |
| D11 Resource limits | OPEN | Bounded verifier |
| D12 Audit custody | OPEN | Audit implementation |
| D13 Verified-facts binding | OPEN | Verifier/evaluator interface |
| D14 Review/release gates | OPEN | Implementation and release |

**No decision is ratified by G0.24.**

## 8. Next step and explicit limits

Next step is owner/security review of this decision register. Decisions may be ratified individually with exact scope; unresolved decisions remain OPEN and block dependent implementation. If the owner wants a recommendation for a specific decision, that decision can be assessed separately without silently ratifying it.

Until the required decisions are explicitly ratified:
- Do not create real keys or trust roots.
- Do not implement a verifier, parser, schema, evidence registry, adapter or executor.
- Do not create real evidence-source integrations or change CI permissions.
- Do not execute G0.23 cases as though a physical trust profile exists.
- Do not access VPS/runtime/provider/database or T0 canonical data.
- Do not perform archive, quarantine, cleanup, expiry, compaction, VACUUM or deletion.

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.

## 9. Final verdict

**G0.24: DECISION PACKAGE DRAFTED — D01–D14 are structured for owner/security ratification; all remain OPEN. No trust profile, implementation or operational authority is established.**

G0.24 is a decision worksheet, not a security certification, cryptographic design approval, verifier implementation approval or lifecycle action authorization.
