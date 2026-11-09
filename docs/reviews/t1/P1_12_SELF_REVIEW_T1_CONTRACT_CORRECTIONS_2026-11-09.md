# P1.12 — Same-session self-review of T1 contract corrections

Date: 2026-11-09
Review type: Same-session static adversarial review; NOT independent.
Verdict: **DOCUMENTATION-LEVEL PASS FOR F01–F06 CORRECTIONS / IMPLEMENTATION READINESS NOT ESTABLISHED / INDEPENDENT REVIEW REQUIRED.**

## 1. Exact reviewed target

- Repository: kenznguyen/btcusdt-telegram-signals2
- Branch: feature/t0-centralized-data-feeder-p1-20261101
- Normative design: docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md
- Exact final design blob SHA: 4034d740c9694ef0d9da7d81cc1d1055a0175302
- P1.11 same-session self-review blob: 08662369f1093658cdd42d56ede01a5b985e0f82
- Pinned producer source SHA: 6e20fe94f3ad64cc450e73def80a167fe371e49e
- Independent review issue: #138, to be retargeted to this exact design SHA.

This is not an independent review and cannot satisfy the independent-review gate.

## 2. P1.11 finding disposition

### F01 CRITICAL — RECONCILED_COMPLETE false-PASS path: ADDRESSED AT CONTRACT LEVEL

P1.12 §22.1 explicitly forbids RECONCILED_COMPLETE under the current v1.1/P1.3 profile, rejects the state and reconciliation_evidence_ref, limits source_health to UNKNOWN/INVALIDATED, and prohibits canonical completeness/sealing/aggregation. Future completeness requires a new versioned evidence profile, independent review and owner approval.

Static consistency: PASS at documentation level. No implementation or parser test exists.

### F02 HIGH — publication_sequence allocation and crash/no-reuse: ADDRESSED AT CONTRACT LEVEL

P1.12 §22.2 defines a per-generation durable publication-counter.json, reserve-before-manifest ordering, file and directory fsync, permanently consumed reservations, allowed sequence gaps, no reuse, consistency checks against receipts/manifest/checkpoint, and quarantine on ambiguity. C100–C103 are added.

Static consistency: PASS at documentation level. Counter implementation and crash tests NOT VERIFIED.

### F03 HIGH — lock topology and initialization: ADDRESSED AT CONTRACT LEVEL

P1.12 §22.3 restricts the reference profile to one Linux host and one verified local POSIX filesystem; excludes network/multi-host/overlay/object-store topologies; specifies flock(2), O_CLOEXEC/O_NOFOLLOW, shared/exclusive locking, offline single-operator initialization, stable inode checks and fail-closed recovery. C104–C108 are added.

Static consistency: PASS at documentation level. The actual Scaleway/VPS filesystem, mount, device/provider, flock and sync behavior remain NOT VERIFIED. No runtime compatibility claim is made.

### F04 HIGH — schema ambiguity: ADDRESSED AT DOCUMENTATION LEVEL, MACHINE SCHEMA NOT IMPLEMENTED

P1.12 §§22.4 and 22.9 specify canonical primitive encodings, exact receipt/counter/initialization/evidence-envelope key sets and types, UUID/hash/timestamp/path rules, root-directory and lock identity, owner/mode, no-follow and link-count constraints, raw ExchangeInfo duplicate-key rejection and exact source-slice digesting.

Residual limitation: this remains prose contract, not a generated machine-readable schema or executable parser. The exact OS mapping of stable file identity must be independently reviewed for the selected Linux filesystem.

### F05 HIGH — ExchangeInfo evidence immutability/provenance: ADDRESSED AT CONTRACT LEVEL

P1.12 §§22.5 and 22.9 define raw-response-byte content addressing, immutable no-overwrite storage, evidence envelope, endpoint/request/response metadata, exact unique BTCUSDT symbol raw-byte slice digest, duplicate-key rejection and fail-closed retrieval/mismatch handling.

Static consistency: PASS at documentation level. Evidence store, raw-byte parser and source capture are NOT IMPLEMENTED/TESTED. Content addressing detects corruption/replacement against a trusted digest; it does not protect against full local-root/host compromise.

### F06 MEDIUM — receipt no-replace and orphan handling: ADDRESSED AT CONTRACT LEVEL

P1.12 §22.6 requires Linux renameat2(RENAME_NOREPLACE), fail-closed when unavailable, commits-directory fsync before lock release, full directory enumeration and quarantine for collision, replacement suspicion, duplicate, malformed, orphan or unexpected entries. C113–C116 are added.

Static consistency: PASS at documentation level. Kernel/filesystem support and implementation are NOT VERIFIED.

## 3. Cross-section consistency and false-PASS checks

Reviewed the precedence of §22 over the earlier v1.1 sections and checked that:
- Current profile cannot accept RECONCILED_COMPLETE or reconciliation_evidence_ref.
- A publication receipt is explicitly not a source-completeness proof.
- The watermark field is non-authoritative observed progress only and cannot authorize canonical aggregation.
- Publication sequence reservation precedes manifest preparation and consumed values are never reused.
- A visible manifest without its matching receipt remains uncommitted.
- Receipt final publication is no-replace; readers validate the full receipt directory.
- Unsupported lock topology or unavailable filesystem primitives fail closed.
- ExchangeInfo evidence binds exact raw response bytes and a unique exact symbol-record slice.
- C100–C116 are marked planned, not implemented or executed.
- The original P1.3 REST uncertainty, decimal serialization defect and T0/T1 authorization boundaries remain intact.

No additional internal contradiction or newly identified false-PASS path was found in this documentation-only pass.

One non-blocking naming concern is retained: `watermark_open_time_exclusive_ms` remains in the legacy manifest/receipt shape even though §22.1 demotes it to a non-authoritative observed-progress cursor. Any future schema version should rename it to avoid semantic confusion; current v1.1 must never treat it as a completeness watermark.

## 4. F07 and unchanged evidence blockers

F07 is not resolved by documentation:
- Target filesystem/mount/device/provider identity NOT VERIFIED.
- flock, atomic rename, fsync/fdatasync, directory fsync and renameat2(RENAME_NOREPLACE) behavior NOT VERIFIED on the target.
- No authorized host/power/provider crash-recovery test has run.
- Producer f64 conversion, fixed 12-decimal formatting and parse-error-to-zero defect remains CONFIRMED / NOT FIXED.
- Binance REST completeness/no-trade/boundary/pagination/finality/correction semantics remain NOT ACCEPTED.
- Producer FINAL_ONLY/product identity implementation NOT VERIFIED.
- Manifest, receipt, counter, ExchangeInfo evidence store and adapter are NOT IMPLEMENTED.
- C01–C116 are design scenarios only; NOT IMPLEMENTED / NOT EXECUTED.
- No GitHub Actions run or artifact is claimed.

## 5. Verdict and authorization boundary

**P1.12 F01–F06 DOCUMENTATION CORRECTIONS PASS AT CONTRACT LEVEL / F07 EVIDENCE GATE OPEN / INDEPENDENT REVIEW REQUIRED / IMPLEMENTATION NOT AUTHORIZED.**

The contract is ready to be submitted for genuinely independent adversarial review on exact blob SHA 4034d740c9694ef0d9da7d81cc1d1055a0175302. This does not mean it is approved for implementation or runtime use.

No source implementation, test execution, GitHub Actions dispatch, Binance REST request, VPS/runtime, T1 activation, T0/T2 change, strategy/AI/ledger/risk/trading change, deletion, archive, cleanup, vacuum, compaction, backup expiry, restore or destructive operation was performed.

T0 remains independent/canonical. No T1 writes to T0. Paper-only; AI_EXECUTION_ENABLED=false; no live orders; no OKX fallback/replacement.
