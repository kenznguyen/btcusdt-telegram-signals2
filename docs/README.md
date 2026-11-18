# Documentation index

Reviewed: 2026-11-18  
Repository: `kenznguyen/btcusdt-telegram-signals2`

This index distinguishes current operating documents from historical evidence. Historical documents are intentionally retained and must not be read as proof of current runtime state.

## Active repository guidance

| Document | Status | Purpose |
|---|---|---|
| [Root README](../README.md) | ACTIVE | Current repository map, verified constraints and entry points |
| [Project Session Handoff](PROJECT_SESSION_HANDOFF.md) | ACTIVE | Current main snapshot at the top; historical handoff preserved below |
| [Repository Maintenance](REPOSITORY_MAINTENANCE.md) | ACTIVE | Branch, CI, safety, release and documentation rules |
| [Contribution Effort Ledger](PROJECT_CONTRIBUTION_EFFORT_LEDGER.md) | ACTIVE / VERIFY BEFORE USE | Effort/accounting record; consult its own date and evidence scope |

## Architecture and decision records

| Path | Status | Notes |
|---|---|---|
| `architecture/T0_POSTGRESQL_ATOMIC_WRITER_P0_2026-11-05.md` | HISTORICAL / DESIGN | T0 writer design; not runtime proof |
| `architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A1_2026-11-11.md` | HISTORICAL / DECISION INPUT | Signature trust policy amendment; use the latest ratified decision/evidence before implementation |

## Evidence and reviews

| Path | Status | Notes |
|---|---|---|
| `evidence/MAIN_CORE_API_QUALITY_SNAPSHOT_STATIC_REVIEW_2026-11-18.md` | ACTIVE FINDING | Main-side Core API ordering defect; static finding, runtime test NOT RUN |
| `evidence/G0_52_D01_D14_CLOSURE_AUDIT_AND_S2_READINESS_2026-11-11.md` | HISTORICAL | D01–D14 closure and S2 readiness assessment for its stated branch/SHA |
| `evidence/SSH_PREFLIGHT_RETIREMENT_2026-11-11.md` | HISTORICAL / RETIRED | Records approved retirement; do not restore retired Preflight |
| `evidence/P1_SSH_PREFLIGHT_CONTRACT_RUN_42793921622.md` | HISTORICAL | Historical contract run only; Preflight has since been retired |
| `evidence/PR140_FAIL_CLOSED_PROBE_FIX_20261110.md` | HISTORICAL | PR #140 evidence, not current runtime evidence |
| `evidence/PR140_SOURCE_REVIEW_20261110.md` | HISTORICAL | PR #140 source review |
| `evidence/T0_SIGNATURE_CONTRACT_FINAL_CONSISTENCY_REVIEW_2026-11-11.md` | HISTORICAL | Signature contract review for its stated source and scope |
| `evidence/T0_T2_DEPLOYMENT_PARITY_EVIDENCE_RECONCILIATION_2026-11-10.md` | HISTORICAL | Historical deployment parity reconciliation; does not prove current deployment |
| `evidence/ANDROID_PR_42_44_SOURCE_RECOVERY_AUDIT_2026-11-05.md` | HISTORICAL | Android source recovery audit |
| `evidence/CHART_PRO_SEPARATION_AUDIT_2026-11-05.md` | HISTORICAL | Android Chart Pro separation audit |
| `reviews/t1/P1_38_SECOND_PASS_ADVERSARIAL_REVIEW_P137_2026-11-09.md` | HISTORICAL | T1 adversarial review for its stated scope |

## Archive

| Path | Status | Notes |
|---|---|---|
| `archive/README_TELEGRAM_LEGACY_2026-11-18.md` | HISTORICAL / ARCHIVED | Full previous root README retained before the 2026-11-18 refresh; deployment instructions are not current deployment evidence |
| `archive/PROJECT_SESSION_HANDOFF_HISTORY_2026-11-10.md` | HISTORICAL | Prior handoff history; preserve as audit trail |

## Classification rules

- **ACTIVE**: current guidance, subject to the exact branch and source SHA.
- **HISTORICAL**: retained evidence or decisions scoped to their original date, branch, SHA and test context.
- **SUPERSEDED / RETIRED**: no longer an instruction to operate; preserve the record and point to the superseding decision.
- **NOT VERIFIED**: the document or evidence does not establish the claimed runtime, deployment, custody or operational state.

Do not delete historical evidence to make the current state appear cleaner. Update this index when documents are added, superseded or archived.
