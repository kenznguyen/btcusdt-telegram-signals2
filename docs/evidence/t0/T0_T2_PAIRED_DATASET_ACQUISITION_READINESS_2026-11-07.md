# T0→T2 Paired Dataset Acquisition Readiness

Date: 2026-11-07  
Status: **READY FOR OPERATOR APPROVAL — NO ACQUISITION PERFORMED**

## 1. Objective

Prepare one bounded, reproducible Binance USD-M vs OKX BTC perpetual OHLCV comparison using the existing offline harness. This is a research/data-quality exercise only. It does not certify strategy performance, select a preferred exchange, or authorize a source switch.

## 2. Recommended first comparison window

Use a 30-calendar-day UTC window for the first pilot:

- `end_ms`: an exact UTC hour boundary after the latest fully closed H1 candle is available from both sources.
- `start_ms`: exactly 30 days before `end_ms`.
- Both values must be divisible by 3,600,000 and 900,000.
- Window semantics are half-open: `[start_ms, end_ms)`.
- Expected rows per source: 2,880 M15 and 720 H1.
- This is far below the harness safety cap of 1,000,000 rows per file.
- Do not use the current/incomplete candle. Both sources must cover identical timestamps.

The exact timestamps must be selected and recorded by the operator at acquisition time; this document does not assume a current market-data endpoint or fabricate a capture window.

## 3. Required immutable inputs

Four UTF-8 CSV files, each with exactly the required fields (additional columns are tolerated by the parser):

`open_time,open,high,low,close,volume,closed`

| File | Required source | Contract / volume semantics |
|---|---|---|
| Binance M15 | Binance USD-M linear perpetual | `BTC/USDT:USDT`; volume in BTC base asset |
| Binance H1 | Binance USD-M linear perpetual | `BTC/USDT:USDT`; volume in BTC base asset |
| OKX M15 | OKX USDT perpetual swap | `BTC-USDT-SWAP`; use `history-candles[6]` / `volCcy`, not contract-count `vol` |
| OKX H1 | OKX USDT perpetual swap | `BTC-USDT-SWAP`; use `history-candles[6]` / `volCcy`, not contract-count `vol` |

Input requirements:

- Preserve original decimal strings; do not round values before writing CSV.
- Use Unix UTC milliseconds for `open_time`.
- Include only confirmed closed candles (`closed=true`).
- Do not forward-fill, interpolate, synthesize, deduplicate silently, or repair gaps.
- Preserve each raw export unchanged after capture. Record its SHA-256 and file size in the acquisition log before analysis.
- Keep raw files read-only during analysis; write reports to a separate output directory.

## 4. T0 provenance requirement

The parity manifest requires two genuine T0 `datasetVersion` values:

- `binance_t0.t0_dataset_version.m15`
- `binance_t0.t0_dataset_version.h1`

They must be copied verbatim from the corresponding T0 `read_window()` results for the exact same UTC window and market identity. They are provenance values, not hashes to calculate from the CSV.

Do not fabricate these values, substitute raw CSV SHA-256, or compare them directly to the T2 V2 digest. If the approved isolated export route cannot produce genuine T0 provenance without touching Canonical SQLite, stop and report the missing provenance as BLOCKED rather than weakening the manifest validator.

## 5. Acquisition boundary

No acquisition has been performed or authorized by this readiness document.

If separately approved, acquisition must be an isolated, bounded, read-only public-market-data export:

- no exchange API keys or account credentials;
- no private endpoints, orders, account state, or trading actions;
- no proxy or VPN;
- no Canonical SQLite creation, access, or writes;
- no Feeder start, scheduler activation, VPS provisioning, or source replacement;
- temporary files and any disposable test database must remain isolated and be deleted only under an explicit cleanup record;
- record UTC capture time, endpoint/source identity, requested window, pagination boundaries, response status, row counts, and SHA-256 for every raw export.

A public read-only export is not the same as canonical ingestion. Any inability to prove the isolation boundary is a stop condition.

## 6. Validation sequence after approval and input availability

1. Verify four files exist, are immutable/read-only, and match the acquisition log hashes.
2. Verify source identities, volume units, exact UTC window and genuine T0 datasetVersion provenance.
3. Run the existing offline harness:
   `python -m market_data.t0_t2_parity --manifest <manifest.json> --json-output <report.json> --markdown-output <report.md>`
4. Require `COMPARABLE`; any gap, duplicate, unclosed candle, malformed OHLC, wrong volume mapping, mismatched window, or missing provenance must fail closed.
5. Review per-field M15/H1 metrics and largest-difference rows. Explain differences; do not impose an arbitrary similarity score.
6. Independently verify source-file SHA-256 values in the report against the acquisition log.
7. Preserve JSON/Markdown reports, raw file hashes, manifest, exact source SHA, workflow run and artifact IDs in GitHub evidence.
8. Only after review, propose any follow-on experiment. This comparison alone does not authorize changing T2's OKX source.

## 7. Acceptance states

- **READY**: runbook and harness are available; no data capture implied.
- **BLOCKED**: approval absent, paired inputs absent, or genuine T0 provenance cannot be supplied within the isolation boundary.
- **PASS**: all four inputs satisfy the manifest and the offline harness returns COMPARABLE with complete evidence.
- **NOT VERIFIED**: source parity conclusions, strategy performance, or source suitability have not been established.

## 8. Current status and next action

- Runbook: READY.
- Paired Binance/OKX exports: NOT PROVIDED.
- T0 datasetVersion provenance: NOT PROVIDED for a paired window.
- Real-data parity: NOT RUN.
- Canonical SQLite: NOT CREATED.
- Feeder: STOPPED.
- T2 OKX source: unchanged.
- Live execution: disabled.

Next action requiring operator authorization: approve a separate isolated public read-only export task for the 30-day pilot, or supply the four immutable CSVs and matching T0 provenance. Until then, do not fetch market data or create any database.


## Operator approval recorded — execution pending (2026-11-07)

The operator explicitly approved one isolated public read-only Binance USD-M / OKX OHLCV export for the 30-calendar-day pilot.

Proposed exact window based on the latest complete H1 boundary at approval time:
- Start: `2026-10-08T03:00:00Z` (`1791428400000` ms)
- End: `2026-11-07T03:00:00Z` (`1794020400000` ms)
- Semantics: `[start_ms,end_ms)`
- Expected per source: 2,880 M15 and 720 H1 rows.

**Execution status: BLOCKED / NOT RUN in this session.** The available connected execution surfaces do not expose a raw public HTTP export runner or a GitHub Actions workflow-dispatch action. The web retrieval path could not access the exchange kline endpoint. No alternative proxy, VPN, credentials, Canonical DB or unverified transport was used. Approval is recorded but is not evidence of acquisition.

Before capture, re-check the latest fully closed H1 boundary and recompute the 30-day start; do not blindly reuse this window if execution occurs later. Keep the exact selected window identical across both exchanges.

T0 `datasetVersion` provenance remains a hard requirement. Since Canonical SQLite does not exist and is not authorized to be created, any implementation that cannot obtain genuine T0 provenance through an isolated temporary store must stop and report BLOCKED; do not fabricate or bypass provenance.

Current state: approval GRANTED; acquisition NOT RUN; paired CSVs NOT PROVIDED; real-data parity NOT RUN; Canonical SQLite NOT CREATED; Feeder STOPPED; T2 OKX source unchanged; live execution disabled.


## Read-window provenance prerequisite resolved in code — 2026-11-07

The 30-day M15 window requires 2,880 candles, which exceeded the prior T0 `read_window()` limit of 2,000. A distinct `MAX_READ_CANDLES=3000` bound has now been introduced for bounded read snapshots, while `MAX_CANDLES=2000` remains the ingestion/sync bound. The regression test covers a complete 2,880-candle M15 snapshot. Exact-SHA CI status is recorded in `T0_T2_COMPATIBILITY_AUDIT_2026-11-07.md`.

This resolves the API-size precondition for one genuine 30-day M15 `datasetVersion`; it does not produce provenance until an isolated T0 temporary store is populated and read. It does not authorize Canonical DB creation, canonical ingestion, or Feeder startup. The user has deferred Canonical DB creation; preserve that decision.
