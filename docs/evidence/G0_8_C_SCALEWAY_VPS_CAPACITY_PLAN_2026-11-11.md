# G0.8-C — Replacement Scaleway VPS Capacity Plan (2026-11-11)

## Scope and decision boundary

Owner-approved capacity planning for a single BTCUSDT research host running T0, T1, T2 and scheduled FreqAI training. This is a design/demand estimate only. No VPS, volume, IP, account resource, package, service, deployment, exchange connection, data import, training job or automation was created or started.

Paper-only remains mandatory. `AI_EXECUTION_ENABLED=false`. T0 remains an independent canonical data asset. No live orders.

## Source and branch pins

- Main repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Starting HEAD for this planning increment: `bc4af221e08aca577fadf3363b8f89c35086254a`
- T0/T2 source reviewed for sizing: prior G0.8-B source HEAD `43ba5a917f162dd5060bfd49bc57a89a9f1d88d8` (the later G0.8-B commit changed documentation only).
- T1 repository: `kenznguyen/binance-futures-collector`
- T1 branch/source HEAD: `f3bae0cfbc26aa694a4d6c9476965121818d3567`
- T1 `config.example.toml` blob: `3436a8b75dc827a9299c083e9af783c8a74196c3`
- T1 `README.md` blob: `5e03d3e00bb4b1fe6ed4ed389006e50d5683c5e3`
- T1 `src/config.rs` blob: `e07fd601986d7a8db18109e3179937579c425f98`
- T0 `market_data/store.py` blob: `4e1b0c54bd56455abe5be0e5c7d0807e63e0bc78`
- T0 `market_data/feeder.py` blob: `935d295ef42c94482a48ce6ccdc927ebfa4c7e22`
- T0 `market_data/api.py` blob: `81733c9b6de811cbebb2f5d472d41f37f337990c`
- T2 `freqai_bridge/http_candles.py` blob: `eb9aeccdf381e8a2ebc3450a7a31ae4e9da164ac`

## 1. Workload envelope

Planning assumption: one symbol (BTCUSDT), Binance USD-M public market data only, no dashboard exposure to the public internet, no live order execution.

### T0
- Two canonical timeframes: M15 and H1.
- Maximum historical read contract is bounded to 3,000 candles; API query cap is 2,000 expected slots.
- Feeder defaults: 5-second poll, 5-second close grace, 60-second lease TTL, 15-second heartbeat.
- T0 canonical candles are small relative to T1 raw tape. Exact database growth has not been measured on a replacement host.

### T1
- Explicit symbol whitelist must eventually be `["btcusdt"]`; current example `symbols=[]` collects all discovered USDT-M perpetuals.
- Existing settings include 500ms order-book updates, 50-level initial depth snapshot, 600-second snapshot interval, one-second flush, 64KB per-file buffer and REST polling of funding/OI/ratios/mark/index/premium metrics.
- Collector README reports approximately 40 GB/day for the entire ~500-symbol universe at 500ms. It does not provide a BTCUSDT-only measured rate.
- Provisional capacity envelope for BTCUSDT raw trades + order book + other streams: **0.5–2.0 GB/day**, explicitly an engineering planning range, NOT a measured result or vendor guarantee.
- At that range, 30 days = 15–60 GB; 90 days = 45–180 GB before filesystem, rotation, indexes/manifests or safety headroom.
- A separate benchmark must measure each stream and total bytes/day before any retention policy is finalized.

### T2 / FreqAI
- Current T0 HTTP client consumes M15 only, 1–32 bars per request; H1 is not consumed by the inspected client.
- The repository evidence reviewed does not establish a frozen `T0_M15_H1_DATASET_BUNDLE_V1`, a complete FreqAI training configuration, the selected estimator, actual feature matrix size, model artifact size or training duration.
- GPU requirement is therefore NOT ESTABLISHED. Size initial deployment for CPU-based tabular training; do not pay for a GPU before the estimator/benchmark proves it is needed.
- Training must be a separate, bounded, non-concurrent scheduled job and must not starve T0/T1 ingestion or T2 inference.

## 2. Recommended initial Scaleway profile

**Recommended budget-first profile for a bounded BTCUSDT paper/research workload:**
- Instance: **GP1-S**
- Compute: 8 vCPU, 32 GB RAM, up to 800 Mbps public bandwidth
- Region used for public price reference: Paris (PAR-1); actual zone availability must be checked in the account console before provisioning.
- Block storage budget: **500 GB total**, provisioned as separate volumes:
  - 80 GB OS / application / bounded logs
  - 20 GB T0 canonical database volume (dedicated mount; no T1 writes)
  - 300 GB T1 raw CSV volume
  - 100 GB T2 model artifacts / FreqAI staging and scratch volume
- Use the 5K NVMe Block Storage class for the initial design. Do not use the 15K class unless the selected instance's block bandwidth satisfies Scaleway's requirement and a benchmark shows the need.
- T0 and T1 remain separate volume/mount boundaries and separate service identities. This is logical/data-path separation, not independent physical fault domains: a single VPS remains one host failure domain.
- Do not place canonical T0 candles or T1 raw evidence in disposable scratch paths.
- No systemd/autostart or service activation is included in this plan. Start/stop policy needs its own approved deployment procedure.

### Why GP1-S first

The official current price table lists GP1-S at 8 vCPU / 32 GB / 800 Mbps and about €139.24/month. This provides materially more memory headroom than the previous 8 GB test VPS while keeping the first deployment below the cost of dedicated compute or GPU instances.

GP1 is a shared-vCPU class. Therefore training duration and CPU contention are NOT guaranteed by the nominal vCPU count. It is suitable as a cost-controlled first benchmark target, not a proven performance guarantee. If scheduled training exceeds its window or impacts ingestion/inference, move to a dedicated compute profile rather than raising unbounded process concurrency.

## 3. Storage and monthly cost estimate

Official Scaleway Product Catalog currently lists Performance Block Storage SSD at €0.000118 per GB-hour in PAR-1. Using Scaleway's 730-hour month convention:

- 500 GB × €0.000118 × 730 = **€43.07/month**.
- GP1-S instance = **about €139.24/month**.
- Estimated compute + 500 GB block storage = **about €182.31/month before VAT/tax and any separately billed IP or ancillary services**.

This is a planning estimate, not a checkout quote. Final pricing depends on the exact zone, volume class, billing configuration, taxes and account discounts. Verify in the Scaleway console before purchase.

If account quotas restrict block storage below 500 GB, validate/raise quota before provisioning; do not silently substitute ephemeral storage for canonical or raw data.

### Storage scenario

| T1 capture rate assumption | 30 days | 90 days | 300 GB T1 volume |
|---|---:|---:|---|
| 0.5 GB/day | 15 GB | 45 GB | ample headroom |
| 1.0 GB/day | 30 GB | 90 GB | ample headroom |
| 2.0 GB/day | 60 GB | 180 GB | usable, but benchmark and reserve required |
| 3.0 GB/day stress case | 90 GB | 270 GB | insufficient headroom for 90-day retention |

The 300 GB T1 volume is a provisional starting allocation, not permission to delete data at a retention boundary. The project has not approved any specific cleanup/deletion action in this scope. Define and approve retention only after measured per-stream growth, protected-data exclusions and recovery requirements are documented.

## 4. CPU and memory budget

Initial resource limits for the planning profile (not yet configured):

| Workload | RAM budget | CPU policy |
|---|---:|---|
| Ubuntu + system services + filesystem cache | 4–6 GB | reserve capacity |
| T0 feeder + SQLite + read-only API | 2–3 GB | low priority |
| T1 Rust collector | 2–4 GB | steady, bounded |
| T2 Core/AI runtime + API/dashboard services | 4–6 GB | latency-sensitive relative to training |
| One FreqAI training job | up to 12–14 GB | cap at 4 vCPU; low priority |
| Safety headroom | 2–4 GB | do not allocate |

The budget is intentionally conservative and totals within 32 GB only when training is single-job and bounded. Measure actual RSS, CPU saturation, I/O wait and swap pressure during a separately approved load test. No swap-off or kernel tuning decision is made here.

## 5. Scheduled FreqAI training proposal

Proposed initial schedule, pending data/model readiness:
- Frequency: once daily, at **03:00 Asia/Ho_Chi_Minh**.
- Maximum concurrent training jobs: 1.
- Initial resource ceiling: 4 CPU cores and 14 GB RAM.
- Initial wall-clock limit: 4 hours; exceeding it marks that training run failed and does not promote an artifact.
- Keep T0 feeder, T1 capture and T2 inference available; training must yield CPU and I/O.
- Validate input bundle ID, manifest, file hashes, coverage, training range, label horizon/purge, feature schema and model configuration before training.
- Publish a model only after independent artifact/provenance checks and calibration/risk acceptance.
- If training fails or the model is stale/invalid, AI strategy must fail closed to WAIT; Strategy Core remains separate and unchanged.

This schedule is a design proposal only. It is **not enabled**. A training cadence cannot be finalized until the immutable dataset bundle, selected estimator, training window, labels, purge/embargo, calibration and artifact contract are frozen. No FreqAI training was run.

## 6. GPU decision

Do not provision GPU in the first profile:
- Current repository review did not establish a GPU-dependent estimator.
- Scaleway L4 pricing is about €0.79/hour (~€574.87/month) before storage and taxes.
- A GPU would materially increase cost without evidence that the current FreqAI pipeline can use it.
- Revisit only if a selected estimator and a reproducible benchmark show CPU training misses the approved schedule.

## 7. Alternatives

| Profile | Compute | Approx instance/month | Intended use |
|---|---|---:|---|
| GP1-XS | 4 vCPU / 16 GB | €67.75 | insufficient headroom for concurrent all-layer workload + training; only reduced test profile |
| **GP1-S (recommended initial)** | **8 vCPU / 32 GB** | **€139.24** | all four layers with bounded CPU training |
| GP1-M | 16 vCPU / 64 GB | €279.96 | growth if training or data processing competes with live ingestion |
| COMPUTE3-X16C-32G | 16 dedicated vCPU / 32 GB | €341.78 | deterministic CPU-heavy training; higher-cost upgrade |

Add approximately €43.07/month for 500 GB of PAR-1 SSD Block Storage to the recommended profile, subject to final console quote.

## 8. Risks and unresolved prerequisites

1. T1 CSV importer pins the T1 merge-base SHA rather than the reviewed feature branch SHA; producer provenance must be reconciled before relying on imported T1 intelligence.
2. T1 BTCUSDT-only whitelist has not been applied or runtime-tested. The whitelist disables dynamic discovery/delisting checks; this trade-off needs an explicit configuration decision.
3. BTCUSDT-specific raw storage growth is unknown. Run a bounded capture benchmark before selecting retention.
4. T0 canonical data and T1 raw evidence on one host share a physical host failure domain despite separate volumes.
5. FreqAI estimator, model footprint, feature/label contract and training duration are not verified.
6. T0 API deployment/runtime parity is NOT VERIFIED; former VPS was deleted 2026-11-11.
7. T2 risk-gate enforcement, 1% equity margin cap, leverage and Kill Switch remain NOT VERIFIED on the inspected paper decision path.
8. Exact current zone capacity, block quota, taxes, flexible IP charges and checkout total must be confirmed in the owner's Scaleway account.

## Verdict

- Capacity architecture and initial profile: **CONDITIONAL PASS — planning only**.
- Recommended initial instance: **GP1-S, 8 vCPU / 32 GB RAM**.
- Storage design: **500 GB separate Block Storage volumes (80/20/300/100 GB)**.
- Estimated monthly compute + storage: **~€182.31 before taxes/IP/ancillary charges**.
- T1 BTCUSDT daily storage rate: **NOT VERIFIED**.
- FreqAI model/training runtime fit: **NOT VERIFIED**.
- GPU need: **NOT ESTABLISHED; do not provision initially**.
- VPS creation/deployment: **NOT AUTHORIZED by this planning approval**.
- Tests/workflows: **NOT RUN**.

## Non-actions

No VPS or storage resource was created; no payment, IP, SSH, firewall, package, service, configuration, deployment or exchange connection was changed. No T0 canonical DB access/mutation, T1 capture, T2 strategy execution, AI training, signal publication, order or cleanup/deletion occurred. T0 remains independent. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.
