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
