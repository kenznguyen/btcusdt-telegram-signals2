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


## 8. Owner-approved read-only D07.11 / D07.7 follow-up (2026-11-14)

Scope approved by the owner: inspect only this exact supplied attachment; perform bounded independent readback and offline comparison preparation; no acquisition, credentials, T0/VPS, ledger/database writes, funding imports, Runner/One-shot or live execution.

### 8.1 D07.11 readback worker result

The existing D07.11 `readback_worker.py` behavior was executed as a separate Python process against the supplied attachment path, using the repository worker implementation (file blob `80de53fae978dd8a706544a0fc762ac66103886f`).

Result:
- `ok=true`
- `byteLength=1431960`
- `sha256=71963e8235106ae36fe386ef0fbd52b078df48ea854d09d814469eddeed58a8c`

This independently reopens the exact attachment using the worker's no-follow file access and recomputes the digest. It corroborates the earlier separate-process check.

**Formal D07.11 resolver disposition: NOT RUN / NOT VERIFIED.** The supplied attachment is not accompanied by an authoritative D07.8 evidence-package `manifest.json`, a D07.9 lineage sidecar, or the complete offline evidence reference index. Creating those declarations from the attachment's own observed hash would be circular and would not establish the acquisition/custody facts. Therefore no formal D07.11 reference-resolution or package-bound raw-file PASS is claimed.

### 8.2 D07.7 settlement-key preparation

The existing D07.7 comparator contract was applied offline. Source comparator file blob: `d677c7d101fd3c659e7c73785d9735dd2ff692d4`; implementation/test evidence remains the prior CI-tested source SHA `0fe30e16018203d6aada91497eb6013a58b71607`.

The D07.7 key is exact venue settlement timestamp in integer milliseconds, under identity:
- venue `BINANCE`;
- instrument `BTCUSDT`;
- market type `USD_M_FUTURES`;
- contract type `PERPETUAL`;
- margin and settlement assets `USDT`.

For each distinct `funding_timestamp`, candidate normalization selected the latest `timestamp` strictly earlier than that funding event, retaining `local_timestamp` as a separate arrival-time field and not using it as the settlement key.

| Funding event UTC | Latest earlier exchange timestamp UTC | Rows tied at latest timestamp | Rate value(s) |
|---|---|---:|---|
| 2026-11-01 00:00:00 | No earlier row in this file | — | Not derivable from this file |
| 2026-11-01 08:00:00 | 2026-11-01 07:59:59.504 | 2 | `0.0001` |
| 2026-11-01 16:00:00 | 2026-11-01 15:59:59.000 | 1 | `0.0001` |
| 2026-11-02 00:00:00 | 2026-11-01 23:59:57.002 | 1 | `0.0001` |

At the 08:00 event, two rows share the latest exchange timestamp; both carry the same rate but have different local receive timestamps. This tie is preserved as an ambiguity/diagnostic and is not silently collapsed into a claim of unique final message. The 00:00 event at the start of the file has no strictly earlier observation in the supplied day.

Three candidate Tardis-normalized observations were passed to the D07.7 comparator with an empty Binance input because the original Binance D07.6 response bytes/parsed observations are not present among the currently supplied files. Result:
- `observationCorroboration=NOT_VERIFIED_NO_OVERLAP`
- `matchedCount=0`
- `mismatchCount=0`
- `unmatchedBinanceCount=0`
- `unmatchedTardisCount=3`
- `issuerIndependence=NOT_VERIFIED_SAME_ISSUER`
- `collectorIndependence=NOT_VERIFIED`
- completeness, authenticity, freshness and factual truth remain `NOT_VERIFIED`.

This is a fail-closed no-counterpart diagnostic, **not** a real Binance-vs-Tardis overlap comparison and not observation corroboration. No timestamp tolerance, assumed schedule, or other venue substitution was used.

### 8.3 Disposition and next gate

- Attachment compressed-byte integrity and GZIP: **PASS**.
- D07.11 independent worker readback: **PASS — LIMITED TO THE ATTACHMENT PATH**.
- Formal D07.11 sidecar/reference-index/package-bound resolver: **NOT RUN / NOT VERIFIED** (required package/sidecar/index inputs absent).
- Tardis candidate settlement normalization: **PARTIAL — 3 candidate events; one event has no prior row; one event has a tied latest exchange timestamp**.
- D07.7 actual two-source overlap: **NOT PERFORMED — Binance source bytes/normalized observations unavailable in this approved evidence set**.
- D07.7 comparator diagnostic with empty Binance side: **NOT_VERIFIED_NO_OVERLAP**; not a corroboration PASS.
- D07.2 `BLOCKED_SHARED_LINEAGE`: unchanged. D07 overall: **PARTIAL**. PAPER ledger bootstrap: **BLOCKED / NOT APPROVED**.

Next gate requires the exact original Binance D07.6 response bytes (or a previously verified, immutable copy and its parser output) to be supplied into this bounded offline evidence review, plus the actual D07.8 manifest, D07.9 sidecar and evidence reference index for formal D07.11 resolution. No VPS/T0 access or database/ledger import is implied. No files were committed from the attachment. No code was changed; no CI run/artifact was produced.

## 9. Owner-pasted VPS read-only D07.6 capture verification and three-event comparison (2026-11-14)

The owner ran the previously supplied read-only commands on `ubuntu@scw-optimistic-jang` and pasted the complete terminal output into this review. The assistant did not establish an SSH session and did not independently access the VPS. Results below are therefore recorded as **owner-provided terminal evidence**, not assistant-observed host evidence.

### 9.1 Capture directory and raw-byte identity

Directory: `/tmp/d07-6-binance-20261114T051131Z`.

Owner-provided inventory showed:
- `response_body.bin`: 63,043 bytes, mtime 2026-11-14 05:11:32 UTC.
- `retrieved_at_utc.txt`: 21 bytes.
- `http_status.txt`: 4 bytes.
- `response_headers.txt`: 889 bytes.
- `provenance-envelope.json`: 1,629 bytes.

The owner-pasted read-only verification returned:
- HTTP status file: `200`.
- Retrieval timestamp: `2026-11-14T05:11:31Z`.
- Response header: `HTTP/2 200`, `content-type: application/json;charset=UTF-8`, `content-length: 63043`.
- Exact response-body length: `63043`.
- SHA-256: `71eece4bd1d885eb090516c63bf261023f207a53747c6c1d9aa55eae1743b526`.

The size and digest match the previously recorded D07.6 capture. The owner-pasted JSON inspection showed a root array of 500 records; first record fundingTime `1780243200004`, last record fundingTime `1794614400004`. A subsequent owner-pasted structural check showed 500 unique fundingTime values, nondecreasing order, no duplicate fundingTime, and all 500 records with `rateType=Regular`. Most common interval is 28,800,000 ms (8 hours), with small millisecond variations. This is a bounded structural check of the captured page, not proof of endpoint-wide enumeration completeness.

### 9.2 Provenance-envelope assessment

The owner-pasted envelope declares:
- schemaVersion 1; evidenceSnapshotId `d07-6-binance-btcusdt-20261114T051131Z`;
- one page, ordinal 0, relativePath `response_body.bin`, byteLength 63043, recordCount 500;
- page SHA-256 `sha256:71eece4bd1d885eb090516c63bf261023f207a53747c6c1d9aa55eae1743b526`;
- `nextCursor=null`, `sourceTotal=null`, `terminal=true`;
- acquisition method: one-time unauthenticated HTTP GET, no credentials or proxy;
- authority basis: public endpoint and captured HTTP metadata, without independent issuer attestation;
- claimed issuer Binance, explicitly not independently verified;
- expected and observed source both Binance USD-M, with shared upstream system Binance.

Envelope declarations match the owner-pasted raw byte length and digest. Because the envelope is self-recorded metadata and no independent issuer attestation or complete endpoint enumeration evidence is present, it does not establish source authenticity, completeness, or issuer independence. In particular, `terminal=true` with `sourceTotal=null` and no next cursor is not sufficient proof that all requested history was returned.

### 9.3 Corrected three-settlement Binance lookup

An earlier diagnostic used three incorrectly calculated target epoch values (each 9,600,000 ms early). Those results are superseded and must not be used. The corrected UTC targets and owner-pasted raw-response lookups are:

| Target settlement UTC | Correct target epoch ms | Binance fundingTime ms | Delta ms | Binance fundingRate |
|---|---:|---:|---:|---:|
| 2026-11-01 08:00:00Z | 1793520000000 | 1793520000003 | +3 | 0.00010000 |
| 2026-11-01 16:00:00Z | 1793548800000 | 1793548800000 | 0 | 0.00010000 |
| 2026-11-02 00:00:00Z | 1793577600000 | 1793577600005 | +5 | 0.00010000 |

The three Binance fundingRate values match the three previously extracted Tardis candidate rates (`0.0001`) numerically. This is **three-event value agreement**, not a formal comparator PASS: no timestamp-matching/tolerance policy has been approved, and the evidence does not prove independent issuer lineage. The Tardis 08:00 candidate still has two rows tied at the latest pre-event exchange timestamp; both have the same rate but distinct local receive timestamps. The 00:00 event at the start of the Tardis daily file still has no strictly earlier observation in that file.

### 9.4 Updated disposition

- D07.6 raw byte length and SHA-256: **PASS — MATCHES RECORDED CAPTURE** (owner-pasted VPS command output).
- D07.6 HTTP metadata and envelope/raw-byte consistency: **PASS — OWNER-PROVIDED EVIDENCE**.
- Binance page structure: **PASS — 500 unique, ordered records; bounded page only**.
- Binance endpoint enumeration/global completeness: **NOT VERIFIED** (`sourceTotal=null`; no authoritative total or pagination proof).
- D07.7 three-event funding-rate agreement: **PASS — 3/3 VALUE AGREEMENT, LIMITED**.
- D07.7 formal comparator/timestamp policy: **NOT VERIFIED / NOT PROMOTED**.
- Tardis provider-origin provenance and formal D07.11 manifest/sidecar/reference-index resolution: **NOT VERIFIED**.
- D07.2: **BLOCKED_SHARED_LINEAGE** (same Binance issuer).
- D07 overall: **PARTIAL**.
- PAPER ledger bootstrap: **BLOCKED / NOT APPROVED**.

No raw VPS capture was uploaded or committed. No source code, comparator, manifest/validator, funding row, ledger/database, T0, VPS runtime, Runner/One-shot, credentials or execution state was changed. Documentation-only; no CI run or artifact was produced.
