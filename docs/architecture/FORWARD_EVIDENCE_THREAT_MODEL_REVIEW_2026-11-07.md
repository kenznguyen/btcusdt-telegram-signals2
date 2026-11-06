# Forward Evidence Capture — Threat Model Review (2026-11-07)

## Status

**DESIGN REVIEW — DOCUMENTATION ONLY; NO SOURCE, SCHEMA, STORAGE, WORKFLOW, OR RUNTIME AUTHORIZATION.**

This review assesses the proposed Root A execution journal and Root B independent observer/checkpoint protocol. It does not select a provider, authorize provisioning, open a persistent account database, import historical records, or activate evidence capture.

Current operational constraints remain unchanged:
- Paper Trading only; `ai_execution_enabled=false`.
- No exchange connectivity, real orders, or profitability claims.
- T0 remains paused/out of scope.
- Historical independent evidence remains unavailable; Option A strict predecessor chain remains current policy.
- A prospective evidence system cannot retroactively prove missing historical records.

## 1. System boundary and assets

### 1.1 In-scope components

- Paper strategy/intent producer (Core and AI).
- Shared Account Risk Engine and Kill Switch.
- Paper order/fill simulator and ledger state transitions.
- Root A append-only event journal.
- Root B independent observer, reducer, projection, and checkpoint.
- Evidence manifests, hashes/signatures, storage retention controls, and audit trail.
- Recovery/replay tooling and read-only evidence health reporting.
- GitHub source and GitHub Actions as software provenance/CI only, not account-event storage.

### 1.2 Assets requiring protection

| Asset | Integrity requirement | Confidentiality/availability requirement |
|---|---|---|
| Event envelopes and sequence | No silent edit, deletion, reordering, or substitution | Restricted access; durable availability |
| Fills, positions, orders, reservations | Exact ownership and economic ordering | Restricted account visibility |
| Fees and funding | Explicit source, amount, currency, time, coverage | Restricted account visibility |
| Marks and precision metadata | Source/time/version bound; no fabricated boundary mark | Available for replay |
| Root A segments | Append-only, hash-linked, byte-verifiable | Recoverable |
| Root B checkpoints | Separate provenance and reducer; immutable | Recoverable |
| Manifests and verification reports | Bind exact bytes, source SHA, config and coverage | Auditable |
| Signing/encryption keys | Protected from writer/observer compromise | Recoverable through controlled rotation |
| Risk readiness and Kill Switch state | Fail closed; no false-ready state | Available for safe reductions/closures |
| Software/configuration provenance | Exact immutable version/digest | Reproducible |

### 1.3 Trust boundaries

1. Strategy/AI producer to Shared Risk Engine.
2. Risk Engine/order simulator to ledger transition and event journal.
3. Root A writer to Root A storage.
4. Root A event delivery to Root B observer.
5. Root B observer to its separate storage.
6. Evidence storage to read-only verifier/recovery process.
7. Operator/admin identities to storage, keys, source control, and CI.
8. Clock/time source to event timestamps and UTC boundary logic.

Root A and Root B are separate retention/computation paths but may share the same upstream event emitter and host/operator control plane. This is a declared common-mode trust limitation. Do not label LEVEL 1 independent retention as independent economic-source verification.

## 2. Threat severity and response model

Severity:
- **CRITICAL:** can fabricate or silently alter economic history, falsely authorize risk readiness, or defeat both evidence roots.
- **HIGH:** can destroy availability/coverage or create ambiguous state requiring a hard block.
- **MEDIUM:** can expose restricted data or impair operations without directly changing verified economic state.
- **LOW:** limited impact with existing controls.

Response states:
- **BLOCK INCREASES:** no new exposure; preserve existing risk-reduction/closure allowance.
- **NOT VERIFIED:** evidence cannot support a reconstruction claim.
- **INCIDENT:** preserve all available evidence, stop automated repair, require reviewed recovery.
- Never convert an unknown, missing, or failed verification result to zero, empty-success, or PASS.

## 3. Threat register

| ID | Threat / failure mode | Severity | Required controls | Residual limitation |
|---|---|---:|---|---|
| T01 | Compromised or defective event emitter creates false fills/fees/funding before either root receives them | CRITICAL | Risk decision and simulator transition provenance; independent reducer; immutable producer/build/config identity; explicit paper-simulator semantics | Root A and B share the upstream emitter; LEVEL 1 cannot prove the event was economically true |
| T02 | Writer or host edits/deletes Root A before sealing | CRITICAL | Append-only API; separate storage identity; retention lock; hash chain; independent Root B receipt/checkpoint; read-back verification | Compromised admin/provider control plane may still affect both roots |
| T03 | Same operator/admin credentials control both roots | CRITICAL | Separate identities, credentials, access domains and audit; prohibit shared write credential; independent administrative review | Single owner may retain ultimate account/provider recovery authority |
| T04 | Root B reads mutable account DB instead of committed event stream | CRITICAL | Architectural prohibition; observer input contract only accepts committed envelopes/immutable segment refs; tests prove no DB dependency | Implementation review is required to verify the boundary |
| T05 | SHA-256 digest is treated as proof of authenticity | CRITICAL | Distinguish integrity from authenticity; sign sealed manifests using a separately controlled signing identity; verify key ID, signature, rotation and revocation history | Signature proves control of a key, not truth of source events; key compromise remains |
| T06 | Signing key or encryption key compromised/lost | CRITICAL | KMS/HSM-backed or equivalent controlled key custody subject to provider review; least privilege; rotation; recovery; key-use audit; no private keys in repo/CI | Provider/admin and recovery process remain trust dependencies |
| T07 | Sequence gap, duplicate sequence, replay, or reordering | HIGH | Monotonic account sequence; stable event ID; previous hash; deterministic tie-break; contiguous watermark; idempotent consumer | Ambiguous upstream ordering cannot be repaired by guessing |
| T08 | Event ID reused with different payload | CRITICAL | Unique ID constraint; payload hash binding; reject conflict and preserve both received byte sets as incident evidence | Requires durable uniqueness scope and concurrency-safe writer |
| T09 | Crash between event journal and ledger state creates split-brain | CRITICAL | Transactional outbox or equivalent recoverable commit protocol; crash-point tests; exactly-once effect through idempotent replay | Exact atomicity design remains unresolved until API/implementation review |
| T10 | Observer crashes or acknowledges before durable checkpoint | HIGH | Atomic projection + watermark commit; at-least-once delivery; replay suffix; crash/restart tests | Storage durability guarantees must be measured and documented |
| T11 | Common bug in Root A and Root B reducer yields matching wrong output | CRITICAL | Separate implementation; independent test vectors; adversarial mutation tests; compare against independently specified invariants | Shared event schema/specification and emitter remain common-mode dependencies |
| T12 | Clock skew, rollback, or wrong UTC conversion changes event/boundary membership | HIGH | Store economic and recorded times; monotonic sequence; UTC normalization; clock-health telemetry; explicit boundary rule; late-event invalidation | Wall-clock time alone cannot order same-time events; source sequence remains necessary |
| T13 | Late event arrives after checkpoint or after a day boundary | HIGH | Preserve original checkpoint; append late-event marker; invalidate candidate; replay both paths and reseal a new manifest | A period cannot be certified while required late-event coverage is unresolved |
| T14 | Fee/funding/mark omitted or silently defaulted to zero | CRITICAL | Explicit coverage/status fields; unknown is not zero; source IDs and amounts; fail-closed completeness checks | Missing source data may make historical period permanently unverifiable |
| T15 | Wrong ledger owner or cross-ledger event attribution | CRITICAL | Immutable owner on event; ownership validation; Core/AI/Legacy reducer isolation; aggregate reconciliation | Unknown ownership remains LEGACY_UNATTRIBUTED and blocks increases |
| T16 | Storage outage, quota exhaustion, timeout, or network partition | HIGH | Durable acknowledgement; capacity alerts; bounded retries; no silent local-only success; block increases when required root unavailable | Availability depends on selected provider and connectivity |
| T17 | Retention policy expires/deletes evidence early | CRITICAL | Retention lock; explicit lifecycle policy; periodic policy audit; deletion approval separation; read-back sampling | Legal/provider exceptions and account-level administrator controls must be assessed |
| T18 | Ransomware or malicious bulk deletion | CRITICAL | Separate storage domains; immutable retention; isolated credentials; offline/exported recovery copy if approved; restore drills | A single provider/control plane may remain a common failure domain |
| T19 | Manifest or package truncation/substitution | HIGH | Component hashes + root digest; signed manifest; object version IDs; byte-for-byte read-back; record count/sequence coverage | Cryptography cannot detect omitted source events that were never captured |
| T20 | Compromised CI/source dependency publishes malicious writer or observer build | CRITICAL | Protected branch/review; exact source SHA; pinned dependencies; reproducible build where feasible; signed build provenance; CI isolation; no runtime secrets in CI | Source review and build attestation cannot prove absence of all defects |
| T21 | Operator repairs or backfills evidence by editing old bytes | CRITICAL | No in-place repair; append-only correction/supersession event; immutable original preserved; reviewed incident record | Corrections can make a period unavailable until complete replay |
| T22 | Unauthorized read leaks account/strategy information | MEDIUM | Least privilege; encryption; access audit; secret/data minimization; retention/deletion policy | Authorized operators and provider access remain privacy boundary |
| T23 | Recovery process skips unknown event type or schema version | CRITICAL | Strict schema allowlist; unknown version/type blocks; versioned canonicalization; migration compatibility tests | Forward compatibility requires deliberate version review |
| T24 | Health dashboard reports storage heartbeat as evidence PASS | HIGH | Separate storage availability, chain integrity, coverage completeness, and reconstruction readiness; exact blocking reason | UI/monitoring implementation must preserve semantic distinctions |
| T25 | Root A and Root B are both writable by the same application process | CRITICAL | Separate process/service identities; separate credentials; network and storage ACL isolation; negative permission tests | Shared host/root administrator can defeat process-level separation |
| T26 | Backup/restore returns internally consistent but stale data | HIGH | Checkpoint age/watermark checks; restore verification against latest sealed manifest; recovery point objective declared | Recent unsealed events may be lost during catastrophic outage |
| T27 | Decimal precision/rounding differs between writer and observer | HIGH | Canonical decimal strings; pinned precision metadata; explicit rounding mode; exact IDs/status and declared numeric tolerances | Undefined instrument precision blocks reconciliation |
| T28 | Event stream leaks secrets or sensitive data | HIGH | Typed allowlist payload; secret scanning; no credentials/private keys; minimize identifiers; encrypted storage | Schema drift may introduce sensitive fields unless reviewed |
| T29 | Malicious or mistaken admin changes retention/access policy | CRITICAL | Dual control for policy changes; append-only admin audit; alert on lock/ACL change; independent periodic review | Provider super-admin or account owner may have ultimate override |
| T30 | Root B lag is hidden and stale checkpoint presented as current | HIGH | Watermark age/lag metric; freshness threshold; block independent verification; explicit stale state | Thresholds require workload and recovery objectives before implementation |

## 4. Security properties and non-properties

### Required properties

- **Integrity:** retained bytes are hash-verifiable; sealed manifests are authenticated.
- **Append-only history:** corrections add records; they do not overwrite prior evidence.
- **Separation:** Root B does not share Root A's mutable DB, write credential, or reducer implementation.
- **Completeness visibility:** gaps, late events, unknown fees/funding, and stale marks remain explicit.
- **Determinism:** same valid evidence package, code version, config, precision, and ordering yields the same replay.
- **Fail-closed risk gate:** evidence uncertainty blocks exposure increases.
- **Recoverability:** sealed evidence can be restored and read-back verified.
- **Auditability:** source SHA, config digest, producer identity, storage object version, key ID, and verification result are retained.

### Explicit non-properties

- SHA-256 alone does not authenticate who produced an event.
- A digital signature does not prove the event is economically true.
- Root A/Root B agreement does not prove correctness if both consume a fabricated upstream event.
- Separate processes on one compromised host are not fully independent.
- Separate buckets under one administrator/provider are not fully independent failure domains.
- GitHub commit history and CI test artifacts are not a substitute for account evidence.
- A prospective archive cannot reconstruct pre-capture history.
- A paper simulator's fill evidence is not exchange execution evidence.

## 5. Mandatory fail-closed decision matrix

| Condition | Evidence status | Risk behavior |
|---|---|---|
| Root A unavailable before durable journal commit | NOT READY | Block increases; do not report committed transition |
| Root B unavailable or behind freshness threshold | NOT INDEPENDENTLY VERIFIED | Block increases under proposed policy; allow approved reductions/closures |
| Hash/signature/sequence conflict | INCIDENT / BLOCKED | Block increases; preserve evidence; no automatic repair |
| Unknown event type/schema | BLOCKED | Block increases |
| Missing fee/funding/mark coverage | NOT VERIFIED | Block any reconstruction/risk decision requiring that value |
| Late pre-boundary event | CANDIDATE INVALID | Replay and reseal; do not use old candidate |
| Key compromise or uncertain signing identity | INCIDENT / BLOCKED | Reject affected manifests pending reviewed key recovery |
| Storage retention lock absent/changed | NOT READY | Block evidence certification; block increases per approved risk policy |
| Root A/Root B mismatch | BLOCKED | Freeze certification; preserve both roots; investigate |
| Dashboard/monitor unavailable | UNKNOWN | Never infer PASS from missing health data |

This matrix is a proposed policy. Exact operational thresholds and whether Root B outage blocks all increases require explicit risk-policy approval before implementation.

## 6. Minimum security acceptance evidence

Before any persistent capture is approved, tests and operational evidence must demonstrate:

1. Root A writer cannot overwrite/delete sealed objects.
2. Root B identity cannot mutate Root A; Root A identity cannot mutate Root B.
3. No shared credential can write both roots.
4. Root B cannot access the mutable account DB or its WAL.
5. Manifest signature verification fails for altered bytes, wrong key ID, revoked key, or unsigned package.
6. Hash chain detects deletion, insertion, reordering, truncation, and payload mutation.
7. Same event ID with different bytes becomes a blocking incident.
8. Writer/outbox and observer crash matrices recover without loss or double application.
9. Storage quota, timeout, partition, retention-lock failure, and permission loss fail closed.
10. Clock rollback/skew, UTC boundary, late events, and same-time ordering are handled deterministically.
11. Unknown fee/funding/mark and unknown schema remain NOT VERIFIED.
12. Separate reducer catches injected calculation and ownership defects.
13. Restore drill verifies the latest sealed manifest and reports any missing unsealed suffix.
14. Admin ACL/retention/key changes produce independently retained audit evidence and alerts.
15. Exact source SHA, dependency versions, config digest, schema/canonicalization version, and test artifacts are recorded in GitHub Actions.
16. CI contains no persistent account data, credentials, or runtime storage write permission.

All tests must run in isolated disposable fixtures before any persistent account storage is touched. Test fixtures prove software behavior, not the existence or correctness of historical account data.

## 7. Open decisions — must not be guessed

| Decision | Current state | Required owner/approval |
|---|---|---|
| Storage provider and region | NOT SELECTED | User; security/cost review |
| Separate provider/account vs separate locked namespaces | NOT SELECTED | User; threat-model acceptance |
| Retention period and deletion/legal hold | NOT SELECTED | User; legal/provider terms review |
| Maximum acceptable Root B lag | NOT DEFINED | Risk-policy approval |
| Root A durability/acknowledgement SLA | NOT DEFINED | Data-integrity design approval |
| Root B outage behavior | Proposed block increases; NOT APPROVED | Risk-policy approval |
| Signing/key custody and recovery | NOT SELECTED | Security approval |
| Clock source and maximum skew | NOT DEFINED | Runtime reliability review |
| Backup/restore RPO and RTO | NOT DEFINED | Operations approval |
| Event payload privacy classification | NOT COMPLETED | Security/privacy review |
| Atomic outbox/journal architecture | NOT SELECTED | API/data-integrity design approval |
| Independent reducer implementation boundary | Proposed separate implementation | Architecture approval |

Do not select defaults by convenience or infer approval from a request to continue documentation.

## 8. Residual risk acceptance

Even after all proposed controls are implemented, LEVEL 1 remains vulnerable to common-mode errors in the event emitter, producer build, host administrator, shared operator, and event schema. The evidence system can prove what the paper system durably recorded and whether two retained computation paths agree; it cannot prove an external market execution that never occurred.

Any claim beyond this boundary requires a new source of evidence and a separate approval. Do not market or label the result as tamper-proof, exchange-verified, or historically reconstructed without the corresponding proof.

## 9. Current disposition

- Threat register: **DOCUMENTED**.
- Critical common-mode risks: **IDENTIFIED; NOT ELIMINATED**.
- Storage/provider and retention choices: **OPEN**.
- Key management/signature design: **OPEN**.
- Atomic writer/outbox design: **OPEN**.
- Security acceptance tests: **SPECIFIED; NOT RUN**.
- Source/schema/workflow/runtime: **UNCHANGED**.
- Persistent database/storage access: **NOT AUTHORIZED**.
- Historical Dual Reconstruction: **UNAVAILABLE / BLOCKED**.
- Current baseline policy: **Option A — strict predecessor chain**.
- T0: **PAUSED / OUT OF SCOPE**.
- Execution: **PAPER ONLY; ai_execution_enabled=false**.

Next gate is an explicit review of open security/storage decisions. This document does not authorize implementation or provisioning.
