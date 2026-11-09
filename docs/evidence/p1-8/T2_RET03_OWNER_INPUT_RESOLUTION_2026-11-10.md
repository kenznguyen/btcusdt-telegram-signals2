# T2 RET-03 Owner Input Resolution — FreqAI / Strategy Decision Lineage

Date: 2026-11-10  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Work type: documentation-only, static source and consumer-dependency reconciliation  
Baseline branch HEAD: `d5921afe81fc4ad801f445726e42ca37ba939358`  
Status: **T2 STATIC CLASS/LINEAGE MAP COMPLETE — OWNER OBLIGATION INPUTS NOT PROVIDED — RET-03 OPEN — NO NUMERIC FLOOR SELECTED**

## 1. Scope and decision boundary

This record continues Stage A.3 of the T0 lifecycle residual plan. It examines the T2 FreqAI research/prediction bridge, its training and inference provenance contract, decision output, and paper-ledger dependencies. It distinguishes intermediate inference artifacts from model/reproducibility evidence and from final strategy/risk/accounting records.

This is a static inspection of committed repository source and documentation at the stated branch baseline. It does not access the external Freqtrade runtime, VPS, model directories, training files, actual prediction files, paper database, T0 endpoint, T1 services, T3/T4 runtime, backups, replicas, exports, recipients, or legal/contract sources. It does not establish that any configured path or model artifact currently exists.

Controlling boundaries:
- Option C — No Destructive Authority remains in force.
- No archive, expiry, cleanup, model pruning, compaction, vacuum, backup/replica removal, export mutation, or deletion is authorized or performed.
- T0 canonical data and its availability/recovery copies remain independently owned and protected. T2 consumes T0 only through the read-only HTTP contract; no direct T0 SQLite access is permitted.
- T2 model, research, inference, decision and paper state remain outside T0.
- CORE_LEDGER and AI_LEDGER remain separate strategy-owned accounting domains behind the shared account risk boundary.
- AI paper decisions and required T3 reconstruction/audit records remain protected; no lifecycle release may be inferred from an inference completion or consumer ACK.
- Independent human review is waived for this lifecycle workstream; the waiver does not waive substantive evidence, authority, technical controls or owner approval. Any owner assessment is not independent assurance.
- Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders.

## 2. Frozen source baseline

| Source | Blob SHA | Use |
|---|---|---|
| Branch HEAD | `d5921afe81fc4ad801f445726e42ca37ba939358` | Frozen repository baseline |
| Dataset/consumer inventory baseline | `9183b94bcb959a999029d9698d129af9b9f39b20` | Static T2 class map, consumer gaps, unknown runtime inventory |
| Dataset Consumer Contract design | `ef5e946b26ad17410023a79a765be73aeb198f0f` | Exact-version dependency, ACK/release separation, T2 obligations |
| Dual Ledger Contract | `e41e544efc6c1ae17596cb92a2cc38f86412ebb5` | CORE_LEDGER / AI_LEDGER isolation and shared risk boundary |
| T0–T1–T2 data-consumption architecture | `1b11883b9d2b93e3039d509ecaed98694afe430e` | T0 ownership and T2 read-only consumer boundary |
| FreqAI bridge README | `380a2c6abdfc2bc8b42281558f8a137d059c4820` | Training/inference provenance and output contract |
| FreqAI research config | `2ddccabc8a88a66ace251070c03d8623214291ac` | Model/training/retention-affecting configuration |
| FreqAI research strategy | `a7722f1148cf105c853deedaacb88edd14e671be` | Features, label horizon, prediction-only behavior |
| FreqAI exporter | `3b707174316d0c6b464ac947cbbe2d2fbee73682` | Prediction validation and atomic artifact replacement |
| T2 HTTP context | `9abe781340dc9b948c40c759d92f340da3e372c1` | Canonical inference-window acquisition |
| T2 decision pipeline | `e718756b415fc193a486900e7b84c2cf05e6a091` | Model/data validation and paper intent construction |
| Strategy Core signal adapter | `df5fbb59611bdd4fbb8224665f79655dd4433455` | Confirms separate Core signal source; not an AI inference artifact |
| Paper execution ledger | `0bc94ae0e704a69e253246a575991c1de436e0a4` | Strategy ledger, order, reservation, audit and event-journal persistence |
| T2 HTTP migration evidence | `8c450e7c66d4b16e277a0ae61f8cd5d1a0c9f9b0` | Historical CI evidence and explicit runtime/training limitations |
| RET-03/RET-07 gap analysis | `e26d056f9f0c2ea57a9951a650b29af11939c422` | Controlling retention-floor method and missing inputs |

The inventory baseline itself states that actual T2 model files, training artifacts, prediction files, backups, replicas, exports and local copies were not inventoried. Its source revision predates this Stage A.3 record; this analysis pins the current source blobs above where inspected.

## 3. T2 pipeline observed in repository

### 3.1 Canonical input and training-data distinction

- The current bridge obtains its inference candle window through T0's authenticated read-only `GET /v1/candles` contract. It does not open T0 SQLite, use a local cache, synthesize candles, or fall back to another venue.
- The FreqAI research README separately instructs the operator to download a historical training prehistory and run Freqtrade/FreqAI research/backtesting. Its sample date range is explicitly an example, not evidence that the data or model exists.
- The bridge requires a trainer-supplied provenance sidecar with an actual immutable model version, strategy version, training dataset manifest fingerprint, `trainedThroughMs`, and `trainingCompletedAtMs`. The code validates the declared fields and chronology but does not certify the training process or independently extract provenance from an arbitrary model.
- Therefore the T0 inference-window hash and the training dataset hash are distinct identities. The inspected sources do not prove that the historical training data came from T0, that a named T0 M15/H1 bundle was actually consumed, or that the model's training dataset can be reconstructed from the declared hash alone.

### 3.2 Features, labels and training configuration

The tracked strategy defines:
- relative price to rolling mean and relative volume to rolling mean;
- percentage price change and raw volume;
- day-of-week and hour-of-day;
- a future-return target using `close.shift(-label_period_candles) / close - 1`;
- a configured label horizon of 4 candles, two shifted candles, and indicator periods 14 and 28 on the configured 15m timeframe.

The research configuration records:
- FreqAI enabled, identifier `chart-pro-shadow-v1`;
- LightGBM research usage in the README;
- 30-day training period, 7-day backtest period and one-hour retraining interval;
- `save_backtest_models=false`;
- `purge_old_models=2` and `expired_hours=2`;
- a 20% non-shuffled test split and configured model parameters.

These values are source configuration, not proof of an executed training run, a complete dataset manifest, an approved retention rule, or a measured model-artifact inventory. In particular, `purge_old_models=2` and `expired_hours=2` are retention-affecting configuration fields that require explicit owner/policy reconciliation before any training runtime is treated as lifecycle-governed. Their effective runtime semantics and actual effects were not verified here. They are not authorized deletion instructions; this task did not change or execute them.

### 3.3 Inference artifact and decision path

- The strategy invokes FreqAI through `self.freqai.start()` and, in dry-run mode, publishes a prediction artifact.
- The exporter validates the real dataframe against the exact canonical inference candles, validates `do_predict == 1`, and binds the output to the current candle dataset version plus the separately declared training dataset version.
- The prediction artifact contains model/strategy versions, predicted return, candle timestamps, prediction availability time, training cutoff/completion time, inference dataset version and training dataset version.
- The configured prediction output defaults to `.data/freqai-prediction.json`. The writer creates a bounded temporary JSON file, fsyncs it, then atomically replaces the configured output path. This is a replaceable latest-output slot, not an append-only prediction history or an immutable evidence archive. The temporary-file cleanup in the writer is an implementation detail, not a general retention policy.
- On unavailable or invalid prediction/provenance/data, the strategy writes an unavailable artifact and keeps native entry/exit flags at zero; `confirm_trade_entry()` returns false.
- The separate paper decision function requires canonical candles, fresh observed trade-flow intelligence, an accepted fresh FreqAI prediction, and a fresh Hummingbot order-book snapshot. A forecast must exceed the configured threshold and agree in direction with net taker flow; otherwise the result is `WAIT`.
- A successful evaluation returns a bounded `PAPER` BUY/SELL intent with model version, strategy version, inference dataset version, intelligence snapshot ID, target position and source-derived decision/expiry times. The decision intent does **not** currently carry the explicit `trainingDatasetVersion`, `trainedThroughMs`, `trainingCompletedAtMs`, or numeric prediction value that were validated in the prediction artifact. This is a traceability gap for later reconstruction unless another immutable, exact-version link is established.

This is a description of the traced repository path, not proof that the pipeline is deployed, trained, continuously running, or connected to a live paper database.

## 4. T2 data and evidence class map

| Class | Examples / source evidence | Retention posture pending owner inputs |
|---|---|---|
| T0 canonical input | T0 BTCUSDT M15 candles and source/quality metadata consumed through HTTP | Protected/excluded from T2 lifecycle disposition; T2 has no authority over T0 payload or recovery copies |
| Training source data | Historical candles and any other source inputs used by Freqtrade/FreqAI training | Exact source, provider, dataset version, window, copies and consumer obligations NOT VERIFIED; retain/protect until identified |
| Feature and label materializations | Feature columns, shifted-candle expansions, target/label rows, preprocessing and train/test split outputs | Reproducibility evidence; do not classify as ephemeral merely because they can be recomputed |
| Training dataset manifests/fingerprints | Trainer-provided `trainingDatasetVersion` and required manifest identity | Preserve exact manifest bytes, digest, source references, transformation/config/code versions and lineage; actual manifest files NOT INVENTORIED |
| Model artifacts | FreqAI/LightGBM model files and immutable `modelVersion` | Model/reproducibility evidence; actual paths, versions, bytes, replicas and restore sets NOT VERIFIED |
| Training runs and experiments | Run identity, parameters, feature/label definitions, split, code/config versions, metrics and completion record | Research provenance; actual run registry/log inventory and replay/retraining obligations NOT VERIFIED |
| Backtest/evaluation/validation outputs | Backtest results, test split metrics, model diagnostics and any calibration/quality reports | Preserve while any performance, model-selection, risk, reproducibility or audit claim relies on them; actual artifact types/paths NOT VERIFIED |
| Training provenance sidecar | Default `.data/freqai-provenance.json` | Required bridge input; binds model and training dataset metadata; actual sidecar and its version history NOT INVENTORIED |
| Inference context | Default `.data/canonical-window.json` | Derived input snapshot with canonical dataset identity; downstream use and historical retention unknown |
| Latest prediction artifact | Default `.data/freqai-prediction.json` | Derived/ephemeral candidate only in provisional taxonomy; currently a replaceable latest-output slot and may be consumed by paper decision logic. Not proven disposable and not eligible for deletion |
| Final AI paper intent / signal | `pipeline.decision.evaluate()` output; model/strategy/data/snapshot references | Decision evidence; preserve exact source lineage and downstream reconstruction dependency |
| AI ledger and paper risk state | `AI_FREQAI` strategy ledger, paper orders, reservations, account risk state, event journal and audit | Protected operational/accounting and decision evidence; not cache, not a T2 ephemeral output, not eligible for class-wide deletion |
| T3 reconstruction/audit records | Paper decision, risk admission, order/fill/reconciliation and required audit/event records | Protected/excluded while needed for paper-outcome reconstruction and governance |
| T4 views/exports | Dashboard/read models and any durable report/export derived from T2/T3 | Actual deployed stores, exports, recipients and dependency edges NOT VERIFIED; preserve unknown copies |

### 4.1 Important distinction: prediction versus decision

A model prediction is not the same object as a final AI strategy signal, risk decision, paper order, fill, or ledger event. The prediction file can be replaced on a later inference cycle; the decision/ledger trail has a separate accounting and reconstruction purpose. A successful inference, a replaced JSON file, a consumed prediction, a completed evaluation, or a consumer ACK does not close all model, decision, replay, audit, or ledger obligations.

### 4.2 Model lineage propagation gap

The current prediction artifact validates and contains the training dataset fingerprint and training cutoff/completion timestamps. The traced final decision intent retains `modelVersion`, `strategyVersion`, inference `datasetVersion`, and `inputSnapshotId`, but not those explicit training-lineage fields or the prediction value. The static source set does not prove a separate immutable lookup that resolves each final intent back to the exact training manifest, model bytes, run, feature/label code and prediction artifact.

This is an evidence/reconstruction gap, not an authorization to change the signal schema in this task. It must be resolved by a separately scoped contract decision before claiming complete T2 decision reproducibility.

## 5. Producer-to-consumer and dependency findings

### 5.1 Confirmed source relationships

- T0 publishes canonical candle data; T2 reads through the versioned read-only HTTP boundary.
- Freqtrade/FreqAI training consumes a historical dataset through its research framework; exact actual source and immutable training dataset are not proven by the current repository evidence.
- The FreqAI strategy publishes a prediction artifact to the configured path.
- The paper decision function consumes the canonical candle window, T1 intelligence snapshot, FreqAI prediction and Hummingbot book snapshot.
- The paper execution subsystem has distinct `STRATEGY_CORE` and `AI_FREQAI` strategy identities, separate strategy-ledger rows, account-wide risk state/reservations and audit/event records. The Dual Ledger Contract requires independent accounting domains with one shared account risk boundary.
- The Dataset Consumer Contract says T2 dependencies should pin source, feature, label, model, experiment and backtest versions; that contract is design-only and is not an active registry.

### 5.2 Not established

The inspected repository does not establish:
- actual model files, model directories, model versions or their complete byte/copy inventory;
- actual training dataset manifest bytes, exact data source, dataset bundle ID used by each training run, or training-data completeness;
- actual feature/label materialization files, preprocessing state, normalization state or split artifacts;
- actual training-run/experiment registry, metrics, calibration/validation artifacts, model-selection rationale or retraining lineage;
- actual prediction/provenance/context files, rotation/overwrite history, consumers, backup/replica/export copies or recipient set;
- whether a given prediction was consumed by a paper decision, which final intents/orders depend on it, or the exact immutable link from intent to training dataset/model/run;
- complete consumer/dependency registrations for replay, retraining, evaluation, backtest, paper execution, T3 reconstruction and T4 reports;
- current paper database path, initialized schema, row population, active AI ledger state, migration version or runtime;
- source-backed legal, contractual, audit, security, incident or recovery holds and their competent release authorities;
- class-specific start events, positive terminal events, numeric minimum durations or approved owner/custodian.

The static Dataset Consumer Contract is explicitly NOT IMPLEMENTED / NOT ACTIVE. No absence of a registry record can therefore be used as proof of no dependency.

## 6. RET-03 owner-input matrix for T2

| Required input | Evidence currently available | Missing owner/source input | Status |
|---|---|---|---|
| Purpose by class | Research, model training, prediction, paper decision and ledger roles are visible in code/docs | Exhaustive owner-confirmed purpose for each model, run, dataset, prediction and derived artifact | PARTIAL / NOT VERIFIED |
| Authoritative obligation source | Repository contracts and configuration only | Owner-approved research/replay/reproducibility, operational, audit/security/incident, contractual or competent legal determination where applicable | NOT PROVIDED |
| Accountable owner/custodian | T2 bridge, Freqtrade/FreqAI and paper execution components identified | Accountable owner and custodian for training data, model/run artifacts, predictions, paper decisions and every copy | NOT PROVIDED |
| Exact object/version scope | Hash fields and version fields are defined in code | Actual manifest, model bytes, run ID, feature/label revision, prediction ID, exact file/object/copy/time range and recipient scope | PARTIAL / NOT VERIFIED |
| Training source and lineage | README requires training manifest fingerprint; code validates declared `trainingDatasetVersion` | Actual training source/provider, immutable dataset manifest bytes, source completeness, transformation and feature/label provenance | NOT VERIFIED |
| Start event | Candle event timestamps, training cutoff and completion fields exist | Owner-approved obligation start semantics for source data, training run, model publication, prediction, signal and ledger event | OPEN |
| Terminal event | No class-specific terminal event established | Positive authoritative closure for replay, retraining, model validation, decision reconstruction, audit, incident and recovery obligations | OPEN |
| Numeric minimum duration | No approved floor in inspected T2 source | Source-backed minimum duration and rationale per object/obligation; no numeric value supplied | NOT PROVIDED |
| Reproducibility/replay | Model and dataset fingerprints are required at bridge boundary | Accepted deterministic replay/retraining standard, dependency closure, exact source availability and model reproducibility evidence | NOT PROVIDED |
| Model retention controls | `purge_old_models=2`, `expired_hours=2`, `save_backtest_models=false` exist in config | Owner-approved meaning, authority, scope, interaction with reproducibility/holds, actual runtime behavior and resulting object inventory | OPEN / NOT VERIFIED |
| Consumer dependency closure | Decision and paper ledger consumers are visible in code | Complete exact-version consumer register, run-to-intent-to-ledger links, release authority and evidence | NOT VERIFIED |
| T3/T4 reconstruction | Architecture expects paper reconstruction and read-only views | Exact downstream records/reports and proof of all dependencies/copies/recipients | NOT VERIFIED |
| Copy/backup/restore graph | No complete T2 copy graph in repository inventory | Actual model/data/artifact directories, mounts, replicas, backups, snapshots, caches, exports, restore sets and external copies | NOT VERIFIED; no inventory performed |
| Holds and legal/contract scope | No scoped T2 hold determination in inspected records | Competent owner/legal/security/audit authority, exact affected scope and release evidence where applicable | NOT PROVIDED |
| Trusted time and ordering | UTC millisecond fields and timestamp validation exist | Trusted-time source, uncertainty, ordering, immutable run/decision event proof and V07/V08-compatible terminal evidence | OPEN / BLOCKED |
| Evidence compliance | SHA-256 manifest and provenance fields are required by contract | Actual immutable manifest, model/run/decision binding, custody, integrity verification and complete reconciliation | PARTIAL / NOT VERIFIED |
| Owner disposition | No T2-specific floor/TTL approval found | Explicit class/object-specific policy decision and any numeric value, tied to exact version and scope | NOT PROVIDED |

## 7. T2-specific owner questions

Before any finite RET-03 floor could be proposed, the owner must provide or identify authoritative answers to:

1. **Training source:** For each model/run, which exact provider and immutable dataset bundle were used? Was the training data sourced from T0, another exchange/provider, or a mixed set? What proves the exact window, completeness and corrections?
2. **Manifest:** Where are the actual training manifest bytes and their immutable version/digest? How are source rows, feature/label transformations, code/config revisions, splits and model output bound together?
3. **Features and labels:** Which feature/label definitions, normalization/preprocessing steps, shifted windows and future-label availability are required to reproduce each model? What exact event closes the replay/retraining obligation?
4. **Model artifacts:** What exact model bytes, versions, framework versions, training run IDs and model lineage are retained? Which artifacts are needed to reproduce or explain a historical AI decision?
5. **Evaluation:** Which backtests, holdout metrics, calibration/quality checks, experiment comparisons and model-selection reports are relied on by any strategy/risk/performance claim? Are any artifacts intentionally not saved by current configuration?
6. **Pruning configuration:** Who approved `purge_old_models=2` and `expired_hours=2`, what exact FreqAI runtime semantics apply at the pinned version, and how are protected models excluded from pruning while obligations/holds remain? No pruning action is authorized by this question.
7. **Prediction-to-decision binding:** What immutable identifier links each prediction artifact, its training manifest/model, final intent, AI ledger event, risk decision, order/fill and T3 reconstruction record? How is the missing explicit training dataset fingerprint/cutoff propagated or independently resolved?
8. **Prediction history:** Is the single configured JSON output intended only as a transient handoff or as evidence? If transient, what immutable downstream record preserves all material fields needed for later reconstruction? No such proof was established here.
9. **Consumer closure:** Which consumers use each training dataset, model, experiment, prediction, signal or report for replay, evaluation, paper execution, reconciliation, audit or dashboard export? Who can attest to exact dependency release?
10. **Start/end and duration:** What exact source-backed event starts and ends each obligation, including recurring retraining, new model successors, late corrections, incident investigations and reopened decisions? What authoritative basis supports any minimum duration?
11. **Copies and holds:** Which local paths, containers, caches, replicas, backups, restore sets, exports and external recipients contain each object? Which legal/contractual/security/audit/recovery holds apply, and who can release them?
12. **Evidence custody/time:** Which trusted time source, ordering and evidence-custody contract proves training completion, model publication, prediction, decision and terminal events under the still-open V07/V08 requirements?

If an authoritative source or competent owner input is absent, the answer remains OPEN / RETAIN / FLOOR_NOT_ESTABLISHED. No value is to be inferred from the config or framework defaults.

## 8. Retention posture pending owner inputs

- **T0 source candles:** protected and outside T2 lifecycle authority.
- **Training inputs, features, labels, manifests, models, runs and evaluation evidence:** preserve exact lineage and all potentially material reproducibility artifacts until obligations, consumers, copies and holds are established.
- **Prediction/provenance/context JSON:** not proven disposable. The prediction output path is replaceable and the final intent does not currently carry all training-lineage fields; preserve/secure the relevant exact versions and resolve the lineage gap before treating any prediction as ephemeral.
- **AI paper intents, ledger, reservations, risk state, orders, fills, event journal and audit:** protected; not candidates for class-wide cleanup or deletion.
- **T3 reconstruction and governance evidence:** protected while required for paper-outcome reconstruction, audit or authority.
- **Unknown model/data/artifact files, copies, exports and recipients:** protected / BLOCKED_UNKNOWN until separately inventoried and adjudicated.
- **`purge_old_models` and `expired_hours`:** configuration observations only. No model-pruning execution or policy inference is authorized. Any future training execution must first reconcile these settings with approved retention floors and model-reproducibility obligations.

A successful model training run, newer model publication, prediction replacement, prediction consumption, paper evaluation, order expiry, consumer ACK, or absence of recent reads does not by itself establish an end event or deletion eligibility.

## 9. Stage A.3 outcome

**T2 product and dependency map:** DOCUMENTED for the tracked FreqAI bridge, decision pipeline, paper-ledger contracts and their declared interfaces.

**T2 obligation resolution:** NOT COMPLETE. Actual training inputs/manifests, model/run/evaluation artifacts, prediction history, model-to-decision lineage, consumer/copy inventories, owner authority, holds, terminal events and duration bases are not established by the inspected repository evidence.

**Traceability finding:** the inference artifact validates a training dataset fingerprint and training timestamps, but the final decision intent does not currently carry those fields. An immutable external lookup binding the intent to the exact training manifest/model/run was not found in the inspected source set.

**Configuration finding:** `purge_old_models=2` and `expired_hours=2` are present in the research config. Their runtime semantics and actual effects are NOT VERIFIED; they are not an approved retention policy and were not executed or changed.

**RET-03 for T2:** OPEN — FLOOR_NOT_ESTABLISHED — NO NUMERIC FLOOR / TTL SELECTED.

No T2 object is made deletion-eligible. No inference is made that predictions, models, features, experiments or training data may be deleted after use. The Dataset Consumer Contract remains design-only; no consumer registry or complete dependency closure is established.

## 10. Verification, provenance and limits

- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Source baseline HEAD: `d5921afe81fc4ad801f445726e42ca37ba939358`.
- Exact source blobs are listed in §2.
- Work performed: GitHub repository document/source retrieval and static documentary comparison only.
- Tests: **NOT RUN**; this increment changes documentation only.
- GitHub Actions: **NOT DISPATCHED**; no workflow run or artifact is claimed for this increment.
- FreqAI training/backtest, model loading, prediction execution and forecast-quality evaluation: **NOT RUN**.
- VPS, Freqtrade runtime, model directories, training files, prediction/provenance files, paper DB, T0 endpoint, T1/T3/T4 runtime, backups, replicas, exports and recipients: **NOT ACCESSED**.
- Operational dataset/model/copy/consumer inventory: **NOT PERFORMED**.
- Legal/contractual determination: **NOT PERFORMED**.
- Source code, workflow, schema, API, adapter, config, runtime, permissions, credentials and data: **UNCHANGED**.
- Model pruning, archive, expiry, cleanup, compaction, vacuum, backup/replica removal, export mutation, restore, staging and deletion: **NOT AUTHORIZED / NOT EXECUTED**.
- Option C, independent-review waiver, T0 independence, separate ledgers, paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.

**Final status: STAGE A.3 DOCUMENTARY CLASS/LINEAGE MAP COMPLETE — T2 RET-03 OPEN — OWNER INPUTS NOT PROVIDED — NO NUMERIC FLOOR OR DESTRUCTIVE AUTHORITY.**
