# D07.8 Source-Origin Clarification — ChatGPT Retrieval

Date: 2026-11-14 (Asia/Ho_Chi_Minh)
Branch: `feature/core-operational-proof-20261112`
Parent HEAD: `077e5e442891bf08f027233b206a66edad70cc7f`

## Owner clarification

The owner clarified that the `BTCUSDT.csv` file was downloaded/retrieved from ChatGPT and that they did not download it from another source. This statement describes the owner's immediate retrieval path. It does not identify who originally supplied or created the file before it became available through ChatGPT, and it does not establish a direct Tardis export or a Tardis acquisition event.

## Byte identity retained

The file previously packaged as D07.8 v4 remains:

- Filename: `BTCUSDT.csv`
- Size: 1,431,960 bytes
- Format: GZIP-compressed UTF-8 CSV
- SHA-256: `71963e8235106ae36fe386ef0fbd52b078df48ea854d09d814469eddeed58a8c`
- D07.8 v4 raw-package comparison: exact byte match, as recorded in the D07.8 builder report.

This proves byte identity between the ChatGPT-retrieved file and the v4 raw package copy. It does not prove provider identity, issuer authenticity, collector identity, acquisition time/method, or pre-ChatGPT custody.

## Revised provenance disposition

| Claim | Disposition |
|---|---|
| Immediate retrieval channel reported by owner | ChatGPT |
| File bytes match D07.8 v4 raw object | PASS — previously verified |
| Original upstream source before ChatGPT | UNKNOWN / NOT VERIFIED |
| Direct Tardis export by owner | NOT ESTABLISHED |
| Tardis export receipt / job metadata | NOT PROVIDED |
| Collector identity and execution record | NOT VERIFIED |
| Custody before ChatGPT retrieval | NOT VERIFIED |
| Binance issuer authenticity | NOT VERIFIED |
| Completeness / authoritative expected set | NOT VERIFIED |

Do not label the file as a verified Tardis export. The existing package identifier and historical D07.8 report describe the intended pilot context, not independently authenticated source lineage. Any later evidence must be assessed on its own merits; do not manufacture a receipt, sidecar, reference index, collector record, or custody event.

## Scope and next gate

This is a documentation-only clarification. No source bytes, package files, builder code, validator, VPS, T0, network, ledger, Runner/One-shot, credentials, or execution state were changed or accessed. No tests or CI workflow were run for this documentation-only record.

D07.8 structural/package result remains `STRUCTURE_VALID` within its existing scope. D07.9 lineage remains `BLOCKED / NOT VERIFIED`; D07.11 real-package resolution remains `NOT VERIFIED`; D07.2 remains `BLOCKED_SHARED_LINEAGE`; D07 overall remains `PARTIAL`; Paper Ledger bootstrap remains `BLOCKED / NOT APPROVED`.

Next permitted action: if the owner can identify the original upstream source or provide a provider-issued export receipt/metadata, assess it read-only against this record. Otherwise retain the provenance fields as UNKNOWN/NOT VERIFIED and do not attempt to promote lineage status.
