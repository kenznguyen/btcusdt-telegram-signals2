# VPS ARM64 and T1 staging inventory — 2026-11-13

## Scope
Read-only inventory of the owner-provided replacement Scaleway VPS, Python/dependency environment, repository checkout, T1 staging, and application process/listener state. No remote action was performed by the assistant; all host observations below were pasted by the owner.

## Host and capacity
- Host: `scw-optimistic-jang`
- OS: Ubuntu 24.04.5 LTS
- Kernel: `6.8.0-147-generic`
- Architecture: `aarch64`
- CPU: 2 vCPU
- RAM: 3.8 GiB total; 3.4 GiB available at observation
- Root disk: 8.0 GB; 2.8 GB used; 5.3 GB available (35% used)
- Network: public IPv4 `51.158.171.222/32`
- Binance Futures `/fapi/v1/time`: HTTP response contained `serverTime=1794544709931`
- Application process scan found no T0/T1/T2/Core Runner/Gunicorn/Uvicorn/Freqtrade process.
- Listening ports showed SSH and local DNS only; no application listener.
- Docker not installed.

## Python/build environment
- Python 3.12.3 at `/usr/bin/python3`; pip unavailable.
- `requests 2.31.0` present.
- NumPy, Pandas, CCXT, Flask, FastAPI, Pydantic and pytest not installed.
- Git 2.43.0 present; GCC absent.
- No packages installed and no build attempted.

## Repository source parity
- VPS checkout: `feature/core-operational-proof-20261112`
- VPS local HEAD: `4af5bf0536c8b45f59033f0bc38625a031621c3e`
- VPS reported status: `## feature/core-operational-proof-20261112...origin/feature/core-operational-proof-20261112` with no local modifications.
- GitHub branch HEAD independently fetched: `513cfedbe392ece46b1f26d5946d3092172bf9db`.
- The VPS checkout is behind the current GitHub branch tip. The reported local tracking status is not proof of freshness because the remote-tracking ref may be stale.
- No checkout update, fetch, pull, reset, or test execution was performed.

## T1 staging and integrity
- Staging path: `/home/ubuntu/t1/staging`.
- Contains runtime log/data directories, extracted binary, ELF identity, checksum manifest, config files and ZIP archive.
- Binary format: ELF 64-bit LSB PIE, ARM aarch64, dynamically linked, interpreter `/lib/ld-linux-aarch64.so.1`.
- BuildID: `719bc30a55ded5691d640edcb9380207eaff80ca`.
- Binary SHA-256: `6dc9b691700c464784b475d2da2ffdcbb4eae62169ee31e74d8e0fba51966469`.
- Manifest verification: `binance-futures-collector: OK`.
- Archive: `t1-arm64-9b2af66.zip`.
- Archive SHA-256: `a1fbb27bcdb7d47b223b3a85ed40bef0df2a2328a9ae3a0c4b735e3066a9e7b0`.
- Interpretation: binary architecture is correct for this host and binary matches its colocated manifest. Archive SHA has been measured but not compared with a trusted published digest. Exact producing source commit/workflow/artifact provenance is NOT VERIFIED.
- Files `ELF-IDENTITY.txt`, `SHA256SUMS`, and ZIP were root-owned mode 0640; read access was obtained with sudo. No permission or ownership changes were made.

## T0/T2 and runtime boundary
- Bounded search under `/home/ubuntu` found only the repository and `/home/ubuntu/t1`; no T0/T2 directories in searched paths.
- This does not establish global absence and does not imply T0 canonical data loss.
- No T0 database was opened or modified.
- No T1 binary execution, service start, systemd/autostart, dependency installation, build, Core Runner invocation, or order placement occurred.

## Gate disposition
| Gate | Status | Evidence |
|---|---|---|
| VPS ARM64 identity and Binance REST | PASS | Owner-pasted host/network output |
| Python/dependency inventory | PASS (inventory only) | Owner-pasted Python/package output |
| Dependency readiness | BLOCKED | pip and required packages absent |
| Bounded T0/T1/T2 inventory | PASS (bounded scope) | Owner-pasted directory/process/port output |
| T1 ELF architecture | PASS | `file` output |
| Binary-to-manifest checksum | PASS | `sha256sum -c SHA256SUMS` |
| Archive provenance | NOT VERIFIED | No trusted source digest or workflow binding |
| VPS Core Runner source parity | BLOCKED | VPS SHA differs from GitHub branch HEAD |
| Core Runner ARM64 compatibility | NOT VERIFIED | No runtime/build test |
| One-shot runtime | NOT AUTHORIZED / NOT RUN | No execution approval |

## Next steps and limits
1. Identify exact source commit and GitHub Actions workflow/artifact that produced `t1-arm64-9b2af66.zip`.
2. Compare the measured archive SHA-256 against the trusted published artifact digest.
3. Plan a bounded, read-only Core Runner source-parity check before any test proposal.
4. Keep T0 independent and untouched. No installation, binary execution, runtime activation, background service, systemd/autostart, Core Runner invocation, or live trading without separate explicit authorization.


## Addendum — exact T1 artifact provenance confirmed

The initial inventory marked archive provenance NOT VERIFIED because no trusted source binding had yet been retrieved. This is superseded by the following exact GitHub evidence:

- Source repository: `kenznguyen/binance-futures-collector`.
- Branch: `feature/t1-connection-sidecar-integration-20261107`.
- Source SHA: `9b2af66e68206898e51f638b67497d574a7252c4`.
- Source commit: `ci: add native ARM64 collector build artifact`.
- Push workflow run: `43334117748`, completed SUCCESS, head SHA exactly matches source SHA.
- Native ARM64 job: `131585840822`, SUCCESS (per the source evidence report).
- Artifact ID: `13996767785`.
- Artifact name: `t1-collector-linux-aarch64-9b2af66e68206898e51f638b67497d574a7252c4`.
- Artifact size: 3,985,895 bytes.
- GitHub artifact digest: `sha256:a1fbb27bcdb7d47b223b3a85ed40bef0df2a2328a9ae3a0c4b735e3066a9e7b0`.
- Artifact expiry: `2026-11-20T00:09:20Z`.
- Owner-measured VPS ZIP digest and size exactly match GitHub artifact metadata. Embedded binary checksum matches the archive manifest.

Updated disposition: T1 source/workflow/artifact provenance PASS; archive digest PASS; binary-to-manifest digest PASS; ELF AArch64 PASS.

### Historical runtime evidence clarification
The repository's `T1_ARM64_CI_ARTIFACT_VERIFICATION_2026-11-13.md` records a prior BTCUSDT-only manual foreground smoke lasting approximately 80–84 seconds, followed by SIGINT and graceful shutdown. It is historical bounded runtime evidence, not a persistent service. Overall runtime acceptance remains PARTIAL because the capture included a freshness rejection/resnapshot and exact root cause was NOT VERIFIED. T1→T2 remains BLOCKED. Current owner-pasted process scan found no T1 process running.

### Core checkout freshness
GitHub compare confirms VPS local SHA `4af5bf0536c8b45f59033f0bc38625a031621c3e` is an ancestor of the current branch and is 164 commits behind / 0 ahead at the latest recorded branch state. No tests or Core Runner runtime may be run from this stale checkout.


## Addendum — Core First source synchronization (2026-11-13)

- Approved operation: fetch + fast-forward only on existing branch `feature/core-operational-proof-20261112`. Initial SSH transport failed with `Permission denied (publickey)` and did not advance the checkout. Owner reran using the public GitHub HTTPS URL.
- Owner-reported result: `SYNC_RESULT=PASS`; branch `feature/core-operational-proof-20261112`; VPS HEAD `562362a69d8455a34e08385d26a47fa21d2b50ed`; working tree clean.
- Independent GitHub branch lookup: HEAD `562362a69d8455a34e08385d26a47fa21d2b50ed` — exact match.
- GitHub compare: tested Runner SHA `8f774d7103f54681497837c7e4fd7c2e1c38c754` to synchronized HEAD `562362a69d8455a34e08385d26a47fa21d2b50ed` = 4 commits ahead / 0 behind; merge base is the tested Runner SHA. The synced branch contains the CI-tested Runner source and four subsequent commits, including evidence/documentation updates.
- The shell prompt showed `[ahead 165]` against `origin/feature/core-operational-proof-20261112`. This is not divergence: the HTTPS fetch used an explicit URL and did not refresh the local `origin/*` tracking ref. GitHub confirms branch HEAD already equals VPS HEAD. No push is required or authorized.
- Status: source parity with GitHub branch PASS; inclusion of exact CI-tested Runner SHA PASS; clean VPS working tree PASS (owner-reported); local Runner file presence NOT VERIFIED; ARM64 build/runtime compatibility NOT VERIFIED; dependency readiness BLOCKED (pip and required packages absent in prior inventory); Runner execution NOT AUTHORIZED / NOT RUN.
- Core Runner CI evidence: run `43365609751`, tested SHA `8f774d7103f54681497837c7e4fd7c2e1c38c754`, artifact ID `14010098776`, artifact SHA-256 `008a574ce79cb8ba4637f5b49ade49d95d6087e5e6ad2df408b2a7d3d183026b`.
- No dependency installation, build, test execution, Runner invocation, service start, systemd/autostart, T0/T1/T2 mutation, or live order occurred. T1 runtime remains not activated; paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.
- Next: bounded read-only VPS checks for `core_runtime` presence and source ancestry. Do not install dependencies or execute Runner without separate explicit approval.
