# D07.7 — Funding lineage dimensions and offline observation comparison

Date: 2026-11-14  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Disposition: **DESIGN + OFFLINE COMPARISON CONTRACT ONLY**

## 1. Purpose and boundary

D07.7 separates three claims that must not be collapsed into a single independence flag:

1. **Issuer independence** — whether two observations are issued by different authoritative market venues.
2. **Collector independence** — whether the observations were acquired through distinct collection paths, without a shared collector, storage, transformation or control dependency that invalidates the claim.
3. **Observation corroboration** — whether two already acquired observations agree for the same venue, instrument and settlement timestamp over their exact overlap.

The current Binance USDⓈ-M BTCUSDT funding history and the candidate Tardis Binance feed both represent Binance-defined funding. Tardis can potentially provide a separate WebSocket collection/observation path, but it is not a second issuer. A Bybit/OKX funding value is a different venue's market event and is not a substitute for Binance BTCUSDT funding.

This increment adds only a pure offline comparator for caller-normalized rows and synthetic tests. It does not add a Tardis parser, source adapter, download, API client, scheduler, source-byte verifier change, database write, funding import or runtime integration. The existing D07.2 verifier and its `BLOCKED_SHARED_LINEAGE` result remain unchanged.

## 2. Independent dimensions and statuses

| Dimension | What it answers | D07.7 output semantics |
|---|---|---|
| `issuerIndependence` | Are the issuers independent authorities for this same event? | `NOT_VERIFIED_SAME_ISSUER` for Binance REST vs Tardis-collected Binance feed |
| `collectorIndependence` | Is the acquisition path independently operated and evidenced? | `NOT_VERIFIED` by default; `BLOCKED_SHARED_COLLECTOR_LINEAGE` when shared collector lineage is declared |
| `observationCorroboration` | Do the supplied values agree on exact settlement keys? | `PASS_WITHIN_OVERLAP`, `MISMATCH`, or `NOT_VERIFIED_NO_OVERLAP` |

A declared different collector name, transport or file does not prove collector independence. A future promotion requires evidence about acquisition actor/process, collection time, transport/feed, raw-byte custody, storage, transformation, credentials/control plane and shared dependencies. D07.7 intentionally has no status that promotes collector independence to PASS.

Observation corroboration is a narrow statement about the exact normalized rows supplied to the comparator. It does not establish that either input is authentic, complete, fresh, globally exhaustive or factually true.

## 3. Normalized comparison row

Each input row must contain:

- `venue`: exactly `BINANCE` for both sides; Tardis's exchange field is mapped to this venue identity, not treated as a Tardis issuer.
- `instrument`: `BTCUSDT`.
- `market_type`: `USD_M_FUTURES`.
- `contract_type`: `PERPETUAL`.
- `margin_asset`: `USDT`.
- `settlement_asset`: `USDT`.
- `funding_time_ms`: integer venue event/settlement timestamp in milliseconds.
- `funding_rate`: finite decimal string.

Tardis source fields such as exchange timestamp, local arrival timestamp and raw feed metadata must be retained in the upstream evidence package by a future, separately approved adapter. They are not silently substituted for the funding event timestamp. This comparator accepts already normalized input only; it is not evidence that a raw Tardis record was parsed correctly.

The settlement key is the exact `funding_time_ms` within the exact instrument identity. Rates are compared as Decimal values, not binary floating point. Duplicate settlement keys, invalid decimal values, venue substitution and mismatched contract identity are rejected.

## 4. Comparison semantics

- Compare only the intersection of settlement timestamps.
- Report matched, mismatched, Binance-only and Tardis-only counts separately.
- One or more exact matching observations with no rate mismatch yields `PASS_WITHIN_OVERLAP`, even if one side has additional unmatched rows. The unmatched counts must remain visible; this status is not population completeness.
- Any rate mismatch in the overlap yields `MISMATCH`.
- No exact overlap yields `NOT_VERIFIED_NO_OVERLAP`.
- `enumerationCompleteness`, `globalCompleteness`, `issuerAuthenticity`, `freshness` and `factualTruth` always remain `NOT_VERIFIED`.

The comparator does not infer missing historical events from a date range, does not apply timestamp tolerances, does not compare mark prices, and does not infer source totals. Those require a future source-specific contract and explicit evidence.

## 5. Offline test matrix

Eleven synthetic unit tests cover:

- exact agreement within an overlap;
- funding-rate mismatch;
- partial overlap with unmatched counts and completeness still NOT_VERIFIED;
- no overlap;
- rejection of a different venue as a substitute;
- rejection of different instrument/contract identity;
- duplicate settlement timestamps;
- invalid/non-finite decimal values;
- explicit shared collector-lineage block;
- empty inputs.

All tests are local pure-function tests. No external provider, network, credentials, VPS, T0, SQLite, PaperLedger or live execution is involved.

## 6. Relationship to D07.2 and current D07 verdict

D07.2 continues to verify exact local source-byte readback and declared pagination structure. Its shared-lineage detection is not changed or bypassed by this comparator. For the captured Binance page, the authoritative D07.2 result remains:

- byte integrity/readback: PASS for the exact captured bytes;
- pagination structure: PASS for the declared single page only;
- independence: `BLOCKED_SHARED_LINEAGE`;
- issuer authenticity, enumeration/global completeness, freshness and factual truth: `NOT_VERIFIED`.

D07.7 adds a separate future-facing analysis dimension; it does not overwrite the D07.2 verdict or change D07 production readiness.

## 7. Disposition and next gates

- Lineage dimension design: **DOCUMENTED**.
- Pure offline normalized observation comparator: **IMPLEMENTED**.
- Synthetic unit tests: **11 ADDED; CI PASS** (workflow `43564125815`, tested source SHA `0fe30e16018203d6aada91497eb6013a58b71607`).
- Tardis raw-file parser/acquisition: **NOT IMPLEMENTED / NOT AUTHORIZED**.
- Independent issuer authority: **NOT VERIFIED**.
- Independent collector lineage: **NOT VERIFIED**.
- Real Binance–Tardis overlap: **NOT TESTED**.
- Enumeration/global completeness, freshness and factual truth: **NOT VERIFIED**.
- Existing D07.2 shared-lineage block: **UNCHANGED**.
- D07 overall: **PARTIAL**; production bootstrap: **BLOCKED / NOT APPROVED**.

A separate approval is required before any Tardis data download, API access, raw-file ingestion, provider parser, persistent connector, source-specific verifier changes, funding-row import, ledger/database write, T0 access or VPS operation.
