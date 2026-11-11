# T0 L4-Minimum — Adversarial Static Review (2026-11-10)

Date: 2026-11-10
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Review type: Same-session adversarial static review; **NOT an independent third-party review**.
Status: PARTIAL — actionable matrix clarifications identified; independent review remains PENDING.

## 1. Exact review inputs

- Acceptance matrix: `docs/evidence/p1-8/L4-MINIMUM-PROVENANCE-ACCEPTANCE-MATRIX.md`
  - Blob SHA: `f39bef0c391e13a3656130f0e74f0e7a385b0c39`
- T0 audit report: `docs/evidence/T0_L4_MINIMUM_READ_ONLY_AUDIT_2026-11-10.md`
  - Blob SHA: `cfecb7428508adf23e6b9e71dc0dfe1e0e38080c`
  - Audit source ref recorded by that report: `cad0453a93f7092ca490a54dc09b7d84dae5d4d4`
- Owner scope decision: `docs/decisions/D-2026-11-09-L4-PROVENANCE-PERSONAL-SCOPE.md`
  - Blob SHA: `6b96c2c37a4989b7ceba291d027a3f8459eecb3b`
- Project handoff blob read: `753c071d608b3eed1122e48606d46e4c56cc266d`

The review is bounded to the exact documents above. It does not claim a complete re-audit of every historical P1.8 record or production implementation.

## 2. Governing scope interpretation

- L4-Minimum is for a single-owner, personal, non-commercial system.
- Exclude independence of **market-data sources**: no requirement for multiple exchanges, independent source corroboration, or independent market-data replicas.
- Retain independent evidence custody/readback and independent technical review. These concern assurance evidence and reviewer conflict, not market-data source independence.
- External TSA integration and dedicated WORM are not mandatory L4-Minimum controls.
- TSA-dependent historical-time claims must remain UNKNOWN/NOT ESTABLISHED when no qualifying time evidence exists.
- Option C — No Destructive Authority — remains in force. No deletion, archive, cleanup, retention reduction, key/trust-root operation, runtime/VPS/DB change, workflow dispatch or live order is authorized.
- `AI_EXECUTION_ENABLED=false`; paper-only.

## 3. Findings

### F-01 — Evidence custody does not bind all stated outage conditions to L4M-01
Severity: HIGH
Affected: L4M-01, G2, evidence package minimum.

L4M-01's positive requirement says the owner-controlled location must be outside T0/VPS. G2 separately asks verification to work when GitHub is unavailable. The PASS condition for L4M-01 does not explicitly require that the retained copy itself be independently accessible when both T0/VPS and GitHub are unavailable.

Required clarification:
- State explicitly that at least one owner-controlled evidence copy is outside the T0/VPS **and GitHub** failure domains.
- Bind the GitHub-unavailable readback test to the L4M-01 PASS condition.
- Define the minimum package inventory and SHA-256 manifest as part of that same proof.

This is evidence-custody availability, not independence of market-data sources.

### F-02 — Replay/freshness detection lacks an explicit latest-head trust anchor
Severity: HIGH
Affected: L4M-03, G1.

The matrix requires detection of an older valid checkpoint replay where freshness is claimed, but sequence/generation fields alone do not prove that the verifier knows the latest accepted checkpoint. An attacker able to present an internally valid older package may cause rollback unless the verifier has a separately retained, authenticated latest-head/monotonic reference.

Required clarification:
- Define the freshness claim separately from integrity verification.
- Identify the owner-controlled latest-head anchor and how it is retained/read independently.
- If no trustworthy latest-head anchor is available, report freshness/rollback status as UNKNOWN or NOT VERIFIED; do not reject/accept based only on a self-consistent sequence number.

No independent market-data feed is implied.

### F-03 — Historical trust state may imply a timestamp guarantee not required by L4-Minimum
Severity: HIGH
Affected: L4M-06, G3, P1.8.36/V07 boundary.

L4M-06 requires distinguishing valid-at-signing-time from currently trusted/revoked/unknown states. The audit says TSA integration is L4-Extended and V07 remains BLOCKED. Without a qualifying trusted-time assertion and sufficient historical revocation evidence, valid-at-signing-time cannot be established merely from a signature or local clock.

Required clarification:
- Make historical validity conditional on the exact available time and revocation evidence.
- Where evidence is absent, return UNKNOWN/NOT ESTABLISHED; never infer historical validity from current trust or signature validity alone.
- Keep current trust, historical trust-at-time, and cryptographic signature validity as separate result fields.
- Do not make TSA mandatory merely to close this wording gap.

### F-04 — “Append-only” is not yet distinguished from tamper-evident storage
Severity: HIGH
Affected: L4M-07, G4.

The matrix requires earlier records to remain addressable and unmodified, but does not state what detects privileged rewriting or replacement of the complete history. Dedicated WORM is out of scope, so the document must not imply WORM-grade immutability from process rules alone.

Required clarification:
- Define the minimum claim as tamper-evident append-only history, not absolute immutability, unless a separately verified immutable medium is actually used.
- Bind records through canonical identities/digests and a verifiable chain or equivalent mechanism.
- Retain an owner-controlled independent copy/manifest so wholesale history replacement can be detected.
- State the residual trust assumption for the storage administrator.

### F-05 — Independent reviewer qualification is underspecified
Severity: MEDIUM
Affected: L4M-09, evidence package minimum.

The matrix asks for reviewer identity and independence basis, but does not explicitly require evidence of relevant competence or a conflict-of-interest assessment. “Not the sole producer/authority” is directionally useful but can still admit a reviewer who cannot assess the cryptographic/storage subject.

Required clarification:
- Record reviewer identity, relevant technical competence, relationship to the evidence producer, conflict assessment, exact artifact hashes, methods, scope and limitations.
- Reviewer must not be the sole producer of the evidence or the sole authority approving the claim.
- If no qualifying reviewer is available, L4M-09 remains PENDING and overall L4 acceptance cannot be PASS.

### F-06 — Aggregate verdict precedence is not explicit
Severity: MEDIUM
Affected: L4M-10 and §5 state semantics.

The matrix defines PASS/BLOCKED/NOT VERIFIED/UNKNOWN, but does not state an unambiguous aggregation rule across all ten controls. A partial technical PASS must not override missing owner custody or pending independent review.

Required clarification:
- Overall L4-Minimum PASS requires every mandatory control L4M-01–L4M-10 to be PASS for the same immutable evidence baseline.
- Any known unsafe/unavailable prerequisite yields BLOCKED.
- Missing, incomplete or unreviewed evidence yields NOT VERIFIED or PENDING as applicable.
- UNKNOWN must never be coerced to PASS.
- Record both per-control status and overall status, with exact evidence references.

## 4. Cross-document consistency

1. The report correctly states that synthetic tests, documentation, Git history and Actions artifacts do not establish production L4 acceptance.
2. The report correctly keeps L4M-01/02 NOT VERIFIED; L4M-03/04/05/06/07/10 PARTIAL; L4M-08 documentary PASS; L4M-09 PENDING.
3. TSA and dedicated WORM are correctly described as non-mandatory L4-Extended capabilities. F-03 and F-04 clarify the claims that can be made without them; they do not add either technology as a requirement.
4. G2's independent evidence availability tests remain in scope even though independence of market-data sources is excluded.
5. P1.8.153 and V07/V08/Restore remain separate lifecycle gates; this review does not close or retarget them.
6. The audit's overall L4-Minimum technical/operational status remains BLOCKED / NOT VERIFIED.

## 5. Required correction order

1. Clarify L4M-01 outage-domain and readback acceptance.
2. Clarify L4M-03 freshness anchor and UNKNOWN behavior.
3. Clarify L4M-06 historical-time/revocation claim boundaries without making TSA mandatory.
4. Clarify L4M-07 tamper-evident versus immutable claims.
5. Strengthen L4M-09 reviewer qualification and conflict evidence.
6. Define L4M-10 aggregate verdict precedence.
7. Run a genuinely independent review of the corrected matrix and exact audit report.

## 6. Verdict and limits

- Adversarial static pass: COMPLETE for the six findings and cross-document checks listed above.
- Matrix readiness: PARTIAL — corrections required before it is a sufficiently precise acceptance baseline.
- Genuine independent review: PENDING. This same-session review does not satisfy L4M-09 or the requested independent-review gate.
- L4 implementation/operational acceptance: BLOCKED / NOT VERIFIED.
- Tests: NOT RUN; this was document-only static review.
- GitHub Actions: NOT DISPATCHED; no workflow run or artifact is claimed.
- No source, schema, API, workflow, runtime, VPS, database, feeder, key, trust-root, permission, data or trading changes.
- No archive, cleanup, vacuum, compaction, backup expiry, replica removal or deletion.

**Final status: SAME-SESSION ADVERSARIAL REVIEW COMPLETE — FINDINGS F-01–F-06 OPEN — GENUINE INDEPENDENT REVIEW PENDING — NO OPERATIONAL AUTHORITY.**


## Superseding owner governance decision — Option C revoked (2026-11-11)

The owner revoked **Option C — No Destructive Authority** on 2026-11-11. Any earlier statement in this historical record that Option C is ACTIVE, remains in force, is unchanged/current, or prohibits all destructive authority is superseded. Current status: **REVOKED**.

This revocation removes Option C as a blanket prohibition but does not authorize any particular destructive operation. Deletion, archive, cleanup, expiry, vacuum, compaction, backup/replica removal, export mutation or provider operation still requires a separately explicit, scoped approval with exact target/data class, preconditions, expected effect, dependencies, verification and recovery/rollback plan. T0 canonical data, lease/fencing, ledgers, audit/reconstruction/recovery, custody and trust evidence remain protected unless separately approved. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged. No L4 control or technical-enforcement status is promoted by this decision.
