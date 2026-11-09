# P1.10 — Publication, fencing, gap-state and manifest contract correction

Date: 2026-11-09
Review type: Same-session static consistency review of documentation changes; NOT independent.
Verdict: **DOCUMENTATION CLARIFICATIONS COMPLETE / STATIC CONSISTENCY PASS AT CONTRACT LEVEL / IMPLEMENTATION READINESS NOT ESTABLISHED.**

## 1. Exact target

- Repository: kenznguyen/btcusdt-telegram-signals2
- Branch: feature/t0-centralized-data-feeder-p1-20261101
- Normative design: docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md
- Exact final design blob SHA: 32cf231227c52590ad1365473c6c742ab7dbc64a
- Archival v1 remains non-normative: c64d6da7b16e608ef5ccebafabce03e51960cfcc
- Pinned T1 source baseline: 6e20fe94f3ad64cc450e73def80a167fe371e49e
- P1.9 self-review: 8c433a59b6c1e5dd793a82f81616d06cc066883c

## 2. P1.9 findings and contract dispositions

### F01 CRITICAL — manifest visibility before directory durability

Resolved at contract level by defining a two-phase publication:
1. Sync data file.
2. Write/sync and rename the new manifest.
3. Fsync the containing directory.
4. Only after that barrier, create and fsync an immutable commit receipt binding the exact manifest digest, generation, publication sequence, file identity, committed offset/count, prefix digest and watermark.
5. Atomically publish the receipt; readers require a matching receipt and a shared lock.

A visible manifest without a matching receipt is PREPARED/UNCOMMITTED. If the process dies before receipt publication, readers reject it. If a receipt is lost after a crash, the result is a safe false-negative. Receipt visibility cannot certify a manifest whose directory fsync did not complete because receipt creation is sequenced after that successful barrier.

The receipt proves durable publication ordering only. It does not prove receive completeness, a clean process shutdown, REST completeness or target filesystem semantics.

### F02 HIGH — writer ownership and generation fencing

Resolved at contract level with a stable kernel advisory lock file:
- Writers acquire exclusive lock before generation allocation and hold it through commit-receipt visibility.
- Readers acquire shared lock across manifest/receipt/prefix validation.
- Lock file is stable and never unlinked/replaced.
- Paused owner cannot be displaced by PID or age; a process crash releases the kernel lock.
- Generation counter is durably updated (file sync, atomic rename, parent-directory sync) before any append.
- Unsupported or unverifiable lock semantics fail closed.

The design explicitly limits this to cooperating processes and requires target filesystem/provider lock verification.

### F03 HIGH — WINDOW_GAP had no valid assignment path

Resolved conservatively: WINDOW_GAP is reserved and not assignable under the current v1.1 profile, just like GAP_DETECTED. P1.3 still does not accept Binance REST as a completeness oracle. Missing REST minutes remain UNKNOWN; source asymmetry remains divergence/unknown. No current fixture, manifest or adapter may assign either gap state. A future profile requires a new version, authoritative no-trade/completeness semantics, independent review and explicit approval.

### F04 HIGH — FINAL_ONLY did not bind interval validation

Contract now requires both the configured USD-M WebSocket subscription and each incoming kline event to validate exact BTCUSDT/1m identity before persistence. Provisional events are filtered. Unexpected interval, symbol, stream or endpoint family rejects/invalidates the generation. Close-time semantics cannot be inferred from local wall-clock time; if the exchange schema mapping is not proven, reject.

### F05 HIGH — hardcoded symbol exception bypass

Contract explicitly prohibits symbol-discovery exceptions from bypassing status=TRADING, contract_type=PERPETUAL, quote_asset=USDT and BTCUSDT/base_asset=BTC checks. Exact ExchangeInfo snapshot and symbol-record digests plus an immutable retrievable evidence reference are bound to the generation. The adapter repeats validation.

### F06 MEDIUM — manifest schema and trust boundary

Specified strict UTF-8 JSON/JCS v1.1 closed schema, exact version identifiers, source-root UUID, generation/publication sequences, immutable ExchangeInfo evidence reference, strict data-file identity object, path binding, commit-receipt schema, safe-integer limits, duplicate-key/unknown-field rejection, symlink/path traversal/hard-link checks and quarantine on ambiguity. Platform identity/lock/no-follow capabilities remain environment-dependent and must be verified.

### F07 MEDIUM — C46 premature acceptance

C46 now permits only further review after full REST/WS match. It cannot commit unless every P1.3 identity, boundary, pagination, finality/correction, source-health, no-conflict, generation-binding, durable-publication and receipt-verification prerequisite passes.

## 3. Static consistency checks performed

- Manifest source_health enum excludes GAP_DETECTED; both gap labels are reserved and unassignable in the current profile.
- C29 and C30 no longer allow a nominal watermark or health label to produce WINDOW_GAP/GAP_DETECTED.
- C46 wording is conditional and consistent with P1.3 C55.
- Manifest inventory in §4.2 points to the complete strict schema in §21.5.
- Writer exclusive lock, reader shared lock and receipt publication ordering are consistent.
- Generation allocation is durable before source append.
- Receipt binds the exact manifest and committed prefix; missing/mismatched receipt fails closed.
- FINAL_ONLY and 1m event validation are explicit.
- Product identity exception bypass is prohibited.
- Archival v1 remains non-normative; v1.1 remains sole normative contract.
- Existing health-event persistence failure rules remain sticky and fail-closed.

No contradiction was found in these reviewed clauses at the documentation level. This is a same-session static check, not independent assurance.

## 4. Required fixture inventory

C01–C99 are design scenarios, not implemented or executed tests. P1.10 clarifies:
- C29–C30: missing data and gap labels remain fail-closed.
- C46: conditional REST/WS reconciliation only.
- C82–C90: publication receipt, crash windows, lock contention, stale-owner and generation allocation.
- C91–C92: interval and product identity.
- C93–C95: strict manifest parsing, path/file identity and ambiguity.
- C96: reject WINDOW_GAP assignment under current profile.
- C97–C99: FINAL_ONLY, close-time and manifest binding.

Fixture PASS cannot prove Binance completeness or D2–D4 filesystem durability.

## 5. Remaining blockers and evidence limits

- REST completeness oracle: BLOCKED. No-trade, boundary, pagination, finality and correction semantics remain unresolved; RECONCILED_COMPLETE remains unavailable.
- Decimal preservation: BLOCKED. Pinned writer still has f64 conversion, fixed 12-decimal formatting and parse-error-to-zero.
- Filesystem/provider durability: NOT VERIFIED. No target lock, rename, fsync, crash/recovery or D2–D4 test was run.
- Producer interval/product identity implementation: NOT VERIFIED. Pinned source has not been changed.
- Manifest parser/receipt/lock implementation: NOT IMPLEMENTED.
- C01–C99: NOT EXECUTED.
- Independent review: PENDING; issue #138 must review exact final design SHA above and this record.
- Implementation and T1 activation: NOT AUTHORIZED by this documentation review.

## 6. Verification boundary and guardrails

Read-only GitHub inspection and documentation writes only. No source code changes, adapter implementation, tests, Binance REST request, GitHub Actions dispatch, VPS/runtime, T1 activation, T0/T2 changes, strategy/AI/ledger/risk changes, live orders, deletion, archive, cleanup, vacuum, compaction, backup expiry, restore or destructive operation.

T0 remains independent and canonical. No T1 writes to T0. Paper-only; AI_EXECUTION_ENABLED=false; no live orders; no OKX fallback/replacement.

## 7. Disposition and next step

**P1.10 DOCUMENTATION UPDATE COMPLETE / SAME-SESSION STATIC CONSISTENCY PASS / INDEPENDENT REVIEW REQUIRED / IMPLEMENTATION BLOCKED.**

Next step: update issue #138 and request a genuinely independent review against design blob SHA 32cf231227c52590ad1365473c6c742ab7dbc64a and this P1.10 record. Do not claim independent approval until an independent reviewer submits a written verdict. Preserve F01 REST, F05 decimal and F07 filesystem blockers.
