# D07.8 — Tardis funding evidence package design

Date: 2026-11-14  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Disposition: **DESIGN + SYNTHETIC OFFLINE CONTRACT VALIDATION ONLY**

## 1. Objective and hard boundary

Define the evidence package required before a future, separately approved review of Tardis-collected Binance USD-M BTCUSDT funding observations. This increment makes the package shape and validation rules explicit and tests the manifest validator against synthetic objects only.

This increment does **not** download Tardis data, call an API, parse a Tardis CSV/raw feed, create a provider connector, hash or read real source files, modify the D07.2 source-byte verifier, import funding rows, write a ledger/database, access T0/VPS, run a trading runner, or enable live execution.

The existing D07.2 `BLOCKED_SHARED_LINEAGE` verdict remains authoritative and unchanged.

## 2. Evidence package layout

A future approved package should be immutable and self-contained:

```text
d07-8-tardis-binance-funding-<package-id>/
  manifest.json
  raw/
    <original-provider-file-1>
    <original-provider-file-2>
  derived/
    normalized-observations.csv
  transforms/
    field-mapping.json
    parser-provenance.json
  checksums/
    SHA256SUMS
```

Rules:
- Preserve original provider bytes exactly; never overwrite raw files with normalized output.
- Normalized/derived files are additional artifacts, not replacements for raw bytes.
- Record parser/transform source revision, configuration fingerprint and execution timestamp before any future parsing is authorized.
- Keep package IDs immutable. A correction creates a new package/version and links to the superseded package; do not silently replace evidence.
- No package is to be imported into the PaperLedger by this design.

## 3. Manifest contract

The synthetic validator implements `TARDIS_BINANCE_FUNDING_EVIDENCE_V1` with these required sections:

| Section | Required information |
|---|---|
| `issuer` | Venue identity = BINANCE and stated authority |
| `collector` | Collector identity = TARDIS and acquisition channel |
| `instrument` | BTCUSDT, USD-M futures, perpetual, USDT margin and settlement |
| `time` | Separate event-time and local receive-time field names; UTC milliseconds |
| `coverage` | Half-open interval `[startAtMs, endAtMs)`, declared expected settlement timestamps and the authority for that expected set |
| `files[]` | Relative path, byte length, lowercase SHA-256, record count and media type |

The manifest validator checks exact schemas, identity, timestamp ordering/range, safe relative paths, nonnegative byte/record counts and SHA-256 syntax. It does not open files or recompute digests. A syntactically valid digest is not byte-integrity proof.

## 4. Timestamp semantics

Do not conflate these fields:
- **Funding event/settlement time:** the venue event timestamp used as the exact comparison key; normalized to UTC epoch milliseconds.
- **Exchange message timestamp:** timestamp attached to the exchange feed message, if supplied.
- **Local receive timestamp:** when the collector observed the message; retain separately as UTC epoch milliseconds or an explicitly documented source-native representation.
- **Package retrieval/creation time:** when the evidence package was assembled; metadata only, never substituted for event time.

The raw field names and source-native units must be retained in the field-mapping record. Conversion to milliseconds must be deterministic and testable. Do not use local arrival time to align funding events.

## 5. Coverage and gap assessment

- Use an explicit half-open scope `[startAtMs, endAtMs)` for internal package comparisons.
- Preserve the source-native query/file period separately where its boundary semantics differ.
- Compare observed timestamps against an explicit expected settlement-time set. Record who/what supplied that set and its evidence reference.
- Report missing and unexpected timestamps separately. Never infer a missing funding event merely from a presumed fixed 8-hour cadence; schedules can change and the expected population itself requires authority.
- A missing timestamp relative to an owner-supplied schedule is a **schedule discrepancy**, not proof of a source omission.
- A file's record count, monthly filename, one terminal page, or matching minimum/maximum timestamps does not establish enumeration or global completeness.
- The current validator therefore always returns `completeness=NOT_VERIFIED`, even when the observed and declared expected timestamp lists match.

## 6. Byte provenance and hashing

For each original and derived file, a future acquisition process must record:
1. exact relative path and media type;
2. exact byte length;
3. SHA-256 of the exact preserved bytes;
4. record count only after a separately validated parser exists;
5. acquisition/retrieval timestamp and acquisition method;
6. provider/dataset identity, file period and source documentation revision;
7. parser/transform source SHA and configuration fingerprint for derived outputs.

The D07.8 offline validator only validates the manifest's SHA-256 representation (64 lowercase hexadecimal characters). It does not hash file content, establish custody, prove that the file came from Tardis, or prove that a collector is independent.

## 7. Binance comparison contract

A future comparison must use the existing D07.7 comparator after a separately approved Tardis raw-file parser has been reviewed and tested.
- Map both observations to Binance venue identity; Tardis is the collector, not the issuer.
- Require exact contract identity: BTCUSDT, USD-M futures, perpetual, USDT margin and settlement.
- Align only on exact funding event/settlement timestamp in milliseconds.
- Compare finite decimal-string funding rates using Decimal, never binary floating point.
- Report exact overlap, mismatches, Binance-only and Tardis-only counts.
- Preserve exchange message time and local receive time for latency/ordering diagnostics, but do not use either as the settlement key.
- A match can only be `PASS_WITHIN_OVERLAP`; it cannot prove issuer authenticity, collector independence, freshness, enumeration completeness, global completeness or factual truth.
- Binance REST and a Tardis-collected Binance feed remain the same issuer. Collector independence requires separate operational evidence and cannot be inferred from a different hostname, transport, file or product name.

## 8. Offline implementation and test evidence

Added `paper_execution/funding_evidence_package.py`, a pure in-memory manifest-structure validator. It does not access the filesystem or network.

Added `paper_execution/test_funding_evidence_package.py`, with synthetic tests for:
- valid manifest and exact declared coverage;
- unknown/missing schema fields;
- issuer/collector identity mismatch;
- path traversal rejection;
- malformed SHA-256 representation;
- invalid half-open coverage range;
- missing expected event reporting without completeness promotion;
- duplicate/unsorted timestamps;
- timestamps outside the declared interval;
- boolean/non-integer timestamp rejection.

The GitHub Actions workflow compiles the new module/tests, runs the focused D07.8 unittest group, records an explicit offline synthetic scope marker and includes the focused log in the evidence artifact.

## 9. Acceptance limits and next gates

D07.8 can be accepted only for manifest contract structure and synthetic offline behavior after the exact-HEAD workflow passes.

Still NOT IMPLEMENTED / NOT VERIFIED:
- Tardis raw-file parser and source-specific field mapping;
- real source-byte acquisition and SHA-256 readback;
- actual package custody and immutable storage;
- independent collector operational lineage;
- exact real Binance/Tardis overlap and rate corroboration;
- source identity, issuer authenticity and freshness;
- independently authoritative expected settlement schedule;
- enumeration completeness, global completeness and factual truth.

A separate explicit approval is required before any Tardis download/API request, raw-file ingestion, parser implementation against real data, persistent connector, source-byte verifier changes, funding-row import, ledger/database write, T0 access or VPS operation.