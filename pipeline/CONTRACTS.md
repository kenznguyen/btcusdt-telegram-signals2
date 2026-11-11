# Paper pipeline v1 — implementation contract

BTCUSDT / binance / USDT_PERPETUAL only. All timestamps UTC ms; price, quantity,
rate and money values are decimal strings at JSON boundaries. No live-order API.
`pipeline.values` supplies bounded `number`, `stamp`, and stable `identity`.

## Intelligence snapshot

`schemaVersion:1, exchange:'binance', marketType:'USDT_PERPETUAL', symbol:'BTCUSDT',
windowStartMs, windowEndMs, availableAtMs, source, quality:'OBSERVED_ONLY',
fundingRate` (decimal string or null), `fundingAtMs` (int or null),
`openInterestBase` (string or null), `openInterestChangeBase` (signed string or null),
`takerBuyQuote`, `takerSellQuote`, `netTakerQuote` (strings or null),
`largeTradeQuote` (string or null), `observedLiquidationBuyQuote`,
`observedLiquidationSellQuote` (strings or null), `coverage` (object per stream),
`collectorCommit`, `inputFiles` (per-file SHA-256 provenance on new snapshots),
`snapshotId` (content hash).

Missing/unverified feeds remain null with explicit coverage; no on-chain whale
claims, zero-filling, or claims that observed liquidation messages are a full tape.
Every stream remains `complete:false`; continuity is `UNVERIFIED` unless aggregate
trade ID gaps are detected. Trade IDs and sample timestamps are deduplicated and
counted; liquidation rows have no event ID and are retained without claiming
exact deduplication. CSV has no heartbeat/disconnect record, so connection
continuity cannot be certified. The API reports per-feed freshness; trades use a
60s maximum age, funding 630s, and open interest 1,230s. Sparse liquidations are
`UNVERIFIABLE` for connection freshness. New snapshots pin collector commit and
SHA-256/size/row counts for each input file; legacy v1 snapshots remain readable
without file provenance. Intelligence importer writes snapshots atomically; no
credentials or trading calls.

## FreqAI prediction artifact

`schemaVersion:1, exchange:'binance', marketType:'USDT_PERPETUAL', symbol:'BTCUSDT',
timeframe:'15m', candleOpenTimeMs, candleCloseTimeMs, availableAtMs, trainedThroughMs,
modelVersion, strategyVersion, trainingCompletedAtMs, trainingDatasetVersion,
predictedReturn` (signed decimal string),
`doPredict:1, datasetVersion` (matches canonical M15 query used for decision).

Artifacts are input data, never executable code. Missing/invalid/outdated model
data yields WAIT. No manufactured predictions. FreqAI producer must use actual
model outputs and suppress native Freqtrade order signals.

## Decision

`evaluate(candle_window, intelligence, prediction, book, now_ms, *, target_base='0.001',
threshold='0.002', max_input_age_ms=60000)` ->
`{action:'WAIT'|'BUY'|'SELL',reason:str,intent:dict|null}`.
Inputs are server-resolved; clients never submit prediction/book data via the API.

Candidate intent fields: `intentId, symbol:'BTCUSDT',exchange:'binance',
marketType:'USDT_PERPETUAL',strategyVersion,modelVersion,datasetVersion,
targetPositionBase` (signed string), `limitPrice` (string), `decisionAtMs`,
`validUntilMs`, `inputSnapshotId` (intelligence hash), `mode:'PAPER'`.
BUY uses bestAsk, SELL bestBid for bounded marketable limit simulation.
Identity stable for the same strategy/model/candle/dataset/target intent, not attempt.

## Paper execution

`PaperLedger(db_path, *, max_position_base='0.01', fee_rate='0.0005')`.
Methods: `submit(intent,book,now_ms)->order`, `snapshot()->dict`,
`set_paused(paused:bool,now_ms)->dict`, `cancel(order_id,now_ms)->order`.
Public `read_snapshot(db_path)` uses read-only SQLite and never initializes state.
Explicit local initialization: `python -m paper_execution --db PATH`.
Snapshot: `mode:'PAPER',liveTradingSupported:false,paused,riskControl:{paused,killed,reason,updatedAtMs,mode,liveTradingSupported},positionBase,
realizedPnlQuote,feesQuote,orders:[...]` (bounded recent orders).
Order: `orderId,intentId,status,side,quantityBase,filledBase,remainingBase,
averagePrice,feeQuote,createdAtMs,updatedAtMs,mode:'PAPER',reason`.
Allowed states include REJECTED,OPEN,PARTIALLY_FILLED,FILLED,CANCELED.
Same intent ID/same payload returns original result, different payload raises
ValueError. SQLite transaction claims intent and updates position/fills atomically.
Paper fills cap to displayed contra liquidity within limit; one snapshot never
pretends exchange queue/latency certainty. No background refills or real orders.

Book input: existing Hummingbot normalized snapshot `{source:'hummingbot',
connector:'binance_perpetual',symbol:'BTCUSDT',observedAtMs,
bids:[{price,quantity}],asks:[...]}`; snapshot timestamp is retrieval time only.

## Common API / React contract

Root-owned module `pipeline.api:application`:
- GET `/health` public process health.
- GET `/v1/system` -> `{mode:'PAPER',liveTradingSupported:false,layers:[{level,name,status,detail}]}`.
- GET `/v1/candles` existing canonical query contract.
- GET `/v1/order-book?symbol=BTCUSDT` existing normalized Hummingbot contract;
  lets the APK use this common API with its read token.
- GET `/v1/intelligence` -> validated snapshot or `{available:false,reason}`; new snapshots include per-file capture SHA-256 provenance.
- GET `/v1/quality` includes T1 per-feed `status`, `freshness`, `ageMs`, `maxAgeMs`, `continuityStatus`, row counts and collector provenance. AI decision validates the full snapshot and currently uses fresh, duplicate-free trade flow with no observed trade-ID gaps as its T1 input. Funding, OI and liquidation are published as observed context and quality telemetry, not yet directional decision features. Strategy Core remains unchanged and does not consume T1, preserving its RSI/ADX/Smart-DCA rules. Missing/old feeds are reported, never silently zero-filled.
- GET `/v1/decision` -> `{action,reason,intent}` (AI/FreqAI stream).
- GET `/v1/signals` -> `{strategyCore,aiStrategy,mode:'PAPER',liveTradingSupported:false}`; streams are independent. Core consumes a versioned `STRATEGY_CORE_REPORT_PATH` artifact; missing or invalid artifact is WAIT.
- POST `/v1/paper/evaluate` accepts `{}` (AI default), `{source:'AI'}`, or `{source:'CORE'}`. Both routes resolve server-side data and submit to the same ledger/risk gate.
- GET `/v1/paper` -> ledger snapshot.
- POST `/v1/paper/evaluate` body `{}` -> `{decision,order:dict|null}`.
- POST `/v1/paper/pause` body `{paused:bool}` -> snapshot.
- POST `/v1/paper/cancel` body `{orderId:str}` -> order.
- POST `/v1/paper/kill` body `{enabled:true}` -> paper snapshot with persistent kill latch.
- POST `/v1/paper/reset-kill` body `{acknowledge:true,ready:true}` -> snapshot; generic Resume never clears the kill latch.

GET bearer uses MARKET_DATA_TOKEN. POST bearer uses separate CONTROL_TOKEN.
Both tokens only kept in frontend memory. Server config MARKET_DATA_DB,
INTELLIGENCE_REPORT_PATH,FREQAI_REPORT_PATH; Hummingbot server creds unchanged.
Missing layers/config => explicit unavailable/WAIT, not demo numbers. API never
syncs exchange candles or starts training in a request. Static React dashboard
served at `/control` (Vite base `/control/`) from built control_dashboard/dist.

## Shared risk latch and independent signals

`paper_execution.risk_control` stores the pause/kill latch in the same SQLite database as the paper ledger. `PaperLedger.submit` checks it after `BEGIN IMMEDIATE` and before creating a new order, so a kill action and an order submission serialize on the same database write lock. Kill is sticky: `set_paused(false)` cannot clear it. Reset requires both `acknowledge=true` and `ready=true`; this is an operator assertion, not an automated proof that all external systems are healthy. The current latch blocks new paper intents; it does not claim to cancel existing open paper orders or flatten positions.

Strategy Core and AI/FreqAI are separate signal streams. Core's producer contract is a validated JSON artifact at `STRATEGY_CORE_REPORT_PATH` (schema v1, `source=STRATEGY_CORE`, BTCUSDT Binance USDT perpetual M15, direction, strategy/data provenance, timestamps, signed target and limit price). AI remains the existing FreqAI evaluation. Both selected sources submit through `PaperLedger`, including the shared kill/pause latch and existing position/spread/visible-depth constraints. The adapter does not yet compute RSI/ADX/Smart-DCA itself; the upstream Strategy Core producer must publish the artifact.
