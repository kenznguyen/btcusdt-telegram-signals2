# D07.13 — Pilot Acquisition Attempt Record (Blocked Before Data Transfer)

Date: 2026-11-14  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Approved pilot date: `2026-11-01` UTC  
Interval: `[2026-11-01T00:00:00Z, 2026-11-02T00:00:00Z)`  
Disposition: **BLOCKED — NO RAW DATA ACQUIRED**

## 1. Approved scope

The owner confirmed the one-day pilot:
- Provider: Tardis.
- Exchange dataset ID: `binance-futures` (Binance USDS-M Futures).
- Dataset type: `derivative_ticker`.
- Dataset symbol: `BTCUSDT`, perpetual.
- Date: 2026-11-01 UTC.
- No credentials, no VPS/T0, no ledger/database writes, no Runner/One-shot and no live execution.
- Intended object: one daily gzip CSV file, preserving original compressed bytes.

## 2. Provider metadata verification

A live read of Tardis public exchange metadata endpoint `https://api.tardis.dev/v1/exchanges/binance-futures` returned HTTP 200 and confirmed:
- `id=binance-futures`, `name=Binance USDS-M Futures`, `enabled=true`.
- `datasets.exportedUntil=2026-11-14T00:00:00.000Z`.
- The `datasets.symbols[]` entry for `BTCUSDT` declares `type=perpetual`.
- `derivative_ticker` is among its supported dataset types.
- Dataset availability begins 2019-11-17 and metadata `availableTo` is 2026-11-14.

The requested date is the first day of the month, which provider documentation says is available without an API key. The expected single-file URL is:

`https://datasets.tardis.dev/v1/binance-futures/derivative_ticker/2026/11/01/BTCUSDT.csv.gz`

References:
- Exchange metadata: https://api.tardis.dev/v1/exchanges/binance-futures
- Dataset API and first-of-month access: https://docs.tardis.dev/downloadable-csv-files/api
- Derivative ticker schema: https://docs.tardis.dev/downloadable-csv-files/data-types

The metadata response confirms dataset/type/symbol availability and export watermark only. It does not prove the exact daily file exists, is non-empty, or contains complete observations.

## 3. Acquisition attempt and blocker

- The binary dataset endpoint could not be opened by the available web retrieval interface; it returned an unsupported/inaccessible response for the gzip object.
- The controlled container download facility refused to start the transfer because the URL could not be verified as an accessible opened page by that facility.
- No bytes were transferred. No raw file exists in the working container.
- No file size, HTTP response headers/status from the dataset endpoint, compressed-byte SHA-256, gzip validation, decompressed row count, independent readback or settlement comparison is available.
- No alternate proxy, VPN, alternate region, credential, account session, or alternate download path was attempted.

This is an environment/tooling limitation, not evidence that Tardis lacks the file or denied access. The pilot is therefore **BLOCKED before data transfer**, not a provider-side failure.

## 4. Evidence status

| Check | Result |
|---|---|
| Exact exchange ID / dataset symbol / type | PASS — metadata |
| Export watermark covers target date | PASS — metadata only |
| First-of-month no-key eligibility | DOCUMENTED |
| Exact dataset endpoint file availability | NOT VERIFIED |
| Raw gzip bytes acquired | NO |
| Original byte preservation | NOT VERIFIED |
| Byte length / SHA-256 | NOT VERIFIED |
| Gzip integrity / CSV schema | NOT VERIFIED |
| Independent preserved-copy readback | NOT PERFORMED |
| D07.7 settlement overlap | NOT PERFORMED |
| Collector-path independence | NOT VERIFIED |
| Enumeration/global completeness, freshness, issuer authenticity and factual truth | NOT VERIFIED |

## 5. Stop conditions and next step

No retries or alternate access routes are authorized by this attempt. To continue, the owner must provide an approved acquisition environment/storage destination that can retrieve the exact public gzip URL without credentials and preserve the original bytes, or provide the original downloaded file as an attachment. A subsequent step can then verify the bytes and perform independent readback against the preserved copy under D07.11.

Any use of VPS/T0, account credentials, paid entitlement, alternate network route, broader date range, raw HTTP replay API or additional datasets requires separate explicit approval.

## 6. Overall disposition

- D07.13 pilot metadata verification: **PASS — METADATA ONLY**.
- D07.13 real acquisition: **BLOCKED BEFORE TRANSFER**.
- Raw data, custody, byte integrity/readback and settlement comparison: **NOT VERIFIED / NOT PERFORMED**.
- D07.2 `BLOCKED_SHARED_LINEAGE`: unchanged.
- D07: **PARTIAL**.
- PAPER ledger bootstrap: **BLOCKED / NOT APPROVED**.

No repository code, D07.2/D07.8 verifier, funding row, ledger/database, T0/VPS or runtime state was changed. No CI was run because this is a documentation-only evidence record.
