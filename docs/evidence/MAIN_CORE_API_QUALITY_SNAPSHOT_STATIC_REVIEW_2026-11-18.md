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
- it reuses the same `core` value for Core projection at lines 408–412.
The branch test contains the same quality projection scenario.

## Disposition

1. Preserve branch `pipeline/api.py` and `core_runtime/test_api_facade.py`; do not import main versions wholesale.
2. Do not selectively cherry-pick the main test without its corrected implementation ordering; the branch already contains the equivalent contract scenario.
3. If future reconciliation requires other main-side API behavior, isolate it into a separate reviewed patch with a regression test and exact-SHA CI.
4. This finding does not validate the full main-side delta or the merged tree.

## Verdict

**STATIC REVIEW PASS WITH CRITICAL MAIN-SIDE DEFECT.** Branch implementation is the safer integration baseline for these two files. Main integration and merge remain **BLOCKED / NOT AUTHORIZED**. No runtime or trading readiness is implied.
