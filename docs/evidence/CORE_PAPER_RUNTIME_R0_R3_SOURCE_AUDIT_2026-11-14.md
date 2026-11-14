# Core Paper Runtime R0–R3 Source Audit — 2026-11-14

## Scope and source identity

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Active branch: `feature/core-operational-proof-20261112`
- Audited GitHub HEAD: `c5903f2165bc8315ecbf9ba956de193e00d1ff76`
- VPS owner-reported checkout SHA: `9aac55b60bec0180cf639086139fc95bf4dabd32`
- GitHub compare: VPS SHA is 43 commits behind this HEAD, 0 ahead; the compare includes Core runtime and workflow changes. Source parity is therefore BLOCKED.
- Core G2–G6 tested code SHA: `34066f4f1d3781c3acc8d597dfcf0cb305882000`; current HEAD is 2 commits ahead, 0 behind, with only `docs/PROJECT_SESSION_HANDOFF.md` and `docs/evidence/CORE_RUNNER_HARDENING_G2_G6_2026-11-14.md` changed. G2–G6 CI evidence remains applicable to code at the tested SHA.
- This was a GitHub source/document review only. No VPS command, test execution, config creation, database access, source change, T0 access, or runtime action occurred.

## Findings

### R0 — Source identity and parity

**Disposition: PASS for GitHub source identification; BLOCKED for VPS parity.**

The branch ref resolves to the exact HEAD above. The VPS-reported SHA is an ancestor, 43 commits behind, with changes to `core_runtime/__main__.py`, `core_runtime/one_shot.py`, `core_runtime/preflight.py`, Core workflow files and tests among the compare results. Do not run a GitHub-HEAD CLI on the older VPS checkout or infer feature availability from the repository branch name.

### R1 — PAPER configuration contract

**Disposition: SOURCE CONTRACT PASS; DEPLOYMENT CONFIG NOT VERIFIED.**

`core_runtime/preflight.py::_load_config` accepts exactly one of two JSON key sets:

- Base: `mode`, `ai_execution_enabled`, `ledger_path`.
- Runner: the base set plus `risk_limits`, `max_book_age_ms`, `max_position_base`.

It requires `mode == "PAPER"`, JSON boolean `ai_execution_enabled == false`, and a non-empty explicit ledger path. Relative ledger paths resolve against the config file's parent. Unknown/missing keys fail closed.

The GitHub tree contains no dedicated Core PAPER deployment config/template. `freqai_bridge/config.research.json` is not a Core Runner config. The VPS path/environment diagnostics supplied by the owner did not identify a Core PAPER config or PAPER-related environment variable names.

### R2 — Credentials and execution boundary

**Disposition: SOURCE CONTRACT PASS WITH BOUNDARY LIMITS; VPS CONFIG NOT VERIFIED.**

Core preflight and bootstrap reject non-empty values for `BINANCE_API_KEY`, `BINANCE_API_SECRET`, `OKX_API_KEY`, and `OKX_API_SECRET`. Runner configuration requires PAPER mode and AI disabled; the dedicated ledger preflight requires `AI_EXECUTION_ENABLED=false` to be explicitly present in the environment. The CLI's `--ledger-preflight` path reports `decisionCycle=NOT_RUN`, `oneShotInvoked=false`, `exchangeCredentialsUsed=false`, and `persistentStateMutation=NONE`.

The owner-provided environment-name query returned no matching PAPER/AI/exchange variable names. This is not a substitute for a fresh source-matched runtime/config verification. No live execution or real-order capability is approved.

### R3 — PaperLedger and T0 isolation

**Disposition: PARTIAL / REQUIRED HARDENING BEFORE ANY RUNNER EXECUTION.**

Positive controls found:

- `inspect_paper_ledger_preflight` requires an existing ledger, read-only account-risk snapshot, PAPER mode, `riskReady=true`, and inactive Kill Switch/Pause.
- Its protected-path checks include `MARKET_DATA_DB`, `T0_FEEDER_LEASE_DB`, `PAPER_DB`, and `PAPER_TRADING_DB`; T0 path overlap is rejected and PAPER aliases must exactly match the configured ledger path.
- `paper_execution.bootstrap` requires a new target path, existing parent directory, explicit `AI_EXECUTION_ENABLED=false`, no configured exchange credentials, exact manifest fields, exact source SHA, funding evidence, cutover evidence and owner-attestation evidence. It builds and validates a temporary PAPER database before publishing the target. This is not a minimal empty-file initializer.
- `ContinuousJournal` uses a separate SQLite journal and checks equality/same-file collisions against T0 DB and lease paths. Continuous static dry-run additionally checks path overlap against T0 and PaperLedger and does not create the journal or bundle directory.
- One-shot Core execution is a bounded CLI operation requiring an explicit config and Bundle v1 input. Continuous orchestration exists as a Python class; the CLI exposes static `--dry-run`, not a continuous daemon/service start command.

Required findings:

1. **T0 alias guard inconsistency:** `run_once` calls `core_runtime.preflight._preflight`, which only compares the ledger path with `MARKET_DATA_DB`. It does not apply the broader protected-path checks from `inspect_paper_ledger_preflight` for `T0_FEEDER_LEASE_DB`, `PAPER_DB`, and `PAPER_TRADING_DB`. The read-only CLI ledger-preflight and the actual One-shot execution path therefore do not share the same complete path-isolation gate. Consolidate the canonical protected-path validator and use it in both paths; add negative tests for every protected alias and path overlap before any runtime execution.
2. **Missing-ledger creation edge:** `PaperLedger.__init__` creates the parent directory and calls `sqlite3.connect(self.path)` before its `apply_migrations=False` branch enables `query_only` and checks migrations. A missing file can therefore be created by constructor invocation (including a path disappearance between preflight and constructor). The One-shot preflight normally requires an existing file, but this constructor is not intrinsically no-create. Add a no-create open mode/atomic identity check or equivalent so a missing/replaced target fails without creating a database; add a regression test proving the path remains absent.
3. **Core leverage policy mismatch:** current source still defines `CORE_LEVERAGE = Decimal("13")`; Core strategy sizing and `PaperLedger` enforce this fixed value. This conflicts with the current project risk direction that Core must not retain a fixed 13x leverage policy. Resolve the policy and update source/tests before treating the Core Runner as runtime-ready. Do not silently accept the legacy 13x behavior as current policy.
4. **Bootstrap evidence prerequisite:** a ready dual ledger cannot be inferred from a blank SQLite file. The bootstrap contract requires funding, cutover and owner-attestation evidence bound to exact hashes/source SHA. The D07 evidence status remains PARTIAL with shared-lineage and completeness/authenticity limits; do not fabricate evidence or bootstrap a ready ledger from synthetic placeholders.

## Test and CI evidence boundary

- Core G2–G6 workflow: run [43571521270](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43571521270), job `132376746126`, SUCCESS, 28/28 workflow steps, exact tested code SHA `34066f4f1d3781c3acc8d597dfcf0cb305882000`.
- Runner hardening 8/8, One-shot regression 15/15, disposable SQLite Core ledger integration 26/26 PASS.
- Artifact ID `14104493037`, name `core-first-code-operational-proof-43571521270`, SHA-256 `205fc3e6108bc86078e4c4b693b40f68de59eefdfd69220f3d76b3462e532ea5`, expires 2026-11-21.
- These tests prove the recorded CI/fixture behaviors, not VPS parity, actual deployed config, actual ledger readiness, continuous service operation, or the unresolved R3 findings above.
- This audit did not run tests. No new workflow run or artifact was created.

## Gate disposition

| Gate | Status | Basis |
|---|---|---|
| R0 GitHub source identity | PASS | Exact branch ref and HEAD verified |
| R0 VPS source parity | BLOCKED | VPS SHA is 43 commits behind |
| R1 PAPER config schema | PASS (source contract) | Exact fail-closed schema reviewed |
| R1 deployed config | NOT VERIFIED | No Core PAPER config identified |
| R2 credential boundary | PASS (source contract) / NOT VERIFIED (VPS runtime) | Four exchange credential variables checked; no matching names in supplied environment listing |
| R3 T0/PaperLedger isolation | PARTIAL / BLOCKED | One-shot preflight guard inconsistency and constructor no-create gap |
| Core leverage policy parity | BLOCKED | Fixed 13x remains in source |
| PaperLedger readiness | NOT VERIFIED | No actual configured, evidence-backed ledger established |
| VPS runtime | NOT RUN | No execution authorized/performed |

## Next bounded steps

1. Reconcile the Core leverage policy and the R3 path/no-create findings in source and tests on the existing branch; use TDD and GitHub Actions only. Do not touch T0 or VPS.
2. Reassess whether a real PAPER ledger can be bootstrapped from valid, independently supportable funding/cutover/owner evidence. If evidence is unavailable or D07 remains PARTIAL, keep readiness BLOCKED rather than inventing a ready account.
3. Only after source fixes and exact-SHA CI evidence, request separate approval for VPS source synchronization and any bounded read-only checks. Source synchronization, config creation, ledger bootstrap, migration, One-shot, Continuous Runner, systemd/autostart, exchange access, AI execution and live orders are not authorized by this audit.

## Explicit non-actions

No branch change, PR, source code modification, VPS/SSH action, package installation, config creation, database creation/open/write, migration, checkpoint, T0 access/mutation, T1/T2 activation, exchange request, AI execution, live trading or real order.


## Follow-up implementation and exact-SHA CI closure — 2026-11-14

The owner-approved source remediation scope was implemented on the same active branch and verified at exact source SHA `482477b4b694af5c812170d11012e9aba29e089f`. This addendum supersedes the unresolved R3 findings above for the current GitHub source only; it does not alter the historical audit baseline or establish VPS parity.

### Implemented source changes

1. **Canonical protected-path validation:** added `core_runtime/ledger_path_guard.py`. Both normal Core preflight and dedicated PaperLedger preflight use the same validator. It rejects equality, same-file aliases and parent/child overlap with `MARKET_DATA_DB` and `T0_FEEDER_LEASE_DB`; configured `PAPER_DB` and `PAPER_TRADING_DB` must resolve to the exact configured ledger. Regression tests cover both T0 aliases, T0 parent/child overlap, PAPER alias mismatch and exact matching aliases.
2. **No-create read-only ledger open:** Core/AI dual-ledger construction with `apply_migrations=False` now requires an existing non-symlink regular file and does not create parent directories. Read-only connections use SQLite `mode=rw` rather than create-capable default mode; device/inode identity is checked before/after open and against the preflight identity. Tests cover missing database, missing parent, symlink, file replacement after construction and replacement between preflight and construction.
3. **Core leverage reconciliation:** `CORE_LEVERAGE` is now 1x and the 1%-of-equity order margin budget remains enforced. The legacy value 13 is retained only as `CORE_ROE_SIGNAL_MULTIPLIER` for the existing signal-threshold scale; it is not order leverage or margin sizing. Core PaperLedger rejects explicit legacy 13x. This owner-approved policy reconciliation supersedes the historical DS-03 fixed-13x decision recorded earlier in the handoff; do not restore 13x as Core execution leverage.

### Exact CI evidence

- Workflow: [43576881822](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43576881822)
- Job: `132392942884` (`operational-proof`), **SUCCESS**; all 25 workflow steps completed successfully.
- Exact checkout/source SHA: `482477b4b694af5c812170d11012e9aba29e089f`.
- Test log confirms: Core Runner hardening 13/13; One-shot regression 15/15; Core operational PaperLedger suite 48/48; disposable SQLite Core Runner integration 26/26; T1–T2 Order Book suite 49/49. Account-wide risk snapshot, compile and remaining workflow checks also completed successfully.
- Artifact ID `14106379805`, name `core-first-code-operational-proof-43576881822`, size 11,297 bytes, GitHub-reported digest `sha256:fe185dde8d551587992b8e08760aa3f12bbebf2f9c8f09c70c13ee1e8f491d70`, expires 2026-11-21T08:39:52Z. Artifact payload was not independently downloaded/re-hashed; payload digest remains **NOT VERIFIED**.
- Branch comparison confirms the active branch is identical to the tested SHA (0 ahead / 0 behind at verification).

### Updated disposition

| Gate | Current status | Basis |
|---|---|---|
| Shared protected-path validator | **PASS (source + CI)** | Same canonical guard used by both preflight paths; alias/overlap regression tests passed |
| Read-only ledger no-create and replacement protection | **PASS (source + CI)** | Existing-file-only, mode=rw and identity checks; missing/replacement regressions passed |
| Core leverage policy | **PASS (source + CI)** | Core 1x, 1% margin budget; legacy 13x rejected as order leverage |
| Core Runner code-level regression | **PASS** | Exact-SHA workflow 43576881822 SUCCESS |
| VPS source parity | **BLOCKED** | VPS-reported SHA `9aac55b60bec0180cf639086139fc95bf4dabd32` predates this source and is not synchronized |
| Actual Core PAPER config / ledger on VPS | **NOT VERIFIED** | No deployment config or evidence-backed Core ledger identified |
| Runner runtime / continuous service | **NOT RUN / NOT AUTHORIZED** | CI fixtures only; no VPS, bootstrap, One-shot or continuous execution |

No VPS synchronization, ledger bootstrap, migration, T0 access/mutation, Runner invocation, service/autostart, exchange access, AI execution, live trading or real orders occurred. `AI_EXECUTION_ENABLED=false` and paper-only posture remain unchanged.

### Next gate

The three approved source fixes are closed for GitHub source/CI scope. Do not start another code change automatically. The next possible work is a separate owner-approved decision on whether to request source synchronization and bounded read-only VPS parity checks. This does not authorize ledger bootstrap or Runner execution.
