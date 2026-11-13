# One-shot Core Runner — T1 / PaperLedger Compatibility Blocker

Date: 2026-11-13 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/core-operational-proof-20261112`
Baseline branch HEAD: `7e4cb233069f22d895aecf4f88c889e1aeb244f2`
Disposition: **BLOCKED — no Runner implementation or source changes**

## 1. Approved task boundary

Owner authorized automatic continuation through completion of the One-shot Core Runner, under the previously prepared Runner design/test plan. Existing boundaries remain controlling:
- Keep Bundle v1 contract/schema version 1.0.0 and T1 as the Core Order Book source.
- Do not change Strategy Core behavior, Shared Risk Engine policy, PaperLedger schema/behavior, T0/T1/T2 runtime, AI execution, or live execution unless separately authorized.
- PAPER only; `AI_EXECUTION_ENABLED=false`; no exchange credentials/orders, VPS, systemd, daemon, scheduler or deployment.
- Continue on the existing branch only; no branch rewrite, merge, rebase or replacement branch.

## 2. Verified source facts

- `core_runtime/input_bundle.py` validates Bundle v1 Order Book provenance as `source=t1`, `connector=binance_usdm_perpetual`, BTCUSDT, and reconstructs/validates the embedded `T1_T2_ORDERBOOK_V1` evidence and snapshot identity.
- `core_runtime/adapter.py` maps Strategy Core producer reports to the existing signal contract without synthesizing provenance.
- `pipeline/core_strategy.py` is the existing RSI/ADX/Smart DCA producer. `pipeline/core_signal.py` is the existing signal validator.
- `paper_execution.ledger.PaperLedger._submit_scoped()` calls `book_value(book, now)` before paper admission.
- The current `paper_execution.ledger.book_value()` explicitly accepts only `source=hummingbot`, `connector=binance_perpetual`, `symbol=BTCUSDT`. It rejects the T1 provenance used by Bundle v1.
- The current PaperLedger call path therefore cannot consume the validated T1 Order Book from Bundle v1 without a compatibility change at the Ledger's book-validation boundary.
- Relabeling a T1 snapshot as Hummingbot to pass the current check would falsify source provenance and is prohibited.
- Passing a synthetic/legacy Hummingbot book would disconnect the paper admission/fill simulation from the validated Bundle v1 T1 snapshot and is also prohibited.

## 3. Why implementation is blocked

The approved Runner design requires the actual validated T1 snapshot to flow through the existing Shared Risk Engine and Core-scoped PaperLedger. The same design explicitly prohibits changing PaperLedger in this increment. These constraints are incompatible with the current source contract.

A Runner that only evaluates Strategy Core and reports a signal, while skipping PaperLedger admission, would not satisfy the approved Runner completion criteria. A Runner that fabricates Hummingbot provenance or silently substitutes a different book would violate data integrity. A Ledger modification would exceed the current no-Ledger-change boundary.

## 4. Required owner decision to unblock

A separate bounded approval is required for a T1-compatible PaperLedger book-input contract. Suggested scope:
1. Extend only the Ledger's paper book provenance/validation boundary to accept the exact `T1_T2_ORDERBOOK_V1` snapshot or a lossless, provenance-preserving normalized representation.
2. Bind the paper book identity/digest to the validated T1 `snapshotId` and exact levels/timestamps; do not relabel T1 as Hummingbot.
3. Preserve all existing Shared Risk Engine, Kill Switch, reservation, idempotency, fill, and ledger schema semantics.
4. Add TDD tests for valid T1 acceptance, Hummingbot regression compatibility where still required, wrong source/connector, tampered levels, stale/future timestamps, snapshot digest mismatch, and duplicate snapshot consumption.
5. Demonstrate no schema migration and no changes to risk thresholds or admission policy.
6. Run focused and full exact-SHA GitHub Actions before returning to the One-shot Runner implementation.

If the owner does not approve that compatibility scope, Runner completion remains BLOCKED and must not bypass paper admission.

## 5. Verification performed

- Read `docs/PROJECT_SESSION_HANDOFF.md` from the active branch before work.
- Read Bundle v1 validator, T1 order-book contract/HTTP reader, producer adapter, CLI preflight, Core strategy, Core signal validator, PaperLedger, existing Runner RED tests and Runner entrypoint design.
- Source blobs inspected:
  - `core_runtime/input_bundle.py`: `19fb3065da1e7d40c8b4376fe3b51e11c8cc8f87`
  - `core_runtime/adapter.py`: `9795c346d2eec4c78c22035c32f463af6b40b8f4`
  - `paper_execution/ledger.py`: read from active branch; current `book_value` source restriction verified directly
  - `pipeline/core_strategy.py`: `f714b6b6dc0822400b6997feb0a8c2f07886aaed`
  - `pipeline/core_signal.py`: `df5fbb59611bdd4fbb8224665f79655dd4433455`
  - `pipeline/test_core_runtime_contract.py`: `f6a365509d9821f5284323cb7e7ff4073621628d`
  - `pipeline/test_core_runtime_adapter_contract.py`: `fbe6cc428fd7058a6dbefd9eaec1979a95638474`
- No source code, tests, workflow, configuration, T0/T1/T2 data, database or runtime was changed.
- No test or CI run was initiated in this checkpoint because the incompatible admission contract is a design blocker, not a test failure.

## 6. Status and next step

- Bundle v1/T1 compatibility: **PASS / GREEN** (prior exact-SHA evidence remains controlling).
- Runner design and pre-existing CLI/adapter contracts: **PASS as documented prior work**.
- T1-to-PaperLedger admission compatibility: **BLOCKED**.
- One-shot Core Runner implementation: **NOT STARTED in this increment**.
- Tests for the new T1 Ledger boundary: **NOT AUTHORIZED / NOT RUN**.
- Runtime/VPS/systemd/autostart/live orders: **NOT AUTHORIZED / NOT RUN**.
- Next step: Owner decision on the narrow T1-compatible PaperLedger book-input contract above.
