# Environment and Evidence Boundary

Date: 2026-11-09
Status: **EXPERIMENTAL VPS READ-ONLY INVENTORY PERMITTED — MUTATIONS NOT AUTHORIZED**

## 1. Purpose

Define how experimental, CI, and future official-environment evidence must be classified so that test activity is not confused with canonical T0 operation or production acceptance.

## 2. Environment classes

| Class | Meaning | Evidence use |
|---|---|---|
| Experimental operations environment | Temporary VPS or host used for limited operational experiments | May support only the specifically approved experiment. Must not be treated as official T0 state or production acceptance. |
| Synthetic CI environment | Disposable GitHub Actions jobs, fixtures, and generated test data | Supports only the exact source SHA, workflow context, job, and artifact proven by CI records. Does not prove deployed runtime state. |
| Future official environment | A separately designated and approved environment for canonical T0 operation | Not designated as of this document. No environment-specific claim is admissible until its identity and evidence scope are approved. |

## 3. Current experimental VPS exclusion

The current VPS is an experimental operations environment only. The user has revoked the prior blanket exclusion and permits scoped read-only data collection from this experimental VPS.

Permitted within a scoped read-only inventory:
- connect to the experimental VPS using the existing approved access path;
- inspect filesystem paths, mounts, volume metadata, service/process metadata, and relevant configuration with secrets redacted;
- inspect database identity/schema/version, table metadata, row counts, bounded time coverage, and integrity status using read-only access;
- inspect backup/replica metadata and consumer/dependency evidence without changing their state.

Constraints:
- do not write, delete, migrate, vacuum, compact, restart, deploy, install, reconfigure, ingest, sync, or alter permissions;
- do not expose credentials, private keys, tokens, or unrestricted raw user/account data in logs or GitHub evidence;
- do not treat experimental observations as official T0 acceptance or canonical production state;
- stop if a command could mutate state or its read-only behavior is uncertain.

## 4. Evidence admissibility

Every evidence item must state:
- environment class;
- repository, branch, exact source SHA;
- observation timestamp and method;
- workflow/run/job/artifact identity where applicable;
- whether evidence is source-defined, synthetic CI, historical experimental observation, or official-environment observation;
- explicit limitations and what the evidence does not prove.

Evidence from one class must not be silently promoted into another:
- source code does not prove runtime deployment;
- synthetic CI does not prove production operation;
- historical experimental observations do not prove current experimental state;
- experimental VPS observations do not prove official T0 state;
- official-environment claims require a designated official environment and traceable evidence from that environment.

## 5. Official environment designation gate

The official environment is **NOT DESIGNATED**.

Before any official-environment inventory or acceptance work:
1. The user must designate the environment as official.
2. The scope of permitted inspection and evidence collection must be explicitly approved.
3. The source identity and target environment identity must be recorded separately.
4. Evidence collection must follow the approved least-privilege procedure.
5. Any write, deployment, service restart, database creation/migration, ingestion, retention, archive, vacuum, cleanup, or deletion requires its own authorization where applicable.

This document records the user's permission for scoped read-only inventory on the current experimental VPS only. It does not authorize write/mutation actions or access to other environments/accounts.

## 6. Data lifecycle implications

- The static dataset/consumer inventory is a repository-level baseline only.
- A scoped read-only runtime inventory may be collected from the current experimental VPS; it remains experimental evidence only.
- Unknown official-environment datasets, copies, consumers, dependencies, backups, and recovery properties remain **NOT VERIFIED**, not absent.
- No numeric retention period, archive tier, backup expiry, vacuum, cleanup, or deletion rule is approved by this boundary.
- Shared ownership and centralized lifecycle governance remain design principles; they do not grant any environment or consumer implicit write/delete authority.

## 7. Acceptance checklist

- [x] Experimental VPS is explicitly classified as non-official.
- [x] User's revocation of the blanket inspection ban is captured.
- [x] Scoped read-only inventory is permitted; mutation remains prohibited.
- [x] Synthetic CI evidence is separated from deployed runtime evidence.
- [x] Official environment is marked NOT DESIGNATED.
- [x] No environment access or lifecycle operation is authorized.

**Status: EXPERIMENTAL VPS READ-ONLY INVENTORY PERMITTED — OFFICIAL ENVIRONMENT NOT DESIGNATED — MUTATIONS NOT AUTHORIZED.**
