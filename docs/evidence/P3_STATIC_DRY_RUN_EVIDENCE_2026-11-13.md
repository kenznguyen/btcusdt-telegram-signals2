# P3 Static No-Side-Effect Dry-Run — Evidence

Date: 2026-11-13  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Implementation source: `bd05e69d943231c1f2ca19a386fd1a7219a168b4`

## Scope

A static-only dry-run entry point was added. It validates configuration and filesystem paths without starting ContinuousCoreRunner or opening persistent runtime state.

CLI:

```bash
python -m core_runtime \
  --config /absolute/path/to/paper-config.json \
  --dry-run \
  --journal-path /absolute/path/to/future-runner-state/journal.sqlite3 \
  --bundle-store-dir /absolute/path/to/future-runner-state/bundles
```

## Safety contract

- Exact Runner config shape and One-shot risk policy are validated.
- `AI_EXECUTION_ENABLED=false` must be explicit.
- Non-empty Binance/OKX credentials are rejected.
- PaperLedger path must exist as a file, but its contents are not opened or read.
- Journal and bundle-store parents must already exist; dry-run creates neither.
- Journal/bundle paths are checked for aliases/overlaps with PaperLedger, `MARKET_DATA_DB`, and `T0_FEEDER_LEASE_DB`.
- No ContinuousCoreRunner or ContinuousJournal instance is created.
- No process lock, recovery, bundle-provider call, bundle persistence, One-shot call, or PaperLedger mutation occurs.
- Output identifies `decisionCycle=NOT_RUN`, `ledgerContentsRead=false`, `persistentStateMutation=NONE`.

This is a static config/path check, not a Continuous Runner scheduler simulation. It does not validate ledger schema or `riskReady`, and it does not establish VPS readiness.

## TDD and CI history

| Source / run | Result | Evidence |
|---|---|---|
| `d12f967744e9912142460e3a98aa46d8fa8d6456`, run `43420846405` | RED | Expected import failure: dry-run module not implemented yet |
| `71899e8df1e5c109edc1bce47d9b255f79cd442d`, run `43420926559` | FAIL | CLI syntax defect from literal escaped newlines; fixed |
| `a71d67ffac70260a1322ed15e2668aded8187602`, run `43421061835` | PASS | Full operational workflow success; 8 static dry-run tests passed; predates CLI subprocess test |
| `a82034631293e07e4537ee8ba6cadb41a0b1365b`, run `43421133314` | FAIL | CLI test missing `subprocess` import; fixed |
| `bd05e69d943231c1f2ca19a386fd1a7219a168b4`, run `43421353331`, attempt 1 | FAIL | Existing journal concurrency test hit transient SQLite `database is locked`; unrelated to dry-run |
| Same source, run `43421353331`, attempt 2 | PASS | Full workflow SUCCESS; all steps passed; dry-run 9/9 |

## Final disposition

- Static dry-run implementation: committed.
- Static dry-run contracts: **PASS 9/9**.
- Full current-source CI regression: **PASS** — run `43421353331`, attempt 2, job `131872065732`, exact code SHA `bd05e69d943231c1f2ca19a386fd1a7219a168b4`, all workflow steps SUCCESS.
- Artifact ID `14034337071`, name `core-first-code-operational-proof-43421353331`, 11,110 bytes, GitHub-reported SHA-256 `11fbeebcc6cfa968ec016fbf069b14345291428c3066964acba83eea14d78e34`, expires `2026-11-20T11:59:24Z`. Payload hash NOT independently verified.
- P3 VPS execution: **NOT APPROVED / NOT RUN**.
- No VPS, T0, T1, T2, PaperLedger runtime, exchange credentials, exchange connection, or real orders were accessed or changed by this work.


## Final CI readback

- Workflow run: [43421353331](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43421353331), attempt 2, job 131872065732, SUCCESS.
- Exact checked-out implementation SHA: `bd05e69d943231c1f2ca19a386fd1a7219a168b4`.
- All 22 workflow steps succeeded. Continuous cadence 5/5, journal 15/15, orchestration 23/23, static dry-run 9/9. Remaining Core/One-shot/Bundle/adapter/PaperLedger/risk/T1-T2 regression steps succeeded.
- Artifact ID `14034337071`, name `core-first-code-operational-proof-43421353331`, 11,110 bytes, GitHub-reported digest `sha256:11fbeebcc6cfa968ec016fbf069b14345291428c3066964acba83eea14d78e34`, expires `2026-11-20T11:59:24Z`. Payload hash was not independently re-computed.
- Branch HEAD at final documentation readback: `837ee6f41dadeffbfec7aaaf52582d3da957020f`. Compare from tested code SHA to documentation HEAD: 1 ahead, 0 behind, only `docs/PROJECT_SESSION_HANDOFF.md` and this evidence file changed. No code changes after tested SHA.
