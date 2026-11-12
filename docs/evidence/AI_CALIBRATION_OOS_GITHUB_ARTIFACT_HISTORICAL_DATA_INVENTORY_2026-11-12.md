# AI Calibration OOS — GitHub Artifact and Historical Data Inventory

Date: 2026-11-12 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Exact source HEAD inspected: `93f3b0e350cf62b205f8d2a3a84fd139e9c5f59e`
Recursive Git tree: `7ed669ada40b2232c672eb026f9aa925cc43d901`
Tree entries: 994; truncated: false
Status: **GitHub inventory PASS; recoverable canonical OOS dataset BLOCKED**

## 1. Scope and non-actions

Owner approved a read-only inventory of GitHub repository content, GitHub Actions run/artifact metadata, selected existing artifact ZIP contents, and historical repository evidence.

No T0 API, SQLite database, VPS/SSH, exchange, external storage, backup location, or current runtime was accessed. No dataset was created/exported/transformed; no code, tests, workflows, dependencies, schema, canonical data, runtime, or trading behavior was changed. No workflow was dispatched and no artifact retention/deletion setting was changed.

## 2. Current repository tree

The exact branch HEAD was verified from GitHub branch metadata. Its complete recursive tree contains 994 entries and is not truncated.

Path-level scan found:
- No `.csv`, `.parquet`, `.feather`, `.arrow`, `.sqlite/.sqlite3`, `.db`, `.jsonl`, or `.ndjson` dataset files.
- No tracked canonical `T0_M15_H1_DATASET_BUNDLE_V1` payload, manifest, or producer path.
- Existing dataset consumer contract is design-only.
- Existing P1.8 ZIP/JSON evidence bundles are explicitly synthetic and are not BTCUSDT market data.

The exact-identifier GitHub code search returned no result. This search is supplementary; the exact branch recursive tree is the controlling repository-path inventory.

## 3. Historical T0 market-data evidence

The repository preserves operator-provided T0 runtime evidence dated 2026-11-09:
- Historical SQLite path: `/home/ubuntu/t0/app/.data/market-data.sqlite3`.
- Bounded M15 coverage: 3 expected / 3 returned candles, no planner gaps.
- Bounded H1 coverage: 3 expected / 3 returned candles, no planner gaps.
- Historical M15 fingerprint: `sha256:7297654ff9b7a8bbd341f16faa502719b17561497178788abaf7fed28696baf4`.
- Historical H1 fingerprint: `sha256:43922096e8f0b4f91c3addb89f73ba586642e0c9864f289a7f46e78af0db541d`.

These are bounded historical observations, not a training/OOS dataset. The historical T2 context JSON was written to `/tmp/t2-canonical-window-20261109T112946Z.json`; the reconciliation report explicitly says it was not uploaded to GitHub Actions. The former Scaleway VPS was deleted on 2026-11-11. No current T0 runtime or accessible canonical SQLite copy is established by this inventory.

## 4. Selected GitHub Actions artifact inspection

The Actions run listing reports 1,387 total runs; the API returned the newest 1,000 for this branch (2026-11-07 through 2026-11-12). Older runs beyond that API listing window were not exhaustively enumerated. Relevant workflow families in the returned window include T0 single-writer contracts, T0 feeder/API integration, T0 SQLite read-only sandbox, T0 manual validation, T0 L4 validation, T0 Binance connectivity probe, T2 HTTP consumer tests, and T2 Freqtrade strategy smoke.

Selected artifact ZIPs were downloaded read-only and their member inventories inspected:

| Artifact ID | Artifact | ZIP contents inspected | OOS dataset? |
|---:|---|---|---|
| 13628691436 | T0 Timescale read-only evidence | 11 preflight/test/verdict log files | No |
| 13628521899 | T0 Feeder/API integration | 9 systemd integration/event/unit/journal log files | No |
| 13627924430 | T0 SQLite read-only sandbox | 4 scope/test/source-SHA/verdict files | No |
| 13627939321 | T0 single-writer gateway contracts | 8 compile/contract/behavior/readiness/restart log files | No |
| 13628178055 | T0 provider bootstrap | 3 test/preflight/verdict files | No |
| 13920786893 | Latest T0 Feeder/API integration | 9 systemd integration/event/unit/journal log files | No |
| 13921070540 | Latest T0 SQLite read-only sandbox | 4 source-SHA/scope/test/verdict files | No |
| 13921095476 | Latest T0 SQLite recovery auto-check | 5 source-SHA/scope/changed-files/test/verdict files | No |
| 13921095419 | Latest T0 SQLite lease-fencing auto-check | 4 scope/test/source-SHA/verdict files | No |

The selected ZIPs contain CI/test and runtime-integration evidence, not raw BTCUSDT candle rows, a historical database snapshot, a canonical M15/H1 bundle, or sample-level lineage.

The two P1.8 artifacts `13546255148` and `13545287609` are explicitly classified as synthetic CI evidence. They are not eligible OOS data and must not be substituted.

## 5. FreqAI research files are not proof of a dataset

- `freqai_bridge/config.research.json` specifies M15 only; it does not configure the named M15/H1 bundle or a separate calibration partition.
- `freqai_bridge/README.md` contains example `freqtrade download-data` and training commands and explicitly states the example dates are not a claim that a dataset/model exists.
- The prediction bridge requires a training-produced `.data/freqai-provenance.json`; the repository does not establish that a real training job produced this sidecar or its referenced immutable dataset.
- Existing `trainingDatasetVersion` hand-off validation checks a declared value; it does not reconstruct or independently prove historical training sample membership.

## 6. Disposition

| Gate | Result |
|---|---|
| Exact branch recursive tree inventory | **PASS** |
| Candidate canonical bundle/manifest/producer in tracked tree | **NOT FOUND** |
| Selected T0 Actions artifact metadata and ZIP member inventory | **PASS — inspected artifacts contain test/log evidence only** |
| Historical T0 market-data ingestion | **HISTORICAL PASS — bounded windows only** |
| Recoverable raw historical candles in GitHub | **NOT FOUND in inspected repository and selected artifacts** |
| Immutable canonical M15/H1 OOS payload | **BLOCKED / NOT VERIFIED** |
| Sample-level lineage, chronological split, embargo, reproducibility | **NOT VERIFIED** |
| Real OOS evaluation and AI admission eligibility | **NOT VERIFIED / fail-closed** |

This result does not prove that no backup or export exists outside GitHub. It proves only that the inspected repository and selected GitHub artifacts do not provide a verifiable OOS bundle.

## 7. Next decision boundary

Before any new collection or runtime work:
1. Determine whether an owner-held backup/export of the historical T0 SQLite database or a prior candle export exists outside GitHub, and identify its exact immutable reference and read-only access path.
2. If no such copy exists, stop and request a separate bounded decision on reacquiring canonical candles through T0. Do not infer permission to provision a VPS, start T0, connect to Binance, export data, or create a derived bundle from this inventory approval.
3. Only after a valid source is identified may the derived bundle contract, sample identity/lineage, chronological split and embargo be frozen.

Keep T0 canonicality unchanged. Synthetic evidence, unpinned external downloads, and the small historical 3-candle coverage windows are not substitutes for a real OOS dataset.
