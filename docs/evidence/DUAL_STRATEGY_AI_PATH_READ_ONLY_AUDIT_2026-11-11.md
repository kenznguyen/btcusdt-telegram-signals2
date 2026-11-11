# AI Strategy independent signal and risk path — read-only audit

**Date:** 2026-11-11  
**Repository:** `kenznguyen/btcusdt-telegram-signals2`  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`  
**Reviewed source SHA:** `6ef0d7456b2791fae73bfea8855ee30482774673`  
**Disposition:** AI signal path PASS at source level; AI leverage/calibration/sizing BLOCKED / NOT IMPLEMENTED.  
**Mode:** read-only; no source or runtime changes.

## 1. Findings

| Area | Status | Evidence |
|---|---|---|
| Independent AI signal producer | PASS — source | `signal_snapshot()` calls `decide()` and `core_decide()` separately; test verifies Core WAIT does not suppress AI BUY |
| AI-specific ledger routing | PASS — source; integration coverage PARTIAL | Dual-mode evaluate route selects `AI_FREQAI`; factory and separate ledger tests exist, but no dedicated end-to-end AI evaluate-route test found |
| Shared Risk Engine | PASS — source; runtime NOT VERIFIED | AI submit path uses the same account equity, 1% margin, gross exposure, readiness, liquidity and Kill Switch checks when dual-ledger mode is active |
| AI 1x–3x dynamic leverage | BLOCKED / NOT IMPLEMENTED | API passes generic `LEVERAGE`; AI ledger only requires leverage > 0; no AI-specific range or dynamic value in decision/submit contract |
| Calibrated confidence and calibration provenance | BLOCKED / NOT IMPLEMENTED | Prediction artifact includes predictedReturn and training provenance, but no calibrated confidence/calibration version |
| Account-equity-based AI sizing | BLOCKED / NOT IMPLEMENTED | AI producer uses fixed `PAPER_TARGET_BASE` default 0.001 BTC; it does not size from current Account Equity and AI leverage |
| Paper-only FreqAI research boundary | PASS — source | dry-run restricted; native entry/exit signals disabled; `confirm_trade_entry()` returns false |

## 2. Source trace

### Independent signal generation

- `pipeline/api.py::signal_snapshot()` calls `decide(data, timestamp)` for AI and `core_decide(timestamp)` for Core as separate functions.
- `pipeline/decision.py::evaluate()` independently validates canonical M15 candles, futures trade-flow snapshot, FreqAI prediction provenance and order-book snapshot.
- `pipeline/test_api.py::test_core_producer_waits_on_incomplete_history_without_suppressing_ai` verifies Core WAIT while AI remains BUY.
- This confirms independent signal production at source level; it does not prove production runtime readiness.

### AI decision and sizing

- `pipeline/api.py::decide()` passes `PAPER_TARGET_BASE` (default `0.001`) to `pipeline.decision.evaluate()`.
- `pipeline/decision.py::evaluate()` accepts a fixed target base and threshold. It creates a positive or negative target position from the prediction direction; it has no account-equity or leverage argument.
- The decision path checks predicted return against a threshold and requires agreement with observed taker flow. It does not use calibrated confidence.
- `freqai_bridge/exporter.py::make_prediction()` emits predictedReturn, doPredict, model/strategy versions, training dataset provenance and training cutoff; no confidence or calibration metadata is emitted.

### Leverage and shared admission

- `pipeline/api.py::ledger()` pins Core to 13x but passes generic `LEVERAGE` to AI.
- `paper_execution/ledger.py::PaperLedger.__init__()` enforces Core exactly 13x; for AI it only enforces leverage is positive.
- Shared ledger admission computes the 1% current-equity margin budget and derives notional from `self.leverage`. Thus AI can be admitted at the generic configured leverage (default 13x) rather than a bounded AI-specific 1x–3x value.
- The shared engine rejects candidates exceeding the admission budget; it does not resize the fixed AI target.
- The API routes AI submissions to `AI_FREQAI` when dual-ledger mode is active. Before dual-ledger readiness it retains the legacy MANUAL path; persistent migration/cutover is not authorized, so runtime dual-ledger behavior remains NOT VERIFIED.

### Paper-only boundary

- `freqai_bridge/ChartProFreqaiResearch.py` is dry-run restricted, has no native entry/exit signals and refuses native trade entry.
- The pipeline decision produces PAPER intents. No live execution, exchange order or deployment path was enabled by this audit.

## 3. Test coverage

- Existing API test proves AI BUY is not suppressed by Core WAIT.
- Existing dual-ledger tests cover separate strategy ledgers and shared account risk primitives.
- Existing API tests verify AI scoped ledger factory construction.
- No dedicated end-to-end test was found for AI evaluate route → AI_FREQAI ledger submit.
- No tests enforce AI 1x–3x bounds, confidence calibration/provenance, or current-equity-based AI candidate sizing.

## 4. Next bounded task

Before AI implementation, prepare and obtain approval for a separate contract/TDD increment that:

1. Freezes the calibrated-confidence and calibration-provenance schema.
2. Freezes the selected AI 1x–3x leverage mapping and fail-closed behavior.
3. Sizes AI ENTRY/DCA from current reconciled Account Equity, selected AI leverage and the same execution limit price used by the ledger.
4. Passes the leverage/config snapshot into the AI reservation and rejects leverage outside the approved range.
5. Adds an end-to-end API test proving AI BUY can occur while Core is WAIT, writes only to AI_FREQAI ledger, and fails closed on missing calibration, invalid leverage, stale equity or Shared Risk Engine denial.

The shared 1% margin budget and Kill Switch remain authoritative. Missing/invalid calibration or leverage must block new ENTRY/DCA; do not infer a fallback to fixed target size or generic leverage.

## 5. Explicit limits

- This is a read-only source audit, not a test run or runtime verification.
- No AI code, calibration data, strategy config, DB schema, ledger state, VPS/T0 runtime, deployment, credentials or exchange state was changed.
- AI leverage/calibration/sizing changes require a separate bounded TDD scope and explicit owner approval.
- Persistent DB migration, account cutover/funding readiness, VPS activation and live execution remain NOT AUTHORIZED / NOT PERFORMED / NOT VERIFIED.
