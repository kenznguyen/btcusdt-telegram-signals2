# Project Session Handoff

Updated: 2026-11-09 UTC  
Active branch: \`feature/t0-centralized-data-feeder-p1-20261101\`

## Latest completed work — P1.8.22 / P1.8.23

- P1.8.22: existing synthetic Ed25519 verifier and negative tests were audited; no duplicate signing helper was retained.
- P1.8.23: added a file-backed synthetic SQLite test for duplicate observer ACK, process death after durable checkpoint write/before checkpoint ACK, reopen, duplicate ACK replay, and idempotent checkpoint ACK recovery.
- Final source SHA tested by CI: \`082cc68b14148829c01fc63558f6781fa006756b\`.
- GitHub Actions run: [42557957929](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42557957929), SUCCESS, 3/3 jobs PASS, 162/162 tests PASS.
- Primary artifact: \`13648297207\`; independent verification artifact: \`13648187759\`; both expire \`2026-11-16T03:43:37Z\`.
- Attested bundle SHA-256: \`283f807f92850893b7cb0aa180b84c1c7673590f754837d94258c0559984143b\`.
- Evidence record: \`docs/evidence/p1-8/082cc68b14148829c01fc63558f6781fa006756b/P1.8.23.md\`.
- Workflow archive commit: \`50f06a49ea391674b31cc561ade0b00363bd8a89\`.
- Evidence record commit: \`90409fc1e0bb30ad4aceea31c8b58c5eec991f01\`.

## Fault-vector status

All 13 catalogued fault/negative vectors now have executable synthetic test coverage: 13/13 PASS, 0 PARTIAL, 0 MISSING. This includes invalid signature, unknown signing key, revoked signing key, checkpoint boundary, recovery, and Root B duplicate ACK/crash.

Production evidence remains NOT VERIFIED for all 13 vectors. The file-backed SQLite adapter is a synthetic reference model only; no production Root B, key-management, database, feeder, exchange, ledger, strategy, or runtime integration has been performed.

## Operating boundaries

- \`AI_EXECUTION_ENABLED=false\`; no live orders.
- Do not modify T0/T1, VPS, DB, Feeder, production runtime, exchange, ledger, strategy, or risk engine without separate explicit approval.
- No PR or merge was created.
- Continue to use GitHub Actions for validation and retain evidence on the existing branch.
- Any future production integration or change to assurance claims requires separate explicit approval.

## Latest completed work — P1.8.26

- Designed an isolated staging Production Verification Protocol for all 13 fault/negative vectors.
- Protocol: `docs/evidence/p1-8/P1.8.26-production-verification-protocol.md`.
- Scope includes prerequisites, per-vector procedure and PASS criteria, durability/storage, concurrency, key lifecycle, business-state reconciliation, evidence package contract, stop gates, and explicit prohibitions.
- Protocol document commit: `3910544269aa2b759df28183efcbde491fe64d70`; final handoff commit / branch HEAD: recorded by the commit that updates this handoff.
- Protocol blob SHA: `863707a63f21327b83f5ee1511b72eae871623de`.
- GitHub check-runs queried for protocol commit: 0; commit status: pending with no status contexts. No workflow run or artifact is claimed for P1.8.26.
- Status: DESIGN COMPLETE; NOT EXECUTED. All 13 vectors remain synthetic PASS / production NOT VERIFIED.
- No production implementation, runtime integration, destructive fault injection, VPS/T0/T1/DB/Feeder/exchange/strategy/ledger/risk changes, PR, or merge.
- Next step: independent review of protocol completeness and environment equivalence criteria before separately approving any isolated staging execution.

## Latest completed work — P1.8.28

- Added `docs/evidence/p1-8/P1.8.28-verification-criteria-environment-equivalence.md`.
- Document commit: `d14b512e6f8b146dabf0fbb08fe0462610df674a`.
- Defined a production/staging environment equivalence matrix covering application, database, transactions, durability, storage, topology, concurrency, identity/key management, time, network, backup/restore, observability, and CI evidence.
- Added measurable minimum deterministic coverage for V01–V13, separate D0–D4 durability claim levels, explicit revocation and checkpoint timestamp contracts, reconciliation fixture requirements, and provisional staging RPO/RTO targets requiring owner approval.
- Added pre-execution/abort checklist and evidence manifest extensions.
- Status: DESIGN COMPLETE; NOT EXECUTED. Environment equivalence NOT VERIFIED; staging BLOCKED / NOT AUTHORIZED; production NOT VERIFIED.
- No source/runtime changes, staging provisioning, fault injection, workflow dispatch, PR, or merge. No CI run or artifact is claimed.
- Next step: independent review of P1.8.28; obtain explicit owner decisions for revocation policy, checkpoint membership policy, and proposed RPO/RTO before any staging execution proposal.

## Latest completed work — P1.8.29

- Completed independent static review of P1.8.26 and P1.8.28; recorded findings F01–F10 and owner decision register DEC-01/02/03.
- Review document: `docs/evidence/p1-8/P1.8.29-independent-review-policy-decision-register.md`.
- Document commit: `ad0fa98728520a6088733d08d28beaefb0205d1a`.
- Findings cover replay denominator/scenario breadth, observer principal independence, D0–D4 claim separation, durable-ACK/RPO scope, unresolved revocation and checkpoint policies, provisional RPO/RTO, claim-scoped environment equivalence, frozen deterministic test plans, and independent evidence provenance.
- DEC-01 signing-key revocation semantics: OPEN; V07 execution BLOCKED.
- DEC-02 checkpoint membership semantics: OPEN; V08 execution BLOCKED.
- DEC-03 restore RPO/RTO targets and failure domain: OPEN; restore acceptance BLOCKED.
- Status: STATIC REVIEW COMPLETE; POLICY DECISIONS OPEN; NOT EXECUTED. Staging NOT AUTHORIZED; production NOT VERIFIED.
- No source/runtime changes, staging provisioning, fault injection, workflow dispatch, PR, or merge. No CI run or artifact is claimed.
- Next step: obtain owner decisions for DEC-01/02/03; then create a versioned policy baseline and re-review affected criteria before proposing isolated staging execution.

## Latest completed work — P1.8.30

- Recorded explicit owner-approved policy direction C–C–B in `docs/evidence/p1-8/P1.8.30-approved-policy-baseline.md`.
- Policy baseline version: P1.8.30-v1.
- Document commit: `585502f233924fdea70e6ebffb8755da61341306`.
- DEC-01 option C approved: quarantine/fail-closed when key validity or revocation state cannot be proven. Exact timestamp authority, cache age, propagation, rotation overlap and quarantine release parameters remain unspecified; V07 BLOCKED.
- DEC-02 option C approved: hybrid event-time + watermark + durable commit-time gate, immutable sealed checkpoints and explicit late-event/correction path. Exact watermark, allowed-lateness, equality and clock parameters remain unspecified; V08 BLOCKED.
- DEC-03 option B approved: retain acknowledged-transaction RPO 0, snapshot RPO ≤5 minutes, staging RTO ≤60 minutes and 3 independent restores as planning targets only, not approved SLOs or measured capability. Restore acceptance BLOCKED pending measurement contract and separate staging authorization.
- Status: OWNER DECISIONS APPROVED; DESIGN BASELINE RECORDED; NOT EXECUTED. 13/13 vectors remain synthetic PASS only; staging NOT AUTHORIZED; production NOT VERIFIED.
- No source/runtime changes, staging provisioning, provider selection, key operations, restore/fault injection, workflow dispatch, PR, or merge. No CI run or artifact is claimed.
- Next step: P1.8.31 documentation-only acceptance-contract update; fill exact test-contract fields and unresolved parameter gates without inventing numerical values, then static review.
