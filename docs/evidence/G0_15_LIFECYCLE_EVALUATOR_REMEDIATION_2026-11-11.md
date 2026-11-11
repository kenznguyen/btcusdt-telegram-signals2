# G0.15 — Lifecycle Evaluator Remediation of G0.14 Findings (2026-11-11)

Date: 2026-11-11  
Work type: bounded source/test remediation; pure in-memory evaluator only  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Base source HEAD: `8853b8f90bd5aa52e33a18f2f219f43e36112d0d`  
Implementation commit: `eb444273f54f46ca48d51f7be8cfed8d3a8a6cf9`

## 1. Approved scope

Owner approved G0.15 remediation limited to G0.14 findings R1–R4:
- R1: explicit type-safe handling for malformed copy inventory state and regression test.
- R2: exact copy/version binding to complete copies inventory, with empty/mismatched/duplicate inventory tests.
- R3: preserve PROTECTED precedence while collecting applicable unknown metadata reason codes.
- R4: add sensitivity label and class-to-policy mapping only if exact owner-ratified vocabulary/mapping exists.

No CI dispatch, TEST-01–07 harness, external evidence authentication, production inventory, VPS/runtime, destructive executor, archive, cleanup, expiry, compaction, vacuum or deletion was included.

## 2. Policy-source reconciliation and R4 disposition

Reviewed:
- RET-01/RET-02 ratification: `docs/evidence/p1-8/P1.8.143-retention-policy-ratification.md`, blob `4e10c73571fe479d8f66138db8c7aa81153109b5`.
- Owner decision package: `docs/evidence/p1-8/P1.8.142-owner-retention-and-data-class-disposition-decision-package.md`, blob `f208ed3e128a9dff3dafb34f319253ccb5d78279`.
- Earlier class policy: `docs/evidence/p1-8/P1.8.80-retention-and-eligibility-policy.md`, blob `a38710c9d01e5409ce989cc73f791c94bc73773f`.
- Logical field map: Stage C.13, blob `c43c8bfbccaf698d6670f33fab66ee12d2072a7f`.

The policy documents establish that sensitivity/classification is a required fact for relevant review gates, but they do not ratify an exact sensitivity-label vocabulary or a complete class-to-policy/version mapping for the evaluator. RET-01 B and RET-02 B identify protected/reviewable data classes and conditions; they do not define the missing sensitivity taxonomy.

**R4: BLOCKED — NOT IMPLEMENTED.** No vocabulary, mapping, default label or policy inference was invented. The evaluator's existing RET-01 B / RET-02 B policy references remain unchanged.

## 3. Changes

### R1 — malformed copy-state handling

- Made the copy inventory state type check explicit before membership testing; non-string/unhashable state values fail closed with `UNK_COPY_LINEAGE`.
- Added `test_copy_inventory_unhashable_state_fails_closed`.
- The regression test was also run against the pre-change source and already failed closed because the prior compound condition short-circuited on its string-shape guard. Thus the G0.14 TypeError was **not reproduced** against the checked-in baseline in this run. The explicit guard is a defensive clarity hardening, not evidence that a baseline crash was reproduced.

### R2 — exact copy inventory binding

- A `COPY_SPECIFIC_REVIEW` now requires `copy_lineage.copy_id == object_id`.
- It requires exactly one complete inventory entry matching the evaluated copy ID, exact object version, `NONCANONICAL_COPY` kind, and a supported string state (`PRESENT` or `RETIRED`).
- Empty, mismatched-version and duplicate matching inventory entries fail closed with `UNK_COPY_LINEAGE`.
- Updated the positive exact-copy test to include the exact matching inventory entry.

### R3 — protected precedence with unknown-code collection

- Protected class or verified binding hold is captured as a protective precedence flag.
- The evaluator continues validating supplied metadata to collect applicable `UNK_*` reason codes.
- Final disposition remains `PROTECTED`; unknown metadata does not downgrade a protected object to `BLOCKED_UNKNOWN`.
- Added regression coverage for missing hold, lineage, dependency, copy-inventory and process metadata.

## 4. Source and test identity

Implementation commit: `eb444273f54f46ca48d51f7be8cfed8d3a8a6cf9`.

| Path | Git blob SHA |
|---|---|
| `pipeline/lifecycle_disposition.py` | `6f083a6b9b7107f3b6e3c7af3b32da34b5dafb5e` |
| `pipeline/test_lifecycle_disposition.py` | `2ba03eb0deac67e1b82afb60ca24a6c15a2a56ce` |

The two GitHub blob SHAs were compared with local `git hash-object` output and matched exactly.

## 5. Test evidence

TDD reproduction results:
- R2 exact-copy inventory tests: **RED** against the pre-change evaluator (empty, mismatched and duplicate inventory were incorrectly accepted).
- R3 protected unknown-metadata test: **RED** against the pre-change evaluator (unknown metadata reason codes were omitted).
- R1 unhashable-state regression: pre-change evaluator already returned fail-closed; no baseline TypeError reproduced. Explicit type guard added and final regression remains PASS.

Final focused command:
`python -m unittest pipeline.test_lifecycle_disposition -v`

Result: **23 tests PASS, 0 failures, 0 errors**.

Compile check:
`python -m py_compile pipeline/lifecycle_disposition.py pipeline/test_lifecycle_disposition.py`

Result: **PASS**.

Repository-wide tests: **NOT RUN**. GitHub Actions: **NOT DISPATCHED**. Workflow run/artifact: **NONE**.

## 6. Verdict

- R1: **PASS — defensive type guard and regression; baseline TypeError NOT REPRODUCED**.
- R2: **PASS — exact object/version inventory binding and negative cases**.
- R3: **PASS — protected precedence and unknown reason-code collection**.
- R4: **BLOCKED — exact sensitivity vocabulary/class-policy mapping absent from ratified policy**.
- Focused unit tests: **23/23 PASS**.
- Compile: **PASS**.
- Repository-wide suite / CI: **NOT RUN / NOT DISPATCHED**.
- TEST-01–07 technical closure: **NOT ESTABLISHED**; 0/87 lifecycle vectors executed remains unchanged.
- TEST-08: **NOT GRANTED**.
- Runtime/VPS: **NOT VERIFIED**.

Overall G0.15: **PARTIAL PASS — R1–R3 remediated; R4 blocked**.

## 7. Explicit non-actions and limits

No workflow, fixture, schema, API, registry, adapter, runner, oracle, scheduler, service, permission, credential, database, storage, VPS, market data, model, ledger or runtime changes. No production inventory, network/provider/database access, external evidence authentication, workflow dispatch, archive, quarantine, cleanup, expiry, compaction, vacuum or deletion.

The evaluator still consumes identity, provenance, completeness, dependency, hold and rebuildability facts as caller-supplied assertions; it does not authenticate them or recompute payload digests. A review disposition is not deletion/archive authorization. T0 remains independent and protected. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.

## 8. Next gate

Resolve R4 only through an explicit owner-ratified sensitivity vocabulary and class-to-policy mapping, then separately approve its implementation/tests. CI workflow/permissions, broader TEST-01–07 harness, external evidence authentication and any destructive operation remain separate gates.
