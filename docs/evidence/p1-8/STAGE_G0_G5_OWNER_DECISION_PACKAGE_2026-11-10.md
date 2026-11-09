# Stage G.0–G.5 — Owner Decision Package
Date: 2026-11-10
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Scope: documentary-only architecture options and owner decision preparation.

## G.0 — Purpose, authority and source baseline

Stage G translates the unresolved prerequisites in Stage F into explicit, reviewable decision options. It does not select a provider, freeze a technical contract, implement code, establish technical readiness, or authorize execution.

Canonical inputs retrieved from this branch:
- Stage F report: `docs/evidence/p1-8/STAGE_F0_F5_PREREQUISITE_CLOSURE_REVIEW_2026-11-10.md` (blob `69cbf95be3aba10a2685ca75f40a36f0c38a6822`).
- Stage E proposal: `docs/evidence/p1-8/STAGE_E0_E5_BOUNDED_IMPLEMENTATION_PROPOSAL_2026-11-10.md` (blob `b0dab61ac0164af8a5e4f6df499a124ee8e7e113`).
- Project handoff at start: `docs/PROJECT_SESSION_HANDOFF.md` (blob `9f85b7947bea0d47ee5d4b51c7fa5b60a2b0f6c6`).

The current technical statuses are carried forward without upgrade: TEST-01/02/04/05/06/07 NOT ESTABLISHED; TEST-03 NOT VERIFIED; TEST-08 NOT GRANTED; LDA-07 87/87 NOT RUN; LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED.

## G.1 — Canonical serialization, digest and schema evolution

### Options

| Option | Description | Advantages | Risks / limits |
|---|---|---|---|
| A — RFC 8785 JCS + SHA-256 | UTF-8 JSON canonicalized using JSON Canonicalization Scheme; SHA-256 over canonical bytes; explicit schema version and domain-separated identifiers | Standardized cross-language representation; deterministic object ordering/number serialization; broad implementation availability | JCS input constraints must be enforced; numeric precision and Unicode edge cases require fixtures; schema evolution remains explicit |
| B — Canonical CBOR + SHA-256 | Deterministic CBOR profile and SHA-256 digests | Compact binary representation; deterministic encoding possible | More implementation/profile complexity; interoperability and debugging costs; profile must be precisely pinned |
| C — Bespoke canonical JSON | Project-defined key ordering, number and string rules | Tailored and superficially simple | High risk of divergent implementations and underspecified edge cases; not recommended |

### Recommended proposal (not owner-approved)

Prefer Option A for manifests, logical records and evidence envelopes, subject to a conformance profile. Do not hash ordinary JSON serialization. Reject duplicate object keys, non-finite numbers, unsupported numeric representations and invalid UTF-8; define treatment of Unicode without silently normalizing values. Restrict numeric fields to explicitly typed integer units where possible; do not encode financial quantities as binary floating point.

Proposed digest construction:
- `record_digest = SHA-256(JCS(record_without_digest_field))`.
- Identifiers use domain separation, e.g. `SHA-256(UTF8("H5LIFECYCLE:<type>:v1") || 0x00 || canonical_bytes)`.
- Digest algorithm and canonicalization profile are explicit metadata, never inferred.
- Schema evolution uses immutable major versions; additive optional fields may be introduced only under a documented compatibility rule. Unknown major versions, unknown critical fields, invalid canonicalization and digest mismatch fail closed.
- Preserve original source bytes where provenance requires byte-level identity; canonical digest does not replace source-byte digest.

Before freezing: specify exact JCS implementation/version, JSON data model, integer bounds, decimal/quantity encoding, Unicode policy, duplicate-key parser behavior, domain labels, digest envelope, compatibility matrix and positive/negative golden vectors. Do not invent values for unresolved clock/provider/trust parameters.

## G.2 — Synthetic resource model and namespace isolation

### Options

| Option | Description | Advantages | Risks / limits |
|---|---|---|---|
| A — Per-run isolated filesystem namespace | Unique run root, synthetic-only fixture store, process/container boundary and explicit path allowlist | Easy to inspect and inventory; clear ownership and cleanup-candidate boundary | Filesystem isolation alone does not prove network, credential or host isolation |
| B — Per-run isolated database/schema | Dedicated ephemeral database or schema per run, synthetic-only credentials and explicit object allowlist | Strong database-level separation and transaction semantics | Requires provisioning and effective privilege proof; may not isolate filesystem, backups or external services |
| C — Layered isolation | Per-run namespace plus isolated storage/database, distinct principal, restricted filesystem and default-deny network | Defense in depth; no single namespace label is treated as proof | More components to verify; must avoid claiming isolation from configuration alone |

### Recommended proposal (not authorized for implementation)

Prefer Option C as the target contract. Each run receives a cryptographically unique run ID and namespace ID, with every resource, fixture, operation, observation and artifact bound to both. Use synthetic-only storage and credentials that cannot address production resources. Network egress is deny-by-default; only explicitly enumerated local test dependencies may be reachable. Filesystem mounts are allowlisted and read-only outside the synthetic writable root. Unknown paths, resource types, namespace IDs and cross-run references fail closed.

Resource inventory must classify every object as synthetic, protected, unknown or unclassified. Only positively proven synthetic objects within the exact run namespace can enter a future candidate manifest. Protected and unknown objects are never candidates. The executor receives no deletion/archive/expiry/compaction/vacuum capability under Option C. A dry-run is also prohibited until separately authorized.

Isolation evidence must be observed independently: effective mount/path view, process identity, effective credentials/capabilities, network policy, storage/database identity, namespace membership and negative reachability/mutation tests. Configuration text or workflow YAML alone is insufficient.

## G.3 — Principal and capability model

### Proposed principals

| Principal | Permitted responsibilities | Explicitly forbidden |
|---|---|---|
| Owner/controller | Approve scope and authorization; inspect evidence | Execute test mutations or author its own independent verification |
| Executor | Run only the frozen synthetic manifest through bounded adapters | Author oracle observations/verdicts; access protected resources or production credentials |
| Adapter service | Enforce synthetic resource API and operation allowlist | Broaden target scope, access production or bypass namespace checks |
| Observer | Read-only capture of actual synthetic state and events | Mutate resources or accept executor-authored observations |
| Oracle/evaluator | Compare frozen expected state with observer output | Mutate target state; trust executor-supplied expected outcomes |
| Evidence publisher | Publish exact run-bound evidence to approved destination | Alter evidence after publication or issue verification verdict |
| Independent verifier | Read exact immutable versions, recompute digests and validate causal references | Publish/modify source evidence or rely on executor's self-attestation |

### Identity and capability requirements

Every principal must be bound to issuer, immutable subject, process/job/build identity, run and namespace, effective resource scope, operation allowlist, credential provenance and a capability snapshot. Authorization is deny-by-default and short-lived where supported. Role names are not proof of effective separation. Executor must be unable to impersonate observer, oracle, publisher or verifier; publisher must not alter already published versions; verifier must independently retrieve exact versions.

Recommended model: distinct principals and credentials for executor, observer/oracle, publisher and verifier, with owner/controller outside the run. If the platform cannot enforce a distinct principal, mark the relevant gate NOT VERIFIED rather than simulating separation through labels.

No permissions are requested or changed in Stage G. LDA-08 remains HOLD / NOT VERIFIED because the existing branch-protection metadata route returned HTTP 403.

## G.4 — Evidence destination and independent verifier

### Destination options

| Option | Description | Advantages | Risks / limits |
|---|---|---|---|
| A — Git repository objects | Versioned documents and evidence manifests committed to the existing repository branch | Existing ownership and traceability; low operational complexity | Repository history is not automatically immutable retention or independent evidence storage; branch protection remains unverified |
| B — GitHub Actions artifacts | Run-associated downloadable artifacts | Convenient association with workflow run | Retention is bounded/configurable; artifacts alone do not prove append-only behavior, independent access or long-term hold |
| C — Dedicated object storage with versioning/retention | Separately owned destination with immutable object versions and explicit retention controls | Better separation and exact-version retrieval potential | Provider, account ownership, policy, retention lock, recovery and effective permissions require owner decision and verification |
| D — Hybrid | Git stores manifests/index; separate destination stores immutable evidence payloads; independent verifier reads both | Clear source traceability plus evidence payload separation | More interfaces and reconciliation obligations; cannot assume either side is immutable |

### Recommended proposal (provider not selected)

Prefer Option D as a logical architecture, but do not select or provision a provider in this stage. GitHub remains the source of project decisions and code. A future evidence destination must have a stable destination identity, owner, trust zone, exact object-version semantics, append-only/versioning proof, retention/hold authority, inventory and recovery contract, and independently readable access policy.

The evidence manifest should bind:
- source commit and relevant blob SHAs;
- schema/profile and vector catalogue versions;
- run/namespace IDs and frozen manifest digest;
- principal/process/build/toolchain identities;
- operation, attempt, resource version and causal event references;
- observer output, oracle verdict and artifact digest;
- destination identity, object key and exact immutable version;
- verifier identity, policy/build identity and verification result.

Verifier checks must include byte retrieval, digest recomputation, schema/profile validation, reference closure, namespace/run consistency, causal ordering, exact source binding, principal separation and completeness against the frozen manifest. Missing, mutable, dangling, cross-run, non-causal or inaccessible evidence yields INDETERMINATE/BLOCKED, never PASS. A successful upload alone is not a verification result.

Retention duration, legal hold, backup/recovery and provider choice remain owner decisions. No provider probe, account setup, artifact publication, permission change or retention mutation is authorized.

## G.5 — Consolidated owner decision register and next gates

| Decision ID | Subject | Proposed direction | Owner disposition |
|---|---|---|---|
| G-DEC-01 | Canonicalization | RFC 8785 JCS + SHA-256 with strict conformance profile | PENDING |
| G-DEC-02 | Synthetic boundary | Layered per-run isolation (namespace + storage + principal + filesystem + default-deny network) | PENDING |
| G-DEC-03 | Principal/capability | Distinct executor, adapter, observer/oracle, publisher and verifier principals | PENDING |
| G-DEC-04 | Evidence destination | Hybrid Git index + separately versioned evidence payload destination; no provider selected | PENDING |
| G-DEC-05 | Verifier | Independent exact-version byte/digest/provenance and causal-closure verifier | PENDING |
| G-DEC-06 | Retention/recovery | Explicit owner-approved retention, hold, inventory and recovery contract before destination selection | PENDING |

### Dependency sequence after owner review

1. Owner accepts, revises or rejects G-DEC-01 through G-DEC-06.
2. If accepted, create a versioned technical contract with exact serialization fixtures, namespace/resource schema, principal/capability matrix and evidence destination contract.
3. Obtain authorized read-only evidence routes for LDA-06 and LDA-08 without broadening permissions.
4. Perform documentary/static consistency review of the versioned contract.
5. Only then prepare a new bounded implementation proposal with exact files, APIs, threat boundaries and acceptance evidence.
6. Any implementation requires separate explicit approval. Any lifecycle execution additionally requires TEST-08 exact-scope approval after implementation and isolation evidence exist.

### Explicit boundaries and status

- Stage G approval authorizes only G.0–G.5 documentary decision preparation.
- No code, schema, adapter, runner, workflow, permission, runtime or data changes.
- No tests, compilation, dry-run, fault injection or Actions dispatch.
- No secrets, VPS, T0/T1, database, provider, recipient, backup or replica probes.
- No provisioning, cleanup, deletion, archive, expiry, compaction or vacuum.
- Option C — No Destructive Authority: ACTIVE.
- TEST-08: NOT GRANTED.
- TEST-01/02/04/05/06/07: implementation NOT ESTABLISHED; TEST-03 NOT VERIFIED.
- LDA-07: 87/87 NOT RUN; LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Independent Review waiver remains in force; no independent assurance claim is made.

**Stage G.0–G.5: DOCUMENTARY OWNER DECISION PACKAGE COMPLETE. Technical readiness remains BLOCKED. Implementation and execution are NOT AUTHORIZED.**
