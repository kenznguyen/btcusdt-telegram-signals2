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
