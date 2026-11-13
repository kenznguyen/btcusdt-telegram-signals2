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


## Addendum — Core Runner read-only VPS preflight (2026-11-13)

- Owner-provided output confirms checkout branch `feature/core-operational-proof-20261112`, HEAD `562362a69d8455a34e08385d26a47fa21d2b50ed`, and `TESTED_SOURCE_ANCESTRY=PASS` for CI-tested Runner source `8f774d7103f54681497837c7e4fd7c2e1c38c754`.
- File-presence checks passed for `core_runtime/__init__.py`, `core_runtime/__main__.py`, `core_runtime/one_shot.py`, and `core_runtime/preflight.py`; output: `RUNNER_FILES=PRESENT`.
- Execution boundary: `NO_INSTALL=YES`, `NO_BUILD=YES`, `NO_TEST=YES`, `NO_RUNNER_EXECUTION=YES`.
- Status: synchronized source parity PASS; tested-source ancestry PASS; Runner file presence PASS (owner-reported read-only check); dependency readiness remains BLOCKED from prior inventory (pip and required packages absent); ARM64 build/runtime compatibility NOT VERIFIED; one-shot runtime NOT AUTHORIZED / NOT RUN.
- Prompt `[ahead 165]` is stale local remote-tracking metadata; explicit HTTPS fetch did not update `origin/*`. GitHub branch HEAD and VPS HEAD match. No push is needed.
- No dependency installation, build, tests, Runner invocation, service activation, T0/T1/T2 mutation, or trading occurred.
- Next: prepare a bounded ARM64 compatibility/dependency plan for owner review. Execution requires separate explicit approval; preserve paper-only posture and `AI_EXECUTION_ENABLED=false`.


## Addendum — Core Runner ARM64 dependency static assessment (2026-11-13)

### Repository and source scope
- Active branch: `feature/core-operational-proof-20261112`; branch HEAD at assessment start: `fa02bffea4b1070e9ad203900f0fc7c45bef96b1` (GitHub compare confirms identical).
- Read-only inspected root `requirements.txt` and Core Runner decision-path modules: `core_runtime/{__main__,preflight,one_shot,input_bundle,adapter,orderbook_contract}.py`; `pipeline/{core_strategy,core_signal,values}.py`; `paper_execution/{ledger,risk_control,equity,account_history,replay_inputs,funding}.py`; `risk_policy.py`.
- Static import graph identifies `rfc8785` as the only third-party import in the inspected Core Runner path. Declared requirement: `rfc8785>=0.1.4,<0.2`. Remaining inspected imports are standard-library or project-local.
- The root requirements file is application-wide and additionally declares `requests>=2.32,<3`, `numpy>=1.26,<3`, `pandas>=2.2,<3`, `Flask>=3,<4`, `gunicorn>=22,<24`, and `cryptography>=42,<47`. These were not identified in the inspected one-shot Core Runner import path. Do not install the entire root requirements set for this bounded Runner assessment.
- No root `pyproject.toml` or `setup.cfg` was found; no dedicated locked Runner requirements manifest was established.

### ARM64/Python compatibility evidence
- PyPI metadata for `rfc8785 0.1.4` identifies it as pure Python, dependency-free, with universal wheel `rfc8785-0.1.4-py3-none-any.whl`; its Python requirement is >=3.8. This is compatible by declared tags with CPython 3.12 on aarch64 in principle. Sources: https://pypi.org/project/rfc8785/ and https://simple-repository.app.cern.ch/project/rfc8785.
- Host inventory (not re-probed): Ubuntu 24.04.5, CPython 3.12.3, aarch64, 2 vCPU, 3.8 GiB RAM, 5.3 GB free root disk; pip and GCC absent.
- This is a static dependency and metadata assessment only. It does not prove successful package resolution, import, runtime behavior, or end-to-end ARM64 compatibility.

### Gate status and limits
| Gate | Status |
|---|---|
| Core Runner static dependency scope | PASS (source-inspection level) |
| rfc8785 universal wheel/Python declaration | CONDITIONAL PASS (metadata only) |
| Host package resolution | NOT VERIFIED |
| Runtime import/test/build | NOT RUN |
| Dependency installation | NOT AUTHORIZED |
| Core Runner invocation/service activation | NOT AUTHORIZED / NOT RUN |

Next proposed step: isolated no-install resolver/wheel-availability check for the minimal Core Runner dependency only, after verifying a safe pip invocation path. Do not bootstrap pip, install packages, create a persistent environment, build, test, invoke Runner, or activate services without separate explicit approval. T0/T1/T2 and paper-only boundaries remain unchanged.


## Addendum — VPS ARM64 Core Runner venv preparation (2026-11-13)

- Owner approved a bounded host-preparation step: install python3-venv, create an isolated Core Runner virtual environment, verify pip, and check availability of the minimal rfc8785 wheel without installing it.
- APT installed python3-venv 3.12.3-0ubuntu2.1 (arm64). APT reported no service/container restarts required and no outdated user sessions; 46 unrelated package upgrades were left untouched.
- Created /home/ubuntu/.venvs/btcusdt-core-runtime. Verified Python 3.12.3, pip 24.0 from that venv, its Python executable path, and aarch64 architecture.
- pip download --no-deps --only-binary=:all: rfc8785==0.1.4 succeeded. Wheel: /tmp/core-runtime-dependency-check/rfc8785-0.1.4-py3-none-any.whl; 9,240 bytes; SHA-256 520d690b448ecf0703691c76e1a34a24ddcd4fc5bc41d589cb7c58ec651bcd48.
- rfc8785 was downloaded but NOT installed. No import verification, tests, build, Core Runner execution, service activation, or trading occurred. T0/T1/T2 were not changed.
- Source SHA before/after: 562362a69d8455a34e08385d26a47fa21d2b50ed. Owner-reported Git working tree clean. Local prompt still reports [ahead 165] due to stale origin/* tracking metadata; this is not branch divergence and no push was needed.
- Gate status: host venv support install PASS; isolated venv and pip PASS; wheel download/resolution PASS; package install/import NOT DONE/NOT VERIFIED; project tests/build/runtime NOT VERIFIED; Runner NOT AUTHORIZED / NOT RUN.
- Next gate requires separate approval to install only rfc8785==0.1.4 into the isolated venv and verify import. Tests/build and Runner invocation remain separate approval gates. Maintain paper-only posture and AI_EXECUTION_ENABLED=false.


## Addendum — isolated Core Runner dependency installation and import (2026-11-13)

- Owner-approved scope: install only `rfc8785==0.1.4` into `/home/ubuntu/.venvs/btcusdt-core-runtime`, then verify import and package version.
- Local wheel SHA-256 expected/actual: `520d690b448ecf0703691c76e1a34a24ddcd4fc5bc41d589cb7c58ec651bcd48` — PASS.
- Installed from the local wheel using `--no-index --no-deps`; pip reported `Successfully installed rfc8785-0.1.4`.
- Verified interpreter: `/home/ubuntu/.venvs/btcusdt-core-runtime/bin/python`; Python 3.12.3; `platform.machine()=aarch64`; package version `0.1.4`; import PASS.
- `pip list`: `pip 24.0`, `rfc8785 0.1.4`; no other package installed in this venv.
- Repository HEAD remained `562362a69d8455a34e08385d26a47fa21d2b50ed`; owner-provided output reports no working-tree modifications. Prompt `[ahead 165]` remains stale remote-tracking metadata, not evidence of branch divergence.
- Updated gate status: Python venv support and isolated venv PASS; wheel resolution and checksum PASS; minimal dependency install/import PASS; project tests/build and ARM64 end-to-end runtime NOT VERIFIED; Core Runner invocation NOT AUTHORIZED / NOT RUN.
- No tests, build, Runner execution, service activation, T0/T1/T2 modification, or trading occurred.
- Next step requires a separate explicit approval for bounded Core Runner tests. This dependency-install approval does not authorize tests or execution.


## Addendum — bounded Core Runner ARM64 VPS test batch (2026-11-13)

### Scope and exact source
- Owner explicitly approved the bounded Core Runner test batch; this did not authorize standalone Runner invocation or service activation.
- VPS repository: `/home/ubuntu/btcusdt-telegram-signals2`; branch `feature/core-operational-proof-20261112`.
- Exact source SHA reported before/after: `562362a69d8455a34e08385d26a47fa21d2b50ed`; final `git status --short` output was empty.
- Environment: dedicated venv `/home/ubuntu/.venvs/btcusdt-core-runtime`; Python 3.12.3; aarch64; `rfc8785==0.1.4`; `AI_EXECUTION_ENABLED=false`.

### Test evidence (owner-provided VPS logs)
| Test group | Command/module scope | Tests | Result | Log |
|---|---|---:|---|---|
| Core CLI contract | `pipeline.test_core_runtime_contract` | 5 | PASS | `/tmp/core-cli-tests.log` |
| One-shot Runner contract | `pipeline.test_core_runtime_one_shot` | 11 | PASS | `/tmp/core-one-shot-tests.log` |
| Input Bundle v1 | `core_runtime.test_input_bundle_contract` | 19 | PASS | `/tmp/core-bundle-tests.log` |
| Producer adapter | `pipeline.test_core_runtime_adapter_contract` | 6 | PASS | `/tmp/core-adapter-tests.log` |
| Core paper operational + short lifecycle | `paper_execution.test_core_first_operational`, `paper_execution.test_core_short_lifecycle` | 41 | PASS | `/tmp/core-operational-tests.log` |
| **Total** | | **82** | **PASS** | |

- All five logs report `Ran N tests` followed by `OK`; operational group: 41 tests in 93.335s.
- Final shell markers: `AI_EXECUTION_ENABLED=false`, `CORE_TEST_BATCH=COMPLETED`, `SOURCE_UNCHANGED=PASS`.

### Disposition and limitations
- Bounded VPS test batch: **PASS (82/82)**.
- Exact source guard and clean worktree: **PASS (owner-provided)**.
- This is manual VPS test evidence, not a GitHub Actions run; no workflow run or artifact ID is claimed for this batch.
- It does not prove standalone one-shot runtime operation, persistent process/service behavior, deployment readiness, or live-trading readiness.
- No standalone `python -m core_runtime ... --run-once`, service/autostart, T0/T1/T2 mutation, exchange execution, or real orders were performed in this scope. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain in force.
- Next gate: separate explicit approval is required before standalone one-shot Runner invocation. Until then: **NOT AUTHORIZED / NOT RUN**.
