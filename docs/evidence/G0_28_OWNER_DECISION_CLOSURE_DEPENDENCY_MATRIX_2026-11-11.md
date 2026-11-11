# G0.28 — Owner Decision Closure and Dependency Matrix

Date: 2026-11-11 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Baseline HEAD: `12f781b077526eae3b5856fdb3c6a9ceba724ce4`
Baseline handoff blob: `803a47772461d4d510718e5c088f746fc512f18a`
Type: documentation-only dependency and decision-closure analysis
Disposition: **DEPENDENCY ANALYSIS PASS — DECISION SCOPE REDUCED; ALL OWNER RATIFICATIONS REMAIN OPEN; IMPLEMENTATION NOT AUTHORIZED**

## 1. Purpose

G0.28 translates the G0.24 D01–D14 register and G0.27 E01–E14 assurance matrix into a decision-closure plan. It identifies:
- which decisions are prerequisites for which claims and work stages;
- which decisions can be deferred if the corresponding claim or capability is explicitly excluded;
- which decisions cannot be avoided for a real authenticated evidence-verification path;
- what evidence is needed to close each decision.

This is not a ratification. A recommendation, dependency classification, continuation request, Git commit or CI result does not constitute owner approval.

## 2. Closure rules

1. **Scope before profile:** first define the exact evidence classes and claims in scope. Do not design a universal trust system for evidence classes that are not being consumed.
2. **No silent downgrade:** an OPEN decision remains OPEN. A stage may exclude a capability only if it also excludes every claim that depends on it.
3. **Separate claim types:** digest integrity, issuer authenticity, owner authorization, freshness, completeness and custody are separate outcomes.
4. **No caller assertions as proof:** names, booleans, paths, counts, timestamps and `complete=true` remain untrusted until independently verified under the selected authority model.
5. **No authority by implication:** verifier PASS, evaluator disposition, workflow success and signed issuer claims do not authorize lifecycle actions.
6. **Preserve existing boundaries:** G1 A remains the unsigned T0 proof-of-existence product; A1 is a separate trust extension. T0 canonical data remains outside lifecycle mutation scope.

## 3. D01–D14 closure matrix

Status at baseline: all D01–D14 remain OPEN. The “closure class” below is a planning classification, not a decision outcome.

| Decision | Closure class | Needed for | Can be deferred only if | Required closure evidence |
|---|---|---|---|---|
| D01 — Crypto integrity/authenticity profile | **Claim-critical** | Any real cryptographic signature verification or issuer-authenticity claim; digest profile for normalized integrity claims | All signed/issuer-authenticity claims and cryptographic verification are excluded; any digest-only claim still needs an explicit digest/byte-binding contract | Exact algorithm/profile/version, signed statement fields and domain separation; separate digest/signature semantics; test vectors; migration/failure behavior |
| D02 — Canonical representation | **Contract-critical** | Any signed structured statement or deterministic digest over structured envelope content | Structured canonical payloads are excluded and only raw-byte digesting is in scope | Normative byte representation, parser rejection rules, Unicode/number/null/duplicate-key behavior, version and cross-implementation vectors |
| D03 — Trust roots and issuer delegation | **Claim-critical** | Any assertion that a real issuer is authentic and authorized for a claim | No real issuer-authenticity claim or real evidence adapter is in scope | Principal/key binding, trust-root custody/authority, issuer scopes, delegation and revocation authority |
| D04 — Key lifecycle | **Claim-critical** | Any real signing or verification trust lifecycle, including issuer rotation/revocation | Only synthetic test keys are used and real signing/issuer trust is excluded | Generation/use/custody/rotation/compromise/revocation/recovery boundaries; synthetic/real separation |
| D05 — Envelope schema/versioning | **Contract-critical** | Any physical verified-facts envelope, parser, verifier API or interoperable evidence contract | No physical envelope/parser/verifier is implemented | Versioned schema, required/critical fields, extension rules, duplicate/unknown field behavior, immutable subject binding and compatibility vectors |
| D06 — Evidence authorities and immutable resolution | **Source-critical** | Real source adapters and claims grounded in GitHub/provider/registry/source records | Only self-contained synthetic fixtures and no real source claims are used | Authority map by evidence class; exact version resolution; consistency/snapshot behavior; availability/readback semantics |
| D07 — Inventory registry and closure | **Completeness-critical** | Claims that holds, dependencies, consumers, copies, backups, replicas or lineage have been exhaustively enumerated | The output explicitly makes no completeness/closure claim and is limited to a known fixed fixture set | Authoritative inventory boundaries, snapshot/terminal cursor proof, reconciliation and exclusion accounting |
| D08 — Freshness, time and revocation | **Current-state-critical** | Claims about current policy, active issuer authority, latest inventory/checkpoint, expiry or non-revocation | The system makes no current/latest/non-revoked claim and rejects such decisions as UNKNOWN/BLOCKED | Class-specific freshness rules, trusted-time/clock-skew policy, expiry semantics, revocation source and outage behavior |
| D09 — Owner/steward authentication | **Authorization-critical** | Owner approval, declassification, lifecycle action approval or other owner-only decisions | No owner approval is verified or action is authorized by the system | Authenticated principal and delegated authority; exact action/target/version/scope; expiry/revocation and separation of duties |
| D10 — Data-class vocabulary/mapping | **Evaluator-critical** | Mapping real objects into supported lifecycle/sensitivity classes | Evaluator is restricted to explicitly enumerated synthetic fixture classes | Versioned allowlist and exact mapping; unknown class behavior; G0.17 inheritance preserved |
| D11 — Resource limits | **Implementation-critical** | Any parser, verifier, adapter or inventory traversal exposed to variable/hostile inputs | No executable parser/verifier/adapter is built | Measured upper bounds and explicit limits for bytes, arrays, depth, pages, time, retries, memory and diagnostics |
| D12 — Audit custody/retention/redaction | **Audit-claim-critical** | Claims that verification/approval history is retained, tamper-evident or recoverable | No such audit custody/retention/recoverability claim is made and no production audit store is introduced | Custodian/store authority, integrity/order mechanism, redaction, retention policy, retrieval and independent readback |
| D13 — Verified-facts binding/process boundary | **Trust-boundary-critical** | Passing verified facts from verifier to evaluator or another process without caller forgery/replay | No verified-facts object is produced or consumed; design remains conceptual | Exact subject/evaluation/policy/build binding, immutability, constructor/process boundary, replay/reuse semantics and freshness revalidation |
| D14 — Review/implementation/release gates | **Stage-control-critical** | Moving from documentation to executable tests, implementation, real adapters or operations | A later stage is not entered | Named gate criteria, reviewers/owners, required evidence, read-only permissions and explicit next-stage authorization |

### Interpretation

- “Can be deferred” never means “implicitly approved”. It means the corresponding capability and claim must be explicitly excluded from the stage.
- D01–D04 form a coupled authenticity/key lifecycle group; selecting a signature algorithm alone cannot close issuer trust.
- D02 and D05 must agree: canonical bytes cannot be specified independently of the schema and parser's accepted representations.
- D06 and D07 jointly govern evidence source authority and inventory completeness.
- D08 depends on D03, D06 and D07: revocation and freshness cannot be established without knowing who is authoritative and where current state comes from.
- D09 is separate from issuer authenticity; a trusted producer is not necessarily authorized to approve an owner action.
- D10, D11, D12 and D13 are necessary for a bounded, safe executable evaluator/verifier boundary, even if no real signing is involved.
- D14 controls stage transitions; it cannot replace technical decisions in D01–D13.

## 4. Minimum decision sets by possible stage

| Stage | Minimum decisions/contracts required | Explicitly excluded claims/capabilities |
|---|---|---|
| S0 — Documentation and synthetic logical matrix only | No owner ratification required beyond permission to author docs; preserve current fail-closed semantics | No executable verifier, no cryptographic trust claim, no real evidence, no completeness claim, no owner authorization, no runtime |
| S1 — Deterministic synthetic parser/contract tests without cryptography | D05 schema/parser contract; D10 synthetic class vocabulary; D11 bounded fixture/parser limits; D14 test gate | No signatures, real issuer authenticity, real source truth, production inventory closure, owner approval or lifecycle action |
| S2 — Synthetic cryptographic verifier tests using test-only keys | D01–D05 for the synthetic profile/schema; D10–D11; D13 binding; D14 test gate; D03–D04 explicitly scoped to isolated test-only trust/key lifecycle | No production keys/trust roots, no real issuer authority, no real source adapter, no production owner approval |
| S3 — Real evidence-source verification | D01–D08, D10–D13 as applicable to the selected evidence classes; D06/D07 authoritative source decisions; D14 real-source gate | No lifecycle action unless D09 and separate action gate are closed |
| S4 — Owner authorization workflow | D01–D05 as applicable, D08–D10, D12–D14; exact owner identity and policy decisions | No execution unless a separate exact-scope executor gate is approved |
| S5 — Guarded lifecycle executor | All applicable decisions D01–D14 closed, plus separately approved exact-object action, preconditions, recovery and executor-specific safeguards | No T0 canonical mutation; no blanket deletion; no automatic expansion to new classes/objects |

Stages are a dependency model, not authorization to begin any stage. Only S0 documentation work is covered by this G0.28 task. S1–S5 each require separate approval.

## 5. Evidence-class impact and current scope

From G0.27:
- E01 G1 A: retain unsigned proof-of-existence contract; do not add signer-authenticity requirements.
- E02–E04 and E12: Git/CI evidence may support integrity and execution-provenance claims, but platform metadata does not become owner authorization or independent custody proof.
- E05: synthetic fixtures can be tested without real identities or production keys; test outcomes do not establish real-source trust.
- E06–E09: real source, inventory, sensitivity and policy claims require authoritative issuers, exact binding and applicable freshness/completeness checks.
- E10 and E14: owner authorization remains a distinct authenticated decision.
- E11: custody/recoverability requires independent readback.
- E13: pure evaluator output remains a disposition only, never execution authority.

No G0.27 evidence class is designated a production authoritative source by this report.

## 6. Recommended owner review order (not ratification)

To avoid premature decisions and minimize unnecessary complexity, review in this order:

1. **Scope decision:** identify which evidence classes and claim types the first executable milestone is allowed to support.
2. **D05 + D10 + D11:** define a bounded synthetic-only contract/class set/resource envelope if the owner wants to authorize S1.
3. **D01–D04:** decide the minimum cryptographic and key/trust model only if S2 or real issuer-authenticity claims are intended.
4. **D06–D08:** choose real evidence authorities, closure and freshness only before S3.
5. **D09 + D12 + D13:** resolve owner authorization, audit custody and verified-facts binding before S4.
6. **D14:** ratify gate evidence and reviewers for the exact next stage.

This order is a recommendation; D01–D14 remain OPEN. No decision is approved or rejected here.

## 7. Explicit non-decisions and prohibitions

- No cryptographic algorithm, canonical encoding, trust root, issuer, key, freshness window, registry, schema, resource limit, audit store, owner authentication method or executor is selected.
- G0.25 DSSE/Ed25519/SHA-256/JCS remain recommendations only.
- No synthetic cryptographic test key is generated; no signing or verification is implemented.
- No parser, verifier, schema, registry, adapter, API, fixture file, runner or workflow is created.
- No tests or workflow dispatch.
- No provider/network/database/VPS/runtime access or inventory.
- No archive, quarantine, cleanup, expiry, compaction, VACUUM or deletion.
- T0 canonical data and lease/fencing remain independent and protected; no T0 mutation.
- CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.

## 8. Final verdict and next gate

**G0.28: DEPENDENCY ANALYSIS PASS — D01–D14 mapped to claim/stage dependencies and conditional deferral rules. All owner/security decisions remain OPEN / NOT RATIFIED; no implementation or operational authority is granted.**

Next gate: owner explicitly chooses the scope of the first executable milestone (if any), including evidence classes and claims it may and may not support. Only after that scope decision should the minimum subset of D01–D14 be ratified. A request to “continue” is not a scope decision or cryptographic ratification.
