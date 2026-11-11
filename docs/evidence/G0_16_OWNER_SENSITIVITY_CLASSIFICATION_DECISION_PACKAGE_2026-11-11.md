# G0.16 — Owner Sensitivity Classification Decision Package (2026-11-11)

Date: 2026-11-11  
Work type: documentation-only policy proposal for owner decision  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Starting HEAD: `612be4f428a34cbc9c4a934d05e422c76ed9ef1c`

## 1. Purpose and boundary

G0.16 proposes a small sensitivity-label vocabulary and conservative class-level default mapping to address G0.14 R4 / G0.15 R4. It is a decision package, not a ratified policy.

The proposal separates two independent questions:

- **Sensitivity**: what confidentiality/access-protection level applies to the information?
- **Lifecycle disposition**: whether an exact object/version is protected, retained, blocked, or may enter a future read-only review under RET-01/RET-02.

A sensitivity label never grants lifecycle eligibility, deletion approval, archive approval, execution authority, or permission to weaken a protection/hold. RET-01 B, RET-02 B and P1.8.144 remain controlling. No numeric retention periods, TTLs, freshness windows, or grace periods are proposed.

No runtime inventory or data inspection was performed. The mapping below is a proposed policy baseline for owner review, not a claim about the current contents of any VPS, database, repository artifact, or provider.

## 2. Proposed sensitivity vocabulary

Four ordered labels are proposed. Higher levels are more restrictive.

| Label | Meaning | Minimum handling expectation |
|---|---|---|
| `PUBLIC` | Information explicitly approved for unrestricted public release; disclosure creates no material confidentiality, security, privacy, or integrity risk | May be published only after an explicit release decision and removal of secrets/identifiers |
| `INTERNAL` | Non-public operational or engineering information intended for the project owner and explicitly authorized collaborators | Authenticated access; do not publish or place in public artifacts by default |
| `CONFIDENTIAL` | Information whose disclosure could expose system design, operational posture, research, proprietary datasets, model behavior, or non-public project activity | Least-privilege access; encrypted transport/storage where supported; restrict exports and copies |
| `RESTRICTED` | Information whose disclosure could compromise canonical data integrity, trading/risk controls, account/ledger reconstruction, security, custody, credentials, trust, or governance authority | Narrowest access; explicit owner-controlled handling; no public or general-purpose artifact distribution |

### 2.1 Non-label classification states

These are states, not sensitivity labels:

- `UNCLASSIFIED`: no authoritative sensitivity decision exists.
- `CONFLICTED`: applicable sources assign inconsistent labels or scope.
- `PENDING_OWNER_DECISION`: a class or exception has not been ratified.

Any of these states blocks ordinary processing that requires an authoritative sensitivity label. Do not silently coerce them to `INTERNAL` or `PUBLIC`. Until resolved, preserve the object and use the more protective handling posture.

## 3. Proposed class-level default mapping

The table proposes a **minimum default label**, not a final classification of every object. Exact object content, embedded fields, lineage, export context, and applicable obligations may require a higher label.

| Data class / domain | Proposed minimum default | Rationale and constraints |
|---|---|---|
| T0 canonical candles, source versions, correction lineage | `RESTRICTED` | Independent canonical asset; integrity, provenance and replay value must be protected. RET-01 B still prohibits routine/automatic deletion |
| T0 lease, fencing, writer and recovery state | `RESTRICTED` | Can affect canonical write safety, recovery and custody |
| T1 raw exchange observations and capture manifests | `CONFIDENTIAL` | Non-public raw market observations, collection details and provenance; raise to RESTRICTED if they expose credentials, security-sensitive endpoints, or protected control evidence |
| T1 sidecar/session integrity, gap and provenance evidence | `RESTRICTED` | Supports source identity, completeness, ordering and evidence trust |
| T2 canonical input snapshots, features, labels, training datasets | `CONFIDENTIAL` | Non-public research inputs and derived information; raise to RESTRICTED where they contain protected source/control or account material |
| T2 model artifacts, evaluation reports and model provenance | `CONFIDENTIAL` | Non-public model behavior, research conclusions and reproducibility information |
| T2 ephemeral inference outputs | `CONFIDENTIAL` | May reveal model behavior or decision context; sensitivity does not determine whether output is material or reviewable |
| T3 CORE_LEDGER, AI_LEDGER, account/equity, reservations, risk state | `RESTRICTED` | Protected account, strategy separation, risk and outcome-reconstruction records |
| T3 signals, decisions, paper events, fills, funding, reconciliation and audit records | `RESTRICTED` | Supports decision and paper-outcome reconstruction and audit |
| T4 deterministic caches, read models and materializations | `INTERNAL` | Proposed minimum only; elevate to the highest sensitivity of source fields or derived content. RET-02 review gates remain mandatory |
| Governance approvals, policy history, custody/trust records, manifests, holds, tombstones and lifecycle evidence | `RESTRICTED` | Proves authority, lineage, policy decisions and lifecycle outcomes |
| Synthetic fixtures and CI reports | `INTERNAL` | Only when wholly synthetic and free of secrets, real identifiers, production payloads and restricted evidence; otherwise inherit the highest embedded level |
| Noncanonical copies, backups, replicas and exports | Inherit source label; never lower by default | Each copy has its own identity and custody. Raise for aggregation, recipient/context or embedded sensitive material; no cascade assumptions |
| Unknown, unclassified, orphaned or incompletely inventoried data | `UNCLASSIFIED` state; handle as `RESTRICTED` pending resolution | Unknown is protective; never infer that unknown data is disposable or public |

## 4. Proposed assignment and inheritance rules

1. Assign sensitivity at the exact object/version boundary where feasible; a broad class default is only a minimum.
2. Effective sensitivity is the most restrictive of: class default, source/parent label, embedded-content label, applicable policy/hold label, and recipient/export-context requirement.
3. A copy, backup, replica, cache, feature, report or export inherits the highest sensitivity of its inputs unless an approved transformation-specific assessment proves otherwise.
4. Aggregation does not lower sensitivity. Derived outputs may be raised where they reveal underlying restricted information or enable reconstruction.
5. Downgrading or declassification requires an explicit owner-approved, exact-scope decision with evidence; successful consumption, rebuildability, ACK, age, or a new copy does not lower a label.
6. Missing, stale, contradictory or unauthenticated classification evidence results in `UNCLASSIFIED` / `CONFLICTED`, fail-closed handling and preservation.
7. Credentials, private keys, tokens, signing material and trust-root secrets are always `RESTRICTED`; never include their values in evidence reports or ordinary CI artifacts.
8. Public release is a separate explicit decision. A `PUBLIC` label cannot be assigned merely because a file is in a public repository or an artifact has expired.

## 5. Relationship to lifecycle decisions

Sensitivity is an input to access, storage, encryption, export and evidence-handling decisions. It does not replace the G0.12 five-disposition evaluator or P1.8.144 obligation analysis.

- `RESTRICTED` does not automatically mean permanent retention; applicable lifecycle policy still governs, with protected precedence.
- `INTERNAL` does not mean disposable.
- `PUBLIC` does not imply deletion eligibility.
- RET-02 reviewability does not automatically lower sensitivity.
- `FLOOR_ESTABLISHED_FOR_REVIEW` is not deletion approval or execution authority.
- Any lifecycle uncertainty remains PROTECTED / RETAIN / BLOCKED as applicable.

## 6. Owner decisions requested

Please ratify, amend or reject each proposal:

1. **Vocabulary** — approve the four ordered labels `PUBLIC < INTERNAL < CONFIDENTIAL < RESTRICTED`, with `UNCLASSIFIED` and `CONFLICTED` as non-label states.
2. **Class defaults** — approve or amend the minimum mapping in §3, especially T1/T2/T4 and synthetic/CI evidence.
3. **Inheritance** — approve the most-restrictive-wins rule for copies, backups, replicas, exports and derived outputs.
4. **Downgrade/declassification** — require a separate exact-scope owner decision; no automatic downgrade.
5. **Unknown handling** — approve fail-closed preservation and restricted handling pending classification.
6. **Credential/trust material** — approve unconditional `RESTRICTED` handling and prohibition on embedding secret values in ordinary evidence artifacts.

If a proposed label or mapping is not accepted, keep the relevant class `PENDING_OWNER_DECISION`; do not invent a fallback.

## 7. Verification and status

- Source policy reconciliation: PASS at documentary level against RET-01 B, RET-02 B, P1.8.80, P1.8.143, P1.8.144 and Stage C.13.
- Proposal authored: pending GitHub readback after commit.
- Owner ratification: **PENDING**.
- Independent review: **NOT RUN**.
- Tests: **NOT RUN** (documentation-only).
- GitHub Actions: **NOT DISPATCHED**; no run/artifact.
- Sensitivity implementation/schema/evaluator integration: **NOT IMPLEMENTED**.
- Runtime inventory/classification: **NOT PERFORMED / NOT VERIFIED**.
- G0.15 R4: remains **BLOCKED** until owner ratifies exact vocabulary and mapping.
- Destructive authority: **NOT GRANTED** by this proposal.

## 8. Explicit non-actions

No source code, tests, fixtures, schema, API, registry, adapter, runner, oracle, workflow, scheduler, service, permission, credential, database, storage, VPS, market data, model, ledger or runtime changes. No production inventory, file scan, secret scan, network/provider/database access, workflow dispatch, archive, quarantine, cleanup, expiry, compaction, vacuum or deletion.

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.

## 9. Next gate

Owner review of the six decisions in §6. If ratified, a separate bounded approval is required before changing evaluator fields/tests or any schema/registry integration. Independent review, TEST-01–07, CI dispatch, evidence authentication, runtime inventory and destructive operations remain separate gates.
