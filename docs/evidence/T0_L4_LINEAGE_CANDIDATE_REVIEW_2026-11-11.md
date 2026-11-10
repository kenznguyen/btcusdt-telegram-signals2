# T0 L4-Minimum — Lineage Candidate Review

Date: 2026-11-11
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

## Scope

Review the non-allowlisted L4 workflow lineage outputs identified in `T0_L4_ACTIONS_WORKFLOW_ARTIFACT_INVENTORY_2026-11-11.md`. Select at most a candidate with additional provenance value. Do not bulk-add historical outputs. No VPS, T0 SQLite, signer, trust-root, offline verification, artifact deletion, retention or cleanup operations.

## Candidate decision

Selected the newest available successful lineage snapshot produced by validation of the then-current five-entry allowlist:

- Workflow run: `42917935285`
- Event: `push`
- Exact source SHA: `cab8122c94e8bb8f30052ae44483fb1ec7e4de65`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Artifact ID: `13810187202`
- Artifact name: `t0-l4-minimum-lineage-42917935285`
- Size: `1,151` bytes
- GitHub artifact expiry: `2026-11-17T22:48:40Z`
- GitHub-reported ZIP SHA-256: `db4e86e8b976304ae1daf90b14dc49cd2f4b149c9c2449867d796b515cd76d07`
- Independently downloaded ZIP size/SHA-256: `1,151` bytes / `db4e86e8b976304ae1daf90b14dc49cd2f4b149c9c2449867d796b515cd76d07`

Archive inspection:
- Exactly four members: `l4-source-sha.txt`, `l4-validation-scope.txt`, `l4-lineage-contract-tests.log`, `l4-lineage-contract-verdict.txt`.
- Source marker exactly matches `cab8122c94e8bb8f30052ae44483fb1ec7e4de65`.
- Scope marker: `T0_L4_MINIMUM_LINEAGE=GITHUB_HOSTED_READ_ONLY`.
- Verdict: `L4_MINIMUM_LINEAGE_CONTRACT=PASS`.
- Test log: 12 tests, all `ok`.

Rationale: this is a later successful source snapshot than the previously allowlisted lineage artifact from run `42917592435`, and it validates the exact commit that introduced the five-entry allowlist. It contributes a newer source/validation point within the existing `L4_LINEAGE_CONTRACT_CI` class. It is not a new evidence class and is not owner-held custody evidence.

## Allowlist update

- Previous allowlist blob: `2fe01dbd2e3367db821f8e18503f965dc32fd42b` (five entries).
- Added only artifact `13810187202`; preserved all five existing records.
- Updated allowlist blob: `0280cd7751c9660baec237242ca7aadef09205a6`.
- Commit: `0251a8cc7995903d2516fc84cc0a33b73ec02777`.
- No historical allowlist entry was removed.

## CI validation of the update

Workflow run: [42922670634](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42922670634)

- Event: `push`
- Exact checked-out/source SHA: `0251a8cc7995903d2516fc84cc0a33b73ec02777`
- Overall jobs: all three SUCCESS.
- Lineage/policy contract job `130201149131`: 12/12 PASS.
- Repository-file inventory job `130201222951`: 10/10 PASS.
- Artifact manifest/readback job `130201223038`: 19/19 PASS.
- Total: 41/41 tests PASS.

Output artifact metadata:
- Lineage ID `13813120888`, size 1,151 bytes, GitHub ZIP SHA-256 `4686edd0c1e80f4a5793aa8d79ac4ce232ee64bd59cee2bfa633c14afd3d29d1`, expiry `2026-11-17T23:21:23Z`.
- Repository inventory ID `13811119271`, size 4,490 bytes, GitHub ZIP SHA-256 `ab8944fe9edb3446a50df1b8041743e93bb6bb628dee70956913c54b862222da`, expiry `2026-11-17T23:21:23Z`.
- Manifest ID `13813280057`, size 3,269 bytes, GitHub ZIP SHA-256 `cc969116e687792321240e19cfa2125abfb8a884328e03715937746709b9b26d`, expiry `2026-11-17T23:21:23Z`.

Independent output readback:
- Manifest ZIP downloaded and re-hashed: 3,269 bytes; SHA-256 matches GitHub metadata.
- Manifest JSON: 12,001 bytes; SHA-256 `520fd49f87595cd39b412a0533ce579c8ead1456ad0361a712b52786bebad428`; sidecar matches.
- Manifest contains exactly six source artifacts: two P1.8.14 synthetic artifacts and four L4 lineage CI artifacts, including selected artifact `13810187202`. It does not include outputs from its own run.
- Lineage output ZIP independently re-hashed: 1,151 bytes; SHA-256 matches GitHub metadata. Source marker matches `0251a8cc7995903d2516fc84cc0a33b73ec02777`; 12 tests; PASS verdict.
- Repository inventory ZIP independently re-hashed: 4,490 bytes; SHA-256 matches GitHub metadata. Inventory JSON is 9,753 bytes; sidecar matches; source commit is `0251a8cc7995903d2516fc84cc0a33b73ec02777`; 40 paths / 518,716 source bytes.

## Non-selected historical outputs and limits

The other historical lineage outputs remain unselected. Their metadata identifies them as the same generated `L4_LINEAGE_CONTRACT_CI` output class; no second evidence class was established that would justify bulk inclusion. This review does not claim that every remaining historical ZIP was independently downloaded or member-rehashed. Their payload-level status remains NOT VERIFIED unless separately documented.

Manifest and repository-inventory bundles remain generated workflow outputs, not source evidence. No L4 control disposition is upgraded by this selection or CI run.

## Status

- Selected candidate payload verification: PASS.
- Allowlist update committed: PASS.
- CI validation on exact allowlist-update SHA: PASS (41/41).
- Independent readback of all three current-run output ZIPs: PASS.
- Remaining historical lineage payloads: NOT VERIFIED / NOT SELECTED.
- Complete repository-wide Actions artifact inventory: NOT VERIFIED / outside this report's scope.
- Aggregate L4-Minimum: BLOCKED / NOT VERIFIED.

## Next step

Reconcile the updated allowlist and six-entry manifest into the current evidence register/crosswalk, then assess whether the evidence baseline is ready for signature/negative-verification design. Do not generate keys, sign, alter trust roots, perform offline verification, access VPS/SQLite, or carry out destructive/retention operations. Option C — No Destructive Authority remains ACTIVE.
