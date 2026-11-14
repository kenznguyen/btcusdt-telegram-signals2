# D07 Repository-Wide Inventory and Scope Review — 2026-11-14

## Scope and method

Read-only GitHub inspection of the complete recursive Git tree at branch feature/core-operational-proof-20261112, HEAD edf5cc1110a8edfd53741e0b06a9fd165654718e.

- Recursive tree response: 1,116 entries, 1,041 files, truncated=false.
- Enumerated all 56 tracked JSON/JSONL/JSON5 files.
- Searched all tracked paths for D07, manifest, sidecar, reference-index, evidence-index, custody, lineage and funding identifiers.
- Inspected D07.8 manifest validator and contract, D07.9 schema/validator, D07.11 resolver/readback worker, synthetic tests, workflow and D07.13 evidence record.
- This is a repository-wide file inventory plus focused D07 implementation review; it is not a line-by-line review of all 1,041 files.

## Repository inventory findings

1. No actual D07.8 Tardis package manifest.json is present in the tracked repository tree.
2. No actual D07.9 TARDIS_COLLECTOR_LINEAGE_V1 sidecar record is present.
3. No actual D07 evidence reference index is present.
4. The only D07 lineage JSON contract file found is d07_9_lineage/schema.v1.json; it is a schema, not a real sidecar.
5. The 16 synthetic-evidence-retention-manifest.json files and corresponding synthetic attestation/trust-root files are under docs/evidence/p1-8/. They are synthetic P1.8 evidence and are not substitutes for D07.8/D07.9 custody artifacts.
6. D07 design/evidence documents, D07.8 in-memory manifest validator, D07.9 schema/validator, D07.11 resolver/readback worker and synthetic tests are present. These prove contract implementation and synthetic behavior only, not real Tardis custody.
7. D07.8 validator explicitly returns completeness=NOT_VERIFIED, byteIntegrity=NOT_CHECKED, issuerAuthenticity=NOT_VERIFIED, collectorIndependence=NOT_VERIFIED and factualTruth=NOT_VERIFIED. It validates caller-supplied structure; it does not open or hash real files.
8. D07.11 resolver requires a supplied sidecar, D07.8 package, evidence root and reference index. Its documentation states that the reference index origin, authority and immutability are not authenticated by the resolver.

## CI and branch state

- Current branch HEAD: edf5cc1110a8edfd53741e0b06a9fd165654718e.
- Combined commit status response for this exact HEAD: no status entries returned. This is NOT evidence that tests passed.
- Previously recorded D07.11 synthetic workflow evidence remains tied to source SHA 61b9e4b569f84a4f4679a18b3eaab30ae280f21e, run 43582892328, 53/53 tests. It does not apply automatically to the current docs-only HEAD.
- GitHub compare against main reported diverged: branch ahead by 4,152 commits and behind by 82 commits; merge base f5b74affb8777953fa66d241784965fbb0e577ba. Do not merge, rebase, reset, switch branches or change the default branch as part of this inventory. Divergence requires separate owner decision and careful reconciliation.

## Focused review boundary

- D07.8/D07.9/D07.11 code and tests are present, but CI synthetic PASS is not real-data acceptance.
- Resolver _safe_relative_path checks for a doubled backslash sequence, while the readback worker rejects any backslash. The worker still fails closed on a single backslash before opening the target, so this inspection does not establish a traversal bypass; add a focused regression test and align both checks in a separately scoped code change.
- No code defect is promoted to a release blocker from this inventory alone. No tests were run in this read-only review.

## Disposition

- Repository-wide tracked-file inventory: PASS — bounded to exact branch tree and complete (not truncated).
- Actual D07.8 manifest: NOT FOUND IN TRACKED REPOSITORY.
- Actual D07.9 sidecar: NOT FOUND IN TRACKED REPOSITORY.
- Evidence reference index: NOT FOUND IN TRACKED REPOSITORY.
- D07.8/D07.9/D07.11 real custody resolution: NOT VERIFIED.
- D07.7 exact-key sample: PASS_WITHIN_OVERLAP — 1/3, LIMITED SAMPLE (unchanged).
- D07.2: BLOCKED_SHARED_LINEAGE (unchanged).
- D07 overall: PARTIAL.
- PAPER ledger bootstrap: BLOCKED / NOT APPROVED.

## Safety and next step

No repository code, VPS, T0, raw evidence, ledger/database, Runner/One-shot, credentials or live execution was changed or invoked. No data was created, moved or deleted.

Next bounded step: resolve branch divergence separately, without automatically merging/rebasing; then, if real D07 custody artifacts are supplied, run existing D07.9/D07.11 gates against those actual files. Handle the single-backslash path-check consistency test as a separate TDD change.
