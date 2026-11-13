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

## GREEN implementation and verification — 2026-11-13

### T2 one-shot reader

- Added core_runtime/orderbook_http.py; exact source blob at verified branch SHA: 89e5129eea4c9e7ceaa4439a546daf112d15c3e3.
- Client API: OrderBookHttpClient.fetch(decision_at_ms=...). Each invocation performs exactly one GET to /internal/v1/orderbook/btcusdt; there is no retry, cache, fallback or downstream callback.
- Configuration accepts only the T1 IPv4 loopback origin 127.0.0.1, a non-empty Bearer token, bounded connect/read/total timeouts and a maximum 65,536-byte response. Token is excluded from config repr; the owned requests Session disables environment proxy inheritance.
- Reader rejects redirects/non-200, invalid auth, non-JSON/compressed payloads, malformed/duplicate-key/non-standard JSON, invalid or oversized Content-Length/body, timeouts, connection failures, and invalid decision timestamps. It passes the full document through the existing validate_snapshot(..., decision_at_ms=...) before returning it.
- T2 reader tests blob: 6edb8dea8ea208c229439b2655f1ed03c173e055. Coverage includes exact decimal-string preservation, one request only, timeout/no retry, refusal/no retry, status/auth errors, malformed/duplicate JSON, response type/encoding, declared/streamed size limits, wrong/missing/unknown identity fields, stale/future timestamps, incomplete depth, invalid numeric price and secret redaction.
- Loopback TCP integration test blob: eaa282ae4ea6fd0d7dba611a124eea36ad31c7d8. It runs a local HTTP fixture using the T1 V1 wire envelope and verifies a single authenticated round-trip with exact price/quantity strings and depth.
- Focused workflow blob: fec69171d648bf0c5ddaa8c30c54ff3c06c50e4f. Full operational workflow blob: 6fbf00fa666c0b7a965ba174eaa1fad61919e2ea.

### RED and exact-SHA GREEN evidence

- RED run #5 ID 43356028851 on SHA 08257c7953dbc9a3ff5ca54ae2a71e5213d265ce failed at the intentional RED step with ModuleNotFoundError: core_runtime.orderbook_http. This is the expected missing-adapter reproduction. Paper-only/no-provider boundary passed.
- T2 exact tested source SHA: 75b8dde6194195f4fd0bc7d1dc07e737f73a4d5c.
- Focused T1→T2 workflow #18 ID 43357183373 completed SUCCESS on that exact SHA. Result: 49 tests passed, 0 failed — 32 frozen contract tests + 16 HTTP reader tests + 1 loopback TCP integration test. Compile, paper-only boundary, status checks and artifact upload PASS.
- Focused artifact ID 14005783966, name t1-t2-orderbook-green-43357183373, ZIP SHA-256 ad9ad2250a20a0c72c8d80afa398f68e2f98ce3c636f1e13409c19bc8077cff3; expires 2026-11-20T03:10:40Z.
- Full Core-First operational proof workflow #110 ID 43357183307 also completed SUCCESS on the same exact SHA. The broader live-data probe, Strategy Core regressions, paper preflight, input bundle, producer adapter, Core paper lifecycle, read-only account risk, shared risk/ledger regressions and the complete 49-test T1→T2 suite all passed.
- Full workflow artifact ID 14005994516, name core-first-code-operational-proof-43357183307, ZIP SHA-256 4131b5184e57a336c9baf63ccb7c730e29c247700fa49f1cbaaaff44a1d95df1; expires 2026-11-20T03:10:40Z.

### Combined C2.2 disposition

- T1 loopback endpoint source and exact-SHA x86_64/ARM64 CI: PASS (T1 source SHA 8326ac2075ebd644e5cca0146a77ce1ae110954c; workflow #637 ID 43355193041; all six jobs PASS; 145 Rust tests per architecture).
- T2 one-shot HTTP reader and strict validator integration: PASS (T2 source SHA 75b8dde6194195f4fd0bc7d1dc07e737f73a4d5c; 49/49 tests PASS).
- Deterministic loopback TCP wire-fixture integration: PASS. This is a test fixture compatible with the T1 V1 serializer, not a connection to a running T1 process.
- Actual T1 process→T2 process delivery, reconnect/re-anchor soak, VPS behavior and runtime freshness under live load: NOT VERIFIED / NOT RUN.
- T1 endpoint is opt-in and disabled unless T1_ORDERBOOK_HTTP_TOKEN is supplied. No runtime activation or deployment was performed.
- No T0 data/API/storage, VPS, systemd/autostart, deployment, Core Runner, strategy, ledger, Shared Risk Engine, AI execution or real-order changes.