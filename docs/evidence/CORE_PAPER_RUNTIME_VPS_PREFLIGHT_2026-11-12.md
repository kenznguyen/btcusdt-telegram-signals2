# VPS Runtime Preflight — 2026-11-12

## Scope
Record owner-provided, read-only host inspection output for the newly created Scaleway VPS. No remote commands were executed by the assistant. The owner connected over SSH and supplied the command output.

## Host evidence
- Public endpoint supplied by owner: `51.158.171.222`.
- Hostname: `scw-optimistic-jang`.
- OS: Ubuntu 24.04.5 LTS (Noble).
- Kernel: `6.8.0-147-generic`.
- Architecture: `arm64` / `aarch64`.
- CPU: 2 vCPU.
- Memory: 3.8 GiB total; 3.5 GiB available at observation.
- Swap: 0.
- Disk: `/dev/sda` 9.3G; root partition `/dev/sda1` 8.3G, 5.8G available at observation; separate boot and EFI partitions.
- Python: 3.12.3.

## Commands reported by owner
Read-only commands:
```bash
hostname
uname -a
nproc
free -h
df -h
cat /etc/os-release
dpkg --print-architecture
python3 --version
python3 -c "import platform; print(platform.machine())"
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT
```

## Repository dependency inspection
Inspected the active branch dependency declarations only; no package installation was performed:
- `requirements.txt` blob `f5c242bdac51eba200b19233e08e7d4b22f598c4`: requests, numpy, pandas, Flask, gunicorn, cryptography, rfc8785.
- `requirements-ci.txt` blob `1910948f82d7b228755552cd3f5b343cebbca412`: PyYAML.
- `requirements-market-data.txt` blob `0c1b47046bc264be48fa9e11360ce3488046530d`: ccxt, psycopg[binary].
- `requirements-web.txt` blob `1ee5316a56713357a8008da7e5423af69e2e9b9b`: Flask, requests, gunicorn, cryptography, rfc8785.
- The inspected files use version ranges, not a complete hash-locked dependency set.
- Static declarations do not pin an x86-only package or binary, but this is not proof that all transitive packages provide compatible ARM64/Python 3.12 wheels or that the runtime works on ARM64.

## Assessment
- SSH access and root shell: PASS (owner-provided observation).
- Ubuntu 24.04 LTS: PASS.
- Requested 2 vCPU / 4 GB RAM class: PASS (observed 2 vCPU and 3.8 GiB reported RAM).
- ARM64 dependency compatibility: **NOT VERIFIED**. No install, wheel resolution, import smoke test or runtime test has been performed. Do not install dependencies or launch runtime until a disposable, reproducible compatibility check is approved and completed.
- Storage target: PARTIAL / NOT MATCHED. Physical disk reports 9.3G and root partition 8.3G, rather than the earlier 10 GB target. 5.8G was available at observation.
- Swap: absent; no change requested or made.
- Core runtime entrypoint: still DESIGN RECORDED / NOT IMPLEMENTED / NOT TESTED. This host preflight does not resolve the missing runnable Core entrypoint.

## Restrictions and non-actions
- No packages installed or upgraded.
- No firewall, SSH, user, service, swap, disk, or system configuration changed.
- No application code deployed and no Core process started.
- No database opened or changed; canonical T0 remains untouched.
- No exchange credentials, exchange endpoints, or real orders used.
- `AI_EXECUTION_ENABLED=false`; AI/T1/T2 remain inactive; no systemd/autostart.
- Do not substitute `app.py` or `python -m paper_execution` for a Core decision runner.

## Status
**PREFLIGHT: PARTIAL PASS — HOST IDENTIFIED; BASIC OS/RESOURCE EVIDENCE RECORDED; ARM64 DEPENDENCY COMPATIBILITY NOT VERIFIED; STORAGE TARGET NOT MATCHED.**
**CORE VPS RUNTIME: NOT STARTED.**

## Next bounded step
Define a disposable ARM64/Python 3.12 dependency-resolution and import-smoke procedure, with no application deployment and no canonical T0 access. Separately resolve whether the 9.3G disk capacity is acceptable or whether a volume expansion is needed. The Core one-shot runner must still be implemented and tested before any runtime launch. Any package installation on this persistent VPS requires a separate bounded approval; do not proceed implicitly.


## Public wheel-availability research (PyPI, 2026-11-12)
Checked published PyPI release metadata for representative native dependencies:
- NumPy 2.5.4 publishes CPython 3.12 Linux ARM64 wheels (including aarch64 manylinux/musllinux variants).
- pandas 3.1.1 publishes CPython 3.12 Linux ARM64 wheels (including aarch64 manylinux/musllinux variants). The project's current constraint is `pandas<3`, so this particular release is outside the allowed range; this confirms the ecosystem publishes ARM64 wheels but does not prove a permitted pandas 2.x candidate resolves.
- psycopg-binary 3.3.8 publishes CPython 3.12 manylinux ARM64 wheels and is within the declared `psycopg[binary]>=3.2,<4` range.
- cryptography's PyPI release metadata shows Linux ARM64 manylinux wheels for current abi3 builds. The project constraint is `cryptography<47`; the exact permitted version and wheel tag still need resolver confirmation.
- Flask, requests, gunicorn, rfc8785, ccxt and PyYAML are expected to be architecture-neutral at the Python package layer, but transitive dependency resolution and installation have not been tested here.

This is **public package-index evidence only**, not proof for the exact dependency set selected by pip on this Ubuntu host. No exact versions, wheel filenames, hashes, or transitive closure were locked for the project. No wheel was downloaded or installed on the VPS.

## Updated compatibility disposition
- Static source/dependency review: PARTIAL PASS; no declared x86_64-only requirement identified in inspected files.
- Public wheel availability: PARTIAL PASS; ARM64 CPython 3.12 wheels are published for key native packages, but the pandas version constraint and exact selected artifacts remain unresolved.
- Exact resolver dry-run on Ubuntu 24.04 / CPython 3.12 / aarch64: NOT RUN.
- Import smoke test and Core test suite on ARM64: NOT RUN.
- Python version parity: NOT VERIFIED; the inspected primary CI workflow pins Python 3.11 while the VPS has Python 3.12.3.
- Dependency reproducibility: NOT VERIFIED; no lockfile found in the inspected root paths.

Next safe technical test: run a no-install pip resolution/download dry-run in a temporary directory on the target host, with explicit cache/temp locations and a strict disk budget, then verify wheel tags and hashes. This still requires explicit owner approval because it performs network access and writes temporary/cache data on the persistent VPS. Do not run it implicitly.
