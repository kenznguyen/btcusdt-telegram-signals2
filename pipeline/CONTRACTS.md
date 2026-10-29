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
`snapshotId` (content hash).

Missing/unverified feeds remain null with explicit coverage; no on-chain whale
claims, zero-filling, or claims that observed liquidation messages are a full tape.
Intelligence importer writes snapshots atomically; no credentials or trading calls.

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
Snapshot: `mode:'PAPER',liveTradingSupported:false,paused,positionBase,
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
- GET `/v1/intelligence` -> snapshot or `{available:false,reason}`.
- GET `/v1/decision` -> `{action,reason,intent}`.
- GET `/v1/paper` -> ledger snapshot.
- POST `/v1/paper/evaluate` body `{}` -> `{decision,order:dict|null}`.
- POST `/v1/paper/pause` body `{paused:bool}` -> snapshot.
- POST `/v1/paper/cancel` body `{orderId:str}` -> order.

GET bearer uses MARKET_DATA_TOKEN. POST bearer uses separate CONTROL_TOKEN.
Both tokens only kept in frontend memory. Server config MARKET_DATA_DB,
INTELLIGENCE_REPORT_PATH,FREQAI_REPORT_PATH; Hummingbot server creds unchanged.
Missing layers/config => explicit unavailable/WAIT, not demo numbers. API never
syncs exchange candles or starts training in a request. Static React dashboard
served at `/control` (Vite base `/control/`) from built control_dashboard/dist.
