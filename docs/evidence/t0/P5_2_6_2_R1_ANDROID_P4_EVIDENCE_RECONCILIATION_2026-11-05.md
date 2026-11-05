# P5.2.6.2-R1 — Android P4 Evidence Reconciliation

- Review date: 2026-11-05
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Workstream: documentation/evidence reconciliation only
- Verdict: **PARTIAL / NOT VERIFIED**
- Runtime or test execution: **NOT RUN**
- Canonical T0 DB / Feeder / exchange / live orders: **NOT TOUCHED**

## 1. Scope and source identities

This reconciliation checks whether the Android P4 evidence referenced by the manifest can be independently retrieved from the repository, GitHub Actions metadata, current conversation uploads, or the available personal Library search.

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

These checks establish that the payloads were not located in the inspected sources. They do not prove that no copy exists elsewhere (for example, on the Android device or in an unindexed external archive).

## 3. Per-artifact reconciliation

The SHA-256 values below are copied from the Android inventory recorded in the manifest. Since the corresponding bytes were not retrieved, none of these hashes has been independently recomputed.

| # | Artifact referenced by manifest | Manifest SHA-256 | Payload availability | Recomputed SHA-256 |
|---:|---|---|---|---|
| 1 | P4.1 runtime heartbeat log | `6c66adb27b221b6c9afb45b6aaf76b435082b4d642256772363b14bbda01c232` | NOT RETRIEVABLE | NOT RUN |
| 2 | P4.1 background runtime log | `48e9c1c8aa6bfc85b2440f0f220eb45d107984901a3690cc6352719c29024a7d` | NOT RETRIEVABLE | NOT RUN |
| 3 | P4.2 Natural Doze log | `814755242d9004f0ff7d4ad9820cdf82c7d4026bd555f8c7e359e23608f07e62` | NOT RETRIEVABLE | NOT RUN |
| 4 | P4.2 Wake-Lock log | `7121bc8f6901a205aba20e56860c38633017272e2eef8a36f98a7ffd15e763f2` | NOT RETRIEVABLE | NOT RUN |
| 5 | P4.3 process A script | `cc4c1adf62643e00c965ff551698ac9f9d4a229cd8b88b1d9933bc7c3cf1b8d5` | NOT RETRIEVABLE | NOT RUN |
| 6 | P4.3 process B script | `06fb92b3b0b27b1179d0b52d57a55522a511a9c295dfa5989c46303482a53b62` | NOT RETRIEVABLE | NOT RUN |
| 7 | P4.3 process A log | `82e02383775d883d708a2225feee34bb4b0ec4b00755f4475e28a1a0ac49d48d` | NOT RETRIEVABLE | NOT RUN |
| 8 | P4.3 process B log | `077118969bcb80286102c93bfeb9fe23e21093fe99ce6d5f175965db2b5d0069` | NOT RETRIEVABLE | NOT RUN |
| 9 | P4.4 process A script | `926fc9f8a2413f9c752b004c62aaff842eb0194fc114f59f7d47d8c0124e597a` | NOT RETRIEVABLE | NOT RUN |
| 10 | P4.4 process B script | `3f765ffccda8ab0011e6d6e7bd53fe700795309f4025befc78bcb56ca2336e1d` | NOT RETRIEVABLE | NOT RUN |
| 11 | P4.4 process A log | `2e3d82b5f5be50c523861339047ca9a8623fed7fe4c25974539e82ef6712c790` | NOT RETRIEVABLE | NOT RUN |
| 12 | P4.4 process B log | `82e5d199713e717060d3a245e63b4f549d9432861e2c49336b8799d0f55b3e37` | NOT RETRIEVABLE | NOT RUN |
| 13 | P4.5 process A script | `278da0bcc624f9945ebe5db2d858d09d5b8b2998a20e23483d3ef90e4e156444` | NOT RETRIEVABLE | NOT RUN |
| 14 | P4.5 process B script | `fed47242e6b098d8faef8d81e0c196a9aca09a918dcc7f3a54e344358d3d0326` | NOT RETRIEVABLE | NOT RUN |
| 15 | P4.5 process A stdout | `3e36cb9d4bd7f3c34114acebf98ccf452c1347ac3d530c1566b801881d6ad969` | NOT RETRIEVABLE | NOT RUN |
| 16 | P4.5 process A log | `3e36cb9d4bd7f3c34114acebf98ccf452c1347ac3d530c1566b801881d6ad969` | NOT RETRIEVABLE | NOT RUN |
| 17 | P4.5 process B log | `9fed174c40cccd9b82f41d40b4053702412e2c1756502fa404e555b7548a41ee` | NOT RETRIEVABLE | NOT RUN |

The manifest records identical hashes for P4.5 process A stdout and process A log. This equality is preserved as a manifest observation only; their bytes were not available for direct comparison.

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

## 5. Limits and next action

- No artifact payload bytes were available; checksum verification is **NOT VERIFIED**.
- Run-specific source identity for historical P4 execution remains **UNVERIFIED**.
- No P4 test was rerun. Natural Doze remains **INTERRUPTED / DEFERRED** as instructed.
- This reconciliation does not authorize canonical T0 DB creation, Feeder activation, exchange connectivity, market-data sync, or live execution.
- `ai_execution_enabled=false`; paper-only boundary remains unchanged.

Next action: obtain the original P4 evidence package from the Android/Termux device or its original archive (the 17 files listed above), preserving relative paths. Then independently recompute SHA-256 and inspect source-SHA evidence. Do not rerun P4 tests as a substitute for retrieving the historical artifacts.
