# Dual-Strategy DS-03 — Core leverage and sizing implementation evidence

**Date:** 2026-11-11  
**Repository:** `kenznguyen/btcusdt-telegram-signals2`  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`  
**Final source SHA:** `6ef0d7456b2791fae73bfea8855ee30482774673`  
**Disposition:** **PASS — source and isolated CI scope only**

## 1. Owner-approved policy

- Strategy Core leverage is fixed at **13x**.
- Preserve existing leverage-adjusted ROE semantics and thresholds: TP +5, DCA -20, Soft SL -35, Emergency SL -90.
- Each new ENTRY and each exposure-increasing DCA uses a fresh margin budget equal to **1% of current reconciled Account Equity** at admission.
- Shared Risk Engine is authoritative and independently recalculates admission-time equity/margin before ACCEPT/REJECT.
- RSI, ADX and Smart-DCA signal rules are unchanged.
- AI leverage/configuration remains separate and is not modified by this increment.

## 2. Source changes

| File | Blob SHA | Change |
|---|---|---|
| `pipeline/core_strategy.py` | `c14e76f2cecb9f8aca54db263ded1ff17881cb24` | Fixed Core 13x; size ENTRY/DCA from fresh 1% account-equity budget; fail closed on unavailable equity |
| `pipeline/api.py` | `d3f587c795daa89b54beb5783b89f14acc189df0` | Pin Core ledger to 13x; pass only reconciled, risk-ready account equity to Core producer |
| `paper_execution/ledger.py` | `21ff7ce8446381baaa4102553fc8f69a8bbacbb3` | Enforce Core 13x; use shared 1% budget constant; include policy in risk-config version |
| `risk_policy.py` | `91b46513041033cbcd7e939ed081b71714c82ff3` | Shared constants: Core leverage 13x and order margin budget 1% |
| `pipeline/test_core_sizing.py` | `788ecb97fc0098209456749ef3c7b15f6f1819ec` | ENTRY/DCA budget, no-equity fail-closed, Core leverage guard, AI config separation |
| `pipeline/test_core_strategy.py` | `a0d5b46845d3fde006ed817fe21bdd8b6546c1d1` | Updated producer call contracts and Smart-DCA test naming |
| `paper_execution/test_dual_strategy_api_red.py` | `f93e5c59a007758329790a7d58b4fd899b9c8c5b` | Verify API passes reconciled account equity into Core producer |
| `.github/workflows/dual-ledger-red.yml` | `8b1620482dabd59d46e6f3f4e7ad66c178e520e8` | Include Core sizing tests in isolated compile and test gates |

## 3. Behavior and safeguards

1. Core ROE and stop/TP calculations use fixed 13x; generic `LEVERAGE` environment changes cannot alter Core.
2. Core API reads account equity through the read-only account risk snapshot only after dual-ledger readiness. It passes equity to the producer only when `riskReady=true`.
3. If account equity is missing, stale, unreconciled or not ready, Core may still report the signal direction but emits **no trade intent**. There is no fallback to local initial capital.
4. ENTRY and DCA candidate sizing uses the same visible limit price that the ledger will use to evaluate requested notional.
5. The shared ledger independently recomputes `current_account_equity * 0.01 * leverage` and rejects oversized candidates. Core cannot override a rejection.
6. Core ledger construction rejects any leverage other than 13x. AI retains its separate configuration path; no AI strategy behavior changed.
7. Persisted `initialMarginQuote` is no longer the DCA budget source.

## 4. TDD evidence

### RED

- Test-only source SHA: `92eb3f737d96e9edbfe0e8cf679ed64db79f0ba4`.
- Workflow: [42974245487](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42974245487).
- Compile: PASS.
- Focused suite: 229 tests executed; the new contract exposed 2 errors and 1 assertion failure against the old implementation. This is the expected RED result.
- Artifact ID: `13834382898`.
- Artifact digest: `sha256:247f12f8a84b9126e0c6b599dce8df50fd29755a943d022a0d0898f010f2303f`.

### GREEN

- Final source SHA: `6ef0d7456b2791fae73bfea8855ee30482774673`.
- Workflow: [42975606884](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42975606884), SUCCESS.
- Python: 3.12.16.
- Isolated paper-only preflight: PASS; no DB path, exchange API keys or external services configured.
- Compile contract: PASS.
- Focused contract: **237/237 PASS**.
- Full `paper_execution` regression: **300/300 PASS**.
- Artifact ID: `13834194926`.
- Artifact name: `dual-ledger-red-evidence-6ef0d7456b2791fae73bfea8855ee30482774673`.
- Artifact digest: `sha256:66403ab6b9c8079e2d9f3b04dcfc650709a64abd77e62554e6a54c2c101cd5c4`.

### T2 compatibility smoke

- Workflow: [42975606665](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42975606665), SUCCESS at the same exact source SHA.
- Pinned Freqtrade 2026.9 strategy loaded without exchange sync or database access.
- Artifact ID: `13835351582`.
- Artifact digest: `sha256:b76352b07321f3921dcdcf8cacfefd88103f366078188fb2a212648aadc17d0e`.

### Intermediate failures and corrections

- Run `42974877655` identified a missing `os` import after the first implementation commit.
- Run `42975018595` identified two further issues: the incomplete-window call retained the removed `initial_capital` parameter, and an unavailable account-risk snapshot incorrectly suppressed the signal result rather than failing closed only at intent creation.
- Both were corrected and covered by the final GREEN run. No failure was hidden or relabelled as PASS.

## 5. Review

- Correctness: fixed Core leverage and order sizing; producer and ledger use one shared policy; admission remains independently enforced.
- Readability: explicit helpers isolate limit-price selection and margin/quantity calculation.
- Architecture: shared constants are in a root-level policy module; no pipeline-to-paper-execution package dependency and no dependency added.
- Security: account equity is read through a read-only reconciled snapshot; missing readiness fails closed; no credentials or network/exchange access introduced.
- Performance: one bounded read-only account snapshot per Core decision; no unbounded work added.
- Result: no Critical or Required finding identified in this bounded self-review. Independent review was not required or performed.

## 6. Explicit limits

- DS-03 is **PASS only for source code and isolated GitHub Actions CI**.
- No backtest or statistical strategy-performance claim.
- No persistent database migration, account cutover, funding readiness activation, VPS/runtime action, deployment, exchange connectivity, or live trading.
- T0 canonical candles, lease/fencing, T0 runtime, T1 activation, credentials and exchange state were not modified.
- `AI_EXECUTION_ENABLED=false` and paper-only posture remain unchanged.

## 7. Next step

Conduct a read-only review of AI Strategy's independent LONG/SHORT signal path, its separate leverage/configuration propagation, and its Shared Risk Engine admission path. Do not change AI sizing, calibration, ledgers or runtime until a separate bounded TDD scope is approved.
