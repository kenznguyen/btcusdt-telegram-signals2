# D-2026-11-10 — Remove Mandatory Independent Reviewer from L4-Minimum

Date: 2026-11-10
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Record type: explicit owner decision; supersedes the reviewer requirement in the 2026-11-09 L4 personal-scope decision for L4-Minimum only
Status: **OWNER-DIRECTED POLICY CHANGE — DOCUMENTED; MATRIX ALIGNMENT REQUIRED; NO TECHNICAL ACCEPTANCE**

## 1. Decision

The owner directs removal of a mandatory independent human/third-party reviewer from the L4-Minimum acceptance criteria.

L4-Minimum may be assessed and dispositioned by the system owner. A qualifying independent reviewer and a separate independent-review disposition are no longer prerequisites for an L4-Minimum aggregate PASS.

This decision supersedes only the independent-review requirement stated in:
- `docs/decisions/D-2026-11-09-L4-PROVENANCE-PERSONAL-SCOPE.md`, §3 and §6;
- the L4-Minimum Acceptance Matrix requirement previously identified as L4M-09; and
- references in L4-Minimum aggregate acceptance that made an independent reviewer disposition mandatory.

The 2026-11-09 decision remains an unchanged historical record. This document is the later controlling owner decision for the narrow subject above.

## 2. Revised acceptance denominator

- L4M-01 through L4M-08 remain mandatory and unchanged in substance.
- L4M-10 remains mandatory, with aggregate acceptance based on the same frozen evidence baseline and owner-issued disposition.
- L4M-09 is retained as a traceability identifier but reclassified **OWNER-WAIVED / NOT A MANDATORY CONTROL**. It is not counted as PASS, does not count in the mandatory-control denominator, and cannot block L4-Minimum acceptance.
- The active mandatory denominator is therefore nine controls: L4M-01–L4M-08 and L4M-10.
- Overall L4-Minimum PASS requires all nine active controls to PASS on the same frozen immutable evidence baseline, plus an owner-issued disposition that identifies that exact baseline and its digest. No averaging or compensating controls are permitted.

## 3. Controls that remain mandatory

Removing the independent reviewer does not remove technical independence or evidence integrity requirements. The following remain mandatory:

1. Owner-controlled evidence custody outside both T0/VPS and GitHub failure domains, including the latest-head anchor and outage readback.
2. Signing authority separated from T0 runtime/admin credentials.
3. Exact-object binding and authenticated freshness/latest-head anchor.
4. Deterministic offline verification on a separate environment using a separately controlled trust policy. The owner must perform and record this verification; it is not an independent human review.
5. Independent evidence-copy readback/recovery, non-destructively.
6. Key/trust lifecycle semantics and fail-closed handling of unknown/revoked states.
7. Tamper-evident history and independent manifest/copy, with storage-administrator assumptions explicit.
8. Bounded and truthful provenance claims.
9. Fail-closed per-control and aggregate owner acceptance under L4M-10.

The terms “independent custody”, “independent offline verification” and “independent readback” continue to describe technical separation/failure-domain properties. They must not be represented as independent human review or third-party assurance.

## 4. Assurance limitations and prohibited claims

Because no independent reviewer is required:
- Do not claim independent assurance, independent audit, third-party review, certification, external attestation of the overall L4-Minimum result, or reviewer-confirmed acceptance.
- Record the assessor as the system owner and disclose that the owner is also the requester/approver and may be the evidence producer/custodian.
- Record exact artifacts, hashes, procedures, observed outputs, unresolved limitations and the owner’s disposition.
- Preserve a clear distinction between owner self-assessment, automated verification, technical independence of storage/environment, and independent human review.
- A successful owner assessment does not prove market-data truth, source completeness, production durability, legal admissibility or trading correctness.

This decision accepts the conflict inherent in owner self-assessment as a conscious personal-project assurance trade-off. It does not claim that owner self-assessment is equivalent to independent review.

## 5. Scope boundaries

This waiver applies only to the L4-Minimum provenance acceptance profile for this personal, non-commercial system.

It does not:
- waive reviewer, approval-separation, competence or conflict controls required by P1.8.152/P1.8.153 or any other lifecycle, legal, security, provider, staging, restore or operational workstream;
- close any P1.8.152 reviewer-control finding;
- waive owner approval gates or Option C — No Destructive Authority;
- authorize key/trust-root operations, permission changes, provider contact, runtime/VPS/database/data changes, staging, restore, fault injection, workflow dispatch, archive, cleanup, expiry or deletion;
- change T0 canonical-data protection, T0's independent asset boundary, or the paper-only/no-live-orders posture.

If another governing record independently requires a reviewer for a distinct decision or operation, that requirement remains in force.

## 6. Required documentation alignment

The L4-Minimum Acceptance Matrix must:
- mark L4M-09 OWNER-WAIVED / NOT MANDATORY without renumbering historical references;
- remove independent-review disposition as an aggregate PASS prerequisite;
- replace reviewer evidence fields with owner assessor identity, conflict disclosure, exact baseline identity and owner disposition;
- retain all technical independence, custody, offline verification and fail-closed controls;
- explicitly prohibit claims of independent assurance.

The historical 2026-11-10 audits and the 2026-11-09 owner decision must not be rewritten. Their reviewer requirements remain accurate descriptions of the policy in force when those records were created; this decision supersedes them prospectively for L4-Minimum only.

## 7. Current status

- Owner decision to waive mandatory independent review for L4-Minimum: **APPROVED BY THIS RECORD**.
- Matrix alignment: **PENDING UNTIL UPDATED AND READ BACK**.
- L4M-01–L4M-08 and L4M-10 implementation/evidence: **NOT VERIFIED / BLOCKED as previously assessed**; this decision does not promote any technical control.
- L4M-09: **OWNER-WAIVED / NOT A MANDATORY CONTROL**.
- L4-Minimum technical/operational acceptance: **BLOCKED / NOT VERIFIED** until the nine active controls have evidence and owner disposition.
- Independent assurance claim: **NOT AVAILABLE / MUST NOT BE CLAIMED**.
- P1.8.152/P1.8.153 lifecycle reviewer gates: **UNCHANGED**.
- Option C — No Destructive Authority: **UNCHANGED**.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.

No tests, GitHub Actions workflows, source code, runtime, VPS, database, T0/T1/T2, keys, trust roots, permissions, providers, data, staging, restore, fault injection or destructive operations are authorized or performed by this decision.
