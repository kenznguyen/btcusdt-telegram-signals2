# AI Strategy Research D1 — Read-Only Bundle Verification

**Date:** 2026-11-11  
**Status:** BLOCKED — candidate bundle not present in inspected GitHub branch; T0 runtime verification not performed  
**Repository:** `kenznguyen/btcusdt-telegram-signals2`  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`  
**Branch HEAD inspected:** `03b1ab3478bbba2b5880271462ea94412667c9a9`

## 1. Authorization and scope

Owner approved a bounded read-only verification of the candidate `T0_M15_H1_DATASET_BUNDLE_V1` for manifest, SHA-256, time coverage and quality metadata.

This pass inspected only GitHub repository metadata, the recursive tree at the branch HEAD, and existing documentation. No T0 endpoint, VPS, SSH session, SQLite database, dataset payload or runtime was accessed. No data was exported, copied, transformed or modified.

## 2. Repository inventory findings

- Recursive Git tree at the inspected branch HEAD returned 890 entries and was not truncated.
- No tracked path identifying `T0_M15_H1_DATASET_BUNDLE_V1` was found.
- No candidate AI research dataset manifest or market-data payload in CSV, Parquet, Feather, Arrow, SQLite/DB or JSONL form was found in the tracked tree.
- The repository does contain synthetic P1.8 evidence ZIPs and their manifests/digests. These are explicitly synthetic evidence artifacts, not the BTCUSDT M15/H1 canonical research bundle; they must not be substituted.
- `docs/evidence/T0_L4_ARTIFACT_MANIFEST_PILOT_EVIDENCE_2026-11-10.md` documents a GitHub-only, three-artifact pilot and explicitly excludes VPS/SSH and canonical T0 SQLite access. It does not establish the existence or contents of the AI research bundle.
- `docs/architecture/DATASET_CONSUMER_CONTRACT.md` is marked design-only, not implemented or activated; it does not supply a published bundle reference.

## 3. Verification results

| Check | Result | Evidence |
|---|---|---|
| Candidate bundle identity in tracked tree | NOT FOUND | Recursive tree inventory, 890 entries |
| Candidate manifest | NOT FOUND | No candidate manifest path/payload in inspected tree |
| Bundle file SHA-256 | NOT VERIFIED | No candidate payload available |
| Manifest digest | NOT VERIFIED | No candidate manifest available |
| UTC coverage / row counts | NOT VERIFIED | No candidate manifest/payload |
| Candle gaps / duplicates / ordering / completion | NOT VERIFIED | No candidate payload or T0 read-only access |
| Source provenance | NOT VERIFIED | No candidate bundle reference |

This is a bounded repository-inventory result, not proof that the bundle does not exist outside GitHub.

## 4. Disposition

**D1: BLOCKED / PARTIALLY DECIDED.** The conceptual choice of BTCUSDT M15 with completed H1 context and the SHA-256 + manifest policy remains approved in principle. The exact bundle is not verified and must not be treated as frozen.

**R1: NOT FROZEN. R2: NOT AUTHORIZED.**

Do not substitute synthetic evidence, live exchange downloads, another timeframe or an unpinned "latest" dataset. Do not compute features or begin experiments.

## 5. Required next step

A separate, narrowly scoped read-only verification must be performed where the actual T0 bundle is stored or published. Before access, establish the exact read-only location/reference and access method. Then capture:
- stable dataset ID/version and producer reference;
- manifest bytes and SHA-256 of the manifest;
- exact file inventory and per-file SHA-256;
- symbol/timeframes, UTC start/end, candle counts and schema version;
- gap, duplicate, out-of-order, incomplete-candle and quality reports;
- source/provenance and immutable-version reference.

If no bundle has been published, stop and request a separate owner decision on whether/how to prepare a derived read-only bundle. Do not create it under this verification authorization.

## 6. Non-actions

No T0 DB/API/runtime/VPS/SSH access, no data read/export/copy, no file creation on T0, no schema/migration, no cleanup/deletion, no tests/workflow, no feature computation, no labels, no model/calibration training, no backtest, no code or trading changes. T0 remains independent and unchanged; Strategy Core remains unchanged; AI DCA remains disabled in v1; paper-only and `AI_EXECUTION_ENABLED=false` remain.
