# AI Strategy Contract and TDD RED Preparation — 2026-11-11

## Scope and owner approval

The owner approved recording the independent AI Strategy contract and preparing test-only RED work. This increment is limited to design documentation and tests. It does not include production implementation.

Reviewed source baseline: `6ef0d7456b2791fae73bfea8855ee30482774673`.

## Changes

1. Added `docs/architecture/AI_STRATEGY_CONTRACT.md`.
   - Independent AI signal producer; Core remains RSI + ADX + Smart DCA.
   - Calibrated confidence plus model/calibration/dataset provenance.
   - AI leverage mapping in [1x, 3x], based on required versioned `C_min`.
   - AI ENTRY/DCA sizing from reconciled Account Equity, 1% margin budget, admitted leverage, execution limit price and lot-step floor.
   - AI ledger isolation and common Shared Risk Engine/Kill Switch authority.
   - Explicit approval boundary: no GREEN implementation, numerical `C_min`, calibration training, migration, backtest acceptance, runtime, VPS, deployment or live trading.

2. Added `pipeline/test_ai_strategy_contract_red.py` with five focused test methods in `pipeline/test_ai_strategy_contract_red.py` covering:
   - Missing calibrated confidence.
   - Confidence bounds and non-finite values.
   - Missing calibration provenance.
   - AI ledger leverage supplied as an admitted policy snapshot, independent of generic `LEVERAGE`.
   - Equity-based sizing and fail-closed missing/non-positive equity.

## Exact Git evidence

- Contract documentation commit: `2f498b33953cb3ecf2c66c242000e9e0de2048ce`.
- Initial test-only commit: `e9b39ad8d2492f8e27c1ad0ecf54e168cbbd8bd7`.
- Follow-up test refinement commit: `d0f1b014463e6ad1eff36425a18411233c484ba2`.
- E2E RED test commit: `550a529c2a726f82911602aee207f0df32c78eb9`.
- Latest known source/test SHA for this increment: `550a529c2a726f82911602aee207f0df32c78eb9`.
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- GitHub commit status query for initial test commit returned no status checks. No workflow run or artifact has been verified for the final test SHA.

## Verification and disposition

- Contract recorded: **PASS — documentation only**.
- Test source committed: **PASS — test authoring only**.
- RED execution: **NOT VERIFIED**. The execution environment could not resolve `github.com` for a shallow clone; no local checkout was available. No test result is claimed.
- Syntax/runtime test status: **NOT VERIFIED**.
- AI implementation: **NOT AUTHORIZED / NOT STARTED**.
- Calibration artifact, numerical `C_min`, OOS evidence and minimum calibration sample/period thresholds: **NOT DEFINED / NOT VERIFIED**.
- E2E AI BUY while Core WAIT → AI ledger only → Shared Risk Engine rejection test: added to `paper_execution/test_dual_strategy_api_red.py` at exact SHA `550a529c2a726f82911602aee207f0df32c78eb9`. It asserts the AI order is rejected while account risk is unready and neither Core state nor Core orders change.
- No production source, Core strategy behavior, DB/schema, T0, T1, T2 runtime, VPS, credentials, deployment or exchange state changed.

## Next step

Run both focused RED test files in the repository's GitHub Actions test environment against exact SHA `550a529c2a726f82911602aee207f0df32c78eb9`. Inspect failures and correct test fixtures/specification only. Do not implement GREEN behavior until a separate owner approval is recorded.


## Automated AI Strategy RED workflow and exact-SHA execution — 2026-11-11

### Workflow implementation

- Added `.github/workflows/ai-strategy-contract-red.yml`.
- Workflow creation commit: `be4e59d0ca0c8d764ea2fffe63234d18cd9497fc`.
- Final workflow blob: `c0b82a4d9ef222c836b7081889206e2b4c12459b`.
- Final test source blob: `ec75ead0c27f3b65c58cc04202b4d6b21181f73d`.
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Triggers: push to the existing branch when either focused RED test or an AI decision/API/ledger/risk module changes; manual `workflow_dispatch` is also enabled.
- Runs on Python 3.12, checks out `${{ github.sha }}`, compiles both focused test files, runs the exact unittest command, and uploads logs/preflight as a SHA-named artifact.
- Workflow permissions are read-only (`contents: read`). Exchange/database credentials are explicitly empty. No external exchange services, database, VPS, deployment or live execution is used.
- Artifact retention set to 7 days to match the repository maximum.
- Workflow configuration is separate from production behavior and is not configured as a required branch-protection check.

### Test-only corrections

- Initial workflow run `42988971070` at SHA `be4e59d0ca0c8d764ea2fffe63234d18cd9497fc` stopped at compile because the earlier E2E test contained an escaped double line-continuation character. Artifact `13841105881`, digest `sha256:3354f492fbee54bc221f4f1d7884399f58366c82b0208f70d5787c265b78bbe0`.
- Corrected the test-only line continuations; intermediate commits: `14e532d4f3de6bcdec8c73c079e5521835cd1ff7`, `084b13df016dcc455f9567b9898420e7e9f91c4c`.
- Reworked test expectations for not-yet-existing API parameters to fail as explicit contract assertions instead of uncaught `TypeError` exceptions.
- Added an AI ledger [1x,3x] leverage-bound test and initialized its dual-ledger fixture before testing. Test-only commits: `0c049a9b37c69cefb6a5117531c64ac579075f5e`, `747dba7e0b264547b72edc52c941357362696804`, final `aa7897520b5435ff4c981b3f2ab8a6710f811eea`.
- No production implementation was changed.

### Final focused RED run

- Workflow run: [42989566675](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42989566675).
- Exact source SHA: `aa7897520b5435ff4c981b3f2ab8a6710f811eea`.
- Preflight: PASS (paper-only, empty exchange/database credential variables, no external services).
- Dependency installation: PASS.
- Python compile of both RED test files: PASS.
- Focused test execution: **36 tests, 23 assertion failures, 0 errors**. Workflow conclusion is failure by design at the RED stage; the failures expose current contract gaps and are not GREEN acceptance.
- The E2E case `test_ai_buy_while_core_wait_routes_only_to_ai_ledger_and_shared_risk_rejects` passed: AI BUY remains available while Core is WAIT, order is routed to AI ledger, shared risk denies admission while account risk is unready, and Core ledger state/orders remain unchanged.
- Current failing contract areas: absent/invalid calibrated-confidence rejection and calibration provenance validation; missing AI leverage admission interface; AI ledger does not enforce the approved 1x–3x domain (0.99x, 3.01x and 13x cases fail the rejection assertions); missing equity-based sizing API; stale/missing equity fail-closed contract.
- Artifact: ID `13841700390`, name `ai-strategy-contract-red-aa7897520b5435ff4c981b3f2ab8a6710f811eea`, digest `sha256:bcddb274a58013060af6293604abee08a5d11d304dc2c4a0e50ebeb852df3445`.

### Existing Dual Ledger regression at the same SHA

- Workflow run: [42989566780](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42989566780).
- Exact source SHA: `aa7897520b5435ff4c981b3f2ab8a6710f811eea`.
- Focused Dual Ledger contract: 238 tests PASS.
- Full `paper_execution` regression: 301 tests PASS.
- Compile and isolated paper-only preflight: PASS.
- Artifact: ID `13841126612`, digest `sha256:aaa0c3c4a9ccd59360c718b2748cfd7077190a84c29dd8e8b298a9ada35963c0`.

### Disposition and next gate

- Automated workflow: **PASS — created, push-triggered, exact-SHA checkout, compile and artifact upload verified**.
- AI Strategy contract RED: **RED CONFIRMED — 23 assertion failures, 0 runtime errors; expected at this TDD stage**.
- E2E AI BUY/Core WAIT/AI-ledger/shared-risk-denial path: **PASS at the isolated test scope**.
- Existing Dual Ledger regression: **PASS — 238 focused and 301 full paper_execution tests**.
- AI GREEN implementation: **NOT AUTHORIZED / NOT STARTED**. Numerical `C_min`, calibration/OOS evidence, migration/cutover, backtest acceptance, feature activation, VPS/runtime, deployment and live execution remain outside approval.
- T0 canonical data, T1 activation, T2 runtime, database state, credentials, exchange state and deployment state were not changed.

Next: review and prioritize the 23 RED assertions, freeze any remaining AI API contract details, and request separate owner approval before GREEN implementation.


## RED failure triage and API boundary proposal — 2026-11-11

- Added proposal-only document: `docs/architecture/AI_STRATEGY_API_CONTRACT_PROPOSAL.md`.
- Proposal commit: `b62f0c3de6e72c5f8419f1cb7da062389a8af80b`.
- Proposal status: **OWNER REVIEW REQUIRED**. It does not amend the owner-approved contract or authorize implementation/test changes.
- Reviewed the exact 23 assertions from run `42989566675` at SHA `aa7897520b5435ff4c981b3f2ab8a6710f811eea`:
  - P0 calibration fail-closed: 17 assertions (missing confidence 1; invalid/non-finite/bool confidence 6; missing provenance fields 10).
  - P0 AI leverage isolation/bounds: 4 assertions (AI ledger factory lacks explicit admitted leverage 1; AI ledger accepts 0.99x, 3.01x and 13x 3).
  - P0 account equity sizing/readiness: 2 assertions (decision function lacks equity/sizing interface; missing/stale equity behavior cannot yet be exercised).
- All 23 are assertion failures; 0 runtime errors. The run is RED by design, not a passing AI contract.
- Existing test's two function-signature checks for sizing/equity are marked as brittle RED sentinels. Proposal recommends replacing them with behavioral tests through a server-created immutable admission context; no test source was changed in this step.
- Proposal recommends keeping `decision.evaluate` pure, receiving a server-created immutable admission context containing versioned AI policy, reconciled account risk, instrument rules and AI-ledger position. The API must submit explicit admitted AI leverage to AI_FREQAI ledger; generic `LEVERAGE` must never be a fallback.
- Additional test coverage still required before GREEN: C_min boundaries/mapping, artifact hash/registry trust, model/dataset/horizon match, temporal leakage/freshness/sample period, lot rounding/minimums, AI-only DCA sizing, Kill Switch/no-partial-reservation, idempotent snapshot replay and Core regression.
- Owner decisions still open: numeric C_min, calibration sample/period/age thresholds, trusted artifact registry, account-risk snapshot provider/freshness contract, instrument-rule source, AI DCA v1 eligibility, and immutable snapshot persistence strategy.
- No production code, RED test source, database, migration, T0/T1/T2 runtime, VPS, credentials, deployment or exchange state changed.

Disposition: **RED triage PASS — analysis/documentation only**. API proposal and unresolved decisions are **PENDING OWNER REVIEW**. GREEN remains NOT AUTHORIZED.


## Owner approval — API Contract design gate — 2026-11-11

- Owner explicitly approved `docs/architecture/AI_STRATEGY_API_CONTRACT_PROPOSAL.md` as the design basis for the next test-only refinement gate.
- Approval recorded in proposal commit: `a7f8ca579ff7990eca3f640e1d496608c0ad36f4`; approved proposal blob: `65c3e5a6102cde6f7d51784fd9638f14aec3269e`.
- **Gate A: APPROVED.** Interface boundaries and behavioral invariants in the proposal are the target for RED test refinement.
- **Gate B: AUTHORIZED — TEST-ONLY.** Replace brittle function-signature introspection sentinels with behavioral API/provider-boundary tests; add deterministic missing-coverage tests. Keep intentional RED failures for missing production behavior. Do not edit production source.
- Numerical `C_min`, calibration sample/period/age thresholds, registry/provider choices, instrument-rule source, AI DCA v1 eligibility and snapshot persistence remain unresolved. Tests may use labeled fixtures for boundary behavior but must not turn fixtures into production defaults or imply owner selection.
- **GREEN: NOT AUTHORIZED.** No production changes, migration/cutover, calibration training/OOS acceptance, backtest acceptance, feature activation, VPS/runtime, deployment, exchange connectivity or live orders.
- No RED test execution or new CI run is claimed by this approval record. The existing RED baseline remains run `42989566675`, exact SHA `aa7897520b5435ff4c981b3f2ab8a6710f811eea`.


## Gate B — RED test-only refinement — 2026-11-11

- Owner approval source: approved API Contract proposal blob `65c3e5a6102cde6f7d51784fd9638f14aec3269e`. Test-only refinement authorized; production changes remain prohibited.
- Test-source commits on the existing branch:
  - `eaf441c97835efba8d7c8d8f25bd01d77b5612d2` — replace signature-introspection checks with decision-boundary behavioral tests and explicit fixture admission context.
  - `ae244d7544a14182ac21dc7853eb55e15a84679e` — exercise invalid execution price through the same decision boundary.
  - `dd1b088a763276f5510f99166ba175c13f70e0d9` — assert Shared Risk Engine rejection leaves no risk reservation in the AI BUY/Core WAIT API integration test.
- Latest test source SHA submitted to the existing branch: `dd1b088a763276f5510f99166ba175c13f70e0d9`.
- Added RED coverage: behavioral admission-context boundary; missing/invalid calibrated confidence and provenance; explicit fixture-only confidence minimum validation and leverage mapping at 1x/3x/interior; malformed artifact hash; temporal ordering/training-cutoff violations; stale calibration and sample/period minimums; equity readiness/freshness/reconciliation; Kill Switch; invalid price and lot/tick/minimum rules; AI ledger admitted leverage isolation and [1x,3x] boundaries; Core fixed 13x regression; no partial risk reservation after Shared Risk Engine denial.
- Fixture `confidenceMin=0.6`, sample minimum `100`, period minimum `100ms`, and calibration age `60000ms` exist only inside test fixtures to exercise boundary behavior. They are not production defaults and do not constitute owner selection of `C_min` or calibration policy.
- Deliberately deferred from test assertions pending unresolved contract/provider decisions: trusted calibration artifact registry identity/lookup; exact model/strategy/training-dataset manifest fields; AI DCA v1 trigger/eligibility; immutable reservation snapshot persistence/idempotent replay contract. No behavior was invented for these unresolved decisions.
- No production files were edited. No database/schema, migration, T0/T1/T2 runtime, VPS, deployment, credentials, exchange state or live-order changes.
- CI status for exact SHA `dd1b088a763276f5510f99166ba175c13f70e0d9`: **NOT VERIFIED**. The GitHub combined commit-status query returned no statuses; available workflow-run lookup did not return push-triggered runs. No test count, workflow run ID or artifact is claimed for this SHA.
- Existing verified RED baseline remains run [42989566675](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42989566675), SHA `aa7897520b5435ff4c981b3f2ab8a6710f811eea`, 36 tests / 23 assertion failures / 0 runtime errors. This is historical baseline only, not verification of the refined suite.

Disposition: **Gate A APPROVED. Gate B TEST SOURCE REFINEMENT WRITTEN; CI NOT VERIFIED. GREEN NOT AUTHORIZED.**
Next: obtain exact push-triggered AI RED workflow run for SHA `dd1b088a763276f5510f99166ba175c13f70e0d9`; inspect compile and test logs, correct only test-source defects, then record exact run/artifact. Stop before GREEN.


## Gate B — exact-SHA GitHub Actions execution — 2026-11-11

- Workflow: [AI Strategy Contract RED run 42991140429](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42991140429).
- Event: push; branch: `feature/t0-centralized-data-feeder-p1-20261101`; exact checkout/source SHA: `dd1b088a763276f5510f99166ba175c13f70e0d9` (confirmed in checkout log and `git rev-parse HEAD`).
- Job: `130424044648` (`Isolated AI Strategy RED contracts`), conclusion FAILURE by design at test execution; setup, checkout, Python 3.12, paper-only preflight, dependency install, compile, and artifact upload all SUCCESS.
- Compile: `AI_STRATEGY_RED_COMPILE=PASS`.
- Test execution: **45 tests, 52 assertion failures, 0 errors**. Expected RED: the decision boundary does not yet accept the approved `admission_context`; AI ledger factory does not yet accept explicit `admitted_leverage`; AI ledger does not yet reject 0.99x/3.01x/13x. Positive BUY/sizing/leverage-mapping assertions remain RED because the production contract is not implemented.
- Regression anchors in the same run: Core fixed-13x regression test **PASS**; AI BUY while Core WAIT → AI-only ledger → Shared Risk Engine rejects unready account → no reservation test **PASS**. Existing API/ledger isolation checks also ran in the same focused module.
- Artifact ID `13841349049`; name `ai-strategy-contract-red-dd1b088a763276f5510f99166ba175c13f70e0d9`; size 4,143 bytes; GitHub-reported digest `sha256:7e2e5048db147243eaade59aebdb01ce0245fdcf1a9062abd7dc416cb7ac64e4`; created `2026-11-11T08:57:39Z`; expires `2026-11-18T08:57:31Z`. Digest is GitHub upload metadata; artifact bytes have not been independently downloaded and re-hashed.
- This is the expected RED outcome, not a GREEN or full acceptance result. Do not edit production code. No C_min production value selected; fixture values remain test-only. GREEN, calibration/OOS acceptance, migration, backtest, activation, VPS/runtime and deployment remain unauthorized.

Disposition: **Gate A APPROVED. Gate B initial behavioral RED suite executed at exact SHA; compile PASS; RED confirmed (45 tests / 52 assertion failures / 0 errors).** The current suite remains subject to test refinement for the precise missing behaviors and unresolved policy/provider boundaries. GREEN NOT AUTHORIZED.


## RED assertion-quality refinement and rerun — 2026-11-11

- Log review of run `42991140429` found that 52 assertion failures were inflated: dependent calibration/equity/sizing tests all received the same synthetic `ADMISSION_CONTEXT_UNSUPPORTED` fallback. This did not establish 52 independent behavioral defects.
- Test-only correction commit `63ee390c17bf32ef8be2842aa2c9f183a4a37785`: make dependent admission-context tests skip when the API is absent; add one explicit behavioral API-boundary RED test that fails when `decision.evaluate` rejects the owner-approved context. This preserves downstream assertions for when the API exists without counting the missing interface repeatedly.
- The first rerun exposed one test helper defect: `evaluate()` did not forward the `book` fixture. Corrected by test-only commit `d37c0d4b554bbdcb936c419ebc134c6a8ff28783`.
- Verified workflow: [run 42991526067](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42991526067), push event, exact checkout SHA `d37c0d4b554bbdcb936c419ebc134c6a8ff28783`, job `130425336828`.
- Setup, exact checkout, Python 3.12, paper-only preflight, dependencies, compile, and evidence artifact upload **PASS**. Compile marker `AI_STRATEGY_RED_COMPILE=PASS`.
- Focused suite: **46 tests, 5 assertion failures, 48 skips, 0 errors**. The 5 RED assertions are: decision boundary rejects `admission_context` (1); AI ledger factory lacks explicit `admitted_leverage` (1); AI ledger accepts out-of-domain `0.99x`, `3.01x`, and `13x` (3). Skips are downstream calibration/equity/sizing/instrument tests whose contract entry point is not yet implemented; these are NOT counted as passing behavior.
- Regression anchors: Core fixed-13x remains **PASS**; AI BUY while Core WAIT → AI-only ledger → Shared Risk Engine rejects unready risk → no reservation remains **PASS**.
- Artifact ID `13842490278`; name `ai-strategy-contract-red-d37c0d4b554bbdcb936c419ebc134c6a8ff28783`; size 3,251 bytes; GitHub digest `sha256:e1f0c8e5c7a9aff58062d7b499b2b7133190c0db710bc3e5a0f6f16d9608b019`; expires `2026-11-18T09:00:26Z`. Artifact payload not independently downloaded/re-hashed.
- Run `42991454332` at SHA `63ee390c17bf32ef8be2842aa2c9f183a4a37785` is superseded as an intermediate test-helper attempt; it reported one helper error and was not accepted as final evidence.
- No production code changed. No C_min production value or calibration thresholds selected; fixture values remain test-only. GREEN, migration, backtest, VPS/runtime, deployment and live execution remain unauthorized.

Disposition: **Gate A APPROVED. Gate B test suite refined; exact-SHA RED verified with 5 meaningful missing-contract assertions, 48 dependent skips, 0 errors.** Remaining skips are intentionally blocked on GREEN implementation/provider contracts; do not treat them as PASS. GREEN NOT AUTHORIZED.
