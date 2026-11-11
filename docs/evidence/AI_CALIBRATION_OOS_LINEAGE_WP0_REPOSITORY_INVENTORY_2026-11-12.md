# WP0 — T0_M15_H1_DATASET_BUNDLE_V1 Repository Inventory

Date: 2026-11-12 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Inspected branch HEAD: `f012305b9c13d0deb7ec1bdfeda22a2affb7a5d2`
Inspected Git tree: `14a19ff0f659eaaf9114cd77ed08c9d6ac1da429` (recursive, 978 entries, not truncated)
Status: **BLOCKED — candidate canonical bundle/contract not present in tracked repository; no schema may be inferred**

## 1. Scope and method

Read-only inspection of the active branch handoff, approved WP0-WP4 scope, recursive Git tree, and directly relevant architecture/evidence/source files. No source, test, workflow, dependency, dataset or runtime was changed. No T0 endpoint, database, VPS, exchange, external provider or local runtime was accessed.

The branch HEAD was confirmed from GitHub branch metadata before inventory. The handoff at that HEAD was read first. The exact scope document was also re-read.

## 2. Candidate bundle discovery

| Check | Result | Evidence |
|---|---|---|
| Exact identifier `T0_M15_H1_DATASET_BUNDLE_V1` in tracked paths | NOT FOUND | Recursive tree at `f012305...`, 978 entries |
| Candidate bundle schema/manifest path | NOT FOUND | Recursive tree; no tracked path identifies the named bundle |
| Candidate canonical bundle payload | NOT FOUND | Tree contains no identified published M15/H1 research bundle |
| Producer implementing the named bundle | NOT IDENTIFIED | No producer path/contract reference found in inspected source surface |
| Consumer binding to the named bundle | NOT IDENTIFIED | Current FreqAI bridge consumes T0 candle HTTP contract, not a named M15/H1 bundle |
| Exact bundle bytes/digest | NOT VERIFIED | No candidate bundle bytes available |
| T0 runtime bundle presence | NOT VERIFIED | Explicitly outside this repository-only read scope |

A previous bounded inventory is consistent with this result: `docs/evidence/AI_STRATEGY_D1_READ_ONLY_BUNDLE_VERIFICATION_2026-11-11.md` (blob `3ce40a23f625f40483a05e0f0846290a62d6bfc0`) recorded that the candidate bundle was absent from the then-inspected tracked tree. That earlier inspection did not prove absence outside GitHub; the same limitation applies here.

Synthetic P1.8 evidence bundles are present in the tree, but are unrelated synthetic verification artifacts and MUST NOT be substituted for the BTCUSDT canonical research bundle.

## 3. Relevant existing contracts and source behavior

| Area | Existing source | What it actually establishes | What it does not establish |
|---|---|---|---|
| T0 dataset access | `freqai_bridge/context.py` (blob `9abe781340dc9b948c40c759d92f340da3e372c1`); `freqai_bridge/http_candles.py` | T2 obtains a bounded read-only M15 candle window from T0 HTTP; no local SQLite/cache fallback | No immutable M15/H1 training bundle or sample-level lineage |
| Candle identity | `pipeline/decision.py` (blob `8720d8ab988529b1545a27aa0792beca9e6a84aa`) and HTTP client | Validates market identity, M15 timeframe, range, ordered gap-free candles, availability, datasetVersion hash for the requested window | No train/calibration/evaluation sample membership or H1 context mapping |
| Feature generation | `freqai_bridge/ChartProFreqaiResearch.py` (blob `a7722f1148cf105c853deedaacb88edd14e671be`) | Relative price/volume rolling means, pct-change, raw volume, day-of-week/hour; strategy timeframe M15 | No explicit per-sample feature lineage manifest, full feature-window boundaries or H1 features |
| Label generation | same strategy file | Target `&-future_return` is `close.shift(-horizon) / close - 1`; configured horizon comes from FreqAI config | No frozen OOS label-definition contract, sample identity, label-availability timestamp mapping or row-level lineage |
| Research config | `freqai_bridge/config.research.json` (blob `2ddccabc8a88a66ace251070c03d8623214291ac`) | M15 only; `label_period_candles=4`; shifted candles=2; indicator periods 14/28; `test_size=0.2`, `shuffle=false`; retraining settings | Not a frozen chronological train/calibration/evaluation protocol; no calibration partition, embargo, seed, split version or reproducibility tolerance |
| Training provenance handoff | `freqai_bridge/exporter.py` (blob `3b707174316d0c6b464ac947cbbe2d2fbee73682`); `freqai_bridge/README.md` (blob `380a2c6abdfc2bc8b42281558f8a137d059c4820`) | Requires externally supplied `trainingDatasetVersion`, `trainedThroughMs`, `trainingCompletedAtMs`, model and strategy versions; validates declared bounds | Does not independently derive/verify training dataset membership, manifest bytes, actual training cutoff, or truthfulness of sidecar |
| OOS record validator | `pipeline/oos_evaluation.py` (blob `756f7d2707051cb7f90bd5b7c62ff4d6f269f21d`) | Checks frozen OOS record structure, supplied manifest binding, and local timestamp/dataset identity consistency | Explicitly cannot verify authoritative lineage, sample-level embargo, reproducibility, trusted time, statistical acceptability or admission |
| Dataset consumer contract | `docs/architecture/DATASET_CONSUMER_CONTRACT.md` (blob `ef5e946b26ad17410023a79a765be73aeb198f0f`) | Design-only conceptual immutable dataset/version dependency model | Not implemented; no actual published bundle schema |
| Prior inventory | `docs/architecture/DATASET_CONSUMER_INVENTORY_BASELINE_2026-11-09.md` (blob `9183b94bcb959a999029d9698d129af9b9f39b20`) | Static inventory differentiates T0 candles, T1 snapshots, T2 artifacts and other data domains | Does not identify the named bundle or prove runtime presence |

## 4. Field-by-field compatibility against OOS Evidence v1

| OOS lineage requirement | Repository evidence | WP0 assessment |
|---|---|---|
| Immutable bundle ID/version/schema | No named bundle or manifest | **MISSING** |
| Canonical bundle bytes and digest domain | T0 per-query `datasetVersion` exists; no bundle serialization/digest contract | **MISSING / NOT EQUIVALENT** |
| Source dataset identity and M15/H1 coverage | T0 HTTP candle contract supports bounded candle windows; inspected FreqAI config requests M15 only | **PARTIAL for M15 inference window; H1 bundle coverage MISSING** |
| Deterministic sample identity and membership | No sample ID or partition-membership manifest identified | **MISSING** |
| Event/availability timestamp semantics for each sample | Candle rows carry open/close/available timestamps; no frozen split timestamp semantic | **PARTIAL source timestamps; split semantics MISSING** |
| Feature-window mapping per sample | Feature formulas and lookback parameters exist; no row-level feature-window mapping/manifest | **PARTIAL formulas; lineage MISSING** |
| Forecast/label horizon mapping per sample | Four-candle future-return target is configured; no sample-level label availability mapping | **PARTIAL target formula; lineage MISSING** |
| Train/calibration/evaluation disjointness | FreqAI config has non-shuffled test split; no distinct calibration dataset/partition or OOS sample IDs | **MISSING** |
| Horizon + feature-window embargo | No explicit versioned embargo implementation or evidence found in inspected bridge/config | **MISSING** |
| Duplicate, missing, excluded sample accounting | T0 candle window checks gaps for inference; no training/OOS sample exclusion ledger | **MISSING** |
| Transformation lineage and deterministic ordering | Feature code is inspectable; no bundle-bound transform graph/version and row ordering manifest | **PARTIAL code only; bundle lineage MISSING** |
| Independent recomputation from canonical T0 source | Current inference window is read-only fetched and hash-checked; historical training dataset cannot be reconstructed from supplied sidecar alone | **PARTIAL for inference window only** |
| Reproducible split/evaluator identity | OOS record has evaluator commit/digest and protocol ID/version fields; no actual frozen split protocol/command implementation | **FIELDS EXIST; SOURCE PROTOCOL MISSING** |

## 5. Timestamp, feature and label observations (not frozen decisions)

- Current inference candles distinguish `openTimeMs`, `closeTimeMs` and `availableAtMs`. The existing prediction bridge also requires `trainedThroughMs` and `trainingCompletedAtMs`, but these training provenance values are supplied by an external sidecar and are not independently reconstructed by this repository code.
- The research strategy is M15. It does not currently show an H1 feature/context input, despite the candidate bundle name containing M15/H1.
- Feature code uses current/past dataframe rows, rolling means, pct-change, volume, day-of-week and hour-of-day. The config gives indicator periods 14 and 28 and shifted candles 2; exact per-feature window semantics and FreqAI-expanded row mapping are not committed as sample-level lineage.
- The target is a forward return over four configured candles. The target is a future label, but the exact label availability semantic and boundary/embargo rules are not frozen.
- `shuffle=false` and `test_size=0.2` are not sufficient evidence of the approved three-way train/calibration/evaluation chronological holdout, horizon embargo, or OOS isolation.

These observations describe current source code only. They do not establish that a training job or model artifact was actually produced.

## 6. WP0 disposition and stop conditions

**WP0: BLOCKED / PARTIAL STATIC INVENTORY COMPLETE.** The named `T0_M15_H1_DATASET_BUNDLE_V1` contract, immutable payload, producer and consumer binding are not present/identifiable in the inspected GitHub branch. Existing M15 inference and FreqAI training-sidecar contracts cannot be silently promoted into that bundle.

Consequently:
- Do not proceed to WP1/WP2 contract freeze by inventing missing bundle fields or timestamp/sample semantics.
- Do not implement WP3 verifier against a hypothetical schema.
- Do not create/export a derived bundle, query T0, collect sample-level lineage, train/calibrate, or run real OOS evaluation under this approval.
- Keep lineage, horizon embargo, reproducibility and OOS evidence **NOT_VERIFIED**; AI admission remains fail-closed.

## 7. Owner decision required to unblock

A separate bounded Owner decision is needed to establish the authoritative location/reference and access method for the already-existing named bundle, if it exists outside GitHub. Any T0/VPS/database access or bundle creation/export requires its own explicit scope and must not be inferred from this WP0 repository-only approval.

If no such bundle exists, Owner must separately decide whether to authorize a derived read-only bundle specification and its producer path. That decision must preserve T0 as canonical and must not mutate T0.

## 8. Non-actions

No T0, T1 or T2 source/runtime/data changes; no VPS or database access; no source code, tests, workflow, dependencies or schema changes; no real dataset collection, bundle creation/export, model training/calibration, real OOS evaluation, trust/time/key changes, registry events, S2, ledger/risk/Kill Switch changes or trading.
