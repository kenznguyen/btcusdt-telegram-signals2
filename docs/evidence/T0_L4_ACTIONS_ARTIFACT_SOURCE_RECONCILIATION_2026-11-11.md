# T0 L4-Minimum — GitHub Actions Source Artifact Reconciliation

Date: 2026-11-11
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Validated collector source SHA: `258c971d06baa9818980ebcf3d1db046b412beb7`
Current branch HEAD before this report: `db3fa4ca5aacccd445f0961fdd0a1876330b0cd0`
Allowlist blob: `d481ca0baaca9605cfda1e3ebb79e423b17ac876`

## 1. Scope and method

Reconciled the four explicitly allowlisted source artifacts against their authoritative GitHub workflow-run artifact metadata, then downloaded each exact artifact ZIP and compared its byte length, archive SHA-256, member paths, member byte lengths and member SHA-256 values against the manifest produced by collector run [42915451341](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42915451341).

The latest collector run metadata identifies:
- workflow: T0 L4-Minimum Validation (workflow ID `413351263`)
- run: `42915451341`, event `push`, conclusion `success`
- branch: `feature/t0-centralized-data-feeder-p1-20261101`
- exact workflow source SHA: `258c971d06baa9818980ebcf3d1db046b412beb7`
- outputs: repository inventory artifact `13810135011`, manifest artifact `13809910243`, lineage artifact `13809780354`.

The collector output artifacts are outputs, not source inputs. None is self-included in its own manifest.

## 2. Source artifact metadata and independent payload readback

| Source run | Source SHA | Artifact ID | Name | Size | Expires (UTC) | Members | ZIP SHA-256 |
|---|---|---:|---|---:|---|---:|---|
| `42304505004` | `19a6629212f2f98aaa08c4ebe6ceb68801881732` | `13546255148` | `p1-8-synthetic-evidence-19a6629212f2f98aaa08c4ebe6ceb68801881732` | 1,208,828 | 2026-11-13 22:24:44 | 47 | `14e157cd8a393a743e01e12a915ab69636cf7cb4765f8a331953daeef1987b6f` |
| `42304505004` | `19a6629212f2f98aaa08c4ebe6ceb68801881732` | `13545287609` | `p1-8-independent-attestation-verification-19a6629212f2f98aaa08c4ebe6ceb68801881732` | 9,065 | 2026-11-13 22:24:44 | 2 | `418fff2ffa874003527db5d83d8717bf8946b489c4e3a62b023f4c5e5e6feedd` |
| `42831240089` | `27aea002a3f404792d4c1a3dc56eff77c2163840` | `13771662067` | `t0-l4-minimum-lineage-42831240089` | 1,125 | 2026-11-17 14:09:25 | 4 | `50991097fb0febf8f38398c656c6edf600f8a079bccd2dbf23a36873931bba68` |
| `42836094887` | `b3a975e151241ba5d5116f49a8d00a056adf9fa4` | `13774031418` | `t0-l4-minimum-lineage-42836094887` | 1,151 | 2026-11-17 14:38:12 | 4 | `801bbc22e1979b3e5260371a22db305d37ddd2bc6837aae3c00c99d60595abcf` |

All four GitHub run records identify the same active branch and the exact source SHAs shown above. All four artifacts are currently unexpired at the time of this check.

**Independent verification result: PASS for the four allowlisted artifacts.** Exact ZIP byte lengths and SHA-256 values match the manifest; all 57 archive members (47 + 2 + 4 + 4) match exact member paths, byte lengths and SHA-256 values. No member mismatch was found.

## 3. Manifest output readback

- Output artifact ID: `13809910243`
- Name: `t0-l4-artifact-manifest-42915451341`
- Size: 3,037 bytes
- Expiry: `2026-11-17T22:32:10Z`
- Independently downloaded ZIP SHA-256: `3914efd3be41a8c92580835826f5c472b752d58a38d2fdaab123dd15e8bc19ef`
- JSON member SHA-256: `75ac4d17c46c4852f2a6a646fdefb3a6f73e1c5bec911c5729acb8affbba94bc`
- The JSON digest matches the included `.sha256` sidecar.
- Manifest schema: `T0_L4_GITHUB_ARTIFACT_MANIFEST_V1`; records exactly the four allowlisted source artifact IDs.

The output lineage artifact `13809780354` and repository-source inventory artifact `13810135011` remain output artifacts for run `42915451341`, not source artifacts in the four-item allowlist. Their presence does not expand the source allowlist implicitly.

## 4. Discovery completeness and disposition

| Check | Result |
|---|---|
| Four allowlist records vs exact source-run metadata | PASS |
| Source artifact ID/name/branch/source SHA/expiry binding | PASS |
| Downloaded ZIP size and SHA-256 for all four sources | PASS |
| All 57 member paths, sizes and SHA-256 values | PASS |
| Manifest ZIP and JSON sidecar readback | PASS |
| Output-vs-source artifact separation | PASS |
| Complete repository-wide enumeration of all eligible Actions runs/artifacts | NOT VERIFIED |

This is a complete verification of the **four declared source artifacts**, not proof that the allowlist contains every eligible artifact in the repository. A repository-wide, paginated workflow-run/artifact discovery baseline has not yet been recorded. Do not claim the source-artifact inventory is globally complete, and do not add candidate artifacts without exact run metadata and evidence-class review.

## 5. Control impact and next gate

No L4 control is promoted by this result. The four sources remain CI/synthetic evidence within the GitHub failure domain; they do not establish owner custody, independent offline operation, signer separation, trusted latest-head freshness, owner-copy recovery or L4M-10 acceptance. Aggregate L4-Minimum remains **BLOCKED / NOT VERIFIED**.

Next permitted step: enumerate relevant workflow runs and their artifacts from authoritative Actions metadata, classify every candidate as source evidence or generated output, and reconcile any eligible candidate against exact source SHA, run ID, artifact ID/name, expiry and payload hashes. Keep the 40-file repository source inventory as a separate inventory class. Do not generate/use signing keys, change trust roots, run offline verification, access VPS/SQLite, delete artifacts, or perform cleanup/expiry/destructive actions. Option C — No Destructive Authority remains ACTIVE.
