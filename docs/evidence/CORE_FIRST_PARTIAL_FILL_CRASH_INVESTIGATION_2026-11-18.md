# Partial-fill process-crash recovery — CI investigation

Date: 2026-11-18 (Asia/Ho_Chi_Minh)

## Scope
- Existing branch: `feature/core-operational-proof-20261112`.
- Test-only increment: `paper_execution/test_partial_fill_process_crash.py`.
- No production ledger source, canonical T0 data, T1 service, VPS/runtime, exchange credentials, or live execution was changed or used.

## CI evidence
1. Earlier workflow run [44210233295](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/44210233295)
   - Checked-out SHA: `56eea1be3126d01ad691e0931787cb20dae9f73f`.
   - Job: `134486415005`.
   - The 50-test Core end-to-end PAPER suite completed PASS.
   - The process-crash test began; `test_process_kill_after_all_writes_before_commit_rolls_back_partial_fill` reported FAIL. The second test did not finish before the workflow operation was cancelled.
   - Artifact ID: `14386797004`, name `core-first-code-operational-proof-44210233295`, 13,268 bytes, SHA-256 `1afb0acc6b9818577373957df6e777a2ea05cebf3ed82861d26310244d0f43b9`.
2. Corrected-trigger workflow run [44210302780](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/44210302780)
   - Checked-out SHA: `ddaf2c3e5fcd957f228ae90300858679d45baf85`.
   - Job: `134495571303`.
   - The process-crash test started but produced no terminal test result before the 20-minute job timeout/cancellation.
   - Artifact ID: `14388426412`, name `core-first-code-operational-proof-44210302780`, 13,232 bytes, GitHub digest SHA-256 `438dd48aa0ceb76567f1d5bc4aa2c32e8082f6d37c3e1216cac6102cc921c6ab`.
   - The artifact's `partial-fill-process-crash-tests.log` contains only the first test's start line; no traceback was emitted.
3. Both runs' preceding Core operational test step completed successfully (50 tests). This does not certify crash recovery.

## Verdict
- Actual process termination/SQLite rollback at the two partial-fill checkpoints: **BLOCKED / NOT VERIFIED**.
- No evidence currently proves a production ledger defect. The available evidence is consistent with a test-harness/process-control hang or failure, but root cause is undetermined.
- Do not mark either crash checkpoint PASS and do not modify `paper_execution/ledger.py` without a reproduced transaction defect.

## Next action
- Isolate each checkpoint test in a bounded CI diagnostic invocation, with process-level timeout and faulthandler/worker exit diagnostics. Run the tests separately so one stuck checkpoint cannot hide the other.
- Inspect worker exit code, whether the checkpoint event was reached, whether termination completed, and where the parent is blocked.
- Fix only the demonstrated test-harness issue, or, if the isolated reproduction proves a ledger atomicity defect, add a RED regression before changing ledger source.
- Keep all existing safety gates: `AI_EXECUTION_ENABLED=false`; no T0/T1 runtime, VPS, real orders, AI execution, merge, or branch promotion.
