# Core Paper Runtime Entrypoint Contract

Date: 2026-11-12
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/core-operational-proof-20261112`
Design baseline: `c23062db769e72b9728c78816cf2eed4d5bda09b`

## 1. Decision

Define the first Core runtime as a **one-shot paper decision runner**, not a continuously running daemon.

Proposed invocation after implementation and tests are separately completed:

```bash
python -m core_runtime --config <paper-config>
```

One invocation performs one bounded decision cycle, emits a machine-readable result, and exits. A scheduler/daemon, service manager, systemd unit, autostart, VPS installation and continuous operation are explicitly deferred.

Do not overload or rename `python -m paper_execution`. The existing `paper_execution.__main__` is a ledger initialization utility: it requires `--db`, constructs `PaperLedger`, prints `ledger.snapshot()`, and exits. It does not load candles, call `pipeline.core_strategy.produce()`, validate a strategy signal, or submit a Core decision.

## 2. Verified existing interfaces

- `pipeline.core_strategy.produce(m15_window, h1_window, paper, strategy_state, book, now_ms, account_equity_quote=None, max_position_base=0.01)` is the current Core decision function. It consumes M15/H1 candle windows, paper position, strategy state, visible order-book snapshot, time and optional account equity.
- The Core strategy contains RSI/ADX entry logic, Smart DCA, exit/stop logic, sizing and an intent builder. Preserve its current thresholds and behavior in this packaging increment.
- `pipeline.core_signal.validate(report, now_ms)` is the signal validation boundary and must be inspected and used only according to its existing contract; do not bypass it.
- `PaperLedger` is the paper persistence/admission boundary. Its scoped Core path is selected with `strategy_id="STRATEGY_CORE"`; the shared Kill Switch and risk controls remain authoritative.
- `paper_execution.read_snapshot(db_path, strategy_id=...)` is read-only and must not initialize missing database state.
- `paper_execution.__main__` is initialization-only, not the Core runner.
- `paper_execution/README.md` states the package has no exchange API key or live order sender. The Core runner must preserve that property.

## 3. Proposed module boundaries

The runner should orchestrate existing components; it must not reimplement strategy or risk logic.

1. **Configuration loader** — accepts an explicit paper configuration file; validates schema, paths, numeric limits and mode. No implicit production defaults.
2. **Input provider interfaces** — inject validated M15/H1 windows, a fresh visible-depth book snapshot, and account/ledger state. Initial R0 implementation uses deterministic fixtures and disposable local data only. No exchange client or live network adapter is part of this gate.
3. **Core decision adapter** — calls `pipeline.core_strategy.produce()` with the exact input bundle and captures its decision report.
4. **Signal validation** — validates the report and intent through the established Core signal contract. Missing, stale, malformed, contradictory or expired input fails closed.
5. **Paper admission adapter** — submits only a validated Core paper intent to the Core-scoped PaperLedger. It does not call an exchange API.
6. **Result/evidence writer** — emits structured JSON containing run ID, source SHA, dataset/snapshot identities, decision, validation/admission outcome, timestamps and exit status. Avoid secrets and do not write into T0 canonical storage.

## 4. Required safety invariants

- `mode=PAPER` is mandatory and enforced at configuration and intent boundaries.
- `AI_EXECUTION_ENABLED=false` is mandatory. This runner is Core-only; no AI strategy invocation, AI admission or AI ledger mutation.
- No exchange API keys, private credentials, exchange order endpoints, live mode or real orders.
- T0 candle input is read-only. The runner must not initialize, migrate, write, delete or otherwise mutate the canonical T0 database.
- The paper ledger path must be explicit and separate from T0 canonical storage. R0/R1 use a disposable SQLite path.
- The Core strategy remains the source of RSI + ADX + Smart DCA decisions. No threshold, sizing, leverage or risk-policy changes in this packaging increment.
- The Shared Risk Engine and persistent Kill Switch remain the final admission authority. The runner must not bypass them or interpret a generated signal as an admitted order.
- Missing/corrupt risk state, unavailable account equity, stale market inputs, missing dataset provenance, invalid config or database errors fail closed; no order/reservation/fill may be fabricated.
- One-shot execution must be idempotent for a repeated intent according to the existing ledger intent contract.
- No implicit database creation on read paths. Any initialization/migration is an explicit, separately testable writer operation against disposable storage only.

## 5. One-shot lifecycle and observable result

The proposed single invocation is:

1. Parse explicit config and verify paper-only flags.
2. Resolve and validate the disposable ledger location; reject canonical T0 path aliases.
3. Load input bundle through injected providers; validate M15/H1 windows and book freshness/provenance.
4. Read Core paper position/state and account risk snapshot without mutating T0.
5. Call Core `produce()`.
6. Validate the decision report and any intent.
7. If action is WAIT or there is no intent, emit a WAIT result and do not submit.
8. If a valid intent exists, submit through Core-scoped PaperLedger; Shared Risk Engine/Kill Switch may reject it.
9. Emit JSON result and evidence metadata; close resources; exit.

Suggested result classes:
- `WAIT`: no actionable Core intent.
- `PAPER_ADMITTED`: intent passed validation and shared risk admission; this does not guarantee a fill.
- `PAPER_REJECTED`: shared risk/ledger rejected the intent.
- `INPUT_BLOCKED`: invalid, stale or incomplete inputs.
- `RISK_STATE_BLOCKED`: risk/Kill Switch state unavailable or invalid.
- `RUNTIME_ERROR`: unexpected infrastructure or storage error; fail closed.

Exit codes must be stable and documented. A successful process exit must not be interpreted as a successful trade or as runtime readiness.

## 6. Contract tests required before implementation is accepted

- CLI help and config schema validation; missing config and unknown keys reject.
- PAPER-only enforcement; AI enabled, live mode, credential variables or live-order configuration reject before any ledger mutation.
- WAIT/no-intent path does not create an order, reservation or fill.
- Valid Core LONG and SHORT intents pass the same validator and Core-scoped ledger path.
- Existing RSI/ADX/Smart DCA golden fixtures remain byte/semantic equivalent; no strategy threshold changes.
- Stale/missing M15, H1, dataset version, book snapshot or account equity fails closed.
- Missing/corrupt Kill Switch and shared-risk state blocks admission with no partial writes.
- ENTRY, DCA and EXIT continue to obey the existing Shared Risk Engine and Kill Switch rules.
- Duplicate invocation with the same intent follows existing idempotency behavior.
- T0 path is rejected as a writable ledger target; tests prove no T0 mutation.
- Output JSON is deterministic where fields are deterministic, contains no secrets, and distinguishes decision from admission and fill.
- Subprocess smoke test proves one invocation starts, processes one cycle, closes and exits without a background process.

## 7. Explicit non-goals for this increment

- No implementation or code changes to Core strategy, ledger schema, risk engine or Kill Switch.
- No AI strategy execution or dual-strategy admission.
- No Hummingbot live connector, Binance market connection, exchange credentials or real orders.
- No persistent host, VPS, SSH, service manager, systemd/autostart or daemon.
- No dependency installation on a persistent machine.
- No T0/T1/T2 runtime changes and no canonical data mutation.
- No automatic data cleanup or destructive storage operation.

## 8. Gate disposition and next step

- Existing Core code-level paper tests: PASS on the prior exact source SHA recorded in the packaging assessment.
- Existing `paper_execution` module CLI: PASS as an initialization-only utility; **not a Core runtime entrypoint**.
- Core one-shot runtime contract: **DESIGN RECORDED; NOT IMPLEMENTED; NOT TESTED**.
- Clean package install/R0 and process restart/R1: **NOT STARTED**.
- Persistent runtime/VPS: **BLOCKED / NOT AUTHORIZED**.

Next bounded increment: inspect the exact `pipeline.core_signal.validate()` and account-risk snapshot contracts, then add RED contract tests for the proposed one-shot runner before implementing it. Keep all tests on disposable state and preserve the active branch. No host operations.
