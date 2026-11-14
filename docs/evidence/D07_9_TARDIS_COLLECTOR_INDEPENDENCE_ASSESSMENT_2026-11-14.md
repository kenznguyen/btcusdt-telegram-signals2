# D07.9 — Tardis Collector Independence Assessment

Date: 2026-11-14  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Disposition: **DESIGN ONLY — NO REAL TARDIS EVIDENCE ACQUIRED OR VERIFIED**

## 1. Objective and approved boundary

Define the evidence and acceptance contract for assessing whether a Tardis-collected Binance USD-M BTCUSDT funding observation is obtained through a collector path distinct from the existing Binance REST capture, and whether the resulting observations corroborate on exact funding settlements.

This is a design/documentation increment only. It does not download Tardis data, call an API, parse real provider files, create a connector, change D07.2 verification behavior, import funding rows, write a ledger/database, access T0/VPS, run Runner/One-shot, or enable live execution. No credentials or private account data are in scope.

The existing D07.2 result remains authoritative: exact captured Binance response byte integrity/readback PASS; declared single-page structure PASS; lineage **BLOCKED_SHARED_LINEAGE**; issuer authenticity, enumeration/global completeness, freshness and factual truth **NOT_VERIFIED**.

## 2. Claims must remain separate

D07.9 defines five independent claims. A PASS in one dimension must never promote another dimension.

| Claim | Question | Permitted positive statement |
|---|---|---|
| Issuer identity / authority | Which venue defines the funding event? | Both observations identify Binance as the issuer/venue |
| Collector-path separation | Were the observations acquired by distinct collection processes and custody paths? | Separate collector paths are evidenced within a declared boundary |
| Byte custody / integrity | Are the exact acquired bytes preserved and reproducibly read back? | The identified bytes match the recorded length and SHA-256 on readback |
| Observation corroboration | Do normalized observations agree on exact settlement keys? | PASS_WITHIN_OVERLAP for the exact matched overlap only |
| Population completeness / freshness | Is the full expected population present and recent enough? | Only the explicitly evidenced interval/population can be assessed |

**Issuer independence is not available from Binance REST versus Tardis-collected Binance data.** Both represent Binance-defined funding events. Tardis is a candidate independent collector/observer, not a second issuer. A Bybit or OKX funding rate is a different venue event and is not a substitute.

A different hostname, file, product name, transport label, process name or declared collector ID is not sufficient evidence of collector independence.

## 3. Threat model and independence boundary

The assessment must identify common-mode dependencies rather than equate “different collector” with “independent truth”.

Record and assess at least:

1. **Acquisition actor/process:** operator or service identity, execution host/environment, process/version and acquisition time.
2. **Transport/feed:** exact Tardis dataset/feed/channel and whether observations originate from Binance exchange WebSocket messages, normalized provider output, or another documented source.
3. **Upstream issuer:** Binance remains the issuer for Binance funding values; upstream exchange publication and any exchange-side omissions are common dependencies.
4. **Storage/custody:** original file location at receipt, immutable package identity, copy/readback path, access controls and any shared storage dependency with the Binance REST capture.
5. **Transformation:** raw-to-normalized mapping, parser source SHA, configuration fingerprint, deterministic conversion rules and whether both comparison sides share transformation code.
6. **Control plane/credentials:** who controls each collector, credential/account dependencies if any, orchestration, network egress and administrative access. Do not expose or store secrets in evidence.
7. **Time and completeness:** source event time, exchange message time, local receive time, package retrieval time, declared coverage and independently justified expected settlement set.

The design should classify a shared dependency as:
- **Common issuer:** expected and unavoidable for Binance-vs-Tardis corroboration; blocks any claim of independent issuer truth.
- **Potential common collector/control dependency:** requires evidence and may block collector-path separation.
- **Unresolved dependency:** fail closed as NOT_VERIFIED; do not infer separation from missing information.

Even if collector-path separation is later supported, it establishes only a separate observation path relative to the declared Binance REST capture. It does not prove that Binance's upstream event is authentic, complete or factually correct.

## 4. Required evidence package

Use the immutable package structure defined by D07.8. D07.9 adds a collector-lineage evidence section to the manifest/evidence record; it does not alter the D07.8 validator or claim that its syntactic manifest checks prove custody.

Required evidence fields:

| Evidence area | Minimum record |
|---|---|
| Package identity | Unique immutable package ID, schema version, creation time, owner/custodian |
| Provider/dataset | Tardis provider identity, exact dataset/feed name, exchange=BINANCE, instrument and contract identity, source documentation revision/reference |
| Acquisition | Acquisition actor/process, host/environment identifier, start/end times, acquisition method, transport/channel, provider-native period and retrieval method |
| Raw files | Exact relative path, byte length, SHA-256, media type, record count only after a validated parser |
| Custody | First-received byte hash/length, preserved-original designation, copy/readback hash/length, custody events and responsible actor |
| Transformation | Parser/transform source SHA, configuration fingerprint, execution timestamp, field mapping and normalized output hashes |
| Time semantics | Funding event time, exchange message time, local receive time and package retrieval time kept distinct with source-native units |
| Coverage | Half-open internal interval, source-native interval semantics, observed timestamps, declared expected timestamps and authority/evidence for the expected set |
| Lineage | Explicit dependency inventory, shared dependencies, unknowns, reviewer disposition and exact scope of any separation claim |

Rules:
- Preserve raw provider bytes exactly; normalized output is a separate derived artifact.
- Hash the exact bytes at receipt and re-read the preserved copy independently before parsing.
- Record hashes and lengths before and after any permitted copy; mismatches block the package.
- Package corrections create a new package ID and retain a supersession link. Never overwrite an accepted raw package.
- A manifest's SHA-256 syntax is not byte-integrity evidence. A digest becomes a byte-integrity claim only after recomputation over the exact bytes.
- A file downloaded from a provider is not by itself proof of the named provider, source channel or collector independence. Preserve acquisition evidence and qualify claims accordingly.

## 5. Comparison and population contract

The future comparator must reuse D07.7's exact normalized event identity:
- venue = BINANCE;
- instrument = BTCUSDT;
- market type = USD-M futures;
- contract type = perpetual;
- margin and settlement asset = USDT;
- exact integer `funding_time_ms` as the event key;
- finite decimal-string funding rate compared using Decimal.

Only exact event-time intersections may be compared. Report:
- matched settlement count;
- rate mismatches;
- Binance-only and Tardis-only settlement counts;
- exact overlap start/end;
- duplicate and malformed records;
- source-side observed count and declared expected count separately.

Do not align by local receive time, exchange message time, filename month, approximate timestamp, presumed eight-hour cadence or nearest-neighbor matching.

### Expected population authority

The expected settlement set must have an explicit authority and provenance reference. A date range, owner-entered schedule, observed minimum/maximum, monthly file name, record count or matching endpoints is not an authoritative expected population.

If the expected schedule is derived from the same Tardis file being assessed, the completeness check is circular. If it is derived from Binance REST history, it shares the Binance issuer and must be labeled accordingly. A schedule discrepancy is not automatically proof of provider omission.

Until an independently justified expected set and its own provenance are available:
- `enumerationCompleteness=NOT_VERIFIED`;
- `globalCompleteness=NOT_VERIFIED`;
- `freshness=NOT_VERIFIED`;
- `factualTruth=NOT_VERIFIED`.

A successful comparison may state only `PASS_WITHIN_OVERLAP`; unmatched rows remain visible and do not disappear into a single PASS flag.

## 6. Status model and promotion rules

Keep the D07.7 dimensions and add an explicit evidence-custody disposition. Do not collapse them into one `independence` boolean.

| Dimension | Initial state | Promotion condition |
|---|---|---|
| `issuerIndependence` | `NOT_VERIFIED_SAME_ISSUER` | Not promotable for Binance REST vs Tardis Binance |
| `collectorIndependence` | `NOT_VERIFIED` | Complete lineage inventory plus reviewed evidence of distinct acquisition/custody/control paths within a declared boundary |
| `byteIntegrity` | `NOT_VERIFIED` until real bytes are read | Exact byte length and recomputed SHA-256 match on independent readback |
| `observationCorroboration` | `NOT_VERIFIED_NO_OVERLAP` until real rows exist | D07.7 exact-key comparison; only `PASS_WITHIN_OVERLAP` |
| `enumerationCompleteness` | `NOT_VERIFIED` | Independently justified expected population and reconciled complete coverage |
| `freshness` | `NOT_VERIFIED` | Explicit freshness policy and trusted retrieval/event-time evidence |
| `issuerAuthenticity` | `NOT_VERIFIED` | Evidence sufficient to authenticate the actual issuer/source, not merely a provider label |
| `globalCompleteness` | `NOT_VERIFIED` | Authoritative global population evidence; overlap alone cannot promote |
| `factualTruth` | `NOT_VERIFIED` | Outside what a second collector of the same issuer can establish by itself |

Collector independence, if eventually supported, must be scoped as “separate collector path relative to the identified Binance REST capture” and must disclose remaining common dependencies. It must not be presented as independent issuer validation.

## 7. Fail-closed acceptance matrix

The future evidence review must block promotion when any of the following occurs:
- collector identity or acquisition method is missing or merely self-declared;
- lineage dependencies are unknown or reveal a shared collector/control/storage path;
- raw bytes are unavailable, modified, truncated, or fail length/hash readback;
- raw-to-normalized mapping is undocumented or parser/configuration provenance is missing;
- event-time and local-receive-time fields are conflated;
- contract identity differs or venue substitution is attempted;
- duplicate settlement keys, malformed rates or invalid timestamps exist;
- expected population has no independent authority or is derived circularly from the observed data;
- gaps, unmatched rows, pagination boundaries or provider period semantics are hidden;
- package custody or immutable version history cannot be reconstructed.

Negative tests for any future implementation should include: same collector under two names; different files from one shared collector; shared storage/control plane; missing lineage fields; byte tampering after capture; byte truncation; hash mismatch; timestamp-unit confusion; duplicate settlement; partial overlap; no overlap; mismatched rates; venue substitution; circular expected schedule; missing expected timestamp; and false completeness claims from a single terminal page.

## 8. Decision gates after this design

1. **D07.9 design review:** confirm the dimensions, evidence fields, failure conditions and status semantics. This document is the proposed contract; no runtime evidence is implied.
2. **Separate acquisition approval:** only after the design is accepted, obtain a distinct bounded approval for a one-time Tardis evidence acquisition or for review of owner-supplied original files. That approval must name exact dataset/file period, method, environment, storage target, allowed network access and stop conditions. It must explicitly exclude credentials/private endpoints unless separately approved.
3. **Parser and byte-verification approval:** separately authorize any real-file parser, source-specific verifier extension and tests. D07.2 must not be weakened to turn the current shared-lineage result into PASS.
4. **Evidence review:** verify raw bytes, custody, lineage, parser provenance and exact overlap; publish each dimension independently.
5. **Bootstrap gate:** only a later, separate owner decision may consider whether funding evidence is sufficient for PAPER ledger bootstrap. No D07.9 outcome automatically authorizes bootstrap.

## 9. Current disposition

- D07.9 collector independence assessment design: **DOCUMENTED — DESIGN ONLY**.
- Tardis real data acquisition/parser: **NOT AUTHORIZED / NOT IMPLEMENTED**.
- Real byte custody/readback for Tardis: **NOT VERIFIED**.
- Collector independence: **NOT VERIFIED**.
- Issuer independence: **NOT AVAILABLE for Binance REST vs Tardis-collected Binance data**.
- Real Binance–Tardis overlap: **NOT VERIFIED**.
- Expected population authority, enumeration/global completeness, freshness, issuer authenticity and factual truth: **NOT VERIFIED**.
- D07.2 `BLOCKED_SHARED_LINEAGE`: **UNCHANGED**.
- D07 overall: **PARTIAL**.
- PAPER ledger bootstrap: **BLOCKED / NOT APPROVED**.

No code, workflow, verifier, provider integration, funding row, ledger/database, T0 or VPS state was changed by this design.
