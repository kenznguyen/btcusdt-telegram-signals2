# P1.14 — Same-session adversarial self-review of corrected T1 contract

Date: 2026-11-09
Review type: Same-session static adversarial self-review; NOT independent.
Exact normative contract: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md`
Reviewed contract blob SHA: `59d8988a368a5bfffa94eacf7fbb8d769aea9b60`
Contract update commit: `5745248abed4fb02fa1a15688b1ba17771eaaa46`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

## Verdict

**DOCUMENTATION-LEVEL PASS for the requested F04/F05/F02 corrections and C117–C124 specification. IMPLEMENTATION READINESS NOT ESTABLISHED. F07 NOT VERIFIED. INDEPENDENT REVIEW REQUIRED.**

This review checks the exact final blob above. It is a same-session review and does not satisfy independent review or authorize implementation.

## Findings

### F04 — One authoritative initialization-record schema
Severity: HIGH
Disposition: PASS AT CONTRACT LEVEL

- §22.4 no longer defines a competing six-key schema; it explicitly defers to §22.9.
- §22.9 defines exactly eleven keys, including root-directory identity, filesystem/device identity, lock identity, owner UID/GID, directory/lock modes and timestamp.
- §22.10 explicitly states §22.9 is the sole authoritative schema and that the former six-key inventory is superseded.
- C121–C123 specify missing-key, extra-key and identity/owner/mode mismatch rejection.

No parser exists and these fixtures have not been implemented or run.

### F05 — One authoritative ExchangeInfo evidence-envelope schema
Severity: HIGH
Disposition: PASS AT CONTRACT LEVEL

- §22.5 now defers to the sole closed key/type inventory in §22.9 rather than defining a second abbreviated schema.
- §22.9 defines the envelope key/type inventory.
- §22.10 defines the captured lowercase response-header allowlist and omission semantics; unknown headers are not admitted and missing allowlisted headers are omitted.
- Raw response digest and exact unique BTCUSDT raw JSON slice requirements remain in §22.5; content addressing is explicitly not represented as protection against full host/root compromise.
- C124 covers missing/unknown envelope keys and header omission/rejection semantics.

No evidence store, raw-byte parser or retrieval test exists.

### F02 — Recovery fsync barrier and commit-acceptance linearization
Severity: HIGH
Disposition: PASS AT CONTRACT LEVEL / RUNTIME DURABILITY NOT VERIFIED

- §22.6.1 defines successful commits-directory fsync after no-replace receipt installation under the exclusive lock as the commit-acceptance linearization point.
- A visible receipt after restart is explicitly UNCONFIRMED when prior fsync completion cannot be proven.
- Recovery validates generation/counter/manifest/data/receipt state, fsyncs commits and generation directories, then persists a bound recovery checkpoint.
- A crash before checkpoint requires the full recovery procedure to repeat; failure quarantines.
- C117–C120 enumerate the key recovery crash/failure/missing-receipt cases.

Residual limitation: this is a contract protocol only. No implementation, process-crash test, host/power-loss test or target-filesystem durability evidence exists. A recovery fsync cannot establish guarantees beyond the semantics actually provided by the target filesystem/provider.

### Negative/crash fixtures
Disposition: SPECIFIED / NOT EXECUTED

C117–C124 now have individual scenario descriptions:
- C117–C120: receipt visibility/recovery barrier/checkpoint crash/missing consumed sequence.
- C121–C123: missing/extra initialization keys and identity/owner/mode mismatch.
- C124: evidence-envelope missing/unknown keys and header allowlist behavior.

The document requires each negative fixture to assert no accepted receipt, no canonical eligibility and no completeness watermark advancement. C01–C124 remain NOT IMPLEMENTED / NOT EXECUTED.

## Cross-checks and remaining blockers

- Current profile continues to forbid `RECONCILED_COMPLETE` and `reconciliation_evidence_ref`; source health remains fail-closed. This is documentation only, not parser proof.
- F03 topology is limited to one Linux host and verified local POSIX filesystem. Actual target mount/provider, flock, renameat2, file/directory fsync semantics remain NOT VERIFIED.
- Binance REST completeness/no-trade/boundary/pagination/finality/correction semantics remain NOT ACCEPTED.
- Pinned producer decimal-loss defect remains CONFIRMED: f64 conversion, fixed 12-decimal formatting and parse-error-to-zero; NOT FIXED.
- Producer FINAL_ONLY/product identity implementation NOT VERIFIED.
- Manifest, receipt, publication counter, ExchangeInfo evidence store and adapter NOT IMPLEMENTED.
- C01–C124 are design scenarios only; NOT IMPLEMENTED / NOT EXECUTED.
- No GitHub Actions run or artifact is claimed.

## Required next actions

1. Retarget issue #138 to exact contract blob SHA `59d8988a368a5bfffa94eacf7fbb8d769aea9b60` and request genuinely independent adversarial review.
2. Wait for written independent findings tied to this exact SHA.
3. Do not implement or activate T1 until independent review, F07 evidence and the other known blockers are resolved and separately approved.

## Authorization and safety boundary

Documentation and review only. No source code, test execution, GitHub Actions dispatch, Binance REST request, VPS/runtime, T0/T1/T2 runtime, T1 activation, strategy/AI/ledger/risk/trading change, data deletion, archive, cleanup, vacuum, compaction, backup expiry, restore or destructive operation.

T0 remains independent/canonical. No T1 writes to T0. Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.
