# T0 Scope Minimization Review — Personal-Use Baseline

- Date: 2026-11-10
- Baseline HEAD: b7b79449f6605654c7768e18ca08bb59799e2755
- Review: read-only source/document inventory and scope classification.
- Principle: preserve progress; reduce active scope, not historical evidence. No deletion or implementation change.

## 1. Minimal active T0 responsibility

1. Acquire canonical Binance USD-M BTCUSDT M15/H1 candles without exchange API keys.
2. Validate market identity, timeframe, timestamps and OHLCV.
3. Persist canonical candles through a single fenced writer/lease with fail-closed recovery.
4. Expose a bounded read-only Candle API to authorized consumers.
5. Preserve canonical data and recovery copies; no destructive lifecycle automation.
6. Retain regression tests for writer fencing, lease, recovery, integrity, API contract and consumer compatibility.

This is a proposed active-scope baseline, not a claim that every capability is production-qualified.

## 2. Source component classification

| Component | Classification | Recommendation |
|---|---|---|
| market_data/feeder.py and feeder_service.py | T0 CORE | Keep; do not simplify before behavior and tests are mapped. |
| market_data/store.py | T0 CORE | Keep as canonical candle contract boundary. |
| market_data/storage.py | CORE + OPTIONAL ADAPTER SWITCH | Keep SQLite as default; PostgreSQL remains opt-in/not selected for active operation. |
| market_data/api.py | T0 CORE | Keep bounded read-only API; internal-only posture until public exposure is approved. |
| market_data/write_gateway.py | CONDITIONAL | Park from active path unless call-graph evidence proves it is required by the canonical writer. Do not remove yet. |
| market_data/postgres.py, migrations and PG tests | OPTIONAL BACKEND | Park provider/migration work; preserve adapter and tests as regression evidence. |
| market_data/kraken_spot.py, kraken_spot_store.py, kraken_spot_api.py and tests | SEPARATE RESEARCH DOMAIN | Keep isolated and explicitly non-canonical; do not merge into Binance schema, feeder, API or readiness denominator. |
| market_data/binance_connectivity_probe.py | SUPPORT TOOL | Keep as optional diagnostic, not part of always-on ingestion or production proof. |
| market_data/sync.py | CONDITIONAL | Keep for explicit backfill/sync only; verify consumers/schedules before deprecation. |
| initialize_sqlite.py, migrations.py and migrations | CORE SUPPORT | Keep; never trigger destructive maintenance implicitly. |
| T0 tests | CORE EVIDENCE | Keep full regression denominator; do not reduce tests to create an appearance of simplicity. |

Source blobs inspected: README 660a2f0f4f88c0de4fa8c1be3c4af96df282de0e; feeder 935d295ef42c94482a48ce6ccdc927ebfa4c7e22; service bdcecf6bc98a2ff070f83098d2c50154a160c99c; store 4e1b0c54bd56455abe5be0e5c7d0807e63e0bc78; storage 13fe1ae01ebb5318b69e69eef3e512d207f74c49; API 81733c9b6de811cbebb2f5d472d41f37f337990c; postgres 2fe27fe2d066dda0c192a381b72d27404487b800; write_gateway b2029d9db15fe39dcbe575acfeb6df1b16e16acd; Kraken adapter d8191606d27617f964f23736e07fb7fe7458dc39; Kraken store 1736935cf143c11f0789651b5ef80a1821aabbb8.

## 3. Architecture/document classification

| Document family | Classification | Recommendation |
|---|---|---|
| Shared Data Foundation | Cross-layer parent architecture | Keep as parent; future capabilities are not automatically active T0 requirements. |
| T0 Read-only Candle Contract and T0/T1/T2 consumption architecture | CORE CONTRACT/BOUNDARY | Keep as authoritative interface and ownership rules. |
| HTTPS front-door and domain/DNS criteria | FUTURE DEPLOYMENT OPTION | Park at D0. No domain, public TLS, proxy, firewall or public endpoint required for current internal/test posture. Keep as one linked future package. |
| Evidence Object/Checkpoint Contract and G0-G3 | OPTIONAL ASSURANCE WORKSTREAM | Park feature expansion; preserve contract, synthetic code and G3 manifest. G2 exact-SHA execution NOT VERIFIED; G3 independent review PENDING. |
| TSA/WORM, multi-TSA, Root A/Root B designs | L4-EXTENDED / SEPARATE EVIDENCE | Preserve records; stop expanding under T0 absent a separately approved claim/threat model. |
| PostgreSQL provider/role and atomic writer designs | OPTIONAL BACKEND | Park; SQLite remains selected default. |
| Lifecycle policy, consumer, deletion, copy/backup contracts and cross-reviews | GOVERNANCE REFERENCE, NOT RUNTIME | Preserve; freeze expansion while Option C applies and runtime inventory is incomplete. No registry, scheduler, retention timer, archive or deletion automation. |
| Forward Evidence Capture/Retention | SEPARATE PROJECT; T0 PAUSED | Keep separate; no T0 implementation or provider selection. |
| Daily Baseline/Epoch/Reconstruction | SEPARATE DOMAIN / CLAIM-DEPENDENT | Do not import into canonical candle service without explicit ownership/consumer evidence. |
| Runtime evidence, connectivity probe and Candle Contract review | HISTORICAL EVIDENCE | Preserve exact SHA and experimental/official labels. |

Document blobs inspected: Shared Data Foundation 18f8566723b95c4b38586e3848bde5305295a4dc; HTTPS design bd8d0f7dff159494fd954f5f14c7949b74e0c607; API domain criteria c647911d0e6ad36320e2ec03a95ee4247df9c475; Candle Contract e4ce9e30b64c73610369dcfeeb8d76dd88f99be9; T0/T1/T2 architecture 1b11883b9d2b93e3039d509ecaed98694afe430e; checkpoint contract 0d98a3dcbb0d403b213b5efcae0c882ac5461578; lifecycle policy 9fd46c029cff643ccc35492fd09620581f6eff35; consumer contract ef5e946b26ad17410023a79a765be73aeb198f0f; consumer inventory 9183b94bcb959a999029d9698d129af9b9f39b20; copy lifecycle 639e5ee5b5a78130cc523a4bcab8b77c0a0a5463; deletion safety e055d88308d8576c5c6826e12280b847f5ec5717; lifecycle cross-review 3d6d8505da43d755d35efe4ac44e580e541a21ae; forward evidence protocol b2ae6ec3ea68d3992d5e1fb63047085ca2a62dc2.

## 4. Findings

- SM-01 HIGH — Active-scope inflation: TSA/WORM, Root A/Root B, public HTTPS, PG qualification and multi-region DR must not be treated as prerequisites for a personal-use T0.
- SM-02 HIGH — Domain mixing: Kraken Spot code exists under market_data but is a separate research dataset, not canonical Binance USD-M BTCUSDT.
- SM-03 HIGH — Evidence workstream expansion: G0-G3 is extensive and G2 exact-SHA execution is unverified. Freeze new features; preserve artifacts and complete only already-approved gates.
- SM-04 MEDIUM — Alternative backend complexity: PostgreSQL is acceptable only as an opt-in isolated adapter while SQLite remains default.
- SM-05 MEDIUM — Public API over-design: DNS/domain/proxy planning is premature while public exposure is not approved.
- SM-06 HIGH — Lifecycle framework proliferation: preserve governance documents but do not turn them into active registry/scheduler/retention services under Option C.
- SM-07 HIGH — T0/forward-evidence conflation: Root A/Root B is a separate evidence product and T0 is paused/out of scope there.
- SM-08 MEDIUM — Recovery design leakage: Daily Baseline and dual reconstruction must not silently become T0 candle requirements.
- SM-09 HIGH — False simplification risk: do not remove lease fencing, fail-closed recovery, canonical validation, read-only boundaries or regression tests.
- SM-10 HIGH — Premature cleanup: no deletion is authorized; retirement requires call graph, imports, workflow, test, consumer, runtime and evidence dependency mapping plus explicit approval.

## 5. Proposed roadmap

### KEEP ACTIVE
- Binance USD-M BTCUSDT M15/H1 canonical SQLite path.
- Single fenced writer/lease, recovery and integrity.
- Read-only Candle API and T2 consumer contract.
- Core tests and paper-only guardrails.

### PARK / FREEZE — DO NOT DELETE
- PostgreSQL provider/migration work; Kraken Spot research path; public HTTPS/DNS/proxy deployment.
- Checkpoint G0-G3 feature expansion after current gates; TSA/WORM/multi-TSA and Root A/Root B.
- Lifecycle registry/scheduler/archive/retention implementation.
- Daily Baseline/dual reconstruction integration into T0.

### REMOVE FROM ACTIVE T0 ACCEPTANCE DENOMINATOR
- Second-exchange truth corroboration; WORM/TSA prerequisites for basic ingestion/API; SaaS/commercial controls.
- Public endpoint before an exposure decision; PG provider qualification while SQLite is selected.
- Multi-region DR or D3/D4 proof without an explicitly approved matching durability claim.

### PROTECT
- Canonical source/market identity; candle schema/time/quality validation; fenced writer/lease.
- Fail-closed recovery/integrity; read-only consumer boundary; bounded/authenticated API.
- Regression tests and exact-source evidence; canonical data and recovery copies.
- No automatic deletion/expiry after use.

## 6. Next safe work

1. Build a dependency map for PARK candidates: imports, runtime entry points, GitHub workflows, tests, consumer references and evidence references. No removals.
2. Reconcile active README/architecture index to label parked options as optional/not active without rewriting historical evidence.
3. Only after dependency mapping, prepare a separate retirement proposal for genuinely unused modules. Do not combine proposal with deletion.
4. Keep G2 exact-SHA and G3 independent-review blockers visible; do not bypass them by changing the acceptance denominator.

## 7. Status and limitations

- Scope classification: PASS — documentary/source inventory only.
- Active T0 baseline: PROPOSED; owner ratification required before source/runtime scope changes.
- Source dependency/call graph: PARTIAL; not fully traced.
- Live consumer/runtime inventory: NOT VERIFIED.
- PostgreSQL provider/production qualification: NOT SELECTED / NOT VERIFIED.
- Kraken Spot live consumer status: NOT VERIFIED.
- Public HTTPS deployment: NOT DEPLOYED / NOT AUTHORIZED.
- Checkpoint G2 exact-SHA execution: NOT VERIFIED; G3 independent review: PENDING.
- L4-Minimum operational acceptance: BLOCKED / NOT VERIFIED.
- No source/test/workflow/schema/runtime/VPS/database/provider/key/permission change; no tests or workflow dispatch; no archive, vacuum, compaction, backup expiry, replica removal, cleanup or deletion.
- Option C remains; AI_EXECUTION_ENABLED=false; paper-only; no live orders.

Final disposition: keep proven T0 core small; park optional assurance, alternate backend, research and public-deployment tracks; preserve history and data; require dependency evidence and explicit approval before any retirement or source change.