# Environment and Evidence Boundary

Date: 2026-11-09
Status: **DOCUMENTATION POLICY — NO ENVIRONMENT INSPECTION AUTHORIZED**

## 1. Purpose

Define how experimental, CI, and future official-environment evidence must be classified so that test activity is not confused with canonical T0 operation or production acceptance.

## 2. Environment classes

| Class | Meaning | Evidence use |
|---|---|---|
| Experimental operations environment | Temporary VPS or host used for limited operational experiments | May support only the specifically approved experiment. Must not be treated as official T0 state or production acceptance. |
| Synthetic CI environment | Disposable GitHub Actions jobs, fixtures, and generated test data | Supports only the exact source SHA, workflow context, job, and artifact proven by CI records. Does not prove deployed runtime state. |
| Future official environment | A separately designated and approved environment for canonical T0 operation | Not designated as of this document. No environment-specific claim is admissible until its identity and evidence scope are approved. |

## 3. Current experimental VPS exclusion

The current VPS is an experimental operations environment only. The user has explicitly excluded collection of its data.

Therefore, this project must not:
- connect to that VPS for inventory or evidence collection;
- list or inspect its files, volumes, databases, backups, replicas, logs, or runtime consumers;
- open/query its databases or calculate dataset sizes/coverage;
- use its current or historical contents as a canonical T0 inventory;
- infer official provider, storage, deployment, or retention decisions from its setup.

This exclusion applies to read-only inspection as well as mutation. A read-only label does not override the user's exclusion.

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

This document does not authorize access to any VPS, host, database, cloud account, or storage service.

## 6. Data lifecycle implications

- The static dataset/consumer inventory is a repository-level baseline only.
- No runtime inventory is required from the current experimental VPS.
- Unknown official-environment datasets, copies, consumers, dependencies, backups, and recovery properties remain **NOT VERIFIED**, not absent.
- No numeric retention period, archive tier, backup expiry, vacuum, cleanup, or deletion rule is approved by this boundary.
- Shared ownership and centralized lifecycle governance remain design principles; they do not grant any environment or consumer implicit write/delete authority.

## 7. Acceptance checklist

- [x] Experimental VPS is explicitly classified as non-official.
- [x] User exclusion of data collection from the experimental VPS is captured.
- [x] Read-only inspection is included in the exclusion.
- [x] Synthetic CI evidence is separated from deployed runtime evidence.
- [x] Official environment is marked NOT DESIGNATED.
- [x] No environment access or lifecycle operation is authorized.

**Status: POLICY DOCUMENTED — OFFICIAL ENVIRONMENT NOT DESIGNATED — NO VPS INVENTORY AUTHORIZED.**
