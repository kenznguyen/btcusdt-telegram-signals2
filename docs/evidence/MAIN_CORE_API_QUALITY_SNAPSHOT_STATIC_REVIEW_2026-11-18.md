# Main-side Core API Quality Snapshot — Static Review

Date: 2026-11-18 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Compared refs: `main` vs `feature/core-operational-proof-20261112`

## Scope

Read-only static review of the two main-only Core API commits from the 85-commit main-side delta:
- `6a21c4183432634437b5014a48da4140fed861a2` — `refactor(core-api): align Core quality projection with Bundle v1`
- `2b0c043e3e336ca79d639c91cb9ecd7078c280c7` — `test(core-api): require ephemeral preview bundle without journal`

No source edits, test runs, workflow dispatches, candidate checkout, merge simulation, runtime/T0/VPS access, or exchange access were performed.

## Exact source identities

| File | main blob | branch blob |
|---|---|---|
| `pipeline/api.py` | `fe5b9ffc8a95001f5b1a9734da67a1cb8d23a31b` | `bb89b0bdf196f64b3ab9d9ac15b6597f333c583e` |
| `core_runtime/test_api_facade.py` | `e41f374afee2b3b2be5c70f12c441218367d7f70` | `f860d32c4047374dec4f574605a1c1b21ba1a58b` |

## Finding MAPI-01 — main quality_snapshot reads local before assignment

**Severity: Critical for the affected API operation.**

In main `pipeline/api.py`, `quality_snapshot(timestamp)`:
- line 328 reads `core.get("sourceEvidence")`;
- line 351 assigns `core = core_runtime_preview(timestamp)`.

Because `core` is assigned within the function, Python treats it as a local variable. The read at line 328 therefore raises `UnboundLocalError` before the later assignment can execute. The affected quality projection cannot complete on this path.

The main-side regression test `test_quality_projection_uses_bundle_preview_and_t1_book_evidence` (main test blob above, lines 160–191) calls `common_api.quality_snapshot(NOW)` and expects the T1 snapshot and Core status projection. Static control-flow analysis predicts it will fail at the earlier read. This test was not executed in this review; runtime failure is therefore **NOT RUN**, while the ordering defect is **CONFIRMED STATICALLY**.

Branch implementation fixes the ordering:
- branch `pipeline/api.py` assigns `core = core_runtime_preview(timestamp)` at line 384;
- it reads `core.get("sourceEvidence")` at line 385;
- it reuses the same `core` value for indicator/status projection at lines 408–412.
The branch test contains the same quality projection scenario.

## Disposition

1. Preserve branch `pipeline/api.py` and branch `core_runtime/test_api_facade.py`; do not import main versions wholesale.
2. Do not selectively cherry-pick the main test without its corrected implementation ordering; the branch already contains the equivalent contract scenario.
3. If future reconciliation requires other main-side API behavior, isolate it into a separate reviewed patch with a regression test and exact-SHA CI.
4. This finding reinforces the prior bounded integration map; it does not validate the full 85-commit main-side delta or the merged tree.

## Verdict

**STATIC REVIEW PASS WITH CRITICAL MAIN-SIDE DEFECT.** Branch implementation is the safer integration baseline for these two files. Main integration and merge remain **BLOCKED / NOT AUTHORIZED**. No runtime or trading readiness is implied.

## CI regression and bounded repair — 2026-11-18

### Test isolation and RED evidence

The first workflow attempts exposed that this main checkout does not contain the imported T0 implementation modules (market_data.api, market_data.postgres, market_data.storage) or the broader core_runtime package. The original facade test therefore failed during module import before reaching the projection assertion.

To avoid importing or copying T0 implementation code into this repository, a focused test was added at ci/test_core_api_quality_snapshot.py. It stubs only import-time adapter symbols and the unrelated risk-limit parser; it patches context, market_window, and core_runtime_preview inputs. The actual pipeline.api.quality_snapshot() implementation remains under test.

- Test file commit: 15158d0bc38e03b939b01765e41e3beb00815ea9.
- Workflow/test commit: 5ec333702185760ab40f8efa5d8e50ca06e3ce8f.
- RED run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/44301561075
- RED source SHA: 5ec333702185760ab40f8efa5d8e50ca06e3ce8f.
- RED result: EXPECTED FAILURE, with UnboundLocalError: cannot access local variable 'core' where it is not associated with a value at the first core.get("sourceEvidence") read in quality_snapshot().
- RED artifact ID: 14425444786; SHA-256: d939a81e6df2b6fadcd71fae893330bb6c71248b21da2ead564a6dc8b6d5bb80.

This is runtime confirmation of the statically identified ordering defect.

### Minimal source repair and GREEN evidence

The repair moves core = core_runtime_preview(timestamp) to immediately before the first read of core, then reuses the same preview result for the Strategy Core projection. No API response schema, strategy behavior, risk policy, T0 source, or runtime configuration was changed.

- Fix commit / exact tested source SHA: 1502521b85565b4b75e5368417b3a1169329ec75.
- pipeline/api.py before blob: fe5b9ffc8a95001f5b1a9734da67a1cb8d23a31b.
- pipeline/api.py after blob: b6f017f603fecd242ba47a83fff387f8594bca2e.
- GREEN run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/44301625371
- Workflow job: quality-snapshot-regression, conclusion SUCCESS.
- Checked-out source SHA: 1502521b85565b4b75e5368417b3a1169329ec75.
- py_compile: PASS.
- Focused regression: 1 test PASS (Ran 1 test ... OK).
- Paper-only guard: PASS; AI_EXECUTION_ENABLED=false; database paths and exchange credentials empty.
- GREEN artifact ID: 14425806625; name: core-api-quality-regression-1502521b85565b4b75e5368417b3a1169329ec75; SHA-256: 8c7fee79dcc06e311097e7b5681fd02a4de6eb71ef396ced85e65f2c2e12dc87.
- Artifact URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/44301625371/artifacts/14425806625

### Verification boundary and disposition

- The specific quality_snapshot() local-variable ordering defect is FIXED / REGRESSION PASS on the exact main SHA above.
- The regression is deliberately isolated from T0. It does not verify the real T0 adapters, candle transport, database, feeder, T1, full API integration, or the entire Core runtime.
- The original broad core_runtime/test_api_facade.py suite remains NOT VERIFIED on this main snapshot because its imported Core runtime modules are absent from this main tree.
- No source from feature/core-operational-proof-20261112 was copied or merged. No T0/VPS/runtime/deployment or exchange action occurred. No live orders are possible in this workflow.
- Next: preserve this evidence and handoff on main; broader API/T0 integration remains a separate, explicitly scoped verification task.
