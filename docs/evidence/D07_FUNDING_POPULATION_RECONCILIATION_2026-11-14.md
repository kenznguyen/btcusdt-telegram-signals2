# D07 — Persisted Funding Population Reconciliation and Readiness Gate

Date: 2026-11-14  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Implementation source SHA: `26985d839b2ea4e4b86222a7aeeef5a26ba75953`  
Disposition: **PASS — synthetic test/CI integration; real population completeness NOT VERIFIED**

## Approved scope

Owner approved D07 implementation limited to synthetic fixtures and GitHub Actions. This increment does not authorize real account evidence ingestion, production database use, VPS operations, T0 mutation, Runner/One-shot execution, exchange credentials or orders.

## Implementation

### 1. Deterministic expected-vs-observed reconciliation

Added `paper_execution/funding_reconciliation.py` and contract tests.

- Compares `EXPECTED_FUNDING_EVENTS` against `OBSERVED_FUNDING_EVENTS` over an identical half-open interval `[startAtMs, endAtMs)` and quote currency.
- Each event requires a unique event ID, integer timestamp, exact Decimal string amount and SHA-256 payload reference.
- Binary floating-point amounts, malformed hashes, unknown fields, out-of-window events and invalid population schemas are rejected.
- Event inventories are canonicalized by event identity before reconciliation hashing; each population is capped at 100,000 events.
- Classifies matched, missing, unexpected and duplicate events. Same-ID content mismatch is represented as missing plus unexpected.
- Any unresolved missing, unexpected or duplicate event returns `BLOCKED`; a clean comparison returns only `COMPLETE_WITHIN_DECLARED_POPULATION`.

The output intentionally retains:
- `independence=DECLARED_NOT_VERIFIED`
- `globalCompleteness=NOT_VERIFIED`
- `freshness=NOT_VERIFIED`
- `issuerAuthenticity=NOT_VERIFIED`

Different caller-supplied population IDs, source labels and snapshot IDs are not proof of real independence or issuer identity.

### 2. Durable reconciliation evidence — schema migration v10

Added immutable `paper_funding_reconciliations` with:
- reconciliation ID and exact canonical result document;
- declared interval and currency;
- expected and observed snapshot IDs;
- reconciliation status, exact-document SHA-256 and recorded timestamp.

Migration v10 adds the coverage-to-certificate reference, immutable update/delete triggers, a verified-coverage insertion guard, a trigger preventing event insertion into already certified intervals, and an event-time index. Existing VERIFIED coverage without D07 evidence demotes account readiness; it is not silently upgraded.

### 3. Fail-closed funding lifecycle

- Funding events can be staged before coverage certification. Staging immediately sets `riskReady=false` before equity refresh, preserving the prior high-water mark.
- `record_funding_reconciliation` independently enumerates persisted ledger funding events for the declared interval and persists the reconciliation document plus audit record.
- `record_funding_coverage(status="VERIFIED")` now requires a matching COMPLETE certificate, exact interval/currency/expected snapshot, recorded-time ordering and a current observed-population digest.
- Once a coverage interval is VERIFIED, additional funding events in that interval are blocked by both the API and SQLite trigger. New events must be staged in an uncovered interval and reconciled before coverage is certified.
- Account equity cutover rechecks the current event-population digest against the certificate.
- The read-only account risk snapshot re-enumerates the current funding events and compares the digest; missing, stale or tampered evidence fails closed.
- Reconciliation or coverage alone never sets readiness true. The existing equity cutover remains the transition that may establish readiness.

### 4. Bootstrap contract

The Dual Ledger bootstrap manifest now requires `fundingExpectedPopulation`, which is included in the exact funding evidence document and bound by its SHA-256 and existing manual Owner attestation.

Fresh-account bootstrap v1 currently accepts only an empty expected funding-event list because the new account has no imported historical funding events. Non-empty historical funding import is not implemented in this increment and must fail closed until a separately approved ingestion workflow exists.

## TDD and CI evidence

- Focused bootstrap contract: **13/13 PASS**.
- D07 pure reconciliation contract: **14/14 PASS**.
- D07 persistence and coverage gate contract: **12/12 PASS**.
- Full PaperLedger regression: **466/466 PASS** in 134.895 seconds.
- Compile, disposable PAPER-only environment guard and artifact upload: PASS.

Final workflow:
- [GitHub Actions run 43514850131](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43514850131)
- Exact tested source SHA: `26985d839b2ea4e4b86222a7aeeef5a26ba75953`
- Job: `132195060968`, SUCCESS.
- Artifact ID: `14080886334`
- Artifact name: `dual-ledger-bootstrap-proof-26985d839b2ea4e4b86222a7aeeef5a26ba75953`
- Size: 11,924 bytes.
- GitHub-reported ZIP digest: `sha256:d9e57e419cc3061193f3dd0f192da4b47c8c05ccc21829fd7ae2ca9f4875ae24`.
- Expires: 2026-11-20T21:54:54Z.
- Artifact payload digest has not been independently recomputed.

Adjacent compatibility evidence:
- Core-First operational proof [43514137221](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43514137221), source `92168d6efedece4f92b969da37ce99a78`? **Use workflow metadata for exact SHA:** `92168d6efedece4f92b969da37ce99a78` is not a verified source pin here; the exact source pin for that run is `92168d6efedece4f92b969da37ce99a78` only if independently confirmed. This adjacent run is not used as the D07 implementation proof.
- Paper Ledger T1 compatibility [43514137410](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43514137410): 100 tests PASS at the preceding compatible source. The D07 proof above remains the authoritative exact-SHA regression.

## Status and limits

- D07 reconciliation engine: **PASS**.
- Persisted certificate, audit and fail-closed VERIFIED coverage gate: **PASS** in disposable CI.
- Cutover and read-only risk-snapshot revalidation: **PASS** in regression.
- Real external expected-population source and actual independence: **NOT VERIFIED**.
- Real issuer authenticity, external source-byte readback, factual truth, global completeness and freshness: **NOT VERIFIED**.
- Real funding-event import and non-empty bootstrap population: **NOT IMPLEMENTED**.
- Production bootstrap: **BLOCKED / NOT APPROVED**.

No VPS, production database, T0, Runner, One-shot, exchange credentials or real orders were touched. All tests use temporary SQLite and synthetic fixtures. Paper-only restrictions and `AI_EXECUTION_ENABLED=false` remain unchanged.

## Next bounded step

Keep production bootstrap blocked. The next design decision is the provenance contract for a genuinely independent expected funding population source and its evidence readback. Do not connect a real source or use real account data without a separate, exact-scope approval.
