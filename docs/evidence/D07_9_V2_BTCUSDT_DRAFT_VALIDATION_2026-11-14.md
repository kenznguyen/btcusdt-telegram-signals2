# D07.9 V2 BTCUSDT Draft — Validation Evidence

Date: 2026-11-14 (Asia/Ho_Chi_Minh)  
Branch: `feature/core-operational-proof-20261112`  
Disposition: **STRUCTURE VALID / PACKAGE BYTE BINDING PASS / PROVENANCE NOT VERIFIED**

## Scope

Created a separately versioned V2 draft for the existing D07.8 v4 BTCUSDT package using only facts already recorded in the D07.8 package report and source-origin clarification. V1 was not changed. No real evidence-reference index was created and D07.11 was not run.

## Draft

- Path: `d07_9_lineage/drafts/btcusdt_20261101_chatgpt_retrieval.v2.draft.json`
- Creation commit: `d3ffa58d21631c07e285e58fab197cd9ab070f3e`
- Git blob SHA: `2c5b76e70992b88d94bb7050c6a9d17923331c18`
- Record ID: `d07-9-btcusdt-20261101-v2-draft`
- Package ID: `d07-8-tardis-btcusdt-20261101-pilot-v4`

The draft asserts only the owner-reported immediate ChatGPT retrieval channel and D07.8 package byte identity. It keeps exact retrieval time, original upstream origin, provider identity, collector identity/execution, host, transport, network egress, custody events and issuer authenticity unknown or unavailable. The intended Tardis dataset/feed labels are not promoted to authenticated provider claims.

## D07.8 manifest binding

The V2 validator test supplies the recorded D07.8 v4 manifest envelope and checks exact package ID, path, byte length and SHA-256:

- Raw path: `raw/BTCUSDT.csv.gz`
- Byte length: `1,431,960`
- SHA-256: `71963e8235106ae36fe386ef0fbd52b078df48ea854d09d814469eddeed58a8c`

The test asserts:
- `structuralStatus=STRUCTURE_VALID`
- `provenanceStatus=NOT_VERIFIED`
- `byteIntegrity=PASS_WITHIN_PACKAGE_BOUNDARY`
- Custody, provider authenticity, collector independence, upstream origin, global completeness, issuer authenticity and factual truth remain `NOT_VERIFIED`.

This is a comparison against the D07.8 manifest values recorded in the committed evidence report. It is not a fresh byte readback of the local ZIP/package in this CI job, and it does not authenticate the manifest's upstream origin.

## Code/test/workflow changes

- Added the V2 draft above.
- Added `test_current_btcusdt_v2_draft_matches_d07_8_manifest_bytes` to `d07_9_lineage/test_validator_v2.py`.
- Test file blob SHA: `bd975c350aa14d15f9db7fbcf0af8f27edaef548`.
- Test commit: `04795b014db3eb5545ef17d40b979bbb206b6d24`.
- Updated V2 workflow path filters to include the draft; workflow blob SHA: `f64f216917f82c8b6545dc5271b55d2b1c293a27`, commit `f536e8cbaf45e4223f610208484e4a98bf06265a`.

## GitHub Actions evidence

- Workflow: [D07.9 V2 Explicit Unknown Contract](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43599557079)
- Run ID: `43599557079`
- Exact checked-out source SHA: `04795b014db3eb5545ef17d40b979bbb206b6d24`
- Job ID: `132461179811`, conclusion `success`.
- V2 schema validation: PASS.
- Python compilation: PASS.
- V1 regression + V2 tests: **53/53 PASS** (37 V1 + 16 V2, including the real draft/manifest-envelope test).
- Artifact ID: `14115871830`
- Artifact name: `d07-9-v2-explicit-unknown-test-evidence`
- Digest: `sha256:75b5304466d2b7236baa7392650bfd03d7a60f5f5005c82167de2334a4f654d5`
- Size: 1,654 bytes; expiry: 2026-11-21T13:23:54Z.

The workflow-file path-filter update was committed after the tested SHA. It does not change the draft, schema, validator or test logic included in the successful run.

## Status and limits

- V2 draft structure: **PASS**.
- D07.8 manifest metadata binding: **PASS WITHIN PACKAGE BOUNDARY**.
- Upstream/provider/collector/custody/issuer provenance: **NOT VERIFIED**.
- D07.11 real reference resolution: **NOT RUN**; no authenticated reference index/trust boundary exists.
- D07.2: **BLOCKED_SHARED_LINEAGE**.
- D07 overall: **PARTIAL**.
- Paper Ledger bootstrap: **BLOCKED / NOT APPROVED**.

No raw package bytes were committed. No network acquisition, VPS/T0 operation, ledger/database write, Runner/One-shot, credential use, live trading, order execution or data deletion occurred.

## Next bounded gate

Review whether a real, independently controlled evidence-reference index and source/custody evidence can be supplied. Until then, retain this record as a V2 draft and do not run D07.11 or promote provenance status.
