# T0 L4 — GitHub Artifact Exact-Readback Verification

Date: 2026-11-11 (UTC)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Workflow run: [42937191664](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42937191664)
Exact workflow source SHA: `8bda3c987e2145a636bbcc9d8609c5ea15a492b9`
Scope: owner-approved, read-only download and independent SHA-256 verification of the three artifacts produced by run 42937191664.

Status: **PASS — THREE GITHUB ARTIFACT ZIP DIGESTS MATCH; PAYLOAD SCOPE LIMITED TO THESE THREE ARTIFACTS**

## 1. Exact artifact readback

Each artifact was downloaded through GitHub's Actions artifact endpoint, materialized as ZIP bytes, and SHA-256 was independently recomputed over the complete downloaded ZIP. Computed digests exactly match the GitHub artifact metadata and upload log.

| Artifact ID | Name | ZIP bytes | GitHub SHA-256 | Independently computed SHA-256 | Result | Expires |
|---|---|---:|---|---|---|---|
| `13819680374` | `t0-l4-artifact-manifest-42937191664` | 3,267 | `3509f2ce14aa174a45e4200ab44d13c7ae532841a74886256e9f6fe20ea55f71` | Same | PASS | 2026-11-18 01:12:12Z |
| `13818967476` | `t0-l4-minimum-lineage-42937191664` | 1,150 | `155986f0f35d875fad02b6c50d0aab7aa43afdcd9191391f9ee0b832e975b67e` | Same | PASS | 2026-11-18 01:12:12Z |
| `13818163804` | `t0-l4-repository-file-inventory-42937191664` | 4,483 | `98fc7fca7123ae0a9e72bcf1f209032a57c24d97aa898aaa075eb7212f04c0fa` | Same | PASS | 2026-11-18 01:12:12Z |

## 2. ZIP and payload checks

- ZIP CRC/read test passed for all three archives.
- No duplicate member names or unsafe absolute/traversal member paths were found.
- Manifest archive contains exactly `l4-artifact-manifest.json` and `l4-artifact-manifest.sha256`.
  - JSON payload SHA-256: `9bc86b32da5e2993729aac9f850ba15d2ff28274075a5ee2f5813119a0c5a0ef`.
  - Sidecar declares the same digest; independently recomputed digest matches.
  - Schema: `T0_L4_GITHUB_ARTIFACT_MANIFEST_V1`; repository and branch match this report; collector source SHA matches `8bda3c987e2145a636bbcc9d8609c5ea15a492b9`.
  - Manifest enumerates six allowlisted source artifacts with unique IDs and 64-character SHA-256 archive digests. Those six source artifact ZIPs were not downloaded/re-read as part of this increment; their presence in this manifest is not represented as a fresh exact-readback.
- Lineage archive contains four expected files:
  - `l4-source-sha.txt` = `8bda3c987e2145a636bbcc9d8609c5ea15a492b9`.
  - `l4-validation-scope.txt` = `T0_L4_MINIMUM_LINEAGE=GITHUB_HOSTED_READ_ONLY`.
  - `l4-lineage-contract-verdict.txt` = `L4_MINIMUM_LINEAGE_CONTRACT=PASS`.
  - Test log reports 12 tests run, no failures, and `OK`.
- Repository inventory archive contains JSON and SHA-256 sidecar.
  - JSON payload SHA-256: `4f57be4a46cac1703135d43dd5a99cc3ffb7e56aa1d71d2bdd87ab87085b9f0b`.
  - Sidecar declares the same digest; independently recomputed digest matches.
  - Schema: `T0_L4_REPOSITORY_FILE_INVENTORY_V1`; exact source commit matches `8bda3c987e2145a636bbcc9d8609c5ea15a492b9`.
  - 40 entries; paths are unique; every entry has a valid Git blob SHA-1 and SHA-256; sum of entry sizes equals declared total of 559,566 bytes.

## 3. Workflow test evidence

Run [42937191664](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42937191664) checked out exact source SHA `8bda3c987e2145a636bbcc9d8609c5ea15a492b9`.

| Job | Tests | Result |
|---|---:|---|
| L4-Minimum source lineage and policy contract | 12/12 | SUCCESS |
| L4-Minimum GitHub artifact readback and SHA-256 manifest | 19/19 | SUCCESS |
| L4-Minimum exact-commit repository-file inventory | 10/10 | SUCCESS |
| Total | 41/41 | SUCCESS |

The 19-test manifest job logged `L4_ARTIFACT_MANIFEST=PASS`; the inventory job logged `L4_REPOSITORY_FILE_INVENTORY=PASS`.

## 4. Control disposition and limitations

- GitHub artifact exact-readback for these three current-run artifacts: **PASS**.
- The result strengthens the GitHub-side artifact readback evidence for L4M-01 and the source-lineage evidence supporting L4M-03.
- L4M-01 owner custody: **PARTIAL / NOT VERIFIED**. This does not prove a complete owner-controlled evidence package, VPS copy, per-copy custody control, or authenticated latest-head anchor.
- L4M-03 exact T0 checkpoint/freshness: **PARTIAL — SYNTHETIC/DESIGN ONLY**. No signed canonical T0 checkpoint or authenticated latest-head anchor was supplied or verified.
- Aggregate L4-Minimum: **BLOCKED / NOT VERIFIED**. No control is promoted to PASS solely from this GitHub artifact readback.
- GitHub Actions artifacts remain within the GitHub failure domain and have the listed expiry. This check does not prove recovery from GitHub unavailability.

## 5. Scope boundary

Only GitHub artifact download/readback and local byte-level validation were performed. No VPS/SSH, T0 API, SQLite, canonical data, runtime, key/signing operation, owner storage, external provider, workflow dispatch, test rerun, deployment, cleanup, deletion, or trading action occurred. T0 remains unchanged; paper-only and `AI_EXECUTION_ENABLED=false` remain in force.

