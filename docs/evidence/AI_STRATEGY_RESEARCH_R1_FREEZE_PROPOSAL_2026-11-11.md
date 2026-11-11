# AI Strategy Research Gate R1 — Proposal Evidence

**Date:** 2026-11-11  
**Repository:** `kenznguyen/btcusdt-telegram-signals2`  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`  
**Status:** PROPOSAL RECORDED / OWNER DECISIONS REQUIRED

## Scope

Prepared an R1 freeze proposal after owner approval of the R0 research protocol. This increment is documentation-only.

## Deliverable

- `docs/architecture/AI_STRATEGY_RESEARCH_R1_FREEZE_PROPOSAL.md`
- Commit: `82f770adc8b2936243174b97e3e83a1ee46f1f63`

The proposal gives owner-review recommendations for:
1. BTCUSDT 15m decisions with completed 1h context, using a verified immutable T0-derived read-only bundle.
2. A restricted trailing-only OHLCV feature inventory.
3. A candidate 4-hour fixed-horizon three-class directional label with a cost-aware neutral band.
4. Expanding chronological validation, separate later calibration, one untouched final holdout, and purge/embargo.
5. Evidence-based fee/spread/slippage/funding/latency/fill assumptions with base and adverse scenarios.
6. Always-flat, unchanged Core parity and simple trailing momentum baselines.
7. Pre-registered statistical, calibration and economic acceptance thresholds.

## Verification and limits

- File creation succeeded on the existing branch.
- No tests or workflow were run; documentation-only.
- The candidate bundle ID `T0_M15_H1_DATASET_BUNDLE_V1` is not asserted to exist or to be complete. Its exact digest, coverage and quality remain to be verified.
- No dataset was read/exported/copied; no T0 DB or runtime was accessed or changed.
- No feature values were computed; no label was generated; no model or calibration was trained; no backtest was run.
- No numeric horizon alternative, neutral-band value, fee rate, cost parameter, split timestamp, minimum sample count or acceptance threshold is frozen by this proposal.

## Gate status

| Gate | Status |
|---|---|
| R0 protocol | RECORDED |
| R1 proposal | RECORDED / OWNER DECISIONS REQUIRED |
| R1 freeze | NOT FROZEN |
| R2 offline experiment | NOT AUTHORIZED |
| GREEN-1..5 | NOT AUTHORIZED |

## Required owner decisions

D1 dataset/timeframe scope; D2 feature inventory; D3 primary label/horizon; D4 chronological split design; D5 execution-cost framework; D6 acceptance-threshold categories and pre-registration rule.

After those conceptual decisions, exact bundle and cost evidence must be verified before numerical parameters and timestamps can be frozen. R2 still requires separate explicit authorization.


## Owner decision update — SHA-256 and manifest

On 2026-11-11, the owner approved in principle a lightweight SHA-256 + manifest policy for AI Research dataset identity, integrity comparison and provenance tracking. Each immutable bundle is to have a stable ID, manifest digest and per-file SHA-256 values; experiment records should retain these with source-code SHA and configuration. Changed data must be represented as a new immutable version, not an overwrite. SHA-256 does not prove data correctness or provenance by itself.

This does not verify the existence or contents of `T0_M15_H1_DATASET_BUNDLE_V1`, nor authorize T0 data access/export/copy. D1 remains PARTIALLY DECIDED pending a separately approved read-only verification scope and actual bundle evidence. R1 remains NOT FROZEN; R2 remains NOT AUTHORIZED. No dataset or runtime was accessed, and no tests/workflow were run.
