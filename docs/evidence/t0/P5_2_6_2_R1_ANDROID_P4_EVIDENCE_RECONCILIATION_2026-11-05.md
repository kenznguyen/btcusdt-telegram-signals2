# P5.2.6.2-R1 — Android P4 Evidence Reconciliation

- Review date: 2026-11-05
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Workstream: documentation/evidence reconciliation only
- Verdict: **PAYLOAD INTEGRITY VERIFIED (17/17); HISTORICAL RUN PROVENANCE NOT VERIFIED**
- Overall reconciliation: **PARTIAL / NOT VERIFIED**
- Runtime or test execution: **NOT RUN**
- Canonical T0 DB / Feeder / exchange / live orders: **NOT TOUCHED**

## 1. Scope and source identities

This reconciliation initially searched repository/CI/library sources, then recovered the original P4 payloads from the user's Android/Termux device and compared all 17 SHA-256 values with the manifest.

Baseline manifest:
- Path: `docs/evidence/t0/P4_ANDROID_BACKGROUND_RESTART_EVIDENCE_2026-11-02.md`
- Manifest branch: `docs/p4-evidence-manifest-20261103`
- Manifest commit: `0ee3db621f6eecd42580dc29ef97915bdcc34fb2`
- Manifest blob SHA: `d1b353fc86842c98adabd06dd0c0172c45b5ce4c`

Recorded Android checkout:
- Observed source HEAD: `1c16755a07a053e1f225c8861ec76dc9ced1a5d8`
- Recorded checkout state: detached HEAD, clean.
- Historical source identity for each P4 test run: **UNVERIFIED**. The manifest explicitly says that the observed P3 checkout does not prove every earlier P4 run used that SHA.

## 2. Retrieval checks performed

| Source | Check | Result |
|---|---|---|
| GitHub source tree at Android observed SHA `1c16755a07a053e1f225c8861ec76dc9ced1a5d8` | Recursive tree inventory for P4 logs/scripts and named evidence paths | No matching P4 log/script files found |
| GitHub manifest branch `docs/p4-evidence-manifest-20261103` | Recursive tree inventory | Contains the evidence manifest; no referenced P4 log/script payloads found |
| GitHub code search | Exact search for `runtime_heartbeat.log` in this repository | 0 results |
| GitHub Actions | Runs created 2026-11-02, inspected returned run metadata | No Android P4 runtime-evidence workflow identified in the returned run set; listed runs were unrelated CI workstreams |
| Current conversation uploads | Files inventory | No uploaded files |
| Available personal Library | Search for the P4 directory names and representative log names | No matching P4 evidence files returned |
| Android/Termux device | Read-only discovery under `$HOME` | Original P4 scripts/logs found in the `p4_*_shadow_20261102` directories |
| Android/Termux SHA-256 | `sha256sum` against all 17 manifest payloads | **17/17 exact matches** |
| Android source checkout | `git rev-parse HEAD`; `git status --short` | HEAD `1c16755a07a053e1f225c8861ec76dc9ced1a5d8`, matching manifest's observed HEAD; no status output (clean) |

| GitHub Actions artifact candidate | Downloaded and inspected artifact from run `41512015687`, artifact `13172784987` (`p5-2-5-g0-evidence-66088d879628141688065eb80cffe0eda55b7343`) | Ruled out: archive contains only P5.2.5 G0 contract RED evidence; no Android P4 logs/scripts |
| GitHub code search | Exact search for three representative P4 SHA-256 values and `p4_3_force_stop_shadow_20261102` | 0 results for each query |

The candidate G0 archive was downloaded and opened locally. Its archive digest from GitHub metadata is `sha256:7b704a65de33204b69a822e4311eddf5934539c4f3a045ac1ee3811f5bddb353`; its contents are G0 contract-test logs/verdicts for source SHA `66088d879628141688065eb80cffe0eda55b7343`, not P4 Android evidence. It is therefore explicitly excluded from the P4 evidence set.

Repository/CI/library searches did not locate the payloads, but the Android/Termux device retained the original files. The user supplied the complete `sha256sum` output; every one of the 17 values matches the manifest exactly. This verifies payload integrity relative to the manifest, not the provenance of each historical test execution.

## 3. Per-artifact reconciliation

The SHA-256 values below were recomputed on the Android/Termux device with `sha256sum` and match the corresponding manifest values exactly.

| # | Artifact referenced by manifest | Manifest SHA-256 | Payload availability | Recomputed SHA-256 |
|---:|---|---|---|---|
| 1 | P4.1 runtime heartbeat log | `6c66adb27b221b6c9afb45b6aaf76b435082b4d642256772363b14bbda01c232` | AVAILABLE ON ANDROID/TERMUX | MATCH |
| 2 | P4.1 background runtime log | `48e9c1c8aa6bfc85b2440f0f220eb45d107984901a3690cc6352719c29024a7d` | AVAILABLE ON ANDROID/TERMUX | MATCH |
| 3 | P4.2 Natural Doze log | `814755242d9004f0ff7d4ad9820cdf82c7d4026bd555f8c7e359e23608f07e62` | AVAILABLE ON ANDROID/TERMUX | MATCH |
| 4 | P4.2 Wake-Lock log | `7121bc8f6901a205aba20e56860c38633017272e2eef8a36f98a7ffd15e763f2` | AVAILABLE ON ANDROID/TERMUX | MATCH |
| 5 | P4.3 process A script | `cc4c1adf62643e00c965ff551698ac9f9d4a229cd8b88b1d9933bc7c3cf1b8d5` | AVAILABLE ON ANDROID/TERMUX | MATCH |
| 6 | P4.3 process B script | `06fb92b3b0b27b1179d0b52d57a55522a511a9c295dfa5989c46303482a53b62` | AVAILABLE ON ANDROID/TERMUX | MATCH |
| 7 | P4.3 process A log | `82e02383775d883d708a2225feee34bb4b0ec4b00755f4475e28a1a0ac49d48d` | AVAILABLE ON ANDROID/TERMUX | MATCH |
| 8 | P4.3 process B log | `077118969bcb80286102c93bfeb9fe23e21093fe99ce6d5f175965db2b5d0069` | AVAILABLE ON ANDROID/TERMUX | MATCH |
| 9 | P4.4 process A script | `926fc9f8a2413f9c752b004c62aaff842eb0194fc114f59f7d47d8c0124e597a` | AVAILABLE ON ANDROID/TERMUX | MATCH |
| 10 | P4.4 process B script | `3f765ffccda8ab0011e6d6e7bd53fe700795309f4025befc78bcb56ca2336e1d` | AVAILABLE ON ANDROID/TERMUX | MATCH |
| 11 | P4.4 process A log | `2e3d82b5f5be50c523861339047ca9a8623fed7fe4c25974539e82ef6712c790` | AVAILABLE ON ANDROID/TERMUX | MATCH |
| 12 | P4.4 process B log | `82e5d199713e717060d3a245e63b4f549d9432861e2c49336b8799d0f55b3e37` | AVAILABLE ON ANDROID/TERMUX | MATCH |
| 13 | P4.5 process A script | `278da0bcc624f9945ebe5db2d858d09d5b8b2998a20e23483d3ef90e4e156444` | AVAILABLE ON ANDROID/TERMUX | MATCH |
| 14 | P4.5 process B script | `fed47242e6b098d8faef8d81e0c196a9aca09a918dcc7f3a54e344358d3d0326` | AVAILABLE ON ANDROID/TERMUX | MATCH |
| 15 | P4.5 process A stdout | `3e36cb9d4bd7f3c34114acebf98ccf452c1347ac3d530c1566b801881d6ad969` | AVAILABLE ON ANDROID/TERMUX | MATCH |
| 16 | P4.5 process A log | `3e36cb9d4bd7f3c34114acebf98ccf452c1347ac3d530c1566b801881d6ad969` | AVAILABLE ON ANDROID/TERMUX | MATCH |
| 17 | P4.5 process B log | `9fed174c40cccd9b82f41d40b4053702412e2c1756502fa404e555b7548a41ee` | AVAILABLE ON ANDROID/TERMUX | MATCH |

The manifest and recomputed device hashes both record identical values for P4.5 process A stdout and process A log. The two paths therefore have matching content hashes.

## 4. Historical test-result treatment

Preserve the manifest's historical labels without promoting them to independently verified results:

| Test | Manifest-recorded result | R1 reconciliation status |
|---|---|---|
| P4.1 runtime heartbeat | PASS (4/4) | RECORDED PASS; payload/source identity NOT VERIFIED |
| P4.1 background runtime | PASS (8/8) | RECORDED PASS; payload/source identity NOT VERIFIED |
| P4.2 Natural Doze | INTERRUPTED | INTERRUPTED / DEFERRED; no investigation or rerun |
| P4.2 Wake-Lock | PASS (12/12) | RECORDED PASS; payload/source identity NOT VERIFIED |
| P4.3 force-stop/restart fencing | PASS | RECORDED PASS; payload/source identity NOT VERIFIED |
| P4.4 reboot/takeover fencing | PASS | RECORDED PASS; payload/source identity NOT VERIFIED |
| P4.5 two-writer fencing | PASS | RECORDED PASS; payload/source identity NOT VERIFIED |
| Overall Android P4 | CONDITIONAL PASS | Remains CONDITIONAL PASS; not production certification |



### 5.1 Read-only log metadata scan (2026-11-05)

The user ran a recursive, read-only `grep` over the six P4 shadow directories, restricted to `*.py`, `*.log`, and `*.stdout`, searching for 40-character hexadecimal strings and source/commit/workflow/run identifiers plus the test date.

Observed results:
- The returned matches are timestamped test events from 2026-11-02 and test-status lines (heartbeat, lease acquisition/release, fencing/takeover assertions).
- No 40-character Git commit SHA, `GITHUB_SHA`, workflow run ID, or explicit source-SHA metadata appeared in the returned output.
- The logs therefore corroborate the recorded sequence/timing and historical test assertions, but do not establish the exact source revision used for each test.
- Scope limitation: the command searched the shadow directories only. Standalone preparation/test scripts in `$HOME` (for example `p4_1_runtime_heartbeat.py`, `p4_1_background_test.py`, `p4_2_natural_doze.py`, and `p4_2_wakelock_test.py`) were not included in that scan and remain to be checked read-only.

This does not change the 17/17 payload hash result or promote historical test labels to independently verified outcomes.



### 5.2 Standalone script and local Git metadata scan (2026-11-05)

The user ran the requested read-only checks against `$HOME/p4_*.py` and the local source checkout:

- Standalone script metadata grep: **NO MATCHES** for 40-character hexadecimal values, source/commit SHA labels, `GITHUB_SHA`, workflow/run identifiers, Git revision commands, or the P4 test date.
- Local checkout HEAD: `1c16755a07a053e1f225c8861ec76dc9ced1a5d8`.
- Local checkout status: clean (`git status --short` returned no output).
- Local Git history includes commits on 2026-11-01 and 2026-11-02, with the latest listed commit `1c16755a07a053e1f225c8861ec76dc9ced1a5d8` timestamped `2026-11-02T04:30:32-05:00` (commit subject: `ci: add isolated manual T0 P3 component test workflow`). Earlier listed commits include SQLite audit, runtime configuration, and data-integrity changes.

The local history establishes that the checkout contains commits dated around the P4 test date, but it does not link any individual P4 log/script to a specific commit or prove that this checkout was active during the recorded test sessions. The observed HEAD must therefore remain contextual metadata only, not a run-specific source SHA. The standalone scan found no embedded provenance to close this gap.

## 6. Limits and next action

- All 17 payload files were recovered on Android/Termux and their SHA-256 values match the manifest: **17/17 MATCH**.
- The observed Android checkout HEAD matches the manifest's observed HEAD (`1c16755a07a053e1f225c8861ec76dc9ced1a5d8`); `git status --short` returned no changes.
- Run-specific source identity for each historical P4 execution remains **UNVERIFIED**; the observed checkout HEAD does not prove which SHA each earlier test used.
- No P4 test was rerun. Natural Doze remains **INTERRUPTED / DEFERRED** as instructed.
- This reconciliation does not authorize canonical T0 DB creation, Feeder activation, exchange connectivity, market-data sync, or live execution.
- `ai_execution_enabled=false`; paper-only boundary remains unchanged.

Next action: no further provenance-bearing metadata was found in the standalone scripts or local Git history. Retain run-specific source identity as UNVERIFIED unless contemporaneous external records (for example, an archived test session transcript or SHA-bound CI artifact) are recovered. Do not execute scripts or rerun P4 tests.
