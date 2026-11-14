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


## 7. Owner-supplied candidate file — follow-up inspection (2026-11-14)

The owner supplied an attachment named `BTCUSDT.csv`. The uploaded path was inspected without modifying the file. Its content is GZIP (magic bytes `1f 8b 08`), despite the `.csv` filename.

### 7.1 Preserved-byte and independent-process checks

| Check | Result |
|---|---|
| Uploaded object size | 1,431,960 bytes |
| SHA-256 of exact uploaded compressed bytes | `71963e8235106ae36fe386ef0fbd52b078df48ea854d09d814469eddeed58a8c` |
| GZIP decompression / trailer integrity | PASS |
| Decompressed payload size | 12,337,426 bytes |
| Separate-process reopen of uploaded path | PASS — same size, SHA-256 and successful GZIP decompression |
| Formal D07.11 sidecar/reference-index custody resolution | NOT RUN |
| Immutable external custody / original provider transfer receipt | NOT VERIFIED |

The separate process reopened the uploaded path from disk, independently recomputed the compressed-byte length and SHA-256, and decompressed it successfully. This is a bounded readback check of the attachment, not a complete D07.11 sidecar/custody proof.

### 7.2 CSV structure and coverage observations

- Header (11 columns): `exchange,symbol,timestamp,local_timestamp,funding_timestamp,funding_rate,predicted_funding_rate,open_interest,last_price,index_price,mark_price`.
- Data rows: **98,211**.
- All rows declare `exchange=binance-futures` and `symbol=BTCUSDT`.
- `timestamp` range: 2026-11-01 00:00:00.000000 UTC through 2026-11-01 23:59:57.002000 UTC; nondecreasing.
- `local_timestamp` range: 2026-11-01 00:00:00.062732 UTC through 2026-11-01 23:59:57.063032 UTC; nondecreasing.
- All `timestamp` and `local_timestamp` values fall within the requested half-open UTC day.
- `timestamp` has 13,953 duplicated key values (14,613 additional rows beyond one row per distinct timestamp; maximum multiplicity 3). This is recorded as an observation, not automatically classified as corruption.
- `local_timestamp` has 2 duplicated key values (2 additional rows; maximum multiplicity 2).
- Four distinct `funding_timestamp` values occur: 2026-11-01 00:00, 08:00 and 16:00 UTC, plus 2026-11-02 00:00 UTC. The first event has no strictly earlier observation in this daily file; the other three have a prior observation in the file.
- Every row has `funding_rate=0.0001`; `predicted_funding_rate` is empty in all rows. `open_interest` is empty in 2 rows and `last_price` in 3 rows. Other listed fields are populated in all rows.

### 7.3 Provenance and semantic limits

The file's internal fields are consistent with the intended exchange, symbol and date, but those fields are self-declared content. The attachment does **not** establish that its compressed bytes were downloaded from the expected Tardis URL. No dataset-endpoint HTTP status/headers, response metadata, signed provider receipt, download log or independently authenticated provider origin accompanied it. Therefore:

- Candidate file received and structurally inspected: **PASS — ATTACHMENT CONTENT ONLY**.
- Exact Tardis URL / provider-origin provenance: **NOT VERIFIED**.
- Compressed-byte integrity for the supplied attachment: **PASS — SHA-256 and GZIP**.
- Separate-process attachment readback: **PASS — LIMITED**.
- Formal D07.11 custody sidecar/reference-index gate: **NOT RUN**.
- D07.7 settlement-key overlap and settlement-rate suitability: **NOT PERFORMED / NOT VERIFIED**. The four observed event timestamps and constant in-file rate are not, by themselves, proof of settlement equivalence.
- Enumeration/global completeness, feed-gap completeness, freshness, issuer authenticity, collector-path independence and factual truth: **NOT VERIFIED**.

The earlier endpoint-transfer blocker remains an accurate record of that attempt. This attachment provides a candidate data object for further bounded verification; it does not retroactively prove the endpoint transfer or provider provenance.

### 7.4 Disposition and boundary

D07.13 is now **PARTIAL PASS — ATTACHMENT RECEIVED, BYTE INTEGRITY AND BASIC STRUCTURE VERIFIED; PROVIDER PROVENANCE AND SETTLEMENT OVERLAP NOT VERIFIED**. D07.2 `BLOCKED_SHARED_LINEAGE` remains unchanged; D07 remains **PARTIAL**; PAPER ledger bootstrap remains **BLOCKED / NOT APPROVED**.

No raw attachment was committed to GitHub. No parser/verifier code, D07.2/D07.8 logic, funding row, ledger/database, T0/VPS, Runner/One-shot, exchange credentials, live execution or order state was changed. This was an evidence/documentation-only increment; no CI run or artifact was produced.
