# Stage K.0–K.6 — Owner Adjudication Decision Package for Contract Freeze Blockers
Date: 2026-11-10
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/t0-centralized-data-feeder-p1-20261101
Work type: documentary decision preparation; no implementation or execution.
Status: PACKAGE COMPLETE; OWNER-ONLY POLICY DECISIONS REMAIN OPEN; CONTRACT FREEZE NOT READY.

## K.0 — Authority and interpretation

The owner approved automatic execution of subsequent stages. This stage applies that approval to documentary work: classify blockers, reconcile already-approved directions, prepare conservative decision proposals, and identify matters that cannot be truthfully resolved without owner policy or technical evidence.

The approval does not authorize the assistant to invent owner preferences, select a paid/external provider, create accounts/credentials, change repository/VPS permissions, implement schemas, run tests/probes, dispatch workflows, or execute lifecycle operations. No owner decision is recorded as APPROVED unless it is already explicitly approved in Stage H or the current project record.

Standing restrictions remain:
- Option C — No Destructive Authority ACTIVE.
- TEST-08 NOT GRANTED.
- No implementation or technical execution authorization.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Independent Review waiver remains in force, without waiving technical verification.

## K.1 — Decision taxonomy

Each J-OPEN item is classified as:
- **OWNER POLICY**: requires an explicit policy choice or acceptance of a trade-off.
- **TECHNICAL SPECIFICATION**: can be drafted from already-approved architecture, but requires conformance evidence before freeze.
- **OWNER + TECHNICAL**: owner selects policy boundary; technical evidence must demonstrate enforcement.
- **EXTERNAL EVIDENCE**: cannot be closed by prose; requires separately authorized read-only inspection or later implementation evidence.

## K.2 — Blocker-by-blocker adjudication proposals

| ID | Class | Existing approved baseline | Conservative proposal | Current disposition |
|---|---|---|---|---|
| J-OPEN-01 JCS library/parser | TECHNICAL SPECIFICATION + OWNER acceptance | RFC 8785 JCS + SHA-256 direction approved | Select one maintained implementation only after compatibility review; require strict input rejection and published positive/negative golden vectors; do not silently normalize invalid input | OPEN; no library selected |
| J-OPEN-02 numeric/Unicode | OWNER + TECHNICAL | No detailed profile approved | Prefer a narrow interoperable subset: bounded integers for counters/sequence, explicit decimal representation for financial quantities, valid Unicode scalar strings, reject non-finite numbers and ambiguous encodings; exact bounds/decimal scale require domain review | OPEN; proposal only |
| J-OPEN-03 digest/ID envelope | TECHNICAL SPECIFICATION | SHA-256 direction approved | Separate raw-source-byte digest from canonical-payload digest; domain-separate each ID class; specify algorithm prefix, byte encoding and collision/uniqueness scope | OPEN; exact envelope/registry not frozen |
| J-OPEN-04 schemas/evolution | OWNER + TECHNICAL | Logical entities and relationships documented in C.13/I | Version every record schema; reject unknown required semantics; additive optional fields only within compatibility rules; prohibit silent reinterpretation and destructive migrations | OPEN; exact schema registry/matrix absent |
| J-OPEN-05 time/causality | OWNER + TECHNICAL | Causal links and monotonic sequence concept documented | Treat sequence/causal links as authoritative for ordering; wall-clock timestamps are descriptive claims with explicit source/precision/uncertainty; never infer causality from timestamps alone | OPEN; sequence scope and clock profile not chosen |
| J-OPEN-06 retry/correction | TECHNICAL SPECIFICATION + OWNER acceptance | C.13 logical operation/attempt/correction entities | Stable operation identity for identical canonical request; unique attempt per retry; immutable append-only corrections; reject cycles, orphan references and ambiguous terminal states | OPEN; formal state machine/golden cases absent |
| J-OPEN-07 synthetic isolation | OWNER + TECHNICAL + EXTERNAL EVIDENCE | Layered per-run synthetic isolation target approved | Default deny network; separate per-run namespace and storage root; no shared writable path with protected/evidence resources; prove both allowed and denied access using isolated synthetic tests before readiness | OPEN; topology and proof absent |
| J-OPEN-08 identities/capabilities | OWNER + TECHNICAL + EXTERNAL EVIDENCE | Distinct least-privilege roles approved | Separate effective principals for executor, adapter, observer/oracle, publisher and verifier; executor has no evidence-store write/delete capability; verify effective permissions, not configuration alone | OPEN; identity provider and capability proof absent |
| J-OPEN-09 evidence destination | OWNER POLICY + EXTERNAL EVIDENCE | Hybrid Git index + separate versioned payload direction approved; no provider selected | Preserve provider-neutral design; require exact-version retrieval, append-only semantics, independent read-back and destination outside cleanup boundary; choose no provider until cost, ownership, retention and access are assessed | OPEN; provider/owner/effective behavior absent |
| J-OPEN-10 verifier trust | OWNER + TECHNICAL + EXTERNAL EVIDENCE | Independent exact-version verifier approved | Verifier must be read-only and separately trusted; bind verifier build/policy/trust roots; verify exact bytes, digest, schema, provenance, causal closure and full denominator; signed result only after trust design is approved | OPEN; trust roots and result schema absent |
| J-OPEN-11 retention/recovery | OWNER POLICY + EXTERNAL EVIDENCE | Governance requirements for retention/hold/recovery partially approved | No automatic expiry/deletion while Option C active; preserve evidence by default; set retention and recovery objectives only after owner selects required preservation horizon and validates provider capabilities | OPEN; no durations/provider/mechanism approved |
| J-OPEN-12 TEST-08 | OWNER AUTHORIZATION | Not granted | Require separate exact-scope approval identifying target, operations, limits, rollback/stop conditions and evidence; this package does not grant it | NOT GRANTED |
| J-OPEN-13 LDA-06/LDA-08 | EXTERNAL EVIDENCE + SEPARATE AUTHORIZATION | LDA-06 partial; LDA-08 hold after 403 | Use only a separately authorized read-only route; do not change permissions or infer effective access from workflow YAML | PARTIAL / HOLD; NOT VERIFIED |

## K.3 — What is already decided versus not decided

### Existing approved decisions retained

1. Canonicalization direction: RFC 8785 JCS + SHA-256.
2. Isolation target: layered per-run synthetic isolation.
3. Identity target: distinct least-privilege principals.
4. Evidence architecture direction: Git index plus separately versioned evidence payload.
5. Verification model: independent exact-version verifier.
6. Retention governance: preserve protected evidence; no implicit cleanup authority.

These decisions are not reopened by Stage K.

### Decisions not made by this stage

- No concrete JCS library/version, numeric bounds or Unicode profile.
- No exact schema IDs/field types/compatibility matrix.
- No time authority, sequence namespace or uncertainty thresholds.
- No identity provider, credential store or external evidence provider.
- No retention duration, backup/recovery objective or paid service selection.
- No lifecycle test authorization, repository permission change or technical probe.

## K.4 — Recommended decision order and dependencies

1. **K-D1 Data/canonical profile:** resolve J-OPEN-01–04 together; golden vectors must cover numeric, Unicode, null/absent, ordering and digest-domain cases.
2. **K-D2 Event and causal model:** resolve J-OPEN-05–06; define deterministic ordering, retries, corrections and cycle rejection.
3. **K-D3 Trust boundaries:** resolve J-OPEN-07–08; choose topology and identity design, then prove effective isolation separately.
4. **K-D4 Evidence/verifier:** resolve J-OPEN-09–10; choose destination only after trust, ownership, exact-version and verifier requirements are concrete.
5. **K-D5 Preservation policy:** resolve J-OPEN-11; retain Option C until owner approves explicit retention/hold/recovery values and evidence shows enforceability.
6. **K-D6 Readiness evidence:** handle J-OPEN-13 only through authorized read-only evidence collection.
7. TEST-08 remains a separate gate; it is not bundled into contract design or freeze approval.

Dependencies are logical, not a grant of permission to execute any later activity.

## K.5 — Freeze-readiness decision

**CONTRACT FREEZE: NOT READY.**

Reasons:
- Normative data/canonicalization and schema profile is not frozen.
- Time/causal and retry/correction semantics are not executable or fully testable.
- Effective isolation and principal separation are not demonstrated.
- Evidence destination and verifier trust are not selected/proven.
- Retention/recovery policy lacks owner-approved operational values.
- LDA-06/LDA-08 remain unverified.

A documentary decision package is not a substitute for the owner's explicit policy decisions or for technical evidence. No item is marked resolved solely because a proposal is written here.

## K.6 — Closure and next step

Stage K.0–K.6 is complete as a decision-preparation package:
- J-OPEN-01–13 classified;
- existing Stage H approvals preserved;
- conservative proposals and dependencies documented;
- unresolved owner decisions remain visibly OPEN;
- contract freeze remains NOT READY;
- no technical gate or authorization upgraded.

Recommended next step: **Stage L — Contract Profile Specification Draft**, documentary-only, limited to translating already-approved directions and the conservative proposals into a candidate profile with explicit TBD markers. It must not select providers, libraries, retention values, credentials or owner policy by implication. Owner decisions remain required before freeze; implementation/testing require separate authorization, and TEST-08 remains mandatory for lifecycle execution.

**STAGE K DECISION PACKAGE COMPLETE — OWNER POLICY ITEMS OPEN — CONTRACT FREEZE NOT READY — OPTION C ACTIVE.**
