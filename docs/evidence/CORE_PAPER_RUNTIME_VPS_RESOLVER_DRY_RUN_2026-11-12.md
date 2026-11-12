# Core Paper Runtime VPS Resolver Dry-Run Evidence — 2026-11-12

## Scope

Record owner-supplied output from the explicitly approved, no-install pip resolver dry-run on the owner-created Scaleway VPS. This is dependency-resolution evidence only. No project package installation, import test, application execution, database access, service change, or runtime launch was performed.

## Source identity

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/core-operational-proof-20261112`
- VPS checkout HEAD observed before this gate: `3cb5eb7c7a22c8e841dd6832324b42ef5a4f60b2`
- Root requirements blob: `f5c242bdac51eba200b19233e08e7d4b22f598c4`
- Requirements scope: root `requirements.txt` only; no market-data, web, or CI requirements files included.

## Host and resolver environment

Owner-reported resolver report: `/tmp/btcquant-preflight/core-resolution.json`

- CPython: 3.12
- OS/platform: Linux
- Architecture: `aarch64`
- Kernel: `6.8.0-147-generic`
- Resolver exit status: `0`
- Report present: yes, 253 KB
- Selected distributions: 23
- pip invocation used `--dry-run` and `--only-binary=:all:`; no source build was requested.

## Resolved distributions

| Distribution | Version | Selected wheel |
|---|---:|---|
| blinker | 1.9.0 | `py3-none-any` |
| certifi | 2026.10.23 | `py3-none-any` |
| cffi | 2.1.1 | `cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64` |
| charset-normalizer | 3.5.2 | `cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64` |
| click | 8.5.1 | `py3-none-any` |
| cryptography | 46.0.7 | `cp311-abi3-manylinux_2_34_aarch64` |
| Flask | 3.1.3 | `py3-none-any` |
| gunicorn | 23.0.0 | `py3-none-any` |
| idna | 3.20 | `py3-none-any` |
| itsdangerous | 2.2.0 | `py3-none-any` |
| Jinja2 | 3.1.6 | `py3-none-any` |
| MarkupSafe | 3.0.4 | `cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64` |
| numpy | 2.5.4 | `cp312-cp312-manylinux_2_27_aarch64.manylinux_2_28_aarch64` |
| packaging | 26.3 | `py3-none-any` |
| pandas | 2.3.3 | `cp312-cp312-manylinux_2_24_aarch64.manylinux_2_28_aarch64` |
| pycparser | 3.12 | `py3-none-any` |
| python-dateutil | 4.0.0 | `py3-none-any` |
| pytz | 2026.6 | `py2.py3-none-any` |
| requests | 2.34.2 | `py3-none-any` |
| rfc8785 | 0.1.4 | `py3-none-any` |
| tzdata | 2026.6 | `py2.py3-none-any` |
| urllib3 | 2.8.0 | `py3-none-any` |
| Werkzeug | 3.1.9 | `py3-none-any` |

## Resource evidence

Owner-reported after resolver:

- Root filesystem: 8.0G total, 2.4G used, 5.7G available, 30% used.
- No disk pressure observed during this bounded resolver operation.

## Assessment

- Resolver command: **PASS** (exit status 0).
- Exact CPython 3.12 / Linux aarch64 resolution: **PASS**.
- Binary-wheel-only selection for all 23 resolved distributions: **PASS**.
- pandas 2.x constraint concern: **RESOLVED AT RESOLVER SELECTION LEVEL**; pandas 2.3.3 ARM64 CPython 3.12 wheel selected.
- Wheel download and independent SHA-256 capture: **NOT VERIFIED**. The report identifies selected filenames but does not prove the wheel bytes were downloaded or hashed.
- Installation/import/runtime compatibility: **NOT VERIFIED**.
- Core one-shot runtime entrypoint: **DESIGN RECORDED; NOT IMPLEMENTED; NOT TESTED**.
- Core VPS runtime: **NOT STARTED**.

A successful `pip install --dry-run` does not install distributions and does not prove importability, ABI/runtime behavior, application tests, or a runnable Core entrypoint.

## Non-actions and safety

- No project requirements were installed.
- No source code or system package was changed in this gate.
- No Core process, daemon, service, systemd unit, or autostart was launched/configured.
- No database was opened or changed; canonical T0 was not accessed.
- No exchange credentials, exchange endpoints, or real orders were used.
- `AI_EXECUTION_ENABLED=false`; AI/T1/T2 remain inactive.
- No cleanup, deletion, migration, or destructive storage operation was performed.

## Next gate — approval required

The next technically relevant check is a temporary-venv install/import smoke test for the root requirements, followed by the specifically scoped Core contract tests only after the runtime entrypoint implementation exists. This would install packages into the existing disposable venv on the persistent VPS and therefore requires separate explicit owner approval before execution.

Do not proceed with installation, import/test execution, Core implementation, or runtime launch on the basis of this resolver approval alone.

## Wheel download and SHA-256 evidence — 2026-11-12

### Scope and command outcome

Following separate owner approval, the exact 23 resolved distributions were downloaded as binary wheels into /tmp/btcquant-preflight/wheels/ using the versions from core-resolution.json, --no-deps, and --only-binary=:all:.

Owner-supplied command output:

- Download command exit status: 0 (pip reported Successfully downloaded all 23 distributions).
- Wheel files found: 23.
- Wheel directory size: 33M.
- Filesystem after download: 8.0G total, 2.5G used, 5.6G available, 31% used.
- Downloaded filenames and tags match the 23 distributions and wheel tags selected in the resolver section above.
- SHA-256 values below were calculated on the VPS with sha256sum.

### Downloaded wheel SHA-256 manifest

| Wheel | SHA-256 |
|---|---|
| blinker-1.9.0-py3-none-any.whl | ba0efaa9080b619ff2f3459d1d500c57bddea4a6b424b60a91141db6fd2f08bc |
| certifi-2026.10.23-py3-none-any.whl | e9b54de76e530bb6cf0ccd036787103acb58fd42ba930ea8bf948ddbaa2f61d1 |
| cffi-2.1.1-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.whl | 68e62fe11f30d5ca8289242866f0a5291402d8529ca2178ab8afc5c9694ae890 |
| charset_normalizer-3.5.2-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl | b91363207bd9dc966a691e959bb47f64b30f7ac4b072be9968b366982f7db77c |
| click-8.5.1-py3-none-any.whl | 8bb5376d2006950386f8c6427613334a2acadc5f559cb80e638d00b4df957e37 |
| cryptography-46.0.7-cp311-abi3-manylinux_2_34_aarch64.whl | 8a469028a86f12eb7d2fe97162d0634026d92a21f3ae0ac87ed1c4a447886c83 |
| flask-3.1.3-py3-none-any.whl | f4bcbefc124291925f1a26446da31a5178f9483862233b23c0c96a20701f670c |
| gunicorn-23.0.0-py3-none-any.whl | ec400d38950de4dfd418cff8328b2c8faed0edb0d517d3394e457c317908ca4d |
| idna-3.20-py3-none-any.whl | ab7ae7122974553370f0bdb919e1a960b2cd1bc1ef0276416d896db81c14582c |
| itsdangerous-2.2.0-py3-none-any.whl | c6242fc49e35958c8b15141343aa660db5fc54d4f13a1db01a3f5891b98700ef |
| jinja2-3.1.6-py3-none-any.whl | 85ece4451f492d0c13c5dd7c13a64681a86afae63a5f347908daf103ce6d2f67 |
| markupsafe-3.0.4-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl | 6a45c3d514f2436064db00d7fc8778d888f0236ebfed649b53d13a59e69ad51b |
| numpy-2.5.4-cp312-cp312-manylinux_2_27_aarch64.manylinux_2_28_aarch64.whl | fe4d21ab149f15e4e6043dfb0de87e6e5f34ac176cde83060e9802981fca2ac2 |
| packaging-26.3-py3-none-any.whl | d7193f7c8e4e93f444fde0262bf90af30e16fa0ad0ad44cb553c87339b23cd1c |
| pandas-2.3.3-cp312-cp312-manylinux_2_24_aarch64.manylinux_2_28_aarch64.whl | ecaf1e12bdc03c86ad4a7ea848d66c685cb6851d807a26aa245ca3d2017a1908 |
| pycparser-3.12-py3-none-any.whl | a076f3f489b39b43ed13563a1dafe42447445bec2e294154ec5c57fcdda4c85e |
| python_dateutil-4.0.0-py3-none-any.whl | a5e246f79eb80475e691bf93862cead98decd8a498cf53ba0516fcdc0f50dc1c |
| pytz-2026.6-py2.py3-none-any.whl | 7fed3fee8fd6bd4a2b7b75a8d56021d0624127bf69bd5691f115db929ac570b3 |
| requests-2.34.2-py3-none-any.whl | 2a0d60c172f83ac6ab31e4554906c0f3b3588d37b5cb939b1c061f4907e278e0 |
| rfc8785-0.1.4-py3-none-any.whl | 520d690b448ecf0703691c76e1a34a24ddcd4fc5bc41d589cb7c58ec651bcd48 |
| tzdata-2026.6-py2.py3-none-any.whl | 0a10eec6e13ef16b627fabed9a5f2ba61a62b1c67f327305f4e7e412a70b4aec |
| urllib3-2.8.0-py3-none-any.whl | 0cf3cae568d36aa9576b28dfb35f11328f1cb974ca7647d9475ebb86c75ac6e3 |
| werkzeug-3.1.9-py3-none-any.whl | 6392e50c78460ba618e5b21f08a71f59c99ce99cdc6cf6e3dd7e6ccca8754fab |

### Updated assessment

- Exact wheel download for all resolver-selected packages: PASS.
- Wheel count and filename/version/tag correspondence: PASS.
- SHA-256 fingerprint capture for all 23 downloaded files: PASS.
- Comparison against publisher/PyPI independently published hashes: NOT VERIFIED; captured values are local artifact fingerprints only.
- Installation, importability, application tests, and runtime compatibility: NOT VERIFIED.
- No package installation, import test, Core launch, database access, or service change was included in this gate.

### Next gate — approval required

Request separate explicit approval before installing these wheels into /tmp/btcquant-preflight-venv and running a bounded import smoke test. Use the local wheel directory with --no-index and --find-links so the tested package bytes are exactly those fingerprinted above. Do not install into system Python. Do not launch Core or activate services.
## Temporary venv installation evidence — 2026-11-12

Owner supplied pip output confirms installation of all 23 distributions into /tmp/btcquant-preflight-venv using:

    python -m pip install --no-index --find-links=/tmp/btcquant-preflight/wheels -r requirements.txt

- pip used only the local wheel directory; no package index access was requested.
- All 23 resolved distributions were installed successfully; pip ended with Successfully installed and no reported error.
- Installation target was the disposable /tmp/btcquant-preflight-venv, not system Python.
- Source build was not requested; pip processed the previously downloaded wheel files.
- Package installation: PASS.
- Import smoke test: NOT VERIFIED.
- Application tests and runtime compatibility: NOT VERIFIED.
- Core runtime: DESIGN RECORDED; NOT IMPLEMENTED; NOT TESTED; NOT STARTED.

### Non-actions

No Core command, service, daemon, database, T0/T1/T2 component, exchange endpoint, or real order was activated by this installation step. No source code was changed.

### Next gate

Run a bounded import/version smoke test only in /tmp/btcquant-preflight-venv. Do not launch application entrypoints, services, Core runtime, or access databases/exchanges.
## Temporary venv import smoke test — 2026-11-12

Owner supplied output from a bounded import/version check executed with /tmp/btcquant-preflight-venv/bin/python:

- Runtime: CPython 3.12.3; executable resolved to /tmp/btcquant-preflight-venv/bin/python.
- requests: 2.34.2 — imported.
- numpy: 2.5.4 — imported.
- pandas: 2.3.3 — imported.
- Flask: 3.1.3 — imported.
- gunicorn: 23.0.0 — imported.
- cryptography: 46.0.7 — imported.
- rfc8785: 0.1.4 — imported.
- Final marker: IMPORT_SMOKE_TEST: PASS.
- A DeprecationWarning was emitted when reading Flask __version__; import succeeded and the warning is not an import failure. Future version reporting should prefer importlib.metadata.version('flask').

### Updated assessment

- Root requirements resolver: PASS.
- Download of 23 exact resolved wheels: PASS.
- Local SHA-256 fingerprint capture: PASS; independent publisher hash comparison remains NOT VERIFIED.
- Temporary venv installation from local wheels: PASS.
- Seven-package import/version smoke test: PASS.
- Full application test suite on this VPS: NOT RUN.
- Runtime entrypoint implementation: NOT IMPLEMENTED.
- Core runtime launch: NOT STARTED.

### Non-actions and safety

No app.py, Gunicorn server, Core entrypoint, daemon, service, or systemd/autostart was launched. No database was opened; canonical T0 was not accessed. No exchange connection, credential, or real order was used. No source code or system Python package was changed by this check.

### Next gate — separate approval required

Before any broader test, inspect and select a strictly bounded set of offline Core contract tests that cannot open persistent databases, write outside disposable test fixtures, activate services, or access exchanges. The Core runtime entrypoint remains design-only, so a successful import smoke test must not be represented as Core runtime readiness.
## Bounded offline Core test selection — 2026-11-12

Repository inspection was performed at branch HEAD `551ad5a2f3fa6dc96d418053168aa02e8593ddcb`. No tests were executed in this selection step.

### Selected small, no-I/O contract tests

1. `python -m unittest pipeline.test_core_signal -v` — 6 tests; source blob `a946716604e2e1a74b0e32f0aae5d07b820f2cbf`. Covers Core LONG/SHORT normalization, FLAT, WAIT, stale/missing artifact, market/source/direction validation. Imports only `unittest` and the pure `pipeline.core_signal.validate` adapter.
2. `python -m unittest pipeline.test_core_strategy -v` — 6 tests; test blob `a0d5b46845d3fde006ed817fe21bdd8b6546c1d1`; producer blob `f714b6b6dc0822400b6997feb0a8c2f07886aaed`. Covers RSI/ADX indicators, incomplete-window rejection, missing-book WAIT, LONG entry, Smart DCA, and protective exits. Test module imports only `unittest` and `pipeline.core_strategy`; inspection found no SQLite, file, network, subprocess, or multiprocessing operations in this test module. Producer reads strategy threshold environment variables at import time; run with a clean/minimal environment to avoid inherited overrides.

Selected total: 12 small tests. These tests exercise signal and strategy logic only; they do not prove account-wide risk admission, PaperLedger persistence, kill-switch behavior, or the one-shot runtime.

### Explicitly excluded from this first bounded run

- `pipeline/test_core_sizing.py`: imports `tempfile` and `PaperLedger`, creates disposable SQLite state; defer to a separately reviewed DB-fixture gate.
- `paper_execution/test_core_first_operational.py`: 1,858 lines; creates multiple SQLite ledgers, performs account cutover/funding setup, uses multiprocessing and concurrency/crash probes. Do not run as part of the small no-I/O gate.
- `paper_execution/test_core_short_lifecycle.py`: builds on the large operational fixture and mutates disposable ledger state; defer.
- `paper_execution/test_ledger.py`, `test_risk_control.py`, and dual-ledger suites: SQLite persistence/migration/risk-state tests; defer until a specific disposable-DB boundary and exact test selection are approved.
- Full test discovery or full suite: not selected.

### Preconditions before executing the selected tests on the VPS

- First verify the VPS checkout's `git rev-parse HEAD` equals `551ad5a2f3fa6dc96d418053168aa02e8593ddcb`, and inspect `git status --short --branch`. Do not run tests against an unknown or stale checkout.
- Execute only the two named unittest modules with the disposable venv interpreter and a clean environment. No pytest discovery, no wildcard test selection, no app/CLI/service invocation.
- Preserve `AI_EXECUTION_ENABLED=false`; these pure tests must not access exchange endpoints or create real orders.
- This selection authorizes inspection/selection only. Test execution is NOT RUN pending exact checkout confirmation and a separate execution approval.

### Current gate disposition

- Test selection review: PASS.
- Selected tests execution: NOT RUN.
- Database/risk/ledger contract tests: DEFERRED.
- Core one-shot runtime implementation: NOT IMPLEMENTED.
- Runtime/VPS readiness: NOT VERIFIED.

## Bounded offline Core contract test execution — 2026-11-12

### Scope and source identity

Following separate owner approval, the two previously selected unittest modules were executed on the owner-operated VPS using the disposable interpreter:

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/core-operational-proof-20261112`
- Source HEAD at the approved pre-run synchronization gate: `4af5bf0536c8b45f59033f0bc38625a031621c3e`
- Interpreter: `/tmp/btcquant-preflight-venv/bin/python`
- Environment: clean `env -i`, `PYTHONPATH=.`, `PYTHONNOUSERSITE=1`, `AI_EXECUTION_ENABLED=false`
- Exact command target: `python -m unittest pipeline.test_core_signal pipeline.test_core_strategy -v`
- No test discovery, wildcard selection, or broader suite was invoked.

### Owner-supplied execution result

- `pipeline.test_core_signal`: 6 tests passed.
- `pipeline.test_core_strategy`: 6 tests passed.
- Total: 12 tests.
- Runtime: 0.050 seconds.
- unittest summary: `Ran 12 tests in 0.050s`; `OK`.
- Shell exit code: `0`.
- Failures: 0.
- Errors: 0.

The passing cases cover LONG/SHORT signal normalization, FLAT/WAIT handling, source/market/direction validation, stale or missing Core artifacts, finite RSI/ADX/DI after warmup, incomplete market-window rejection, Smart DCA intent using fresh account budget, protective exit priority, valid LONG entry, and WAIT when the execution book is missing.

### Gate assessment

- Bounded Core signal contract tests: **PASS (6/6)**.
- Bounded Core strategy tests: **PASS (6/6)**.
- Combined selected offline tests: **PASS (12/12)**.
- Root dependency resolver, wheel download/fingerprinting, temporary venv installation, and import smoke test: **PASS** as recorded above.
- Account-wide shared-risk admission, kill-switch behavior, PaperLedger persistence/migrations, and Core end-to-end paper execution: **NOT VERIFIED** by these 12 tests.
- Core one-shot runtime entrypoint: **DESIGN RECORDED; NOT IMPLEMENTED; NOT TESTED**.
- Core VPS runtime: **NOT STARTED**.
- AI strategy/runtime: **NOT TESTED; INACTIVE**.

### Safety and non-actions

The approved scope was limited to the two pure unittest modules. No application server, Core runner, daemon, service, systemd/autostart, or exchange connection was started. No database was intentionally opened by the selected test modules; canonical T0 was not accessed. No exchange credentials or real orders were used. No source code was modified by this test run.

### Next gate and restrictions

The next possible gate is a separately scoped review and approval of disposable SQLite-backed sizing/ledger/shared-risk tests. Before that gate, define and verify the exact disposable database path and prove it cannot alias canonical T0. Do not run broad operational/concurrency suites, implement or launch the Core runtime, access canonical T0, activate AI, or enable live execution without separate explicit approval.
