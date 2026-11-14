# D07.8 Offline Package Builder — Owner-Supplied BTCUSDT Export

Date: 2026-11-14  
Branch: \`feature/core-operational-proof-20261112\`  
Scope: owner-approved offline package creation from the previously supplied \`BTCUSDT.csv\` only.

## 1. Authorization and source identity

- Owner approved an offline D07.8 Package Builder using the existing \`BTCUSDT.csv\`, with the original file preserved and no lineage fabrication.
- The source file was recovered from the user's ChatGPT Library, not from the VPS.
- Original filename: \`BTCUSDT.csv\`; size: **1,431,960 bytes**.
- The file has GZIP magic bytes and contains a UTF-8 CSV after decompression; the original bytes were not modified.
- Original SHA-256: \`71963e8235106ae36fe386ef0fbd52b078df48ea854d09d814469eddeed58a8c\`.
- The Tardis export identity is based on the user-supplied file context. Provider identity, issuer authenticity and collector provenance are **not independently authenticated**.

## 2. Bounded source inspection

- Decompressed CSV bytes: **12,337,426**.
- Structurally parsed rows: **98,211**; 11 expected columns.
- Observed exchange value: \`binance-futures\` for all rows.
- Observed symbol: \`BTCUSDT\` for all rows.
- \`timestamp\`, \`local_timestamp\`, and \`funding_timestamp\` are source-native microseconds in this export.
- Funding event keys were converted to milliseconds only where integer microseconds divide exactly by 1,000.
- Unique \`timestamp\` values: **83,598**; duplicate timestamp rows: **14,613**. These are message-time duplicate observations, not funding-event duplicate keys.
- Unique \`local_timestamp\` values: **98,209**.
- Unique observed \`funding_timestamp\` keys: **4**:
  - 2026-11-01 00:00:00 UTC
  - 2026-11-01 08:00:00 UTC
  - 2026-11-01 16:00:00 UTC
  - 2026-11-02 00:00:00 UTC
- All 98,211 rows contain funding rate \`0.0001\`. This is a property of the supplied file only; no new Binance comparison was performed.
- Message timestamp range: 2026-11-01 00:00:00.000000 UTC through 2026-11-01 23:59:57.002000 UTC.
- Receive timestamp range: 2026-11-01 00:00:00.062732 UTC through 2026-11-01 23:59:57.063032 UTC.
- The last observed funding event key is exactly at 2026-11-02 00:00 UTC. Manifest coverage therefore uses the half-open event-key interval \`[1793491200000, 1793577600001)\` ms to include all four observed keys. This is an observed-key range, not a claim that the source file enumerates the complete funding population.

## 3. Package produced

Package ID: \`d07-8-tardis-btcusdt-20261101-pilot-v4\`  
Assembly timestamp: \`2026-11-14T13:00:00Z\`  
Builder source revision: \`a13d736bed35a928b00a1e8660171e53cfaed886\`

Package layout:

| File | Bytes | SHA-256 |
|---|---:|---|
| \`raw/BTCUSDT.csv.gz\` | 1,431,960 | \`71963e8235106ae36fe386ef0fbd52b078df48ea854d09d814469eddeed58a8c\` |
| \`transforms/field-mapping.json\` | 1,655 | \`f7fe5c5aec02ebc209d0523f2de49cc5ac7ce71249740e2b0f5c19f7beb57e0c\` |
| \`manifest.json\` | 1,496 | \`f8c598471044c47a49fecd09de18371bb83961eb97e258c3a0dcafdce5226301\` |
| \`checksums/SHA256SUMS\` | 261 | \`fe758018fc022d19056bbabbe188ccea95e345ae973cd8fe4221d4bba70e4cdb\` |

The raw package copy is byte-for-byte identical to the supplied source. The package readback independently reproduced the raw and field-mapping byte lengths and SHA-256 values. The GZIP readback parsed **98,211 rows** and reproduced the four observed funding keys.

No raw data or generated package was committed to GitHub. The package exists as a local generated artifact for owner retrieval; the source file remains unchanged.

## 4. Manifest disposition

The existing D07.8 manifest validator returned:

- \`status=STRUCTURE_VALID\`
- \`fileCount=2\`
- \`recordCount=98,211\`
- \`coverageComparison=NOT_AVAILABLE_NO_EXPECTED_SET\`
- \`missingExpectedTimestampsMs=[]\`
- \`unexpectedObservedTimestampsMs=[]\`
- \`completeness=NOT_VERIFIED\`
- \`issuerAuthenticity=NOT_VERIFIED\`
- \`collectorIndependence=NOT_VERIFIED\`
- \`factualTruth=NOT_VERIFIED\`

The expected settlement schedule is deliberately empty and marked \`NOT_SUPPLIED_NO_AUTHORITATIVE_EXPECTED_SET\`. The validator was clarified so that an absent schedule is not misreported as four unexpected observations. This does not upgrade completeness.

## 5. Code and test evidence

- Builder implementation commit: \`c541d2d205038cb66b5dcabff7915b108cfeea44\`.
- Coverage semantics and regression test commit: \`a13d736bed35a928b00a1e8660171e53cfaed886\`.
- New builder tests: 8.
- Existing D07.8 contract tests plus new builder tests: **19/19 PASS** locally.
- GitHub Actions workflow: **D07.8 Offline Package Builder**.
- Workflow run: \`43597428777\`, exact source SHA \`a13d736bed35a928b00a1e8660171e53cfaed886\`, conclusion **SUCCESS**.
- Job: \`132454841040\`, compile and test steps SUCCESS.
- Artifact: \`14115062712\`, \`d07-8-offline-package-builder-test-evidence\`, SHA-256 digest \`sha256:26b27eb55c1156dfa09a9e15cffa9584b167690565d199c27ba1aa3a8918ad77\`.

## 6. Explicit limits and next gates

This work establishes an offline package with exact source-byte preservation, local readback and a structure-valid manifest. It does **not** establish:

- Tardis/provider authenticity or Binance issuer authenticity;
- collector operational independence;
- authoritative expected funding schedule;
- source enumeration or global completeness;
- freshness or factual truth;
- a real D07.9 lineage sidecar or authenticated evidence reference index;
- formal D07.11 resolution or D07.7 exact-key comparison against this package.

No D07.9 sidecar or reference index was fabricated. D07.11 was not run because the required independent lineage sidecar and reference index are still absent. D07.2 remains \`BLOCKED_SHARED_LINEAGE\`; D07 remains **PARTIAL**; Paper Ledger bootstrap remains **BLOCKED / NOT APPROVED**.

No network acquisition, VPS/T0 operation, ledger/database write, Runner/One-shot, credential use, live order or execution action occurred.
