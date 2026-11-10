# T0 L4-Minimum — GitHub Multi-Artifact Inventory and Manifest Pilot

Date: 2026-11-10 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

## Scope and boundaries

GitHub-hosted, read-only artifact discovery/readback for three explicitly allowlisted GitHub Actions artifacts. Build a deterministic manifest containing exact run/artifact identity, source SHA, retention timestamps, archive SHA-256 and per-member SHA-256.

No VPS/SSH, canonical T0 SQLite, owner storage access, signer/key/trust-root operation, signature verification, offline verification, T1, PostgreSQL, service operation, artifact deletion/retention mutation or trading action.

## Source and workflow

- Collector source SHA: `db01cbe7750b75fcaafd4576d646d04c5b029c4b`
- Workflow blob: `b01842b3b4ad7e834256b0f270688f758b8abed9`
- Collector module blob: `77b9fd9a7fafd1d17539fb517bcf84c4c8e024d4`
- Collector contract tests blob: `ae122dc7bf3a53be443e17edce8c19e6cb32d868`
- Explicit allowlist blob: `d80b386e981bc1aec259e1026463a7abe39b4b1c`
- The allowlist pins exact run IDs, artifact IDs, names, branches, source SHAs, workflow paths and evidence classes. Source SHAs must be ancestors of the collector commit. No automatic "latest artifact" substitution is allowed.
- API read permission is limited to `actions: read` and `contents: read`; bearer authorization is stripped on redirects to artifact storage.

## Workflow verification

Run: [42834966105](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42834966105)
- Event: `push`
- Exact checked-out/source SHA: `db01cbe7750b75fcaafd4576d646d04c5b029c4b`
- Lineage job: `129894622621`, SUCCESS, 11/11 tests.
- Artifact manifest job: `129894707925`, SUCCESS, 19/19 tests; `L4_ARTIFACT_MANIFEST=PASS`.
- Run conclusion: SUCCESS.

## Allowlisted source artifacts

| Artifact ID | Source run | Source SHA | Evidence class | ZIP SHA-256 | Members |
|---:|---:|---|---|---|---:|
| 13546255148 | 42304505004 | `19a6629212f2f98aaa08c4ebe6ceb68801881732` | CI synthetic test bundle | `14e157cd8a393a743e01e12a915ab69636cf7cb4765f8a331953daeef1987b6f` | 47 |
| 13545287609 | 42304505004 | `19a6629212f2f98aaa08c4ebe6ceb68801881732` | CI independent-runner verification | `418fff2ffa874003527db5d83d8717bf8946b489c4e3a62b023f4c5e5e6feedd` | 2 |
| 13771662067 | 42831240089 | `27aea002a3f404792d4c1a3dc56eff77c2163840` | L4 lineage contract CI | `50991097fb0febf8f38398c656c6edf600f8a079bccd2dbf23a36873931bba68` | 4 |

All three source ZIPs were downloaded independently. Their exact bytes matched the SHA-256 values in the generated manifest. All 53 member byte sequences were independently hashed and matched their manifest entries (47 + 2 + 4). GitHub compare results confirmed each source SHA is an ancestor of the collector source SHA with `behind_by=0`.

Retention:
- Both P1.8.14 artifacts expire `2026-11-13T22:24:44Z`.
- L4 lineage source artifact expires `2026-11-17T14:09:25Z`.
- No retention setting was changed and no artifact was deleted.

## Generated manifest artifact

- Name: `t0-l4-artifact-manifest-42834966105`
- Artifact ID: `13772792245`
- Size: 2,877 bytes
- Expiry: `2026-11-17T14:31:38Z`
- Upload-reported and independently downloaded ZIP SHA-256: `a361eae206bffc312e1e1c04cd86aa9f9b75c8eb748900b6f663955efa08e9e4`
- Manifest JSON SHA-256: `a2d4089abd2fcf820919c4ba4cb39108fc1e1823c0e325efb2b8b005fdb5c4ec`; matches the adjacent `.sha256` file.
- Manifest contains three artifact records and all 53 member digests.

## Earlier failure and correction

Run [42834714404](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42834714404) failed closed with `GITHUB_RESPONSE_TOO_LARGE`: the GitHub compare response for an older source SHA exceeded the initial 1 MiB API response cap. The collector now requests a bounded one-commit comparison page and uses a 4 MiB API response ceiling; the complete multi-artifact run above passed. The cap remains bounded, and larger/ambiguous responses still fail closed.

## Disposition

- Lineage/reference gate: **PASS — 11/11**.
- Multi-artifact GitHub inventory/ZIP readback: **PASS for the three allowlisted artifacts**.
- Manifest contract tests: **PASS — 19/19**.
- Independent ZIP SHA-256 verification: **PASS — 3/3**.
- Independent member SHA-256 verification: **PASS — 53/53**.
- Complete L4 evidence package inventory: **NOT VERIFIED**; this is a three-artifact pilot only.
- L4M-01: **PARTIAL** — GitHub artifacts read back; owner custody and complete package not proven.
- L4M-02: **NOT VERIFIED** — CI synthetic verification artifact is not owner signer separation/custody proof.
- L4M-03: **PARTIAL — SYNTHETIC/DESIGN ONLY**.
- L4M-04: **PARTIAL — SYNTHETIC/CI ONLY**; owner offline assertion not performed.
- L4M-05: **PARTIAL — SYNTHETIC MODEL ONLY**.
- L4M-06: **PARTIAL — SYNTHETIC POLICY ONLY**.
- L4M-07: **PARTIAL — SYNTHETIC MODEL ONLY**.
- L4M-08: **DOCUMENTARY PASS ONLY**.
- L4M-09: **OWNER-WAIVED**.
- L4M-10: **NOT VERIFIED / OWNER-ONLY**.
- Aggregate L4-Minimum: **BLOCKED / NOT VERIFIED**.
- Signature verification and network-disabled offline verification: **NOT STARTED**.
- Option C — No Destructive Authority: **ACTIVE**.

## Next step

Reconcile all remaining existing GitHub evidence artifacts referenced by the current matrix/register and extend the explicit allowlist only with exact verified run/artifact metadata. Preserve original artifacts and expiry evidence. Do not treat this pilot as a frozen L4 package. After the available evidence inventory is complete and stable, proceed to exact-object signature/negative verification and then network-disabled offline verification. Keep owner custody/control and owner offline assertions separate from CI results.
