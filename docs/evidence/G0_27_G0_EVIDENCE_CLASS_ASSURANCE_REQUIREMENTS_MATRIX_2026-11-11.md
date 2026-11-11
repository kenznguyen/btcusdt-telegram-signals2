# G0.27 — G0 Evidence-Class Assurance Requirements Matrix

Date: 2026-11-11 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Baseline HEAD: `db95116a5b0625835eda78abcbb5050bd5f79aa6`
Baseline handoff blob: `1a24d108864dffee61e079dd47b0eae9eb93a77f`
Type: documentation-only classification
Disposition: **CLASSIFICATION PASS — CLAIM-SPECIFIC ASSURANCE NEEDS MAPPED; CRYPTO/TRUST PROFILE NOT RATIFIED; IMPLEMENTATION NOT AUTHORIZED**

## 1. Purpose and scope

G0.27 classifies the assurance properties needed by distinct G0 evidence classes. It operationalizes the minimality principles in G0.26 without selecting or ratifying a cryptographic profile.

The matrix distinguishes:

- **I — Byte integrity:** recompute a digest over the exact bytes and bind the result to an immutable subject/version.
- **S — Signer/issuer authenticity:** authenticate the issuer and verify that its authority covers the exact statement, subject, purpose and audience.
- **O — Owner authorization:** separately authenticate an owner decision for an exact action, target, scope and policy version.
- **F — Freshness / anti-replay:** establish whether evidence or policy is current where the claim depends on latestness, expiry, revocation or sequence.
- **C — Completeness / provenance:** prove source lineage, inventory scope, closure and the relevant producer/build/input/output relationships.
- **R — Custody / readback:** independently establish possession, retrieval and byte-for-byte readback where custody or recoverability is claimed.

Legend:
- **REQ** = required to make the stated claim.
- **COND** = required only if the evidence is used to make the stated claim or the listed condition applies.
- **N/R** = not required for this evidence class in its ordinary, bounded claim.
- **OPEN** = the exact mechanism, authority or acceptance rule remains undecided.
- **OUT-OF-SCOPE** = must be handled by a separate gate; this row does not grant it.

These labels classify claims, not files in the abstract. The same artifact may support several claims and therefore require several independent checks.

## 2. Evidence-class matrix

| ID / evidence class | I | S | O | F | C | R | Required interpretation / boundary |
|---|---|---|---|---|---|---|---|
| E01 — G1 A T0 checkpoint proof-of-existence payload | REQ | N/R | OUT-OF-SCOPE | COND | COND | COND | Preserve the existing unsigned digest/proof-of-existence contract. Add freshness only if claiming accepted-latest status; completeness only to the extent defined by that checkpoint contract. No signer-authenticity claim is implied. |
| E02 — Git-tracked source, policy and evidence documents | REQ | COND | OUT-OF-SCOPE | COND | COND | COND | Bind exact path, ref/commit and Git blob identity; recompute any separately claimed SHA-256. Git commit authorship or a repository identity is not automatically an authenticated owner signature. Current-ref claims require a trusted ref observation. |
| E03 — GitHub Actions workflow/run metadata and logs | REQ | COND | OUT-OF-SCOPE | COND | REQ | COND | Bind workflow identity, event, branch, exact checkout SHA, job result and run ID. Platform metadata can support a platform-origin claim only within its verified source/authority; it does not prove source truth, owner acceptance or custody outside GitHub. |
| E04 — CI output artifacts and manifests | REQ | COND | OUT-OF-SCOPE | COND | REQ | COND | Recompute downloaded payload/member digests; bind artifact ID, originating run, source SHA, manifest version and expiry. Issuer authenticity is needed if claiming a trusted producer attested to the output. Artifact metadata alone is not independent payload readback. |
| E05 — Synthetic fixtures and expected outcomes (G0.10/G0.23) | COND | N/R | N/R | N/R | REQ | N/R | Use deterministic, explicitly synthetic inputs and expected outcomes; bind fixture version and test case. Production keys, real identities and production evidence are excluded. Synthetic test success does not establish real-source authenticity. |
| E06 — Real source-adapter assertions / verified facts | REQ | REQ | OUT-OF-SCOPE | COND | REQ | COND | Authenticate each issuer's scoped authority; bind exact immutable source object/version and recomputed evidence digest; verify source lineage and inventory closure. Freshness/revocation is required where source state can change or stale facts affect disposition. |
| E07 — Inventory, completeness and closure statements | REQ | COND | OUT-OF-SCOPE | COND | REQ | COND | Define authoritative inventory boundary, query/ref/time/scope, pagination and exclusions; prove closure and bind the resulting manifest. Issuer authenticity is required when relying on a source owner's completeness assertion. |
| E08 — Sensitivity classification and inherited-label evidence (G0.17) | REQ | REQ | COND | COND | REQ | COND | Authenticate the policy authority and classification issuer; bind object/copy/lineage and policy version; apply most-restrictive-wins inheritance. Unknown, stale, conflicting or unauthenticated classification remains RESTRICTED pending resolution. Declassification requires separate exact-scope owner authorization. |
| E09 — Policy/profile/trust configuration | REQ | REQ | COND | REQ | COND | COND | Verify exact policy bytes/version and the authority that approved them; current-policy claims require freshness and rollback/revocation checks. A policy digest alone does not prove approval. No D01–D14 profile is ratified by this matrix. |
| E10 — Owner decisions and action approvals | REQ | COND | REQ | COND | REQ | COND | Approval must identify owner authority, exact action, target/object/version, scope, preconditions, expiry and policy version. A generic signed document or CI PASS is not authorization. Authentication method remains OPEN under D09. |
| E11 — Custody receipts, independent retrieval and readback | REQ | COND | OUT-OF-SCOPE | COND | REQ | REQ | Verify retrieved bytes against the bound digest and record the independent retrieval path, custodian and scope. A receipt or artifact listing without independent readback does not prove possession or recoverability. |
| E12 — Evaluator/test execution results (G0.20 and later) | REQ | COND | N/R | COND | REQ | COND | Bind exact source/test blobs, checkout SHA, workflow/run/job, command and result counts. Platform-origin authenticity is conditional on the claim; CI success does not authorize owner decisions or lifecycle actions. |
| E13 — Lifecycle disposition output from the pure evaluator | REQ | COND | OUT-OF-SCOPE | COND | REQ | COND | Bind exact input envelope, evaluator version and deterministic output. Authenticate issuer only if an external consumer relies on the evaluator's identity; the output is classification, not owner authorization or execution permission. |
| E14 — Exact-object owner authorization for a proposed lifecycle action | REQ | COND | REQ | REQ | REQ | COND | Separate gate after verified facts and evaluator result. Authorization must be current, non-replayed and bound to exact object/action. This row defines assurance needs only; no action or executor is approved. |

## 3. Cross-cutting conclusions

1. **Digest is the baseline for byte-integrity claims, not identity.** Recompute against exact bytes; do not treat a digest string, filename, artifact listing or caller-supplied boolean as proof.
2. **Signer authenticity is claim-specific.** It is required where a downstream decision relies on an issuer's authority or attestation. It is not required merely because a file exists or because synthetic tests are being run.
3. **Owner authorization is always a separate decision.** An issuer signature, CI result, evaluator disposition or custody receipt cannot grant deletion, cleanup, archive, policy-change or execution authority.
4. **Freshness is conditional but explicit.** It is needed for current-policy, latest-checkpoint, non-revoked-key, current-inventory and anti-replay claims. A local timestamp or signature timestamp alone is not a trusted freshness anchor.
5. **Completeness cannot be inferred from a valid signature.** Inventory boundary, source query, pagination, exclusions, lineage and closure need their own evidence.
6. **Custody requires readback.** An artifact ID, upload digest or provider receipt is not equivalent to independently retrieving and hashing the bytes.
7. **One evidence object may need multiple independent verdict dimensions.** Record integrity, authenticity, authorization, freshness, completeness and custody separately; never collapse them into a single PASS.
8. **Unknown, stale, conflicting or unauthenticated facts remain fail-closed.** This is consistent with the G0.17 sensitivity policy and G0.21 trust-boundary findings.

## 4. Explicit non-decisions

This matrix does not select or ratify:

- D01 signature/envelope algorithm or digest profile;
- D02 canonical encoding;
- D03 trust roots, delegation or issuer hierarchy;
- D04 key custody/signing mechanism;
- D05 physical verified-facts schema;
- D06 evidence authorities;
- D07 inventory closure source/protocol;
- D08 freshness, expiry or revocation protocol/windows;
- D09 owner authentication;
- D10 vocabulary beyond the already ratified G0.17 sensitivity labels/states;
- D11 parser/resource limits;
- D12 audit custody;
- D13 verified-facts binding details;
- D14 implementation/release gates.

G0.25 recommendations DSSE, Ed25519, SHA-256 and RFC 8785 JCS remain recommendations only. G1 A remains unsigned as specified in its existing contract. A1 remains a separate signature/trust extension.

## 5. Sequencing and gates

1. Owner/security reviews this classification and identifies any row whose claim boundary or assurance requirement must change.
2. Resolve D06–D09, D12 and D13 dependencies for the exact evidence classes selected for real issuer authentication.
3. Ratify only the minimum cryptographic, canonicalization, trust, freshness and owner-authentication profile needed for those claims.
4. Separately approve synthetic executable verifier tests using test-only keys and bounded fixtures.
5. Separately approve real evidence adapters and authenticated source integration.
6. Separately approve any exact-object lifecycle authorization and guarded executor.

No stage automatically authorizes the next.

## 6. Scope and verification

- Documentation-only classification; no source, test, fixture, schema, API, registry, adapter, runner, workflow, permission, credential, key, trust-root, database, storage, market-data, model, ledger, VPS or runtime changes.
- No tests or workflow dispatch.
- No key generation/import/signing/rotation/revocation; no trust-policy or anchor instance created.
- No network/provider/database/VPS access or inventory.
- No archive, quarantine, cleanup, expiry, compaction, VACUUM or deletion.
- No T0 canonical data access or mutation. T0 remains independent and protected.
- CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.

## 7. Final verdict

**G0.27: CLASSIFICATION PASS — claim-specific assurance requirements mapped across 14 evidence classes. D01–D14 remain OPEN / NOT RATIFIED where previously open; no cryptographic profile, verifier implementation, real evidence adapter, lifecycle authorization or executor is approved.**

Next: owner/security review of the evidence-class boundaries and explicit ratification/modification of the required decisions. Do not infer approval from a continuation request.
