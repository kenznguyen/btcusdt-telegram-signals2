# Phase 4 — independent verification of Phase 3 paper artifacts

Scope: **180-day offline OKX BTC/USDT:USDT** paper research only. Inherits Phase 3's fixed RSI + ADX + Smart DCA CORE rules and independent FreqAI LONG/SHORT research predictions. There are no exchange orders, no parameter changes, no Android APK changes, and no automatic 360-day unlock.

## Acceptance workflow

1. On Codemagic, select branch `feature/dual-strategy-phase4-artifact-audit-20261030`; run `dual-strategy-phase3-unit` first. The 7 new stdlib-only tests use explicitly synthetic fixtures and must not be presented as historical backtest results.
2. Only after tests pass, manually run `dual-strategy-phase3-native-research` with `PHASE3_DAYS=180`, `PHASE3_DETAIL_MINUTES=5`, and `PHASE3_DOWNLOAD_DAYS=220`.
3. The job runs real Freqtrade/FreqAI research, a 180-day CORE_ONLY/AI_ONLY/DUAL replay, and finally `quant_system.paper_audit`. A nonzero integrity-audit exit code fails the Codemagic job. The audit JSON and log are retained under `artifacts/phase3/paper/`.
4. Inspect `paper-180-independent-audit.json`, `paper-180-summary.json`, all 12 per-mode report/CSV files, native provenance JSON, forecast SHA, logs and actual event rows.

For existing artifacts copied to one machine, from the repository root:

```sh
python3 -m quant_system.paper_audit \
  --paper-dir artifacts/phase3/paper \
  --native-report artifacts/phase3/native/native-research-180.json \
  --predictions artifacts/phase3/native/freqai-native-predictions.csv \
  --out artifacts/phase3/paper/paper-180-independent-audit.json
```

### What the independent check verifies

- The three paper mode reports exactly match the aggregate report, with the same 180-day OKX source SHA and detailed-candle SHA.
- The genuine native research report has recorded CORE/FreqAI runtime success; the native prediction SHA matches the file received by the auditor.
- No event is duplicated or time-reversed, no trade exits before entry, no DCA is performed more than once per position, and all events are attributed to the correct strategy origin.
- Every nonempty event supplies finite positive expected/actual simulated fills, with `fill_difference = actual_fill_price - expected_fill_price`, a permitted simulated source and valid fees.
- The trade rows match closing events, the realized gross/net totals reconcile with event fees, and the final equity and maximum drawdown agree with the equity time series.
- Both CORE_ONLY and AI_ONLY have actual closed paper trades. A mismatch, missing file, nonfinite number, unsupported certification flag, or bad checksum fails closed.

Passing `artifact_integrity_verified=true` **only certifies internal artifact consistency**. It does not prove the native model was trained without future data, actual exchange execution prices, walk-forward OOS quality, independent Kotlin/Freqtrade parity or complete funding/mark/liquidation history. Outputs keep `ready_for_360=false` and `full_core_parity_certified=false`; live trading stays disabled.

### Scientific blockers

Do not change CORE thresholds to force DCA/stop observations. When market DCA or Emergency SL is absent, the audit records `MARKET_DCA_NOT_OBSERVED` / `MARKET_EMERGENCY_SL_NOT_OBSERVED` as remaining evidence gaps, not fabricated fills. High AI_ONLY/DUAL drawdown of at least half the initial balance is flagged for review without silently rewriting test performance. A fully separate chronological, leakage-free FreqAI walk-forward/OOS audit, risk-collateral investigation and funding/liquidation research are needed before any broader claims.

Codemagic is **build and research infrastructure**, not an always-on trading server. GitHub is the source of truth. Do not merge into `main` or build a release APK from this research branch without a separate regression and approval process.
