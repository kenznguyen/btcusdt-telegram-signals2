# Core-First Paper-Only Packaging Assessment and Runtime Evidence Acquisition

Date: 2026-11-12
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/core-operational-proof-20261112`
Code baseline: `755b6c4b783e873c5c9b023e4a4c0d8271a7748b`

## 1. Disposition

- Core-first code-level paper behavior: **PASS** (83/83 exact-SHA CI tests).
- Evidence artifact payload integrity: **PASS** (downloaded and independently SHA-256 verified).
- Packaging readiness: **CONDITIONAL / NOT YET A RELEASE PACKAGE**.
- Ephemeral CI process execution: **PASS** for the test suite only.
- Persistent application runtime: **NOT VERIFIED / BLOCKED**.
- VPS runtime: **NOT AVAILABLE**; the previous Scaleway VPS was deleted on 2026-11-11 and no replacement host is established in the current handoff.
- Production/live trading: **BLOCKED / OUT OF SCOPE**.

This assessment does not authorize deployment, provisioning, installation on a host, service restart, exchange connectivity, AI execution or real orders.

## 2. Packaging inspection

Repository inspection on the active branch found:
- No root `pyproject.toml`.
- No root `Dockerfile`.
- `requirements.txt` exists but contains broad version ranges, not a fully resolved/hash-locked release dependency set.
- `requirements-web.txt` is used by the operational-proof CI workflow as an isolated test dependency input; that workflow is not a packaging workflow.
- `paper_execution/__init__.py` describes the package as paper execution only and exposes `PaperLedger` and `read_snapshot`. It states there is no exchange order endpoint in this package.
- Root `app.py` exposes dashboard and T0 feeder health endpoints. It is not a Core paper-execution daemon or a packaged Core runtime entrypoint.
- README explicitly says the 5-layer architecture is a target design and fixture tests do not prove runtime, model or frontend operation.

Consequently, a source checkout plus passing tests is not yet a versioned, reproducible, installable paper-only release package. A package must not be labelled production-ready or runtime-ready.

### Required packaging gates

1. Define the supported execution shape: library/CLI/worker and its explicit start/stop lifecycle. Do not misrepresent the existing T0 health Flask app as a Core execution service.
2. Add a reproducible dependency lock with exact versions and hashes, or another approved reproducible build mechanism.
3. Build an immutable release bundle containing only required source/config/docs, with exact source SHA, dependency manifest, build metadata and SHA-256 manifest.
4. Verify package contents exclude exchange execution credentials and any live order path; verify AI remains disabled.
5. Install/run the package in a clean isolated environment using disposable SQLite only.
6. Publish the package as a paper-only release candidate only after exact-SHA tests, package integrity and clean-environment smoke tests pass.

## 3. Independent artifact verification

GitHub Actions run: `43232993104`
Run URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43232993104

- Exact tested source SHA: `755b6c4b783e873c5c9b023e4a4c0d8271a7748b`
- Job: `operational-proof`, SUCCESS.
- Artifact: `core-first-code-operational-proof-43232993104`
- Artifact ID: `13951366739`
- Downloaded ZIP size: 4,026 bytes.
- GitHub artifact digest: `sha256:7d0fec151bc96f36e71d228c3c790e4f41ff48870b59d982a047f1be7ae35f49`.
- Independently calculated downloaded ZIP SHA-256: `7d0fec151bc96f36e71d228c3c790e4f41ff48870b59d982a047f1be7ae35f49` — MATCH.
- ZIP integrity and archive listing: PASS.
- Artifact contains 8 evidence files; embedded source SHA matches the tested SHA.
- Logs independently report 4/4 live-data probe contracts, 12/12 Core/signal regressions, 39/39 Core operational tests and 28/28 shared-risk/paper-ledger tests: **83/83 PASS**.
- Safety markers: `AI_EXECUTION_ENABLED=false`, `CANONICAL_T0_TOUCHED=false`, `EXCHANGE_CREDENTIALS_USED=false`, `REAL_ORDERS_SENT=false`, `VPS_OR_PERSISTENT_RUNTIME_USED=false`.
- Workflow verdicts: Core ENTRY, DCA, margin budget, LONG lifecycle, SHORT lifecycle, mixed-writer stress and repeated mixed-writer stress all PASS.

This closes the previous artifact-payload checksum gap. It does not convert the CI run into persistent runtime evidence.

## 4. Runtime evidence inventory

| Evidence class | Current status | What it proves |
|---|---|---|
| Compile on GitHub runner | PASS | Selected modules compile on ephemeral Ubuntu/Python 3.12 |
| Disposable SQLite lifecycle | PASS | Core paper ENTRY/DCA/EXIT, PnL, fees, equity and Kill Switch work in test fixtures |
| Contention/retry tests | PASS within tested fixture bounds | Tested concurrent writers serialize and preserve tested invariants |
| CI artifact provenance | PASS | Exact source SHA and evidence payload integrity |
| Clean package installation | NOT VERIFIED | No release package exists yet |
| Core application startup as a long-running process | NOT VERIFIED | Current workflow runs tests, not a Core service |
| Persistent SQLite runtime across process restart | NOT VERIFIED | CI fixtures do not establish a durable runtime service |
| Runtime health/metrics/log rotation | NOT VERIFIED | No Core runtime instance has been measured |
| Host reboot/power loss/filesystem fault recovery | NOT VERIFIED | No currently available authorized host |
| VPS runtime | BLOCKED | Former VPS deleted; no replacement host in handoff |

Important distinction: the CI workflow itself explicitly records `VPS_OR_PERSISTENT_RUNTIME_USED=false`. The 83 tests are valid code-level/fixture execution evidence, not VPS or continuous-operation evidence.

## 5. Runtime collection plan — bounded and non-destructive

### R0 — Local/ephemeral package smoke
Status: **NOT STARTED**; follows packaging gates.

- Build and install the exact package in a clean isolated environment.
- Use a temporary directory and disposable SQLite database.
- Keep AI disabled; no exchange credentials, exchange order API, T0 canonical database or T1/T2 runtime.
- Capture source SHA, package SHA-256, dependency versions, OS/Python versions, startup/shutdown timestamps, exit codes and test output.
- Verify database integrity and expected paper ledger state after clean shutdown.

### R1 — Process restart persistence
Status: **NOT STARTED**.

- Start the paper worker in an isolated test environment.
- Create deterministic paper-only state, stop gracefully, restart, and verify ledger/equity/Kill Switch state.
- Separately test forced process termination and recovery against disposable state.
- No systemd/autostart or host-level persistence changes.

### R2 — Bounded duration/health observation
Status: **NOT STARTED**.

- Observe the same isolated runtime for a pre-approved finite interval.
- Record process liveness, readiness, DB integrity, ledger consistency, CPU/RAM/disk, logs and error counts.
- Include a bounded mixed-writer workload and ensure Kill Switch remains effective.
- No external market feed or exchange connection required for the initial runtime gate.

### R3 — Host runtime
Status: **BLOCKED pending a separately approved replacement environment and bounded host scope**.

The old Scaleway host was deleted. Do not attempt SSH, provision a new VPS, install dependencies, restart services or configure autostart under this report. Once an environment is separately authorized, capture host identity/specification, exact deployed source/package digest, config provenance, process/service state, health checks, DB integrity, logs, resource metrics, controlled restart and recovery evidence. T0 canonical data and T1/T2 remain outside scope.

## 6. Immediate next steps

1. Define the Core paper runtime entrypoint and package contract (without changing Core signal/risk behavior).
2. Add reproducible dependency/build metadata and package verification tests.
3. Produce and independently verify the first paper-only release candidate bundle.
4. Run R0 and R1 in disposable isolated environments.
5. Only then seek separate approval for bounded R2/R3 runtime measurement.

## 7. Guardrails

- Preserve Core RSI + ADX + Smart DCA.
- Keep `AI_EXECUTION_ENABLED=false`.
- Paper-only; no real orders or live trading.
- No exchange execution credentials or exchange order endpoints.
- No canonical T0 mutation; no T1 activation or T2 runtime changes.
- No VPS provisioning, remote access, service restart, package installation on a persistent host or systemd/autostart without separate explicit approval.
- Keep every result tied to exact source SHA, workflow run, artifact ID and digest.
- Update the same active branch handoff after each meaningful increment.
