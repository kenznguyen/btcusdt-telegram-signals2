# Stage H.0–H.5 — Owner Decision Resolution
Date: 2026-11-10
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Scope: documentary-only resolution of G-DEC-01 through G-DEC-06 under the owner's approval to execute Stage H automatically.

## H.0 — Authority and decision method

The owner authorized automatic execution of Stage H. This package records the architecture-level dispositions below as owner-approved directions for the next documentary design step. It does not authorize implementation, technical tests, runtime access, provider selection/provisioning, permission changes, data lifecycle actions or lifecycle execution.

Source baseline:
- Stage G report: `docs/evidence/p1-8/STAGE_G0_G5_OWNER_DECISION_PACKAGE_2026-11-10.md`, blob `a8a9b46eeed5b35612bef800887f863ad654ed84`.
- Project handoff at Stage H start: `docs/PROJECT_SESSION_HANDOFF.md`, blob `daf82b11657ccb38d2e60d2f9af3a32c50392bfc`.

Decision principle: approve stable architectural direction where the proposal is sufficiently bounded; preserve unresolved implementation parameters and external-provider choices as OPEN rather than inventing them. No approval in this stage expands Option C or TEST-08 authority.

## H.1 — G-DEC-01: Canonicalization, digest and schema evolution

**Disposition: APPROVED — RFC 8785 JCS + SHA-256 direction.**

Approved direction:
- Use RFC 8785 JSON Canonicalization Scheme as the canonical JSON representation for future manifests, logical records and evidence envelopes.
- Use SHA-256 for canonical-record digests.
- Preserve source-byte digests separately where byte-level provenance is required; canonical digests do not replace them.
- Use domain-separated identifiers and explicit schema/profile metadata.
- Reject duplicate keys, invalid UTF-8, non-finite numbers, unsupported numeric representations, digest mismatch and unknown major schema versions; fail closed.
- Prefer integer-unit representations for quantities where feasible; do not rely on binary floating-point for financial quantities.
- Schema major versions are immutable; additive optional fields require a documented compatibility rule.

Still OPEN before a technical contract can be frozen: exact JCS library/version and conformance profile; parser behavior; integer bounds; decimal/quantity encoding; Unicode handling; domain-label registry; digest envelope; compatibility matrix; and positive/negative golden vectors. These details must be specified and tested later; no implementation or tests are authorized here.

## H.2 — G-DEC-02: Synthetic resource boundary and isolation

**Disposition: APPROVED — layered per-run isolation as the required target architecture.**

Approved direction:
- Every run has unique run and namespace identities.
- All fixtures, resources, operations, observations and artifacts bind to the exact run/namespace.
- Synthetic-only storage and credentials; no production credentials or protected-resource reachability.
- Default-deny network egress, explicit filesystem/mount allowlists, and isolated storage/database scope.
- Resource inventory classes: synthetic, protected, unknown and unclassified. Only positively proven synthetic resources in the exact run namespace may be eligible for a future synthetic lifecycle manifest.
- Protected, unknown and unclassified resources are excluded by default; cross-run or unknown references fail closed.
- Effective isolation must be independently observed; configuration declarations alone do not prove isolation.

Implementation topology, concrete namespace technology, resource types, filesystem/network policy details, credential issuance and negative proof fixtures remain OPEN. No provisioning, isolation test, dry-run or destructive executor is authorized. Option C remains ACTIVE.

## H.3 — G-DEC-03: Principal and capability separation

**Disposition: APPROVED — distinct least-privilege principals.**

Approved direction:
- Owner/controller remains outside the test execution path.
- Executor, adapter, observer/oracle, evidence publisher and independent verifier have distinct identities and credentials where the platform supports it.
- Observer is read-only; oracle evaluates independently frozen expected state against observer output.
- Executor cannot author authoritative observer/oracle/verifier records or access protected resources.
- Publisher cannot alter already published evidence versions.
- Verifier independently retrieves exact versions and validates bytes, digests, schema, causal references and completeness.
- Each identity is bound to immutable subject/issuer, run/namespace, process/build identity, effective resource scope, operation allowlist and observed capability snapshot.
- If effective separation cannot be proven, the relevant gate remains NOT VERIFIED; role labels are insufficient.

Concrete identity provider, credential mechanism, token lifetime, policy syntax and effective permission evidence remain OPEN. No permissions are requested or changed; LDA-08 remains HOLD / NOT VERIFIED.

## H.4 — G-DEC-04 and G-DEC-05: Evidence destination and verifier

**G-DEC-04 disposition: APPROVED — provider-neutral hybrid architecture direction.**

GitHub remains the source of project decisions, source and evidence index/manifests. A separate versioned evidence-payload destination is the target architecture, subject to future owner selection and proof of exact-version retrieval, append-only/versioning behavior, ownership, trust boundary, retention/hold and recovery. No storage provider, account, bucket, region or service is selected.

**G-DEC-05 disposition: APPROVED — independent exact-version verifier.**

The verifier must independently retrieve exact evidence versions; recompute source-byte and canonical digests as applicable; validate schema/profile; close all references; bind source SHA, run, namespace, principal and causal event chain; and reconcile completeness against the frozen manifest. Missing, mutable, dangling, inaccessible, cross-run or non-causal evidence is INDETERMINATE/BLOCKED, never PASS. Upload success alone is not verification.

Still OPEN: destination provider and owner; object/version semantics; access policy; append-only enforcement; retention lock/hold; inventory pagination; recovery/backup design; verifier implementation, build identity and trust roots. No provider probe, account setup, artifact publication or retention mutation is authorized.

## H.5 — G-DEC-06: Retention, hold and recovery; consolidated disposition

**Disposition: PARTIALLY RESOLVED — governance requirements approved; all operational values and mechanisms remain OPEN.**

Approved direction:
- No evidence retention duration, legal-hold period, backup schedule, recovery point/objective or recovery mechanism is inferred or selected in this stage.
- A future destination proposal must state owner, data classification, retention authority, hold/release authority, versioning/immutability semantics, inventory completeness, recovery scope and evidence of restore/readability.
- Retention and recovery must preserve auditability and must not silently convert missing/unavailable evidence into evidence of absence.
- Any deletion, expiry, archive, compaction, vacuum, overwrite or other destructive lifecycle operation remains separately controlled and unauthorized under Option C.
- If retention/hold/recovery policy or effective enforcement cannot be proven, destination approval and evidence-readiness remain BLOCKED.

### Consolidated decision register

| Decision | Disposition | Remaining OPEN items |
|---|---|---|
| G-DEC-01 Canonicalization | APPROVED direction | Exact conformance profile and golden vectors |
| G-DEC-02 Synthetic isolation | APPROVED target architecture | Concrete topology, policy and isolation proof |
| G-DEC-03 Principals/capabilities | APPROVED target model | Identity provider, credentials and effective permission proof |
| G-DEC-04 Evidence destination | APPROVED hybrid direction; no provider | Provider, owner, exact-version and append-only proof |
| G-DEC-05 Verifier | APPROVED functional contract | Implementation, trust roots and independent verification proof |
| G-DEC-06 Retention/recovery | PARTIALLY RESOLVED | Duration, hold, backup, recovery and enforcement mechanisms |

### Next dependency sequence

1. Prepare a versioned documentary technical contract translating H.1–H.5 into exact schemas, profiles, resource and principal contracts, evidence manifest/verifier interface and retention decision fields. Keep unresolved parameters explicitly OPEN.
2. Reconcile that contract against C.13, C.14, C.15 and the Stage D–G records; do not alter the 87-vector denominator or claim executable coverage.
3. Determine a separately authorized read-only evidence route for LDA-06 and LDA-08; do not broaden permissions or probe external systems under this stage.
4. Prepare a new bounded implementation proposal only after documentary contract review. Any implementation requires separate explicit authorization.
5. TEST-08 remains a separate exact-scope gate and cannot be inferred from Stage H approval. No lifecycle execution before TEST-08 is explicitly granted and all prerequisites are evidenced.

### Status and prohibitions

- Stage H.0–H.5: DOCUMENTARY DECISION RESOLUTION COMPLETE.
- Architecture directions G-DEC-01/02/03/04/05: APPROVED at direction/contract level only.
- G-DEC-06: PARTIALLY RESOLVED; operational policy OPEN.
- Technical readiness: BLOCKED; implementation: NOT AUTHORIZED; execution: NOT AUTHORIZED.
- TEST-01/02/04/05/06/07: NOT ESTABLISHED; TEST-03: NOT VERIFIED; TEST-08: NOT GRANTED.
- LDA-07: 87/87 NOT RUN; LDA-06: PARTIAL / NOT VERIFIED; LDA-08: HOLD / NOT VERIFIED.
- Option C — No Destructive Authority: ACTIVE.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- No source/code/schema/adapter/runner/workflow/permission/runtime/data changes.
- No tests, compilation, dry-run, fault injection or Actions dispatch.
- No secrets, VPS, T0/T1, database, provider, recipient, backup or replica probes.
- No provisioning, publication to external evidence storage, cleanup, deletion, archive, expiry, compaction or vacuum.
- No workflow run or artifact is claimed.

**Stage H.0–H.5 COMPLETE within documentary scope. No technical gate is upgraded by this decision record.**
