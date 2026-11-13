# T1 → PaperLedger Compatibility — GREEN

Date: 2026-11-13
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/core-operational-proof-20261112`
Status: **PASS — exact-SHA CI GREEN; runtime NOT VERIFIED**

## Approved scope
Owner approved the T1-compatible PaperLedger input boundary for the Core-only One-shot Runner. The implementation preserves T1 provenance and snapshot identity and does not change the Ledger schema or risk policy.

## Implementation
- `paper_execution/ledger.py` extends `book_value(raw, now_ms, allow_t1=False)` with explicit opt-in T1 validation.
- Default path continues to accept only the existing Hummingbot source/connector. T1 is rejected unless `allow_t1=True`.
- T1 is enabled only inside the existing `STRATEGY_CORE` scoped submit path; AI and MANUAL paths are unchanged.
- Validator requires exact T1 evidence fields, source/connector/symbol, matching observed timestamp, exact level projection, canonical SHA256 snapshot identity, and the frozen `T1_T2_ORDERBOOK_V1` validator (freshness, continuity, sequence, depth and future/stale bounds).
- T1 book consumption identity is derived from source + connector + symbol + immutable `snapshotId`. Existing scoped per-level reservation semantics are retained, allowing strategies to share a snapshot only up to its visible depth.
- No schema migration, table change, risk-policy change, Kill Switch change, reservation algorithm change, fill algorithm change, or legacy Hummingbot behavior change.

## Tests
- RED baseline: run `43363049113`, SHA `20583fc7542a5373dc39aa30ecc5d6bef527d90e`, failed as expected because `book_value` had no T1 opt-in argument (8 expected test errors; pre-existing 19 tests passed).
- First T1 validator GREEN: run `43363339545`, SHA `5662b7b4af43ae44d6dcc8987a75b1badb8ef716`, focused Ledger suite PASS (25/25).
- Integration iteration caught an incorrect test assumption about dual-ledger shared book depth and then a test-only query key error; both were corrected without weakening assertions.
- Final focused workflow run `43363662032`, exact SHA `3adf741f5a454d677c003c375141acdd179b37f5`, job `131682851514`, **100/100 tests PASS**.
- Core-First operational proof run `43363662013`, exact SHA `3adf741f5a454d677c003c375141acdd179b37f5`, **SUCCESS**. All jobs PASS, including Core operational proof, account-wide read-only risk snapshot, shared risk/PaperLedger regressions, and T1/T2 contract/HTTP/integration tests.
- Artifact `14009053121`, name `core-first-code-operational-proof-43363662013`, SHA256 `c4a1dbffb4a1cb98a08d5577419a424e86ad5146838d147bc5921077a9bf26be`.
- The focused workflow currently produces no artifact.
- Branch compare from prior handoff SHA `a034729d7c0946f35937e6c29a5c5c8dd7f8a898` to this tested SHA: 9 ahead / 0 behind.

## Boundaries and limitations
- CI is code/fixture evidence only. No VPS, service, background loop, T0/T1 runtime, live exchange order, AI Strategy, or AI execution was activated.
- Ledger schema and migration checksums are unchanged.
- T1 → PaperLedger compatibility: **PASS**.
- Actual runtime behavior: **NOT VERIFIED**.
- One-shot Core Runner: implementation still pending.

## Next step
Proceed with a separate one-shot Core Runner orchestration layer using validated Bundle v1, existing RSI/ADX/Smart DCA producer, existing Core signal validator, existing Shared Risk/PaperLedger admission, and one invocation only. Preserve PAPER-only, Core-only, no AI invocation, no background loop, no runtime/VPS activation, and no real orders.
