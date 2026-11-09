# P1.44 — Adversarial self-review of T1 kline decimal preservation fix

Date: 2026-11-09 UTC
Review type: Same-session adversarial code self-review; NOT independent.
Main repository branch: `feature/t0-centralized-data-feeder-p1-20261101`
T1 collector repository: `kenznguyen/binance-futures-collector`
T1 branch: `feature/t1-connection-sidecar-integration-20261107`

## Exact reviewed source and evidence

- T1 branch HEAD at review: `c502fa1032c71c8b34cc09a6c5cca8eb79996d13`.
- `src/utils/csv_writer.rs` current blob: `c41cc7c13fc320e4083058fe6fe5683dc5c213d5`.
- `src/models.rs` current blob: `9b195b921eda2863f3769eaac34b3bd0bae48bd1`.
- Tested implementation checkpoint: `ad03560b6409de3c28688fb25d57fa49aed66a9f`.
- TDD RED run: [42644618882](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42644618882), test-only SHA `c0a8a6fe506d6c8bf4596dbf1e0b8d0c15bf7ae2`, 43 passed / 3 failed as intended.
- GREEN CI run: [42644995874](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42644995874), exact tested SHA `ad03560b6409de3c28688fb25d57fa49aed66a9f`, overall SUCCESS, 5/5 jobs PASS.
- Green run artifact: `13686259637`, digest `sha256:eea348cc8cc370b9368abfc661655fa607aa0cb0ae0d9530ee81e081eecd1e04`.
- Current HEAD `c502fa1...` contains only the two additional decimal-grammar tests and evidence documentation beyond the green implementation checkpoint. Workflow attempts [42645569066](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42645569066) and [42645581768](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42645581768) ended `startup_failure` with zero jobs; current HEAD's additional tests are NOT VERIFIED.

## Five-axis review

### 1. Correctness — PASS at tested implementation checkpoint

- Source decimal strings remain strings through `format_decimal_str`; no binary-float conversion or fixed 12-place normalization occurs before the kline writer.
- `write_kline` validates all eight numeric string fields before opening/creating the file, then writes the exact original lexemes.
- Invalid input returns an error; the regression test asserts no destination file is created.
- The TDD RED run demonstrated precision loss (e.g. `123456789.123456789123456789` became `123456789.123456791043`) and acceptance of invalid/non-finite input before the fix.
- The green run passed the 46-test collector library suite and the remaining CI jobs. The two later lexical edge-case tests are not included in that green run.

### 2. Readability and simplicity — PASS

- No new dependency or generic decimal abstraction was introduced.
- The validator is a small lexical boundary check; it does not parse into a numeric representation or normalize bytes.
- Field-specific error context identifies the rejected kline field.

### 3. Architecture — PASS for the bounded scope

- Raw WebSocket decimal preservation remains at the producer/model boundary.
- Validation and serialization occur at the CSV persistence boundary.
- T0/T2 and the independent T1 sidecar are outside the change.
- `format_decimal_str` is also used by trade conversion; the trade writer retains its existing formatting behavior. This review does not claim that non-kline data types have been migrated to lossless decimal persistence.

### 4. Security and input handling — PASS for numeric CSV fields

- The lexical validator accepts optional sign, decimal point and exponent forms.
- It rejects empty input, malformed syntax, NaN/Infinity, whitespace, commas, quotes and embedded line breaks because they do not match the accepted numeric grammar.
- It does not replace semantic validation of OHLC relationships, non-negative volumes, market identity or exchange provenance; those remain separate contract obligations.

### 5. Performance — PASS

- Validation scans each of eight short decimal strings once and allocates no parsed numeric objects.
- No dependency, network request, database call or blocking work was added to the hot path.

## Findings and limitations

No actionable defect was found in the bounded kline decimal-preservation implementation at the tested source checkpoint.

Explicit limitations:
- Green CI is pinned to `ad03560b6409de3c28688fb25d57fa49aed66a9f`, not the later exact branch HEAD `c502fa1032c71c8b34cc09a6c5cca8eb79996d13`.
- The later malformed/non-finite/exponent grammar edge tests have not executed because the two workflow attempts for the latest head failed before job creation.
- This fix does not implement FINAL_ONLY manifest/product identity, durable publication, target-filesystem proof, Binance REST completeness or consumer-side decimal semantics.
- The artifact is a CI build artifact only; no deployment or runtime activation is authorized.

## Verdict

**DOCUMENTATION/CODE SELF-REVIEW PASS for the bounded kline decimal-loss fix at tested SHA `ad03560b6409de3c28688fb25d57fa49aed66a9f`.** Same-session, NOT independent.

The exact latest T1 branch HEAD remains **NOT VERIFIED** because its two additional test cases have not run. Keep PR #1 OPEN/DRAFT. Do not merge, deploy, activate T1, access VPS, mutate T0/T2, or place orders based on this review.


## Latest test-fixture correction — 2026-11-09

- Corrected the malformed-input edge test so its input contains an actual embedded newline at runtime, rather than the two-character backslash-plus-`n` sequence.
- T1 commit: `bb70a28d21486cb844d6fb8536be310172502abd`.
- Current `src/utils/csv_writer.rs` blob: `6fa31c4b5874f2ca874db47b2cb3c35dfc02953c`.
- This is a test-only change; implementation logic is unchanged from the green tested checkpoint `ad03560b6409de3c28688fb25d57fa49aed66a9f`.
- Workflow run `42645946681` ended `startup_failure` with zero jobs. The exact latest branch HEAD and added test remain NOT VERIFIED. Do not interpret this as a test pass or a test failure.


## Latest GitHub Actions startup investigation — 2026-11-09

- T1 evidence update commit: `4566cffbbcf8495182abbc0d3496fdc65709ac14`; exact current T1 branch HEAD at the end of this investigation: `4566cffbbcf8495182abbc0d3496fdc65709ac14`.
- The evidence update itself triggered two new runs for the exact HEAD:
  - [42646416010](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42646416010), push, `startup_failure`, zero jobs.
  - [42646425898](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42646425898), pull_request, `startup_failure`, zero jobs.
- Both check suites report `latest_check_runs_count=0` and `rerequestable=false`; job listing is empty. Thus no runner step or Rust test was started.
- Workflow file `.github/workflows/ci.yml` is unchanged at blob `8329039c807d63cf6834ca9c85fbd0cd99e474d4`; it has the expected push and pull_request triggers. There is no path filter or job-level conditional that explains the zero-job runs.
- The connected GitHub tools expose rerun-failed-jobs and rerun-single-job operations, but no full-workflow rerun operation. Since these runs contain zero jobs and are not rerequestable, a rerun is not available through the current authorized connector.
- Verdict unchanged: source implementation is green-tested at `ad03560b6409de3c28688fb25d57fa49aed66a9f`; added lexical edge tests and latest T1 branch HEAD `4566cff...` remain NOT VERIFIED. This is an Actions platform/startup blocker, not evidence of source test failure.
- No workflow change, PR merge, branch creation, issue retarget, deployment, VPS/runtime operation, T1 activation, T0/T2 mutation or destructive operation was performed.
