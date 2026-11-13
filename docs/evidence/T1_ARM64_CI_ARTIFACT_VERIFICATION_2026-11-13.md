# T1 Native ARM64 CI and Artifact Verification — 2026-11-13

## Scope

Verify the native ARM64 CI result and the exact GitHub Actions artifact produced for the T1 collector on the current Scaleway ARM64 host architecture. This increment is limited to CI evidence and artifact payload verification. No collector runtime execution or VPS modification was performed.

## Source and workflow provenance

- Repository: `kenznguyen/binance-futures-collector`
- Branch: `feature/t1-connection-sidecar-integration-20261107`
- Exact source SHA: `9b2af66e68206898e51f638b67497d574a7252c4`
- Changed file in that source commit: `.github/workflows/ci.yml` only
- Workflow file blob SHA: `e907972128d680d7d4b3cf0f0e1cbc533a53c869`
- Push workflow run: [43334117748](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43334117748) — completed / success
- PR workflow run: [43334123943](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43334123943) — completed / success
- Both runs report the exact head SHA above.

## CI results

Push run `43334117748`:
- Native ARM64 build/test/artifact job `131585840822`: SUCCESS.
- Native ARM64 runner assertion, format, Clippy, release build, tests, sidecar offline tests, ELF verification/checksum preparation, artifact upload: all SUCCESS.
- Docker build, security checks, dashboard frontend, dashboard backend, and existing x86-64 collector job: SUCCESS.

PR run `43334123943`:
- Native ARM64 build/test job `131585861454`: SUCCESS.
- Runner assertion, format, Clippy, release build, tests and sidecar offline tests: SUCCESS.
- ELF verification and artifact upload steps were SKIPPED by workflow conditions for the PR event; this does not invalidate the artifact from the successful push run.
- Other workflow jobs: SUCCESS.

Overall push CI: PASS. Overall PR CI: PASS.

## ARM64 artifact provenance and payload verification

- Artifact ID: `13996767785`
- Artifact name: `t1-collector-linux-aarch64-9b2af66e68206898e51f638b67497d574a7252c4`
- GitHub-reported size: 3,985,895 bytes
- GitHub expiry: `2026-11-20T00:09:20Z`
- Downloaded archive: `t1-arm64-9b2af66.zip`
- Downloaded ZIP size: 3,985,895 bytes
- ZIP SHA-256 independently computed: `a1fbb27bcdb7d47b223b3a85ed40bef0df2a2328a9ae3a0c4b735e3066a9e7b0`
- Archive members: `binance-futures-collector`, `SHA256SUMS`, `ELF-IDENTITY.txt`
- Embedded SHA256SUMS verification: PASS
- Binary SHA-256: `6dc9b691700c464784b475d2da2ffdcbb4eae62169ee31e74d8e0fba51966469`
- ELF identity: ELF64, little-endian, PIE, dynamically linked, AArch64; interpreter `/lib/ld-linux-aarch64.so.1`.
- `readelf -h` confirms machine `AArch64`.
- `file`, `readelf`, and checksum verification agree.

The x86-64 artifact from the same push run (ID `13995953595`) is not suitable for the ARM64 host and must not be used there.

## Disposition

- Exact-SHA native ARM64 CI: **PASS**.
- ARM64 artifact existence and source naming/provenance: **PASS**.
- Downloaded artifact ZIP and embedded binary checksum: **PASS**.
- ELF architecture verification: **PASS**.
- Current Scaleway host architecture (owner-provided observation): ARM64/aarch64; artifact architecture is compatible.
- T1 collector runtime acceptance: **NOT VERIFIED / BLOCKED**.
- T1 Order Book V1 runtime correctness: **NOT VERIFIED**.
- T1 → T2 real integration: **BLOCKED**.

This artifact verification does not prove runtime behavior, Binance collector acceptance, reconnect/re-anchor correctness in production, or T1→T2 integration.

## Safety boundary observed

No binary was executed on the VPS. No package, runner, service, systemd unit, autostart, credential, or exchange API key was installed or changed. No T0 database or canonical data was accessed. No trading API or order was used. No VPS deployment or persistent runtime activation occurred. `AI_EXECUTION_ENABLED=false`; paper-only posture remains.

## Next bounded step

If the owner continues the previously bounded runtime acceptance, transfer only the verified ARM64 artifact to the current host and perform a manually started, time-bounded, BTCUSDT-only, public-market-data runtime smoke with explicit output location and cleanup boundaries. Do not install a persistent runner, create a service/autostart, touch T0, use credentials, or place orders. Runtime validation must test the frozen Order Book V1 contract and fail closed on any unmet readiness condition. T1 → T2 remains blocked until runtime evidence and integration contract acceptance are separately established.
