# P1.13 — Same-session adversarial self-review of P1.12 T1 contract

Date: 2026-11-09
Review type: Same-session static adversarial review; NOT independent.
Exact target: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md`
Reviewed blob SHA: `4034d740c9694ef0d9da7d81cc1d1055a0175302`
Target commit recorded by P1.12: `353f6b0ff11a379b53da6292682eefa09073f5f8`
Pinned producer: `kenznguyen/binance-futures-collector@6e20fe94f3ad64cc450e73def80a167fe371e49e`

## Verdict

**REQUEST CHANGES — P1.12 F01/F02/F03/F05/F06 are substantially specified at contract level, but F04 is NOT CLOSED because the initialization-record schema is contradictory. F07 remains NOT VERIFIED. Implementation readiness is NOT ESTABLISHED.**

This is a self-review, not an independent review. It does not satisfy issue #138.

## Findings

### F01 — Current-profile completeness fail-closed
Severity: HIGH
Disposition: PASS AT DOCUMENTATION LEVEL

Section 22.1 explicitly prohibits `RECONCILED_COMPLETE` and `reconciliation_evidence_ref`, limits accepted source_health to UNKNOWN/INVALIDATED, and demotes the retained watermark field to a non-authoritative observed-progress cursor. Section 22.4 binds the manifest schema to those constraints. The older clauses in §§4.2–4.3 and §21.5 conflict, but §22 explicitly states that it supersedes those clauses. No current-profile completeness or canonical aggregation path is authorized by the text.

Residual: this is not parser/adapter evidence. A future implementation must test legacy enum values and receipt-derived views fail closed.

### F02 — Durable publication sequence and crash recovery
Severity: HIGH
Disposition: PARTIAL — DESIGN SPECIFIED, RECOVERY PROOF NOT ESTABLISHED

Section 22.2 establishes reserve-before-manifest, file fsync, atomic counter replacement, generation-directory fsync, permanent sequence consumption, and quarantine on ambiguous state. This is a materially improved protocol.

Gap: C103 covers a crash after receipt rename but before commits-directory fsync, yet the recovery rule does not explicitly require recovery to revalidate and fsync the commits directory (and relevant parent directory state) before treating a surviving receipt as a durable accepted commit. Visibility after restart is not itself proof that the pre-crash directory fsync completed. Specify the recovery barrier and exact acceptance linearization point; otherwise retain quarantine/NOT COMMITTED.

The counter and crash protocol are not implemented or tested.

### F03 — Filesystem topology and writer lock
Severity: HIGH
Disposition: PASS AT CONTRACT LEVEL / TARGET NOT VERIFIED

Section 22.3 restricts the reference profile to one Linux host and one verified local POSIX filesystem, requires flock(2), stable lock identity and offline initialization, and excludes network/multi-host/overlay/object-store topologies.

Actual target mount/provider, stable identity mapping, flock behavior, atomic rename, fsync, directory fsync and renameat2 support remain NOT VERIFIED. This is not runtime approval.

### F04 — Closed schemas and initialization identity
Severity: HIGH
Disposition: REQUEST CHANGES — CONTRADICTION CONFIRMED

Section 22.4 states that the source-root initialization record has exactly six keys:
- record_version
- source_root_id
- filesystem_id
- device_id
- lock_file_id
- initialized_at_utc

Section 22.9 then states that the same initialization record has exactly eleven keys, adding:
- root_directory_id
- owner_uid
- owner_gid
- directory_mode
- lock_file_mode

Both clauses use normative “exactly” language. Section 22.9 does not explicitly declare the six-key definition in §22.4 superseded. A strict closed-schema implementation cannot satisfy both definitions. Therefore F04 is not closed.

Required correction: define one authoritative initialization-record schema in one place, explicitly supersede the other inventory, and ensure all identity/owner/mode fields have one exact key/type/encoding contract. Add positive and negative fixtures for missing/extra keys and identity/mode mismatch.

### F05 — ExchangeInfo evidence
Severity: HIGH
Disposition: PARTIAL — CORE BINDING SPECIFIED

Section 22.5 binds the exact raw response bytes and unique BTCUSDT raw symbol-record slice, with content-addressed immutable storage and fail-closed retrieval. Section 22.9 adds a closed evidence-envelope key/type inventory.

Clarify one authoritative field inventory and the precise captured response-header allowlist/absence semantics. No evidence store, byte-preserving parser or retrieval test exists. Content addressing is not protection against full local-root/host compromise, as the document correctly limits the claim.

### F06 — Immutable receipt no-replace
Severity: MEDIUM
Disposition: PASS AT CONTRACT LEVEL / IMPLEMENTATION NOT VERIFIED

Section 22.6 requires renameat2(RENAME_NOREPLACE), no overwrite fallback, receipt-directory fsync, full directory enumeration and quarantine on collision/orphan/unexpected entries. C113–C116 cover the principal negative cases.

The actual kernel/filesystem primitive and crash behavior are unverified. Recovery acceptance after C103 must be aligned with F02 above.

### F07 — Target filesystem durability
Severity: HIGH
Disposition: OPEN / NOT VERIFIED

No evidence establishes the intended VPS filesystem/mount/device/provider or its flock, renameat2, file fsync, directory fsync and crash/power-loss behavior. No target-runtime test was authorized or run.

## Cross-checks and unchanged blockers

- P1.3 Binance REST completeness/no-trade/boundary/pagination/finality/correction semantics remain NOT ACCEPTED.
- Producer decimal loss remains CONFIRMED: f64 conversion, fixed 12-decimal formatting and parse-error-to-zero; NOT FIXED.
- FINAL_ONLY and product identity producer implementation NOT VERIFIED.
- Manifest, receipt, publication counter, ExchangeInfo evidence store and adapter NOT IMPLEMENTED.
- C01–C116 are contract scenarios only; NOT IMPLEMENTED / NOT EXECUTED.
- No GitHub Actions run or artifact is claimed for this review.
- Handoff currently records P1.12 as a contract-level PASS; this review supersedes that assessment for implementation-readiness purposes. P1.12 document changes remain present, but F04 must be corrected and F02 recovery semantics clarified.

## Required next actions

1. Correct F04 to one exact initialization-record schema; reconcile the evidence-envelope inventory at the same time.
2. Clarify F02/C103 recovery fsync and commit-acceptance linearization.
3. Add negative fixtures for schema key-set conflict, recovery after receipt rename-before-directory-fsync, and recovery barrier failure.
4. Re-run same-session static review on the new exact blob SHA.
5. Keep issue #138 open and obtain a genuinely independent review of the corrected SHA.
6. Do not implement, run tests, dispatch Actions, access REST/VPS, or activate T1 without separate approval and evidence gates.

## Authorization and safety boundary

Review/documentation only. No source code, tests, Actions dispatch, REST request, VPS/runtime, T0/T1/T2, strategy/AI/ledger/risk/trading change, T1 activation, deletion, archive, cleanup, vacuum, compaction, backup expiry, restore or destructive operation.

T0 remains independent/canonical. No T1 writes to T0. Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.
