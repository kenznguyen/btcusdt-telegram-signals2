# Stage A.8 — RET-06 and RET-08 Documentary Input Contracts

Date: 2026-11-10
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Work type: Stage A documentary requirements definition only
Frozen baseline HEAD: `21b4f9f5aba3392760ca7f6e7069262abd8ce662`
Status: **DOCUMENTARY CONTRACTS DEFINED — OWNER VALUES / AUTHORITY SOURCES NOT PROVIDED — RET-06 AND RET-08 OPEN**

## 1. Purpose and authority boundary

This document defines the minimum information that would be required to assess RET-06 (grace, cancellation, authorization lifetime and freshness) and RET-08 (emergency/legal/security request handling). It does not select values, interpret law, approve an exception, establish a break-glass route, authorize a mutation, or implement technical enforcement.

Controlling boundaries:
- Stage A automatic owner approval authorizes documentary work only.
- Option C — No Destructive Authority — remains unchanged.
- Lifecycle independent-human-review waiver applies only to the reviewer gate; explicit owner authorization, legal/security authority, substantive evidence and technical controls remain mandatory.
- T0 canonical data and availability/recovery copies, CORE_LEDGER, AI_LEDGER, required T3 reconstruction/audit records, governance evidence and unknown/unclassified/orphan/incompletely inventoried objects remain protected.
- Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders.
- Stage B technical contracts/implementation and Stage C operational inventory/enforcement are outside this approval.

## 2. RET-06 — grace, cancellation, authorization lifetime and freshness

### 2.1 Required contract fields

| Field group | Required documentary input | Current value/status |
|---|---|---|
| Policy identity | Immutable policy ID, revision, effective interval, supersession relation and exact class/object scope | NOT PROVIDED |
| Authorization identity | Unique authorization ID, issuer, authority basis, subject, exact action and object/version scope | NOT PROVIDED |
| Grace semantics | Definition of what grace delays, the event that starts it, whether it is calendar/elapsed/business time, and whether it is per object, class or request | NOT PROVIDED |
| Grace value | Approved duration and authoritative rationale for each applicable class/action | NOT PROVIDED; no value selected |
| Cancellation | Who may cancel, eligible states, cancellation event, effective ordering and proof of cancellation | NOT PROVIDED |
| Cancellation race | Precedence when cancellation, hold, policy revision, expiry or an operation request races | NOT PROVIDED; fail closed |
| Authorization lifetime | Start event, expiry event, one-time/reusable semantics, renewal/revocation and terminal status | NOT PROVIDED |
| Freshness | Which evidence must be fresh (policy, owner authority, object version, dependency graph, holds, trusted time, request and verifier result) | NOT PROVIDED |
| Freshness value | Maximum age / validity interval per evidence type and rationale | NOT PROVIDED; no value selected |
| Trusted clock | Authoritative time source, clock domain, uncertainty bounds, monotonicity, rollback behavior and outage response | V07 unresolved; NOT PROVIDED |
| Revision binding | Atomic or provably ordered binding among policy revision, exact object/version, hold/dependency state, authorization and trusted-time revision | RET-05/LDA-05 technical enforcement NOT VERIFIED |
| Expiry behavior | Behavior at, before, after or uncertain about expiry; in-flight operation treatment | NOT PROVIDED; fail closed |
| Evidence | Signed/immutable record of issue, approval, cancellation, renewal, expiry, revocation, freshness checks and final disposition | RET-07 OPEN; no evidence-retention floor |
| Recovery/replay | How to reconstruct ordering and state after restart, delayed messages, duplicate requests or restore | V08/Restore OPEN |

### 2.2 Required event model

The documentary contract must distinguish at least:

1. Request created — not an authorization.
2. Request authenticated — identity evidence only; not authority.
3. Owner/authority decision issued — exact scope and policy revision bound.
4. Authorization becomes effective — only after all required preconditions are satisfied.
5. Grace begins — only from a specifically approved typed event.
6. Cancellation requested — does not imply cancellation has taken effect.
7. Cancellation committed — ordered against all competing events.
8. Authorization renewed/reissued — new version/identity; must not silently extend a superseded authorization.
9. Authorization expired or revoked — no new operation may begin; in-flight handling must be explicitly specified.
10. Evidence freshness check — bound to the exact object/version and trusted-time observation.
11. Operation eligibility evaluated — a decision record, not permission to mutate under Option C.
12. Terminal disposition — recorded only when the approved lifecycle process proves the exact obligation closure.

These event names are a requirements vocabulary, not existing runtime events or an implementation claim.

### 2.3 Mandatory fail-closed outcomes

Until the owner supplies authoritative values and technical semantics:

- Missing/ambiguous grace value: no expiry or eligibility inference.
- Missing/ambiguous cancellation authority or event ordering: request remains unresolved; no operation.
- Missing/expired/revoked/uncertain authorization: deny operation.
- Stale or unverifiable policy, owner authority, object version, hold/dependency inventory or verifier evidence: deny operation.
- Trusted-time unavailable, rolled back, outside uncertainty bounds or inconsistent: deny operation; do not substitute local wall-clock guess.
- Concurrent policy revision, hold, cancellation, expiry or object-version change without proven ordering: deny operation.
- Missing evidence, incomplete copy graph or unknown object classification: retain/protect; no class-wide disposition.
- A valid RET-06 contract would still not override Option C or itself authorize deletion.

### 2.4 RET-06 status

**OPEN / NOT PROVIDED.** No grace duration, cancellation window, authorization lifetime, evidence freshness threshold, clock tolerance or expiry behavior is approved. V07, RET-05/LDA-05, V08, RET-07 and Restore dependencies remain unresolved.

## 3. RET-08 — emergency, legal and security request decision protocol

### 3.1 Request classification

A request must be classified before consideration. At minimum, distinguish:
- legal demand / court or regulator process;
- privacy or data-subject request;
- security incident / compromise / containment request;
- operational emergency / availability or integrity incident;
- internal owner request;
- ordinary lifecycle disposition request.

Classification is not a finding that the request is valid, binding, urgent or within the requester's authority.

### 3.2 Required request record

| Field group | Required evidence | Current value/status |
|---|---|---|
| Request identity | Immutable request ID, received time, channel, original document/message digest and custody | NOT PROVIDED |
| Requester identity | Verified person/organization, role, contact route and identity proof | NOT PROVIDED |
| Authority | Exact legal instrument, contract, policy delegation or incident authority; issuing body/person and competence | NOT PROVIDED |
| Jurisdiction/scope | Applicable jurisdiction, entity, system, data subject, dataset, object/version, time range and recipients | NOT PROVIDED |
| Request type | Preservation, access, disclosure, correction, restriction, investigation, security containment, deletion or other exact action | NOT PROVIDED |
| Deadline/urgency | Source of deadline, timezone, calculation basis and consequences of non-response | NOT PROVIDED |
| Conflict check | Existing holds, court orders, disputes, investigations, security incidents, contractual duties and contradictory instructions | NOT PROVIDED |
| Technical feasibility | Exact affected objects/copies, dependencies, provenance and risk to T0/T3 reconstruction/recovery | NOT VERIFIED |
| Decision authority | Competent owner/legal/security/operational decision-maker for the request category | NOT PROVIDED |
| Decision | Accept, reject, narrow, preserve pending clarification, refer/escalate or unable to comply; reason and authority | NOT PROVIDED |
| Execution authority | Separate explicit scope, action, object/version, preconditions and authorization, if any | NOT PROVIDED; no execution authority |
| Notification | Who may/must be notified, restrictions, recipient and proof | NOT PROVIDED |
| Evidence/custody | Request, identity/authority verification, analysis, decision, communications, actions and readback evidence | RET-07 OPEN |
| Reconsideration | Appeal, clarification, expiry, review trigger, changed order and supersession handling | NOT PROVIDED |

### 3.3 Decision sequence

1. Preserve the original request and its provenance; do not alter or destroy the request record.
2. Authenticate the requester and independently validate the asserted authority using an authoritative channel appropriate to the request type.
3. Classify the request and record the claimed jurisdiction, scope, deadline and requested action.
4. Identify exact objects and versions. If scope is broad, ambiguous, unclassified or not fully inventoried, do not infer a safe target set.
5. Identify conflicts, existing holds, dependencies, T0 canonical/recovery status, CORE_LEDGER/AI_LEDGER and T3 reconstruction/audit requirements.
6. Obtain a competent decision from the appropriate owner/legal/security authority. The lifecycle reviewer waiver is not a waiver of competent authority.
7. Record a reasoned disposition: accept, reject, narrow, preserve pending clarification, escalate or unable to comply. Preserve the source and decision chain.
8. Keep decision and execution authority separate. A request, deadline, emergency label or approval to disclose/preserve does not authorize deletion or any other mutation.
9. Any future action would require a separate explicit owner decision and the applicable technical/operational gate. This document grants none.
10. Verify and retain evidence of any separately authorized action; if the result or scope cannot be verified, record BLOCKED/NOT VERIFIED and stop.

### 3.4 Default handling and fail-closed rules

- Unauthenticated requester or unverified authority: do not act on the request; preserve the request record and escalate for clarification.
- Ambiguous legal instrument, jurisdiction, deadline or scope: do not infer; seek competent clarification.
- Conflicting order, hold, dispute, investigation or preservation duty: preserve the affected data and escalate; do not resolve legal priority by software.
- Unknown or incompletely inventoried object/copy/recipient: protect and mark BLOCKED_UNKNOWN.
- Emergency/security label without validated authority and exact scope: no bypass.
- Request to disclose or preserve: does not authorize deletion.
- Request to delete or shorten retention: does not override Option C, protected-class exclusions, incomplete inventory or separate owner approval.
- No break-glass path is approved. No emergency/legal/security exception is pre-approved.
- If authority, scope, time, evidence or outcome is uncertain, take no destructive action and preserve the status quo.

### 3.5 RET-08 status

**OPEN / NOT PROVIDED.** No competent authority register, jurisdictional protocol, legal/security decision workflow, exception path, break-glass authority, response deadline rule or execution authorization is approved.

## 4. Interaction between RET-06 and RET-08

- RET-08 request receipt/authentication does not create a RET-06 authorization.
- A RET-08 decision cannot bypass RET-06 policy/object/version binding, trusted-time or freshness requirements.
- RET-06 grace or authorization expiry cannot extinguish a legal/security hold or unresolved request unless a competent authority has explicitly determined the applicable rule.
- A cancellation/expiry race with a legal request, hold, incident or policy revision is unresolved and must fail closed.
- Neither contract changes protected-class exclusions, the independent T0 boundary, ledger separation or Option C.

## 5. Stage A.8 outcome

| Criterion | Result |
|---|---|
| RET-06 required fields and event vocabulary | **PASS — DOCUMENTARY REQUIREMENTS ONLY** |
| RET-06 numeric values / trusted-time profile / enforcement | **NOT PROVIDED / OPEN / NOT VERIFIED** |
| RET-08 request taxonomy and evidence fields | **PASS — DOCUMENTARY REQUIREMENTS ONLY** |
| RET-08 competent authority / jurisdictional protocol | **NOT PROVIDED / OPEN** |
| Break-glass / exception authority | **NONE APPROVED** |
| Technical implementation or enforcement | **NOT AUTHORIZED; Stage B/C excluded** |
| Tests / GitHub Actions | **NOT RUN / NOT DISPATCHED** |
| Runtime, legal-system, provider, copy or permission probes | **NOT PERFORMED** |
| Any mutation or destructive lifecycle operation | **NOT AUTHORIZED / NOT EXECUTED** |

## 6. Next Stage A action

Stage A documentary work can now reconcile RET-03/06/07/08 inputs into one consolidated acceptance checklist, marking each exact owner-supplied field as PROVIDED only when supported by a pinned authoritative record. The current result is that material owner/legal/operational inputs remain NOT PROVIDED. If no such source is found, preserve the block and complete Stage A with explicit unresolved dispositions; do not manufacture policy values.

**Final disposition: RET-06 AND RET-08 DOCUMENTARY INPUT CONTRACTS DEFINED — VALUES / AUTHORITY NOT PROVIDED — BOTH OPEN — OPTION C UNCHANGED.**
