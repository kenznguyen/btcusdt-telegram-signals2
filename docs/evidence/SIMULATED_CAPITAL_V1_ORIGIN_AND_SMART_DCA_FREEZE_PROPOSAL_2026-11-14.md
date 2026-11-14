# SIMULATED_CAPITAL_V1 — Capital Origin and Smart DCA Freeze Proposal

Date: 2026-11-14 (Asia/Ho_Chi_Minh)
Branch: `feature/core-operational-proof-20261112`
Source HEAD reviewed: `139495a4a5c38f0cc6069c31ddbfe50cacd52f98`
Status: **OWNER APPROVED — DESIGN FROZEN; IMPLEMENTATION NOT STARTED**

## 1. Purpose and boundary

This proposal resolves the two design items identified by the PaperLedger audit:
- persistent, immutable provenance for the synthetic 100 USDT capital;
- exact Smart DCA lifecycle semantics to preserve during simulated-capital integration.

It does not authorize database migration, Ledger initialization, Bootstrap, Runner, exchange access, live orders, T0/VPS operation or AI execution.

## 2. Proposed simulated capital origin schema

Add a distinct simulated-origin record. Do not encode the seed as a funding event, deposit, exchange balance, legacy adjustment or fabricated funding coverage.

### 2.1 Immutable origin record

Proposed table: `paper_simulated_capital_origin`

| Column | Type / rule | Purpose |
|---|---|---|
| `account_id` | INTEGER PRIMARY KEY, FK to paper account | One origin record per paper account |
| `capital_mode` | fixed `SIMULATED` | Distinguish synthetic seed from funded accounts |
| `trading_mode` | fixed `PAPER` | Prevent mode ambiguity |
| `initial_capital_quote` | canonical Decimal text, exactly `100` | Immutable initial capital |
| `quote_currency` | fixed `USDT` | Quote currency |
| `contract_id` | fixed `SIMULATED_CAPITAL_V1` | Contract identity |
| `contract_schema_version` | integer, fixed `1` | Contract schema binding |
| `contract_sha256` | 64 lowercase hex | Exact machine-contract content binding |
| `seed_event_id` | UNIQUE deterministic identifier | One-time seed identity |
| `seeded_at_ms` | positive integer | Seed creation time |
| `seed_source` | fixed `OWNER_APPROVED_SIMULATION` | Truthful synthetic origin |
| `record_sha256` | 64 lowercase hex | Canonical origin-record digest |

Add append-only `paper_simulated_capital_seed_events` with a unique `event_id`, account ID, amount, currency, contract hash, event time and canonical payload hash. UPDATE/DELETE triggers reject mutation of both origin and seed-event rows. The seed must never be represented in `paper_funding_events`.

### 2.2 Initialization and restart rules

- Initialization occurs only through a pure, explicit simulated-account initializer in a disposable test fixture until separately approved.
- One SQLite `BEGIN IMMEDIATE` transaction creates the account/origin/seed event and initial risk baseline/HWM together.
- Initial equity, daily baseline and HWM start at 100 USDT only when the account is empty, the seed is valid, and the required baseline provenance is created atomically.
- Unique account key and unique seed-event ID prevent concurrent duplicate initialization.
- Repeating initialization with identical contract and seed identity returns/validates the existing account without writing another seed.
- Any mismatch in amount, currency, mode, contract ID/version/hash, account identity or seed event is a hard error. Never reset, top up, overwrite, auto-repair or silently adopt an existing legacy account.
- Restart/reopen verifies the origin record, seed event, account initial capital, contract digest and risk baseline/HWM. Any missing or inconsistent evidence blocks new exposure.
- Existing real/funded account Bootstrap and funding/cutover rules remain unchanged.

### 2.3 Contract digest

Compute SHA-256 over the exact canonical machine-contract bytes committed in the repository (UTF-8, no newline normalization at runtime). Persist the digest and compare it on every initialization and risk admission. Do not trust a caller-supplied digest without loading and validating the committed contract.

## 3. Smart DCA semantics found in the current Core producer

Source: `pipeline/core_strategy.py` blob `0be512d99b4302077ab79879184b74949f0feaaa`; tests: `pipeline/test_core_strategy.py` blob `a0d5b46845d3fde006ed817fe21bdd8b6546c1d1`.

Current implementation behavior:
1. Core supports **at most one DCA addition per position lifecycle**. It uses persisted `dcaUsed`; when the position returns to flat, ledger state resets the flag.
2. DCA is considered only when emergency stop, soft stop and take-profit checks have not triggered.
3. DCA trigger requires ROE <= `DCA_ROE` (default -20%) and M15 ADX > `DCA_ADX` (default 45).
4. LONG DCA requires RSI > `LONG_DCA_RSI` (default 20) and RSI rising versus the previous M15 RSI. SHORT DCA requires RSI < `SHORT_DCA_RSI` (default 80) and RSI falling versus the previous M15 RSI.
5. DCA target adds one new quantity to the existing same-direction position. Sizing uses current validated account equity and the Core 1x leverage policy.
6. Current producer's per-order margin sizing uses 1% of current account equity. The Ledger independently rechecks the order against its risk limits before reservation/fill.
7. The existing dual-ledger persistence has a boolean `dca_used`; it cannot represent a multi-leg DCA sequence with multiple indexed additions.

### Proposed preservation decision

- Freeze Core Smart DCA at **one DCA addition per Core position lifecycle** for this SIMULATED_CAPITAL_V1 increment. Do not change RSI/ADX thresholds, ROE trigger, exit priority or signal behavior in this task.
- Each DCA addition is a normal risk-increasing order: it must pass the same fresh-equity 1% order-margin admission, shared 10 USDT gross exposure cap, shared drawdown/daily-loss controls and Kill Switch as a new entry.
- The 1% value is an **order-level ceiling**, as named by the approved contract. Do not silently reinterpret it as a cumulative account-wide 1% margin cap. A separate aggregate reserved-margin ceiling is not currently specified and would require a distinct owner decision.
- The same account-wide exposure and Kill Switch apply to Core and AI. AI does not inherit Core's Smart DCA behavior; AI DCA remains unsupported unless separately specified and approved.
- If future work needs multiple DCA legs, it requires a new versioned DCA contract and persisted leg identities; do not weaken the existing boolean guard in this increment.

## 4. Atomic order admission contract

Within the same `BEGIN IMMEDIATE` transaction, the order path must:
1. Verify immutable simulated origin, seed event and exact contract digest.
2. Verify account state and accepted equity/mark provenance are present, current, finite, positive and internally reconciled.
3. Verify UTC daily baseline and HWM provenance.
4. Compute equity from seed capital plus realized/unrealized PnL, less fees and funding, including any valid account adjustments; synthetic seed itself is not funding.
5. Calculate aggregate gross exposure as filled Core + filled AI + active remaining reservations (including the candidate increase exactly once).
6. Enforce order-level margin: `requested_incremental_notional / effective_leverage <= accepted_equity * 0.01`.
7. Enforce shared gross exposure <= 10 USDT.
8. Enforce drawdown < 10% and daily loss < 2 USDT. At either boundary, persist the shared Kill Switch latch and reject increases/DCA; allow valid reductions.
9. Verify order identity, strategy ownership, expiry and visible-book constraints.
10. Persist reservation/order/audit changes atomically or persist none.

Core leverage remains 1x. AI leverage 1x–3x remains a separate AI sizing policy and may not bypass shared admission. This proposal does not authorize AI execution.

## 5. Required tests before considering simulated Ledger readiness

- Exact origin and seed event created once; exact 100 USDT starting equity.
- Two concurrent initializers cannot create duplicate accounts or seed events.
- Reopen/restart preserves origin, contract digest, seed, balance, baseline and HWM.
- Any changed contract/amount/currency/mode/seed or corrupted/missing row fails closed.
- Existing funded-account migration/bootstrap tests remain unchanged and green.
- DCA triggers only under the existing ROE/ADX/RSI/momentum conditions; exits retain priority.
- Second DCA in the same Core lifecycle rejects; after fully flat, a new lifecycle may qualify for one DCA.
- Core DCA and AI entry share the 10 USDT exposure cap; concurrent admission cannot double-spend reservations.
- At exactly 1% per-order margin admission succeeds; above it rejects; DCA is tested identically.
- Daily loss 2 USDT and drawdown 10% latch the shared Kill Switch; increases/DCA reject; valid reductions remain allowed.
- Missing/stale/future/invalid equity, mark, baseline, origin or provenance rejects new exposure.
- Partial fill, reservation release/expiry, idempotent retry and process reopen preserve risk accounting.
- Full relevant regression suite and CI run against exact source SHA.

## 6. Decisions requiring owner confirmation

The following are proposed defaults, not yet frozen by the owner:
- **Origin schema:** the immutable table + append-only seed event described above, bound to the exact SIMULATED_CAPITAL_V1 contract digest.
- **Smart DCA:** preserve current one-addition-per-Core-position-lifecycle behavior.
- **Margin interpretation:** 1% is per order (including DCA); no additional aggregate account-wide margin cap is introduced in this increment because the approved contract does not define one.
- **AI DCA:** not supported by this Core-specific DCA freeze.

No code or tests were changed. No database, migration, Bootstrap, Runner, T0, VPS, exchange, or live-order action occurred.


## 7. Owner approval — 2026-11-14

The owner explicitly approved all four freeze decisions in this proposal:

1. **Simulated origin:** approve the separate immutable `paper_simulated_capital_origin` record and append-only seed event, bound to the exact SIMULATED_CAPITAL_V1 contract SHA-256. The synthetic seed must not be represented as a funding/deposit event.
2. **Core Smart DCA:** preserve at most one DCA addition per Core position lifecycle, with existing ROE/ADX/RSI/momentum triggers and exit priority unchanged.
3. **Margin interpretation:** 1% of accepted current equity is a per-order margin ceiling, including every DCA order. No aggregate account-wide margin ceiling is added in this increment.
4. **AI DCA:** AI does not inherit Core Smart DCA; AI DCA remains unsupported unless separately specified and approved.

This approval freezes the design and authorizes the next bounded implementation increment: isolated TDD implementation of the simulated-origin persistence/initialization and atomic risk admission on the current branch. It does **not** authorize database migration or mutation of any existing operational database, Bootstrap, Runner, VPS/T0 access, exchange access, AI execution, live trading or real orders.

Implementation must begin test-first, use disposable test databases/fixtures only, preserve funded-account Bootstrap/cutover behavior, and stop if the existing schema or risk semantics require an unapproved change.


## 8. Implementation progress — 2026-11-14

The owner-approved design remains frozen. The first isolated implementation increment is complete:
- Immutable origin and distinct seed-event persistence primitive implemented.
- Exact contract byte hash, duplicate/restart verification, record digests and UPDATE/DELETE triggers implemented.
- 12/12 focused CI tests PASS on source SHA `d7be89a09c660a4a43b3de0a739d67558b65152a`, workflow run `43602607051`.
- Evidence: `docs/evidence/SIMULATED_CAPITAL_V1_ORIGIN_PERSISTENCE_2026-11-14.md`.

This is **not** full simulated-account initialization: account creation, origin, seed, UTC daily baseline and HWM are not yet composed in one atomic transaction. No PaperLedger runtime integration, 1% contract-bound order-margin enforcement, migration, Bootstrap or Runner is implemented or authorized. PAPER Ledger readiness remains **BLOCKED / NOT VERIFIED**.
