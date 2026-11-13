# P3 Read-only PaperLedger Preflight — 2026-11-13

## Scope and safety boundary

Implement and verify a read-only PaperLedger readiness gate for the Continuous Core P3 pre-approval checklist. This increment is repository code and GitHub Actions CI only.

- No VPS/SSH access, package installation, config creation on VPS, service, systemd/autostart, or runner activation.
- No T0 canonical database, T0 lease/fencing state, T1/T2 runtime, exchange credentials/connections, or real orders.
- AI_EXECUTION_ENABLED=false is mandatory.
- The check does not instantiate ContinuousCoreRunner, ContinuousJournal, One-shot, or any order submission path.

## Implementation

- Added core_runtime/paper_ledger_preflight.py.
- Added CLI mode: python -m core_runtime --config <paper-config.json> --ledger-preflight.
- Uses the existing paper_execution.ledger.read_account_risk_snapshot reader, which opens SQLite with mode=ro, enables PRAGMA query_only=ON, and validates the account-wide risk snapshot and required schema/migrations.
- Requires PAPER mode, liveTradingSupported=false, riskReady=true, Kill Switch not killed, and risk not paused.
- Rejects missing/unreadable/corrupt ledger, missing readiness, active kill latch, pause state, exchange credentials, or AI execution not explicitly disabled.
- Output states decisionCycle=NOT_RUN, oneShotInvoked=false, and persistentStateMutation=NONE.
- New tests compare database SHA-256 before and after successful and rejected reads.

## Tests

New suite: core_runtime.test_paper_ledger_preflight — 6/6 PASS in the read-only PaperLedger preflight CI step:
1. Ready ledger reports PAPER/riskReady and leaves database bytes unchanged.
2. Active Kill Switch blocks without database byte changes.
3. Paused ledger blocks without database byte changes.
4. riskReady=false blocks without database byte changes.
5. Missing/incomplete ledger fails closed without mutation.
6. AI execution must be explicitly disabled and exchange credentials must be absent.

## CI history

- Test source was added in commit ce41efc169ce52524bfdb07c640221e1ee25be9d.
- Implementation was added in 124dde60938add1c3a22feacabaa8079bad76f94.
- CLI/workflow integration is in the current tested source commit 528a0f633673871ed65b5a6dab1894bd46e2b6a4.
- Run 43422378468 failed at the existing Core CLI contract step because the first CLI edit contained a literal escaped newline; fixed.
- Run 43422593680 failed at the same existing CLI contract step because the CLI flag had not been registered; fixed in the complete CLI rewrite.
- Run 43422713480, attempt 1, hit the previously observed intermittent SQLite "database is locked" in the unrelated journal concurrency test. The failing job was retried without source changes.
- Run 43422713480, attempt 2, exact checked-out source SHA 528a0f633673871ed65b5a6dab1894bd46e2b6a4, conclusion SUCCESS. All workflow steps completed successfully, including Core end-to-end operational proof, account-wide risk snapshot read-only tests, shared risk/PaperLedger regressions, and T1/T2 integration. The read-only PaperLedger preflight step passed 6/6. The initial attempt failed only on the previously observed intermittent SQLite journal concurrency lock; attempt 2 passed without source changes.

Workflow: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43422713480

Final artifact: ID 14035196887, name core-first-code-operational-proof-43422713480, size 11,114 bytes, GitHub-reported digest sha256:7eb37b0b7ea88e704ddb60603a8ee1e82c97ec61454e26733ae2a2f23afe7e20, expires 2026-11-20T12:09:30Z. The artifact payload digest was not independently re-computed; the digest above is the GitHub-reported upload digest.

## Current disposition

- PaperLedger read-only preflight contract: PASS — 6/6.
- Existing Core CLI and One-shot suites in attempt 2: PASS.
- Full workflow at exact source SHA 528a0f633673871ed65b5a6dab1894bd46e2b6a4: PASS — run 43422713480, attempt 2; all workflow steps SUCCESS.
- P3 VPS execution/activation: NOT APPROVED / NOT RUN.
- Full live-host runtime dependency/config readiness: NOT VERIFIED.

## Next step

Code and CI verification are complete for this increment. Next: preserve P3 VPS activation as a separate owner approval gate; before that, reconcile the previously unresolved live-host dependency/config readiness from an explicitly approved, bounded read-only host inventory.

Do not run this command on a VPS until a separate bounded VPS approval is granted. No runner startup, scheduler loop, One-shot, AI Strategy, deployment, exchange access, credentials, or real orders are authorized by this evidence.
