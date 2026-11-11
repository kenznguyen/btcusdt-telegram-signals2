# T0 Minimum Operational — Read-Only Evidence Assessment

- Date: 2026-11-11 (Asia/Ho_Chi_Minh)
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Repository HEAD observed before this evidence commit: `fe85a676753aac1ee308c24d4390ea4bac2ec58e`
- Operation class: READ-ONLY REPOSITORY AND EXISTING ARTIFACT REVIEW
- Owner decision: T0 Minimum Operational is the current operational acceptance target; L4-Minimum is a separate assurance objective.
- Scope: inspect current repository contracts and an existing, already completed SSH preflight artifact. No new VPS command or workflow dispatch.

## 1. Decision

**T0 Minimum Operational: PARTIAL EVIDENCE — NOT VERIFIED / NOT ACCEPTED.**

The existing preflight provides point-in-time evidence for SQLite integrity and the loopback listener, plus feeder PID observations. It does not establish the minimum operational criteria as a whole because candle readability/schema, data freshness progression, lease/writer ownership, authenticated read-path success and current process state are not evidenced by this artifact.

This is not a failure finding about the database. It is an evidence sufficiency finding.

## 2. Source and artifact identity

- Existing workflow run: [42997062646](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42997062646)
- Branch/source SHA checked out by workflow: `383c8275eef9f7751a5078337f490771c9790476`
- Workflow jobs:
  - `P1 SSH preflight contract checks`: SUCCESS.
  - `P1 authenticated Scaleway read-only preflight`: SUCCESS.
  - Recovery-specific tests, isolated SQLite tests, T0→T2 data-flow tests, G4 contract tests and manual acceptance: SKIPPED.
- Artifact ID: `13844077578`
- Artifact name: `p1-scaleway-ssh-preflight-42997062646`
- Artifact GitHub SHA-256: `f63703a454b51cba281c7d780219f3d0231b5d3403bcfb1b9db2e33eea4becd3`
- Artifact size: 1,066 bytes
- Created: `2026-11-11T09:40:07Z`
- Expires: `2026-11-18T09:39:50Z`
- Downloaded ZIP independently recomputed SHA-256: same value as GitHub metadata.
- Remote checkout SHA reported by the preflight: `9ae2eeae4ece3d657781b68e96b6f4509cd95f24`.
- Host label: `btcquant-t0-t1-test-01`.

The workflow source SHA, remote checkout SHA and repository branch HEAD are distinct identities. This artifact does not prove that the VPS checkout matches the current repository HEAD `fe85a676753aac1ee308c24d4390ea4bac2ec58e`.

## 3. What the artifact proves

Sanitized remote output:
- `FEEDER_PIDS=22045,22046`
- `API_8788_ENDPOINTS=127.0.0.1:8788`
- `API_8788=LOOPBACK_ONLY`
- `SQLITE_INTEGRITY=PASS`
- `P1_SSH_PREFLIGHT=PASS_READ_ONLY_PREFLIGHT`
- SSH exit code: `0`

The complete downloaded ZIP was inspected. It contains only the CI source SHA, sanitized remote preflight log, verdict, SSH diagnostic and exit-code files. No secret values were present in the inspected payload.

## 4. Minimum operational criteria cross-check

| Criterion | Evidence | Disposition |
|---|---|---|
| SQLite database integrity | Existing preflight reports `SQLITE_INTEGRITY=PASS` | **PASS — point-in-time only** |
| Feeder process exists | Two PIDs were reported | **PARTIAL** — PID observation does not prove current process health or writer uniqueness |
| Single writer / valid lease and fencing | Not included in artifact | **NOT VERIFIED** |
| BTCUSDT M15/H1 schema and candle queries | No DB query or schema evidence in artifact | **NOT VERIFIED** |
| New candle progression / freshness | No watermarks or repeated observation | **NOT VERIFIED** |
| Read-only reader/API access | Listener bound to `127.0.0.1:8788`; no authenticated request | **PARTIAL / NOT VERIFIED** |
| API authentication and response contract | Not tested by this preflight | **NOT VERIFIED** |
| No external/public listener | API 8788 reported loopback-only | **PASS — port 8788 snapshot only** |
| T1/T2 consumption | No end-to-end test in this run; relevant jobs skipped | **NOT VERIFIED** |

## 5. Current disposition

- SQLite integrity: **PASS — existing point-in-time snapshot**.
- Loopback-only API listener metadata: **PASS — existing point-in-time snapshot**.
- Feeder activity: **PARTIAL**.
- T0 Minimum Operational aggregate: **NOT VERIFIED / NOT ACCEPTED**.
- T0 L4-Minimum: remains a separate assurance workstream; this assessment neither promotes nor downgrades L4 controls.
- T1 activation and T0→T1→T2 integration: unchanged, NOT VERIFIED.
- Paper-only posture and `AI_EXECUTION_ENABLED=false`: unchanged.

## 6. Next evidence needed

To complete the minimum gate, obtain a separately bounded, sanitized read-only evidence set for:
1. Current Feeder process state and unique writer/lease ownership.
2. SQLite read-only schema and bounded M15/H1 query results (counts/watermarks only; no candle payload export).
3. Freshness progression from two time-separated observations.
4. Authenticated read-only API request and response metadata, using an already approved secret source that never exposes the token.

The existing owner deployment protocol `docs/evidence/T0_OWNER_READONLY_DEPLOYMENT_EVIDENCE_PROTOCOL_2026-11-10.md` explicitly excludes API/health requests, database reads and agent SSH access. The current SSH workflow uses a fixed forced command and has no verified second-probe dispatcher or safe installation path. Therefore those additional checks are **BLOCKED pending a separate exact runtime-probe/access approval and a verified invocation path**. Do not bypass the forced-command boundary or improvise SSH/SCP commands.

## 7. Actions not performed

No new SSH/VPS access, command invocation, workflow dispatch, API request, token use, SQLite connection/query, database write, Feeder/API restart, deployment, installation, configuration change, lease/fencing operation, T1 activation, cleanup/deletion, exchange connection or trading action occurred.
