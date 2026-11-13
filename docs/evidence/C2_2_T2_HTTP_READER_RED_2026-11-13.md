# C2.2 T2 One-shot Order Book HTTP Reader — RED Evidence

Date: 2026-11-13
Status: RED reproduced; implementation not yet present.

## Scope

- Existing T2 strict validator remains the authority: core_runtime/orderbook_contract.py validate_snapshot(..., decision_at_ms=...).
- New test module: core_runtime/test_orderbook_http.py.
- Intended adapter: one bounded GET to T1 loopback endpoint; no retry, no fallback, no state mutation or downstream Core/Risk/Ledger/Execution callback.
- This increment uses synthetic deterministic responses only. No T1 runtime, Binance, T0, VPS, database, credentials or live trading.

## RED source and workflow

- Existing branch: feature/core-operational-proof-20261112.
- Exact tested source SHA: 08257c7953dbc9a3ff5ca54ae2a71e5213d265ce.
- Test source blob: 35f5a4944f9c3c3bd709afe54249490d448d0bb9.
- Workflow: T1 to T2 Order Book V1 contract tests, run #5, ID 43356028851.
- Exact-SHA run conclusion: FAILURE at the intentional RED step, before compilation or GREEN contract tests.
- RED step: Run RED T2 one-shot HTTP reader tests.
- Failure reproduced: ImportError / ModuleNotFoundError: No module named core_runtime.orderbook_http. The tests therefore prove the adapter is not yet implemented.
- Paper-only boundary step PASS: AI_EXECUTION_ENABLED=false; T0/Paper DB and exchange credential variables empty.
- Evidence artifact ID 14005393795, name t1-t2-orderbook-green-43356028851, ZIP SHA-256 0a6acc4d5b896ea231c506b99bfb4ac715ea0f1df9d72b3e3642d63021761432. Artifact is only pre-test safety/source metadata; it is not GREEN evidence.

## RED test coverage planned

- Valid snapshot: exact T1 V1 fields and decimal strings preserved; one GET only.
- Config: loopback-only origin, non-empty token and bounded response limit.
- Transport: non-200/redirect/401, timeout, connection refusal; all fail without retry.
- Payload: malformed JSON, duplicate keys, non-JSON/compressed response, declared and streamed oversize.
- Contract: unknown/missing fields, wrong symbol/version, stale/future timestamps and incomplete depth.
- Invalid decision timestamp fails before any network request.

## Next

Implement only core_runtime/orderbook_http.py with an injected session for deterministic tests, one GET per invocation, strict bounded response parsing, Bearer token, and full validate_snapshot gate. Then replace the RED workflow step with the GREEN adapter+contract suite and record exact-SHA CI. No Core Runner or runtime integration.