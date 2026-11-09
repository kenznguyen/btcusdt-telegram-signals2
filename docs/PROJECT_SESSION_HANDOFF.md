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

## Latest completed work — P1.8.31

- Added documentation-only acceptance contract: `docs/evidence/p1-8/P1.8.31-acceptance-contract-update.md`.
- Document commit: `b11637060fff5d6bfd6c1eaf4a05150d7baf2e56`.
- Converts P1.8.30 C–C–B policy direction into frozen-manifest requirements, scenario denominator rules, observer-principal independence, D0–D4 claim boundaries, durable-ACK scope, V07 revocation fixtures/gates, V08 checkpoint fixtures/gates, restore measurement contract, V01–V13 acceptance index, evidence provenance and stop conditions.
- Unresolved values are intentionally not invented: V07 BLOCKED on timestamp authority/cache/propagation/rotation/quarantine parameters; V08 BLOCKED on watermark/lateness/boundary/clock/correction parameters; restore acceptance BLOCKED on failure-domain, RPO/RTO measurement and rehearsal-independence contract.
- Status: DOCUMENTATION COMPLETE; STATIC REVIEW REQUIRED; NOT EXECUTED. Prior vectors V01–V06 and V09–V13 remain SYNTHETIC PASS only; V07/V08 remain BLOCKED pending parameters; staging NOT AUTHORIZED; production NOT VERIFIED.
- No source/runtime changes, staging provisioning, provider selection, key operations, restore/fault injection, workflow dispatch, PR, or merge. No CI run or artifact is claimed.
- Next step: independent static consistency review of P1.8.31 against P1.8.26–P1.8.30; then report findings before proposing any separately authorized staging work.

## Latest completed work — P1.8.31 / P1.8.32

- P1.8.31 acceptance contract: `docs/evidence/p1-8/P1.8.31-acceptance-contract-update.md`.
- P1.8.31 initial commit: `b11637060fff5d6bfd6c1eaf4a05150d7baf2e56`; subsequent documented refinements aligned D0–D4 to P1.8.28, strengthened independent-principal and environment-equivalence requirements, mapped F01–F10, and normalized sections.
- Final reviewed P1.8.31 blob SHA: `bc124a346eac9d8239d2dc6b8d44fd86a96c072c`.
- P1.8.32 independent static review: `docs/evidence/p1-8/P1.8.32-independent-static-review.md`.
- P1.8.32 final document commit: `d8cbf9d7de43ea85d96101ce5aac66048f4c16c0`; blob SHA: `ad9ed529342e3694a376f9c158a5d8f392523cd4`.
- Static review: PASS for V01–V13 catalog traceability, F01–F10 mapping, C–C–B policy binding, D0–D4 alignment, RPO/RTO planning values, V07/V08 timestamp contracts, observer independence, claim-scoped environment matrix, section structure and authorization boundaries.
- Review caught and corrected the first P1.8.31 D0–D4 table so definitions exactly match P1.8.28: D0 application/process termination; D1 database process restart; D2 host restart; D3 storage/provider interruption; D4 power loss/device failure/filesystem corruption.
- Residual gates remain: V07 BLOCKED on exact revocation parameters; V08 BLOCKED on exact watermark/boundary parameters; restore acceptance BLOCKED on measurement contract and separate staging authorization; environment equivalence NOT VERIFIED; D3/D4 NOT TESTED.
- Status: P1.8.31 STRUCTURAL/TRACEABILITY REVIEW PASS; execution readiness NOT ESTABLISHED. Staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED. Prior vectors remain SYNTHETIC PASS only.
- No source/runtime changes, staging provisioning, provider selection, key operations, restore/fault injection, workflow dispatch, PR or merge. No CI run or artifact is claimed.
- Next step: prepare an owner-review package for unresolved V07, V08 and restore parameters; no staging action until values are frozen and separately authorized.
