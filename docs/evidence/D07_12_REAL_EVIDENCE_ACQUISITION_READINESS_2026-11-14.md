# D07.12 — Real Evidence Acquisition Readiness Assessment

Date: 2026-11-14  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Starting HEAD: `52ee5a8f44893ef251257fa8b655d74d60c16cca`  
Disposition: **READINESS REVIEW COMPLETE — ACQUISITION NOT AUTHORIZED OR PERFORMED**

## 1. Approved scope

This increment assesses whether a future, separately approved Tardis evidence acquisition is technically and evidentially feasible for D07. It is limited to public documentation review and repository documentation.

Permitted:
- Review public Tardis documentation for Binance USD-M Futures coverage, feed types, downloadable datasets, API access and data semantics.
- Compare documented capabilities against D07.7 settlement identity and D07.9 lineage/custody requirements.
- Record prerequisites, risks, stop conditions and a recommended bounded acquisition design.

Not permitted or performed:
- No Tardis API call, dataset URL request, download, account login, credential use, subscription purchase or entitlement check.
- No real data, package, parser, funding row, D07.2 verifier or D07.8 manifest change.
- No VPS/SSH, T0, ledger/database, Runner/One-shot, service or runtime operation.
- No live trading or order execution. `AI_EXECUTION_ENABLED=false` remains unchanged.

## 2. Public provider capability findings

The reviewed provider documentation states:

1. Tardis documents Binance USDT Futures historical data coverage beginning 2019-11-17. Its Binance Futures page lists BTCUSDT downloadable `derivative_ticker` data, with a sample date of 2020-02-01. The same page notes data collection issues before 2020-05-14, including missing data and latency spikes during market volatility. Therefore, availability from 2019-11-17 must not be interpreted as uniform quality across the whole period.
2. The normalized `derivative_ticker` CSV schema includes `timestamp`, `local_timestamp`, `funding_timestamp`, and `funding_rate`. Provider documentation defines `funding_timestamp` as the next funding event and `funding_rate` as the rate for that next event; the final value immediately before the funding timestamp is the value applied by the exchange. This is a stream of changing ticker observations, not documented as a canonical, one-row-per-settlement ledger.
3. Downloadable CSV datasets are daily gzip files, partitioned by local message-arrival timestamp. CSV files for the first day of each month are documented as available without an API key. Other historical dataset access requires confirming account entitlement; no entitlement was checked.
4. The raw HTTP replay API returns exchange-native WebSocket feed data in one-minute slices, with local arrival timestamps and disconnect markers. The documentation says unauthenticated historical access is available for the first day of each month. Tardis describes its data as sourced from exchange real-time WebSocket feeds, rather than the venue's REST history.
5. Provider documentation describes derivative ticker fields as sourced from exchange real-time WebSocket instruments/ticker feeds and states that values are added when tracked values change. The exact Binance Futures feed/channel and historical collection semantics relevant to BTCUSDT funding must be confirmed against the exact provider metadata and raw sample before any settlement-level claim is made.

Public references:
- Binance USDT Futures coverage and collection notes: https://docs.tardis.dev/historical-data-details/binance-futures
- Downloadable CSV API and access rules: https://docs.tardis.dev/downloadable-csv-files/api
- CSV derivative ticker schema: https://docs.tardis.dev/downloadable-csv-files/data-types
- Raw HTTP replay API: https://docs.tardis.dev/api/http-api-reference
- Tardis data-source and normalization FAQ: https://docs.tardis.dev/faq/data

## 3. Fit against D07 requirements

| Requirement | Readiness finding | Status |
|---|---|---|
| Candidate provider / BTCUSDT market coverage | Public docs identify Binance USDT Futures and BTCUSDT derivative_ticker datasets | DOCUMENTED |
| Distinct collector candidate | Tardis states that its historical feed data comes from captured exchange WebSocket feeds, unlike the prior Binance REST capture | PLAUSIBLE, NOT VERIFIED |
| Independent issuer | Both records concern Binance-defined funding events | NOT AVAILABLE — SAME ISSUER |
| Exact settlement observation | CSV contains changing next-event funding observations; a validated rule is still needed to select the final pre-event value for each exact settlement key | NOT VERIFIED |
| Raw-byte custody | Downloadable gzip files can be preserved and hashed, but no bytes were acquired | NOT VERIFIED |
| Independent readback | D07.11 synthetic resolver/readback contract is available; no real preserved copy exists | NOT VERIFIED |
| Source identity / authenticity | Public documentation describes the provider, but a downloaded file and its metadata alone will not authenticate the actual capture path | NOT VERIFIED |
| Expected population / enumeration completeness | Provider file availability and observed rows do not independently establish the complete expected settlement population | NOT VERIFIED |
| Freshness | Provider documents export/replay delays; no actual retrieval timestamp or freshness policy has been tested | NOT VERIFIED |
| Historical quality | Provider flags Binance Futures collection issues before 2020-05-14 | QUALIFIED / PERIOD-DEPENDENT |
| Account entitlement / full-period access | Not checked; only first day of each month is documented as unauthenticated | NOT VERIFIED |

**Important distinction:** Tardis provides a plausible second collector path, not an independent issuer. Even a successful byte-integrity and overlap test cannot establish independent issuer truth, global completeness or factual truth.

## 4. Critical semantic gap: ticker observations vs settlement records

D07.7 compares exact funding settlements using the key `venue + instrument + funding_time_ms` and a finite decimal funding rate.

Tardis's documented `derivative_ticker` feed instead reports the funding rate for the *next* funding event and may emit a row whenever tracked values change. The final pre-event value is documented as the applied value, but the documentation reviewed here does not establish:
- that every funding settlement has at least one retained ticker observation;
- that the final pre-event observation is always available in the exported dataset;
- the exact event-time and update-order semantics needed to identify the final observation without ambiguity;
- how reconnects, gaps, duplicate messages, event-time ties or collection outages affect that selection;
- that the selected row can be mapped to D07.7's exact integer settlement timestamp and rate without a source-specific validated rule.

Therefore, the existence of BTCUSDT `derivative_ticker` CSV files is **not yet proof** that they can serve as settlement-level corroboration. A future parser/adapter must preserve all raw rows and demonstrate deterministic selection against source-native semantics. It must not silently forward-fill, interpolate, infer cadence or substitute local receive time for funding event time.

## 5. Recommended acquisition design — future approval required

If the owner later approves real acquisition, use a small, bounded pilot before any broad historical range:

1. Owner first selects one exact UTC date (preferably a date on the first day of a month for the documented no-key sample path) and the exact BTCUSDT USD-M perpetual dataset/feed. No date is inferred by this assessment.
2. Before any request, verify the provider's current exchange metadata for the exact exchange ID, symbol, data type, exported/available period and documented channel. Preserve the metadata response as evidence.
3. Prefer the daily normalized `derivative_ticker` gzip dataset for a file-oriented custody test. Use the raw replay API only if the normalized schema cannot support the required event semantics and the separately approved access entitlement permits it.
4. Preserve the exact compressed response bytes as an immutable raw object. Record request path (without secrets), response status and headers, retrieval actor/process/version, environment, UTC start/end, byte length and SHA-256. Do not rewrite or decompress in place.
5. Copy to a separate preserved location and run D07.11's distinct-process readback against the preserved copy. Retain the readback output and independently recomputed byte length/SHA-256.
6. Only after raw custody passes, separately approve a source-specific parser and synthetic/real-file tests. Preserve the original CSV rows; derived settlement candidates must be a separate artifact with parser SHA, configuration fingerprint and field mapping.
7. Compare exact settlement keys with the existing Binance capture. Report matched, Binance-only, Tardis-only, duplicate, malformed and unmatched rows explicitly. Limit any positive result to `PASS_WITHIN_OVERLAP`.
8. Keep completeness, freshness, issuer authenticity, enumeration/global completeness and factual truth as separate gates.

### Stop conditions

Stop without retrying through alternate routes if the provider returns access denied, authentication required, rate limit, unexpected redirect, unsupported symbol/type, missing date, empty or malformed response, or an ambiguous coverage result. Do not use proxies, VPNs, alternate regions, account sharing or circumvention. Do not broaden the date range automatically. Do not store credentials or secret-bearing URLs in the evidence package.

## 6. Decisions still required before real acquisition

A future acquisition approval must specify all of the following:
- Exact UTC date or bounded date range and whether the pilot is limited to a first-of-month sample.
- Exact provider product: normalized CSV dataset or raw HTTP replay API.
- Exact symbol/contract: Binance USD-M BTCUSDT perpetual.
- Whether the owner has an eligible Tardis account/subscription if the requested date is outside the documented no-key sample availability.
- Exact permitted environment and storage destination; this assessment does not authorize VPS access or storage.
- Maximum file count/bytes and network request count.
- Explicit permission (or prohibition) for any credential use; the default for this assessment is no credentials.
- Stop conditions and whether a follow-on real-file parser/readback is separately approved.

## 7. Disposition

- D07.12 public-documentation readiness review: **PASS — DOCUMENTATION REVIEW ONLY**.
- Provider capability for BTCUSDT derivative ticker history: **DOCUMENTED**.
- Feasibility of a distinct Tardis collector path: **PLAUSIBLE, NOT VERIFIED**.
- Exact settlement-level suitability: **NOT VERIFIED — SEMANTIC GAP REMAINS**.
- Full-period access/entitlement: **NOT VERIFIED**.
- Real acquisition, byte custody/readback, collector-path independence, overlap and population completeness: **NOT PERFORMED / NOT VERIFIED**.
- D07.2: `BLOCKED_SHARED_LINEAGE` unchanged.
- D07 overall: **PARTIAL**.
- PAPER ledger bootstrap: **BLOCKED / NOT APPROVED**.

This readiness approval is exhausted by this assessment. It does not authorize any real Tardis request/download, credentials, purchase, VPS/T0 access, parser against real data, D07.2/D07.8 change, ledger import/bootstrap, Runner/One-shot or live execution. Each requires a separate, exact-scope owner approval.
