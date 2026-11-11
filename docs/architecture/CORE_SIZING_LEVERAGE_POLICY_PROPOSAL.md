# Strategy Core sizing and leverage policy — owner decision proposal

**Status:** PROPOSAL ONLY — no Core sizing/leverage change authorized  
**Date:** 2026-11-11  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`  
**Scope:** Resolve DS-03 without changing RSI / ADX / Smart-DCA signal rules.

## 1. Why a decision is required

The current Strategy Core source (`pipeline/core_strategy.py`, blob
`b4266fc05ea41355ba9dcf6f15cb7b5a6d3800b0`) contains:

- `LEVERAGE` default `13`;
- `ENTRY_MARGIN_PCT` default `0.50` (50% of the producer's equity basis);
- `DCA_MARGIN_RATIO` default `1.00`;
- ROE, stop/threshold and DCA calculations that depend on `LEVERAGE`;
- initial ENTRY quantity derived from `account_equity * ENTRY_MARGIN_PCT * LEVERAGE / close`;
- DCA quantity derived from `initialMarginQuote * DCA_MARGIN_RATIO * LEVERAGE / close`.

The shared paper ledger (`paper_execution/ledger.py`, blob
`38f71f974068eb12c56dd2174a4200d07c4c98bf`) independently checks each
exposure increase against admission margin of 1% of current account equity and
computes admission notional using the ledger's leverage. Thus the producer's
50% margin sizing can exceed shared admission by a wide margin and be rejected.
The producer and ledger also need one consistent, versioned leverage input;
otherwise signal ROE math, requested notional, reservation and simulated margin
can disagree.

## 2. Non-negotiable constraints already established

1. Preserve RSI + ADX + Smart-DCA signal rules and their thresholds unless the
   owner separately approves a strategy change.
2. Shared Risk Engine remains authoritative for every Core and AI candidate.
3. Every new ENTRY and every exposure-increasing DCA is capped at a margin
   reservation of 1% of current account equity at admission time.
4. Core and AI ledgers remain separate; risk and Kill Switch remain account-wide.
5. Paper-only. `AI_EXECUTION_ENABLED=false`; no live exchange orders.
6. Do not infer a Core leverage range from the AI 1x–3x dynamic sizing policy.
   That policy is an AI-specific decision and does not automatically authorize
   the same range for Core.
7. No persistent account migration, cutover, VPS activation or deployment is
   part of this decision.

## 3. Decisions required from owner

### D1 — Core leverage policy

Choose one policy; none is selected by this proposal:

- **Fixed leverage:** owner supplies one explicit Core leverage value.
- **Bounded configurable leverage:** owner supplies minimum, maximum and
  selection rule. The rule may be static per configuration or depend on a
  separately specified measurable input.
- **Dynamic leverage:** owner supplies the formula, bounds, inputs, calibration
  requirements and fail-closed conditions. This is the most complex option and
  must not reuse AI confidence without separate evidence.

The existing default 13x is not treated as approved merely because it is in
source. Missing or invalid approved leverage configuration must not silently
fall back to 13x.

### D2 — Meaning of ROE-dependent Core rules

Core uses leverage in `_roe()` and `_threshold()`. A leverage change therefore
changes the price distance at which TP, DCA, soft-stop and emergency-stop
conditions trigger, even if RSI/ADX rules remain unchanged.

Choose whether to:

- preserve current leverage-adjusted ROE semantics and explicitly accept that
  approved leverage changes alter price thresholds; or
- redefine those risk thresholds in price-return terms independent of leverage,
  which is a Strategy Core behavior change and requires separate strategy
  approval plus parity/backtest evidence.

No threshold semantics are changed by this proposal.

### D3 — ENTRY and DCA sizing source

Proposed invariant for implementation after approval:

- The producer may calculate a candidate target, but it must not authorize a
  margin amount above the Shared Risk Engine budget.
- Shared Risk Engine computes the admission-time margin budget as
  `account_equity * 0.01` independently for each exposure-increasing ENTRY/DCA.
- The same approved leverage/config version is used by producer, ledger,
  reservation and paper fill accounting.
- DCA must receive a fresh admission-time 1% budget; it must not inherit a
  50%-of-equity initial margin basis.
- No order may be increased after the shared engine rejects it. The producer
  must not silently shrink/rewrite the strategy target without an explicit
  sizing contract.

Owner confirmation is required that the 1% cap is also the intended fixed
budget per Core DCA event, not only a ceiling. Existing account-wide direction
and tests indicate this, but this proposal asks for explicit confirmation before
changing Core sizing behavior.

## 4. Recommended implementation guardrails (not yet authorized)

After D1-D3 are decided:

1. Introduce one explicit, versioned Core leverage/config object consumed by
   both Core signal calculations and the scoped paper ledger.
2. Remove implicit 13x fallback for new exposure; invalid/missing config fails
   closed with an observable reason.
3. Keep RSI, ADX, entry crossings, Smart-DCA eligibility, TP and stop predicates
   unchanged unless D2 explicitly authorizes threshold-semantic changes.
4. Replace the 50% producer margin basis with a candidate sizing contract
   consistent with the 1% per-order admission budget.
5. Keep risk engine validation independent; producer output never bypasses the
   1% margin, gross exposure, equity readiness, reservation, liquidity or Kill
   Switch checks.
6. Add RED tests for ENTRY and DCA at current equity, changed equity between
   orders, leverage/config mismatch, missing config, invalid bounds, ROE/price
   threshold parity and risk rejection. Then run isolated paper-only CI.
7. Do not run backtests until the owner separately authorizes the backtest
   window, parity protocol and acceptance metrics.

## 5. Current disposition

- DS-01: PASS — source and isolated CI scope only.
- DS-02: PASS — source and isolated CI scope only.
- DS-03: **BLOCKED — owner policy decision required**.
- DS-04: documentation reconciliation completed separately.
- No Core sizing/leverage source change, test change, workflow dispatch, database
  migration, runtime action or deployment was performed as part of this
  proposal.
- No leverage value or range is recommended as an implicit default.

## 6. Approval boundary

Approval of this proposal's policy decisions would authorize only the specifically
approved follow-up TDD scope. It would not authorize persistent account DB
migration, account cutover, VPS/runtime activation, deployment, exchange
connectivity, or live execution. Those remain separate approval gates.
