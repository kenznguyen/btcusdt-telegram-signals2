# L4-Minimum Provenance Acceptance Matrix — Lifecycle-Aligned Revision

Date: 2026-11-10
Parent decision: `docs/decisions/D-2026-11-09-L4-PROVENANCE-PERSONAL-SCOPE.md`
Scope: personal, non-commercial BTCUSDT Quant System
Status: **DESIGN / TEST-PLAN ONLY — DOCUMENTARY REVISION — NOT IMPLEMENTED, NOT EXECUTED, NOT ACCEPTED**

Controlling lifecycle records:
- P1.8.143 — Owner Retention Policy Ratification, blob `6f4451f1eb193e763970581bcd6d8a782508acfd`.
- P1.8.144 — Retention Floor Evidence Contract, blob `f3002ba709f874936ca434c883ef855d2f11784a`.
- P1.8.152 — Retention Decision and Lifecycle Residual Finding Reconciliation, blob `e1a4d95af216e94a58fa5528850fcd0c1ff465f8`.
- P1.8.146/P1.8.147/P1.8.148/P1.8.149/P1.8.150/P1.8.151 reviewer and copy-graph clarification chain as recorded in P1.8.152.

## 1. Purpose, scope and authority

Translate the owner-approved L4-Minimum provenance profile into falsifiable acceptance requirements and align its evidence lifecycle with the owner-ratified retention policy.

L4-Minimum is proportionate to a single-owner, personal, non-commercial system. It does not require SaaS/multi-tenant features, customer SLA, commercial compliance certification, multi-TSA quorum, dedicated WORM or a paid third-party assurance service absent a concrete need.

**Market-data source independence is excluded from this L4 scope.** No requirement is imposed for multiple exchanges, independent market-data corroboration or independent market-data replicas. This exclusion does not remove independent evidence custody, independent offline verification or qualifying independent review.

This matrix is subordinate to P1.8.143 and P1.8.152 and cannot amend owner policy or grant operational authority. Where a conflict exists, the stricter protective rule applies and must be escalated.

### 1.1 Binding lifecycle decisions

- **RET-01 B:** T0 canonical data is protected by default. No routine, automatic or scheduled deletion. A narrowly scoped binding legal/security exception may only be considered through separate evidence, competent review and a new explicit owner decision. No exception is approved here.
- **RET-02 B:** only exact T4 rebuildable caches/read models/materializations, T2 ephemeral inference outputs, T1 raw observations meeting exact reproducibility and obligation-closure proof, and individually identified noncanonical copies may enter a future **read-only, exact-object/version eligibility assessment**. This does not make any object eligible by default and does not authorize mutation.
- T0 canonical data and its availability/recovery copies; CORE_LEDGER; AI_LEDGER; required T3 reconstruction/audit records; governance approvals, policy history, tombstones and lifecycle evidence; and unknown, unclassified, orphaned or incompletely inventoried data remain excluded from ordinary class-wide deletion review.
- RET-03 through RET-10 remain OPEN, NOT VERIFIED or otherwise as classified by P1.8.152. No numeric TTL, retention floor, grace period, review cadence, authorization lifetime or trusted-time freshness value is approved.
- **Option C — No Destructive Authority — remains in force.** Archive and irreversible lifecycle transitions are non-executable. No deletion, cleanup, compaction, vacuum, backup expiry, replica removal, export mutation or other destructive transition is authorized.
- Consumer ACK, successful use, inference completion, downstream consumption, dependency release or a computed retention floor is not deletion approval or execution authorization.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.

### 1.2 Evidence lifecycle principle

L4 evidence is itself governance/provenance evidence. Preserve original signed bytes, manifests, checkpoints, signer/trust-policy snapshots, verification outputs, review dispositions, lifecycle approvals, tombstones and lineage needed to establish claims and authority.

No L4 evidence object receives a default TTL or automatic self-deletion rule. No data is deleted merely because it has been read, verified, consumed, superseded, acknowledged or used to produce another artifact. Any future disposition must first pass the controlling lifecycle policy for the exact object/version/copy and remain separately subject to explicit owner authorization. This matrix authorizes no such disposition.

## 2. Acceptance matrix

| ID | Requirement | Positive evidence required | Negative/adversarial cases | PASS condition |
|---|---|---|---|---|
| L4M-01 | Owner-controlled evidence custody | Complete package inventory and SHA-256 manifest; at least one owner-controlled copy outside both T0/VPS and GitHub failure domains; custody/location and readback procedure. The separately authenticated latest-head/monotonic anchor required by L4M-03 is part of this custody package and must be retained/readable outside both failure domains. | T0/VPS unavailable; GitHub unavailable; both unavailable; latest-head anchor missing, stale, rolled back or inaccessible under either outage; copy missing, truncated or corrupted | Owner locates and integrity-checks the retained evidence copy and latest-head anchor without T0/VPS or GitHub. Both must remain independently readable and integrity-checkable during either failure-domain outage; the GitHub-unavailable readback is part of this control's PASS, not an optional G2 note |
| L4M-02 | Signing authority separated from T0 | Signer identity, key custody, authorization boundary and recovery procedure; evidence signer is not an ordinary T0 runtime/admin credential | T0 compromise; signer unavailable; unauthorized signing request; key loss or substitution | T0 process/admin credentials alone cannot create an accepted owner signature; recovery path is documented and verified only in a separately authorized isolated test |
| L4M-03 | Exact-object binding and freshness | Signed envelope binds exact checkpoint bytes/digest, schema/version, dataset identity, sequence/generation and context; separately authenticated owner-controlled latest-head/monotonic reference for any freshness claim. The anchor is an exact evidence object included in the L4M-01 custody inventory and retained outside both T0/VPS and GitHub failure domains | Single-byte mutation; payload/signature swap; dataset substitution; replay of older valid checkpoint; missing, stale, substituted or rolled-back latest-head anchor; anchor unavailable when T0/VPS or GitHub is unavailable | Exact object verifies; mutations/substitutions fail. Freshness/rollback is assessed against the separately authenticated latest-head anchor, whose exact digest and custody/readback are verified independently of T0/VPS and GitHub. If the anchor is absent, stale, rolled back, inaccessible or unverifiable, freshness is UNKNOWN/NOT VERIFIED; sequence/generation alone cannot establish freshness |
| L4M-04 | Independent offline verification | Verifier on a separate environment; pinned trust-policy snapshot; no ChatGPT, producer runtime or live network/TSA dependency for offline cryptographic verification | ChatGPT/producer/network unavailable; unknown root; malformed package; verifier crash; incomplete policy snapshot | Owner verifies the exact package offline; incomplete or ambiguous inputs fail closed. Historical time claims are limited by L4M-06 |
| L4M-05 | Independent readback/recovery | Readback of retained evidence copy from owner-controlled custody; inventory/manifest/signatures rechecked; non-destructive recovery procedure and exact scope | Missing/truncated/corrupted/stale copy; partial readback; unavailable custody location; restore would overwrite an existing source | Missing/corrupt evidence is detected and result is either a fully verifiable readback or explicit failure. No restore-overwrite, production restore or destructive recovery test is implied or authorized |
| L4M-06 | Key and trust lifecycle | Versioned trust policy; owner approval records for trust-root/key changes; rotation/revocation evidence; distinct fields for signature validity, current trust and historical trust-at-time | Unknown/revoked key; substituted root; policy rollback; absent or conflicting revocation evidence; no qualifying trusted-time proof | Verifier distinguishes cryptographic signature validity, current trust state and historical trust-at-time. Without sufficient time and revocation evidence, historical status is UNKNOWN/NOT ESTABLISHED. No historical validity is inferred from signature validity, local clock or current trust. TSA is not mandatory solely to satisfy L4-Minimum |
| L4M-07 | Tamper-evident append-only evidence history | Original bytes, timestamp intents/attempts, tokens if present, verifier outputs, revocation evidence, policy versions and manifests linked by canonical identities/digests; owner-controlled independent retained manifest/copy | Retry after timeout; duplicate attempt; late token; conflicting verification; record overwrite; deletion; wholesale history replacement; storage-admin rewrite | Earlier records remain addressable and tampering/replacement is detectable against independently retained evidence. Claim is **tamper-evident**, not absolute immutability or WORM, unless a separately qualified immutable medium is actually evidenced. Storage-administrator trust assumptions are stated |
| L4M-08 | Claim discipline | Each provenance statement identifies exact object, verification performed, time basis, trust assumptions and limits | Valid signature but false market data; incomplete source coverage; timestamp without durable-commit proof; consumer ACK misrepresented as lifecycle release | No inference of market-data truth, exchange completeness, DB durability, strategy correctness, obligation closure or deletion eligibility from a signature, timestamp, ACK or successful use alone |
| L4M-09 | Qualifying independent review | Reviewer identity; relevant competence and specialist boundaries; independence from requester, custodian, obligation owner, approver, executor, provider selector and evidence producer; conflict assessment; exact artifact hashes, methods, scope and limitations | Same producer issues acceptance; conflicted preliminary reviewer presented as independent; reviewer lacks artifacts/competence; scope silently expands | A qualifying independent reviewer directly examines exact immutable artifacts and underlying evidence and alone issues the independent disposition. A conflicted contributor may provide factual input/preliminary analysis only, labelled non-independent and non-authoritative. If no qualifying reviewer exists, control remains PENDING/BLOCKED |
| L4M-10 | Fail-closed per-control and aggregate acceptance | Machine-readable and human-readable per-control verdicts; evidence references; explicit aggregation rule and exact baseline identity | Missing evidence/custody; unknown trust state; verifier crash; unavailable dependency; mismatched digest; unresolved mandatory control; reviewer pending | Before independent review, freeze and identify the evidence baseline (canonical manifest plus SHA-256 and immutable baseline ID). The reviewer examines that frozen baseline and issues a separate review-disposition record that references the exact baseline ID and digest; the disposition is not inserted into or used to mutate the frozen baseline. Aggregate verdict binds both the frozen baseline and its separately retained review disposition. Overall L4 PASS only when **all mandatory L4M-01–L4M-10 are PASS for the same frozen immutable evidence baseline**, and the qualifying review disposition explicitly references that baseline digest. Known unsafe/unavailable prerequisite => BLOCKED. Missing, incomplete or unreviewed proof => NOT VERIFIED/PENDING. UNKNOWN never becomes PASS. A technical PASS cannot override failed custody or pending independent review |

## 3. Required test groups

These are acceptance requirements, not authorization to execute tests.

### G1 — Integrity, exact binding and freshness
- Valid exact package verifies.
- Single-byte mutation and signature/payload swap fail.
- Dataset identity, schema, sequence or generation substitution fails.
- Older valid checkpoint is compared with an authenticated owner-controlled latest-head anchor.
- Verify the anchor itself against its exact digest and owner-controlled custody copy while T0/VPS is unavailable, while GitHub is unavailable, and while both are unavailable.
- If the anchor is absent, stale, rolled back, inaccessible or unverifiable, freshness is UNKNOWN/NOT VERIFIED, not inferred from sequence alone.

### G2 — Evidence custody and availability
- Evidence readback works with T0/VPS unavailable.
- Evidence readback works with GitHub unavailable.
- Evidence readback works when both T0/VPS and GitHub are unavailable.
- At least one owner-controlled copy outside both failure domains can be integrity-checked.
- The latest-head/monotonic anchor is included in that independently retained custody package and can be read and integrity-checked during T0/VPS outage, GitHub outage, and simultaneous outage.
- Missing/corrupt/partial copies or anchor unavailability are detected; no silent success.
- This tests assurance-evidence custody only; it does not require independent market-data sources.

### G3 — Signer and trust lifecycle
- T0 runtime credentials cannot impersonate the owner-controlled signer.
- Unknown/substituted trust roots fail closed.
- Rotation preserves historical verification under an explicit policy.
- Current trust and historical trust-at-time are separate.
- Missing trusted-time or revocation proof produces UNKNOWN/NOT ESTABLISHED for historical status.
- TSA integration is not a mandatory L4-Minimum prerequisite.

### G4 — Tamper-evident history and uncertainty
- Timeout is recorded as UNKNOWN, not success or definitive failure.
- Retry creates a distinct attempt and preserves original records.
- Late-arriving proof is linked to the exact request/checkpoint.
- Conflicting/incomplete verification records remain visible.
- Original bytes remain unchanged; independent manifest/copy detects tampering or wholesale replacement.
- No claim of WORM/absolute immutability without separately qualified evidence.

### G5 — Claim boundaries
- A valid signature is not proof of market-data truth.
- A timestamp is not proof of DB/WAL durability unless the exact durable boundary is independently evidenced.
- Successful verification is not proof of source completeness, exchange truth, trading performance, retention-floor completion or deletion eligibility.
- Consumer ACK/use completion does not grant disposition authority.

### G6 — Lifecycle and no-destructive-authority boundary
- L4 evidence, governance records and T0 canonical data remain protected; no default TTL or self-deletion.
- T0 canonical data and T0 availability/recovery copies are not admitted to ordinary deletion-eligibility review.
- RET-02 permits only future read-only exact-object/version assessment for its enumerated noncanonical classes/copies, with all class-specific proof.
- Unknown/unclassified/orphaned/incompletely inventoried objects, active holds, unresolved dependencies, recovery chains or uncertain copy lineage yield RETAIN / BLOCKED.
- A retention floor, when eventually established for an exact object, is not deletion approval.
- No automatic cascade, archive, cleanup, vacuum, compaction, backup expiry, replica removal or deletion occurs under this matrix.
- Option C remains effective; any future lifecycle mutation requires a separate owner decision and separately approved authority.

## 4. Evidence package minimum

For each authorized acceptance run, retain:
1. immutable test input package and SHA-256;
2. exact verifier source/build identity and SHA-256;
3. trust-policy snapshot and root fingerprints;
4. test case ID, expected result and observed result;
5. verifier output and exit status;
6. environment identity and network/availability conditions;
7. owner-custody location reference and readback result, without exposing secrets;
8. reviewer identity, competence, conflict/independence assessment and exact reviewed artifact hashes;
9. per-control and aggregate PASS/BLOCKED/NOT VERIFIED disposition with unresolved limitations;
10. frozen baseline ID, canonical manifest digest and freeze/closure record;
11. separate reviewer disposition record referencing the exact frozen baseline ID and digest, retained as a linked evidence object without modifying the baseline;
12. review-input lineage manifest that records the exact SHA-256 of the current Acceptance Matrix and every supporting historical audit/decision artifact. The 2026-11-10 read-only audit report (blob `cfecb7428508adf23e6b9e71dc0dfe1e0e38080c`) records the then-current matrix blob `f39bef0c391e13a3656130f0e74f0e7a385b0c39`; that reference is historical and must not be mistaken for the current matrix (`8f9e34acb4e9ae0b89d5e7163566ab2982d99c63`). Preserve the audit report unchanged; reviewer must examine both exact artifacts and explicitly reconcile their version lineage.

Do not include private signing keys or secrets. Record key fingerprints and custody references only.

Evidence package retention is governed by the applicable lifecycle obligations and owner policy. No numeric retention duration is set here. Evidence needed to prove provenance, trust, authority, lifecycle decisions or prior outcomes remains protected while those obligations remain active or unknown.

## 5. Required state semantics

- **PASS:** all required evidence for the exact claim is present, integrity-checked and independently verified.
- **BLOCKED:** a required prerequisite is known to be unavailable, unsafe, prohibited or unresolved.
- **NOT VERIFIED:** evidence is absent, incomplete, stale or has not been independently checked.
- **PENDING:** a required qualifying independent review or owner decision has not occurred.
- **UNKNOWN:** an operation's outcome or relevant state cannot be established; UNKNOWN is protective and must never be coerced to PASS or to an obligation end.
- **FLOOR_NOT_ESTABLISHED / RETAIN / BLOCKED:** applicable obligation inventory/end conditions/copy lineage/time ordering are incomplete or uncertain under P1.8.144.
- A document-only/static-review PASS applies only to the exact reviewed document and scope.
- Freeze and identify the evidence baseline before independent review; record its canonical manifest digest and closure record.
- The independent reviewer issues a separate disposition referencing that exact baseline ID/digest. The disposition is linked evidence, not a mutation or append operation inside the frozen baseline.
- **Overall L4 PASS** requires every mandatory control L4M-01–L4M-10 to be PASS on the same frozen immutable evidence baseline and a qualifying review disposition that names its exact digest. No averaging, majority or compensating control is allowed.

## 6. Execution sequencing and authorization gates

1. Reconcile remaining P1.8.152 lifecycle/reviewer findings; do not infer that this matrix closes them.
2. Treat the 2026-11-10 read-only audit report as a historical snapshot: it references the pre-F-01–F-08 matrix blob `f39bef0c391e13a3656130f0e74f0e7a385b0c39`. Do not rewrite that report or treat its matrix reference as current.
3. Freeze and identify the exact review-input baseline (current matrix blob `8f9e34acb4e9ae0b89d5e7163566ab2982d99c63`, audit report blob `cfecb7428508adf23e6b9e71dc0dfe1e0e38080c`, and applicable controlling decision/lifecycle artifacts) in a canonical manifest with digest and closure record.
4. Obtain independent review of the current matrix and all exact frozen review inputs, explicitly reconciling historical-to-current matrix lineage; require a separate disposition that references the exact baseline ID/digest.
3. Inventory existing evidence and implementation only within separately approved, non-operational scope.
4. Design isolated synthetic fixtures and expected outputs.
5. Obtain explicit owner approval for any activity touching keys, trust roots, GitHub permissions, persistent storage, VPS, database, runtime inventories, providers, staging, restore or fault injection.
6. Run only the explicitly approved test scope; preserve exact source SHA, workflow run and artifact where applicable.
7. Obtain qualifying independent review before changing any acceptance status.

This document does not authorize any step that crosses an existing authorization boundary. It does not authorize key operations, permission inventory, provider calls, runtime/data/copy inventory, staging, restore, fault injection, workflow dispatch, implementation, archive or destructive operations.

## 7. Lifecycle crosswalk and outstanding gates

| Lifecycle control | Effect on L4-Minimum | Current status from P1.8.152 |
|---|---|---|
| RET-01 B — T0 protection | T0 canonical data and availability/recovery copies remain protected; no routine/automatic deletion path | OWNER-RATIFIED — POLICY ONLY |
| RET-02 B — limited noncanonical review | Only exact eligible classes/copies may enter future read-only assessment; no default eligibility or mutation authority | OWNER-RATIFIED — ASSESSMENT SCOPE ONLY |
| RET-03 — numeric retention floors | No TTL/floor may be invented; no object floor established by this matrix | OPEN |
| RET-04 — archive | Archive remains non-executable under Option C | NON-EXECUTABLE |
| RET-05 — approval/authority separation | No actor/adapter/verifier receives destructive authority; technical enforcement not proven | POLICY APPROVED / ENFORCEMENT NOT VERIFIED |
| RET-06 — grace, authorization lifetime, freshness | No values selected; do not infer time windows | OPEN |
| RET-07 — tombstone/audit/evidence retention | Preserve governance/evidence needed to prove authority, lineage and outcomes; no expiry rule set | OPEN |
| RET-08 — emergency/legal requests | RET-01 exception is not pre-approved; requires exact-scope evidence, competent review and new explicit owner decision | OPEN |
| RET-09 — runtime consumer/copy/restore inventory | Completeness not established; unknown copies/dependencies remain protected | NOT VERIFIED |
| RET-10 — adapter/verifier requirements | No adapter qualified; no lifecycle mutation path accepted | OPEN / NOT VERIFIED |
| V07 — trusted time/revocation | Historical trust-at-time may remain UNKNOWN; no TSA requirement added by this matrix | BLOCKED |
| V08 — durable checkpoint/seal ordering | No durable commit/seal claim without exact proof | OPEN / BLOCKED |
| Restore | No measured provider/database recovery guarantee; no restore-overwrite authorized | OPEN / BLOCKED |
| Mutation fence / Option C enforcement | No technical destructive authority assumed | NOT VERIFIED |

P1.8.153 remains the next documented lifecycle gate in the handoff. This L4 matrix does not replace, close or retarget it. The unresolved P1.8.152 reviewer-control finding remains open until a qualifying independent review explicitly closes it.

## 8. Current verdict

- Matrix revision: DOCUMENTATION UPDATE — F-01 THROUGH F-08 ADDRESSED IN WORDING; NOT INDEPENDENTLY REVIEWED.
- Lifecycle alignment: DOCUMENTARY CROSSWALK ADDED; P1.8.152 residual findings remain open.
- Requirements implemented: NOT VERIFIED.
- Test fixtures created/executed: NOT RUN / NOT CREATED BY THIS RECORD.
- GitHub Actions: NOT DISPATCHED.
- Qualifying independent review of this revised matrix: PENDING.
- L4 implementation/operational acceptance: BLOCKED / NOT VERIFIED.
- Destructive authority: NOT GRANTED; Option C remains in force.

No code, schema, API, workflow, runtime, VPS, database, T0/T1/T2/T3/T4, feeder, ledger, strategy, risk, key, trust-root, permission, provider, inventory, test, archive or destructive operation is authorized or performed by this revision.
