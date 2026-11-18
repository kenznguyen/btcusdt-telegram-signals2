# T0 A2.2 Stage I — F-01/F-02 Fixture Conformance Repair

Date: 2026-11-18
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/core-operational-proof-20261112
Final source HEAD: 9e385fd95e79d1049d3ce0959a36619a879f3e91
Scope: only t0_signature_stage1/verdicts.py and t0_signature_stage1/tests/test_verdicts.py.

## Authorization and TDD evidence

The owner explicitly approved repair of F-01/F-02 in the two scoped files and isolated tests. TDD sequence:
- RED test commit: b9f2b8b56f52737e13d0f6b4dfbfcd2032f48397.
- Implementation and follow-up corrections: 910967dd0b136faedafe1e51011174c44a4c6dc0, 9457ce935d8331619de55527842bebe099cc63e6, c11843409cd42df1d9522a22b4f0c44c9c4aff7c, 0512580b5410e3b2e7f7400a118dc8bec2aebbd4, final cleanup 9e385fd95e79d1049d3ce0959a36619a879f3e91.
- The RED run against the pre-fix source failed as expected: 27 mutation-path assertions failed and the new path/evaluator helpers were absent.
- Final source was fetched by exact commit SHA into an isolated ephemeral Python sandbox; no repository CI or workflow was dispatched.

## Changes

### F-01 — addressed

- Replaced flat/incomplete baselines with nested B0, B0-PF and hypothetical B-A fixture shapes aligned to A2.2 §18.
- All 27 mutation paths now resolve to pre-existing leaves.
- Fixture builder rejects absent intermediate/leaf paths; it never creates dictionaries or fields during mutation.
- Builder checks that the before/after leaf-path sets are identical and exactly the declared leaf changes.
- Added tests for existing-path enforcement, fail-closed missing path, no field addition/removal, compound-mutation rejection, and defensive isolation of mutable catalog values.

### F-02 — addressed

- Removed catalog fact_key routing metadata. Added a regression case proving compound mutations fail closed.
- Added deterministic fact derivation from actual fixture content.
- evaluate_stage1_fixture() now builds the baseline/mutated pair and routes using the mutated fixture content.
- Added a regression test that restores the mutated purpose field and confirms the purpose verdict disappears, proving the evaluator is not merely reading a preassigned catalog fact.

### Scope limits

- These are synthetic deterministic routing fixtures, not a cryptographic verifier.
- No real key, signature generation/verification, trust-root enrollment, bootstrap, durable state, anchor, custody, or readback integration was added.
- The B-A fixture is hypothetical test data only; it does not enable operational Path A.
- This work does not establish all A2.2 per-dimension assertions or production security properties. Stage I contract-conformance must not be upgraded to unconditional PASS solely from these tests.

## Exact final source identity

- Commit: 9e385fd95e79d1049d3ce0959a36619a879f3e91
- t0_signature_stage1/verdicts.py blob: 85938c16d338f56d38721460adf4494f18bb2ed3
- t0_signature_stage1/tests/test_verdicts.py blob: a28d957fc4522cf56805f0435c04a4b98b812268
- GitHub compare from pre-work HEAD 00dd663b05741f6a7fc3d863301f90e29bcf2781 to final HEAD: ahead 6, behind 0; exactly two changed paths, both within the approved scope.

## Verification

Executed in an isolated ephemeral Python test sandbox after fetching the exact final commit:
- python -m compileall -q t0_signature_stage1: PASS.
- python -m unittest t0_signature_stage1.tests.test_verdicts -v: 17 tests PASS.
- python -m unittest discover -s t0_signature_stage1/tests -p 'test_*.py' -v: 40 tests PASS.
- No external service, DB, network, credential, VPS or exchange access was used by the test process after source retrieval.
- This is not a GitHub Actions run; no workflow run or artifact ID exists.

## Safety and disposition

- F-01: PASS — repaired and regression-tested.
- F-02: PASS — repaired and regression-tested.
- Scoped Stage I package tests: PASS in isolated sandbox.
- Stage I full contract conformance: PARTIAL / NOT VERIFIED beyond the tested synthetic scope.
- Workflow execution: NOT RUN / NOT AUTHORIZED.
- Stages II–V: BLOCKED / NOT APPROVED.
- Merge/deployment/trading: NOT AUTHORIZED.
- No source outside the two approved files changed. No workflow, runtime, T0 canonical data, VPS, credentials, exchange or trading state changed. No merge, rebase, reset, cherry-pick, force-push or history rewrite performed.

## Next step

Perform a separate read-only review of the repaired two-file diff against A2.2 §18 and §17, then decide whether the Stage I documentation can be reconciled. Do not dispatch the workflow or proceed to Stage II without separate approval.
