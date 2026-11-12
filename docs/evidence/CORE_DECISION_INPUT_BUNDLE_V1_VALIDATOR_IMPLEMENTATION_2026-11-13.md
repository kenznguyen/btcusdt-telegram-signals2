# Core Decision Input Bundle v1 — Validator Implementation Evidence

- Date: 2026-11-13
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/core-operational-proof-20261112`
- Frozen contract: `CORE_DECISION_INPUT_BUNDLE` v1.0.0 / schema v1
- Design authority: `docs/evidence/CORE_DECISION_INPUT_BUNDLE_V1_DESIGN_2026-11-13.md`
- Implementation scope: pure validator only; no runner or source acquisition.

## Pre-implementation RED evidence

GitHub Actions run [#92](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43267464123):
- Exact checked-out source SHA: `e017345049352a86fd3c5e24d8f12427559a4794`.
- Conclusion: SUCCESS; operational-proof job completed.
- All 16 workflow steps completed successfully.
- The 10-test validator suite failed for the expected missing-module reason and was explicitly classified as EXPECTED_RED; downstream checks were not skipped.
- Live-data probe: 4 tests PASS; Core strategy/signal: 12 PASS; preflight: 5 PASS; producer adapter: 6 PASS; Core operational proof: 39 PASS; account-risk read-only gate: 3 PASS; shared risk/paper-ledger regressions: 28 PASS.
- Existing Core behavior, risk snapshot read-only checks, Shared Risk Engine and PaperLedger regression gates passed.
- Artifact: `core-first-code-operational-proof-43267464123`, ID `13966093909`, 5,314 bytes, expires `2026-11-19T17:15:22Z`, GitHub upload digest `sha256:91c6d34a8834c13ef84c182c120888103d244c2875f17b67dc2f48397f3bef15`. Artifact payload was not independently downloaded/re-hashed in this increment.

## GREEN implementation scope

Added `core_runtime/input_bundle.py` with the frozen API:
- `BundleValidationError(ValueError)` with stable diagnostic codes.
- `compute_bundle_id(bundle)`: RFC 8785 canonical JSON + SHA-256, excluding only top-level `bundleId`.
- `validate_bundle(bundle, *, max_book_age_ms)`: validates envelope, PAPER/AI-disabled guard, market identity, embedded T0 M15/H1 provenance/coverage/freshness/continuity/OHLC/decimal values, explicit order-book age and visible depth, Core state projection, exact account-risk snapshot digest, and bundle identity.
- No filesystem, network, database, ledger, producer, risk-admission, or execution imports/calls.
- Does not import or initialize PaperLedger.

Expanded the deterministic contract suite from 10 to 15 tests. Corrected the fixture so the latest H1 candle closes at the start of the current M15 hour bucket, matching the frozen eligibility rule.

Updated the existing GitHub Actions workflow to compile and run the GREEN validator suite and upload its log/status. Existing Core, risk and ledger regressions remain in the same workflow.

## Scope limits

No runner/one-shot decision cycle, no ledger or schema changes, no strategy/threshold/leverage changes, no AI admission, no network/provider integration, no T0/T1/VPS access, no canonical database access, no persistent runtime, no systemd/autostart, no real orders. `AI_EXECUTION_ENABLED=false` remains mandatory.

## Verification disposition

- Pre-implementation RED evidence: **PASS**.
- Validator source and 15-test suite: **IMPLEMENTED; CI VERIFICATION PENDING**.
- Core decision cycle: **NOT IMPLEMENTED**.
- Runtime/provider integration: **NOT AUTHORIZED / NOT STARTED**.
- Release readiness: **NOT CLAIMED**.

Next gate: run the updated existing GitHub Actions workflow against the exact implementation commit. Accept GREEN only if all 15 validator tests and all existing regression steps pass.


## CI #93 findings and correction
Run [#93](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43268766381), exact source `81c91e2131774ef8e4d2bc5ed97783bec10fb8e9`, failed in the validator test step after 3 of 15 assertion mismatches. Compilation and the earlier four suites passed; downstream steps were skipped by fail-fast.

Corrections:
1. Risk snapshot availability is checked before digest comparison so unavailable snapshots return `RISK_SNAPSHOT_UNAVAILABLE`.
2. The float-in-candle test now expects the global `JSON_FLOAT_NOT_ALLOWED` guard.
3. Stale/future order-book mutation tests recompute the top-level bundle identity so they exercise the intended timestamp checks.

Corrected source blob: `497b94505862fd5d41411c4273e3e7c79340d588`.
Corrected test blob: `a196466680eb1b9015e2d9039b390089a61dfcb5`.

Run #93 artifact ID `13967212176`, upload SHA-256 `0d051dd70c880d7fa3b4948265a8b8c08d801135c2df21d3f7dd84b0c058ea45`; payload hash not independently verified.

Disposition: validator implementation remains **BLOCKED pending corrected CI**. No downstream runtime scope is opened.


## CI #94 finding and correction
Run [#94](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43269036006), exact source `eae945d579381afcad1ba9a89092d3fc8ae54554`, failed only in the future-order-book test. Fourteen of 15 validator tests passed. The fixture added 1 ms to an observedAtMs value already 1,000 ms behind decisionAtMs, so it remained in the past and correctly did not raise a future-timestamp error.

The fixture now adds 1,001 ms to make the timestamp strictly future and recomputes bundleId. This is a test-fixture correction; no production validator behavior change is indicated.

Run #94 downstream regression steps were skipped because the workflow is fail-fast. Artifact ID `13967357175`, 3,548 bytes, expires `2026-11-19T17:24:07Z`, upload digest `sha256:41066049784c1dc693c8e83741aa392fdc2215d3f6d45fe9ba2de66668a0c4fa`; payload not independently read back.

Corrected test blob: `f7de191153610abb07eb185a7ad6989f21571743`. Corrected CI #95 is required before promoting GREEN.
