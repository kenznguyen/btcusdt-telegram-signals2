# Dual Ledger documentation status reconciliation — 2026-11-11

## Scope

Read-only comparison of the current Dual Ledger source/CI disposition against
architecture and migration documents. Documentation-only, append-only updates
were made to reconcile current authorization and verification status. No source
code, tests, workflow definitions, SQLite database, VPS process, T0 data, lease,
credential, exchange state or deployment setting was changed by this task.

## Exact implementation and verification evidence

- Source/test SHA: `8d9eee6cd503237f8b8a398fcaf1e055dfa9d644`.
- Dual Ledger CI: [run 42971136555](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42971136555).
- Run conclusion: SUCCESS; exact head SHA matches the source/test SHA above.
- Job: Isolated Core and AI ledger contract — SUCCESS.
- Compile: PASS.
- Focused DS-01 / DS-02 contract: PASS.
- Full `paper_execution` regression: 300 tests PASS.
- Artifact ID: `13833202840`; name
  `dual-ledger-red-evidence-8d9eee6cd503237f8b8a398fcaf1e055dfa9d644`;
  SHA-256 `0eb0bbb6ad5bfbca27c9665e06548a11dba37e2d25d4939ea891301a6054f506`.
- Independent code review is recorded in the main evidence report; no
  Critical/Required finding remains within DS-01 / DS-02 scope.

## Documentation inconsistencies found

1. `docs/architecture/DUAL_LEDGER_CONTRACT.md` retained a design-stage
   header saying implementation had not started, a Section 8 note saying RED 1
   was the only coexistence test, and a Section 9 statement that implementation
   was not authorized. Those statements were historically correct at the time
   written, but stale if read as the current project status.
2. `docs/architecture/DUAL_LEDGER_SCHEMA_MIGRATION_PLAN.md` retained a
   design-stage authorization header saying implementation/database changes
   remained unauthorized. Its later v1-v5 appendices document historical
   implementations and CI evidence, but the document lacked a current bounded
   DS-01 / DS-02 authorization disposition.
3. `docs/architecture/DUAL_LEDGER_OPEN_DECISIONS_PROPOSAL.md` correctly
   recorded that the 2026-11-06 approval of six design decisions authorized
   documentation only. It did not record the later, separate owner approval
   for the bounded DS-01 / DS-02 source/test increment.

## Documentation-only corrections committed

Append-only dated sections were added to all three architecture documents:

- `docs/architecture/DUAL_LEDGER_CONTRACT.md`
  - distinguishes historical design-stage status from current DS-01 / DS-02
    source/CI PASS;
  - clarifies that the 300-test result does not prove all 15 contract gates or
    the complete Dual Ledger migration contract.
- `docs/architecture/DUAL_LEDGER_SCHEMA_MIGRATION_PLAN.md`
  - records the later bounded approval and exact verification;
  - explicitly preserves persistent DB migration, account cutover, funding
    verification and runtime activation as separately gated.
- `docs/architecture/DUAL_LEDGER_OPEN_DECISIONS_PROPOSAL.md`
  - preserves the original 2026-11-06 approval boundary and appends the
    subsequent separate implementation approval.

No historical section, migration checksum, schema version, or previous evidence
was deleted or rewritten.

## Current disposition

| Area | Status | Boundary |
|---|---|---|
| DS-01 API writer/cancel/account mark/equity | PASS | Source + isolated CI only |
| DS-02 Core strategy-scoped read | PASS | Source + isolated CI only |
| DS-04 documentation reconciliation | PASS | Append-only documentation scope |
| Full Dual Ledger contract acceptance | NOT VERIFIED | Not all 15 contract gates claimed |
| Persistent account DB migration | NOT AUTHORIZED / NOT PERFORMED | No persistent DB touched |
| Account cutover and funding readiness | NOT VERIFIED | Fail-closed until separately approved and evidenced |
| VPS/runtime/deployment | NOT AUTHORIZED / NOT PERFORMED | No runtime action |
| DS-03 Core sizing/leverage | BLOCKED | Requires separate owner decision |
| Stage II A2.3 / Ed25519 adapter | PAUSED BY OWNER | Do not resume without explicit reopen |
| Live execution | NOT AUTHORIZED / NOT PERFORMED | `AI_EXECUTION_ENABLED=false` |

## Next step and limits

Next work should be a separate owner proposal for DS-03 Core sizing/leverage
policy or another specifically approved paper-only scope. Do not apply schema
migrations, perform account cutover, activate runtime, change T0, alter Core
sizing/leverage, deploy, connect exchange credentials or place live orders
without separate explicit approval.



## Post-DS-03 and AI-path status reconciliation — 2026-11-11 (append-only)

This addendum supersedes only the dated status cells below; historical
documentation and evidence remain preserved.

| Item | Current status | Evidence / limit |
|---|---|---|
| DS-01 API writer, cancellation, account equity | PASS | Exact source/CI evidence remains in prior addendum |
| DS-02 Core strategy-scoped read | PASS | Exact source/CI evidence remains in prior addendum |
| DS-03 Core fixed 13x and 1% current-equity sizing | PASS — source/isolated CI only | Source SHA `6ef0d7456b2791fae73bfea8855ee30482774673`; run `42975606884`; 237 focused + 300 full tests PASS; artifact `13834194926` |
| DS-04 contract/document status reconciliation | PASS — append-only status reconciliation | This addendum plus current contract, migration plan, open-decisions proposal, baseline and handoff |
| AI independent signal path | PASS at source level | Core WAIT / AI BUY test; AI decision function is separate |
| AI 1x–3x dynamic leverage | BLOCKED / NOT IMPLEMENTED | Generic `LEVERAGE` env only; no AI-specific bound |
| AI confidence calibration | BLOCKED / NOT IMPLEMENTED | Prediction artifact has no calibrated confidence/calibration version |
| AI account-equity sizing | BLOCKED / NOT IMPLEMENTED | Fixed `PAPER_TARGET_BASE`; shared risk engine rejects over-budget but does not resize |
| Persistent account DB migration / cutover / funding readiness | NOT AUTHORIZED / NOT PERFORMED / NOT VERIFIED | Fail-closed until separate owner approval and evidence |
| VPS/runtime/deployment/live execution | NOT AUTHORIZED / NOT PERFORMED | `AI_EXECUTION_ENABLED=false` |

The AI audit is read-only and is not an implementation approval. AI sizing,
calibration, ledger leverage changes, schema migration and runtime activation
require a separate bounded scope and explicit owner approval.
