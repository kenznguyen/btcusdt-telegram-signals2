# T0 P4 Android Background & Restart Evidence Manifest

- Evidence date: 2026-11-02
- Timezone: Asia/Ho_Chi_Minh (UTC+07:00)
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Evidence environment: Android / Termux, shadow databases only
- Manifest prepared: 2026-11-03
- Overall verdict: **CONDITIONAL PASS**
- Production readiness: **NOT APPROVED**

## 1. Source identity

| Field | Recorded value |
|---|---|
| Repository checkout | `$HOME/five-layer-system-source-p3` |
| Observed HEAD | `1c16755a07a053e1f225c8861ec76dc9ced1a5d8` |
| Commit date | `2026-11-02T04:30:32-05:00` |
| Commit subject | `ci: add isolated manual T0 P3 component test workflow` |
| Branch at inspection | `DETACHED_HEAD` |
| Working tree at inspection | Clean (empty `git status --porcelain=v1`) |
| Current HEAD matches recorded P3 SHA | Yes |
| Historical P4 execution source identity | **UNVERIFIED** |

The inspected checkout matches the recorded P3 commit. This does not prove that every P4 test was executed from this exact commit because no run-specific source SHA was present in the supplied P4 logs. Do not set `source_identity_verified=true`.

## 2. Scope and safety boundary

- All P4 tests used Android shadow/test databases.
- Canonical T0 database: **NOT CREATED**.
- Production Feeder: **NOT RUNNING**.
- Exchange credentials/connection: **NOT CONFIGURED**.
- Live trading / real orders: **DISABLED**.
- No P4 test is authorized as evidence of production readiness.
- This manifest records evidence supplied from the Android device; it does not claim independent access to the device filesystem.

## 3. Test results

### P4.1 — Runtime heartbeat

**Status: PASS**

Evidence: `p4_1_lease_shadow_20261102/runtime_heartbeat.log`

- Lease acquired: owner `android-shadow-runtime`, generation 1, TTL 60 seconds.
- Heartbeat interval: 15 seconds.
- Heartbeats: 4/4 passed.
- `lease_current=true` for each recorded heartbeat.
- SQLite integrity: `ok`.
- Lease release: PASS.
- Test marker: `P4_1_RUNTIME_HEARTBEAT=PASS (4/4)`.

### P4.1 — Background runtime

**Status: PASS**

Evidence: `p4_1_lease_shadow_20261102/runtime_background.log`

- Lease acquired: owner `android-background-shadow`, generation 1, TTL 60 seconds.
- Heartbeat interval: 15 seconds.
- Heartbeats: 8/8 passed.
- `lease_current=true` for each recorded heartbeat.
- SQLite integrity: `ok`.
- Lease release: PASS.
- Test marker: `P4_1_BACKGROUND_TEST=PASS (8/8)`.

This is a short background observation, not proof of multi-hour or multi-day process stability.

### P4.2 — Natural Doze observation

**Status: INTERRUPTED**

Evidence: `p4_2_natural_doze_shadow_20261102/natural_doze.log`

- Lease acquired: owner `android-p4-2-natural-shadow`, generation 1, TTL 60 seconds.
- Configured heartbeat interval: 15 seconds; planned duration: 1,200 seconds.
- One heartbeat passed with a 15.02-second gap.
- Observation was interrupted at `2026-11-02T17:08:13.108577+07:00`.
- Error: `Lease lost before heartbeat; no takeover attempted`.
- Automatic takeover: not attempted.
- Fail-closed behavior: observed.
- Root cause (Doze vs. device/vendor process management): **NOT CONFIRMED**.

The result does not pass the Natural Doze resilience objective. The fail-closed response is a safety property, not evidence that the Feeder can remain active during Doze.

### P4.2 — Wake-Lock comparison

**Status: PASS**

Evidence: `p4_2_wakelock_shadow_20261102/wakelock_shadow.log`

- Lease TTL: 60 seconds.
- Heartbeat interval: 15 seconds.
- Heartbeats: 12/12 passed.
- Observed heartbeat gaps: 15.02–15.03 seconds.
- SQLite integrity: `ok`.
- Lease release: PASS.
- Test marker: `P4_2_WAKELOCK_TEST=PASS (12/12)`.

This result applies to the Wake-Lock test condition only; it does not override the interrupted Natural Doze result.

### P4.3 — Force-stop / restart fencing

**Status: PASS**

Evidence:
- `p4_3_force_stop_shadow_20261102/process_a.log`
- `p4_3_force_stop_shadow_20261102/process_b.log`

Recorded behavior:
- Process A acquired generation 1 and waited for force-stop.
- Process B observed A's prior lease and acquired generation 2 after the lease became available.
- Stale A write rejected: PASS.
- Stale A release rejected: PASS.
- B lease current: PASS.
- SQLite integrity: `ok`.
- B release: PASS.
- Test marker: `P4_3_FORCE_STOP_TEST=PASS`.

### P4.4 — Reboot / takeover fencing

**Status: PASS**

Evidence:
- `p4_4_reboot_shadow_20261102/process_a.log`
- `p4_4_reboot_shadow_20261102/process_b.log`

Recorded behavior:
- Process A acquired generation 1 and waited for reboot.
- Process B acquired generation 2 after reboot.
- Stale A write rejected: PASS.
- Stale A release rejected: PASS.
- B lease current: PASS.
- SQLite integrity: `ok`.
- B release: PASS.
- Test marker: `P4_4_REBOOT_TEST=PASS`.

This test does not independently prove full recovery consistency of Paper Ledger, Risk State, or Paper State.

### P4.5 — Two-writer exclusion and fencing

**Status: PASS**

Evidence:
- `p4_5_two_writer_shadow_20261102/process_a.log`
- `p4_5_two_writer_shadow_20261102/process_b.log`

Recorded behavior:
- A acquired generation 1.
- B was blocked while A remained active.
- A remained current and released the lease.
- B acquired generation 2 after A's release.
- Stale A write rejected: PASS.
- Stale A release rejected: PASS.
- B lease current: PASS.
- SQLite integrity: `ok`.
- B release: PASS.
- Test marker: `P4_5_TWO_WRITER_TEST=PASS`.

## 4. Evidence artifact SHA-256 inventory

The following 17 hashes were supplied by the Android Termux evidence inventory. They fingerprint the listed files as observed during that inventory; a hash alone does not establish the semantic correctness of a test result.

| Artifact | SHA-256 |
|---|---|
| P4.1 runtime heartbeat log | `6c66adb27b221b6c9afb45b6aaf76b435082b4d642256772363b14bbda01c232` |
| P4.1 background runtime log | `48e9c1c8aa6bfc85b2440f0f220eb45d107984901a3690cc6352719c29024a7d` |
| P4.2 Natural Doze log | `814755242d9004f0ff7d4ad9820cdf82c7d4026bd555f8c7e359e23608f07e62` |
| P4.2 Wake-Lock log | `7121bc8f6901a205aba20e56860c38633017272e2eef8a36f98a7ffd15e763f2` |
| P4.3 process A script | `cc4c1adf62643e00c965ff551698ac9f9d4a229cd8b88b1d9933bc7c3cf1b8d5` |
| P4.3 process B script | `06fb92b3b0b27b1179d0b52d57a55522a511a9c295dfa5989c46303482a53b62` |
| P4.3 process A log | `82e02383775d883d708a2225feee34bb4b0ec4b00755f4475e28a1a0ac49d48d` |
| P4.3 process B log | `077118969b80286102c93bfeb9fe23e21093fe99ce6d5f175965db2b5d0069` |
| P4.4 process A script | `926fc9f8a2413f9c752b004c62aaff842eb0194fc114f59f7d47d8c0124e597a` |
| P4.4 process B script | `3f765ffccda8ab0011e6d6e7bd53fe700795309f4025befc78bcb56ca2336e1d` |
| P4.4 process A log | `2e3d82b5f5be50c523861339047ca9a8623fed7fe4c25974539e82ef6712c790` |
| P4.4 process B log | `82e5d199713e717060d3a245e63b4f549d9432861e2c49336b8799d0f55b3e37` |
| P4.5 process A script | `278da0bcc624f9945ebe5db2d858d09d5b8b2998a20e23483d3ef90e4e156444` |
| P4.5 process B script | `fed47242e6b098d8faef8d81e0c196a9aca09a918dcc7f3a54e344358d3d0326` |
| P4.5 process A stdout | `3e36cb9d4bd7f3c34114acebf98ccf452c1347ac3d530c1566b801881d6ad969` |
| P4.5 process A log | `3e36cb9d4bd7f3c34114acebf98ccf452c1347ac3d530c1566b801881d6ad969` |
| P4.5 process B log | `9fed174c40cccd9b82f41d40b4053702412e2c1756502fa404e555b7548a41ee` |

P4.5 process A stdout and process A log have identical SHA-256 values, so their contents are identical according to the supplied checksum inventory.

## 5. Consolidated verdict

| Area | Result |
|---|---|
| Runtime heartbeat | PASS |
| Background runtime | PASS |
| Natural Doze | INTERRUPTED |
| Wake-Lock | PASS |
| Force-stop / restart | PASS |
| Reboot / takeover | PASS |
| Two-writer fencing | PASS |
| Historical P4 source identity | UNVERIFIED |
| Overall P4 | **CONDITIONAL PASS** |

## 6. Open limitations / follow-up gates

1. Obtain a run-specific source identity record before claiming P4 execution was performed on the inspected P3 SHA.
2. Natural Doze resilience remains unproven; do not treat Wake-Lock PASS as a substitute.
3. Full backup/restore validation must include candles, Paper Ledger, Risk State, and Paper State.
4. WAL-consistent backup behavior, extended runtime stability, and recovery after real power/kernel failure remain unproven.
5. No canonical database activation or production Feeder start is authorized by this evidence.

## 7. Explicit non-actions

- No P4 tests were rerun for this manifest.
- No SQLite database was opened or modified while preparing this document.
- No canonical database was created.
- No Feeder was started.
- No exchange was connected.
- No live trading or real order execution was enabled.

## 8. Reuse in P5

This manifest is the P4 evidence baseline for the Android-canonical / PC-worker architecture review. It is not a production certification and does not grant PC direct access to the Android canonical SQLite database.
