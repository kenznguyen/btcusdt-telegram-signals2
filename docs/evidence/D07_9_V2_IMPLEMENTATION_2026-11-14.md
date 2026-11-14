# D07.9 V2 Explicit-Unknown Contract — Implementation Evidence

Date: 2026-11-14
Branch: `feature/core-operational-proof-20261112`
Implementation status: **PASS — SYNTHETIC CONTRACT / REGRESSION CI**
Real provenance status: **NOT VERIFIED**

## Scope and approval

Owner approved implementation of the separately versioned D07.9 V2 contract after review of the design proposal. Scope was limited to V2 schema, V2 validator, synthetic tests, dedicated GitHub Actions workflow and documentation. V1 was preserved.

## Files and source identities

| File | Git blob SHA |
|---|---|
| `d07_9_lineage/schema.v2.json` | `d4de666a831c622a36bf5b9b4e9de3ff8e41a0e6` |
| `d07_9_lineage/validator_v2.py` | `d73548f96caa892d16b716e65471370ffa94ca45` |
| `d07_9_lineage/test_validator_v2.py` | `47d61a400fe6470af2b8f77531afbb6a94ff638f` |
| `.github/workflows/d07-9-v2-explicit-unknown.yml` | `d81a30abd636e801a91c00dd03f3f8ff7693af16` |
| `d07_9_lineage/README.md` | `3961ab6ea05aa54be8cb46f5bf5879a943d8ea7d` |

V1 preservation verified by unchanged blob identities:
- `schema.v1.json`: `69b55f1ac8b5e223cd0005eeae5ba3577eed9244`
- `validator.py`: `160727bcd545472ff6cd9c67bbaea8d7957b195d`
- `test_validator.py`: `52fd70b13dd5528511b97dd52d610fcad56761ad`

Implementation commits, all on the existing branch:
- Test-first V2 contract tests: `2fb1d311c08c8df694d4df88d78beb13060f74e8`
- V2 schema: `c9e2d19a0fba64e78ed41b402f0666bf3f7ac9b0`
- V2 validator: `3a5fe36cfd6f19de4badc808315e5fe1c7c08636`
- Dedicated workflow: `095b36fbd325e96924a920f654be14ac6f47dcf4`
- README: `cbcb132cca2cf3249782752248a1ea2091bda608`

## Implemented behavior

- Claims use `KNOWN`, `UNKNOWN`, `UNAVAILABLE`, `NOT_APPLICABLE`, with value/basis/limitation/evidenceRefs.
- Contradictory status/value combinations and unknown properties fail closed.
- Unknown acquisition timestamps do not require fabricated chronology.
- Empty custody events are schema-valid but custody remains `NOT_VERIFIED`.
- Owner-reported claims do not establish provider authenticity or upstream origin.
- Optional D07.8 manifest comparison checks exact package ID, path, byte length and SHA-256. A match is only `byteIntegrity=PASS_WITHIN_PACKAGE_BOUNDARY`.
- Known shared + material dependency blocks collector-independence claims.
- Evidence references are not resolved or authenticated by V2; D07.11 remains separate.
- V1 schema, validator and tests remain unchanged.

## GitHub Actions evidence

- Workflow: [D07.9 V2 Explicit Unknown Contract](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43599304075)
- Run ID: `43599304075`
- Exact checked-out source SHA: `095b36fbd325e96924a920f654be14ac6f47dcf4`
- Event: push; branch: `feature/core-operational-proof-20261112`
- Job: `v2-contract-and-v1-compatibility`, ID `132460419077`, conclusion `success`.
- Steps: dependency install PASS; V2 schema check PASS; py_compile PASS; V1 + V2 tests PASS; artifact upload PASS.
- Test result: **52/52 PASS** (37 V1 regression + 15 V2 contract tests).
- Artifact ID: `14115851384`
- Artifact name: `d07-9-v2-explicit-unknown-test-evidence`
- Artifact digest: `sha256:b56eba890e6c543b8c68f6bfdf549c7b3d2582df851116876e70a8b3e1827311`
- Artifact size: 1,621 bytes; expires 2026-11-21T13:20:53Z.
- Workflow run tested code/schema at SHA `095b36f...`; the subsequent README-only commit advanced branch HEAD to `cbcb132...`. No implementation files changed after the tested SHA; their current blob identities above were re-read from HEAD.

## Limits and non-claims

- CI fixtures are synthetic; no real D07.8 package or current provisional V1 draft was passed through V2 in this workflow.
- No D07.11 real evidence resolution, provider/issuer authentication, collector-independence proof, expected-set completeness or factual truth.
- No network acquisition, VPS/T0 access, database/ledger writes, Runner/One-shot, credentials, trading or data deletion.
- This does not authorize Paper Ledger bootstrap.

## Status

- D07.9 V2 schema/validator + synthetic tests + CI: **PASS WITHIN SYNTHETIC CONTRACT SCOPE**.
- V1 compatibility: **PASS — unchanged V1 test suite included in 52/52 run**.
- Current actual provenance: **NOT VERIFIED**.
- D07.11 real package resolution: **NOT RUN**.
- D07.2: **BLOCKED_SHARED_LINEAGE**.
- D07: **PARTIAL**.
- Paper Ledger bootstrap: **BLOCKED / NOT APPROVED**.

## Next bounded step

Create a clearly labeled V2 draft for the existing D07.8 v4 package using only the facts already available. Validate its schema and package-byte binding, while preserving unknown upstream/provider/collector/custody claims as NOT_VERIFIED. Do not run D07.11 without an actual evidence reference index and separately established trust boundary.
