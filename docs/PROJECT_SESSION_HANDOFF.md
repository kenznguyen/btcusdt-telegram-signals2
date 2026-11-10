## Runtime verification continuation — SSH preflight recovered, deeper acceptance still pending (2026-11-10)

- Owner confirms SSH preflight is now working. Repository evidence independently confirms run [42814402445](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42814402445): contract job `129823665846` SUCCESS; authenticated read-only SSH job `129823736309` SUCCESS; manual isolated acceptance job `129823667801` SKIPPED.
- Exact workflow checkout/source SHA: `8ad36cae8aa971a537a6f363902f86046aa32e5e`. Remote deployed checkout SHA reported by the forced command: `9ae2eeae4ece3d657781b68e96b6f4509cd95f24`.
- Remote read-only snapshot: host `btcquant-t0-t1-test-01`; SSH user `ubuntu`; Feeder PIDs `22045,22046`; API 8788 bound to `127.0.0.1:8788` (`LOOPBACK_ONLY`); SQLite `PRAGMA integrity_check=ok` (`SQLITE_INTEGRITY=PASS`). No remote write/restart was performed.
- Artifact ID `13762564163`, name `p1-scaleway-ssh-preflight-42814402445`, SHA-256 `f6303919c69b05d412722492f05b8dd3aefa1a655043fa98029a94fee5ee8c28`, expires `2026-11-17T12:16:53Z`.
- This successful preflight supersedes the earlier SSH authentication failure in run `42792435714` for connectivity status. It is a point-in-time read-only snapshot only; the installed forced command currently checks hostname/user, Git SHA, matching Feeder process command lines, API listener binding and SQLite integrity.
- Runtime checks not yet covered: authenticated `/health` and `/v1/candles` response from the VPS, candle freshness/coverage against current time, current SQLite lease owner/generation/expiry, recent candle watermark progression over an observation interval, and Feeder/API stability over time. The manual acceptance job was skipped; therefore these remain NOT VERIFIED.
- Existing workflow has no dedicated live-runtime acceptance gate. The GitHub Actions integration available in this session can inspect runs/logs/artifacts and update repository files, but does not expose a workflow-dispatch action. No fresh run was triggered in this session.
- Safe next stage: prepare a narrowly allowlisted read-only runtime acceptance contract and tests in the existing branch; first inspect SQLite schema and current lease/freshness invariants from source. Do not expand the VPS forced command, copy/install a script, change `authorized_keys`, restart processes, write the canonical DB, activate T1 or place orders without separate explicit approval.
- Current disposition: SSH authentication/connectivity **PASS at the time of run 42814402445**; process/listener/integrity baseline **PASS at that snapshot**; full T0 runtime acceptance **NOT VERIFIED**. T1 remains NOT ACTIVATED; PostgreSQL remains PARKED; `AI_EXECUTION_ENABLED=false`; paper-only.

---
## G1–G3 evidence review and next blocker (2026-11-10)

- Reviewed final G3 workflow, contract assertions, integration fixture and component test inventories against run `42818787474` and source SHA `fa75ed84f6a4f84bc936d8f20d0e971d872d00d1`.
- G3 evidence is internally consistent: 15 workflow/isolation contract tests + 2 end-to-end integration tests + 10 sync tests + 13 API tests + 45 T2 HTTP consumer tests = **85/85 PASS**. API tests explicitly cover missing auth/store fail-closed without DB creation, read-only methods, invalid/unbounded parameters, contract identity and freshness. Sync tests cover exact futures market, exchange clock, bounded pagination, open/out-of-window candles, gaps, invalid pages and no partial commit. Consumer tests cover Bearer auth/no token in URL, strict identity/coverage/freshness, transport limits, retry bounds, no redirects and disabled native-order signals.
- G3 end-to-end test is deliberately narrower than all component tests: M15 only, two synthetic candles, loopback WSGI and the actual T2 HTTP adapter. It tests complete provenance and gap fail-closed; it is not T1 integration, H1 parity, real Binance validation or runtime availability.
- Review disposition: **G1/G2/G3 repository-level CI evidence accepted as PASS; no new code change or runtime inference made in this review.** Artifact `13766236420` expires `2026-11-17T12:47:45Z`; preserve/download it before expiry if long-term evidence retention is required.
- Separate operational blocker remains from SSH preflight run `42792435714`: authentication rejected (exit 255); no forced-command output or VPS state was obtained. Before any G4/runtime acceptance, owner must independently compare the fingerprint derived from the exact GitHub `SCW_SSH_PRIVATE_KEY` with the intended restricted `authorized_keys` entry and confirm SSH username. Do not disclose private key/passphrase. No workflow rerun, key rotation, secret update, `authorized_keys` edit, SSH shell or remote command is authorized by this handoff; each requires separate explicit approval.
- Next permitted work: evidence-only alignment review of key fingerprint and SSH username, without sharing private key material or reconnecting to VPS. Until that blocker is resolved and a new explicit approval is given, G4 runtime acceptance remains BLOCKED/NOT AUTHORIZED; T0 runtime, deployed API/Feeder and canonical SQLite remain NOT VERIFIED.

---
## Latest T0 G3 automation — isolated T0 → T2 data flow (2026-11-10)

- Owner approved G3: synthetic exchange sync → disposable SQLite → read-only T0 Candle Contract v1 API → T2 HTTP consumer. G3 is separately path-scoped and requires G1 and G2 PASS in the same workflow run. G2 is deliberately re-run for G3-surface changes so G3 cannot pass with a skipped G2 prerequisite.
- Existing branch retained: `feature/t0-centralized-data-feeder-p1-20261101`; no PR/branch split.
- G3 integration test added in commit `f07f321a840ceace2f91072faab95a03c6b84bbe`; final test blob `f49eab3d4d003e1f0f120c4b860c5bf57acc6163`. Two end-to-end tests cover complete data provenance and fail-closed behavior for incomplete/gapped SQLite coverage.
- G3 integration uses a synthetic Binance USD-M exchange fixture, temporary SQLite DB, actual T0 WSGI application served over ephemeral `127.0.0.1` loopback HTTP, and the actual T2 `CandleHttpClient`/`canonical_context`. It does not call Binance, use exchange credentials, or access VPS/canonical DB.
- Workflow G3 automation commit `470fdbb7bd5a46b04f93bad77faa3ef9a6901a87`; final workflow blob `db82b15bdb9b56d26e030e898fb819ebabec9853`. Workflow contract tests expanded in commit `fa75ed84f6a4f84bc936d8f20d0e971d872d00d1`; final contract-test blob `bf96faa6f51e156b7f1391584e5b501c1a6cf39e` (15 contract tests).
- Automatic sequencing: `sqlite-data-flow-auto` requires `sqlite-lease-fencing-auto.result == success`, `sqlite-recovery-auto.result == success`, and path-scoped `data-flow-change-scope.outputs.changed == true`. G3 uses GitHub-hosted runner, read-only `contents: read`, exact source SHA checkout, full history only for change evidence, `persist-credentials: false`, blank production DB/API-key/token env, loopback-only test HTTP, and its own source SHA/log/verdict artifact.
- Final workflow run: [42818787474](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42818787474), event `push`, branch `feature/t0-centralized-data-feeder-p1-20261101`, source SHA `fa75ed84f6a4f84bc936d8f20d0e971d872d00d1`, conclusion **SUCCESS**.
- Final G1 job: 15 workflow/isolation contract tests PASS + 55 lease/fencing/write-gateway/lifecycle tests PASS. Artifact ID `13765818716`, name `t0-sqlite-lease-fencing-auto-42818787474`, SHA-256 `c4bee43f6b83955296137bfc00a32443e86cf945a955c0545ce01672f46ca45e`; [artifact](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42818787474/artifacts/13765818716).
- Final G2 job: 64 recovery/scheduler/startup lifecycle tests PASS; verdict `SQLITE_RECOVERY=PASS`. Artifact ID `13765618170`, name `t0-sqlite-recovery-auto-42818787474`, SHA-256 `b533905a6a95c451f6a750ac2999b2198a939a178668ea6fd44a82a02a643038`; [artifact](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42818787474/artifacts/13765618170).
- Final G3 job: **85/85 PASS** (15 workflow contracts, 2 end-to-end integration tests, 10 sync tests, 13 API tests, 45 T2 HTTP consumer tests); verdict `SQLITE_T0_TO_T2_DATA_FLOW=PASS`. Artifact ID `13766236420`, name `t0-sqlite-data-flow-auto-42818787474`, SHA-256 `a52e500812e216e2cbeebfa72391cb33ef3f72ed9c3beee98c17660684941f3c`; [artifact](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42818787474/artifacts/13766236420).
- An earlier workflow revision/run `42818706718` also passed the 80-test G3 suite before the G3-specific workflow contract assertions were added. Final run `42818787474` reran all gates on the final source SHA and passed 15 contract tests, G1, G2 and G3.
- Disposition: **G1 CI PASS; G2 CI PASS; G3 CI PASS** for isolated repository-level contracts. Runtime/VPS state, deployed API process, current canonical SQLite contents, actual Feeder continuity and real production data freshness remain **NOT VERIFIED**. No inference from CI PASS to deployed runtime PASS.
- No SSH/VPS operation, canonical SQLite access/change, Feeder/service operation, T1 activation, PostgreSQL work, T2 strategy/trading change, live order or data deletion occurred. `AI_EXECUTION_ENABLED=false`; paper-only; no live orders; T1 NOT ACTIVATED; PostgreSQL/TimescaleDB PARKED.
- Next decision: owner review of G1–G3 evidence before authorizing any further gate. Candidate follow-on scopes must be approved separately; do not start VPS/runtime acceptance, activate T1, or alter canonical data automatically.

---
## Latest T0 G2 automation — SQLite recovery (2026-11-10)

- Owner approved a separate G2 recovery gate, isolated from VPS/canonical SQLite and dependent on G1 lease/fencing PASS.
- Existing branch retained: `feature/t0-centralized-data-feeder-p1-20261101`; no PR/branch split.
- Final workflow change commit: `ebd3ff51577c80653e9378153927f7705193c19a`; final workflow blob: `0b8bccfaf03809e591c92b0c5ada0f0c21c8deea`.
- Recovery gate was introduced in workflow commit `00cedf0e5dfd9fd78ed654519e714999177ac365`; follow-up scope and full-history checkout corrections are included in final commit `ebd3ff51577c80653e9378153927f7705193c19a`.
- Workflow contract test commits: correction/deduplication `bd65e14ecc6876447bfe4be668025028c373b5d1`; recovery-scope assertion `fbaaa02e95f1740423198766383886db05667341`; final test blob `8c7a5e5f735ff05f0726ac26c4118dd02bf3a684`.
- Automatic G2 sequence: `recovery-change-scope` checks push/PR changed paths; `sqlite-recovery-auto` requires successful `sqlite-lease-fencing-auto` and `recovery-change-scope.outputs.changed == true`. Scope includes workflow, recovery/lifecycle implementation and tests, and the workflow contract test. PR/push filters include recovery source/test paths.
- G2 runs only on GitHub-hosted disposable runner with read-only `contents: read`, exact source checkout, `fetch-depth: 0` for diff evidence, `persist-credentials: false`, empty DB/API-key environment variables, no SSH secrets/environment, and uploads source SHA, changed-path evidence, tests and verdict.
- G2 suite: `market_data.test_feeder_recovery`, `market_data.test_feeder_scheduler`, `market_data.test_feeder_lifecycle`; final result **64/64 PASS**. Coverage includes chronological/aligned gap recovery, coverage recheck and fail-closed behavior, scheduler watermark behavior, restart recovery before readiness, lease renewal and takeover during paged recovery, and real temporary-SQLite integration with synthetic exchange fixtures.
- Final workflow run: [42817869706](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42817869706), event `push`, branch `feature/t0-centralized-data-feeder-p1-20261101`, source SHA `ebd3ff51577c80653e9378153927f7705193c19a`, conclusion **SUCCESS**.
- Final G1 job: 10 workflow contract tests PASS + 55 lease/fencing/write-gateway/lifecycle tests PASS. Artifact ID `13765172690`, name `t0-sqlite-lease-fencing-auto-42817869706`, SHA-256 `ce3eb85efc6197743f630181ba232d857ca6044927152e5f1d4eacd68d86e0d2`; [artifact](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42817869706/artifacts/13765172690).
- Final G2 job: 64 recovery/scheduler/lifecycle tests PASS; verdict `SQLITE_RECOVERY=PASS`. Artifact ID `13765782460`, name `t0-sqlite-recovery-auto-42817869706`, SHA-256 `32b4d61ad94bda605b489e22a37eb565f35ab232b65f0be8fb043bf1725ed105`; [artifact](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42817869706/artifacts/13765782460).
- Intermediate failed attempts were not treated as PASS: run `42817517277` exposed an over-escaped contract assertion; run `42817725074` exposed a shallow-checkout `fatal: bad object` when G2 recorded the push diff. Contract assertion was corrected and G2 checkout now fetches full history. Final run `42817869706` validates the corrected workflow and both gates. Earlier malformed intermediate workflow revisions were replaced by the final read-back-verified workflow; no T0 runtime/source data was changed.
- Disposition: **G1 AUTOMATED CI PASS; G2 AUTOMATED CI PASS** for isolated tests. This is not proof of current VPS recovery, live lease ownership, canonical DB state, deployed Feeder readiness or production data continuity. Runtime acceptance remains **NOT VERIFIED**.
- G3 end-to-end data flow remains deferred. Next step: define a separate isolated G3 data-flow gate (Feeder sync contract → disposable SQLite → read-only API → consumer contract), requiring G1 and G2 PASS; do not access VPS or canonical DB.
- No SSH/VPS operation, canonical SQLite access/change, Feeder/service operation, T1 activation, PostgreSQL work, T2/strategy/trading change, live order or data deletion occurred. `AI_EXECUTION_ENABLED=false`; paper-only; no live orders; PostgreSQL/TimescaleDB PARKED.

---
## Latest T0 G1 automation — SQLite lease/fencing (2026-11-10)

- Owner approved converting G1 from manual-only to automatic execution on path-scoped `push` and `pull_request` events. Existing `workflow_dispatch` gate `sqlite-lease-fencing` remains available.
- Existing branch retained: `feature/t0-centralized-data-feeder-p1-20261101`; no branch/PR split.
- Workflow automation commit: `c1ce31f5d74b68c558a0354ca7eb1f9494bbd0ea`; workflow blob at that commit: `950b9d183f98fa7ac17916cab5819135e5185e53`.
- Follow-up workflow-contract execution commit: `df1a58f33be66c36d932e1c16f934b0895841421`; final workflow blob: `a4a285491861b958e8e62ce82c55296c4b1e5887`.
- Contract tests added in `ci/test_t0_ssh_preflight_contract.py`: test commit `a0a06467024ff9bac9af7e8b0dea9d669e8a73df`; false-positive scope correction commit `56c3130d81a9413f5f4f32607a62d6796e95170a`; final test blob: `a646c381d600bfccaadc472280729ac590042367`.
- Trigger scope is limited to the existing feature branch for push, and to PRs with changes in the workflow, contract test, T0 lease/write/lifecycle source or the three corresponding test modules. The automatic job uses a GitHub-hosted disposable runner, read-only contents permission, no SSH environment/secrets, empty DB/key environment variables, exact checkout SHA, and uploads source SHA + test logs + verdict.
- Final automatic run: [42816562930](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42816562930), event `push`, branch `feature/t0-centralized-data-feeder-p1-20261101`, source SHA `56c3130d81a9413f5f4f32607a62d6796e95170a`, conclusion **SUCCESS**.
- Job `Automatic isolated SQLite lease and fencing tests`: **PASS**. Workflow trigger/isolation contract: 7 tests PASS. G1 lease/fencing/write-gateway/lifecycle suite: 55 tests PASS. Verdict `SQLITE_LEASE_FENCING=PASS`.
- Artifact: `t0-sqlite-lease-fencing-auto-42816562930`; artifact ID `13764396878`; SHA-256 `c4b8c9fb630ed4ca5012ceed6ce9c566d67fe34d9022b6544fd7222f1e005df8`; [artifact page](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42816562930/artifacts/13764396878).
- An intermediate run `42816455084` failed only because the new contract test searched beyond the G1 job into unrelated SSH job configuration; the assertion was narrowed to the G1 job and final run `42816562930` passed. Earlier run `42816359160` independently recorded 55/55 G1 tests PASS before the contract-test step was added.
- Disposition: **G1 AUTOMATED CI GATE PASS** for isolated SQLite lease/fencing/lifecycle contracts. This is not proof of current VPS lease/fencing state or deployed runtime acceptance; VPS/runtime/DB were not accessed.
- G2 recovery and G3 end-to-end data-flow gates remain deferred. No SSH/VPS operation, canonical SQLite access/change, Feeder/service operation, T1 activation, PostgreSQL work, T2/strategy/trading change, live order or data deletion occurred.
- Next step: review G1 CI evidence, then define/approve a separate isolated G2 recovery gate. Do not infer recovery or data-flow PASS from G1.
- Safety posture unchanged: `AI_EXECUTION_ENABLED=false`; paper-only; no live orders; T1 NOT ACTIVATED; PostgreSQL/TimescaleDB PARKED; T0 canonical SQLite protected.

---

## T0 → T2 repository source parity review (2026-11-10)

- Read-only comparison record: `docs/evidence/T0_T2_REPOSITORY_SOURCE_PARITY_REVIEW_2026-11-10.md`; creation commit `7e2080c2410fe8ab889338684390eed453535069`; verified report blob `204cd41aefc38abaf33838b1723c4d84533d0818`.
- Compared historical runtime T0 source commit `9ae2eeae4ece3d657781b68e96b6f4509cd95f24` with branch HEAD before this report `1b1b4d49c1af9ae63d75343774df229d1249f02e` (GitHub compare: ahead 828, behind 0).
- Thirteen inspected runtime-relevant blobs are identical: T0 API/feeder/feeder_service/storage, T2 context/http client/research config, T0 API/storage tests, T2 context/http tests, and T2 HTTP consumer + Freqtrade smoke workflows. Exact blob IDs are in the report.
- Only `market_data/README.md` differs among the selected paths: historical blob `660a2f0f4f88c0de4fa8c1be3c4af96df282de0e`; current blob `d90f84f8135c8ab9da1b57863e145d86565bf179`. The change is documentation-only and clarifies loopback topology / no public reverse proxy required for same-host T0→T2.
- Disposition: inspected repository source parity PASS; current VPS checkout SHA, service configuration/listener state, environment and process-loaded byte parity remain NOT VERIFIED. Static Git blob equality does not attest deployed runtime.
- No tests, compile, Actions dispatch/artifact, SSH/VPS/runtime/DB/network/provider probe, source/test/workflow/dependency change, service operation, T1 activation, trading or data mutation occurred.
- Next step: use owner-supplied current sanitized VPS checkout SHA, service unit/command, loopback listener and redacted T0/T2 environment/config evidence to close documentary parity. Only propose a bounded read-only probe if evidence remains insufficient and obtain separate approval.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders. T1 NOT ACTIVATED; PostgreSQL/TimescaleDB PARKED. Option C REVOKED; no destructive authority implied.

---
## T0 → T2 historical runtime evidence reconciliation (2026-11-10)

- Corrective record: `docs/evidence/T0_T2_DEPLOYMENT_PARITY_EVIDENCE_RECONCILIATION_2026-11-10.md`; branch commit `987c245a9e6dec3e1aa169458280399f6d1bc70c`; readback blob `25aa2cae62fb7a693bc31d80a359fe304555e7ad`.
- Corrects the new checklist's intake status: prior operator-provided runtime evidence dated 2026-11-09 already exists in `docs/evidence/t2/T0_T2_LOOPBACK_RUNTIME_VERIFICATION_2026-11-09.md` (blob `568b7d2c5ba6f606221519aba7ee4b298dff34c8`) and the deployment gate (blob `4919abb30afc5f6fd7a98e013633d1e19d112325`).
- Historical bounded gate result: loopback API at `127.0.0.1:8788`; `/health` 200; missing token 401; authenticated M15/H1 reads 200; each returned 2/2 complete closed VALIDATED candles; M15 ingestion lag 8,558 ms under 120,000 ms; one-shot T2 2-bar M15 context command exit 0 and JSON parse PASS.
- Historical T0 source SHA `9ae2eeae4ece3d657781b68e96b6f4509cd95f24`; T2 context file SHA-256 `e22d6c7d186b1fb9a5079eb9b4224c8acbcd835a0938dc970e9bc4b072eb75d3`. Process-loaded byte identity was not independently attested. T2 artifact stayed local at `/tmp/t2-canonical-window-20261109T112946Z.json`; no GitHub Actions artifact/run exists for this operator-run gate.
- Corrected status: historical bounded T0→T2 loopback gate = PASS; current deployment parity on 2026-11-10 = PARTIAL / NOT VERIFIED because current VPS source SHA, service/listener state, environment/token state and current data freshness have not been re-established. Do not repeat historical success as current-state proof.
- T1 remained NOT ACTIVATED in that gate. No broader Freqtrade runtime activation, strategy/model training, signal publication, ledger/risk change, live order or data deletion occurred.
- No new VPS/SSH/runtime/DB/network probe, test, compile, Actions dispatch or artifact upload was performed for this reconciliation.
- Next step: compare historical evidence with owner-supplied current sanitized source/service/config evidence; propose a new bounded read-only check only if needed and separately approved.
- `AI_EXECUTION_ENABLED=false`; paper-only; PostgreSQL/TimescaleDB PARKED. Option C REVOKED; no destructive action authority implied.

---
## Latest T0 → T2 deployment parity evidence checklist (2026-11-10)

- Added `docs/evidence/T0_T2_DEPLOYMENT_PARITY_EVIDENCE_CHECKLIST_2026-11-10.md`.
- Checklist commit: `d91dbeffc40b96059b865d3700eb811588c6573b`.
- Defines owner-supplied sanitized evidence for T0/T2 exact source SHAs, API bind/port, T0 SQLite ownership, token presence without disclosure, T2 endpoint and explicit 120,000 ms lag threshold, service identity/status, and any alternate data paths.
- Adds gates G1–G5 for documentary source/config/endpoint/storage/contract parity; G6 is a bounded non-destructive read test requiring separate explicit approval.
- Reconciles transport behavior: T2 code accepts HTTPS for non-loopback and HTTP only for localhost/127.0.0.1/::1; T2 README describes HTTPS. Actual endpoint/topology parity remains NOT VERIFIED.
- Deployment parity remains NOT VERIFIED. No owner-supplied evidence, VPS/SSH/runtime/DB/network probes, tests, compile, Actions dispatch or data changes were performed.
- Next step: collect the six sanitized evidence categories in the checklist; omitted items remain NOT VERIFIED. Do not access VPS or run operational tests without separate approval.
- Option C remains REVOKED; this does not grant destructive authority. VPS operational-data lifecycle cleanup remains a separate proposal.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders; PostgreSQL/TimescaleDB PARKED.

---
## Latest T0 → T2 synchronization review (2026-11-10)

- Added `docs/evidence/T0_T2_HTTP_SYNCHRONIZATION_CONTRACT_REVIEW_2026-11-10.md`.
- Review commit: `f2032ffaa50a8c67beeef4d1710a8c9b7412bf1e`.
- Review records the exact T0 API / T2 HTTP consumer source blobs and confirms the intended same-host loopback topology: T0 read-only API at `127.0.0.1:8788`, T2 `CandleHttpClient`, no local SQLite or exchange fallback in the inspected T2 context path.
- T2 adapter is currently M15-only with a maximum 32-candle context; T0 also exposes H1, but the inspected FreqAI research configuration is M15-only. No H1 consumer change is implied.
- `T0_CANDLE_MAX_LAG_MS=120000` is applied to `latestAvailableAtMs - latestCloseTimeMs`, not observation age or close lag. Feeder source schedules with 5-second close grace and 5-second polling; this supports a nominal 5–10 second scheduling contribution, but does not establish measured production latency. 120 seconds remains an explicit fail-closed ceiling, not a production SLA.
- Historical T2 migration validation is recorded as 45 + 11 + 6 = 62 tests PASS at baseline `65fe065ccdc197a51b969da37ce99d5414201a92`; current review did not rerun tests or Actions. Combined status lookup for that commit returned no status contexts; no workflow run/artifact is claimed here.
- Deployment environment, actual T0 API listener/source SHA, deployed T2 consumer path and production freshness distribution remain NOT VERIFIED. No VPS/SSH/runtime/DB/network/provider probes, tests, compile, Actions dispatch or data changes were performed.
- Next step: prepare deployment-parity evidence intake for owner-supplied sanitized T0 API/T2 service configuration. No host access or runtime probe is authorized by this review.
- Current governance correction: Option C — No Destructive Authority — was revoked by the owner on 2026-11-10. This does not itself authorize any destructive operation. T0 canonical data and protected ledgers/audit/recovery evidence remain protected; VPS operational-data cleanup is a separate proposal awaiting classification, retention and execution approvals.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.

---

## Latest T0 simplification — C-01 regression coverage map (2026-11-10)

- Updated read-only report: `docs/evidence/T0_SIMPLIFICATION_ACTIVE_SQLITE_STARTUP_CONFIGURATION_REVIEW_2026-11-10.md`.
- Update commit: `d8fbf57e67afcb146b64246048714961f73e507e`; final report blob `71950724964e5cb29df01b987d858a14b7a8c341`.
- Corrected coverage map: production-builder tests exist for PostgreSQL in `market_data/test_postgres_feeder_runtime.py`; API status/auth semantics are covered in `market_data/test_api.py`; store factory behavior is covered in `market_data/test_storage.py`.
- No equivalent production-builder SQLite branch coverage was identified in the bounded inspected test set. The systemd/API CI script composes `FeederRuntime` directly and does not call `build_production_runtime()`.
- C-01 regression plan now preserves API pre-auth UNCONFIGURED / auth 401 / store 503 ordering, SQLite default/explicit selection and same-file lease invariant, PostgreSQL TLS/host/lease restrictions, per-process owner generation, no implicit DB/schema provisioning, and recovery-before-readiness.
- This is a static coverage map only. Tests NOT RUN; Actions NOT DISPATCHED; full repository-wide caller/trigger coverage NOT VERIFIED. No implementation approval or source change.
- Next step: finish read-only references outside `market_data`; then decide whether C-01 merits a minimal test-first change. Keep T0 canonical SQLite and PostgreSQL PARKED.
- L4-Minimum remains administratively closed BLOCKED / NOT VERIFIED; L4-Extended PARKED. Option C ACTIVE; paper-only; no live orders.

---

## Latest T0 simplification — backend configuration caller/workflow inventory (2026-11-10)

- Expanded read-only review: `docs/evidence/T0_SIMPLIFICATION_ACTIVE_SQLITE_STARTUP_CONFIGURATION_REVIEW_2026-11-10.md`.
- Expanded review commit: `073878c07a640fd4325e04994b4e9d34d11bf0bd`; final report blob `c6728bdcb6fecc332cbf77750ecf52aefc9f4417`.
- Found three reads of `MARKET_DATA_BACKEND`: API preflight in `market_data/api.py`, production backend/TLS/lease selection in `market_data/feeder_service.py`, and store selection in `market_data/storage.py`.
- Important compatibility limit: API preflight precedes bearer authorization/query handling; do not move or reorder it without preserving current HTTP status behavior.
- `build_production_runtime()` is defined and called by `feeder_service.py` main; CI systemd integration composes `FeederRuntime`/ `run_service` directly and does not exercise the production builder.
- Read-only workflow map includes T0 Gateway full market_data regression, T0 systemd/API integration, SQLite sandbox, manual validation, G2, T2 smoke and T2 HTTP consumer workflow. Exact workflow blob SHAs are in the report.
- C-01 remains candidate only; no source implementation approval. Full repository-wide caller/trigger denominator NOT VERIFIED. Tests/compile NOT RUN; Actions NOT DISPATCHED; no run/artifact.
- Next safe step: finish repository-wide references outside `market_data` and map the exact C-01 regression cases, preserving API preflight/auth ordering and SQLite/PostgreSQL fail-closed behavior.
- No code/test/package/workflow/runtime/VPS/DB/provider/secret/permission/network/data changes. L4-Minimum remains administratively closed BLOCKED / NOT VERIFIED; L4-Extended PARKED. Option C ACTIVE; paper-only; no live orders.

---

## Latest T0 simplification — active SQLite startup/configuration review (2026-11-10)

- Read-only review: `docs/evidence/T0_SIMPLIFICATION_ACTIVE_SQLITE_STARTUP_CONFIGURATION_REVIEW_2026-11-10.md`.
- Review commit: `e0b545aab4512da91cf16063472d460e49871fb7`.
- Inspected source baseline: last recorded branch commit before this review `c66c34ab709d6677530c0a745d37791034331651`.
- Exact source blobs: `market_data/feeder.py` `935d295ef42c94482a48ce6ccdc927ebfa4c7e22`; `market_data/feeder_service.py` `bdcecf6bc98a2ff070f83098d2c50154a160c99c`; `market_data/storage.py` `13fe1ae01ebb5318b69e69eef3e512d207f74c49`; relevant tests and README are recorded in the review.
- Mapped ownership: FeederConfig; production environment builder; side-effect-free store factory; runtime composition; FeederRuntime lifecycle; process/systemd readiness.
- C-01 candidate: `MARKET_DATA_BACKEND` is independently parsed in `build_production_runtime()` and `create_store_from_env()`. Candidate only; NOT IMPLEMENTED / NOT APPROVED pending complete caller/workflow inventory and focused production-builder regression matrix.
- Timeframe defaults, retry defaults, close-grace reuse, runtime readiness and systemd readiness were assessed as intentional or not proven harmful; KEEP.
- Bounded source review PASS. Full repository-wide caller/workflow denominator NOT VERIFIED. Tests/compile/dry-run NOT RUN. GitHub Actions NOT DISPATCHED; no run/artifact. Independent review NOT PERFORMED.
- No source/test/package/workflow/runtime/VPS/DB/provider/secret/permission/network/data changes.
- Next safe step: read-only branch-local caller and workflow inventory for `build_production_runtime` and store factory; then define C-01 regression matrix before any implementation approval.
- L4-Minimum remains ADMINISTRATIVELY CLOSED — BLOCKED / NOT VERIFIED; L4-Extended remains PARKED. Option C ACTIVE; canonical SQLite protected; PostgreSQL PARKED; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders.

---

## Latest work — L4-Minimum administrative closure and T0 Core handoff (2026-11-10)

- Administrative closure record: `docs/evidence/T0_L4_MINIMUM_ADMINISTRATIVE_CLOSURE_2026-11-10.md`.
- Closure record commit: `9ae183c586d47bc319369ccda1615c144b8e66b8`.
- Disposition: **ADMINISTRATIVELY CLOSED — BLOCKED / NOT VERIFIED**. This closes the current work cycle only; it is not PASS, technical acceptance, baseline freeze, or owner acceptance.
- L4M-01 remains NOT VERIFIED: no actual owner package inventory, canonical SHA-256 manifest, custody provenance, or exact-object readback evidence.
- L4M-03 remains PARTIAL / NOT VERIFIED: no actual authenticated latest-head anchor, exact digest, custody/readback linkage, or freshness/rollback evidence.
- Other control dispositions remain unchanged. No control promoted; no frozen baseline; no owner acceptance.
- L4-Extended remains BLOCKED/PARKED. Do not create its branch or implement it until L4-Minimum is accepted and frozen.
- Next workstream: resume T0 Core simplification on the existing branch `feature/t0-centralized-data-feeder-p1-20261101`, separate from L4-Extended. Start with bounded source/document inspection.
- No code, test, compile, Actions dispatch, runtime/VPS/SSH/DB probe, storage mutation, or destructive lifecycle operation was performed for this closure.
- Option C — No Destructive Authority — ACTIVE; T0 canonical SQLite protected; PostgreSQL/TimescaleDB PARKED; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Latest closure record commit: `9ae183c586d47bc319369ccda1615c144b8e66b8`. No workflow run or artifact is claimed.

---

## Latest L4-Minimum continuation — owner narrows evidence custody to VPS + GitHub (2026-11-10)

- Owner decision: `docs/decisions/D-2026-11-10-L4-EVIDENCE-CUSTODY-VPS-GITHUB-ONLY.md`; commit `89f7b5a9ba8f6b86b126cf24fa6b4235760878b9`.
- Explicit scope: no additional backup/custody copy outside the project VPS and GitHub is required. No third-party object store or paid external custody service is required.
- Assurance boundary: VPS and/or GitHub are the approved custody locations. Exact package inventory, SHA-256 manifest, custody provenance, authenticated latest-head anchor, signer separation, exact-object readback and digest verification remain required.
- If copies are claimed in both locations, each copy must be read back and digest-checked. A single-location outage recovery claim requires an accessible verified copy in the remaining location.
- Simultaneous VPS + GitHub unavailability is outside the accepted recovery-availability claim. Do not claim recovery for that combined outage.
- GitHub-hosted runners/artifacts remain within the GitHub failure domain and are not independent third-party custody. This decision does not assume VPS/GitHub credentials, administrators, regions or failure domains are otherwise independent.
- Updated acceptance matrix: `docs/evidence/p1-8/L4-MINIMUM-PROVENANCE-ACCEPTANCE-MATRIX.md`, initial commit `294f0134b342f5152b9ab949ecde6cdb5f2e1803`; terminology clarification commit `a4e8fcde9942ef032e261fb3d69e1eef0e64d090`, final blob `75db0d98134fd656d91a8545bc307c56595aebf7`.
- Updated intake contract: commit `a0f0b0771b7f4fe47ac4a07fc20198d053051b19`, blob `3d65bf941b7884010ec79cb6fc23e42998713770`.
- Updated acquisition register: commit `c69fafbf57f6a3b928a7af6a9ca58768f60526c9`, blob `c7605704c5868ef2534017029cef2766e94eca6a`.
- Updated historical non-substitution assessment to mark its former external-custody criterion superseded while retaining technical findings: commit `c35f031852dcfa688e4d2005feb504f14bf6978b`, blob `1fea06d455e020fb3e87d7378c8f95bb127f9c4b`.
- L4M-01 remains NOT VERIFIED pending exact inventory/manifest/custody/readback. L4M-03 remains PARTIAL / NOT VERIFIED pending authenticated latest-head anchor and exact-object freshness evidence. Aggregate L4-Minimum remains BLOCKED / NOT VERIFIED. No control promoted.
- No external storage provisioned or accessed; no VPS/SSH/runtime/DB/provider/key/permission/network operation; no tests, workflow dispatch, run or artifact; no destructive lifecycle operation.
- Option C — No Destructive Authority — remains ACTIVE. T0 canonical SQLite; PostgreSQL PARKED; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Next gate: owner-supplied sanitized evidence for the exact VPS/GitHub custody object(s), manifest and L4M-03 anchor. No external backup is requested.

---

## Latest L4-Minimum continuation — L4M-10 frozen-baseline readiness (2026-11-10)

- Documentary assessment: `docs/evidence/T0_L4M10_FROZEN_BASELINE_OWNER_SELF_ASSESSMENT_READINESS_2026-11-10.md`.
- Assessment commit: `05bfa000db33e933eeb7958b2349bdb4b6f9fe73`.
- Assessment: NOT READY. Baseline NOT CREATED; owner acceptance NOT ISSUED.
- Readiness analysis: L4M-01/02 NOT VERIFIED; L4M-03–07 remain synthetic/design/CI/model/policy partial; L4M-08 DOCUMENTARY PASS ONLY; L4M-09 OWNER-WAIVED / NOT MANDATORY; L4M-10 NOT VERIFIED.
- Defined future-only baseline packaging sequence: package boundary, custody/latest-head anchor, signer/trust evidence, offline verification/readback, tamper-evident history, claim mapping, canonical manifest and digest, non-self-referential baseline identity, freeze gate, owner disposition.
- Defined owner self-assessment safeguards: assessor identity/role, producer/custodian/approver conflict disclosure, nine per-control verdicts and exact baseline ID/digest reference. No independent assurance claim.
- Aggregate L4-Minimum remains BLOCKED / NOT VERIFIED. L4-Extended branch remains BLOCKED.
- No baseline creation/freeze/signing, owner storage access/readback, tests, compile, dry-run, fault injection, Actions dispatch, workflow run/artifact, runtime/VPS/DB/data/secret/permission/network/service changes or destructive operations.
- Option C ACTIVE; T0 canonical SQLite; PostgreSQL PARKED; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Next gate: owner-supplied sanitized L4M-01 custody evidence with L4M-03 authenticated latest-head anchor, then L4M-02 signer-separation evidence.

---

## Latest T0 continuation — launch source revalidation (2026-11-10)

- Revalidated the DEP intake and launch reconciliation references against current branch HEAD `d1617c16da83fc5afd0d97759fbf2666b6d9dffc`.
- Report: `docs/evidence/T0_LAUNCH_CONTRACT_SOURCE_REVALIDATION_2026-11-10.md`.
- Feeder blob `bdcecf6bc98a2ff070f83098d2c50154a160c99c`, API blob `81733c9b6de811cbebb2f5d472d41f37f337990c`, README blob `d90f84f8135c8ab9da1b57863e145d86565bf179`; all match the previously recorded reconciliation references.
- Static assertions PASS: Feeder module entrypoint, post-start READY notification, STOPPING notification, 30-second drain, missing-notify-socket behavior, API health/data routes and 2000-candle limit, Gunicorn target/bind/workers/threads/timeout, same-host loopback and separate remote/browser gateway wording.
- This establishes current repository source/document consistency only. Deployed VPS SHA, unit properties, process identity, listener ownership, API/Feeder readiness and data freshness remain NOT VERIFIED / NOT RUN.
- DEP owner evidence remains NOT SUPPLIED. Old `ops/ssh/t0-readonly-preflight.sh` remains NOT APPROVED for metadata-only collection and was not run.
- No source/runtime/test/workflow/VPS/SSH/DB/data/secret/permission/network changes; no tests or Actions dispatch. No workflow run/artifact is claimed.
- Option C ACTIVE; canonical T0 SQLite retained; PostgreSQL PARKED; `AI_EXECUTION_ENABLED=false`; no live orders.
- Next step: receive sanitized DEP-01–DEP-09 owner evidence and reconcile exact deployed facts. No host access or runtime probe is authorized.

---

## Latest T0 continuation — DEP intake preparation and deployment contract status (2026-11-10)

- Latest baseline before this continuation: `fa65e4d5e4817be1273f4f5646d4c526357975ec`; active branch remains `feature/t0-centralized-data-feeder-p1-20261101`.
- Completed T0 static preflight audit: `docs/evidence/T0_READONLY_PREFLIGHT_STATIC_SAFETY_AUDIT_2026-11-10.md`. The old `ops/ssh/t0-readonly-preflight.sh` is NOT approved as a metadata-only DEP collector because it reads process command lines and runs SQLite `PRAGMA integrity_check`. Script was not run or changed.
- Completed Feeder/Candle API launch contract reconciliation: `docs/evidence/T0_DEPLOYMENT_LAUNCH_CONTRACT_RECONCILIATION_2026-11-10.md`.
- Clarified `market_data/README.md`: same-host T0 → T2 uses loopback `127.0.0.1:8788` and does not require Nginx/reverse proxy; remote/browser access is a separate design/approval scope.
- Previous reconciliation commit: `fa65e4d5e4817be1273f4f5646d4c526357975ec`.
- Current source launch contracts: Feeder `python -m market_data.feeder_service`; Candle API Gunicorn `market_data.api:application` bound to `127.0.0.1:8788`. Feeder source emits `READY=1` / `STOPPING=1`; actual systemd `Type` / `NotifyAccess` and effective unit properties are host evidence, not inferred.
- Added next-step template: `docs/evidence/T0_DEP01_DEP09_OWNER_EVIDENCE_INTAKE_2026-11-10.md`. It is a blank intake sheet, not host evidence.
- DEP-01–DEP-09 owner evidence remains NOT SUPPLIED; deployment parity NOT VERIFIED; operational readiness NOT VERIFIED.
- No VPS/SSH access, preflight execution, systemd/Nginx/API probe, DB/data/secret access, service/runtime/network change, tests or GitHub Actions dispatch. No workflow run/artifact is claimed.
- Option C — No Destructive Authority — ACTIVE; T0 remains canonical SQLite; PostgreSQL PARKED; `AI_EXECUTION_ENABLED=false`; no live orders.
- Next step: wait for owner-supplied sanitized DEP-01–DEP-09 evidence, then compare against the launch contract and record only evidence-supported discrepancies. Do not infer host parity or initiate host access.

---

# Project Session Handoff

Updated: 2026-11-09 UTC  
Active branch: \`feature/t0-centralized-data-feeder-p1-20261101\`

## Latest completed work — P1.8.22 / P1.8.23

- P1.8.22: existing synthetic Ed25519 verifier and negative tests were audited; no duplicate signing helper was retained.
- P1.8.23: added a file-backed synthetic SQLite test for duplicate observer ACK, process death after durable checkpoint write/before checkpoint ACK, reopen, duplicate ACK replay, and idempotent checkpoint ACK recovery.
- Final source SHA tested by CI: \`082cc68b14148829c01fc63558f6781fa006756b\`.
- GitHub Actions run: [42557957929](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42557957929), SUCCESS, 3/3 jobs PASS, 162/162 tests PASS.
- Primary artifact: \`13648297207\`; independent verification artifact: \`13648187759\`; both expire \`2026-11-16T03:43:37Z\`.
- Attested bundle SHA-256: \`283f807f92850893b7cb0aa180b84c1c7673590f754837d94258c0559984143b\`.
- Evidence record: \`docs/evidence/p1-8/082cc68b14148829c01fc63558f6781fa006756b/P1.8.23.md\`.
- Workflow archive commit: \`50f06a49ea391674b31cc561ade0b00363bd8a89\`.
- Evidence record commit: \`90409fc1e0bb30ad4aceea31c8b58c5eec991f01\`.

## Fault-vector status

All 13 catalogued fault/negative vectors now have executable synthetic test coverage: 13/13 PASS, 0 PARTIAL, 0 MISSING. This includes invalid signature, unknown signing key, revoked signing key, checkpoint boundary, recovery, and Root B duplicate ACK/crash.

Production evidence remains NOT VERIFIED for all 13 vectors. The file-backed SQLite adapter is a synthetic reference model only; no production Root B, key-management, database, feeder, exchange, ledger, strategy, or runtime integration has been performed.

## Operating boundaries

- \`AI_EXECUTION_ENABLED=false\`; no live orders.
- Do not modify T0/T1, VPS, DB, Feeder, production runtime, exchange, ledger, strategy, or risk engine without separate explicit approval.
- No PR or merge was created.
- Continue to use GitHub Actions for validation and retain evidence on the existing branch.
- Any future production integration or change to assurance claims requires separate explicit approval.

## Latest completed work — P1.8.26

- Designed an isolated staging Production Verification Protocol for all 13 fault/negative vectors.
- Protocol: `docs/evidence/p1-8/P1.8.26-production-verification-protocol.md`.
- Scope includes prerequisites, per-vector procedure and PASS criteria, durability/storage, concurrency, key lifecycle, business-state reconciliation, evidence package contract, stop gates, and explicit prohibitions.
- Protocol document commit: `3910544269aa2b759df28183efcbde491fe64d70`; final handoff commit / branch HEAD: recorded by the commit that updates this handoff.
- Protocol blob SHA: `863707a63f21327b83f5ee1511b72eae871623de`.
- GitHub check-runs queried for protocol commit: 0; commit status: pending with no status contexts. No workflow run or artifact is claimed for P1.8.26.
- Status: DESIGN COMPLETE; NOT EXECUTED. All 13 vectors remain synthetic PASS / production NOT VERIFIED.
- No production implementation, runtime integration, destructive fault injection, VPS/T0/T1/DB/Feeder/exchange/strategy/ledger/risk changes, PR, or merge.
- Next step: independent review of protocol completeness and environment equivalence criteria before separately approving any isolated staging execution.

## Latest completed work — P1.8.28

- Added `docs/evidence/p1-8/P1.8.28-verification-criteria-environment-equivalence.md`.
- Document commit: `d14b512e6f8b146dabf0fbb08fe0462610df674a`.
- Defined a production/staging environment equivalence matrix covering application, database, transactions, durability, storage, topology, concurrency, identity/key management, time, network, backup/restore, observability, and CI evidence.
- Added measurable minimum deterministic coverage for V01–V13, separate D0–D4 durability claim levels, explicit revocation and checkpoint timestamp contracts, reconciliation fixture requirements, and provisional staging RPO/RTO targets requiring owner approval.
- Added pre-execution/abort checklist and evidence manifest extensions.
- Status: DESIGN COMPLETE; NOT EXECUTED. Environment equivalence NOT VERIFIED; staging BLOCKED / NOT AUTHORIZED; production NOT VERIFIED.
- No source/runtime changes, staging provisioning, fault injection, workflow dispatch, PR, or merge. No CI run or artifact is claimed.
- Next step: independent review of P1.8.28; obtain explicit owner decisions for revocation policy, checkpoint membership policy, and proposed RPO/RTO before any staging execution proposal.

## Latest completed work — P1.8.29

- Completed independent static review of P1.8.26 and P1.8.28; recorded findings F01–F10 and owner decision register DEC-01/02/03.
- Review document: `docs/evidence/p1-8/P1.8.29-independent-review-policy-decision-register.md`.
- Document commit: `ad0fa98728520a6088733d08d28beaefb0205d1a`.
- Findings cover replay denominator/scenario breadth, observer principal independence, D0–D4 claim separation, durable-ACK/RPO scope, unresolved revocation and checkpoint policies, provisional RPO/RTO, claim-scoped environment equivalence, frozen deterministic test plans, and independent evidence provenance.
- DEC-01 signing-key revocation semantics: OPEN; V07 execution BLOCKED.
- DEC-02 checkpoint membership semantics: OPEN; V08 execution BLOCKED.
- DEC-03 restore RPO/RTO targets and failure domain: OPEN; restore acceptance BLOCKED.
- Status: STATIC REVIEW COMPLETE; POLICY DECISIONS OPEN; NOT EXECUTED. Staging NOT AUTHORIZED; production NOT VERIFIED.
- No source/runtime changes, staging provisioning, fault injection, workflow dispatch, PR, or merge. No CI run or artifact is claimed.
- Next step: obtain owner decisions for DEC-01/02/03; then create a versioned policy baseline and re-review affected criteria before proposing isolated staging execution.

## Latest completed work — P1.8.30

- Recorded explicit owner-approved policy direction C–C–B in `docs/evidence/p1-8/P1.8.30-approved-policy-baseline.md`.
- Policy baseline version: P1.8.30-v1.
- Document commit: `585502f233924fdea70e6ebffb8755da61341306`.
- DEC-01 option C approved: quarantine/fail-closed when key validity or revocation state cannot be proven. Exact timestamp authority, cache age, propagation, rotation overlap and quarantine release parameters remain unspecified; V07 BLOCKED.
- DEC-02 option C approved: hybrid event-time + watermark + durable commit-time gate, immutable sealed checkpoints and explicit late-event/correction path. Exact watermark, allowed-lateness, equality and clock parameters remain unspecified; V08 BLOCKED.
- DEC-03 option B approved: retain acknowledged-transaction RPO 0, snapshot RPO ≤5 minutes, staging RTO ≤60 minutes and 3 independent restores as planning targets only, not approved SLOs or measured capability. Restore acceptance BLOCKED pending measurement contract and separate staging authorization.
- Status: OWNER DECISIONS APPROVED; DESIGN BASELINE RECORDED; NOT EXECUTED. 13/13 vectors remain synthetic PASS only; staging NOT AUTHORIZED; production NOT VERIFIED.
- No source/runtime changes, staging provisioning, provider selection, key operations, restore/fault injection, workflow dispatch, PR, or merge. No CI run or artifact is claimed.
- Next step: P1.8.31 documentation-only acceptance-contract update; fill exact test-contract fields and unresolved parameter gates without inventing numerical values, then static review.

## Latest completed work — P1.8.31

- Added documentation-only acceptance contract: `docs/evidence/p1-8/P1.8.31-acceptance-contract-update.md`.
- Document commit: `b11637060fff5d6bfd6c1eaf4a05150d7baf2e56`.
- Converts P1.8.30 C–C–B policy direction into frozen-manifest requirements, scenario denominator rules, observer-principal independence, D0–D4 claim boundaries, durable-ACK scope, V07 revocation fixtures/gates, V08 checkpoint fixtures/gates, restore measurement contract, V01–V13 acceptance index, evidence provenance and stop conditions.
- Unresolved values are intentionally not invented: V07 BLOCKED on timestamp authority/cache/propagation/rotation/quarantine parameters; V08 BLOCKED on watermark/lateness/boundary/clock/correction parameters; restore acceptance BLOCKED on failure-domain, RPO/RTO measurement and rehearsal-independence contract.
- Status: DOCUMENTATION COMPLETE; STATIC REVIEW REQUIRED; NOT EXECUTED. Prior vectors V01–V06 and V09–V13 remain SYNTHETIC PASS only; V07/V08 remain BLOCKED pending parameters; staging NOT AUTHORIZED; production NOT VERIFIED.
- No source/runtime changes, staging provisioning, provider selection, key operations, restore/fault injection, workflow dispatch, PR, or merge. No CI run or artifact is claimed.
- Next step: independent static consistency review of P1.8.31 against P1.8.26–P1.8.30; then report findings before proposing any separately authorized staging work.

## Latest completed work — P1.8.31 / P1.8.32

- P1.8.31 acceptance contract: `docs/evidence/p1-8/P1.8.31-acceptance-contract-update.md`.
- P1.8.31 initial commit: `b11637060fff5d6bfd6c1eaf4a05150d7baf2e56`; subsequent documented refinements aligned D0–D4 to P1.8.28, strengthened independent-principal and environment-equivalence requirements, mapped F01–F10, and normalized sections.
- Final reviewed P1.8.31 blob SHA: `bc124a346eac9d8239d2dc6b8d44fd86a96c072c`.
- P1.8.32 independent static review: `docs/evidence/p1-8/P1.8.32-independent-static-review.md`.
- P1.8.32 final document commit: `d8cbf9d7de43ea85d96101ce5aac66048f4c16c0`; blob SHA: `ad9ed529342e3694a376f9c158a5d8f392523cd4`.
- Static review: PASS for V01–V13 catalog traceability, F01–F10 mapping, C–C–B policy binding, D0–D4 alignment, RPO/RTO planning values, V07/V08 timestamp contracts, observer independence, claim-scoped environment matrix, section structure and authorization boundaries.
- Review caught and corrected the first P1.8.31 D0–D4 table so definitions exactly match P1.8.28: D0 application/process termination; D1 database process restart; D2 host restart; D3 storage/provider interruption; D4 power loss/device failure/filesystem corruption.
- Residual gates remain: V07 BLOCKED on exact revocation parameters; V08 BLOCKED on exact watermark/boundary parameters; restore acceptance BLOCKED on measurement contract and separate staging authorization; environment equivalence NOT VERIFIED; D3/D4 NOT TESTED.
- Status: P1.8.31 STRUCTURAL/TRACEABILITY REVIEW PASS; execution readiness NOT ESTABLISHED. Staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED. Prior vectors remain SYNTHETIC PASS only.
- No source/runtime changes, staging provisioning, provider selection, key operations, restore/fault injection, workflow dispatch, PR or merge. No CI run or artifact is claimed.
- Next step: prepare an owner-review package for unresolved V07, V08 and restore parameters; no staging action until values are frozen and separately authorized.

## Latest completed work — P1.8.33

- Added `docs/evidence/p1-8/P1.8.33-owner-parameter-decision-package.md`.
- Package commit: `0d7aa316c710a5c7eabf4825bba7b1a196e594e1`.
- Package blob SHA: `6858d5d4d8dca961eb03954a0f3fa0b7ed483f03`.
- Scope: owner decision register for V07 revocation parameters (V07-D1–D9), V08 checkpoint parameters (V08-D1–D9), and restore measurement parameters (RST-D1–D9); includes fixture matrices, evidence-derived lateness workflow, RPO/RTO measurement definitions, dependency order and decision-record template.
- Recommendations are explicitly nonbinding. No exact cache-age, propagation, rotation, watermark, lateness, clock-skew, provider, failure-domain or RTO/RPO measurement parameter has been owner-approved by this package.
- DEC-01 C / DEC-02 C / DEC-03 B remain the approved policy directions. Detailed V07, V08 and restore gates remain OPEN/BLOCKED pending explicit owner decisions and supporting evidence.
- Status: DECISION PACKAGE PREPARED; OWNER DECISIONS PENDING; NOT EXECUTED. Environment equivalence NOT VERIFIED; staging NOT AUTHORIZED; production NOT VERIFIED; D3/D4 NOT TESTED; `AI_EXECUTION_ENABLED=false`.
- No source/runtime changes, VPS/T0/T1/DB/Feeder changes, provider selection, key operations, data collection/read probes, staging provisioning, restore/fault injection, workflow dispatch, PR or merge. No CI run or artifact is claimed.
- Next step: owner reviews the decision register and explicitly selects or revises each parameter; only then prepare a versioned parameter baseline and independent static review.

## Latest completed work — P1.8.34

- Recorded explicit owner approval of the V07, V08 and Restore recommendations in `docs/evidence/p1-8/P1.8.34-owner-approved-parameter-policy.md`.
- P1.8.34 document commit: `e0ac51452053c968c4d08dd53df77f359851f504`.
- P1.8.34 document blob SHA: `fa996f9573ba73609efcf697340b6b969c70479e`.
- Approved V07 direction: independently verifiable trusted timestamp proof; distinct trusted-time/received/revocation semantics; fail-closed and quarantine; explicit revocation authority, key-rotation boundaries and audited quarantine release. Exact authority, proof profile, cache age, propagation, cutover, roles and other numeric/operational parameters remain OPEN.
- Approved V08 direction: UTC half-open `[start,end)` windows; monotonic source-progress watermark; lateness derived from evidence; seal when `watermark >= window_end`; clock uncertainty hold/quarantine; durable commit boundary tied to actual implementation; deterministic seal/commit linearization; immutable checkpoints and append-only idempotent corrections. Exact lateness, skew, clock, source, precision, provider/commit proof and correction contract details remain OPEN.
- Approved Restore measurement direction: explicit failure domain; durable ACK boundary; frozen transaction-ID/digest population; snapshot RPO by time and missing committed transactions; auditable RTO start/stop; three separate rehearsals; integrity/reconciliation oracle; rollback and cleanup. Exact failure domain, provider/database semantics, formulas, rehearsal independence and operational controls remain OPEN.
- Existing planning targets remain unchanged and are not SLOs or measured capabilities: acknowledged-transaction RPO 0 only within tested boundary/failure domain; snapshot RPO ≤5 minutes; staging RTO ≤60 minutes; 3 independent restore rehearsals.
- Owner explicitly withheld staging authorization. Staging NOT AUTHORIZED; no provisioning, restore, fault injection, key operation, data collection/read probe, workflow dispatch, source/runtime change, PR or merge.
- `AI_EXECUTION_ENABLED=false`; no live orders. Production NOT VERIFIED; D3/D4 NOT TESTED. No CI run or artifact is claimed for this documentation-only change.
- Next gate: independent static review of P1.8.34 against P1.8.26–P1.8.33. Keep all measurement-dependent parameters OPEN; any staging proposal requires separate explicit approval.


## Latest completed work — P1.8.35

- Completed documentation-only independent static review of P1.8.34 against P1.8.26–P1.8.33.
- Review: `docs/evidence/p1-8/P1.8.35-independent-static-review.md`.
- Review commit: `06cb331a0cfc8cb46ebfe3a0bfcefb1bb20592e5`.
- Review finding F-01 (HIGH): timestamp proof must cryptographically bind the exact signature being verified, not merely the payload/unsigned envelope; otherwise an old payload timestamp does not prove that a particular signature existed before revocation. Exact imprint construction, canonicalization, proof profile and authority remain OPEN.
- PASS: owner decision/scope recording, C–C–B continuity, OPEN parameter preservation, V08 interval/watermark/checkpoint/correction direction, Restore measurement direction, assurance separation and authorization boundary.
- Result: PARTIAL — policy consistency PASS with one security-critical V07 clarification required.
- V07 remains BLOCKED pending F-01 resolution and all detailed parameters/fixtures. V08 detailed parameters remain OPEN/BLOCKED; Restore measurement contract remains OPEN/BLOCKED.
- Environment equivalence NOT VERIFIED; staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED; D3/D4 NOT TESTED; `AI_EXECUTION_ENABLED=false`.
- No source/runtime changes, VPS/T0/T1/DB/Feeder changes, provider selection, key operations, data collection/read probes, staging provisioning, restore rehearsal, fault injection, workflow dispatch, PR or merge. No CI run or artifact is claimed.
- Next gate: documentation-only clarification of F-01, with exact timestamp-to-signature binding and positive/negative boundary fixtures; all provider/authority/numeric parameters remain OPEN. Then independent static review. Separate staging authorization remains mandatory.


## Latest completed work — P1.8.36

- Added documentation-only contract `docs/evidence/p1-8/P1.8.36-trusted-timestamp-signature-binding-contract.md`.
- Document commit: `62dc6ee297401287270adef9beaf7c754db572ad`.
- Resolves the design ambiguity raised by P1.8.35 F-01 at contract level: the trusted timestamp imprint must cryptographically bind the exact signature value and immutable verification context, not only payload bytes or an unsigned envelope.
- Carefully limits the claim: a valid token establishes that the timestamped signed object existed no later than TSA `genTime`; it does not prove the exact signature creation instant or signer intent.
- Defines deterministic verification obligations, immutable context binding, token/trust validation requirements, fail-closed behavior, historical revocation boundary handling and 15 positive/negative contract fixtures (TB-P01, TB-P02, TB-N01–TB-N13).
- No fixture code or test execution was added. Fixture bytes, imprint encoding, digest algorithm, TSA protocol/profile, trust anchors, policy OID, timestamp uncertainty, revocation equality semantics and all other provider/numeric parameters remain OPEN.
- Status: F-01 CLARIFICATION DRAFTED; independent static security review REQUIRED; V07 remains BLOCKED. V08 and Restore remain OPEN/BLOCKED. Environment equivalence NOT VERIFIED; staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED; D3/D4 NOT TESTED; `AI_EXECUTION_ENABLED=false`.
- No source/runtime changes, VPS/T0/T1/DB/Feeder changes, provider selection, key provisioning/signing/rotation/revocation, data collection/read probes, staging provisioning, restore rehearsal, fault injection, workflow dispatch, PR or merge. No CI run or artifact is claimed.
- Next gate: independent static security review of P1.8.36 against P1.8.26–P1.8.35, especially exact signature-byte binding and the limited `genTime` claim. Separate explicit staging authorization remains mandatory.

## Latest completed work — P1.8.37

- Completed documentation-only independent static security review of P1.8.36 against P1.8.26, P1.8.28, P1.8.34 and P1.8.35.
- Review: `docs/evidence/p1-8/P1.8.37-independent-security-review.md`.
- Review commit: `3dd25969d8039bd052975dc29be7d7f0aa481879`.
- Reviewed P1.8.36 blob SHA: `9883ed1fb856a161fc56f5c5721e36813a6fabe7`.
- Result: PARTIAL — exact-signature binding design PASS; narrow fixture-disposition clarification required.
- F-01 is CLARIFIED / DESIGN PASS: imprint binds exact signature bytes and immutable verification context; the `genTime` claim is properly limited to existence no later than the TSA assertion, not exact signature creation time.
- New finding F-11 (MEDIUM): TB-P01/TB-P02 wording “historical policy decision proceeds” could be read as acceptance even though the V07 trust profile, revocation authority, precision, uncertainty and equality parameters remain OPEN. Clarify that cryptographic fixture PASS does not imply historical acceptance; final disposition remains BLOCKED/NOT DETERMINED until V07 is frozen.
- V07 remains BLOCKED; V08 and Restore remain OPEN/BLOCKED. Environment equivalence NOT VERIFIED; staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED; D3/D4 NOT TESTED; `AI_EXECUTION_ENABLED=false`.
- No source/runtime changes, VPS/T0/T1/DB/Feeder changes, provider selection, key operations, data probes, staging provisioning, restore rehearsal, fault injection, workflow dispatch, PR or merge. No CI run or artifact is claimed.
- Next gate: P1.8.38 documentation-only correction of TB-P01/TB-P02 expected outcomes, keeping all provider, cryptographic profile, time, revocation and numeric parameters OPEN; then independent re-review. Separate explicit staging authorization remains mandatory.

## Latest completed work — P1.8.38

- Added documentation-only amendment `docs/evidence/p1-8/P1.8.38-positive-timestamp-fixture-acceptance-clarification.md`.
- Document commit: `12c85965dde76853a41506e756648acbe0c5a84b`.
- Scope: resolves P1.8.37 finding F-11 by separating BINDING_RESULT, TOKEN_VALIDATION_RESULT, EVENT_SIGNATURE_RESULT, HISTORICAL_ELIGIBILITY_RESULT and FINAL_DISPOSITION.
- TB-P01/TB-P02 now permit cryptographic binding PASS without implying historical acceptance. Until V07 is frozen and independently reviewed, historical eligibility remains BLOCKED / NOT DETERMINED and final disposition remains QUARANTINE / HOLD (or BLOCKED); ACCEPT is prohibited.
- Late receipt in TB-P02 does not rewrite trusted genTime and does not bypass revocation freshness, replay/idempotency or quarantine controls.
- P1.8.36 TB-N01–TB-N13 remain unchanged. All TSA/provider/profile, cryptographic encoding, time uncertainty, revocation, cache, propagation, rotation, fixture-byte and numeric parameters remain OPEN.
- Status: F-11 addressed at documentation-oracle level; independent re-review REQUIRED. F-01 remains CLARIFIED / DESIGN PASS but formal closure pending frozen profile/fixtures/final review. V07 BLOCKED; V08 and Restore OPEN/BLOCKED; environment equivalence NOT VERIFIED; staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED; D3/D4 NOT TESTED; `AI_EXECUTION_ENABLED=false`.
- No source/runtime changes, VPS/T0/T1/DB/Feeder changes, provider selection, key operations, data probes, staging provisioning, restore rehearsal, fault injection, workflow dispatch, PR or merge. No CI run or artifact is claimed.
- Next gate: independent static review of P1.8.38 against P1.8.26, P1.8.28 and P1.8.34–P1.8.37. Separate explicit staging authorization remains mandatory.


## Latest completed work — P1.8.39

- Completed documentation-only independent static security review of P1.8.38 against P1.8.26, P1.8.28 and P1.8.34–P1.8.37.
- Review: `docs/evidence/p1-8/P1.8.39-independent-static-security-review.md`.
- Review commit: `6d7edefd29e1199b591a5c43e10453f222d7bca3`.
- Review blob SHA: `54c97c3e4bb1f59113261add539a1f976fb7e426`.
- Reviewed P1.8.38 blob SHA: `21b0aec3a308cd2b9dcbdbada16699ee0476bca9`.
- Result: PASS — P1.8.38 correctly separates binding, token validation, event-signature validation, historical eligibility and final disposition. TB-P01/TB-P02 remain BLOCKED / NOT DETERMINED and QUARANTINE / HOLD until V07 is frozen and independently reviewed.
- P1.8.37 F-11 is ADDRESSED at documentation-oracle level. P1.8.35 F-01 remains CLARIFIED / DESIGN PASS; formal closure still requires frozen profile, fixture bytes/hashes and final review.
- No new finding. V07 remains BLOCKED; V08 and Restore remain OPEN/BLOCKED; environment equivalence NOT VERIFIED; staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED; D3/D4 NOT TESTED; `AI_EXECUTION_ENABLED=false`.
- No source/runtime, VPS/T0/T1/DB/Feeder, exchange, ledger, strategy or risk-engine changes; no provider/key operations, data probes, staging, restore, fault injection, workflow dispatch, PR or merge. No CI run or artifact is claimed.
- Next gate: documentation-only parameter-closure inventory for V07, V08 and Restore, listing each OPEN field, required evidence, decision owner and dependencies. Do not select unsupported values or authorize staging.


## Latest completed work — P1.8.40

- Added documentation-only inventory: `docs/evidence/p1-8/P1.8.40-parameter-closure-inventory.md`.
- Commit: `f1ac12388ffce2645cf1d376c232befba0be9986`.
- Blob SHA: `167e5b4a478f2b6bf5053f85d8260e755a2f18da`.- Enumerates V07-D1–D9, V08-D1–D9 and RST-D1–D9 with current status, evidence required, decision authority, dependencies and closure sequence.
- Preserves approved policy directions without inventing numeric/provider/implementation values. Includes cross-stream dependency order, owner decision record requirements and explicit distinction between READY FOR REVIEW and execution authorization.
- Status: INVENTORY COMPLETE; PARAMETERS OPEN; NOT EXECUTED. V07 BLOCKED; V08 OPEN/BLOCKED; Restore OPEN/BLOCKED; environment equivalence NOT VERIFIED; staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED; D3/D4 NOT TESTED; synthetic 13/13 remains synthetic only; `AI_EXECUTION_ENABLED=false`.
- No source/runtime, VPS/T0/T1/DB/Feeder, exchange, ledger, strategy or risk-engine changes. No provider/key operations, data probes, staging, restore, fault injection, workflow dispatch, PR or merge. No CI run or artifact is claimed.
- Next gate: P1.8.41 independent static review of P1.8.40 for completeness, traceability and consistency with P1.8.26/P1.8.28/P1.8.33/P1.8.34/P1.8.39. Documentation-only; no new permissions required.


## Latest continuation — P1.8.41 / P1.8.42

### P1.8.41 — Independent review of P1.8.40
- Review: `docs/evidence/p1-8/P1.8.41-independent-review-parameter-closure-inventory.md`.
- Review commit: `b390f8e6a7b29c43b66a1ffd9fed07f0290b010a`.
- Review blob SHA: `c869b2fd47abe3405689e588e0905f6b1991a465`.
- Result: PARTIAL. All 27 top-level decision IDs and V08/Restore coverage pass; findings F-12 (V07 trust-time sub-items not individually enumerated) and F-13 (source-clause traceability) require a narrow documentation supplement.
- No parameter values were selected; all gates and authorization limits remain unchanged.

### P1.8.42 — V07 trusted-time profile sub-register
- Supplement: `docs/evidence/p1-8/P1.8.42-v07-trusted-time-profile-subregister.md`.
- Commit: `f71e864d6dc17341077faaba33d0f6843ee6023f`.
- Blob SHA: `2b11706786f0f825fff46b368f92c575a797d7dc`.
- Adds explicit traceable sub-items for trust authority/profile, trust-anchor lifecycle, certificate/path validation, timestamp accuracy/uncertainty, nonce/replay, imprint encoding, canonical envelope/context, exact signature binding, fixture bytes/digests and stage-separated oracle; maps them to P1.8.33/P1.8.34/P1.8.36/P1.8.38/P1.8.39.
- All provider, algorithm, clock, uncertainty, trust and fixture parameters remain OPEN. Stage-separated oracle documentation rule remains as previously approved/reviewed; executable fixtures remain OPEN.
- Status: F-12/F-13 DOCUMENTATION RESPONSE RECORDED; independent review REQUIRED. V07 BLOCKED; V08 OPEN/BLOCKED; Restore OPEN/BLOCKED; environment equivalence NOT VERIFIED; staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED; D3/D4 NOT TESTED; `AI_EXECUTION_ENABLED=false`.
- No code/tests, provider selection, key operation, data probe, staging, restore, fault injection, workflow dispatch, PR or merge. No CI run or artifact is claimed.
- Next gate: P1.8.43 independent static review of P1.8.42. Documentation-only; no new permission required.


### P1.8.43 — Independent review of V07 trusted-time sub-register
- Review: `docs/evidence/p1-8/P1.8.43-independent-review-v07-trusted-time-subregister.md`.
- Review commit: `1be0658896fcffd0b4edbee3fa562aace5e90d57`.
- Review blob SHA: `1a92beda8eb52d681353e62133a4fa6507c9e78a`.
- Reviewed P1.8.42 blob SHA: `2b11706786f0f825fff46b368f92c575a797d7dc`.
- Result: PASS. P1.8.41 F-12/F-13 are addressed at documentation/traceability level. V07-D1a–D1f and V07-D2a–D2e explicitly enumerate trust-anchor lifecycle, TSA profile/token validation, timestamp uncertainty, nonce/replay, imprint encoding, exact signature binding, fixture bytes/digests and stage-separated oracle.
- This is register completeness only; no provider/profile/algorithm/value is approved, fixtures are not frozen/executed, and V07 remains BLOCKED.
- V08 OPEN/BLOCKED; Restore OPEN/BLOCKED; environment equivalence NOT VERIFIED; staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED; D3/D4 NOT TESTED; synthetic 13/13 remains synthetic only; `AI_EXECUTION_ENABLED=false`.
- No source/runtime, VPS/T0/T1/DB/Feeder, exchange, ledger, strategy or risk-engine changes; no provider/key operations, data probes, staging, restore, fault injection, workflow dispatch, PR or merge. No CI run or artifact is claimed.
- Next gate: continue documentation-only closure inventory/review for V08 and Restore. Request owner decisions only when evidence-backed proposals are ready; request separate permission before any privileged or operational action.


### P1.8.44 / P1.8.45 / P1.8.46 — V08 and Restore traceability
- P1.8.44 review: `docs/evidence/p1-8/P1.8.44-independent-review-v08-restore-inventory.md`; commit `6c706fcde9956f839a97e34e736998d3c248eb6e`; blob `6163f6fb18ace869e290af9b86bd79918f13e415`.
- P1.8.44 result: PARTIAL. V08-D1–D9 and RST-D1–D9 technical coverage PASS; F-14 LOW required per-row source-clause provenance.
- P1.8.45 crosswalk: `docs/evidence/p1-8/P1.8.45-v08-restore-source-clause-crosswalk.md`; commit `82227e376181af4109abe26e4ff56ea9ae773906`; blob `bea314c9092a801102c180ca01104212d4664177`.
- P1.8.46 independent review: `docs/evidence/p1-8/P1.8.46-independent-review-v08-restore-crosswalk.md`; commit `0dbc93f7ef000b9f4473731b64f5b8ce42580cbc`; blob `0a2e8d4f29bf2756cfdba26cd0325245aacad0c9`.
- P1.8.46 result: PASS; F-14 ADDRESSED at documentation/traceability level. Every V08-D1–D9 and RST-D1–D9 row now maps to P1.8.33/P1.8.34 and relevant P1.8.26/P1.8.28 clauses.
- No parameter values, provider, failure domain, SLO or authorization was promoted. V07 BLOCKED; V08 OPEN/BLOCKED; Restore OPEN/BLOCKED; environment equivalence NOT VERIFIED; staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED; D3/D4 NOT TESTED; RPO/RTO remain planning targets only; `AI_EXECUTION_ENABLED=false`.
- No source/runtime, VPS/T0/T1/DB/Feeder, exchange, ledger, strategy or risk-engine changes; no provider/key operations, data probes, staging, restore, fault injection, workflow dispatch, PR or merge. No CI run or artifact is claimed.
- Next gate: consolidate a documentation-only owner decision readiness register, distinguishing decisions answerable from current documentary evidence from those requiring measurement or implementation/provider choice. No execution authorization implied.


### P1.8.47 / P1.8.48 — Owner decision readiness
- P1.8.47 register: `docs/evidence/p1-8/P1.8.47-owner-decision-readiness-register.md`; commit `98404af889e5bca6c1bd99e6db5dcb1a63ffbbf8`; blob `b78e7151eab25e852b2f6ed61f98a0de94365dd1`.
- Separates approved policy directions, documentation-ready items, evidence-required values, implementation-dependent values, owner decisions after evidence/design, and separate permission gates.
- Explicitly states when to ask owner; no unsupported numeric/provider choices and no new owner decision recorded.
- P1.8.48 independent review: `docs/evidence/p1-8/P1.8.48-independent-review-owner-decision-readiness.md`; commit `776ffcf82bea98b4fa56cf3157834fd91ab3b217`; blob `90ac80acd1c92d63b9669b549b6242b576124f8b`.
- P1.8.48 result: PASS; no implied owner approval or execution permission; no new findings.
- V07 BLOCKED; V08 OPEN/BLOCKED; Restore OPEN/BLOCKED; environment equivalence NOT VERIFIED; staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED; D3/D4 NOT TESTED; synthetic 13/13 only; RPO/RTO planning targets only; `AI_EXECUTION_ENABLED=false`.
- No source/runtime, VPS/T0/T1/DB/Feeder, exchange, ledger, strategy or risk-engine changes; no provider/key operations, data probes, staging, restore, fault injection, workflow dispatch, PR or merge. No CI run or artifact is claimed.
- No evidence-backed numeric/provider owner decision is currently ready from the reviewed documents alone. Continue documentation-only work; ask for separate permission only when an exact privileged/operational action becomes necessary.


### P1.8.49 / P1.8.50 — Evidence acquisition readiness
- P1.8.49 plan: `docs/evidence/p1-8/P1.8.49-evidence-acquisition-readiness-plan.md`; commit `545aaf8dc52307d524c9fe127fcd9abc3b2f7980`; blob `f93cb1e2677074491340620eb2e931abc08dbc8d`.
- Defines E0 documentary, E1 synthetic, E2 authorized non-production, E3 operational and E4 staging evidence classes; includes V07/V08/Restore evidence fields and permission prerequisites.
- No sample size, duration, percentile, tolerance, provider, clock source or numeric threshold selected. No evidence acquired.
- P1.8.50 review: `docs/evidence/p1-8/P1.8.50-independent-review-evidence-acquisition-plan.md`; commit `8b1adad56d575c2b10e3968b97ccd529c142c708`; blob `0bb24c6cf9e3c850ebe83acf4940747449190740`.
- P1.8.50 result: PASS; no new findings. Evidence classes/provenance and separate E2/E3/E4 permission gates are consistent.
- V07 BLOCKED; V08 OPEN/BLOCKED; Restore OPEN/BLOCKED; no E2/E3/E4 evidence acquired; environment equivalence NOT VERIFIED; staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED; D3/D4 NOT TESTED; RPO/RTO planning targets only; `AI_EXECUTION_ENABLED=false`.
- No source/runtime, VPS/T0/T1/DB/Feeder, exchange, ledger, strategy or risk-engine changes; no provider/key operations, live data probes, staging, restore, fault injection, workflow dispatch, PR or merge. No CI run or artifact is claimed.
- Next gate: concise owner status/permission-boundary handoff. Do not request generic permission in advance; ask only when a specific evidence-backed action is ready.


## Latest continuation — P1.8.51

- Added E0 documentary assessment: `docs/evidence/p1-8/P1.8.51-evidence-backed-candidate-assessment.md`.
- Document commit: `052568f8c877de1f97675db80d2f7a242e72225a`.
- Verified document blob SHA: `1462169d0bcac9c5a4ce41a9d1e4016781eb381c`.
- Reviewed public primary sources: RFC 3161 (TSA timestamp token, imprint, nonce, genTime/accuracy); RFC 6960 (OCSP status and time semantics); RFC 5280 (certificate path/CRL); Apache Flink documentation (event-time/watermarks, checkpoint/replay and exactly-once constraints); PostgreSQL 17 documentation (base backup + WAL/PITR).
- Assessment conclusions: missing RFC 3161 accuracy is not zero; OCSP `good` is not standalone proof of historical issuance/validity; watermark is not durable-commit proof; exactly-once claims depend on replayable sources and transactional/idempotent sinks; successful backup job/startup is not restore plus business reconciliation proof.
- No TSA/CA/OCSP provider, trust anchor, algorithm, policy OID, accuracy/cache threshold, watermark/lateness/clock parameter, database provider, failure domain, RPO/RTO SLO or staging authorization was selected.
- Status: P1.8.51 DOCUMENTARY ASSESSMENT COMPLETE (E0 only); V07 BLOCKED; V08 OPEN/BLOCKED; Restore OPEN/BLOCKED; environment equivalence NOT VERIFIED; staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED; D3/D4 NOT TESTED; 13 vectors SYNTHETIC PASS only; RPO/RTO planning targets only; `AI_EXECUTION_ENABLED=false`.
- No source/runtime, VPS/T0/T1/DB/Feeder, exchange, ledger, strategy or risk-engine changes; no provider connection, key operation, live probe, staging, restore, fault injection or workflow dispatch. No CI run or artifact is claimed.
- Next gate: independent static review of P1.8.51 for standards interpretation, source traceability, candidate neutrality and preservation of all OPEN/permission gates. Continue documentation-only work; stop for explicit permission before any E2/E3/E4 or operational action.


### P1.8.51 / P1.8.52 / P1.8.53 — Candidate assessment and independent review
- P1.8.51 E0 documentary assessment: `docs/evidence/p1-8/P1.8.51-evidence-backed-candidate-assessment.md`.
- Initial document commit: `052568f8c877de1f97675db80d2f7a242e72225a`; initial blob `1462169d0bcac9c5a4ce41a9d1e4016781eb381c`.
- P1.8.52 independent review: `docs/evidence/p1-8/P1.8.52-independent-review-candidate-assessment.md`; commit `7e0ac520ea970a0e82d32b2c866248cd1b3a8c1d`. Result PARTIAL; finding F-15 identified that RFC 6960's OCSP Nonce extension had later updates.
- Corrected P1.8.51 commit: `59d0cd86582c575fc10ec8165f003991ea893bad`; verified corrected blob SHA `55a20cdf127a1303f795ce9fb40d9e6bd5696802`.
- Correction cites RFC 9654 as the current OCSP Nonce update to RFC 6960 and notes that it obsoletes RFC 8954; protocol constraints are explicitly distinguished from a project-selected nonce policy. Interoperability fixture categories are recorded; provider compatibility and project nonce parameters remain OPEN.
- P1.8.53 independent re-review: `docs/evidence/p1-8/P1.8.53-independent-rereview-corrected-candidate-assessment.md`; commit `c27cb1f48a3b1614d6c26bc96bbb2b7b4cbe5f3d`.
- P1.8.53 result: PASS; F-15 addressed at documentary standards-currency/traceability level; no additional finding within E0 scope.
- Assessment conclusions remain: RFC 3161 accuracy absence is not zero; OCSP GOOD is not standalone historical issuance/validity proof; watermark is not durable-commit proof; exactly-once depends on source replayability and sink transaction/idempotency; backup success is not restore plus business reconciliation.
- Status: P1.8.51 DOCUMENTARY ASSESSMENT PASS after correction; V07 BLOCKED; V08 OPEN/BLOCKED; Restore OPEN/BLOCKED; environment equivalence NOT VERIFIED; staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED; D3/D4 NOT TESTED; 13 vectors SYNTHETIC PASS only; RPO/RTO planning targets only; `AI_EXECUTION_ENABLED=false`.
- No source/runtime, VPS/T0/T1/DB/Feeder, exchange, ledger, strategy or risk-engine changes; no provider connection, key operation, data probe, staging, restore, fault injection or workflow dispatch. No CI run or artifact is claimed.
- Next gate: prepare a consolidated evidence-to-decision matrix for the minimum E2/E3/E4 evidence needed to resolve each OPEN parameter family. Remain documentation-only until a concrete action requires separate explicit permission.


### P1.8.54 / P1.8.55 — Minimum evidence-to-decision matrix
- P1.8.54 matrix: `docs/evidence/p1-8/P1.8.54-minimum-evidence-to-decision-matrix.md`; commit `40f63f9f4d26fb845d1ab8ca8494aab62f93793f`.
- Maps each OPEN V07/V08/Restore parameter family to minimum evidence categories, earliest useful evidence class, owner decision supported and explicit permission gate.
- Defines cross-cutting evidence manifest (source/configuration SHA, environment, identity, UTC/uncertainty, raw artifact digest, verifier, oracle, custody, retention, rollback/cleanup).
- Separates E0/E1 documentary/synthetic evidence from E2 non-production, E3 operational read-only and E4 staging evidence. No blanket permission requested; provider, key, production, VPS, staging, restore, fault injection and side-effect workflow actions each require explicit bounded approval.
- P1.8.55 independent review: `docs/evidence/p1-8/P1.8.55-independent-review-evidence-to-decision-matrix.md`; commit `e7c21d14d28677f458a35523ffe63746b4995592`.
- P1.8.55 result: PASS within documentary scope; coverage, proportionality, evidence classes, decision mapping, provenance and permission boundaries consistent; no findings.
- No sample counts, durations, numeric thresholds, providers, failure domains or SLOs selected. No E2/E3/E4 evidence acquired.
- Status: P1.8.54 DOCUMENTATION COMPLETE; P1.8.55 REVIEW PASS; V07 BLOCKED; V08 OPEN/BLOCKED; Restore OPEN/BLOCKED; environment equivalence NOT VERIFIED; staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED; D3/D4 NOT TESTED; 13 vectors SYNTHETIC PASS only; RPO/RTO planning targets only; `AI_EXECUTION_ENABLED=false`.
- No source/runtime, VPS/T0/T1/DB/Feeder, exchange, ledger, strategy or risk-engine change; no provider connection, key operation, production probe, staging, restore, fault injection or workflow dispatch. No CI run or artifact is claimed.
- Next gate: consolidate local E1 fixture specifications and acceptance oracles, without executing provider, runtime, staging or operational tests. Any E2/E3/E4 action remains separately permission-gated.


### P1.8.56 / P1.8.57 — Consolidated E1 fixture index
- P1.8.56 index: `docs/evidence/p1-8/P1.8.56-consolidated-local-e1-fixture-index.md`; commit `c8ab57a279d078f6a23ddefcacdccd95f3a57d82`.
- Consolidates the 13 historical synthetic fault vectors without renaming; cross-references TB-P01/P02 and TB-N01–TB-N13; defines proposed V08-E1-01–15 and RST-E1-01–10 index categories.
- Preserves stage-separated V07 outcomes and adds RFC 9654 OCSP nonce interoperability categories. V08/Restore IDs are proposed fixture index IDs only, not existing test executions.
- Requires fixture IDs, immutable bytes/digests, exact source/test SHA, deterministic setup/barriers, intermediate and terminal oracles, base-event vs delivery identity, and forbidden-side-effect assertions before freeze.
- P1.8.57 independent review: `docs/evidence/p1-8/P1.8.57-independent-review-e1-fixture-index.md`; commit `5b613bfcc30ce6c90dfb03f3beb3c14509b941f4`.
- P1.8.57 result: PASS within documentation/index scope; no omissions or oracle/authorization conflicts found.
- No fixture bytes were frozen or executed; no new synthetic result is claimed. Existing 13 vectors remain historical SYNTHETIC PASS only.
- Status: P1.8.56 INDEX COMPLETE; P1.8.57 REVIEW PASS; V07 BLOCKED; V08 OPEN/BLOCKED; Restore OPEN/BLOCKED; E2/E3/E4 NOT ACQUIRED; environment equivalence NOT VERIFIED; staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED; D3/D4 NOT TESTED; RPO/RTO planning targets only; `AI_EXECUTION_ENABLED=false`.
- No source/runtime, VPS/T0/T1/DB/Feeder, exchange, ledger, strategy or risk-engine changes; no provider connection, key operation, data probe, staging, restore, fault injection or workflow dispatch. No CI run or artifact is claimed.
- Next gate: prepare deterministic E1 fixture-byte specifications for high-risk V07 boundary/replay cases; do not execute tests or select OPEN policy values. E1 execution is a separate decision gate.


### P1.8.58 / P1.8.59 / P1.8.61 — V07 boundary and replay fixture specification
- P1.8.58 parameterized E1 fixture specification: `docs/evidence/p1-8/P1.8.58-v07-boundary-replay-fixture-specification.md`; initial commit `f83734439910e38868629e1b6d8bd838ebcd7feb`.
- Defines exact signature/context substitution, uncertainty interval vs revocation, equality/overlap, missing accuracy, late receipt, OCSP stale/unknown/unavailable/contradictory status, RFC 3161 nonce, OCSP RFC 9654 nonce and replay cases. Cryptographic fixture bytes are not frozen because TSA/profile/algorithm/trust/revocation parameters remain OPEN.
- P1.8.59 independent review: `docs/evidence/p1-8/P1.8.59-independent-review-v07-boundary-fixtures.md`; commit `6d5176ad79834d320a3c45a11ff120d1e07e1977`. Result PARTIAL; finding F-16 required RFC 9654-permitted OCSP nonce omission to be distinguished from nonce-echo PASS.
- Corrected P1.8.58 commit: `f0d6ac527f165d4ef11e7225838ac2e01ff4c9b3`; corrected blob SHA `2fb60fff3e87d63bd269947ef9cd22fe99464af2`.
- Correction records permitted omission as NONCE_ECHO=NOT_PRESENT, not PASS; replay/freshness remains NOT VERIFIED absent a separately approved mechanism. Project profile-required omission/mismatch fails the project nonce policy; malformed/unsupported profile combinations are explicit.
- P1.8.61 independent re-review: `docs/evidence/p1-8/P1.8.61-independent-rereview-v07-boundary-fixtures.md`; commit `3bbf452b29251d0726c9a7f4887e5357ab829154`. Result PASS; F-16 addressed at documentary fixture-oracle level; no project nonce profile selected.
- Status: P1.8.58 SPECIFICATION COMPLETE; CRYPTOGRAPHIC BYTES NOT FROZEN; NOT EXECUTED; P1.8.61 REVIEW PASS; V07 BLOCKED; V08 OPEN/BLOCKED; Restore OPEN/BLOCKED; E2/E3/E4 NOT ACQUIRED; environment equivalence NOT VERIFIED; staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED; D3/D4 NOT TESTED; existing 13 vectors historical SYNTHETIC PASS only; RPO/RTO planning targets only; `AI_EXECUTION_ENABLED=false`.
- No fixture bytes generated or executed; no provider, key, runtime, VPS, DB, Feeder, production, staging, restore, fault injection or workflow operation. No CI run or artifact is claimed.
- Next gate: independent review of separation between policy design, frozen E1 bytes, E1 execution and external/provider integration. Keep all OPEN decisions and execution permissions separate.


### P1.8.62 — E1 lifecycle and external integration boundary review
- Review: `docs/evidence/p1-8/P1.8.62-independent-review-e1-lifecycle-boundaries.md`; commit `5005773501220d1bc6869e18e65f2289c317e731`.
- Result: PASS. Confirms policy design vs fixture specification vs frozen bytes vs executed E1; E1 vs E2; E2 vs E3; E3 vs E4; E4 vs production; and readiness vs execution authorization remain distinct.
- V07 RFC 9654 nonce omission behavior remains correctly separated from nonce-echo PASS. No provider/profile/algorithm/trust/nonce/accuracy/revocation parameter selected.
- V08/Restore proposed fixture IDs remain specifications, not executions; watermark/checkpoint/backup/startup are not accepted as durable commit or restore/reconciliation proof.
- No finding. No provider connection, key operation, E1 execution, data probe, VPS/runtime change, staging, restore, fault injection or workflow dispatch. No CI run or artifact is claimed.
- Status: P1.8.62 REVIEW PASS; P1.8.58 SPECIFICATION COMPLETE / CRYPTOGRAPHIC BYTES NOT FROZEN / NOT EXECUTED; existing 13 vectors historical SYNTHETIC PASS only; V07 BLOCKED; V08 OPEN/BLOCKED; Restore OPEN/BLOCKED; E2/E3/E4 NOT ACQUIRED; environment equivalence NOT VERIFIED; staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED; D3/D4 NOT TESTED; RPO/RTO planning targets only; `AI_EXECUTION_ENABLED=false`.
- Next gate: determine which local E1 fixtures can be frozen without selecting unresolved policy/provider/implementation parameters. If no fixture meets that condition, record the blocker and do not fabricate values or request generic permission.


### P1.8.63 — E1 fixture freeze eligibility
- Assessment: `docs/evidence/p1-8/P1.8.63-e1-fixture-freeze-eligibility-assessment.md`; commit `63bbba09678c0f3a0a5ac741c805512ac626188c`.
- Determination: no new V07/V08/Restore E1 fixture can be fully frozen without choosing unresolved profile, trust, revocation, precision/serialization, source/adapter or database/WAL implementation parameters.
- Existing FV-01–FV-13 remain historical synthetic evidence and are not duplicated/re-frozen. V07 exact-signature/time/revocation/nonce fixture bytes remain blocked; V08 UTC half-open semantics are approved but exact executable serialization/precision and source/commit contract remain open; Restore fixture compatibility depends on a declared database/backup/WAL implementation and failure domain.
- No new fixture bytes frozen or executed; no new owner numeric/provider/implementation decision is ready from documentary evidence alone.
- Status: P1.8.63 ASSESSMENT COMPLETE; V07 BLOCKED; V08 OPEN/BLOCKED; Restore OPEN/BLOCKED; E2/E3/E4 NOT ACQUIRED; environment equivalence NOT VERIFIED; staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED; D3/D4 NOT TESTED; 13 vectors historical SYNTHETIC PASS only; RPO/RTO planning targets only; `AI_EXECUTION_ENABLED=false`.
- No source/runtime, VPS/T0/T1/DB/Feeder, exchange, ledger, strategy or risk-engine change; no provider/key operation, data probe, E1 execution, staging, restore, fault injection or workflow dispatch. No CI run or artifact is claimed.
- Next gate: wait for a concrete evidence-backed candidate/profile or implementation decision; do not manufacture test parameters or request generic permission.


### P1.8.64 / P1.8.65 — Public TSA/OCSP candidate assessment
- P1.8.64: `docs/evidence/p1-8/P1.8.64-public-tsa-ocsp-candidate-assessment.md`; commit `d71533cf7d66a864eab03689e68ad30fe43ffb01`; verified blob SHA `6fdfae26121add0bbe74ddcfcf19e2a5ae0f3bef`.
- Public primary-source comparison covered GlobalSign, DigiCert and Sectigo TSA documentation and RFC 3161/RFC 6960/RFC 9654.
- GlobalSign is the strongest documentary follow-up candidate only: published non-qualified general-use policy, policy OIDs, stated 1-second UTC accuracy, GNSS plus UTC(k)-referenced NTP monitoring, SHA-256/384/512, issuer/OCSP verification path and stated availability aims. Its TPS is dated 2022; current endpoint/profile/chain/terms still require confirmation. NOT SELECTED.
- DigiCert publishes RFC 3161 endpoint and current certificate-chain materials; its page notes 2026-09-03 certificate replacements and at-least-15-month certificate updates. Accuracy, policy OID, generic-use scope, nonce and SLA remain undocumented in the reviewed page; it contains an RFC 3151 endpoint-heading typo. NOT SELECTED.
- Sectigo CPS v1.0.0 (2024-08-26) documents RFC 3161, UTC(k) clock synchronization and auditable drift/adjustment controls, but expressly limits the TSA intended use to software signing with a Sectigo Code Signing Certificate. Out of current general-purpose scope unless written terms establish broader use.
- OCSP is not independently vendor-selected: use the issuer-authorized responder for the exact TSA certificate chain, discovered through AIA or approved local configuration; verify signer authorization, freshness, exact CertID and preserve signed historical responses/CRLs. Current GOOD is not retroactive proof of historical validity.
- P1.8.65 independent review: `docs/evidence/p1-8/P1.8.65-independent-review-tsa-ocsp-assessment.md`; commit `68fcbcf1bb12206769174cff689509002f4d5c27`. Result PASS within E0 documentary scope; no findings.
- Status: P1.8.64 E0 ASSESSMENT COMPLETE; P1.8.65 REVIEW PASS; GlobalSign strongest follow-up candidate only / NOT SELECTED; DigiCert NOT SELECTED; Sectigo out of current documented scope; no OCSP vendor selected; V07 BLOCKED; V08 OPEN/BLOCKED; Restore OPEN/BLOCKED; E2/E3/E4 NOT ACQUIRED; environment equivalence NOT VERIFIED; staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED; D3/D4 NOT TESTED; 13 fault vectors historical SYNTHETIC PASS only; RPO/RTO planning targets only; `AI_EXECUTION_ENABLED=false`.
- No provider contact/connection, OCSP query, key/trust-anchor operation, production probe, VPS/runtime/T0/T1/DB/Feeder change, staging, restore, fault injection or workflow dispatch. No CI run or artifact is claimed.
- Next gate: present narrow owner decision whether to authorize a written-information request to GlobalSign (no account, endpoint call, test or key operation). Sending any provider request requires explicit approval; no blanket permission requested.


### P1.8.66 — Draft GlobalSign TSA due-diligence questionnaire
- Draft: `docs/evidence/p1-8/P1.8.66-draft-globalsign-tsa-due-diligence-questionnaire.md`; commit `6e9dd9ca773ccffa93450297031f2466f8c29bdf`.
- Contains written questions covering arbitrary opaque-hash use scope, current non-qualified endpoint/policy OID, applicable TPS/CPS/terms, accuracy semantics and TSTInfo accuracy presence, accepted algorithms, nonce behavior, errors/rate limits, signer chain/rollover, historical OCSP/CRL evidence, token/audit retention, availability, support, price and jurisdiction.
- Explicitly states no account, service, credential, key, endpoint test or provider contact is requested at this stage. The questionnaire is DRAFT ONLY and NOT SENT.
- Sending the inquiry requires explicit owner approval. Any E2 sandbox/endpoint call, credential or trust-anchor/key operation requires a separate bounded approval.
- Status: P1.8.66 DRAFT COMPLETE / NOT SENT; GlobalSign documentary follow-up candidate only / NOT SELECTED; DigiCert NOT SELECTED; Sectigo outside current general-purpose scope under reviewed CPS; no OCSP vendor selected; V07 BLOCKED; V08 OPEN/BLOCKED; Restore OPEN/BLOCKED; E2/E3/E4 NOT ACQUIRED; environment equivalence NOT VERIFIED; staging NOT EXECUTED / NOT AUTHORIZED; production NOT VERIFIED; D3/D4 NOT TESTED; 13 fault vectors historical SYNTHETIC PASS only; RPO/RTO planning targets only; `AI_EXECUTION_ENABLED=false`.
- No provider contact/connection, OCSP query, key/trust-anchor operation, production probe, VPS/runtime/T0/T1/DB/Feeder change, staging, restore, fault injection or workflow dispatch. No CI run or artifact is claimed.
- Next gate: owner review and explicit approval before sending P1.8.66 to GlobalSign. No sending or external action performed automatically.



### P1.8.67 — Provider-neutral TSA architecture assessment (2026-11-09)

- Assessment: `docs/evidence/p1-8/P1.8.67-provider-neutral-tsa-architecture-assessment.md`.
- Document commit: `fb1e3454e598b1928b611a1e99ea8854cccdff58`.
- Verified document blob SHA: `50654f3f4f4caa509598e4393e2634ea977df5dd`.
- Defines TSA as asynchronous optional evidence outside the authoritative T0 write path; ingestion and durable ledger commits must continue during TSA outage.
- Defines exact signed-checkpoint-object binding consistent with P1.8.36; logical durable intent/outbox; unknown submission outcomes; append-only evidence lifecycle; retry/duplicate handling; independent RFC 3161 verification; historical OCSP/CRL preservation; provider-neutral adapter boundary; long-term evidence package; failure matrix and commercial-claim limits.
- RFC references: RFC 3161, RFC 6960 and RFC 9654. RFC 9654 updates RFC 6960 and obsoletes RFC 8954.
- No provider, endpoint, OCSP responder, policy OID, algorithm, checkpoint format, retry threshold, retention duration, accuracy bound, trust anchor, DB/WAL commit semantics or failover model selected. All implementation-dependent and numeric parameters remain OPEN.
- Status: DESIGN ASSESSMENT COMPLETE; INDEPENDENT REVIEW REQUIRED. V07 BLOCKED; V08 OPEN/BLOCKED; Restore OPEN/BLOCKED; E2/E3/E4 NOT ACQUIRED; staging NOT AUTHORIZED; production NOT VERIFIED; `AI_EXECUTION_ENABLED=false`.
- Documentation-only commit. No source/runtime, T0/T1, VPS, DB, Feeder, exchange, ledger, strategy or risk-engine changes; no provider contact, endpoint/OCSP call, key/trust-anchor operation, staging, restore, fault injection or workflow dispatch. Tests/workflows NOT RUN; artifact NONE.
- Next step: independent static review of P1.8.67 against P1.8.36 and P1.8.51–P1.8.66. Keep all OPEN parameters and authorization gates unchanged.



### P1.8.68 — Independent static review of P1.8.67 (2026-11-09)

- Review: `docs/evidence/p1-8/P1.8.68-independent-static-review-provider-neutral-tsa-architecture.md`.
- Review commit: `bde1e14c4e14eecaf13bd9f6637102e874ac5674`.- Verified review blob SHA: `9ae0c50830644d21d850da4c4d246a2837f62fc6`.
- Reviewed P1.8.67 blob SHA: `50654f3f4f4caa509598e4393e2634ea977df5dd`.- Result: PASS within E0 documentary/static scope; no blocking or non-blocking findings. Confirmed write-path independence, exact-signature binding consistent with P1.8.36, limited `genTime` claim, RFC 3161 verification boundary, issuer-bound historical OCSP/CRL, RFC 9654 currency, unknown submission outcome handling, retry/idempotency, provider portability and commercialization-claim limits.- Limitations: no proof of current T0 implementation, DB/WAL boundary, provider interoperability, historical evidence restore, production reliability or commercial/legal readiness.- Status: P1.8.67 DESIGN ASSESSMENT COMPLETE; P1.8.68 REVIEW PASS (E0 only). P1.8.66 DRAFT ONLY / NOT SENT; provider NONE SELECTED; V07 BLOCKED; V08 OPEN/BLOCKED; Restore OPEN/BLOCKED; E2/E3/E4 NOT ACQUIRED; staging NOT AUTHORIZED; production NOT VERIFIED; `AI_EXECUTION_ENABLED=false`.
- No E1 fixture freeze/execution, provider contact, endpoint/OCSP call, key/trust-anchor operation, staging, restore, fault injection, runtime/DB/VPS/Feeder change or workflow dispatch. Tests/workflows NOT RUN; artifact NONE.
- Next gate: decide whether to prepare a separate implementation-neutral evidence-contract decomposition before any source work. Do not infer implementation or execution authorization from the review PASS.



### P1.8.69–P1.8.76 — TSA evidence-contract decomposition and review (2026-11-09)

- P1.8.69 contract decomposition: `docs/evidence/p1-8/P1.8.69-provider-neutral-tsa-evidence-contract-decomposition.md`.
- Initial document commit: `d748e6ffe7f26cf82d54f2a06b6c289f0f674cb3`; initial blob `55eb96514c82b80fc1cf2b390bd1d6ae1ee48236`.
- P1.8.70 static review: commit `f6f4820333681e51b0ddfcf0b3a6e1d3612f28e1`; identified F-17 (MEDIUM): one VERIFIED token could conceal unresolved submission attempts.
- P1.8.69 correction for F-17: commit `ffaa0ce388881d958a843d89d5e6b7d744e8ab6b`; blob `66fbab5d537979fcd028877f1171cef2c6cf3708`. Separated proof availability from attempt/reconciliation state.
- P1.8.72 re-review: commit `296428c01bd4f844b2b8a9e01ada7c6dfd3cbd92`; identified F-18 (LOW): OPEN/RETRYABLE and EXHAUSTED/SETTLED labels could overlap.
- P1.8.69 correction for F-18: commit `450d9597fcd982d286296c4cd2d32d15d6f63e4a`; blob `7f788bb2f084414d42ad5dca1061702ecf0e4794`. Separated attempt resolution from retry disposition.
- Final state-clarity correction: commit `cb77afc65b2ba8864208f530d439aa18c5abb091`; final P1.8.69 blob `caf0943865b096a0d592ae0718472754424991d0`. Explicitly defines attempt-resolution facts as non-exclusive and retry disposition as independent.
- P1.8.76 final static review: `docs/evidence/p1-8/P1.8.76-final-static-review-corrected-evidence-contract.md`; commit `fe7086a40705acfdcdf5cc1eb519054665a6e17e`; verified review blob `f559f642b48f1e7ea1e7f37935d00273d53ba161`.
- Result: P1.8.69 CONTRACT DECOMPOSITION PASS; F-17 and F-18 ADDRESSED; P1.8.76 REVIEW PASS within E0 documentary scope. Distinct checkpoint/intent/attempt/token/verification/revocation/archive identities; unknown outcomes; immutable verification history; provider-neutral adapter boundary; two-dimensional proof/attempt/retry projections confirmed.
- No source/schema/runtime implementation, provider contact, endpoint/OCSP call, key/trust-anchor operation, E1 fixture freeze/execution, E2/E3/E4 acquisition, staging, restore, fault injection, workflow dispatch, VPS/T0/T1/DB/Feeder/exchange/ledger/strategy/risk changes. Tests/workflows NOT RUN; artifact NONE.
- Provider NONE SELECTED; P1.8.66 DRAFT ONLY / NOT SENT; V07 BLOCKED; V08 OPEN/BLOCKED; Restore OPEN/BLOCKED; E1 NOT AUTHORIZED; E2/E3/E4 NOT ACQUIRED; staging NOT AUTHORIZED; production NOT VERIFIED; `AI_EXECUTION_ENABLED=false`.
- Next gate: any source/schema implementation proposal must first map the actual T0 checkpoint, DB/WAL durability, storage and lifecycle contracts and obtain separate bounded owner approval. These documentation PASS results do not authorize implementation or operational execution.



### P1.8.77 / P1.8.78 — Read-only T0 source mapping for TSA compatibility (2026-11-09)

- P1.8.77 report: `docs/evidence/p1-8/P1.8.77-read-only-t0-source-mapping-tsa-compatibility.md`; commit `5bb3f626c14e2724f0c20f479929836136a8a0f0`; verified blob `35057494b5b3c240e636cfdea3505e8870361ca5`.
- Read-only source scope: `feature/t0-centralized-data-feeder-p1-20261101`; inspected market_data README, store/storage/Feeder/write-gateway/PostgreSQL code and migrations 001–004. Individual source blob SHAs are recorded in P1.8.77.
- Finding F-19 (HIGH): inspected T0 path is a closed-candle store/Feeder, not a signed event ledger. No checkpoint/seal object, signing-key lifecycle, timestamp-intent/outbox, RFC 3161 verifier or TSA evidence archive exists in the inspected market_data source/migrations.
- Current SQLite write path uses `BEGIN IMMEDIATE`, lease checks and explicit commit/rollback; WAL mode is enabled, but project-specific synchronous/fsync/failure-domain guarantees are not established by inspected application source.
- Current PostgreSQL write path invokes the fenced candle function inside a transaction context; application-level `synchronous_commit`, replication and storage failure-domain guarantees are not established by inspected source.
- Scheduler completion boundary is in-memory in the inspected FeederScheduler. API `datasetVersion` is a SHA-256 over the selected read-window response, not the whole database or a persisted checkpoint.
- Critical distinction recorded: (A) dataset/checkpoint proof-of-existence over a deterministic manifest digest; versus (B) P1.8.36 signed-object historical verification requiring exact signature bytes/context and a signer/key lifecycle. These are distinct assurance claims and must not be conflated.
- P1.8.78 static review: `docs/evidence/p1-8/P1.8.78-independent-review-t0-source-mapping.md`; commit `173b615089efa495ee4a679ff790e54226e562b7`; verified review blob `4794a531befa0bf1ce2fbb428ae466fcb6a280a9`. Result PASS within inspected source scope; no additional finding. F-19 remains OPEN/HIGH pending owner use-case decision.
- Status: read-only source mapping COMPLETE; current implementation is not TSA-capable; provider NONE SELECTED; P1.8.66 DRAFT ONLY / NOT SENT; V07 BLOCKED; V08 OPEN/BLOCKED; Restore OPEN/BLOCKED; DB/WAL durability and production failure-domain equivalence NOT VERIFIED; E1 NOT AUTHORIZED; E2/E3/E4 NOT ACQUIRED; staging NOT AUTHORIZED; production NOT VERIFIED; `AI_EXECUTION_ENABLED=false`.
- No source/schema/runtime/database/VPS/Feeder/exchange change; no provider contact, endpoint/OCSP call, data probe, test, workflow dispatch, staging, restore or fault injection. No CI run or artifact claimed.
- Next gate: owner chooses TSA assurance subject: A (dataset/checkpoint proof-of-existence), B (signed-object historical verification), or A+B as separately versioned products. No source design or provider operation until the decision is explicit.

### P1.8.79 — Deletion Mechanism Gap Assessment (2026-11-09)

- Assessment: `docs/evidence/p1-8/P1.8.79-deletion-mechanism-gap-assessment.md`.
- Assessment commit: `ba951f4f9872422ddb072290d9149401f85d5de9`.
- Reviewed deletion safety contract, consumer contract, central lifecycle policy, copy lifecycle contract, static dataset/consumer inventory, shared lifecycle cross-contract review, and environment evidence boundary on `feature/t0-centralized-data-feeder-p1-20261101`.
- Result: **PARTIAL** — governance/authority separation, fail-closed rules, exact-scope intent, ACK-vs-release distinction, no-cascade rule, cancellation/reconciliation direction, and no-implementation boundary are established at design level.
- Gaps recorded: class-by-class retention/eligibility decisions; T0 canonical deletion default; consumer archive-availability vocabulary; authoritative registry consistency/availability; manifest canonicalization and object-resolution proof; approval quorum/separation model; grace/cancellation/authorization/evidence-freshness parameters; legal/emergency governance; runtime copy inventory and restore/rebuild evidence; tombstone/audit lifecycle; adapter-specific safeguards; independent verifier/oracle; deterministic deletion acceptance matrix.
- Next: P1.8.80 Retention and Eligibility Policy, then P1.8.81 Dependency and Consumer Governance, P1.8.82 Authorization and Execution Contract, P1.8.83 Copy and Evidence Lifecycle, P1.8.84 Acceptance Matrix, followed by independent static review. Do not begin V07/V08/Restore/TSA conflict review before deletion design completion and independent review.
- No source/schema/API/workflow/service/registry/scheduler/storage/runtime change; no VPS/DB access; no tests or CI run; no workflow dispatch or artifact. No retention values or deletion permissions selected. No destructive operation authorized. `AI_EXECUTION_ENABLED=false`.
- Status: DESIGN GAP ASSESSMENT COMPLETE; DELETION MECHANISM PARTIAL / NOT IMPLEMENTED / NOT ACTIVE / NOT AUTHORIZED.

### P1.8.80 — Retention and Eligibility Policy (2026-11-09)

- Policy decomposition: `docs/evidence/p1-8/P1.8.80-retention-and-eligibility-policy.md`.
- Document commit: `3d059cedbd5ce548ebfa7c229ab18a267c1a205b`.
- Defines class-by-class retention and disposition posture across T0 canonical candles/metadata/feeder controls, T1 raw observations/derived snapshots/sidecar evidence, T2 inputs/features/training/models/predictions, T3 CORE_LEDGER/AI_LEDGER and execution/reconciliation state, T4 read models/caches, CI evidence, governance records, and backup/replica/export/local copies.
- Separates PROTECTED, RETAIN_UNTIL_REVIEW, ARCHIVE_REVIEWABLE, DELETION_REVIEWABLE, BLOCKED_UNKNOWN and OPEN_OWNER_DECISION. These are policy outcomes, not runtime enums or execution permissions.
- T0 canonical deletion remains OPEN; no deletion permission inferred. No dataset class is authorized for deletion. Archive is blocked where consumer availability/latency/restore requirements are unknown; P1.8.81 owns that contract gap.
- Retention remains demand/obligation-based. No numeric retention floor, TTL, grace period, approval quorum, authorization lifetime or evidence-freshness window was invented. Rebuildability requires exact-source and transformation evidence.
- RET-01–RET-10 owner decisions and missing evidence are recorded explicitly. CORE_LEDGER and AI_LEDGER remain separate; no copy cascade.
- Status: DOCUMENTARY POLICY DECOMPOSITION COMPLETE; OWNER DECISIONS OPEN; NOT IMPLEMENTED / NOT ACTIVE / NOT AUTHORIZED.
- No source/schema/API/workflow/service/registry/scheduler/storage/runtime change; no VPS/DB access; no tests/CI, deletion dry-run, archive, vacuum, cleanup, restore, fault injection or destructive operation. Workflow run/artifact: NONE.
- Next: P1.8.81 Dependency and Consumer Governance; close normative availability/latency/restore vocabulary, authoritative registry consistency and dependency reconciliation. Do not begin V07/V08/Restore/TSA conflict review before P1.8.84 and independent deletion-design review.

### P1.8.81 — Dependency and Consumer Governance Contract (2026-11-09)

- Contract: `docs/evidence/p1-8/P1.8.81-dependency-and-consumer-governance-contract.md`.
- Contract commit: `6cae08c666c5780e3cd28a5244a48b3d1e3ba1a8`.
- Defines mandatory consumer availability declarations: access pattern, qualitative availability class, owner-supplied latency/restore bounds, completeness, consistency, degraded mode and restore evidence.
- Defines qualitative classes ONLINE_REQUIRED, DEGRADED_ACCESS_ACCEPTABLE, RESTORE_ON_DEMAND, REBUILD_FROM_RETAINED_INPUTS, NO_CURRENT_DEPENDENCY and UNKNOWN. These are design vocabulary only; no numeric SLO, SLA, RPO/RTO, or runtime enum is activated.
- Archive is blocked when any consumer requirement is unknown, the registry is unavailable/inconsistent, an unregistered consumer is suspected, or restore evidence is missing.
- Defines logical authoritative registry requirements: durable acknowledged commits, atomic uniqueness/transitions, authoritative decision barrier, fail-closed partition/recovery behavior, audit continuity. No registry technology/topology is selected.
- Stale replicas/read models cannot prove dependency absence. Heartbeat loss, timeout, ACK, review date or consumer decommissioning never auto-release dependency.
- Adds reconciliation outcomes for active/released, transfer pending, unreachable/owner unknown, registry unavailable, evidence conflict, ambiguous state and suspected unregistered consumers. Unknown/mismatch remains protective.
- T0–T4 and independent backup/replica/export lifecycle boundaries retained. No dependency governance operation grants archive/deletion authority.
- Open GOV-01–GOV-12: registry technology, consistency/commit proof, recovery evidence, consumer-specific bounds, freshness/reconciliation intervals, identity/delegation, registration enforcement, operational cadence, RPO/RTO/SLO, audit authority, exceptional adjudication, and runtime inventory.
- Status: DOCUMENTARY CONTRACT DESIGN COMPLETE; IMPLEMENTATION DECISIONS/RUNTIME EVIDENCE OPEN; NOT IMPLEMENTED / NOT ACTIVE / NOT AUTHORIZED.
- No source/schema/API/workflow/service/registry/scheduler/database/VPS/Feeder/storage/copy/runtime change. No tests/CI, workflow dispatch, deletion dry-run, archive, cleanup, vacuum, restore, fault injection or destructive operation. Workflow run/artifact: NONE.
- Next: P1.8.82 Deletion Authorization and Execution Contract. Do not begin V07/V08/Restore/TSA conflict review before P1.8.84 and independent deletion-design review.

### P1.8.82 — Deletion Authorization and Execution Contract (2026-11-09)

- Contract: `docs/evidence/p1-8/P1.8.82-deletion-authorization-and-execution-contract.md`.
- Contract commit: `eb7c1b5a8779e72bf5d7146c82f986629b540d7c`.
- Defines separation of duties for requester, steward, consumer owner, lifecycle reviewer, independent approver, execution authority, storage executor, independent verifier and auditor. Requester/approver must differ; executor cannot approve or authorize itself; verifier must independently establish outcome.
- Requires immutable exact-scope manifest with canonical digest, dataset/version/object identities, operation, storage namespace, lineage/copy identity, policy version, dependency decision point, holds, recovery/copy evidence, actors and verification method. Wildcards, mutable aliases, dynamic predicates and unreviewed scope expansion are prohibited.
- Approval package is immutable; manifest, policy, dependency, hold, owner, evidence, actor, adapter or verification changes invalidate approval and require re-review.
- Separates approval from narrow, single-purpose execution authorization. Final rechecks cover manifest, current policy, authoritative dependency state, holds, copies, evidence, separation of duties, adapter capabilities and cancellation.
- Defines cancellation/revocation races, executor capability boundaries, idempotency, ambiguous/partial outcomes, interruption handling and independent post-operation verification. No blind retry or inferred rollback.
- Executor cannot decide eligibility, release dependencies/holds, widen scope, cascade copies or self-certify completion. Executor success alone is not VERIFIED_COMPLETE.
- AUTH-01–AUTH-14 remain OPEN/MISSING where appropriate: approval quorum/compensating controls, identity/MFA/delegation, manifest canonicalization/digest/signature, grace/cancellation, approval/authorization lifetime, evidence freshness, revocation race control, idempotency durability, adapter enforcement, independent verifier, audit authority/retention, partial recovery, exceptional authority and separately approved non-production test.
- Status: DOCUMENTARY CONTRACT DESIGN COMPLETE; IMPLEMENTATION DECISIONS/ADAPTER EVIDENCE OPEN; NOT IMPLEMENTED / NOT ACTIVE / NOT AUTHORIZED.
- No source/schema/API/workflow/service/registry/scheduler/database/VPS/Feeder/storage/backup/replica/archive/runtime change. No tests/CI, workflow dispatch, deletion dry-run, cleanup, vacuum, restore, fault injection or destructive operation. Workflow run/artifact: NONE.
- Next: P1.8.83 Copy and Evidence Lifecycle Closure, including copy identity/inventory completeness, backup-chain disposition, tombstone/audit evidence lifecycle and adapter safeguards at contract level. Do not begin V07/V08/Restore/TSA conflict review before P1.8.84 and independent deletion-design review.

### P1.8.83 — Copy and Evidence Lifecycle Closure (2026-11-09)

- Contract supplement: `docs/evidence/p1-8/P1.8.83-copy-and-evidence-lifecycle-closure.md`.
- Contract commit: `b3c47969aef06643c9457de316abc132ad7cce8c`.
- Closes design-level gaps for copy inventory completeness, backup-chain/recovery-point governance, evidence and tombstone lifecycle, and adapter-specific safety requirements.
- Defines per-boundary inventory outcomes VERIFIED_COMPLETE_WITHIN_SCOPE, PARTIAL, UNKNOWN, CONFLICTED, STALE and NOT_APPLICABLE. Registry presence or recent observation alone cannot prove completeness. Runtime copy inventory remains NOT VERIFIED.
- Requires exact copy/source identity, immutable version, scope, lineage, owner, location, consistency point, integrity, dependencies, holds, recovery and distribution evidence. Unknown or unmanaged copies remain protective.
- Defines recovery-point identity across base/incremental/log chains, metadata and encryption-key dependencies; backup upload/checksum/job success is not restore proof. No chain pruning, backup expiry, restore or key destruction is authorized.
- Defines decision/execution/verification/lineage/recovery evidence classes and tombstone minimum metadata. Payload, credentials, key material and unnecessary sensitive data are excluded. Evidence/tombstone retention remains OPEN and separately governed.
- Adds contract-level safeguards for SQLite/filesystem (including WAL/journal/sidecars and path identity), PostgreSQL (WAL/replication/partitions/dependencies), object storage (immutable versions, delete markers, replication and lifecycle rules), exports/local copies (recipient and destination scope), and caches/materializations/model artifacts (exact lineage and rebuildability).
- Adapter approval requires exact-scope enforcement, fail-closed authorization, concurrency/precondition protection, durable idempotency, interruption handling, no cascade, independent verification, recovery/audit preservation and negative-test evidence. No adapter is implemented or approved.
- Open decisions COPY-INV-01–03, COPY-REC-01–03, COPY-EVD-01–02, COPY-ADP-01–06, COPY-POL-01 and COPY-ENV-01 remain OPEN, NOT VERIFIED, NOT IMPLEMENTED or NOT DESIGNATED as specified in the contract.
- Status: DOCUMENTARY DESIGN CLOSURE COMPLETE; RUNTIME COPY INVENTORY NOT VERIFIED; ADAPTERS NOT IMPLEMENTED; NOT ACTIVE / NOT AUTHORIZED.
- No source/schema/API/workflow/service/registry/scheduler/database/VPS/Feeder/storage/backup/replica/archive/runtime change. No tests/CI, workflow dispatch, runtime inventory, deletion dry-run, cleanup, vacuum, restore, fault injection or destructive operation. Workflow run/artifact: NONE.
- Next: P1.8.84 Deletion Acceptance and Negative-Case Matrix. Consolidate end-to-end acceptance gates, fail-closed vectors, evidence requirements and non-goals across P1.8.79–P1.8.83. After P1.8.84, perform an independent deletion-design review before any V07/V08/Restore/TSA conflict review.

### P1.8.84 — Deletion Acceptance and Negative-Case Matrix (2026-11-09)

- Matrix: `docs/evidence/p1-8/P1.8.84-deletion-acceptance-and-negative-case-matrix.md`.
- Matrix commit: `8fbda4c1e26621c5eb165c120818e52936cc8583`.
- Consolidates P1.8.79–P1.8.83 and governing lifecycle contracts into 15 end-to-end gates from scope/authority through post-closure monitoring.
- Defines acceptance vocabulary distinguishing DESIGN_DEFINED, EVIDENCE_REQUIRED, OPEN_DECISION, NOT_IMPLEMENTED, BLOCKED, NOT_VERIFIED and ACCEPTED_DESIGN_ONLY; documentary design status is explicitly not runtime acceptance.
- Adds 45 negative cases covering identity/role separation, immutable manifest, policy/evidence changes, registry and consumer uncertainty, ACK vs release, holds, copy/backup/recovery gaps, T0/T3 protected state, archive/rebuildability, authorization/cancellation races, adapter scope, idempotency, ambiguous/partial execution, independent verification, residuals, audit evidence and prohibited TTL/age-based deletion.
- Consolidates cross-domain invariants and protected boundaries for T0–T4, CI/research evidence, copies and governance/audit/tombstones.
- Defines the required future acceptance evidence package, including exact SHA, immutable vector, isolated synthetic fixture, manifest digest, dependency/hold/copy/recovery snapshots, actual observations, independent verification and artifact provenance when a workflow is separately authorized.
- ACC-01–ACC-17 remain OPEN, NOT VERIFIED, NOT IMPLEMENTED, NOT AUTHORIZED or NOT DESIGNATED as stated. No numeric retention/grace/freshness/quorum/lifetime/RPO/RTO/provider is selected.
- P1.8.79–P1.8.84 documentary design work is ready for independent review only; this is not production acceptance and grants no deletion/archive/cleanup authority.
- Status: DOCUMENTARY MATRIX COMPLETE; INDEPENDENT REVIEW PENDING; TESTS/CI NOT RUN; NOT IMPLEMENTED / NOT ACTIVE / NOT AUTHORIZED.
- No source/schema/API/workflow/service/registry/scheduler/database/VPS/Feeder/storage/backup/replica/archive/runtime change. No tests/CI, workflow dispatch, runtime inventory, deletion dry-run, cleanup, vacuum, restore, fault injection or destructive operation. Workflow run/artifact: NONE.
- Next: independent deletion-design review of P1.8.79–P1.8.84 and governing contracts. Assess completeness, contradictions, missing failure modes, authority separation and testability. Do not begin V07/V08/Restore/TSA conflict review until this review is complete.

### Independent Deletion-Design Review — P1.8.79–P1.8.84 (2026-11-09)

- Review: `docs/evidence/p1-8/INDEPENDENT-DELETION-DESIGN-REVIEW-P1.8.79-84.md`.
- Initial review commit: `e0ef71b068f57e6f1ed9d053362344542e8e9cbf`.
- Exact evidence SHA pinning update commit: `1e36d8b56975c56c04a57b81b8486715cee2a9dc`.
- Review blob SHA after pinning: `2439a48bcb6c74bce9e6844a168a347e01219abe`.
- Verdict: **PARTIAL — design principles coherent; material closure gaps remain.** No unsafe contradiction was found that grants or implies destructive authority.
- Reviewed governing evidence includes:
  - Data Deletion Safety Contract blob `e055d88308d8576c5c6826e12280b847f5ec5717`;
  - Central Data Lifecycle Policy blob `9fd46c029cff643ccc35492fd09620581f6eff35`;
  - Dataset Consumer Contract blob `31d958360315eb24716a7656cef8b430187c82b1`;
  - Copy/Backup/Replica Lifecycle Contract blob `4112c68eceef7d9047117efc5027750ae2edf2d8`;
  - Shared Data Foundation blob `18f8566723b95c4b38586e3848bde5305295a4dc`;
  - P1.8.79 blob `4942433048d1e052e989a9a9bca9a1a2ce3433ab`;
  - P1.8.80 blob `a38710c9d01e5409ce989cc73f791c94bc73773f`;
  - P1.8.81 blob `f1423d16e0327f47e2b974ae13e622174c5a0cb6`;
  - P1.8.82 blob `99f7e5a4cdcdf3edf88c424dde30e8306ad78aae`;
  - P1.8.83 blob `3020dbeb47d54b41fa6b7608ddf2721f83b5b47e`;
  - P1.8.84 blob `99b2e688075b0b39e84fc1a07673ebd2a7e69a62`.
- Findings:
  - DR-01 MAJOR: hold lifecycle, propagation and concurrent change semantics incomplete.
  - DR-02 MAJOR: no single canonical state-machine mapping across dataset/dependency/copy/request/authorization/object/evidence domains.
  - DR-03 MAJOR: registry/hold decision barrier is not fenced through the full multi-object mutation window.
  - DR-04 MAJOR: storage disposition semantics and bounded deletion claims are not normalized per adapter.
  - DR-05 MAJOR: personal-project requester/approver identity and compensating-control model is not approved/operable.
  - DR-06 MAJOR: runtime and unmanaged external-copy inventory completeness remains unproven.
  - DR-07 MAJOR: 45 negative cases are not yet deterministic executable test specifications with independent oracles.
  - DR-08 MAJOR: trusted time, event ordering and evidence freshness are not operationally bound.
  - DR-09 MINOR: copy lifecycle contract section numbering has §5.6 before §5.5.
  - DR-10 OBSERVATION: no unsafe cross-contract contradiction found in the reviewed design set.
- T0 canonical data and T3 CORE_LEDGER/AI_LEDGER protection remain intact. No deletion authority is granted.
- Tests/CI NOT RUN; workflow run/artifact NONE; runtime evidence NOT VERIFIED. No source/schema/API/workflow/service/registry/scheduler/database/VPS/Feeder/storage/backup/replica/archive/runtime mutation or inventory was performed.
- Next documentary work, in order:
  1. P1.8.85 Hold Lifecycle and Mutation-Window Fencing Contract (DR-01, DR-03).
  2. P1.8.86 Canonical Lifecycle State Mapping (DR-02).
  3. P1.8.87 Storage Disposition Semantics and Bounded Claims (DR-04).
  4. P1.8.88 Identity, Trusted Time and Approval Governance (DR-05, DR-08).
  5. P1.8.89 Inventory Claim Boundaries and Discovery Evidence (DR-06).
  6. P1.8.90 Executable Negative-Case Specification (DR-07), design-only; no test run without separate authorization.
  7. Correct section numbering in the copy lifecycle contract.
  8. Second independent review.
- Do not begin V07/V08/Restore/TSA conflict review until second independent deletion-design review is complete. No implementation, staging, workflow dispatch, real-storage dry-run, archive, cleanup, restore, key destruction or deletion is authorized.

### P1.8.85 hold lifecycle and mutation window fencing contract (2026-11-09)

- Document: `docs/evidence/p1-8/P1.8.85-hold-lifecycle-and-mutation-window-fencing-contract.md`.
- Commit: `a290d7e4012622fadf952de9a363e1fa59f22640`.
- Blob SHA: `95d7c2655c327675e493851cdec2371da13b889a`.
- Status: DOCUMENTARY DESIGN ONLY; NOT IMPLEMENTED / NOT ACTIVE / NOT AUTHORIZED.
- Tests/CI NOT RUN; workflow run/artifact NONE; runtime evidence NOT VERIFIED.
- No source, schema, API, workflow, service, registry, scheduler, database, VPS, Feeder, storage, backup, replica, archive or runtime mutation. No real-data inventory or destructive operation.

### P1.8.86 canonical lifecycle state mapping (2026-11-09)

- Document: `docs/evidence/p1-8/P1.8.86-canonical-lifecycle-state-mapping.md`.
- Commit: `a3d2bac7736a82b2b45813d370e1f90aacaa509b`.
- Blob SHA: `41bfe76e4afd2e26526684fc71a3070c651df566`.
- Status: DOCUMENTARY DESIGN ONLY; NOT IMPLEMENTED / NOT ACTIVE / NOT AUTHORIZED.
- Tests/CI NOT RUN; workflow run/artifact NONE; runtime evidence NOT VERIFIED.
- No source, schema, API, workflow, service, registry, scheduler, database, VPS, Feeder, storage, backup, replica, archive or runtime mutation. No real-data inventory or destructive operation.

### P1.8.87 storage disposition semantics and bounded claims (2026-11-09)

- Document: `docs/evidence/p1-8/P1.8.87-storage-disposition-semantics-and-bounded-claims.md`.
- Commit: `3f68ce5ddfffd26f02ce0ce4ba036a296b60cba2`.
- Blob SHA: `f803f7c14b6054e36fb8313329e25e38cdb8ff78`.
- Status: DOCUMENTARY DESIGN ONLY; NOT IMPLEMENTED / NOT ACTIVE / NOT AUTHORIZED.
- Tests/CI NOT RUN; workflow run/artifact NONE; runtime evidence NOT VERIFIED.
- No source, schema, API, workflow, service, registry, scheduler, database, VPS, Feeder, storage, backup, replica, archive or runtime mutation. No real-data inventory or destructive operation.

### P1.8.88 identity trusted time and approval governance (2026-11-09)

- Document: `docs/evidence/p1-8/P1.8.88-identity-trusted-time-and-approval-governance.md`.
- Commit: `e83e5f332f004ddc214f18c4bb28c088b6db61c5`.
- Blob SHA: `7cdc8647823596925df9d991963ec11660078d7f`.
- Status: DOCUMENTARY DESIGN ONLY; NOT IMPLEMENTED / NOT ACTIVE / NOT AUTHORIZED.
- Tests/CI NOT RUN; workflow run/artifact NONE; runtime evidence NOT VERIFIED.
- No source, schema, API, workflow, service, registry, scheduler, database, VPS, Feeder, storage, backup, replica, archive or runtime mutation. No real-data inventory or destructive operation.

### P1.8.89 inventory claim boundaries and discovery evidence (2026-11-09)

- Document: `docs/evidence/p1-8/P1.8.89-inventory-claim-boundaries-and-discovery-evidence.md`.
- Commit: `5029d1b324478ea51dc6e439de81b2c7f502cf5e`.
- Blob SHA: `bfc84ed0dcf565f44041782ea6c0cc0f67422453`.
- Status: DOCUMENTARY DESIGN ONLY; NOT IMPLEMENTED / NOT ACTIVE / NOT AUTHORIZED.
- Tests/CI NOT RUN; workflow run/artifact NONE; runtime evidence NOT VERIFIED.
- No source, schema, API, workflow, service, registry, scheduler, database, VPS, Feeder, storage, backup, replica, archive or runtime mutation. No real-data inventory or destructive operation.

### P1.8.90 — Executable Negative-Case Specification (2026-11-09)

- Document: `docs/evidence/p1-8/P1.8.90-executable-negative-case-specification.md`.
- Commit: `43ca42452d9d0b58dfa34c87899fde561887435f`.
- Blob SHA: `8014ef15f347d255ee3d02f6f28847a02db27aff`.
- Converts P1.8.84 and P1.8.85–P1.8.89 into deterministic future test specifications, including 47 minimum vectors, deterministic concurrency barriers, independent oracle requirements, result vocabulary and evidence package.
- Test design only: no test code, fixture, workflow or CI job created; no tests executed.
- Status: TEST DESIGN ONLY; NOT EXECUTED / NOT IMPLEMENTED / NOT AUTHORIZED.
- Tests/CI NOT RUN; workflow run/artifact NONE; runtime evidence NOT VERIFIED. No source/runtime/storage/VPS/database mutation or inventory; no archive, cleanup, restore, vacuum, key destruction or deletion.

### Copy Lifecycle Contract — section numbering correction (2026-11-09)

- Document: `docs/architecture/DATA_COPY_BACKUP_REPLICA_LIFECYCLE_CONTRACT.md`.
- Commit: `5b6b5b66bd1375ceb6479db01f5263fc03abdda3`.
- Blob SHA: `639e5ee5b5a78130cc523a4bcab8b77c0a0a5463`.
- Corrected §5.6/§5.5 ordering: Hold inheritance is now §5.5; Evidence copies is now §5.6. Content and lifecycle authority are unchanged.
- Read-back confirms §5.5 precedes §5.6. No source/runtime or destructive operation.

### P1.8.91 — Second Independent Deletion-Design Review (2026-11-09)

- Review: `docs/evidence/p1-8/P1.8.91-second-independent-deletion-design-review.md`.
- Commit: `d79c6791a9988b8dcd52647551418c1c5a5457c3`.
- Review blob SHA: `be3b4839fdb048b428c2b46ced5e4afc3e360223`.
- Verdict: **PARTIAL — second independent design review complete; material design, owner and implementation gaps remain.** No unsafe cross-contract authority escalation found.
- Findings: SR-01 MAJOR state-vocabulary crosswalk; SR-02 MAJOR mutation-window fencing mechanism; SR-03 MAJOR test traceability/missing race vectors; SR-04 MAJOR personal-project independent approver model not approved; SR-05 MAJOR archive availability contract alignment; SR-06 MAJOR trusted identity/time/freshness not bound; SR-07 MAJOR runtime/external-copy inventory NOT VERIFIED; SR-08 MAJOR adapters/verifier NOT IMPLEMENTED; SR-09 MAJOR retention/deletion owner decisions OPEN; SR-10 MINOR P1.8.90 title clarity; SR-11 numbering correction verified; SR-12 no unsafe authority escalation observed.
- Copy lifecycle numbering correction: commit `5b6b5b66bd1375ceb6479db01f5263fc03abdda3`; blob `639e5ee5b5a78130cc523a4bcab8b77c0a0a5463`; §5.5 Hold inheritance precedes §5.6 Evidence copies.
- Tests/CI NOT RUN; workflow run/artifact NONE; runtime evidence NOT VERIFIED. No source/runtime/database/VPS/storage change or inventory; no destructive operation.
- Next: remediate documentary SR-01/SR-02/SR-03/SR-05, then focused independent re-review. Keep identity/time/retention owner decisions OPEN. Do not begin V07/V08/Restore/TSA conflict review while material findings remain unresolved.

### P1.8.92 — Canonical State Transition Crosswalk (2026-11-09)

- Document: `docs/evidence/p1-8/P1.8.92-canonical-state-transition-crosswalk.md`.
- Commit: `c589e3fdffb5a565d36a6c0bbe10132c53fe96f1`.
- Blob SHA: `0e74e1fd29abbc9328fe355a7b59d72d7de58a17`.
- Resolves SR-01 with canonical request states, legacy-label crosswalk, transition authorities/events, domain-state separation, terminality and re-entry rules.
- Does not collapse dataset/dependency/hold/copy/approval/authorization/object/evidence domains; no runtime state machine or implementation selected.
- Tests/CI NOT RUN; workflow run/artifact NONE; runtime evidence NOT VERIFIED. No source/runtime/database/VPS/storage or destructive operation.

### P1.8.93 — Registry-to-Storage Mutation Fencing Protocol (2026-11-09)

- Document: `docs/evidence/p1-8/P1.8.93-registry-to-storage-mutation-fencing-protocol.md`.
- Commit: `4b3dcc00fa2eef0d7d1d687e7cc91e1b528d0e6e`.
- Blob SHA: `8b3ee3a332f9a91616fb6cb8fadcac7c29e1be2d`.
- Resolves SR-02 at abstract design level: protected decision vector, one mutation linearization point, per-object conditional mutation, race ordering, multi-object partial outcomes, adapter proof requirements and deterministic race catalogue.
- Explicitly disqualifies read-then-write, polling, heartbeat/cache invalidation and lease-only substitutes. If registry/storage cannot prove atomic coupling, adapter remains INELIGIBLE. No provider/transaction product selected.
- Tests/CI NOT RUN; workflow run/artifact NONE; runtime evidence NOT VERIFIED. No source/runtime/database/VPS/storage change or destructive operation.

### P1.8.94 — Negative Test Traceability and Missing Race Vectors (2026-11-09)

- Document: `docs/evidence/p1-8/P1.8.94-negative-test-traceability-and-missing-race-vectors.md`.
- Commit: `8b4ad817449a83e79f69d584591128c05bef8509`.
- Blob SHA: `01277c46bdebf52a2d48fa7be64eb9aaaa6c5639`.
- Resolves SR-03: explicit N01–N45 traceability to baseline P1.8.90 vectors; adds supplemental deterministic vectors for uncovered owner/heartbeat/bypass/hold/copy/recovery/availability/authorization/cascade/audit/policy/T0/scope races. Minimum catalogue: 69 vectors (47 baseline + 22 supplemental).
- All vectors remain NOT_RUN; test runner, synthetic adapters, independent oracle and separate test approval remain OPEN. No test code or workflow created.
- Tests/CI NOT RUN; workflow run/artifact NONE; runtime evidence NOT VERIFIED. No source/runtime/database/VPS/storage change or destructive operation.

### P1.8.95 — Consumer Availability Contract Alignment (2026-11-09)

- Alignment record: `docs/evidence/p1-8/P1.8.95-consumer-availability-contract-alignment.md`.
- Record commit: `f4b828a13748ae6e60b3e2a129f77db154e11689`.
- Record blob SHA: `10a2bbef6e8ebe27f5d839f7fb5401448d1e5359`.
- Governing contract updated: `docs/architecture/DATASET_CONSUMER_CONTRACT.md`, §20 normative extension v1; update commit `8d326ae6b41292e14609b0f579bdca59ff916e56`; blob `ef5e946b26ad17410023a79a765be73aeb198f0f`.
- Resolves SR-05 at documentary alignment level: owner-attributed per-dependency availability declaration, qualitative classes, UNKNOWN/CONFLICTED protective behavior, most-protective compatible requirement, immutable revisions, ACK/release separation and archive admission gates.
- Numeric latency/restore/freshness values, trusted time, registry/provider, runtime declarations and discovery completeness remain OPEN/NOT VERIFIED. No archive or deletion authority.
- Tests/CI NOT RUN; workflow run/artifact NONE; runtime evidence NOT VERIFIED. No source/runtime/database/VPS/storage or destructive operation.


### P1.8.93 / P1.8.94 review-preparation corrections (2026-11-09)

- P1.8.93 now explicitly pins applicable consumer availability-declaration revisions and owner-attestation references in the protected decision vector. Updated blob: `4cc158b5f766fb024e411519be36076bc1e3758a`.
- P1.8.94 adds explicit vectors for unproven reviewer/approver separation (NEG-ID-05), unavailable independent verifier (NEG-VER-01), and inventory completeness without a declared boundary (NEG-INV-01). It corrects cascade vector identity to NEG-ADP-09 and minimum catalogue count to 69 (47 baseline + 22 supplemental). Updated blob: `cd2ae56f98b96a2271e8dcf02494c2061abe2572`.
- These are documentary corrections only; all vectors remain NOT_RUN.


### P1.8.93 / P1.8.94 review-preparation corrections (2026-11-09)

- P1.8.93 now explicitly pins applicable consumer availability-declaration revisions and owner-attestation references in the protected decision vector. Updated blob: `4cc158b5f766fb024e411519be36076bc1e3758a`.
- P1.8.94 adds explicit vectors for unproven reviewer/approver separation (NEG-ID-05), unavailable independent verifier (NEG-VER-01), and inventory completeness without a declared boundary (NEG-INV-01). Cascade vector is NEG-ADP-09. Updated branch blob: `40d8e30bb7e247fbc81f1657998d13032650590a`. Minimum catalogue: 69 vectors (47 baseline + 22 supplemental); all remain NOT_RUN.
- A file creation was inadvertently sent to the repository default branch during this correction (commit `9099e4ffc7f58d700cd3886425e86225e6d0f9cc`), followed by a content update (commit `cbf41b04b47bfaad287bcebb51a610ed41cdccdc`) and deletion (commit `1599e5f4d9a9b23e0295d1ab8073f92ab0473761`). Final default-branch read-back returned NOT_FOUND, restoring the prior absence of this file; the default-branch history retains the create/update/delete commits. No source/runtime files were involved. Project work continues only on `feature/t0-centralized-data-feeder-p1-20261101`.


### P1.8.94 coverage closure correction (2026-11-09)

- Final branch document blob: `5388a9186e6acaf9dc0869acfa9e54af98055584`; commit: `5d0ca0bd1987295ee214c356588915288d7d0e61`.
- Added missing explicit vectors for reviewer/approver separation (NEG-ID-05), independent verifier unavailable (NEG-VER-01), and inventory completeness without a declared boundary (NEG-INV-01). The cascade vector remains NEG-ADP-09.
- Full traceability remains N01–N45; minimum catalogue is 69 vectors: 47 baseline + 22 supplemental. All are specifications only and NOT_RUN.

### P1.8.92 / P1.8.94 quality corrections before independent review (2026-11-09)

- P1.8.92 now explicitly maps the exact P1.8.86 alias `AWAITING_EXECUTION_AUTHORIZATION` to FINAL_RECHECK. Updated blob: `20bc00017200969acdf8675b6837ec458301c25d`.
- P1.8.94 removed duplicate supplemental rows for NEG-VER-01 and NEG-INV-01 and labels the traceability column as P1.8.90/P1.8.94 vector mapping. Unique catalogue remains 69 vectors: 47 baseline + 22 supplemental. Updated blob: `c9fd74ef74be96cdc4ce31469715d563db98c022`.


### P1.8.94 unique supplemental vector verification (2026-11-09)

- Final P1.8.94 blob: `0e25c253ecc0f0a2657e2b4056a97222b3e92877`; commit: `c4a8f53a73ff21a1ed97474a6dcbadba3321d449`.
- Verified 45 distinct traceability rows and 22 unique supplemental vector IDs, including explicit NEG-ID-05, NEG-VER-01 and NEG-INV-01. No duplicate supplemental IDs remain.
- Total specified vectors: 69 (47 baseline + 22 supplemental); NOT_RUN.

### P1.8.96 — Independent Review of P1.8.92–P1.8.95 (2026-11-09)

- Review: `docs/evidence/p1-8/P1.8.96-independent-review-of-p1-8-92-to-95.md`.
- Commit: `853dc7edf834f005f93aa1f15443354e0961cc61`.
- Blob SHA: `5c8d3d8886269929bc8ac83ee4fc15c3aaaf9911`.
- Verdict: **PARTIAL — remediation review complete; IR-01/IR-02/IR-03 MAJOR and IR-04 MINOR remain.**
- IR-01 MAJOR: BLOCKED/reconciliation/expiry/revocation transition authority and events incomplete.
- IR-02 MAJOR: N19 backup-chain ambiguity and N24 ledger-obligation mappings overstate vector coverage.
- IR-03 MAJOR: N09 missing evidence/provenance uncertainty not directly tested.
- IR-04 MINOR: N36 residual references/indexes not directly isolated.
- IR-05 OBSERVATION: P1.8.93 fencing protocol is conservative; no adapter qualified.
- IR-06 OBSERVATION: P1.8.95 resolves documentary contract alignment only; runtime declarations NOT VERIFIED.
- IR-07 OBSERVATION: no destructive authority escalation found.
- Read-back checks: 45 traceability rows, 47 baseline vectors, 22 unique supplemental vectors, 69 unique total IDs; exact state alias, availability revision pinning and contract §20 verified.
- Tests/CI NOT RUN; workflow run/artifact NONE; runtime evidence NOT VERIFIED. No source/runtime/VPS/database/storage mutation or inventory.
- Next: P1.8.97 close transition authority; P1.8.98 correct negative-case semantic coverage; then focused independent review. Do not begin V07/V08/Restore/TSA before focused review and owner blockers are addressed.

### P1.8.97 — Blocked, Reconciliation and Terminal Transition Authority Closure (2026-11-09)

- Document: `docs/evidence/p1-8/P1.8.97-blocked-reconciliation-terminal-transition-authority.md`.
- Commit: `e437e61743145616be49efc84e5347acc00d0971`.
- Blob SHA: `45c35ae20c68f21a00584179fa8e98f53ec56f1c`.
- Closes P1.8.96 IR-01 at documentary design level: explicit authority/event/guard rows for BLOCKED quarantine and resolution, reconciliation resume, expiry, revocation and observer-only reporting.
- Defines per-object reconciliation partition and requires lifecycle-review acceptance plus separate execution-authority final recheck; old authorization is never revived. Ambiguous objects block resume.
- No new role, self-approval, numeric TTL/freshness/time bound, identity/time provider, registry, event store or implementation selected. Owner decisions remain OPEN.
- Tests/CI NOT RUN; workflow run/artifact NONE; runtime evidence NOT VERIFIED. No source/runtime/VPS/database/storage change or inventory; no destructive operation.

### P1.8.98 — Negative-Case Semantic Coverage Corrections (2026-11-09)

- Record: `docs/evidence/p1-8/P1.8.98-negative-case-semantic-coverage-corrections.md`.
- Commit: `cbbf038fd76d68460cad471ebada772d135575f9`.
- Blob SHA: `c50619f54cc04effcda8221259e9cc22086d20a8`.
- Closes P1.8.96 IR-02/IR-03/IR-04 at test-specification level. P1.8.94 updated with direct vectors for missing/ambiguous recovery-chain member (NEG-REC-03), unresolved ledger-specific obligation (NEG-T3-02), missing/dangling evidence reference (NEG-EVD-06), unresolved evidence provenance/source/scope (NEG-EVD-07), and unexplained residual reference/index/sidecar (NEG-ADP-10).
- Corrected N09/N19/N24/N36 mappings. Static read-back: 45 traceability rows, 27 unique supplemental vectors, 74 total specified IDs (47 baseline + 27 supplemental).
- All vectors remain NOT_RUN. No runner, fixture, adapter, workflow, CI job, runtime inventory or destructive operation.
- Tests/CI NOT RUN; workflow run/artifact NONE; runtime evidence NOT VERIFIED.

### P1.8.99 — Independent Review of P1.8.97–P1.8.98 (2026-11-09)

- Review: `docs/evidence/p1-8/P1.8.99-independent-review-of-p1-8-97-to-98.md`.
- Commit: `be025bcfffbd64f9921e1b871285078c3f61332d`.
- Blob SHA: `dac951b5a45b2ba466e387ca682228e893f38485`.
- Verdict: **PARTIAL — P1.8.98 closes IR-02/IR-03/IR-04 at specification level; P1.8.97 retains three MAJOR findings IR2-01/IR2-02/IR2-03.**
- IR2-01 MAJOR: generic Any non-terminal → BLOCKED can bypass reconciliation from EXECUTING/VERIFICATION_PENDING; restrict BLOCKED to pre-mutation and keep observer report-only.
- IR2-02 MAJOR: CANCELLED_WITH_PARTIAL_OUTCOME must not terminalize while any object remains ambiguous; unresolved objects require RECONCILIATION_REQUIRED/NOT_VERIFIED.
- IR2-03 MAJOR: BLOCKED → FINAL_RECHECK requires positive complete proof that no object intent or side effect began.
- IR-02/03/04 resolved at specification level: direct vectors NEG-REC-03, NEG-T3-02, NEG-EVD-06, NEG-EVD-07, NEG-ADP-10.
- Static checks: 45 traceability rows, 47 baseline vectors, 27 unique supplemental vectors, 74 unique total IDs. All vectors NOT_RUN.
- Tests/CI NOT RUN; workflow run/artifact NONE; runtime evidence NOT VERIFIED. No source/runtime/VPS/database/storage/ledger mutation or inventory.
- Next: P1.8.100–P1.8.102 correct three transition-safety findings, then focused independent review. Do not start V07/V08/Restore/TSA or any destructive/runtime work.


## P1.8.100–P1.8.103 — Transition-safety remediation and focused review (2026-11-09)

- Approved scope: P1.8.100–P1.8.102 documentary remediation plus focused independent review. No implementation, test execution, runtime, storage or destructive authority was included.
- P1.8.100 — BLOCKED Transition Restriction and Observer-Only Quarantine:
  - Document: `docs/evidence/p1-8/P1.8.100-blocked-transition-and-observer-quarantine.md`.
  - Commit: `4a7459ec108db81ac6e9940c52200de435404685`.
  - Blob SHA: `8193d24dbba321a7091732847d3f83e03cfe15ef`.
  - Restricts BLOCKED to positively established pre-mutation states; in-flight/uncertain mutations route to RECONCILIATION_REQUIRED. Observer report and protective quarantine are separate from canonical state authority.
- P1.8.101 — Partial-Cancellation Terminality:
  - Document: `docs/evidence/p1-8/P1.8.101-partial-cancellation-terminality.md`.
  - Commit: `c6057fe4bffe060b14684dbfb90526910e0fc697`.
  - Blob SHA: `f115bc49541ad1c70f113ce11b86f1072ab241f0`.
  - Requires determinate, independently supported disposition for every manifest object; any ambiguous, unknown, NOT_VERIFIED or in-flight object prohibits terminalization.
- P1.8.102 — Positive No-Mutation Proof:
  - Document: `docs/evidence/p1-8/P1.8.102-positive-no-mutation-proof.md`.
  - Commit: `c52743d26c4d3eef064972929b609a2a9325899c`.
  - Blob SHA: `6b5c1a5b8253c37a7f0096c9c6deb885e1cf25a6`.
  - Requires complete, positive, revision-bound proof over the immutable manifest, mutation-intent boundary, backend submissions, independent object oracle, workers/queues, authorization and audit continuity before BLOCKED → FINAL_RECHECK.
- P1.8.94 updated with 13 additional negative vectors:
  - First update commit: `dde587cfe7ff91ab91df02bfbd4de92b9b715edf`; intermediate blob: `6952180425c7e1499427d88b926c3e9988ed4b05`.
  - Denominator correction commit: `5b41bf548d8a30cbbd3123593784f0e8df584877`; final blob: `4588379d8e101ee496bcf8927186c6c989e6c6a6`.
  - Final catalogue: 47 baseline + 40 unique supplemental = 87 unique specified vectors. 45 original N01–N45 rows remain. All 87 vectors are NOT_RUN.
- P1.8.103 — Focused Independent Review:
  - Review: `docs/evidence/p1-8/P1.8.103-independent-review-of-p1-8-100-to-102.md`.
  - Commit: `e7fadc6582ae2e660a815870f36570c81ab53514`.
  - Blob SHA: `50579909b0312368ee6692fab7deb1f94c8891bc`.
  - Verdict: PASS at documentary specification level; P1.8.99 IR2-01/IR2-02/IR2-03 closed. Overall implementation/readiness remains NOT VERIFIED.
  - Residual gates remain OPEN: independent approver/compensating-control model; trusted identity/time/freshness; atomic registry/storage fencing implementation; independent oracle; complete worker/queue discovery; inventory completeness; executable synthetic runner and separate test/staging authorization.
- Tests/CI NOT RUN; workflow run/artifact NONE; runtime evidence NOT VERIFIED. No source/schema/API/registry/adapter/scheduler/service/database/VPS/Feeder/storage/ledger/runtime mutation or inventory. No staging, synthetic execution, fault injection, archive, cleanup, restore, key operation or deletion.
- No deletion authority is granted. T0 canonical data and CORE_LEDGER/AI_LEDGER protections remain unchanged.
- Next gate: assess cross-contract conflicts between the completed self-deletion design and V07/V08/Restore/TSA as a separate documentary review only; do not implement or execute without separate explicit approval.


## P1.8.104 — Cross-Contract Conflict Review: Self-Deletion vs V07 / V08 / Restore / TSA (2026-11-09)

- Review: `docs/evidence/p1-8/P1.8.104-cross-contract-conflict-review.md`.- Review commit: `671dc975d3cba4f95cc2ac961bc7f46ef2e437dc`.
- Review blob SHA: `8cce46c9c32c369372453df6908f6e3b1a09a30a`.- Source branch/base commit reviewed: `feature/t0-centralized-data-feeder-p1-20261101` / `936abd84396152b71825c86241d705595d45ab24`.
- Verdict: **PARTIAL — no direct policy contradiction found; cross-contract integration gaps remain.**- V07: PARTIAL; trusted-time authority/profile, freshness, propagation, revocation and boundary parameters remain OPEN/BLOCKED.
- V08: PARTIAL; deletion eligibility does not yet explicitly bind source-progress/watermark/seal/commit and correction-lineage closure evidence.
- Restore: BLOCKED; explicit restore governance epoch, stale authorization invalidation, operation-history reconciliation and independent object-generation oracle remain incomplete.
- TSA: PARTIAL; timestamp proof is narrowly scoped to exact signed-object existence no later than genTime; token/trust/revocation evidence lifecycle needs explicit copy/restore linkage.
- Findings: CCX-01 MAJOR restore governance epoch; CCX-02 MAJOR V08 closure evidence; CCX-03 MAJOR trusted-time cross-domain binding; CCX-04 MODERATE TSA evidence lifecycle; CCX-05 MAJOR restore operation history/object oracle.
- Recommended next documentary work items P1.8.105–P1.8.108 are proposals only and are NOT authorized by P1.8.104.
- Tests NOT RUN; GitHub Actions NOT DISPATCHED; workflow run/artifact NONE; runtime evidence NOT VERIFIED; inventory NOT PERFORMED.
- No source/runtime/schema/API/registry/adapter/scheduler/service/database/VPS/T0/T1/Feeder/ledger/strategy/risk changes; no staging, restore, fault injection, archive, cleanup, key operation or deletion.
- No deletion authority granted; T0 canonical data and CORE_LEDGER/AI_LEDGER protections unchanged.
- **Next gate:** obtain separate explicit approval before starting any P1.8.105–P1.8.108 work item. Implementation, staging and destructive actions remain separately gated.


## P1.8.105–P1.8.108 — Approved Cross-Contract Lifecycle Closure Contracts (2026-11-09)

Owner approval: explicit approval received for all four documentation-only work items in order. Approval does not authorize implementation, staging, restore, fault injection, provider selection, key/TSA operations, workflow dispatch, archive, cleanup, vacuum or deletion.

### P1.8.105 — Restore Governance Epoch and Post-Restore Reconciliation
- Document: `docs/evidence/p1-8/P1.8.105-restore-governance-epoch-post-restore-reconciliation-contract.md`.
- Commit: `c1f7ccf5661fd9dce8c6803d35c7cc994ddd41c4`.
- Blob SHA: `6a16805a066cdbc1d7c47c2eb33b8261e1e80f92`.
- Defines distinct restore run, restore epoch, governance epoch, snapshot identity and operation-history high-water mark.
- Requires quarantine by default, independent epoch issuance, invalidation of every pre-restore execution authorization, authoritative governance-event reconciliation, exact object-generation checks and operation-history/object-oracle agreement.
- Snapshot presence/absence cannot prove a prior mutation committed or did not commit. Ambiguous outcomes remain quarantined; no blind retry.
- Restore READY is scoped and requires complete governance, operation, copy-lineage, integrity and independent-review evidence.
- Epoch authority, event-history source, provider operation-history guarantees, object oracle, role model and all measurement parameters remain OPEN.
- Status: DOCUMENTARY CONTRACT DRAFT COMPLETE; STATIC REVIEW REQUIRED; RESTORE NOT EXECUTED / NOT AUTHORIZED.

### P1.8.106 — V08 Checkpoint-to-Lifecycle Closure
- Document: `docs/evidence/p1-8/P1.8.106-v08-checkpoint-to-lifecycle-closure-contract.md`.
- Commit: `0c4d06797738ef4657a359fd60aae370c7b5723b`.
- Blob SHA: `ecf1115f47817a217a03d7583a0710c72bda65e9`.
- Binds exact dataset/version lifecycle review to source/partition inventory, monotonic watermark, UTC half-open windows, allowed-lateness policy, durable commit proof, seal linearization, immutable checkpoint and append-only correction lineage.
- Missing partitions, unknown progress, uncertain clock boundaries, ambiguous commit/seal ordering or unresolved corrections block closure.
- Checkpoint closure is only one eligibility input; it does not release dependencies or authorize deletion. T0 source data and all copies remain independently governed.
- Watermark algorithm, lateness, precision, clock uncertainty, persistence/commit proof, correction schema and related values remain OPEN.
- Status: DOCUMENTARY CONTRACT DRAFT COMPLETE; STATIC REVIEW REQUIRED; V08 PARAMETERS OPEN/BLOCKED; NOT EXECUTED.

### P1.8.107 — Trusted-Time Cross-Domain Binding
- Document: `docs/evidence/p1-8/P1.8.107-trusted-time-cross-domain-binding-contract.md`.
- Commit: `602a3d146c4b0872970da3b6a1966972132e95e0`.
- Blob SHA: `b11c6af1bdf1c48489879c52057af3fe02b88d87`.
- Defines distinct semantics for signed_at, TSA genTime, received/observed time, revocation effective time, durable commit, seal, authorization and restore boundaries.
- Requires exact event/object binding, precision/uncertainty, source/profile and fail-closed handling when intervals overlap or evidence is stale/ambiguous.
- Binds V07, V08, lifecycle freshness/authorization, restore epoch and mutation fencing without transferring authority across domains.
- TSA/provider, trust anchors, revocation source, freshness, uncertainty, expiry and all numerical/operational parameters remain OPEN.
- Status: DOCUMENTARY CONTRACT DRAFT COMPLETE; STATIC SECURITY REVIEW REQUIRED; TRUST PROFILE/PARAMETERS OPEN; NOT EXECUTED.

### P1.8.108 — TSA Evidence Copy and Historical Verification Lifecycle
- Document: `docs/evidence/p1-8/P1.8.108-tsa-evidence-copy-historical-verification-lifecycle.md`.
- Commit: `afa3c47b3a45c39c462309bdacef61b4540dd2a0`.
- Blob SHA: `1cf8e33a5ce62d63a03e0ed2c15872649d84a705`.
- Defines separate identities and lifecycle obligations for signed bytes/imprint inputs, timestamp tokens, trust-policy/anchor history, certificate chain, revocation evidence, verifier profile, verification result, manifests and each copy.
- Requires historical verification to recompute the exact P1.8.36 imprint, validate applicable historical policy and preserve current-trust assessment separately.
- No token-only assurance, no evidence co-deletion, no cascade across source/replica/backup/export, and no use of timestamp validity as deletion authority.
- TSA/provider/profile, trust-anchor/revocation history, retention floors, copy topology, integrity oracle and all numerical/operational parameters remain OPEN.
- Status: DOCUMENTARY CONTRACT DRAFT COMPLETE; STATIC REVIEW REQUIRED; TRUST/RETENTION/COPY PARAMETERS OPEN; NOT EXECUTED.

### Combined status and next gate
- All four documents were read back from the approved existing branch; exact blob SHAs recorded above.
- Work was documentation-only. No code, schema, API, registry, adapter, scheduler, service, database, VPS, T0/T1, Feeder, ledger, strategy or risk-engine changes.
- Tests: NOT RUN. GitHub Actions: NOT DISPATCHED. Workflow run/artifact: NONE. Runtime evidence: NOT VERIFIED. Provider selection: NONE. Staging/restore/fault injection/key/TSA operations: NOT EXECUTED.
- No deletion authority granted. T0 canonical data and CORE_LEDGER/AI_LEDGER protections remain unchanged; `AI_EXECUTION_ENABLED=false`.
- Next gate: focused independent static cross-contract review of P1.8.105–P1.8.108 against P1.8.26, P1.8.34–P1.8.37, P1.8.93–P1.8.104 and governing lifecycle/copy contracts. This review is not an implementation or execution authorization.


## P1.8.109 — Independent Cross-Contract Review of P1.8.105–P1.8.108 (2026-11-09)

- Review: `docs/evidence/p1-8/P1.8.109-independent-cross-contract-review-p1-8-105-to-108.md`.
- Review commit: `da441ac706d19db8166404fa647f53416ee738c5`.
- Review blob SHA: `edf3b93b866ae2413a38982f295a36f068fad639`.
- Scope: static/documentary review against P1.8.26, P1.8.28, P1.8.34, P1.8.36, P1.8.93, P1.8.102, P1.8.103, P1.8.104 and governing deletion, consumer, lifecycle and copy contracts.
- Verdict: **PARTIAL — no direct policy contradiction found; five integration/authority findings remain.**
- IR109-01 MAJOR: Restore Epoch and Governance Epoch are separately named but their issuance, ordering, concurrency/fencing and atomic binding to operation-history high-water mark are not frozen.
- IR109-02 MODERATE: V08 requires deterministic commit/seal linearization but does not explicitly freeze same-representable-boundary/equality disposition or require an ordering token; equality/overlap must remain UNKNOWN/HOLD absent proof.
- IR109-03 MAJOR: P1.8.107 trusted-time evidence needs a normative, versioned field-by-field crosswalk into P1.8.93 protected decision vector and mutation-boundary recheck.
- IR109-04 MODERATE: TSA evidence objects need explicit parent/child dependency, consumer/audit/recovery hold and per-copy disposition crosswalk.
- IR109-05 MAJOR: Restore readiness, V07 quarantine resolution, TSA verification, lifecycle eligibility, approval, execution authorization and storage execution roles remain OPEN; READY/quarantine release must not imply deletion approval.
- PASS at documentary level: T0 canonical independence, CORE_LEDGER/AI_LEDGER separation, no default TTL, no automatic release, ACK/release separation, no cascade, fail-closed behavior and paper-only boundary.
- Recommended follow-up documents P1.8.110–P1.8.114 are proposals only and are NOT authorized by P1.8.109 approval.
- Tests: NOT RUN. GitHub Actions: NOT DISPATCHED. Workflow run/artifact: NONE. Runtime/provider evidence: NOT VERIFIED. Runtime inventory: NOT PERFORMED.
- No implementation, source/runtime/schema/API/registry/adapter/scheduler/service/database/VPS/T0/T1/Feeder/ledger/strategy/risk-engine changes. No staging, restore, fault injection, provider selection, key/TSA operation, archive, cleanup, vacuum or deletion.
- Deletion authority: NOT GRANTED. T0 and CORE_LEDGER/AI_LEDGER protections unchanged; `AI_EXECUTION_ENABLED=false`.
- Next gate: owner review of the five findings and separate approval for any P1.8.110–P1.8.114 documentation work. No runtime or destructive action is authorized.


## P1.8.110–P1.8.114 — Approved Documentary Closure of P1.8.109 Findings (2026-11-09)

Owner approval: explicit automatic approval received for all five documentary work items, in order. This authorizes documentation only; it does not authorize implementation, tests, workflow dispatch, staging, restore, provider/key/TSA operations, fault injection, IAM changes, archive, cleanup, vacuum or deletion.

### P1.8.110 — Restore Epoch / High-Water-Mark Atomic Binding Clarification
- Document: `docs/evidence/p1-8/P1.8.110-restore-epoch-high-water-mark-atomic-binding-clarification.md`.
- Commit: `35b5e3311488483b450765141fefef5ef78fab6e`.
- Blob SHA: `70e7f311b27679d5642ca99f2b7e6db8adda1cfa`.
- Closes IR109-01 at documentary-design level: Restore Run ID, Restore Epoch, Governance Epoch, snapshot consistency point, operation-history HWM and governance revision vector are separate identities.
- Requires an immutable binding record tying the epochs, exact snapshot, contiguous authenticated HWM and governance revision vector to one reconciliation cut; concurrent restore attempts must be fenced/serialized; ambiguous or mismatched binding remains QUARANTINED.
- Epoch issuer, rollback/uniqueness proof, HWM source/completeness, atomic coupling mechanism, identity and numeric parameters remain OPEN. Restore NOT EXECUTED / NOT AUTHORIZED.

### P1.8.111 — V08 Commit/Seal Equality and Total-Order Contract Clarification
- Document: `docs/evidence/p1-8/P1.8.111-v08-commit-seal-equality-total-order-contract-clarification.md`.
- Commit: `af2a00684e55e79405f7f1ca2cff78bdf5783ce6`.
- Blob SHA: `50efc83fece41e6da62db299c765985203c16271`.
- Closes IR109-02 at documentary-design level: exact before/after requires a proven common ordering domain/token; equal timestamps, equal sequence without tie semantics, overlapping uncertainty, missing tokens or incomparable domains are UNKNOWN/HOLD.
- Preserves UTC half-open windows, watermark `>= window_end`, immutable sealed checkpoints and append-only corrections.
- Commit/seal token, DB/provider durable boundary, clock, precision, lateness and correction parameters remain OPEN. V08 execution BLOCKED.

### P1.8.112 — Trusted-Time to Mutation Decision-Vector Crosswalk
- Document: `docs/evidence/p1-8/P1.8.112-trusted-time-mutation-decision-vector-crosswalk.md`.
- Commit: `78e003a264626416ce6101f89fe69d2d863c8c14`.
- Blob SHA: `fbe32e84308184abcd855428c0ce5ea537ae63a4`.
- Closes IR109-03 at documentary-design level: maps exact evidence identity/version, subject/event binding, time semantic, source/profile, precision/uncertainty, historical trust/revocation state, freshness, authorization, restore binding and final-check identity into P1.8.93 protected vector.
- Any material evidence/revision change invalidates the vector; final recheck must be atomic/transactionally coupled to mutation. Without proof, adapter remains INELIGIBLE.
- TSA/profile, trust/revocation authorities, freshness/uncertainty values, authorization lifetime, registry and atomic fence remain OPEN; no adapter qualified.

### P1.8.113 — TSA Evidence Dependency / Copy / Hold Graph Crosswalk
- Document: `docs/evidence/p1-8/P1.8.113-tsa-evidence-dependency-copy-hold-graph-crosswalk.md`.
- Commit: `f447f242102f5029195ef25a817267753464d27a`.
- Blob SHA: `a5c49170d33c56cf21d218879091c1d1429bca98`.
- Closes IR109-04 at documentary-design level: defines immutable evidence/copy node identity and typed CLAIM_REQUIRES, REPRODUCES, VALIDATED_UNDER, DERIVED_FROM, COPY_OF, RESTORE_DEPENDS_ON, AUDIT_REQUIRES, CONSUMER_DEPENDS_ON, HOLD_APPLIES_TO and SUPERSEDES edges.
- Each copy has independent lifecycle state; incomplete graph, unknown edge or uncertain hold applicability remains protective. No cascade or automatic release.
- Runtime inventory, registry, graph completeness, copy topology, hold authority, trust/revocation, retention and integrity oracle remain OPEN/NOT VERIFIED.

### P1.8.114 — Lifecycle / Restore / Quarantine Authority Separation Decision Record
- Document: `docs/evidence/p1-8/P1.8.114-lifecycle-restore-quarantine-authority-separation-decision-record.md`.
- Commit: `f815aae06697ce0ad790db7c9b69ad0ca45ebf9f`.
- Blob SHA: `067038d870b30b18934c4f6fe1b6d25ccd529ac5`.
- Closes IR109-05 at documentary non-escalation level: separates restore readiness, V07 quarantine resolution, TSA/V08 verification, lifecycle assessment, independent approval, execution authorization, storage execution and independent verification.
- Explicitly records that READY, quarantine resolution and evidence PASS do not imply lifecycle eligibility, approval or deletion authority.
- The owner has NOT yet selected named principals, independent-approver or single-owner compensating-control model, delegation, emergency access or IAM assignments. Those decisions remain OPEN; default is no self-approval and no combining incompatible authority domains.
- Deletion authority remains NOT GRANTED.

### Combined result and evidence status
- P1.8.110–P1.8.114 documents were fetched back from the existing branch after creation; all five exact blob SHAs and document headings were verified.
- Work is documentation-only. No source/runtime/schema/API/registry/adapter/scheduler/service/database/VPS/T0/T1/Feeder/ledger/strategy/risk-engine or IAM changes.
- Static authoring/read-back check: PASS. Independent review of the five new documents: NOT YET PERFORMED.
- Tests: NOT RUN. GitHub Actions: NOT DISPATCHED. Workflow run/artifact: NONE. Runtime/provider evidence: NOT VERIFIED. Runtime inventory: NOT PERFORMED.
- Restore/staging/fault injection/provider/key/TSA operation: NOT EXECUTED / NOT AUTHORIZED.
- Archive/cleanup/vacuum/deletion: NOT EXECUTED / NOT AUTHORIZED. Deletion authority: NOT GRANTED.
- T0 canonical independence and CORE_LEDGER/AI_LEDGER separation unchanged; `AI_EXECUTION_ENABLED=false`.
- Next gate: focused independent static review of P1.8.110–P1.8.114 against P1.8.93, P1.8.103–P1.8.109 and governing lifecycle/consumer/copy contracts. Any implementation, tests, workflow dispatch, IAM, staging or operational work requires its own explicit authorization.


## P1.8.115 — Independent Static Review of P1.8.110–P1.8.114 (2026-11-09)

Owner approval: explicit approval received for P1.8.115. Scope was limited to static/documentary cross-contract review. No implementation, tests, workflow dispatch, IAM, staging, restore, provider/key/TSA operation or destructive action was authorized.

- Review: `docs/evidence/p1-8/P1.8.115-independent-static-review-p1-8-110-to-114.md`.
- Review commit: `9ce5fd1c8ad690767ee9a2b80637a6ebb5a4f4de`.
- Review blob SHA: `cc78bc8c7d13eb7c82024dd9666a5b9689178e03`.
- Exact reviewed document SHAs are pinned in §2 of the review.
- Verdict: **PARTIAL — no direct policy contradiction found; four residual closure findings remain (2 MAJOR, 2 MODERATE).**
- IR115-01 MAJOR: P1.8.110 restore governance revision vector does not explicitly cover every applicable P1.8.93 protected-vector revision/reference, notably consumer availability declarations/owner attestations and copy/backup/recovery disposition revision.
- IR115-02 MODERATE: P1.8.112 does not explicitly require freshness age/uncertainty to be recomputed using a trusted current-time observation at the actual mutation linearization point.
- IR115-03 MODERATE: P1.8.113 defines typed graph edges but does not normatively define per-type edge orientation/canonical traversal; graph closure and source-hold mapping to descendants need deterministic semantics.
- IR115-04 MAJOR: P1.8.114 records safe non-escalation boundaries but leaves the owner role-model decision open. Independent approver availability, single-owner compensating-control acceptability, named role ownership/delegation and effective permission separation remain undecided. IR109-05 is therefore PARTIAL/OPEN, not closed.
- P1.8.111: PASS at documentary-design level. Equality/overlap without a proven common ordering token/domain remains UNKNOWN/HOLD; V08 execution remains blocked.
- Positive invariants preserved: T0 canonical independence; CORE_LEDGER/AI_LEDGER separation; no default TTL; no automatic consumer release; no cascade; fail-closed; paper-only boundary.
- Tests: NOT RUN. GitHub Actions: NOT DISPATCHED. Workflow run/artifact: NONE. Runtime/provider semantics: NOT VERIFIED. Runtime graph/copy inventory: NOT PERFORMED.
- Restore/staging/fault injection/provider/key/TSA operations: NOT EXECUTED / NOT AUTHORIZED.
- Archive/cleanup/vacuum/deletion: NOT EXECUTED / NOT AUTHORIZED. Deletion authority: NOT GRANTED.
- T0 and CORE_LEDGER/AI_LEDGER protections unchanged; `AI_EXECUTION_ENABLED=false`.
- Recommended next documentary decisions: P1.8.116 Restore Governance Vector Completeness Crosswalk; P1.8.117 Trusted-Time Freshness at Mutation Linearization; P1.8.118 TSA Graph Orientation/Closure/Hold Propagation; P1.8.119 Owner Role-Model Decision Record. These are proposals only and require separate explicit approval.


## P1.8.116–P1.8.119 — Approved Documentary Closure Work (2026-11-09)

Owner approval: explicit approval received for all four proposed documentary work items. Scope is documentation/decision-record preparation only. The approval does not authorize implementation, tests, GitHub Actions dispatch, IAM, restore, staging, provider/key/TSA operations, fault injection, archive, cleanup, vacuum or deletion.

### P1.8.116 — Restore Governance Vector Completeness Crosswalk
- Document: `docs/evidence/p1-8/P1.8.116-restore-governance-vector-completeness-crosswalk.md`.
- Commit: `616e9b123e73290c443b748997887e7aa7580118`.
- Blob SHA: `161e76b643c65ec768c7ccecd81a5cf9fb771af2`.
- Explicitly crosswalks all P1.8.93 protected-vector domains, including per-consumer availability declaration/owner-attestation references and per-copy backup/recovery disposition revisions.
- Requires schema-versioned completeness proof and one consistent restore reconciliation cut; digest alone does not prove completeness.
- Missing/non-coincident revisions, HWM gaps or unverifiable parent-child revision coverage keep restore QUARANTINED.
- Registry/HWM authority, consistency mechanism, identity/time sources and parameters remain OPEN.

### P1.8.117 — Trusted-Time Freshness at Mutation Linearization
- Document: `docs/evidence/p1-8/P1.8.117-trusted-time-freshness-at-mutation-linearization.md`.
- Commit: `254ef9bfb1a8aeb19f57c087bba022525b9045fa`.
- Blob SHA: `873a0bd4726ab7870a9691bb5681f57c8871632a`.
- Separates preflight freshness from final mutation-boundary evaluation.
- Requires trusted current-time observation bound to exact object, generation, mutation intent and protected decision vector; recomputes age/uncertainty at the final fence.
- Requires atomic/transactionally coupled or provably ordered observation; uncertainty overlap, stale revocation or unavailable trust source means HOLD/adapter INELIGIBLE.
- Time/TSA/revocation providers, policy values, uncertainty model and adapter proof remain OPEN.

### P1.8.118 — TSA Graph Orientation, Closure and Hold-Propagation Semantics
- Document: `docs/evidence/p1-8/P1.8.118-tsa-graph-orientation-closure-hold-propagation.md`.
- Commit: `b4114bbeb108126c171cf1c4a57e94174bc1be46`.
- Blob SHA: `3b8f314b6690231cbeed8057fb2c28f3a851e5a8`.
- Defines canonical dependent/derived/copy-to-prerequisite/source edge orientation for every P1.8.113 edge type.
- Defines deterministic prerequisite, descendant, hold, consumer and audit/restore traversal; source holds conservatively cover known copies/representations/derived descendants.
- Absence claims require authenticated registry/HWM, full inventory/pagination/partition coverage, queue/delegation reconciliation and independent completeness proof.
- Runtime graph inventory, source coverage, graph registry and completeness oracle remain OPEN/NOT VERIFIED.

### P1.8.119 — Owner Role-Model Decision Record
- Document: `docs/evidence/p1-8/P1.8.119-owner-role-model-decision-record.md`.
- Commit: `f8e215604f4ba707840999f96ba816fc04dab5d5`.
- Blob SHA: `f9b516605d026e9e514d9d2239f293a7bf15dbd9`.
- Presents three explicit owner choices: A independent multi-principal separation; B single-owner with separately proven compensating controls; C no destructive authority until independent coverage exists.
- **No option was selected by this work.** Approval to create the decision record is not a role-model selection.
- Default remains no self-approval, no incompatible authority combination, no IAM/access changes and no destructive capability.
- Named principals, delegation, emergency access, effective-permission analysis and owner selection remain OPEN. IR115-04 is therefore DECISION READY / OWNER DECISION OPEN, not closed.

### Combined result and evidence status
- All four documents were fetched back from GitHub; exact headings, blob SHAs and fail-closed/authority boundaries were verified.
- Static authoring/read-back: PASS.
- Independent review of P1.8.116–P1.8.119: NOT YET PERFORMED.
- Tests: NOT RUN. GitHub Actions: NOT DISPATCHED. Workflow run/artifact: NONE.
- Runtime/provider/graph/consumer/copy inventory: NOT VERIFIED / NOT PERFORMED.
- Restore/staging/fault injection/provider/key/TSA operations: NOT EXECUTED / NOT AUTHORIZED.
- IAM/role assignment/access grant/workflow activation: NOT EXECUTED / NOT AUTHORIZED.
- Archive/cleanup/vacuum/deletion: NOT EXECUTED / NOT AUTHORIZED. Deletion authority: NOT GRANTED.
- T0 canonical independence and CORE_LEDGER/AI_LEDGER separation unchanged; `AI_EXECUTION_ENABLED=false`.
- Next gate: independent static cross-contract review of P1.8.116–P1.8.119, including validation of the protected-vector completeness crosswalk, final-boundary trusted-time semantics, graph edge/traversal definitions and the non-selected owner role options. Any tests, implementation, IAM, staging or operational work requires separate explicit authorization.

## P1.8.120 — Independent Static Review of P1.8.116–P1.8.119 (2026-11-09)

Owner approval: explicit approval received for P1.8.120. Scope was limited to static/documentary cross-contract review. No implementation, tests, GitHub Actions dispatch, IAM, restore, staging, provider/key/TSA operation, fault injection or destructive action was authorized.

- Review: `docs/evidence/p1-8/P1.8.120-independent-static-review-p1-8-116-to-119.md`.
- Review commit: `a07bddab30492b8672a9e5da2be99b208f305664`.
- Review blob SHA: `dcd7e8e2bcc10d4e980b0d4e9482a374ff9cad2e`.
- Exact reviewed source blob SHAs are pinned in §2 of P1.8.120.
- Verdict: **PARTIAL — P1.8.116–P1.8.118 PASS at documentary-design level; P1.8.119 correctly leaves the owner decision open; Option B is not selection-ready.**
- IR115-01: CLOSED at documentary-design level. P1.8.116 explicitly crosswalks all applicable P1.8.93 protected-vector fields, including per-consumer declarations/attestations and per-copy backup/recovery disposition revisions; implementation/source completeness NOT VERIFIED.
- IR115-02: CLOSED at documentary-design level. P1.8.117 requires trusted current-time observation and age/uncertainty recomputation at the final mutation boundary, bound to exact intent/object/vector/fence; provider/adapter atomicity proof remains OPEN.
- IR115-03: CLOSED at documentary-design level. P1.8.118 defines directed edge semantics, deterministic traversal, conservative hold propagation and graph completeness requirements; runtime inventory/completeness NOT VERIFIED.
- IR115-04: OWNER DECISION OPEN. P1.8.119 is a decision framework, not an owner selection. No A/B/C option is selected.
- IR120-01 MAJOR: Option B lacks a mandatory, technically enforced independent pre-commit veto/control. “Where appropriate” review/delay and retrospective verification cannot establish prevention of unilateral destructive action. Option B is NOT SELECTION-READY; it requires a separately reviewed control definition. If unavailable, Option B must not be selected.
- Current authority remains unchanged: no self-approval, no incompatible role combination, no IAM/access change, no destructive capability and no deletion authority.
- Tests: NOT RUN. GitHub Actions: NOT DISPATCHED. Workflow run/artifact: NONE.
- Runtime/provider/IAM/graph/consumer/copy inventory: NOT VERIFIED / NOT PERFORMED.
- Restore/staging/fault injection/provider/key/TSA operations: NOT EXECUTED / NOT AUTHORIZED.
- Archive/cleanup/vacuum/deletion: NOT EXECUTED / NOT AUTHORIZED. Deletion authority: NOT GRANTED.
- T0 canonical independence and CORE_LEDGER/AI_LEDGER separation unchanged; `AI_EXECUTION_ENABLED=false`.
- Next gate: owner decision on role-model direction remains OPEN. Option A or C can be considered as owner decisions; Option B first requires a separate mandatory pre-commit independent-control specification and review. Any IAM, implementation, test, workflow or operational work requires separate explicit authorization.


## P1.8.121 — Owner Decision Ratification: Option C No Destructive Authority (2026-11-09)

Owner decision: explicit approval received to select **Option C — No Destructive Authority** as the system's default authorization model.

- Decision record: `docs/evidence/p1-8/P1.8.121-owner-decision-ratification-option-c-no-destructive-authority.md`.
- Decision document commit: `d06b50db98025c8c6b31c5e921924d20cb43ea38`.
- Decision document blob SHA: `b92c63f593af0088fc522a55dc841af0ad1e5ac7`.
- Option C is now the approved default: no worker, adapter, service, operator or individual receives destructive authority until independently controlled coverage is demonstrated and separately approved.
- Read-only inspection, inventory/manifest reconciliation, non-mutating integrity checks and lifecycle eligibility assessment remain permissible only within existing access boundaries.
- Delete, overwrite, truncate, purge, archive, destructive cleanup/vacuum and any equivalent mutation remain prohibited. No authority may arise from timeout, ACK, restore readiness, quarantine resolution, evidence PASS, repository write access or alternate credentials.
- Option A is a possible future transition target, not selected. Any C-to-A proposal requires genuinely independent principals, separation of requester/approver/executor/verifier, exact-object authorization, bypass-resistant revocation/delegation/emergency controls, independent review and separate owner approval.
- Option B remains unselected and not selection-ready while P1.8.120 IR120-01 remains unresolved. Selecting C does not close that finding for Option B.
- P1.8.121 status: OWNER DECISION APPROVED; DOCUMENTARY RATIFICATION RECORDED; independent static review PENDING.
- Static authoring/read-back: PASS — exact document fetched back from the branch; decision and authority boundary verified. Tests: NOT RUN. GitHub Actions: NOT DISPATCHED. Workflow run/artifact: NONE.
- IAM/role assignment/access grant/credential/workflow activation: NOT EXECUTED / NOT AUTHORIZED. Runtime/provider/storage/registry/consumer/copy inventory: NOT VERIFIED / NOT PERFORMED.
- Restore/staging/fault injection/provider/key/TSA operations: NOT EXECUTED / NOT AUTHORIZED. Archive/cleanup/vacuum/deletion: NOT EXECUTED / NOT AUTHORIZED. Destructive/deletion authority: NOT GRANTED.
- T0 remains an independent canonical data asset; CORE_LEDGER and AI_LEDGER remain separate; `AI_EXECUTION_ENABLED=false`.
- Next gate: independent static review of P1.8.121. No tests, workflow dispatch, IAM, implementation, staging or destructive operation is authorized by this decision.


## P1.8.122 — Independent Static Review of P1.8.121 Option C Owner Decision (2026-11-09)

Owner approval: explicit approval received for independent static review of P1.8.121. Scope remained documentary only.

- Review: `docs/evidence/p1-8/P1.8.122-independent-static-review-p1-8-121-option-c.md`.
- Review commit: `edf4a0a3bc33378c0b39adeefbe322e9d1ee7e3b`.
- Review blob SHA: `69cc991264317c3763aedab03a92d977f7758ed1`.
- Exact reviewed P1.8.121 blob SHA: `b92c63f593af0088fc522a55dc841af0ad1e5ac7`.
- Governing cross-checks: P1.8.114 blob `067038d870b30b18934c4f6fe1b6d25ccd529ac5`; P1.8.120 blob `dcd7e8e2bcc10d4e980b0d4e9482a374ff9cad2e`.
- Verdict: **PARTIAL — Option C is internally consistent and safe at documentary level; effective-permission enforcement remains NOT VERIFIED.**
- P1.8.121 owner selection, no-authority boundary, read-only/assessment separation, fail-closed semantics and future C-to-A conditions: PASS at documentary level.
- P1.8.120 IR120-01 remains OPEN for Option B; selecting C does not close that finding for B.
- IR122-01 MODERATE: before any operational enforcement claim, explicitly enumerate GitHub Actions GITHUB_TOKEN/reusable workflow permissions, repository/organization/environment secrets and variables, OIDC trust, GitHub Apps, deploy keys, PATs, self-hosted runner identities and external provider permissions. This is an inventory requirement, not a claim that any credential currently has destructive access.
- Static review/readback: PASS — P1.8.122 fetched back from the branch; source blob SHA pinned above.
- Tests: NOT RUN. GitHub Actions: NOT DISPATCHED. Workflow run/artifact: NONE.
- IAM/role assignment/access grant/credential creation or activation: NOT EXECUTED / NOT AUTHORIZED.
- Effective GitHub Actions/repository/organization/environment/OIDC/runner/App/PAT/deploy-key/provider permissions: NOT VERIFIED.
- Runtime/provider/storage/registry/consumer/copy inventory: NOT VERIFIED / NOT PERFORMED.
- Restore/staging/fault injection/provider/key/TSA operations: NOT EXECUTED / NOT AUTHORIZED.
- Archive/cleanup/vacuum/deletion: NOT EXECUTED / NOT AUTHORIZED. Destructive/deletion authority: NOT GRANTED.
- T0 remains an independent canonical data asset; CORE_LEDGER and AI_LEDGER remain separate; `AI_EXECUTION_ENABLED=false`.
- Next gate: decide whether to approve a documentary control-plane identity inventory contract addressing IR122-01. No permission inspection beyond read-only metadata, IAM change, secret disclosure, workflow dispatch, implementation, staging or destructive operation is authorized by this review.


## P1.8.123 — GitHub Control-Plane Identity and Effective-Permission Inventory Contract (2026-11-09)

Owner approval: explicit approval received for **P1.8.123 documentary-only contract**. Work was limited to drafting and recording the inventory/evidence specification on the existing branch.

- Contract: `docs/evidence/p1-8/P1.8.123-github-control-plane-identity-effective-permission-inventory-contract.md`.
- Contract commit: `fc08497ff0d9f101ca19b4ede2e050023507b21e`.
- Contract blob SHA: `d2c2a4a22b63b2214448b4405b44dc69de29b864`.
- Contract defines future bounded inventory coverage for GitHub Actions workflow/job permissions and reusable workflows; triggers and protection gates; secrets/variables metadata only; GitHub Apps, PATs, deploy keys, bot/human principals; runner identities; OIDC federation; external provider identities and resource policies.
- Defines operation-level capability classes, direct/inherited/delegated/effective-permission graph, credential-minting and control-plane-to-data-plane paths, required inventory fields, completeness rules and UNKNOWN/NOT VERIFIED handling.
- Explicitly prohibits retrieving or exposing secret values, running jobs or host inspection, contacting provider endpoints, changing IAM/permissions/credentials/workflows, remediation, and destructive tests.
- Option C remains the approved default. No destructive authority is granted. Effective permissions remain NOT VERIFIED.
- Static authoring/read-back: PASS — exact document fetched back from the approved branch; title, Option C boundary, secret-value prohibition and core inventory coverage inspected.
- Tests: NOT RUN. GitHub Actions: NOT DISPATCHED. Workflow run/artifact: NONE.
- IAM/role assignment/access grant/permission change/credential creation-rotation-revocation/workflow activation: NOT EXECUTED / NOT AUTHORIZED.
- Live GitHub/org/environment/OIDC/runner/provider permission inventory: NOT PERFORMED / NOT VERIFIED.
- Runner jobs/host inspection/provider endpoint probes: NOT EXECUTED / NOT AUTHORIZED.
- Restore/staging/fault injection/provider/key/TSA operations: NOT EXECUTED / NOT AUTHORIZED.
- Archive/cleanup/vacuum/deletion: NOT EXECUTED / NOT AUTHORIZED. Destructive/deletion authority: NOT GRANTED.
- IR122-01 remains OPEN pending a separately approved read-only inventory execution and independent review. This contract does not close it or claim Option C is technically enforced.
- T0 remains an independent canonical data asset; CORE_LEDGER and AI_LEDGER remain separate; `AI_EXECUTION_ENABLED=false`.
- Next gate: independent static review of P1.8.123 contract. Any read-only metadata collection, permission inspection, remediation or enforcement verification requires its own explicit approval and bounded scope.


## P1.8.124 — Independent Static Review of P1.8.123 (2026-11-09)

- Owner approval: explicit approval received for P1.8.124 independent static/documentary review only.
- Review: `docs/evidence/p1-8/P1.8.124-independent-static-review-p1-8-123.md`.
- Review commit: `69ac77ad7761452e2cc998dd058b8761c709bb8c`.
- Reviewed P1.8.123 blob SHA: `d2c2a4a22b63b2214448b4405b44dc69de29b864`.
- Cross-contract sources: P1.8.122 blob `69cc991264317c3763aedab03a92d977f7758ed1`; P1.8.121 blob `b92c63f593af0088fc522a55dc841af0ad1e5ac7`; P1.8.114 blob `067038d870b30b18934c4f6fe1b6d25ccd529ac5`; P1.8.93 blob `4cc158b5f766fb024e411519be36076bc1e3758a`.
- Verdict: **PARTIAL**. P1.8.123's core identity inventory and fail-closed model are directionally sound and consistent with Option C, but three clarifications are required before using it as the basis for a read-only inventory proposal or an Option C technical-enforcement claim.
- IR124-01 MAJOR: multi-source inventory snapshot consistency, collection drift detection, final read-only revalidation and manifest-bound observation window are underspecified.
- IR124-02 MAJOR: opaque secret-derived credentials need explicit non-secret provenance requirements and mandatory UNKNOWN/NOT VERIFIED handling when effective scope cannot be established without revealing values.
- IR124-03 MODERATE: explicitly map GitHub organization/repository administration, Actions policy, ruleset/environment bypass, runner-group administration, privileged workflow approval/rerun, and artifact/cache supply-chain edges.
- P1.8.123 core scope retained; no direct contradiction with P1.8.121 Option C or P1.8.93 mutation-fencing boundary found.
- P1.8.122 IR122-01 remains OPEN: contract design is not live permission evidence. P1.8.120 IR120-01 remains OPEN for Option B; B remains unselected/not selection-ready.
- Static review: COMPLETE. Tests: NOT RUN. GitHub Actions: NOT DISPATCHED. Workflow run/artifact: NONE.
- Live GitHub/org/environment/OIDC/runner/provider permission inventory: NOT PERFORMED / NOT VERIFIED.
- Secret-value retrieval, IAM/role/permission change, credential creation/rotation/revocation, workflow activation/remediation, runner jobs/host inspection/provider probes: NOT EXECUTED / NOT AUTHORIZED.
- Restore/staging/fault injection/provider/key/TSA operations: NOT EXECUTED / NOT AUTHORIZED.
- Archive/cleanup/vacuum/deletion: NOT EXECUTED / NOT AUTHORIZED. Destructive/deletion authority: NOT GRANTED.
- Option C remains the approved default; T0 remains independent; CORE_LEDGER and AI_LEDGER remain separate; `AI_EXECUTION_ENABLED=false`.
- Next gate: prepare a documentation-only P1.8.125 clarification for IR124-01/02/03, then independently review it. Any live read-only metadata inventory still requires separate explicit owner approval and bounded scope.


## P1.8.125–P1.8.126 — Effective-Permission Inventory Clarification and Independent Review (2026-11-09)

- Owner instruction: automatic continuation approved within P1.8. This approval is bounded by existing P1.8 guardrails; it does not grant live inspection, permission changes, credential operations, workflow activation, provider access or destructive authority.
- P1.8.125 clarification: `docs/evidence/p1-8/P1.8.125-clarification-of-effective-permission-inventory-contract.md`.
  - Commit: `7c332935160140b256afcc70cbff96aac77eed50`.
  - Blob SHA: `d1c3ca152ce3bc4986574c524b0ac99442c576a2`.
  - Adds a bounded multi-source inventory cut, per-source observation/revision and pagination evidence, drift detection, high-impact final revalidation, manifest binding and invalidation on material change.
  - Preserves the absolute no-secret-value rule and defines non-secret provenance requirements; opaque/unbounded credential paths are UNKNOWN/NOT VERIFIED and can block an Option C technical-enforcement PASS.
  - Adds explicit GitHub organization/repository administration, Actions policy, workflow, ruleset/environment bypass, runner, artifact/cache/dependency and high-risk trigger graph edges.
  - Numeric freshness/clock/collection thresholds and source/provider guarantees remain OPEN; no global atomic snapshot is claimed.
- P1.8.126 independent static review: `docs/evidence/p1-8/P1.8.126-independent-static-review-p1-8-125.md`.
  - Review commit: `dde3516e89252e380774550e76cd6cca05e72f61`.
  - Review blob SHA: `d18d9d30329855af1dbcb81d0711346fc0aa2956`.
  - Reviewed P1.8.125 blob: `d1c3ca152ce3bc4986574c524b0ac99442c576a2`.
  - Verdict: PASS — IR124-01, IR124-02 and IR124-03 CLOSED at documentary-design level. No direct contradiction with P1.8.123 or P1.8.121 Option C found.
- IR122-01 remains OPEN pending separately authorized live read-only inventory and independent review. Option C technical enforcement remains NOT VERIFIED. P1.8.120 IR120-01 remains OPEN for Option B; B remains unselected/not selection-ready.
- Static author/readback and review readback: PASS. Tests: NOT RUN. GitHub Actions: NOT DISPATCHED. Workflow run/artifact: NONE.
- Live GitHub/org/environment/OIDC/runner/provider permission inventory: NOT PERFORMED / NOT VERIFIED. Secret values were not accessed.
- IAM/role/permission changes, credential creation/rotation/revocation, workflow activation/remediation, runner jobs/host inspection/provider probes: NOT EXECUTED / NOT AUTHORIZED.
- Restore/staging/fault injection/provider/key/TSA operations: NOT EXECUTED / NOT AUTHORIZED.
- Archive/cleanup/vacuum/deletion: NOT EXECUTED / NOT AUTHORIZED. Destructive/deletion authority: NOT GRANTED.
- Option C remains the approved default; T0 remains an independent canonical data asset; CORE_LEDGER and AI_LEDGER remain separate; `AI_EXECUTION_ENABLED=false`.
- Next bounded P1.8 documentary step: prepare a consolidated crosswalk/closure index mapping P1.8.121–P1.8.126, findings, owner decisions, evidence blobs, unresolved operational gates and the separate authorization needed for live inventory. Do not execute live inventory under automatic documentary approval.


## P1.8.127–P1.8.128 — Lifecycle Authority and Permission-Assurance Closure Index (2026-11-09)

- Owner instruction: automatic continuation within P1.8 remains limited to documentary work and independent static reviews under existing guardrails.
- P1.8.127 index: `docs/evidence/p1-8/P1.8.127-lifecycle-authority-and-github-permission-assurance-closure-index.md`.
  - Commit: `ad46716f709de05c761cde81c1ef9415e01f32ef`.
  - Blob SHA: `9e78a0d890f6b190e95746fd31a5fc1ebece33bb`.
  - Consolidates P1.8.121–P1.8.126 owner decision, review findings, commit/blob identities, documentary dispositions and live-inventory authorization gates.
  - Explicitly preserves Option C, distinguishes documentary closure from operational closure, and records IR122-01 as operationally OPEN.
- P1.8.128 independent static review: `docs/evidence/p1-8/P1.8.128-independent-static-review-p1-8-127.md`.
  - Review commit: `9e073483b2f1397ed450b8efd6803754fe22c93e`.
  - Review blob SHA: `04546d990cb355c10c824a3d1ab9ca74caa952f2`.
  - Reviewed P1.8.127 blob: `9e78a0d890f6b190e95746fd31a5fc1ebece33bb`.
  - Verdict: PASS — traceability and decision/status consistency verified; no status inflation or authority expansion found.
- Static readback: PASS. Tests NOT RUN. GitHub Actions NOT DISPATCHED. Workflow run/artifact NONE.
- IR124-01/02/03 remain CLOSED at documentary-design level. IR122-01 remains operationally OPEN pending separately authorized read-only inventory and independent review. Option C technical enforcement remains NOT VERIFIED.
- No live GitHub/API/provider inventory, secret access, IAM/permission/credential/workflow/runner changes, runner jobs, provider probes, remediation or destructive operations were performed or authorized.
- No restore/staging/fault injection/provider/key/TSA operations. No archive/cleanup/vacuum/deletion. Destructive authority NOT GRANTED.
- T0 remains independent; CORE_LEDGER and AI_LEDGER remain separate; `AI_EXECUTION_ENABLED=false`.
- Next gate: any live read-only inventory must be presented as a separate bounded authorization request. Automatic P1.8 documentary approval does not extend to live inspection, operational access or permission changes.


## P1.8.129–P1.8.134 — Read-Only GitHub Inventory Proposal and Endpoint-Matrix Reviews (2026-11-09)

- Continuation remained documentary-only under the owner's automatic P1.8 instruction. No live API inspection or inventory execution was authorized.
- P1.8.129 proposal:
  - Path: `docs/evidence/p1-8/P1.8.129-read-only-github-permission-inventory-execution-proposal.md`.
  - Commit: `e958b1a17f24128243af0272782743f1db842e46`.
  - Blob SHA: `563d476d98d1fc21cfe2b18fda3cfbd2deb9586d`.
  - Bounded proposed repository: `kenznguyen/btcusdt-telegram-signals2`; metadata-only; source content, secret metadata, runner hosts, provider, VPS/T0/T1 and all mutation/execution paths excluded.
  - Status: PROPOSED — NOT APPROVED FOR EXECUTION.
- P1.8.130 independent review:
  - Path: `docs/evidence/p1-8/P1.8.130-independent-static-review-p1-8-129.md`.
  - Commit: `cc9dff21cf3e0b77ca27d1bcb064443ac720acef`.
  - Findings: IR130-01 MAJOR endpoint/permission matrix incomplete; IR130-02 MODERATE owner namespace assumed; IR130-03 MODERATE secret metadata response safety insufficiently gated. Verdict PARTIAL.
- P1.8.131 endpoint permission matrix and scope correction:
  - Path: `docs/evidence/p1-8/P1.8.131-endpoint-permission-matrix-and-scope-correction.md`.
  - Commit: `e6d7fd7416324200df2b77b47955ae63bc1228bb`.
  - Blob SHA: `9a33fcd70087f48fc926f5af532689c7340a23ae`.
  - Adds exact candidate GET endpoints and fine-grained read permissions for repository metadata, Actions policy/workflow permissions, workflow metadata, environments, rulesets, active branch rules and conditional organization Actions policy.
  - Separates token permission from actor-role prerequisites. Excludes collaborator and runner endpoints requiring privileged actors; excludes secret metadata and deploy-key endpoints; records ruleset bypass-actor visibility limitations.
  - Official GitHub REST documentation URLs are included in P1.8.131. Documentation was researched only; no live endpoint was called.
- P1.8.132 independent review:
  - Path: `docs/evidence/p1-8/P1.8.132-independent-static-review-p1-8-131.md`.
  - Commit: `8698d5b2cf11331be1e2e15c56d51149f0b621e2`.  - Verdict PARTIAL; new finding IR132-01 MODERATE: classic branch-protection GET endpoint missing from candidate matrix.
- P1.8.133 classic branch-protection closure:
  - Path: `docs/evidence/p1-8/P1.8.133-classic-branch-protection-endpoint-closure.md`.  - Commit: `b3923082e24529e30abd72aace8dd982372b0769`.
  - Blob SHA: `b90deed965714fa2beb09f11b04752fa0cf3a055`.
  - Adds `GET /repos/{owner}/{repo}/branches/{branch}/protection`, documented repository `Administration: read`, response minimization, branch manifest scope and 404/inherited-rule limitations.- P1.8.134 independent review:
  - Path: `docs/evidence/p1-8/P1.8.134-independent-static-review-p1-8-133.md`.
  - Commit: `c0d17caa21378ade360aaf8c3d2a3f14b5c58c79`.
  - Reviewed P1.8.133 blob: `b90deed965714fa2beb09f11b04752fa0cf3a055`.
  - Verdict PASS; IR132-01 CLOSED at documentary-design level. IR130-01/02/03 remain CLOSED at documentary-design level.
- Current state: IR122-01 remains operationally OPEN. P1.8.129 remains NOT APPROVED FOR EXECUTION. No actual GitHub effective permissions, collaborator/runner inventory, secret provenance, OIDC trust, external provider permissions or complete bypass paths have been verified. Full Option C technical enforcement remains NOT VERIFIED.
- Static author/readback and independent review records: PASS where recorded. Tests NOT RUN. GitHub Actions NOT DISPATCHED. Workflow run/artifact NONE.
- No live GitHub/API/provider inventory, secret access, credential operation, IAM/permission change, workflow dispatch, runner job, provider probe or remediation.
- No staging, restore, fault injection, key/TSA operation, archive, cleanup, vacuum or deletion. Option C remains the approved default; destructive/deletion authority NOT GRANTED.
- T0 remains independent; CORE_LEDGER and AI_LEDGER remain separate; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Next gate: independent static review of the consolidated P1.8.129–P1.8.134 evidence/status index. Any live inventory requires a separate explicit owner approval of exact scope, endpoint set, collector identity, evidence handling and independent reviewer.


## P1.8.135–P1.8.136 — GitHub Read-Only Inventory Proposal Closure Index (2026-11-09)

- P1.8.135 index:
  - Path: `docs/evidence/p1-8/P1.8.135-github-read-only-inventory-proposal-closure-index.md`.
  - Final commit after exact review-blob reconciliation: `86c6d5e6148e15ebfd4ae9e0afcf178bb828bc25`.
  - Final blob SHA: `3fd9196de5745e00545b24e1101619e8fb4149e6`.
  - Consolidates P1.8.129–P1.8.134 proposal, findings, endpoint matrix, exclusions, exact commit/blob identities and future owner-approval gates.
- P1.8.136 independent static review:
  - Path: `docs/evidence/p1-8/P1.8.136-independent-static-review-p1-8-135.md`.
  - Commit: `3e19a5e18ccd36eda9e3226882bd998177687721`.
  - Blob SHA: `74b7db83fd05f6b934012e794c9cc1535cf5d770`.
  - Reviewed P1.8.135 blob: `3fd9196de5745e00545b24e1101619e8fb4149e6`.
  - Verdict: PASS — evidence references, findings, scope exclusions and authorization boundaries are internally consistent.
- Documentary finding state: IR130-01/02/03 and IR132-01 CLOSED at design level. IR122-01 remains operationally OPEN.
- P1.8.129 remains NOT APPROVED FOR EXECUTION. The candidate endpoint list is not an execution list until the owner separately approves exact scope, endpoint subset, collector identity and effective read-only boundary, evidence handling, observation window and independent reviewer.
- Important blind spots remain explicit: collaborator/runner actor-role prerequisites, ruleset bypass-actor visibility, secret metadata and provenance, deploy keys, workflow source, OIDC and provider paths. The metadata-only phase cannot prove full Option C technical enforcement.
- Static author/readback and independent review: PASS. Tests NOT RUN. GitHub Actions NOT DISPATCHED. Workflow run/artifact NONE.
- No live GitHub/API/provider endpoint was called. No live repository/org metadata, credentials or secrets were inspected. No IAM/permission/credential/workflow/runner changes, runner jobs, provider probes or remediation.
- No staging, restore, fault injection, key/TSA operation, archive, cleanup, vacuum or deletion. Option C remains the approved default; destructive/deletion authority NOT GRANTED.
- T0 remains independent; CORE_LEDGER and AI_LEDGER remain separate; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Next gate: owner decision on whether to authorize the bounded read-only inventory and, if so, approval of the exact execution parameters listed in P1.8.135. Automatic documentary approval does not grant this access.


## P1.8.137–P1.8.138 — Bounded GitHub EP-01 Inventory Execution and Independent Review (2026-11-09)

- Owner explicitly approved the bounded read-only inventory under P1.8.135 and separately permitted API inventory.
- One repository metadata GET was executed through the GitHub connector for `kenznguyen/btcusdt-telegram-signals2`.
- EP-01 result: READ SUCCESS. Repository ID `1411446586`; owner `kenznguyen`, type `User`; visibility `public`; archived `false`; default branch `main`.
- Returned repository actor permissions: `admin=true`, `maintain=true`, `push=true`, `pull=true`, `triage=true`. These actor-role fields do not establish the underlying connector credential/token/App effective scopes.
- EP-09 is EXCLUDED because owner type is `User`, not Organization.
- EP-02–EP-08 were NOT RUN. Collection stopped at Phase 0 because the collector's effective read-only boundary and credential identity could not be independently established from non-secret evidence. No secret values/metadata, source contents, IAM/settings/permissions, workflows, runners or providers were accessed or changed.
- P1.8.137 execution record: `docs/evidence/p1-8/P1.8.137-read-only-github-inventory-ep01-execution-record.md`.
  - Commit: `cd17ece7ebe8af035f5354d66a42a6ad091d94d8`.
  - Final blob SHA after read-back: `b563f377044336e7ce5eef7dd956ccd4e879d0ab`.
  - Result: PARTIAL / BLOCKED at Phase 0 after EP-01.
- P1.8.138 independent static review: `docs/evidence/p1-8/P1.8.138-independent-static-review-p1-8-137.md`.
  - Commit: `45c0c53079f0aa1f383a08236b6c8b80671c6161`.
  - Review verdict: PARTIAL. Stop decision and authorization boundaries PASS; IR137-01/02/03 remain OPEN for formal inventory provenance, collector principal attribution and response-minimization evidence.
- IR122-01 remains operationally OPEN. Effective read-only identity/credential scope remains NOT VERIFIED. Full Option C technical enforcement remains NOT VERIFIED.
- Tests NOT RUN. GitHub Actions NOT DISPATCHED. Workflow run/artifact NONE. No source/runtime/VPS/T0/T1/database/Feeder/strategy/ledger/risk changes. No IAM/credential/permission changes. No destructive operation; deletion authority NOT GRANTED.
- T0 remains independent; CORE_LEDGER and AI_LEDGER remain separate; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Next gate: obtain non-secret, independently attributable evidence of the collector's effective read-only boundary within the existing scope. Do not call EP-02–EP-08 unless that precondition is established. Do not create or expand credentials or change permissions to bypass the stop. If proof cannot be obtained within the approved boundary, retain PARTIAL/NOT VERIFIED.

- P1.8.138 final review blob SHA after read-back: `61daada60027b6f962a674231a479b5ce75dc4f8`. The handoff was subsequently refreshed; this line records the earlier intermediate update only.

## P1.8.139–P1.8.140 — Collector Identity and Effective Read-Only Assurance Feasibility (2026-11-09)

- P1.8.139 documentation-only capability/authorization-boundary assessment:
  - Path: `docs/evidence/p1-8/P1.8.139-collector-identity-read-only-assurance-feasibility.md`.
  - Commit: `ef3eeafa9f2d48600bec9c43eee8c1a88e95f6a9`.
  - Final blob SHA after read-back: `d2c5e874c17170fda7345a5436d82ea3a7ea0bb4`.
  - Result: BLOCKED — no in-scope, non-secret evidence path currently establishes the effective read-only collector boundary. Connector catalog inspection found no exposed dedicated authenticated-principal/effective-scope introspection action in the inspected catalog. This is a limitation of the inspected connector path, not a claim about all GitHub APIs.
  - No GitHub API endpoint was called; installation listing was explicitly not called because it is outside the approved P1.8.135 endpoint matrix and would not by itself prove the credential used for EP-01.
- P1.8.140 independent static review:
  - Path: `docs/evidence/p1-8/P1.8.140-independent-static-review-p1-8-139.md`.
  - Commit: `827aeb5b2bec02c87f30d5ffe153024fa0669720`.
  - Final blob SHA after read-back: `fad9b7e472f503a8ddbe7199bfd6de1cc8ca4640`.
  - Verdict: PARTIAL. Fail-closed feasibility conclusion and stop boundary PASS. IR140-01 OPEN: connector catalog observation provenance not reproducible from artifact. IR140-02 OPEN: distinguish narrow repository endpoint-scope assurance from broader GitHub/provider control-plane assurance.
- IR137-01/02/03 remain OPEN; IR140-01/02 remain OPEN; IR122-01 remains operationally OPEN.
- Effective collector principal/credential scope and read-only boundary remain NOT VERIFIED. EP-02–EP-08 remain NOT RUN; EP-09 remains EXCLUDED because owner type is User. Full Option C technical enforcement remains NOT VERIFIED.
- Tests NOT RUN. GitHub Actions NOT DISPATCHED. Workflow run/artifact NONE. No API calls, credential/secret inspection, IAM/permission/credential changes, workflow/runner/provider operations, source/runtime/VPS/T0/T1/database/Feeder/strategy/ledger/risk changes, or destructive operations.
- No destructive/deletion authority. Option C remains approved. T0 remains independent; CORE_LEDGER and AI_LEDGER remain separate; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Next gate: keep the inventory BLOCKED unless non-secret evidence can independently bind a stable collector principal and effective read-only scope to the exact approved request path. Any broader control-plane assurance or different identity/credential path requires a separate bounded proposal and explicit owner approval. Do not call EP-02–EP-08 or installation listing to bypass the current stop.

## P1.8.141 — Holistic Data Lifecycle Design Closure Assessment (2026-11-09)

- Assessment: `docs/evidence/p1-8/P1.8.141-holistic-data-lifecycle-design-closure-assessment.md`.
- Commit: `2e7f90c7dbc97a46a1ab1653eb5581ea35dfafa6`.
- Final blob SHA after read-back: `c20616d79f6dcedde08128f589a5c0e04d6257f1`.
- Source branch HEAD at review start: `7c35fb80d8abed17d21602fa597699cfae420c2a`.
- Scope: documentation-only holistic review of the lifecycle architecture and P1.8.80–P1.8.140 evidence. Compared retention, consumer/dependency, hold, copy/evidence, request-state, mutation-fencing, negative-case, availability, V07/V08/Restore/TSA and Option C contracts.
- Verdict: PARTIAL — core safety model is coherent at documentary level; lifecycle design is NOT READY FOR CLOSURE OR IMPLEMENTATION.
- No direct cross-contract contradiction granting destructive authority was found. Option C remains the owner-approved default. T0 remains independent; CORE_LEDGER and AI_LEDGER remain separate.
- Residual findings LDA-01–LDA-09: retention/class disposition decisions OPEN; V07 trust/revocation parameters BLOCKED; V08 durable ordering parameters OPEN/BLOCKED; Restore measurement/provider proof OPEN/BLOCKED; mutation-fence/backend adapter capability NOT VERIFIED; runtime consumer/copy inventory NOT VERIFIED; 87 negative vectors specified but all NOT_RUN; Option C technical enforcement NOT VERIFIED; current Option C also keeps archive/irreversible transitions non-executable.
- GitHub permission inventory remains PAUSED by owner instruction. No additional API calls, collector identity proposal, credential inspection or permission changes were performed.
- Tests NOT RUN. GitHub Actions NOT DISPATCHED. Workflow run/artifact NONE.
- No source/runtime/schema/API/registry/adapter/scheduler/VPS/T0/T1/Feeder/ledger/strategy/risk changes; no provider/key/TSA/restore/staging/fault-injection operations; no archive/cleanup/vacuum/deletion. Destructive authority NOT GRANTED.
- Next gate: owner-level, evidence-backed retention policy decisions; keep all runtime, provider, identity, test and destructive work separately gated. Do not infer numeric TTLs or deletion eligibility.

## P1.8.142 — Owner Retention and Data-Class Disposition Decision Package (2026-11-09)

- Package: `docs/evidence/p1-8/P1.8.142-owner-retention-and-data-class-disposition-decision-package.md`.
- Commit: `13557657eeabfb80f5c810271896a605359a4762`.
- Final blob SHA after read-back: `a8b6027c5ff25192ebba82dadc52c70dd1983c82`.
- Scope: documentary owner-decision package based on P1.8.80, central lifecycle policy, consumer contract, deletion safety contract, copy/backup/replica contract, Option C and P1.8.141.
- Recommendation RET-01: T0 canonical data protected by default, with only a narrowly scoped exceptional review path for a separately ratified binding legal/security requirement; no routine lifecycle deletion. This is a recommendation, NOT owner-ratified.
- Recommendation RET-02: restrict any future read-only deletion-eligibility review to a limited noncanonical set: exact T4 rebuildable cache/read-model/materialization; T2 ephemeral inference output after proving no material downstream decision/claim; T1 raw observation only after exact reproducibility and obligation closure; individually identified copies after copy-specific checks. No class-wide or automatic eligibility.
- T3 CORE_LEDGER and AI_LEDGER, T0 canonical data, governance/audit/tombstone evidence and unknown data remain protected/excluded from class-wide review.
- Numeric retention floors, TTL, grace, review cadence, authorization lifetime and evidence freshness remain OPEN; no values inferred.
- Archive remains non-executable under current Option C. No deletion, archive, cleanup, vacuum, compaction, backup expiry, replica removal or other destructive authority is granted.
- Owner decisions RET-01 and RET-02 require explicit ratification/revision/deferment. Other RET decisions remain OPEN or NOT VERIFIED as recorded in package.
- GitHub permission inventory remains PAUSED. No additional API calls, runtime/data inventory, tests, workflow dispatch or artifacts.
- No source/runtime/schema/API/registry/adapter/scheduler/VPS/T0/T1/T2/T3/T4/Feeder/ledger/strategy/risk changes. No staging, restore, provider/key/TSA operation, synthetic execution or destructive action.
- Status: DECISION PACKAGE PREPARED — OWNER RATIFICATION REQUIRED — NO POLICY CHANGE OR OPERATIONAL AUTHORITY ACTIVATED.

## P1.8.143 — Owner Retention Policy Ratification (2026-11-09)

- Owner explicitly approved RET-01 option B and RET-02 option B from P1.8.142.
- Ratification record: `docs/evidence/p1-8/P1.8.143-owner-retention-policy-ratification.md`.
- Record commit: `e938d90b2b95d4d432db0eb387b64601e21c5e3c`.
- RET-01 B ratified: T0 canonical data is protected by default; no routine or automatic deletion. A narrowly scoped binding legal/security exception may only be considered through separate evidence, competent review and a new explicit owner decision. No exception or execution is approved.
- RET-02 B ratified: only exact T4 rebuildable caches/read models/materializations, T2 ephemeral inference outputs, T1 raw observations meeting strict reproducibility/obligation-closure proof, and individually identified noncanonical copies may enter future read-only eligibility assessment. This does not make any class/object automatically eligible or authorize mutation.
- T0, CORE_LEDGER, AI_LEDGER, required T3 reconstruction/audit records, governance approvals/policy history/tombstones/evidence, and unknown/unclassified/orphaned/incompletely inventoried data remain excluded from ordinary class-wide deletion review.
- RET-03 through RET-10 remain OPEN/NOT VERIFIED as recorded in P1.8.142. No TTL, retention floor, grace, cadence, authorization lifetime or freshness value was set.
- Option C — No Destructive Authority — remains in force. Archive remains non-executable. No deletion, cleanup, vacuum, compaction, backup expiry, replica removal, runtime inventory, provider operation or permission change is authorized.
- GitHub permission inventory remains PAUSED. T0 remains independent; CORE_LEDGER and AI_LEDGER remain separate; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Tests NOT RUN. GitHub Actions NOT DISPATCHED. Workflow run/artifact NONE. Runtime enforcement NOT VERIFIED. Lifecycle design closure NOT ESTABLISHED; P1.8.141 residual findings remain open.
- Next gate: continue with bounded documentary analysis of unresolved P1.8.141 findings and RET-03–RET-10; each operational, identity, provider, test or destructive activity remains separately gated.
- Status: RET-01/RET-02 OWNER-RATIFIED — POLICY ONLY — NO IMPLEMENTATION OR DESTRUCTIVE AUTHORITY.

## P1.8.144 — Retention Floor Evidence Contract (2026-11-09)

- Contract: `docs/evidence/p1-8/P1.8.144-retention-floor-evidence-contract.md`.
- Commit: `0d1547edc0eb98148c3b573eb4dcc40d8ff8954b`.
- Scope: documentation-only contract defining how an evidence-backed minimum retention floor may be established for an exact object/version/copy without inventing TTLs or confusing retention completion with deletion authority.
- Defines the obligation-set rule: candidate floor is the latest proven end among all applicable obligations, and is valid only when scope/inventory is sufficiently complete, every applicable end condition is evidenced, holds/dependencies/recovery/copy obligations are closed, and time/order evidence is adequate. Unknown or unproven obligations produce FLOOR_NOT_ESTABLISHED / RETAIN / BLOCKED.
- Covers legal/contractual, canonical/source, consumer, replay/correction, training/inference/evaluation, backtest/research, trading/paper reconstruction, audit/security/incident, recovery/backup, replica/failover, export/recipient, governance/evidence, copy lineage and availability domains.
- Applies ratified RET-01 B / RET-02 B: T0 remains protected with no routine deletion path; only the limited noncanonical RET-02 classes may enter future read-only exact-object/version assessment. CORE_LEDGER and AI_LEDGER remain separate/protected; unknown data remains blocked.
- No numeric retention floor, TTL, grace, freshness, cadence or authorization lifetime was selected. RET-03 remains OPEN. Archive remains non-executable; Option C remains in force; destructive authority NOT GRANTED.
- Independent review REQUIRED / NOT RUN. Tests NOT RUN. GitHub Actions NOT DISPATCHED. Workflow run/artifact NONE. Read-back pending.
- No runtime/data/provider inventory, source/runtime/schema/API/registry/adapter/scheduler/VPS/T0/T1/T2/T3/T4/Feeder/ledger/strategy/risk change, staging, restore, fault injection, workflow dispatch, archive, cleanup, vacuum, compaction, backup expiry, replica removal or deletion.
- GitHub permission inventory remains PAUSED. `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Next gate: read back P1.8.144 and obtain an independent static review of its completeness and consistency with P1.8.80–P1.8.143, especially consumer/dependency, copy/hold, restore, trusted-time, V07/V08/TSA and Option C contracts. No implementation or operational work is implied.
- Status: CONTRACT DRAFTED — INDEPENDENT REVIEW REQUIRED — NO NUMERIC RETENTION POLICY OR DESTRUCTIVE AUTHORITY.

## P1.8.145 — Independent Static Review of P1.8.144 (2026-11-09)

- Review: `docs/evidence/p1-8/P1.8.145-independent-static-review-p1-8-144.md`.
- Commit: `1ddf6337800d2a13f282911cd2938b08f9788a0d`.
- Target P1.8.144 blob reviewed: `f3002ba709f874936ca434c883ef855d2f11784a`.
- Verdict: PARTIAL — core safety direction PASS; P1.8.144 is NOT READY for retention-floor acceptance.
- Findings: IR145-01 MAJOR — obligation-inventory completeness proof/source coverage not specified; IR145-02 MAJOR — typed terminal obligation states and recurring/indefinite obligation handling not specified; IR145-03 MODERATE — copy/backup-chain graph and floor aggregation semantics incomplete; IR145-04 MODERATE — RET-02 noncanonical-copy boundary should be explicit in class-specific rules; IR145-05 MINOR — reviewer independence/competency evidence underspecified.
- Cross-contract: RET-01/02 ratification and Option C PASS; no weakening of P1.8.93 mutation-fence or P1.8.117 final-boundary trusted-time semantics identified. Restore/V08/TSA graph evidence remains PARTIAL; P1.8.141 residual findings remain open.
- Recommended next documentary task: P1.8.146 — Retention Obligation Inventory Completeness, Typed End-State and Copy-Graph Clarification. This is a recommendation only; no additional authority is inferred.
- Tests NOT RUN. GitHub Actions NOT DISPATCHED. Workflow run/artifact NONE. Runtime/data/provider inventory NOT PERFORMED. Adapter enforcement NOT VERIFIED. Negative vectors NOT RUN.
- No source/runtime/schema/API/registry/adapter/scheduler/VPS/T0/T1/T2/T3/T4/Feeder/ledger/strategy/risk changes; no provider/identity/permission work; no staging, restore, fault injection, synthetic execution, archive, cleanup, vacuum, compaction, backup expiry, replica removal or deletion.
- GitHub permission inventory remains PAUSED. T0 remains independent; CORE_LEDGER and AI_LEDGER remain separate; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Option C remains in force. Destructive authority NOT GRANTED.
- Status: P1.8.145 STATIC REVIEW COMPLETE — PARTIAL — CONTRACT CLARIFICATION REQUIRED — NO IMPLEMENTATION OR DESTRUCTIVE AUTHORITY.


## Latest completed work — P1.8.146 (2026-11-09)

- Added documentation-only clarification supplement: `docs/evidence/p1-8/P1.8.146-retention-obligation-completeness-end-state-copy-graph-clarification.md`.
- Commit: `e6f0f428771353b97e84babdd51085ce94fc5cce`.
- Scope: addresses P1.8.145 IR145-01..05 without retroactively changing P1.8.144 or ratified owner decisions.
- Defines bounded assessment scope, versioned source-of-truth manifest, source authority/coverage/freshness/reconciliation and fail-closed completeness proof.
- Defines typed obligation states ACTIVE, SATISFIED, RELEASED, SUPERSEDED_WITH_SUCCESSOR, INDEFINITE and UNKNOWN, including terminal evidence, successor linkage and recurring/ongoing obligation handling.
- Defines copy/backup/restore-set graph nodes, edges, shared dependencies and bounded affected-scope semantics without cascade disposition.
- Reasserts RET-02 applies only to individually identified noncanonical copies; T0 canonical data and T0 availability/recovery copies remain protected under RET-01 B absent a separate exceptional owner decision.
- Adds reviewer competency, independence, conflict-of-interest and specialist/legal attribution evidence requirements.
- Status: CLARIFICATION DRAFTED; INDEPENDENT STATIC REVIEW REQUIRED. Documentary specification only; no runtime inventory, tests, provider/identity work or implementation.
- Tests NOT RUN. GitHub Actions NOT DISPATCHED. Workflow run/artifact NONE. Runtime enforcement NOT VERIFIED.
- Option C remains in force; archive and destructive transitions remain non-executable. Destructive authority NOT GRANTED. GitHub permission inventory remains PAUSED.
- No source/runtime/schema/API/registry/adapter/scheduler/VPS/T0/T1/T2/T3/T4/Feeder/ledger/strategy/risk changes; no staging, restore, fault injection, provider/key/TSA operation, cleanup, vacuum, compaction, backup expiry, replica removal or deletion.
- Next step: independent static review of P1.8.146 against P1.8.142–P1.8.145 and controlling lifecycle contracts. Any operational inventory, test execution or destructive work requires separate explicit approval.


## Latest completed work — P1.8.147 (2026-11-09)

- Completed documentation-only independent static review of P1.8.146 against P1.8.144, P1.8.145, P1.8.143, P1.8.93 and P1.8.117.
- Review: `docs/evidence/p1-8/P1.8.147-independent-static-review-p1-8-146.md`.
- Review commit: `f22befd498667b40df0ae54aa4e674dbcea233c7`.
- Target P1.8.146 blob reviewed: `5efb0ae86d88ede5627ed7b77322463c39fb737e`.
- Verdict: PARTIAL. IR145-01 through IR145-04 CLOSED at documentary specification level. IR145-05 substantially addressed but IR147-01 MODERATE remains OPEN: P1.8.146 records conflicts across requester/custodian/obligation-owner/approver/executor roles but does not mandate independence from all of them or require an independent second-review control where roles overlap.
- Cross-contract review: RET-01 B, RET-02 B, Option C, T0 independence, CORE_LEDGER/AI_LEDGER separation, P1.8.93 mutation-fencing and P1.8.117 trusted-time final-boundary semantics remain consistent.
- Recommended next step: P1.8.148 — Reviewer Independence and Conflict-Control Clarification, documentation-only, narrowly addressing mandatory role separation and independent second review.
- Tests NOT RUN. GitHub Actions NOT DISPATCHED. Workflow run/artifact NONE. Runtime/data/provider/identity inventory NOT PERFORMED. Runtime enforcement NOT VERIFIED.
- No source/runtime/schema/API/registry/adapter/scheduler/VPS/T0/T1/T2/T3/T4/Feeder/ledger/strategy/risk changes; no staging, restore, fault injection, provider/key/TSA operations, archive, cleanup, vacuum, compaction, backup expiry, replica removal or deletion.
- GitHub permission inventory remains PAUSED. Option C remains in force. Destructive authority NOT GRANTED.


## Latest completed work — P1.8.148 (2026-11-09)

- Added documentation-only supplement: `docs/evidence/p1-8/P1.8.148-reviewer-independence-conflict-control-clarification.md`.
- Commit: `7bf13e2f9a5eb69a4e14fe504268c12ee34d51e6`.
- Final target blob SHA after read-back: `baea1eb363a06ea7e804fe986777b31e9b693513`.
- Scope: closes the narrow documentary gap IR147-01 by requiring independence from requester, custodian, obligation owner, approver, executor and provider selector; mandates an independent second review for every affected claim when full role separation is infeasible; conflicted persons cannot be sole reviewers/verifiers.
- Adds claim-to-role matrix, direct examination of underlying evidence, competence/specialist boundaries and fail-closed rules.
- Preserves RET-01 B / RET-02 B, T0 protection, ledger separation and Option C — No Destructive Authority.
- Status: CLARIFICATION DRAFTED — INDEPENDENT STATIC REVIEW REQUIRED. No identity/personnel/permission inventory or operational assessment.
- Tests NOT RUN. GitHub Actions NOT DISPATCHED. Workflow run/artifact NONE. Runtime enforcement NOT VERIFIED.
- No source/runtime/schema/API/registry/adapter/scheduler/VPS/T0/T1/T2/T3/T4/Feeder/ledger/strategy/risk changes; no staging, restore, fault injection, provider/key/TSA operations, archive, cleanup, vacuum, compaction, backup expiry, replica removal or deletion.
- GitHub permission inventory remains PAUSED. Destructive authority NOT GRANTED.
- Next gate: independent static review of P1.8.148 against P1.8.146–P1.8.147 and controlling lifecycle contracts. No implementation or operational work is implied.


## Latest completed work — P1.8.149 (2026-11-09)

- Completed documentation-only independent static review of P1.8.148 against P1.8.146 §6, P1.8.147, P1.8.144, P1.8.143 and controlling lifecycle authority boundaries.
- Review: `docs/evidence/p1-8/P1.8.149-independent-static-review-p1-8-148.md`.
- Review commit: `cdf0322affefb053fec1a9b1a0d4a9ba6e784d1e`.
- Target P1.8.148 blob reviewed: `baea1eb363a06ea7e804fe986777b31e9b693513`.
- Final review blob SHA after read-back: `cce7aa0bf9c7b6048b61ef5c436433e3ac0c01c4`.
- Verdict: PARTIAL. P1.8.148 materially strengthens mandatory role separation, second review, evidence provenance, competence and fail-closed behavior. IR147-01 is substantially addressed but not closed.
- IR149-01 MODERATE OPEN: ambiguity remains whether a conflicted person may act as primary reviewer when a qualifying independent second reviewer is used. Required clarification: distinguish conflicted contributor/non-authoritative preliminary assessment from the qualifying independent reviewer who alone issues the independent review disposition.
- Cross-contract: RET-01 B / RET-02 B, T0 protection, CORE_LEDGER/AI_LEDGER separation, retention-floor evidence-only boundary and Option C remain PASS/preserved.
- Status: STATIC REVIEW COMPLETE — PARTIAL — DOCUMENTARY CLARIFICATION REQUIRED.
- Tests NOT RUN. GitHub Actions NOT DISPATCHED. Workflow run/artifact NONE. Runtime enforcement NOT VERIFIED. Identity/personnel/permission and operational inventories NOT PERFORMED.
- No source/runtime/schema/API/registry/adapter/scheduler/VPS/T0/T1/T2/T3/T4/Feeder/ledger/strategy/risk changes; no staging, restore, fault injection, provider/key/TSA operations, archive, cleanup, vacuum, compaction, backup expiry, replica removal or deletion.
- GitHub permission inventory remains PAUSED. Option C remains in force. Destructive authority NOT GRANTED.
- Recommended next step: P1.8.150 — Conflicted Contributor versus Qualifying Independent Reviewer Clarification, documentation-only. No implementation or operational work is implied.


## Latest completed work — P1.8.150 (2026-11-09)

- Added documentation-only supplement: `docs/evidence/p1-8/P1.8.150-conflicted-contributor-independent-reviewer-clarification.md`.
- Commit: `600704c5c969dc6bcbfbd48736bc45430a777b98`.
- Final target blob SHA after read-back: `f23fbcfdc85c82b95271d835a1e452e4a9863db2`.
- Scope: addresses P1.8.149 IR149-01 by distinguishing CONFLICTED CONTRIBUTOR / evidence producer from QUALIFYING INDEPENDENT REVIEWER.
- A conflicted participant may provide factual inputs or a preliminary analysis only when labelled NON-INDEPENDENT — NON-AUTHORITATIVE — NOT AN ACCEPTANCE; cannot issue, approve, co-sign, veto or override the independent disposition.
- Where role separation is infeasible, the independent second reviewer becomes the sole qualifying reviewer for the affected claim and must directly examine underlying evidence. If none is available, claim remains INDEPENDENT_REVIEW_REQUIRED / BLOCKED.
- Preserves P1.8.143 RET-01 B / RET-02 B, T0 protection, CORE_LEDGER/AI_LEDGER separation and Option C — No Destructive Authority.
- Status: CLARIFICATION DRAFTED — INDEPENDENT STATIC REVIEW REQUIRED. Documentary-only; no personnel/identity/permission inventory.
- Tests NOT RUN. GitHub Actions NOT DISPATCHED. Workflow run/artifact NONE. Runtime enforcement NOT VERIFIED.
- No source/runtime/schema/API/registry/adapter/scheduler/VPS/T0/T1/T2/T3/T4/Feeder/ledger/strategy/risk changes; no staging, restore, fault injection, provider/key/TSA operations, archive, cleanup, vacuum, compaction, backup expiry, replica removal or deletion.
- GitHub permission inventory remains PAUSED. Destructive authority NOT GRANTED.
- Next gate: independent static review of P1.8.150 against P1.8.148–P1.8.149, P1.8.146 §6 and controlling lifecycle contracts. No implementation or operational work is implied.


## Latest completed work — P1.8.151 (2026-11-09)

- Completed documentation-only independent static review of P1.8.150.
- Review: `docs/evidence/p1-8/P1.8.151-independent-static-review-p1-8-150.md`.
- Review commit: `d6ff977324461eb293f41e501e23c602fa7c2500`.
- Target P1.8.150 blob reviewed: `f23fbcfdc85c82b95271d835a1e452e4a9863db2`.
- Final review blob SHA after read-back: `64902f09d0f5576a47da44dbb194a56e18d727c2`.
- Verdict: PASS — P1.8.150 resolves P1.8.149 IR149-01 at documentary specification level.
- IR149-01 is CLOSED at documentary specification level: conflicted participants are contributors/evidence producers only, cannot issue or accept independent dispositions; where separation is infeasible, the independent second reviewer is the sole qualifying reviewer for the affected claim and directly examines underlying evidence; absence of a qualifying reviewer remains INDEPENDENT_REVIEW_REQUIRED / BLOCKED.
- Cross-contract checks PASS for P1.8.148, P1.8.146 §6, P1.8.144, RET-01 B / RET-02 B, T0 protection, CORE_LEDGER / AI_LEDGER separation and Option C.
- Limit: PASS is documentary only. Actual personnel/identity independence, competence, inventory completeness and runtime enforcement remain NOT VERIFIED. P1.8.141 residual findings and other prior open findings are not closed by this review.
- Tests NOT RUN. GitHub Actions NOT DISPATCHED. Workflow run/artifact NONE. Runtime/data/provider/identity inventory NOT PERFORMED.
- No source/runtime/schema/API/registry/adapter/scheduler/VPS/T0/T1/T2/T3/T4/Feeder/ledger/strategy/risk changes; no staging, restore, fault injection, provider/key/TSA operations, archive, cleanup, vacuum, compaction, backup expiry, replica removal or deletion.
- GitHub permission inventory remains PAUSED. Option C remains in force. Destructive authority NOT GRANTED.
- Next gate: continue with the next unresolved documentary lifecycle finding from P1.8.141 / retention controls; do not infer closure or authorize operational/destructive work from P1.8.151.


## Latest completed work — P1.8.152 (2026-11-09)

- Completed documentation-only reconciliation of P1.8.141 LDA-01 through LDA-09 against P1.8.142–P1.8.151.
- Record: `docs/evidence/p1-8/P1.8.152-retention-and-lifecycle-residual-finding-reconciliation.md`.
- Commit: `cc72eeb74e3b26c2fa39d2ddd6d436620c47553c`.
- Final document blob SHA after read-back: `e1a4d95af216e94a58fa5528850fcd0c1ff465f8`.
- Reconciled verdict: PARTIAL — lifecycle design NOT CLOSED.
- LDA-01 PARTIALLY RESOLVED: RET-01 B / RET-02 B are owner-ratified; RET-03–RET-10 remain open, non-executable or not verified according to their individual status. P1.8.144 is not accepted as a complete retention-floor contract.
- LDA-02 V07 BLOCKED; LDA-03 V08 OPEN/BLOCKED; LDA-04 Restore OPEN/BLOCKED; LDA-05 mutation fence/adapter NOT VERIFIED; LDA-06 runtime consumer/copy inventory NOT VERIFIED; LDA-07 87 negative vectors remain NOT RUN; LDA-08 Option C technical enforcement NOT VERIFIED and GitHub permission inventory remains PAUSED.
- LDA-09 archive-policy alignment is evidenced at documentary level; archive remains non-executable under Option C. Formal finding closure requires independent review.
- Reviewer-control distinction preserved: IR145-01..04 CLOSED at documentary specification level; IR147-01 remains NOT CLOSED (P1.8.149 says substantially addressed but not closed); IR149-01 CLOSED by P1.8.151. P1.8.144 therefore remains not accepted as a complete floor contract.
- Source branch HEAD at start: `0804c02ede010697c69c80cacd43d3fbb301e5e2`.
- Tests NOT RUN. GitHub Actions NOT DISPATCHED. Workflow run/artifact NONE.
- No runtime, source, schema, API, registry, adapter, scheduler, VPS, T0/T1/T2/T3/T4, Feeder, ledger, strategy or risk changes. No operational inventory, provider/key/TSA, staging, restore, fault injection, archive, cleanup, vacuum, compaction, backup expiry, replica removal, export mutation or deletion.
- Option C remains in force; T0 remains independent; CORE_LEDGER and AI_LEDGER remain separate; paper-only; `AI_EXECUTION_ENABLED=false`; destructive authority NOT GRANTED.
- Next bounded documentary gate: P1.8.153 — independent review of P1.8.152 and residual reviewer-control closure assessment. No identity/personnel discovery, permission inventory, runtime/provider inventory, tests, workflow dispatch or destructive operations are implied.

## T0 → T2 Loopback Deployment Gate — 2026-11-09

- Owner approved same-VPS T0/T2 loopback deployment, allowed Feeder/DB changes and T1/T2 runtime activation within the ordered rollout; no OKX replacement and no live trading.
- Deployment-gate record: `docs/evidence/t2/T0_T2_LOOPBACK_DEPLOYMENT_GATE_2026-11-09.md`.
- Record commit: `9e7967adc6c328c6772607f2fb95842a627a313b`.
- Latest recorded T0 VPS source SHA: `9ae2eeae4ece3d657781b68e96b6f4509cd95f24`.
- Exact file blob parity between that T0 source commit and current branch HEAD `e11f174ea2e9dce4bc528b4de019d94d36be70c2` was verified for `market_data/api.py`, `market_data/feeder.py`, `market_data/feeder_service.py`, `market_data/write_gateway.py`, `market_data/storage.py`, and `market_data/store.py`. This is file-level source parity, not proof of loaded process bytes.
- T2 HTTP consumer migration and isolated loopback integration remain PASS at their recorded source SHAs; live canonical T0 API read remains NOT VERIFIED.
- Current T0 API listener/service state: NOT VERIFIED. The 2026-11-08 no-listener observation is historical and must not be treated as current.
- No authenticated SSH/terminal action for the Scaleway VPS is exposed in the current tool connection; plugin discovery found no available SSH/VPS execution connector. No remote command, API deployment, T2 one-shot read, or runtime activation was performed.
- Tests NOT RUN for this documentation increment. GitHub Actions NOT DISPATCHED; workflow run/artifact NONE. VPS/Feeder/DB/API/T2 runtime unchanged.
- Status: PARTIAL / BLOCKED AT VPS EXECUTION. Next gate: obtain authenticated remote execution or operator-run reviewed procedure; verify API loopback-only, GET/auth/read-only behavior, complete/fresh M15 data, then run one-shot T2 context read. Do not start T1 before this gate passes.
- No public API exposure, OKX source replacement, live orders, strategy/ledger/risk changes, or data deletion authorized. `AI_EXECUTION_ENABLED=false` remains in force.

## Latest completed work — P1 GitHub Actions Authenticated SSH Preflight (2026-11-09)

- Owner explicitly approved P1 within a strict read-only remote inspection scope. No service start/stop/restart, deployment, source update, DB mutation, permission broadening, firewall change, T1/T2 activation, API request, live trading or destructive action is included.
- Extended existing manual workflow `.github/workflows/t0-manual-validation.yml` with gate `scaleway-ssh-preflight`; workflow final commit: `63094a1d550ed3fabf51e2627d247a49e0dc3128`; final workflow blob SHA: `395ae93274a9202f14ab63d528be5cd582c30149`.
- Added forced-command read-only remote script `ops/ssh/t0-readonly-preflight.sh`; file commit: `94dd300014fc85444d60eb85ad09cd343a7da231`; final blob SHA: `39de5aa7602cdf7dc301ff6bc65a68fad417ea84`.
- Added contract tests `ci/test_t0_ssh_preflight_contract.py`; file commit: `a4f5a0b3877567d8c4c1b884d406461acac935fa`; final blob SHA: `d485052f63d2bdc57d2129a8ce83496e82ce3206`.
- Added setup/authorization/evidence record `docs/evidence/t2/P1_GITHUB_ACTIONS_AUTHENTICATED_SSH_PREFLIGHT_2026-11-09.md`; commit: `b8efdecc2d8104b8e9f7be4519650dadb334c289`; blob SHA: `21187d1362d7afb1705e17b263069f6f2479f309`.
- Workflow security shape: contract job runs before SSH job; SSH job is protected by GitHub Environment `scaleway-preflight`; secrets are environment-scoped; host key pinning is mandatory; no runtime ssh-keyscan; SSH sends no remote command and relies on a server-side forced command; account must be dedicated, non-root, no sudo, and key restricted against forwarding/PTY.
- Remote command only reports sanitized host/user, source SHA, Feeder PID(s), TCP 8788 listener binding and read-only SQLite integrity. DB access uses `mode=ro`, `PRAGMA query_only=ON`, and `PRAGMA integrity_check`.
- Verification performed: remote shell `bash -n` PASS; Python test module `py_compile` PASS; GitHub read-back/static assertions 11/11 PASS; exact workflow/script/test/evidence blob SHAs verified.
- Actual unit test execution NOT RUN; GitHub Actions workflow NOT DISPATCHED; workflow YAML not yet validated by a GitHub run. No SSH private key or connection secret was generated, received, or stored in this session.
- Dedicated VPS account, root-owned forced-command installation, authorized_keys restriction, host-key pin verification, file ACL review and GitHub Environment/secrets setup remain NOT DONE. Remote SSH authentication and VPS inspection NOT VERIFIED.
- Final implementation status: **PARTIAL — REPOSITORY IMPLEMENTATION RECORDED; OPERATOR SETUP AND REMOTE PREFLIGHT PENDING**. No VPS/T0/T1/DB/Feeder/API/T2 runtime change was made.
- Next step: operator completes the one-time secure setup described in `docs/evidence/t2/P1_GITHUB_ACTIONS_AUTHENTICATED_SSH_PREFLIGHT_2026-11-09.md`, then manually dispatches `T0 Manual Validation → scaleway-ssh-preflight` on this branch. Record exact run ID, tested source SHA, artifact ID and final verdict after the run.
- After P1 PASS, API deployment and T2 one-shot read remain separate rollout gates. No live trading; `AI_EXECUTION_ENABLED=false`.

### P1 follow-up — contract-test hardening

- Strengthened `ci/test_t0_ssh_preflight_contract.py` to assert Ed25519-only host-key algorithm pinning, the fixed SSH target invocation with no remote command argument, and absence of `ssh-keyscan`.
- Test hardening commit: `8161b3ed1daeb7d0e27c7846b4cf0161353ea583`; final test blob SHA: `d27df67b24de575669aeed5e51f966f45768f79d`.
- Updated P1 evidence record commit: `badc696a436409062906debe6333652adfe3cdfa`; final evidence blob SHA: `74f8d7e86aa7cae22af0f987371db7c8aeb5b233`.
- Static GitHub read-back assertions PASS; shell syntax and Python compilation PASS. Actual unit test run and GitHub Actions dispatch remain NOT RUN; no remote access or VPS mutation.


## T0 → T2 Loopback Runtime Verification — 2026-11-09

- Completed the owner-approved same-VPS loopback API gate and bounded T2 one-shot canonical-context read.
- Evidence record: `docs/evidence/t2/T0_T2_LOOPBACK_RUNTIME_VERIFICATION_2026-11-09.md`.
- Evidence record commit: `e5d7ceac664ce419f0b421ddeee291aa92d27d3d`.
- T0 VPS source SHA reported by operator: `9ae2eeae4ece3d657781b68e96b6f4509cd95f24`.
- T2 `freqai_bridge/context.py` SHA-256 reported from VPS: `e22d6c7d186b1fb9a5079eb9b4224c8acbcd835a0938dc970e9bc4b072eb75d3`.
- T0 Candle API: active under systemd, bound only to `127.0.0.1:8788`; `/health` HTTP 200; unauthenticated candle request HTTP 401; authenticated M15/H1 requests HTTP 200. Service remains disabled for boot autostart.
- M15/H1 each returned 2/2 closed VALIDATED candles, complete coverage, no gaps. API dataset versions recorded in the evidence document.
- T2 freshness logic was inspected: `max_lag_ms=120000` applies to ingestion lag `availableAtMs - closeTimeMs`, not candle age / `closeLagMs`. Observed latest M15 ingestion lag 8,558 ms; PASS. No threshold change.
- T2 one-shot command with `--bars 2`: exit code 0; BTCUSDT M15; 2 candles; complete coverage; JSON parse PASS.
- T2 dataset version: `sha256:104e7a83286ac0b35c4665964ae29c5926e8deb18220b715e73f51b94cffb05f`.
- Local VPS artifact: `/tmp/t2-canonical-window-20261109T112946Z.json`. It was not uploaded to GitHub Actions artifacts.
- Overall gate: **PASS — T0 loopback API and bounded T2 canonical-context read**.
- GitHub Actions NOT DISPATCHED for this operator-run runtime gate; workflow run ID NONE; Actions artifact ID NONE. This record does not claim process-loaded byte attestation.
- T1 remains NOT ACTIVATED in this gate. No Feeder restart, DB/WAL mutation, strategy/model/signal/ledger/risk change, OKX replacement, live order, or data deletion. `AI_EXECUTION_ENABLED=false`.
- Next step: review and authorize the next rollout gate separately; do not infer T1 activation or expanded T2 execution from this PASS.


## Latest completed work — T1 Collector and Data Contract Compatibility Review (2026-11-09)

- Added read-only static review: `docs/evidence/t1/T1_COLLECTOR_DATA_CONTRACT_COMPATIBILITY_REVIEW_2026-11-09.md`.
- Evidence commit: `27838b1329ba3a3dc5a964d070f094d228814c91`.
- Reviewed T1 repository `kenznguyen/binance-futures-collector`, PR #1 (OPEN / DRAFT / not merged), exact PR head SHA `6e20fe94f3ad64cc450e73def80a167fe371e49e`.
- Source/contract findings: T1 persists partitioned CSV, not T0 canonical SQLite or Candle HTTP; documented kline source is 1m while canonical T0/T2 paths require 15m/1h; reviewed CSV schema does not establish the T0 candle envelope/coverage/quality/closed-candle semantics; buffered `flush()` is not a durable ingestion ACK; connection sidecar is explicitly not integrated and does not prove market-data completeness.
- Exact-head GitHub Actions run `42479498182`: SUCCESS, 5/5 jobs; no artifact published. CI success is code-level evidence only and does not establish T0/T2 compatibility or runtime readiness.
- Status: **PARTIAL — T1 repository CI PASS; T1→T0/T2 contract compatibility BLOCKED**. Static review only; no tests executed in this review, no VPS/runtime/deployment, no T1 activation, no adapter/integration, no T0/T2/strategy/ledger/risk changes.
- Required next step: freeze a versioned T1 source-file contract and design a read-only, idempotent ingestion adapter plus deterministic 1m→15m/1h aggregation/coverage tests. Keep T0 canonical storage independent; do not allow T1 direct writes into T0. Independent review and a separate activation approval remain required.
- Guardrails preserved: paper-only, `AI_EXECUTION_ENABLED=false`, no OKX replacement, no live orders, no data deletion/archive/cleanup/vacuum/compaction/backup expiry or destructive testing.


## Latest completed work — T1 Source-File Contract v1 and Ingestion Adapter Design (2026-11-09)

- Added design proposal: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_AND_INGESTION_ADAPTER_DESIGN_2026-11-09.md`.
- Design commit: `ce9546e98ff898b2537d2188567a35a772388093`.
- Design is based on T1 PR #1 exact source SHA `6e20fe94f3ad64cc450e73def80a167fe371e49e`, including README, config, CSV writer, models, constants and `docs/SCHEMA.md`.
- Critical finding: T1's WebSocket `KlineData` includes Binance `is_closed` (`x`), but persisted `KlineCsv` and `HEADER_KLINES` omit it. Current CSV therefore cannot prove final-candle status. Legacy CSV must not be used for canonical 1m→15m/1h aggregation. A versioned source change or explicit final-only output is a prerequisite.
- Proposed boundary: read-only T1 source files → isolated adapter-owned staging store → validated 15m/1h candidate windows/report. No T1 writes to T0; no T0 API/SQLite access or promotion path in this design.
- Defined proposed v1 header/manifest requirements, path/row validation, byte-offset cursor and atomic checkpoint/idempotency semantics, conflict/quarantine behavior, UTC 1m→15m/1h aggregation rules, provenance, error taxonomy and 24 deterministic fixture scenarios.
- Explicitly identified that buffered T1 `flush()` is not a durable-commit acknowledgement; collector-side durability/sealing semantics remain unproven and require a separate source contract.
- Status: **DESIGN COMPLETE / IMPLEMENTATION BLOCKED** pending T1 source schema change, source durability semantics and independent review. No code implementation, tests, workflow dispatch, VPS/runtime, T0/T2, strategy/AI/ledger/risk changes. T1 remains NOT ACTIVATED.
- GitHub Actions: NOT DISPATCHED; run ID NONE; artifact NONE. No test execution or runtime proof claimed.
- Next step: independent review of the design, then explicit approval before any T1 source-schema change. Adapter implementation and T0 promotion are separate future gates.
- Guardrails preserved: T0 remains independent/canonical; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders, OKX replacement/fallback, data deletion/archive/cleanup/vacuum/compaction/backup expiry or destructive tests.


## Latest completed work — T1 Contract v1 Adversarial Pre-Review (2026-11-09)

- Added review record: `docs/reviews/t1/T1_SOURCE_FILE_CONTRACT_V1_ADVERSARIAL_PREREVIEW_2026-11-09.md`.
- Review commit: `378ac2264fbb6be5a117798b639e16e434fb2212`.
- Review type is a same-session adversarial pre-review, **not an independent reviewer sign-off**. Do not report this as independent approval.
- Verdict: **REQUEST CHANGES — DESIGN NOT READY FOR IMPLEMENTATION**.
- Findings: (R1 Critical) persisted `market=futures` does not prove exact USD-M/USDT-M perpetual identity; (R2 Critical) no producer-owned durable completeness watermark/seal protocol; (R3 High) exact decimal preservation from WS payload through CSV bytes has not been traced/proven; (R4 High) manifest/file-generation lifecycle and atomic publication ordering are undefined; (R5 High) T1 `flush()` is not durable fsync evidence and producer crash/restart durability remains unproven; (R6 Medium) fixed 1m interval must be explicitly encoded/validated in v1 metadata; (R7 Medium) active-file reads need captured-length bounded scans and identity revalidation before cursor commit.
- Required next steps: revise source contract for product identity, interval, durable watermark/manifest lifecycle, decimal preservation, bounded read snapshot semantics and additional fixtures; then obtain a genuinely independent review from another reviewer/model or designated human.
- No source changes, adapter implementation, tests, workflow dispatch, VPS/runtime, T1 activation, T0/T2 or trading-system changes. No destructive data operations.
- GitHub Actions: NOT DISPATCHED; run ID NONE; artifact NONE.
- Guardrails remain: T0 independent/canonical, no T1 writes to T0, paper-only, `AI_EXECUTION_ENABLED=false`, no live orders, no OKX replacement/fallback, no data deletion/archive/cleanup/vacuum/compaction/backup expiry.


## Latest completed work — P1.1 T1 Source Contract v1.1 revision draft (2026-11-09)

- Added design revision: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md`.
- Design commit: `dd2d6eaaef2e0a1af4e2c74ea86b8d393f9f25d5`.
- Revision addresses pre-review findings R1–R7 at contract level:
  - Explicit Binance USD-M/perpetual product identity and trusted symbol metadata; no inference from generic `futures` or BTCUSDT spelling.
  - Producer-owned exclusive event-time watermark tied to receive-health state, committed byte offset and durable source publication. Before valid seal, missing rows remain PENDING; after valid contiguous seal, missing rows are WINDOW_GAP and still block aggregation.
  - Explicit interval=1m and is_closed schema requirements.
  - Single-writer generation, ACTIVE/SEALED/QUARANTINED lifecycle, data-sync-before-atomic-manifest-publication ordering, and non-destructive crash recovery requirements.
  - Decimal byte-preservation requirements and full producer call-path/golden-test gate.
  - Bounded active-file scans, captured committed offsets and pre-commit identity/manifest revalidation.
- Important limitation: this is a design revision only. Product metadata mapping, producer watermark/health implementation, exact decimal writer path, filesystem durability and adapter concurrency remain NOT VERIFIED. None of R1–R7 is implementation-resolved.
- Status: **P1.1 DESIGN REVISION DRAFTED / IMPLEMENTATION BLOCKED / INDEPENDENT REVIEW REQUIRED**.
- No T1 source code changes, adapter code, tests, workflow dispatch, VPS/runtime, T0/T2 or trading-system changes. No destructive data operations.
- GitHub Actions: NOT DISPATCHED; run ID NONE; artifact NONE.
- Guardrails: T0 remains independent/canonical; no T1 writes to T0; no OKX fallback; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no deletion/archive/cleanup/vacuum/compaction/backup expiry.
- Next step: static consistency review of v1.1 against the actual T1 source and existing v1 design, with explicit traceability of the kline conversion/writer path. Then obtain a genuinely separate review; no implementation before separate approval.


## P1.1 source trace addendum — confirmed T1 kline decimal-loss defect (2026-11-09)

- Read-only source trace recorded at `docs/reviews/t1/T1_KLINE_PRODUCER_CALL_PATH_TRACE_2026-11-09.md`.
- Trace commit: `df4406d08fb16010f78a2bef3f9748582cca82be`.
- Reviewed T1 source SHA: `6e20fe94f3ad64cc450e73def80a167fe371e49e`.
- Critical confirmed defect: `src/utils/csv_writer.rs::write_kline` parses every kline decimal field as f64, formats to 12 fractional digits, and uses `unwrap_or(0.0)` on parse failure. Thus current CSV serialization is lossy and malformed numeric input may silently become zero. Exact decimal provenance cannot be reconstructed downstream. R3 is BLOCKED pending producer-only correction and regression tests.
- Finality clarification: `message_handler.rs::process_kline` drops all `is_closed=false` events before CSV writing; persisted klines are intended to be final-only. But CSV/model header does not declare final-only semantics or persist the flag. v1 must explicitly declare a versioned FINAL_ONLY mode and prove it with tests, or persist `is_closed=true`.
- Product metadata refinement: inspected ExchangeInfoSymbol model exposes symbol/status/base_asset/quote_asset/underlying_type/contract_type; discovery filters TRADING, PERPETUAL, excludes PREMARKET and requires quote_asset=USDT. The inspected model does not expose margin_asset; do not require it without another verified source.
- No source edits, tests, workflow dispatch, VPS/runtime or T0/T2 changes. No data operations.
- Current status: **P1.1 DESIGN DRAFT / R3 CONFIRMED BLOCKER / IMPLEMENTATION NOT AUTHORIZED / INDEPENDENT REVIEW REQUIRED**.
- Next step: revise v1.1 design to require lossless raw decimal serialization and explicit final-only source semantics; then perform consistency review and obtain separate independent review. Any source code fix requires separate explicit approval.


### P1.1 v1.1 design amended with producer trace findings

- Updated design commit: `80e5a54940793f1a8ebbd3a1296ce3d7c635f161`.
- Updated design blob SHA: `b7bdaccda1c3519ab0d899ee907f5e04f0912e6e`.
- The v1.1 design now explicitly records the confirmed f64/12-decimal/unwrap_or(0.0) serialization defect and requires byte-preserving raw decimal output plus malformed-value rejection.
- It also clarifies that the current producer filters provisional kline events; v1 must explicitly declare FINAL_ONLY + interval=1m in versioned metadata with regression tests, or persist is_closed=true on each row.
- This does not resolve the defect. R3 remains BLOCKED; source implementation is not authorized.


## Latest completed work — P1.2 T1 Contract v1.1 static consistency review (2026-11-09)

- Updated v1.1 design: docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md.
- Design revision commit: d83e6555556e5e6482015df93c408a3669fe8120; blob SHA: 746de0920e8a79eaa79dc196b2489f198edaf977.
- Consistency review: docs/reviews/t1/P1_2_T1_CONTRACT_V1_1_STATIC_CONSISTENCY_REVIEW_2026-11-09.md.
- Review commit: 1add1d325c4ef89daf9f13d71430e74cd73b20ad.
- Review is same-session static consistency review, not an independent reviewer sign-off.
- P12-01 PASS: design correctly records confirmed producer decimal-loss defect (f64, 12-decimal formatting, parse failure to 0.0); requires lossless raw decimal serialization and malformed-value rejection.
- P12-02 PASS: v1 source mode is now coherent: versioned output_mode=FINAL_ONLY + interval=1m; per-row is_closed is not required for this first mode; provisional-event filtering must be regression-tested. Existing unversioned CSV is not retroactively trusted.
- P12-03 BLOCKER: design recognizes WebSocket health alone cannot prove no final candle was missed and introduces RECONCILED_COMPLETE, but the producer-owned authoritative reconciliation procedure/evidence contract is not defined. Must specify source, ranges/boundaries, delayed/unavailable/conflicting responses, evidence binding to generation/manifest, late corrections and deterministic fixtures. Until then watermark remains withheld; no aggregate/promotion.
- P12-04 HIGH: FINAL_ONLY manifest declaration and producer regression tests do not yet exist.
- P12-05 HIGH: target filesystem/provider durability and crash recovery remain unverified.
- Status: P1.2 STATIC CONSISTENCY REVIEW PARTIAL / RECONCILIATION PROOF BLOCKED / INDEPENDENT REVIEW PENDING / IMPLEMENTATION NOT AUTHORIZED.
- No T1 source edits, adapter implementation, tests, Actions dispatch, VPS/runtime, T0/T2 or trading-system changes. No destructive data operations.
- GitHub Actions: NOT DISPATCHED; run ID NONE; artifact NONE.
- Guardrails: T0 independent/canonical; no T1 writes to T0; paper-only; AI_EXECUTION_ENABLED=false; no live orders; no OKX fallback/replacement; no deletion/archive/cleanup/vacuum/compaction/backup expiry.
- Next step: revise v1.1 to define the producer-owned authoritative final-candle reconciliation protocol and manifest evidence schema; then request a genuinely independent review. No implementation until separate explicit approval.


### P1.2 reconciliation-source addendum

- Inspected pinned T1 source tree and src/rest/client.rs at SHA 6e20fe94f3ad64cc450e73def80a167fe371e49e. Existing REST client exposes mark-price, index-price and premium-index klines, but no standard trade-kline endpoint; T1 currently has no implemented source for the proposed completeness reconciliation.
- Candidate identified from official Binance USDⓈ-M documentation: GET /fapi/v1/klines, symbol BTCUSDT, interval 1m. Official references: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Kline-Candlestick-Data and https://developers.binance.info/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data.
- v1.1 design expanded with reconciliation transaction, raw response/digest evidence, WS-vs-REST conflict handling, bounded retries, generation/manifest binding, late correction quarantine and C46–C54 fixtures.
- Design update commit: 88d08819dc253e50eaf4ea8ccac69ea6acfa4df2; blob SHA: 21c85a7867f3bcca1475353e89cacd8297f55d1a.
- Source addendum: docs/reviews/t1/P1_2_BINANCE_REST_KLINE_RECONCILIATION_SOURCE_ADDENDUM_2026-11-09.md; commit 5dced81d20bb4e795fd2742822a0c66bc0424f4d.
- Remaining critical unknowns: REST start/end boundary semantics, no-trade-minute omission semantics, candle finality and historical revisions, maintenance/symbol-state behavior, and gap-free pagination. If no-trade minutes may be omitted without authoritative distinction, REST absence cannot prove either a data gap or no-trade minute. No watermark may advance until these are verified.
- Status: CANDIDATE SOURCE IDENTIFIED / COMPLETENESS ORACLE NOT VERIFIED / IMPLEMENTATION NOT AUTHORIZED / INDEPENDENT REVIEW PENDING.
- No REST endpoint called; no T1 code, tests, Actions workflow, VPS/runtime, T0/T2 or trading logic changed. No destructive data operations.


## Latest completed work — P1.3 fail-closed REST reconciliation acceptance profile (2026-11-09)

- Read current handoff and T1 Contract v1.1 before continuing. Active branch remains feature/t0-centralized-data-feeder-p1-20261101.
- Reviewed official Binance USDⓈ-M Kline documentation: GET /fapi/v1/klines; open-time identity; optional startTime/endTime; documented maximum limit 1500; response includes close time and decimal-string fields. Sources: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Kline-Candlestick-Data and https://developers.binance.info/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data.
- Documentation does not establish exact start/end inclusion semantics, whether no-trade minutes are emitted, formal candle finality/immutability, historical correction behavior or complete pagination proof. Do not infer these properties.
- Updated design section 15 with conservative acceptance profile: exact one REST row for every expected minute plus verified boundaries, pagination, finality, source comparison and durable manifest-bound evidence. Any missing minute or empty response is SOURCE_HEALTH_UNKNOWN, not no-trade and not a confirmed gap; no watermark or aggregate. No synthetic zero-volume candle/interpolation/carry-forward. Post-seal mismatch creates immutable correction event/quarantine.
- Design commit: 0e2cbec07b1289950a7aa7ec1b99ef0ec7f6302c; blob SHA: 1befbcbb9f9a1a489e2eec1fce43773bfb71cd04.
- P1.3 record: docs/reviews/t1/P1_3_FAIL_CLOSED_REST_RECONCILIATION_ACCEPTANCE_PROFILE_2026-11-09.md; commit 975cbef397619b36702b1aeafb0030251e54df12.
- Added deterministic contract fixtures C55–C62 for exact expected coverage, missing minute, duplicate page overlap, uncertain boundaries, incomplete pagination, unproven finality, post-seal correction and empty response.
- Status: P1.3 DESIGN PROFILE RECORDED / REST COMPLETENESS ORACLE NOT VERIFIED / INDEPENDENT REVIEW PENDING / IMPLEMENTATION NOT AUTHORIZED.
- This is same-session design work, not independent sign-off. No REST endpoint called; no T1 source, adapter, tests, CI workflow, VPS/runtime, T0/T2 or trading-system changes. No destructive data operations.
- GitHub Actions: NOT DISPATCHED; run ID NONE; artifact NONE.
- Guardrails: T0 independent/canonical; no T1 writes to T0; no T1 activation; paper-only; AI_EXECUTION_ENABLED=false; no live orders; no OKX fallback/replacement; no deletion/archive/cleanup/vacuum/compaction/backup expiry.
- Next step: independent review of P1.3 against the official API contract and pinned T1 producer source. If independent reviewer access is unavailable, keep status pending and do not label this work independent. Implementation requires a separate explicit approval.


## P1.4 — Independent adversarial review request (2026-11-09)

- Re-read current handoff and T1 Contract v1.1 before continuing. Branch: feature/t0-centralized-data-feeder-p1-20261101.
- Created GitHub issue #138 requesting an independent reviewer for Contract v1.1/P1.3: https://github.com/kenznguyen/btcusdt-telegram-signals2/issues/138. Issue is OPEN; no reviewer assigned and no review submitted.
- Review request record: docs/reviews/t1/P1_4_INDEPENDENT_ADVERSARIAL_REVIEW_REQUEST_2026-11-09.md; commit d5445b8653d95f5b822cf18ae2e0fb8d613fc4a5.
- Exact target: design at P1.3 commit 0e2cbec07b1289950a7aa7ec1b99ef0ec7f6302c and pinned T1 source SHA 6e20fe94f3ad64cc450e73def80a167fe371e49e.
- Review scope asks about watermark false-PASS, no-trade minute semantics, REST boundary/pagination, finality/corrections, shared WS/REST blind spots, decimal preservation, product identity, manifest/filesystem durability and bounded reads. Required output: reviewer identity, SHA-pinned evidence, severity-ranked findings and PASS/REQUEST CHANGES/BLOCKED verdict.
- Independence gate remains PENDING. Issue creation is not a review and does not constitute independent sign-off.
- No source code, adapter, tests, Actions, VPS/runtime, T0/T2, strategy or trading changes. No data deletion or destructive operation. No REST call.
- GitHub Actions: NOT DISPATCHED; run ID NONE; artifact NONE.
- Status: P1.4 REVIEW REQUEST OPEN / INDEPENDENT REVIEW NOT YET RECEIVED / COMPLETENESS ORACLE NOT VERIFIED / IMPLEMENTATION NOT AUTHORIZED / T1 ACTIVATION NOT AUTHORIZED.
- Guardrails: T0 independent/canonical; no T1 writes to T0; paper-only; AI_EXECUTION_ENABLED=false; no live orders; no OKX fallback/replacement; no deletion/archive/cleanup/vacuum/compaction/backup expiry.
- Next step: obtain an independent reviewer response on issue #138, then assess findings against exact SHAs. Do not self-certify independence or implement until separately approved.


## Latest completed work — P1.4 same-session self-review (2026-11-09)

- User requested a self-review of T1 Source Contract v1.1 / P1.3.
- Review record: `docs/reviews/t1/P1_4_SELF_REVIEW_T1_SOURCE_CONTRACT_V1_1_AND_P1_3_2026-11-09.md`.
- Review commit: `65d9bcbee55a3ac9690cc4bd7ffce1ffdd36b5c8`.
- Review verdict: REQUEST CHANGES — design is conservative but not implementation-ready.
- Findings: F01 CRITICAL — no accepted completeness oracle; F02 HIGH — REST-only recovery/source provenance underspecified; F03 HIGH — receive-path failure signals and durable health events underspecified; F04 HIGH — manifest rollback/authenticity threat model incomplete; F05 HIGH — confirmed f64/12-decimal/parse-to-zero producer defect; F06 MEDIUM — FINAL_ONLY is not immutable-finality proof; F07 MEDIUM — durability protocol is design only, target filesystem unverified; F08 MEDIUM — C01–C62 are planned fixtures, not executed tests.
- Positive controls: strict fail-closed missing-minute handling, no synthetic/no-trade inference, REST remains candidate only, post-seal correction quarantine, T0 independence and no-T0-write boundary retained.
- This is explicitly a same-session self-review and does NOT satisfy independent review. Issue #138 remains OPEN with no reviewer/comments at last check.
- Status: SELF-REVIEW COMPLETE / REQUEST CHANGES / INDEPENDENT REVIEW PENDING / COMPLETENESS ORACLE NOT VERIFIED / IMPLEMENTATION NOT AUTHORIZED / T1 ACTIVATION NOT AUTHORIZED.
- Review only. No tests, REST request, source edits, adapter implementation, Actions dispatch, VPS/runtime, T0/T2 or trading changes. No data deletion or destructive operation.
- GitHub Actions: NOT DISPATCHED; run ID NONE; artifact NONE.
- Next step: address F02–F04 as documentation-only clarifications, preserve F01/F05/F07 blockers, then request a genuinely independent review. Any source implementation requires separate explicit approval.


## Latest completed work — P1.5 documentation clarifications for F02/F03/F04 (2026-11-09)

- Re-read current handoff, P1.4 self-review and T1 Source Contract v1.1 before continuing. Existing branch retained: `feature/t0-centralized-data-feeder-p1-20261101`.
- Updated design: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md`.
- Design commit: `d5865355bdf941aab5978480b568767988d01d6c`; design blob SHA: `fccd57ef184b9bf2092140e5d323a90348c348cc`.
- P1.5 record: `docs/reviews/t1/P1_5_DOCUMENTATION_CLARIFICATIONS_F02_F03_F04_2026-11-09.md`; commit: `6df3a24a35af845ebefc48824b506c82c840388b`.
- F02 clarified: REST-only row with no WS counterpart is RECONCILIATION_SOURCE_DIVERGENCE, not agreement. Current contract forbids inserting it into a WS-derived generation or advancing watermark. A mixed-source mode requires a new versioned contract and separate review/approval.
- F03 clarified: explicit producer health events, sticky invalidation, failure ordering and unclean-shutdown uncertainty are required. Added planned negative fixtures C63–C71. Actual producer instrumentation remains NOT IMPLEMENTED/NOT VERIFIED.
- F04 clarified: current adjacent manifest/prefix digests cover accidental corruption/inconsistency only. No claim of adversarial tamper/rollback protection. Authenticated manifests, separated key custody and independent monotonic anchor require a separately reviewed design. Added planned fixtures C72–C76.
- Disposition: F02/F03/F04 clarified at design level only. F01 remains CRITICAL (REST completeness oracle not accepted); F05 remains HIGH (confirmed decimal-loss defect); F07 remains an unverified target-filesystem durability blocker.
- Status: P1.5 DOCUMENTATION UPDATE COMPLETE / DESIGN NOT READY FOR IMPLEMENTATION / INDEPENDENT REVIEW PENDING / COMPLETENESS ORACLE NOT VERIFIED / IMPLEMENTATION NOT AUTHORIZED / T1 ACTIVATION NOT AUTHORIZED.
- Verification: GitHub content writes only; no executable tests, REST request, Actions dispatch, VPS/runtime, source edit, T0/T2 or trading change. No data deletion or destructive operation.
- GitHub Actions: NOT DISPATCHED; run ID NONE; artifact NONE.
- Next step: perform a consistency review of P1.5 clauses against the existing v1.1/P1.3 rules, then request independent review against the updated design SHA. Do not self-label as independent. Implementation still requires separate explicit approval.
- Guardrails retained: T0 independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no deletion/archive/cleanup/vacuum/compaction/backup expiry.


### P1.5.1 taxonomy and consistency amendment

- Added `RECONCILIATION_SOURCE_DIVERGENCE` and `SOURCE_HEALTH_INVALIDATED` to the contract status taxonomy so F02/F03 rules have explicit outcomes.
- Final design commit: `630b118fc9f8c1d9d6e97253881dc51be42bcde5`; final design blob SHA: `42d0238edc6baa5bc8990ba27022b3db7c54772b`.
- Final P1.5 record commit: `5bbf73029c4100cf0f7c3e036b36db2d8276d847`; record blob SHA: `4663ac7d86a5c16d8ae3483ed6a34f0a77d2652c`.
- Same-session consistency check: F02 does not weaken P1.3 missing-minute handling; F03 invalidation prevents P1.3 seal preconditions from passing until resolved; F04 narrows the manifest security claim without changing completeness rules. No contradiction found in reviewed clauses. This is not independent review.
- Final status: P1.5 DOCUMENTATION CLARIFICATIONS COMPLETE / SAME-SESSION CONSISTENCY CHECK PARTIAL-PASS / DESIGN NOT READY FOR IMPLEMENTATION / INDEPENDENT REVIEW PENDING / F01, F05, F07 BLOCKED.


## Latest completed work — P1.6 T1 contract cross-document consistency review (2026-11-09)

- Re-read the current handoff and cross-checked original v1, current v1.1, P1.3, P1.4 and P1.5 documents against pinned T1 source SHA `6e20fe94f3ad64cc450e73def80a167fe371e49e`.
- Review: `docs/reviews/t1/P1_6_CONTRACT_CROSS_DOCUMENT_CONSISTENCY_REVIEW_2026-11-09.md`.
- Review commit: `2ce332b910a557c4afcc4eaa870e4793cb5fc5ab`.
- Findings: P1.6-F01 HIGH — original v1 document retains per-row `is_closed` schema/finality wording superseded by v1.1 FINAL_ONLY mode, but is not marked superseded; P1.6-F02 MEDIUM — manifest `GAP_DETECTED` lacks source-specific evidence semantics and could be confused with REST-missing/unknown; P1.6-F03 HIGH — inability to durably persist a health event (e.g. fsync/disk-full) needs an explicit immediate sticky invalidation and restart/quarantine rule.
- Cross-document PASS: REST remains candidate-only; missing REST minute remains SOURCE_HEALTH_UNKNOWN; no-trade inference/synthetic candles prohibited; REST-only rows are divergence and cannot enter WS generation; mismatches quarantine; sticky invalidation retained; manifest checksum claim limited to accidental corruption; decimal-loss defect and target-filesystem durability remain blockers; T0 remains independent.
- Verdict: PARTIAL — core fail-closed principles are consistent, but document set is not yet one unambiguous implementation contract. REQUEST CHANGES before readiness assessment.
- Review is same-session static review, not independent sign-off. Issue #138 remains the separate independent-review gate.
- Status: P1.6 REVIEW RECORDED / P1.6-F01/F02/F03 OPEN / REST COMPLETENESS ORACLE NOT VERIFIED / IMPLEMENTATION NOT AUTHORIZED / T1 ACTIVATION NOT AUTHORIZED.
- Verification: documentation writes only. Tests NOT RUN; GitHub Actions NOT DISPATCHED (run ID NONE; artifact NONE); no REST request, source edit, adapter implementation, VPS/runtime, T0/T2 or trading changes. No data deletion or destructive operation.
- Next step: P1.7 documentation-only resolution of the three findings; mark original v1 finality/schema clauses superseded, define evidence semantics for `GAP_DETECTED`, and specify health-event persistence failure behavior. Preserve F01/F05/F07 blockers and request independent review only after the normative document set is reconciled.
- Guardrails: T0 independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no deletion/archive/cleanup/vacuum/compaction/backup expiry.


## Latest T1 contract work — P1.7 (2026-11-09)

- P1.7 documentation-only clarification and same-session static check recorded in `docs/reviews/t1/P1_7_CONTRACT_CLARIFICATIONS_AND_STATIC_REVIEW_2026-11-09.md`.
- Review commit: `8cfa5ca526fcc2fcd7ed436119732f65ce7d51e6`.
- P1.7 closes the three P1.6 document findings at design level:
  - Original v1 source-file design is now explicitly archival/non-normative for this producer scope; v1.1 is sole normative contract. Per-row `is_closed` and proposed v1 schema clauses are superseded/do-not-implement. Current FINAL_ONLY mode requires versioned manifest declaration, interval=1m and producer regression evidence; legacy/unversioned inputs remain ineligible.
  - `GAP_DETECTED` is reserved and not assignable under current profile. Missing/empty REST, absent WS rows, no-trade inference, uncertain pagination/boundaries, transport/queue/parser/writer errors and unsealed windows cannot set it. A future authoritative gap profile requires separate versioning, approval and independent review.
  - Failure to durably persist health evidence immediately causes sticky in-process invalidation and stops offset/manifest/watermark/seal advancement. Restart without verifiable clean-close/checkpoint state or with missing/corrupt health journal requires quarantine. No independent durable health channel is assumed; limitation is explicit.
- Updated archival v1 final blob SHA: `c64d6da7b16e608ef5ccebafabce03e51960cfcc`.
- Updated normative v1.1 blob SHA: `fd640ab36efed6975f1dfaaed750f9d0ae7f708c`.
- P1.7 review verdict: DOCUMENTATION CLARIFICATIONS COMPLETE / SAME-SESSION STATIC CHECK PARTIAL-PASS. Not independent sign-off and not implementation readiness.
- Planned negative fixtures C77–C81 added; NOT implemented or executed.
- Unchanged blockers: F01 CRITICAL (REST completeness oracle not accepted); F05 HIGH (producer decimal f64/12-decimal/parse-to-zero defect confirmed); F07 HIGH/operational (target filesystem/provider durability unverified). Independent review issue #138 remains pending.
- Tests NOT RUN; GitHub Actions NOT DISPATCHED (run ID NONE; artifact NONE); REST NOT CALLED; T1 source/adapter NOT MODIFIED/IMPLEMENTED; T1 activation NOT AUTHORIZED.
- No T0/T2, strategy/AI/ledger/risk changes; T0 remains independent/canonical; paper-only, `AI_EXECUTION_ENABLED=false`, no live orders, no OKX fallback/replacement. No deletion or destructive operation.
- Next step: independent adversarial review against exact v1.1 blob `fd640ab36efed6975f1dfaaed750f9d0ae7f708c` and the archival v1 supersession change. Maintain implementation block until independent review and F01/F05/F07 gates are resolved.


## Latest work — P1.8 independent review request refreshed for final contract (2026-11-09)

- Re-read this handoff before continuing. GitHub issue #138 was OPEN with no comments and still targeted the pre-P1.7 design baseline.
- Updated issue #138 title to `P1.8 — Independent adversarial review of final T1 Source Contract v1.1`, keeping it OPEN and replacing the review target with exact final document SHAs. Issue URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/issues/138.
- Exact normative v1.1 blob SHA: `fd640ab36efed6975f1dfaaed750f9d0ae7f708c`.
- Exact archival v1 blob SHA: `c64d6da7b16e608ef5ccebafabce03e51960cfcc`.
- Pinned producer SHA remains `6e20fe94f3ad64cc450e73def80a167fe371e49e`.
- Required reviewer output now explicitly includes independent reviewer identity, exact SHA linkage, severity-ranked findings, evidence/reproduction rationale and PASS / REQUEST CHANGES / BLOCKED verdict. Questions include watermark false-PASS, REST completeness/no-trade/boundary/pagination/finality, REST/WS common blind spots, FINAL_ONLY, GAP_DETECTED, health-journal persistence failure, decimal loss, product identity, manifest/cursor ordering, filesystem durability, fixtures and archival-v1 precedence.
- Request record: `docs/reviews/t1/P1_8_INDEPENDENT_REVIEW_REQUEST_FINAL_CONTRACT_2026-11-09.md`; commit `9dd38e5c80313b1fe260064a9f0ebeda5998f694`.
- Status: REQUEST UPDATED / ISSUE OPEN / INDEPENDENT REVIEW PENDING. No reviewer response or independent sign-off is claimed.
- Unchanged blockers: F01 CRITICAL (REST completeness oracle not accepted); F05 HIGH (producer f64/12-decimal/parse-to-zero defect); F07 HIGH/operational (target filesystem durability unverified). C77–C81 remain planned only.
- Verification: GitHub issue/documentation updates only. No tests, REST request, Actions dispatch, source edit, adapter implementation, VPS/runtime, T1 activation, T0/T2 or trading changes. No deletion/destructive operation.
- Next step: wait for an independent reviewer to post a written review against the exact SHAs. If no reviewer is available, do not relabel self-review as independent; implementation remains blocked pending the review and F01/F05/F07 evidence gates.
- Guardrails: T0 independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no deletion/archive/cleanup/vacuum/compaction/backup expiry.


## Latest work — P1.9 same-session adversarial self-review of final T1 contract (2026-11-09)

- Re-read the handoff and reviewed the exact normative v1.1 contract, archival v1, P1.3, P1.7, P1.8 request and pinned T1 source files. This is explicitly a same-session self-review, NOT independent review.
- Review record: `docs/reviews/t1/P1_9_SELF_REVIEW_FINAL_T1_CONTRACT_2026-11-09.md`.
- Review commit: `75ecdf3758f5ba8f49d09fb1297814412afc64b7`.
- Exact review inputs:
  - v1.1 contract blob `fd640ab36efed6975f1dfaaed750f9d0ae7f708c`
  - archival v1 blob `c64d6da7b16e608ef5ccebafabce03e51960cfcc`
  - P1.3 blob `a99cf2e21edc4519a2f2d0833c6cdf1e6d768599`
  - P1.7 review blob `a83bb0246b9480f593516dd410782fc619122127`
  - pinned T1 source `6e20fe94f3ad64cc450e73def80a167fe371e49e`
  - source blobs: csv_writer `2c4538dcef7dfa758a854292031239c15f7c282b`; message_handler `7d7f221fbf4b31470049baea55584645352f61b7`; models `993419725268d1308645e3a37c15e9779a9e92cc`; rest client `3f2068a07fbf6a6e348fb227274f7b0d54703e8d`; symbol discovery `34e453cbb96d5964d1f58e204bbfbe147041ced6`; constants `0bf50b5fe02f4f196b38481cde6ecab9e2adb941`.
- Verdict: REQUEST CHANGES — DESIGN NOT READY FOR IMPLEMENTATION.
- New findings:
  - F01 CRITICAL: manifest rename becomes visible before directory fsync; no reader/writer barrier prevents consumers accepting a not-yet-durable watermark. Specify enforceable publication visibility/commit protocol and tests.
  - F02 HIGH: single-writer ownership and generation fencing lack a concrete stale-owner/takeover protocol.
  - F03 HIGH: WINDOW_GAP has no reachable assignment path under the current rules requiring complete REST rows and treating source asymmetry/missing REST as UNKNOWN/divergence; explicitly disable it or add a separately approved evidence profile.
  - F04 HIGH: FINAL_ONLY proof does not yet require explicit producer interval validation; pinned handler filters provisional events but does not validate `interval == 1m` or persist interval/close_time.
  - F05 HIGH: pinned symbol discovery has hardcoded BTCUSDT/DOGEUSDT exceptions that re-add symbols based on TRADING status without rechecking PERPETUAL and quote_asset=USDT; manifest producer must independently validate exact metadata.
  - F06 MEDIUM: manifest machine-readable schema, canonicalization, file-to-manifest binding, path/symlink and duplicate-manifest rules underspecified.
  - F07 MEDIUM: C46 wording may be read as accepting coverage/equality before all P1.3 identity/boundary/pagination/finality/durability gates pass.
- Existing blockers re-confirmed: F01 REST completeness oracle not accepted; F05 producer f64/12-decimal/parse-to-zero defect confirmed; F07 target filesystem/provider durability unverified. Review record uses P1.9 finding labels locally; these do not replace the historical F01/F05/F07 blocker labels.
- Positive checks: archival v1 is clearly non-normative; v1.1 is normative; missing REST stays UNKNOWN; no-trade inference/synthetic candles prohibited; REST-only rows not silently inserted; health invalidation sticky; manifest security claim bounded to accidental corruption; T0 independent.
- Verification: read-only GitHub inspection only. Tests NOT RUN; REST NOT CALLED; Actions NOT DISPATCHED (run ID NONE; artifact NONE); no source edit, adapter, VPS/runtime, T1 activation, T0/T2 or trading change. No deletion/destructive operation.
- Issue #138 remains the independent-review gate. This self-review does not satisfy independence.
- Next step: documentation-only correction of P1.9 findings, beginning with publication visibility ordering; then independent review against new exact SHAs. Implementation and T1 activation remain NOT AUTHORIZED.
- Guardrails retained: paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no T0 write path; no deletion/archive/cleanup/vacuum/compaction/backup expiry.


## 2026-11-09 — Strategic decision D-2026-11-09: Operational First, Empirical Validation

- User-approved decision recorded at `docs/decisions/D-2026-11-09-OPERATIONAL-FIRST-EMPIRICAL-VALIDATION.md`.
- Decision: prioritize minimum reliable operation before additional strategy optimization/feature expansion; then evaluate Strategy Core and independent AI Strategy using real market data with paper-only simulated execution.
- Required order: T0 data integrity → T1 collection reliability → T2 Dual-Strategy Intelligence → integrated operations/recovery/observability → paper baseline capture → empirical evaluation → controlled optimization.
- Strategy boundary: preserve RSI + ADX + Smart DCA Core; preserve independent AI LONG/SHORT signal generation and separate attribution/ledgers; both must pass the shared Risk Engine and Kill Switch.
- Acceptance requires traceable data/model/config/signal/execution assumptions; record rejected as well as accepted signals; evaluate Core and AI separately and measure AI incremental risk-adjusted contribution after shared risk admission; separate technical reliability from trading performance; avoid strategy tuning during baseline collection except safety/correctness/data-integrity fixes.
- No calendar deadline substitutes for sufficient observations and market-regime coverage.
- Safety unchanged: paper/signal-only; `ai_execution_enabled=false`; no live orders; T0 remains an independent canonical data asset. This decision does not authorize production activation, VPS/runtime changes, destructive data operations, or any previously blocked work.
- Existing P1.8/P1.9 findings, independent-review gates, exact-SHA evidence requirements and T0/T1 activation restrictions remain binding.
- Verification: documentation-only. Tests NOT RUN; GitHub Actions NOT DISPATCHED (run ID NONE); artifact NONE. No source, workflow, runtime, database, Feeder, exchange, market-data sync, ledger or trading state changed.
- Current work continues on existing branch `feature/t0-centralized-data-feeder-p1-20261101`; no parallel branch or PR created for this decision.
- Next step: continue closing current T0/T1 contract correctness findings and obtain independent review on exact final SHA before implementation/activation gates are reconsidered.


## Latest completed work — P1.10 T1 publication/fencing/gap/manifest contract correction (2026-11-09)

- User explicitly approved automatic continuation for: publication visibility/durability ordering; writer fencing/generation ownership; WINDOW_GAP semantics; FINAL_ONLY/interval/product identity; manifest/fixture normalization; and independent review request on the new SHA.
- Scope executed in this unit: documentation/contract/evidence only on the existing branch `feature/t0-centralized-data-feeder-p1-20261101`. No source implementation, test execution, REST request, Actions dispatch or runtime work.
- Normative design: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md`.
- Final design blob SHA: `32cf231227c52590ad1365473c6c742ab7dbc64a`.
- Design update commits included: `d315615407931f2d34abe51c0a9ebcf268beb0f7`, `7bd35b1d192a3e397a28853edbafbdc788db97ff`, `4576f810f561de74a993505ffa280e7039e9d011`, `a20652d924db89498061c1bcb06c590e6be1c5f6`, `c7d9f781920c05ef48ec45c0420adcbbc4059ef8`, and final design commit `1cf41fdaff08e72bc71bcbafe47fe882f621acc2`.
- Publication protocol: manifest rename is not a commit point. The writer must fsync the containing directory, then publish an immutable commit receipt binding exact manifest digest, generation, publication sequence, file identity, committed offset/count, prefix digest and watermark. Readers require a shared lock and matching receipt; a visible manifest without one is PREPARED/UNCOMMITTED. Missing receipt is a safe false-negative. Receipt visibility only proves the prior directory barrier was completed; it does not prove source completeness or clean shutdown.
- Writer fencing: stable kernel advisory lock file; writers exclusive, readers shared; lock inode never replaced/unlinked; no PID/age-based stealing; paused writer retains lock; process crash releases lock. Durable generation counter transaction completes before append. Unsupported/unverifiable lock or filesystem semantics fail closed.
- WINDOW_GAP and GAP_DETECTED are both reserved/unassignable under the current v1.1 profile. Missing REST remains UNKNOWN; source asymmetry remains divergence/unknown. Future gap classification requires a separately versioned authoritative profile, independent review and explicit approval.
- FINAL_ONLY now requires exact configured USD-M subscription and per-event BTCUSDT/1m validation; provisional events are filtered; interval/symbol/stream mismatch rejects/invalidates generation. Hardcoded symbol exceptions cannot bypass TRADING/PERPETUAL/USDT quote-asset checks. Exact ExchangeInfo snapshot and symbol record evidence are bound.
- Manifest/receipt: strict UTF-8 JSON/JCS closed schema; fixed version identifiers; source_root_id; generation/publication sequence; ExchangeInfo evidence reference; strict file identity object; safe integer limits; path/no-follow/symlink/hard-link checks; receipt schema. C46 is conditional on every P1.3 gate. Planned fixture inventory extends to C99.
- P1.10 same-session static review: `docs/reviews/t1/P1_10_PUBLICATION_FENCING_MANIFEST_CONTRACT_REVIEW_2026-11-09.md`; commit `f0ff3bf564a077af196bc0620d6a32036ed4d6df`; blob `1abbb75e52df88b354191668ce2b276a322f4411`. It is not independent review.
- Independent review request: GitHub issue #138 updated to P1.11, OPEN: https://github.com/kenznguyen/btcusdt-telegram-signals2/issues/138. Exact target contract SHA `32cf231227c52590ad1365473c6c742ab7dbc64a`; archival v1 SHA `c64d6da7b16e608ef5ccebafabce03e51960cfcc`; pinned producer SHA `6e20fe94f3ad64cc450e73def80a167fe371e49e`.
- Request record: `docs/reviews/t1/P1_11_INDEPENDENT_REVIEW_REQUEST_REVISED_CONTRACT_2026-11-09.md`; commit `2f9e24235a26a136e4b940c8ffe646a997aa6b6d`.
- Status: P1.10 DOCUMENTATION CLARIFICATIONS COMPLETE / SAME-SESSION STATIC CONSISTENCY PASS AT CONTRACT LEVEL / INDEPENDENT REVIEW PENDING / IMPLEMENTATION NOT AUTHORIZED.
- Unchanged blockers: REST completeness oracle NOT ACCEPTED; decimal f64/12-decimal/parse-to-zero defect CONFIRMED and NOT FIXED; target filesystem/provider durability and advisory lock semantics NOT VERIFIED; producer interval/product identity implementation NOT VERIFIED; manifest/receipt/lock code NOT IMPLEMENTED; C01–C99 NOT EXECUTED.
- No GitHub Actions run or artifact is claimed. No T1 source edit, adapter implementation, test, REST, VPS/runtime, T1 activation, T0/T2, strategy/AI/ledger/risk/trading change. No deletion/archive/cleanup/vacuum/compaction/backup expiry/restore/destructive operation.
- Next step: wait for genuinely independent written review tied to the exact new SHAs. Do not self-certify independence. Implementation and T1 activation remain blocked until independent review and F01/F05/F07 evidence gates are resolved.
- Guardrails: T0 remains independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.


## 2026-11-09 — Conditional source change governance decision

- User requested evaluation of source-change authorization; conditional governance decision recorded in docs/decisions/D-2026-11-09-OPERATIONAL-FIRST-EMPIRICAL-VALIDATION.md.
- Decision status: APPROVED WITH CONDITIONS — CHANGE GOVERNANCE ONLY. This is not blanket authorization to edit arbitrary source, refactor architecture, expand features, tune strategies, deploy, or activate runtime services.
- Eligible candidate work: bounded, reproducible correctness/security defects; reliability, data-integrity, observability, recovery and resource-safety corrections; contract-conformance patches only after governing contract/review gates; documentation/evidence updates.
- Every source patch requires an explicit bounded work item and approval before editing; exact branch/baseline SHA; files/components and exclusions; regression test/TDD where applicable; small isolated patch; GitHub Actions verification; exact tested SHA, run ID/artifacts/logs; and review on the final SHA. Major/security/data-integrity/concurrency/persistence/cross-layer changes require genuinely independent review.
- Preserve the existing branch. Do not create parallel branch/PR unless separately approved. Do not weaken tests/gates to obtain PASS.
- Source/CI PASS does not authorize deployment, VPS, DB, Feeder, exchange, runtime, paper execution, or live trading.
- T1 implementation and activation remain NOT AUTHORIZED. P1.10 remains design/documentation only. Independent review is pending on contract SHA 32cf231227c52590ad1365473c6c742ab7dbc64a. REST completeness oracle NOT ACCEPTED; producer decimal f64/12-decimal/parse-to-zero defect CONFIRMED / NOT FIXED; target filesystem/provider durability and advisory-lock semantics NOT VERIFIED; implementation and fixtures NOT EXECUTED.
- No blanket T0 or T2 source implementation authorization. Each concrete item needs target layer, exact baseline SHA, scope, tests, review gates, and explicit approval.
- Explicit prohibitions remain: broad refactors/architecture replacement/feature expansion/strategy tuning; T0/T1/T2 runtime/VPS/DB/Feeder/exchange/deployment changes; data deletion/archive/retention/cleanup/vacuum/compaction/backup expiry/restore/fault injection/key destruction; live orders; enabling AI_EXECUTION_ENABLED; weakening T0 independence or adding T1 write path to T0.
- Verification/effect: documentation-only. Tests NOT RUN; GitHub Actions NOT DISPATCHED; workflow run NONE; artifact NONE. No source/runtime/VPS/DB/Feeder/exchange/ledger/strategy/trading state changed.
- Next step: prepare a bounded change request naming target layer/files and exact baseline SHA; wait for explicit approval before source edits. T1 remains blocked by independent-review and evidence gates.


## Latest completed work — P1.11 same-session self-review of revised T1 contract (2026-11-09)

- User requested a self-review of the revised T1 Source Contract v1.1.
- Review: `docs/reviews/t1/P1_11_SELF_REVIEW_REVISED_T1_CONTRACT_2026-11-09.md`.
- Review commit: `a0c4d22949140aa2fbba653eaaf3695dd649f1b5`.
- Review blob SHA: `08662369f1093658cdd42d56ede01a5b985e0f82`.
- Exact reviewed normative contract blob SHA: `32cf231227c52590ad1365473c6c742ab7dbc64a`.
- Review type: same-session adversarial self-review, NOT independent.
- Verdict: REQUEST CHANGES — contract has a critical false-PASS path and material publication-sequence, lock-topology, schema and immutable-receipt gaps.
- F01 CRITICAL: §4.2/§21.5 manifest schema still allows `source_health=RECONCILED_COMPLETE` with a merely retrievable `reconciliation_evidence_ref`, while P1.3 has not accepted any completeness oracle. Current v1.1 must reject this state; future enabling requires a new, versioned, independently reviewed evidence profile.
- F02 HIGH: publication_sequence monotonic allocation and crash/no-reuse recovery are not specified, unlike generation_sequence.
- F03 HIGH: advisory-lock topology is not bounded (single-host/local filesystem vs network/multi-host); lock API, initialization race and canonical lock-object identity are underspecified.
- F04 HIGH: manifest, receipt, generation-counter and ExchangeInfo evidence schemas are not fully machine-unambiguous; canonical UUID/time/path, exact types/enums and counter recovery need specification.
- F05 HIGH: ExchangeInfo evidence reference lacks immutable content-addressed storage/retrieval and exact raw-byte digest/canonicalization contract.
- F06 MEDIUM: immutable receipt publication needs atomic no-replace semantics and explicit handling of duplicate/orphan/unexpected receipt files.
- F07 HIGH: target filesystem durability remains unproven; process tests cannot establish host/power/provider durability.
- Existing blockers revalidated: REST completeness BLOCKED; producer f64/12-decimal/parse-to-zero defect BLOCKED; filesystem/provider durability NOT VERIFIED; producer implementation and C01–C99 NOT VERIFIED/NOT EXECUTED.
- No source changes, tests, Actions, REST calls, VPS/runtime, T1 activation, T0/T2 changes, trading, or destructive data operation.
- Independent review issue #138 remains separate and must be retargeted to a corrected SHA after these findings are resolved. Do not treat this self-review as independent approval.
- Next step: correct F01–F06 in the contract, add negative/crash/parser fixtures (planned only), perform a fresh static review, then update issue #138 with the exact corrected SHA for genuinely independent review.
- Guardrails unchanged: implementation NOT AUTHORIZED; T1 activation NOT AUTHORIZED; T0 independent/canonical; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.


## Latest completed work — P1.12 T1 contract corrections and independent-review retarget (2026-11-09)

- User explicitly approved automatic execution of the ordered documentation-only work: F01–F06 corrections, negative/crash fixture additions, self-review of the final SHA, and retargeting issue #138 for independent review.
- Work remained on existing branch `feature/t0-centralized-data-feeder-p1-20261101`; no parallel branch or PR created.
- Normative design: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md`.
- Final design update commit: `353f6b0ff11a379b53da6292682eefa09073f5f8`.
- Final design blob SHA: `4034d740c9694ef0d9da7d81cc1d1055a0175302`.
- P1.12 section 22.1 closes F01 at contract level: current v1.1 forbids `RECONCILED_COMPLETE` and `reconciliation_evidence_ref`; only UNKNOWN/INVALIDATED are accepted; no current completeness seal or canonical aggregation is permitted. A future completeness profile requires new versioning, independent review and explicit approval.
- Section 22.2 closes F02 at design level: durable per-generation publication counter, reserve-before-manifest, consumed sequence never reused, crash recovery and quarantine on ambiguous state.
- Section 22.3 closes F03 at design level: single Linux host + verified local POSIX filesystem only; Linux `flock(2)`, stable lock inode, no-follow opens, offline single-operator initialization; unsupported network/multi-host/overlay/provider filesystems fail closed.
- Sections 22.4 and 22.9 close F04 at documentation level: closed JCS schemas and exact encodings for manifest, receipt, generation counter, source-root initialization and ExchangeInfo evidence envelope; root/lock/file identity, owner/mode, paths, link-count and raw JSON parser constraints.
- Sections 22.5 and 22.9 close F05 at contract level: content-addressed raw ExchangeInfo response evidence, exact raw-byte digest, endpoint/request/response envelope, unique BTCUSDT raw symbol-record slice and fail-closed retrieval.
- Section 22.6 closes F06 at contract level: atomic `renameat2(RENAME_NOREPLACE)`, no overwrite fallback, commits-directory fsync, full receipt-directory validation and quarantine for collision/orphan/unexpected entries.
- Added planned deterministic negative/crash/parser/lock/evidence fixtures C100–C116. These remain NOT IMPLEMENTED / NOT EXECUTED.
- Same-session self-review: `docs/reviews/t1/P1_12_SELF_REVIEW_T1_CONTRACT_CORRECTIONS_2026-11-09.md`; commit `d56358aed26a42c0b90f65270ef5b3c20864540f`; blob SHA `402c10c899837bbcebd2545b24117837fba1ac75`.
- Self-review verdict: DOCUMENTATION-LEVEL PASS FOR F01–F06 CORRECTIONS / IMPLEMENTATION READINESS NOT ESTABLISHED / INDEPENDENT REVIEW REQUIRED. It is not independent.
- F07 remains NOT VERIFIED: actual target filesystem/mount/device/provider identity, flock, rename, fsync/directory-fsync and renameat2 semantics have not been tested. No host/power/provider crash test authorized or executed.
- Unchanged blockers: Binance REST completeness/no-trade/boundary/pagination/finality/correction semantics NOT ACCEPTED; pinned producer f64/12-decimal/parse-to-zero defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; manifest/receipt/counter/evidence store/adapter NOT IMPLEMENTED; C01–C116 NOT EXECUTED.
- GitHub issue #138 retargeted and remains OPEN: https://github.com/kenznguyen/btcusdt-telegram-signals2/issues/138. New title: `P1.12 — Independent adversarial review of corrected T1 Source Contract`. Exact target design blob SHA `4034d740c9694ef0d9da7d81cc1d1055a0175302`; latest design commit `353f6b0ff11a379b53da6292682eefa09073f5f8`. Issue requires genuinely independent reviewer, severity-ranked findings and explicit PASS / REQUEST CHANGES / BLOCKED. Latest readback: OPEN, 0 comments; no independent review has been received.
- No source implementation, test execution, GitHub Actions dispatch, Binance REST request, VPS/runtime, T1 activation, T0/T2, strategy/AI/ledger/risk/trading change. No data deletion/archive/cleanup/vacuum/compaction/backup expiry/restore/destructive operation. No workflow run or artifact is claimed.
- Status: P1.12 DOCUMENTATION CORRECTIONS COMPLETE / SAME-SESSION SELF-REVIEW PASS FOR F01–F06 AT CONTRACT LEVEL / F07 NOT VERIFIED / INDEPENDENT REVIEW PENDING / IMPLEMENTATION NOT AUTHORIZED / T1 ACTIVATION NOT AUTHORIZED.
- Guardrails unchanged: T0 remains independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.
- Next step: wait for genuinely independent written review on exact design blob SHA `4034d740c9694ef0d9da7d81cc1d1055a0175302`. Do not implement or activate T1 before independent review and separate approval/evidence gates.


## Latest completed work — P1.13 same-session adversarial self-review of P1.12 T1 contract (2026-11-09)

- Review: `docs/reviews/t1/P1_13_SELF_REVIEW_P1_12_T1_CONTRACT_2026-11-09.md`.
- Review commit: `20cf3a4b2a86e0c4d262a34166428c64ca9b581d`.
- Exact reviewed normative design blob SHA: `4034d740c9694ef0d9da7d81cc1d1055a0175302`.
- Review type: same-session static adversarial self-review; NOT independent.
- Verdict: REQUEST CHANGES — F04 is not closed because §22.4 defines a six-key source-root initialization record while §22.9 defines an eleven-key record, both using exact closed-schema language. Strict parser implementation cannot satisfy both definitions.
- F02 PARTIAL: C103 covers crash after receipt rename before commits-directory fsync, but recovery does not explicitly require a recovery fsync barrier and define the acceptance linearization point before treating a surviving receipt as committed.
- F01 PASS at documentation level: §22.1 forbids RECONCILED_COMPLETE and reconciliation_evidence_ref; watermark is non-authoritative observed progress only. No parser/adapter test exists.
- F03 PASS at contract level; actual target filesystem, mount/provider, flock, renameat2 and fsync semantics remain NOT VERIFIED.
- F05 PARTIAL: raw ExchangeInfo evidence binding is specified, but the exact evidence-envelope/header inventory should be normalized into one authoritative schema.
- F06 PASS at contract level; implementation and target primitive availability NOT VERIFIED.
- F07 remains NOT VERIFIED. Binance REST completeness semantics remain NOT ACCEPTED. Producer f64/12-decimal/parse-to-zero defect remains CONFIRMED / NOT FIXED. FINAL_ONLY/product identity implementation NOT VERIFIED. Manifest/receipt/counter/evidence store/adapter NOT IMPLEMENTED. C01–C116 NOT EXECUTED.
- This review supersedes P1.12 self-review's implementation-readiness assessment. P1.12 design changes remain present; implementation is still NOT AUTHORIZED.
- No source code, tests, Actions dispatch, REST, VPS/runtime, T0/T1/T2, strategy/AI/ledger/risk/trading changes, T1 activation, or destructive data operations. No workflow run or artifact is claimed.
- Issue #138 remains OPEN and targets the exact P1.12 design SHA; it still requires genuinely independent review. P1.13 is not independent and does not close the issue.
- Next step: correct F04 schema contradiction, clarify F02 recovery barrier/linearization, normalize F05 evidence-envelope schema, add negative/crash fixtures, then self-review the new exact SHA before independent review.
- Guardrails: T0 remains independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.


## Latest completed work — P1.14 T1 schema/recovery corrections, self-review and independent-review retarget (2026-11-09)

- User explicitly approved automatic execution of: F04 single initialization schema; F05 single authoritative ExchangeInfo evidence-envelope schema; F02 recovery fsync barrier/commit-acceptance linearization; negative/crash fixtures; self-review; issue #138 retarget.
- Work remained on existing branch `feature/t0-centralized-data-feeder-p1-20261101`. Documentation/evidence only.
- Normative design: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md`.
- Final design update commit: `5745248abed4fb02fa1a15688b1ba17771eaaa46`.
- Final design blob SHA: `59d8988a368a5bfffa94eacf7fbb8d769aea9b60`.
- F04: §22.4 now defers to §22.9; §22.9 is the sole authoritative eleven-key initialization-record schema; §22.10 expressly supersedes the former six-key inventory. C121–C123 cover missing/extra keys and identity/owner/mode mismatches.
- F05: §§22.5/22.9/22.10 establish one authoritative closed ExchangeInfo evidence-envelope schema and explicit lowercase response-header allowlist/absence semantics. C124 covers missing/unknown envelope keys and header handling.
- F02: §22.6.1 defines commit acceptance at successful commits-directory fsync after no-replace receipt installation, plus restart validation, commits/generation directory recovery fsync barriers, durable recovery checkpoint and fail-closed behavior. C117–C120 cover recovery barrier, fsync failure, crash before checkpoint and consumed sequence with missing receipt.
- Fixture inventory is now C01–C124. All are design scenarios only; NOT IMPLEMENTED / NOT EXECUTED.
- P1.14 same-session self-review: `docs/reviews/t1/P1_14_SELF_REVIEW_T1_CONTRACT_SCHEMA_RECOVERY_2026-11-09.md`; commit `744e9ec1c07cb2cb8f5f1db3b204f40ac52ba71e`; blob SHA `64ca44a5549ad51e66c9dc5d0e0dd4947e826552`.
- Self-review verdict: DOCUMENTATION-LEVEL PASS for requested F04/F05/F02 corrections and C117–C124 specification; IMPLEMENTATION READINESS NOT ESTABLISHED; F07 NOT VERIFIED; INDEPENDENT REVIEW REQUIRED. This is same-session, not independent.
- Issue #138 retargeted and remains OPEN: https://github.com/kenznguyen/btcusdt-telegram-signals2/issues/138. Title: `P1.14 — Independent adversarial review of corrected T1 Source Contract`. Exact target contract blob SHA `59d8988a368a5bfffa94eacf7fbb8d769aea9b60`; target commit `5745248abed4fb02fa1a15688b1ba17771eaaa46`. Latest readback: OPEN, 0 comments; no independent review received.
- Remaining blockers unchanged: F07 target filesystem/provider durability and flock/renameat2/fsync behavior NOT VERIFIED; Binance REST completeness/no-trade/boundary/pagination/finality/correction semantics NOT ACCEPTED; producer f64/12-decimal/parse-to-zero defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; manifest/receipt/counter/evidence store/adapter NOT IMPLEMENTED; C01–C124 NOT EXECUTED.
- No source code, tests, GitHub Actions dispatch, Binance REST, VPS/runtime, T1 activation, T0/T2, strategy/AI/ledger/risk/trading changes. No destructive data operations. No workflow run or artifact is claimed.
- Status: P1.14 DOCUMENTATION CORRECTIONS COMPLETE / SAME-SESSION SELF-REVIEW PASS AT CONTRACT LEVEL FOR F02/F04/F05 / F07 NOT VERIFIED / INDEPENDENT REVIEW PENDING / IMPLEMENTATION NOT AUTHORIZED / T1 ACTIVATION NOT AUTHORIZED.
- Guardrails unchanged: T0 remains independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.
- Next step: wait for genuinely independent written review on exact contract blob SHA `59d8988a368a5bfffa94eacf7fbb8d769aea9b60`. Do not implement or activate T1 before independent review and separate evidence/approval gates.


## Latest completed work — P1.15 follow-up adversarial self-review of P1.14 (2026-11-09)

- User requested a fresh self-review of P1.14.
- Review: `docs/reviews/t1/P1_15_SELF_REVIEW_P1_14_CHECKPOINT_AND_EVIDENCE_ID_2026-11-09.md`.
- Review commit: `bdc4d66e86e4fffeccb7338f9a34621de1d829ca`.
- Exact reviewed normative contract blob SHA: `59d8988a368a5bfffa94eacf7fbb8d769aea9b60`.
- Review type: same-session adversarial static self-review; NOT independent.
- Verdict: REQUEST CHANGES. F04's former six-key/eleven-key conflict is closed at documentation level, but two residual ambiguities were found:
  - F02-R1 HIGH: §22.6.1 requires a durable recovery checkpoint but does not define its exact closed schema/path/version, immutable or replacement semantics, monotonic relationship to the publication counter, or how rollback/copy of checkpoint and counter together is detected. The checkpoint is the proof used to resolve an otherwise unconfirmed receipt, so this is a required contract correction. Add missing/corrupt/regressed/copied/conflicting checkpoint fixtures.
  - F05-R1 MEDIUM: §22.5 describes the raw HTTP body digest as the evidence object identifier, while §22.9 defines `evidence_id` as the digest of the canonical envelope. The contract must explicitly separate the raw-body object ID from the envelope-record ID and define exactly which one `exchange_info_evidence_ref` references. Add swapped-ID/reference-confusion fixtures.
- Rechecked: F01 contract-level PASS; F03/F06 specified but runtime/target primitive NOT VERIFIED; F04 documentation-level PASS for schema precedence; F02 recovery linearization/fsync sequence specified but checkpoint proof contract incomplete; F05 raw evidence requirements specified but identifier namespace/reference unresolved.
- C117–C124 remain design-only; checkpoint rollback/corruption cases are not covered. C01–C124 NOT IMPLEMENTED / NOT EXECUTED.
- Unchanged blockers: F07 target filesystem/provider/flock/rename/fsync behavior NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer f64/12-decimal/parse-to-zero defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; manifest/receipt/counter/checkpoint/evidence store/adapter NOT IMPLEMENTED.
- Issue #138 remains OPEN and targets P1.14 blob `59d8988a368a5bfffa94eacf7fbb8d769aea9b60`; no independent reviewer response is present. Do not retarget until a corrected final SHA exists.
- No source changes, tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2, strategy/AI/ledger/risk/trading changes, or destructive data operations. No workflow run/artifact is claimed.
- Status: P1.15 SELF-REVIEW COMPLETE / REQUEST CHANGES / IMPLEMENTATION NOT AUTHORIZED / INDEPENDENT REVIEW STILL REQUIRED.
- Next step: documentation-only correction of F02-R1 and F05-R1, add negative fixtures, then review the final SHA and retarget issue #138. All existing authorization boundaries remain unchanged.


## Latest completed work — P1.15 corrections and P1.16 self-review (2026-11-09)

- User explicitly approved automatic execution of: F02-R1 recovery-checkpoint contract/rollback boundary; F05-R1 separation of raw-body and envelope IDs; negative/crash fixtures; self-review; then retarget issue #138 for independent review.
- Work remained on existing branch `feature/t0-centralized-data-feeder-p1-20261101`; documentation/evidence only.
- Normative contract: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md`.
- Final contract update commit: `69559bb0363934158351d794a48e17555f0222a8`.
- Exact final contract blob SHA: `f78dc4410db61755149cb6a7e0c440330bc80741`.
- F02-R1: §22.11.1 defines the recovery-checkpoint path, immutable per-publication record, closed 17-key schema, canonical JCS, file/directory fsync and no-replace publication. §22.11.2 embeds a five-key publication-counter snapshot and digest, validates monotonic consistency, and explicitly denies local checkpoint/counter status as an independent anti-rollback anchor. Full-root copy/restore without a separately trusted monotonic external anchor => continuity NOT PROVEN and quarantine. §22.11.3 defines restart revalidation and repeat fsync barriers before recovery acceptance.
- F05-R1: §22.11.4 separates Raw-body object ID (digest of exact original HTTP bytes) from Envelope-record ID (digest of canonical envelope projection with `evidence_id` omitted). The manifest reference must identify the Envelope-record ID; the envelope raw_body_sha256 binds the raw body. Resolution order and namespace confusion rejection are explicit.
- Added C125–C130 for checkpoint schema, binding, counter, rollback and crash/fsync failures; C131–C132 for raw-body/envelope namespace confusion and digest failures. C01–C132 remain design scenarios only; NOT IMPLEMENTED / NOT EXECUTED.
- Same-session self-review: `docs/reviews/t1/P1_16_SELF_REVIEW_P1_15_RECOVERY_CHECKPOINT_AND_EVIDENCE_ID_2026-11-09.md`; commit `9fe360f25c07610dd248eedab112397152aaef59`; blob `aa26ad804d151b07ceae1c2731b65fc121b9a197`.
- P1.16 verdict: DOCUMENTATION-LEVEL PASS for F02-R1/F05-R1 corrections and C125–C132 specification. This is same-session, NOT independent. Implementation readiness NOT ESTABLISHED; F07 NOT VERIFIED.
- Unchanged blockers: target filesystem/provider/flock/renameat2/fsync behavior NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; pinned producer f64/12-decimal/parse-to-zero defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; manifest/receipt/counter/checkpoint/evidence store/adapter NOT IMPLEMENTED.
- No source implementation, tests, GitHub Actions dispatch, Binance REST, VPS/runtime, T1 activation, T0/T2, strategy/AI/ledger/risk/trading changes, or destructive data operations. No workflow run or artifact is claimed.
- Next step: issue #138 is retargeted only after this final contract SHA and same-session review are recorded; wait for genuinely independent review. Implementation remains NOT AUTHORIZED and T1 activation remains NOT AUTHORIZED.
- Guardrails unchanged: T0 independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.


## Latest completed work — P1.17 follow-up adversarial self-review (2026-11-09)

- User requested another self-review after P1.15/P1.16.
- Exact reviewed normative contract blob SHA: `f78dc4410db61755149cb6a7e0c440330bc80741` (contract commit `69559bb0363934158351d794a48e17555f0222a8`).
- Review file: `docs/reviews/t1/P1_17_SELF_REVIEW_F05_MANIFEST_REFERENCE_AND_F02_ROLLBACK_LIMIT_2026-11-09.md`.
- Review commit: `17b4ddecfc7370163f6c78f3a5d778fe5a773a10`.
- Review type: same-session static adversarial self-review; NOT independent.
- Verdict: REQUEST CHANGES. Two residual findings:
  - F05-R2 HIGH: §22.11.4 says manifest `exchange_info_evidence_ref` references the Envelope-record ID, but §21.5 still calls it a reference to the raw ExchangeInfo snapshot and says it resolves to that snapshot. §22.11's precedence statement does not expressly supersede §21.5. Update §21.5 and precedence; add a fixture that rejects a manifest reference to a valid Raw-body object.
  - F02-R2 HIGH capability-boundary clarification: local checkpoint/counter/receipt/data all share one rollback domain. A same-filesystem full-root snapshot rollback can preserve all local identities and self-consistency; without an independent monotonic anchor the process cannot automatically detect that it is looking at an older state. The design must state that local checkpoint supports crash recovery only under a no-full-root-rollback assumption; known/suspected restore/clone/snapshot rollback must quarantine. Automatic full-root rollback detection is NOT PROVIDED absent a separately designed external anchor.
- Rechecked F01: §22.1 expressly supersedes older conflicting clauses and forbids current-profile `RECONCILED_COMPLETE`; watermark is non-authoritative progress only.
- F02-R1 checkpoint structure and fsync ordering are specified, but do not solve full-root rollback detection.
- F05-R1 is not fully closed across the document until §21.5 is aligned with §22.11.4.
- F03/F06/F07 target filesystem/provider behavior NOT VERIFIED; REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED.
- C01–C132 remain design-only; NOT IMPLEMENTED / NOT EXECUTED. No source implementation, tests, Actions run/artifact, REST, VPS/runtime, T1 activation or destructive operation.
- Issue #138 remains OPEN and targets the exact P1.15 contract SHA. No independent reviewer response is present. Do not treat P1.17 self-review as independent.
- Next step: documentation-only correction of F05-R2 and F02-R2, add negative fixtures, then self-review final SHA before retargeting issue #138.
- Authorization/guardrails unchanged: T1 implementation and activation NOT AUTHORIZED; T0 independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.


## Latest completed work — P1.17 contract corrections and P1.18 self-review (2026-11-09)

- User explicitly approved automatic execution: fix F05-R2 in §21.5 and precedence; clarify F02-R2 rollback boundary; add negative fixtures; self-review exact new contract SHA; only then retarget issue #138.
- Work remained on existing branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Normative contract file: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md`.
- Final contract update commit: `d6610f571417873e4c0b74dd770f705c86b24a56`.
- Exact final contract blob SHA: `984f7669f4dae5902b852b6f6fa1c09d799f9957`.
- F05-R2 correction: §21.5 manifest field inventory and resolver both require the Envelope-record ID; envelope `raw_body_sha256` resolves the exact Raw-body object; a direct manifest Raw-body reference is explicitly invalid. §22.11 precedence now expressly includes §21.5.
- F02-R2 clarification: local checkpoint/counter are crash-recovery evidence only; they do not detect/prevent full-root rollback. Automatic detection is NOT PROVIDED without a separately designed independent monotonic anchor. The protocol assumes no full-root rollback. If rollback is independently known or suspected, quarantine and require separately approved new root/recovery epoch. The text explicitly says internally consistent local files cannot reveal an unobserved rollback.
- Added C133 (valid Raw-body ID incorrectly used as manifest ref → reject), C134 (independent restore/rollback indication → quarantine), C135 (self-consistent old root without external signal is indistinguishable locally; automatic detection NOT PROVIDED).
- P1.18 self-review file: `docs/reviews/t1/P1_18_SELF_REVIEW_F05_R2_F02_R2_ROLLBACK_BOUNDARY_2026-11-09.md`.
- P1.18 review commit: `dc29e843d10ad63209743b6672e8c9fe963e1a7f`.
- P1.18 review blob: `960016187f1311d9d540a8f0c20340c8df31151c`.
- Verdict: DOCUMENTATION-LEVEL PASS for F05-R2, F02-R2 capability-boundary clarification and C133–C135 fixture specifications. Same-session review only; NOT independent. Implementation readiness NOT ESTABLISHED.
- Issue #138 was retargeted only after P1.18 review to exact contract blob `984f7669f4dae5902b852b6f6fa1c09d799f9957`; title now `P1.18 — Independent adversarial review of corrected T1 Source Contract`; state OPEN. It includes the P1.18 review blob and requests genuinely independent review. No reviewer response is claimed.
- F07 target filesystem/provider behavior remains NOT VERIFIED. Binance REST completeness oracle NOT ACCEPTED. Pinned producer f64/12-decimal/parse-to-zero defect remains CONFIRMED / NOT FIXED. Producer FINAL_ONLY/product identity NOT VERIFIED. C01–C135 remain design-only, NOT IMPLEMENTED / NOT EXECUTED.
- No T1 source implementation, adapter, tests, GitHub Actions run/artifact, Binance REST, VPS/runtime, T1 activation, T0/T2 change or destructive operation occurred.
- Next step: wait for genuinely independent written review of exact contract blob `984f7669f4dae5902b852b6f6fa1c09d799f9957`. Do not implement, test, dispatch Actions, access REST/VPS or activate T1 before independent review, F07 evidence and remaining blockers are resolved and separately approved.
- Guardrails unchanged: T0 independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no destructive data operations without separate explicit approval.


## Latest follow-up — P1.19 adversarial self-review (2026-11-09)

- User requested another self-review of the latest P1.18 contract.
- Exact reviewed contract blob remains `984f7669f4dae5902b852b6f6fa1c09d799f9957`, commit `d6610f571417873e4c0b74dd770f705c86b24a56`.
- Review file: `docs/reviews/t1/P1_19_SELF_REVIEW_RESTORE_EPOCH_PRECEDENCE_2026-11-09.md`.
- Review commit: `2b2677fa0c92a2c28d97c4579881bc1be7b2bdcb`.
- Verdict: REQUEST CHANGES. F02-R3 MEDIUM — restore/recovery-epoch semantics are not harmonized across §18.3, §21.5 and §22.11.2:
  - §18.3 says older-backup restore requires restore epoch/reconciliation and a new generation.
  - §21.5 says assign a new `source_root_id` when restore/copy cannot prove continuity.
  - §22.11.2 requires separately approved new `source_root_id`/recovery epoch and fresh reconciliation for known/suspected full-root rollback.
  - §22.11 precedence does not expressly harmonize §18.3. An implementer could misread "new generation" as sufficient.
  - §21.5 phrase "independently trusted latest counter/checkpoint" should clarify that only an independently controlled anchor outside the source-root rollback domain can establish latest-state continuity; local checkpoint/counter are not independent.
- Required: harmonize §18.3 and §21.5, add a fixture rejecting recovery via new generation only under old `source_root_id`, then self-review the corrected SHA.
- F05-R2 and F02-R2 core corrections were rechecked and remain sound at documentation level.
- No contract update or issue #138 retarget was made during P1.19. Issue #138 remains targeted to P1.18 contract SHA `984f7669f4dae5902b852b6f6fa1c09d799f9957`, OPEN; no independent reviewer comments were present at last check.
- C01–C135 remain NOT IMPLEMENTED / NOT EXECUTED; F07 NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; pinned producer decimal defect CONFIRMED / NOT FIXED; FINAL_ONLY/product identity NOT VERIFIED.
- No source implementation, tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes or destructive operation occurred.
- Next step: documentation-only correction of F02-R3, add the negative fixture, self-review the new exact contract SHA, and only then decide whether to retarget issue #138.
- Guardrails unchanged: T0 independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no destructive data operations without separate explicit approval.


## P1.20 — F02-R3 restore-epoch correction and self-review (2026-11-09)

- User approved automatic execution of the P1.19 next steps: correct F02-R3, add a negative fixture, self-review the exact new contract SHA, then retarget issue #138 only after the self-review.
- Normative contract file: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md`.
- Contract correction commit: `22dc3cde9a709197e84c7524d5fec076f10c9d7e`.
- Exact contract blob SHA: `77457a11aaf5b91f11aa8ea66cbf1414f7d9723a`.
- F02-R3 correction: §18.3 now distinguishes ordinary approved backup restore from known/suspected full-root rollback; for the latter, quarantine immediately, reject a new generation under the old `source_root_id`, and require separately approved new `source_root_id`, new recovery epoch and fresh reconciliation.
- §21.5 now explicitly states that local counter/checkpoint/receipt/manifest/data are not independent anchors; only an independently controlled monotonic anchor outside the source-root rollback domain could establish latest-state continuity, and none is provided by this profile.
- §22.11 precedence now expressly includes §18.3 and makes the new-root/recovery-epoch rule authoritative for known/suspected full-root rollback.
- New fixture C136 rejects recovery that retains the old `source_root_id` and only creates a new generation after known/suspected full-root rollback.
- Self-review file: `docs/reviews/t1/P1_20_SELF_REVIEW_F02_R3_RESTORE_EPOCH_2026-11-09.md`.
- Self-review commit: `ca91e2805cd4ddb55be6fab9a7572ad194e96be3`.
- Self-review blob: `8866b9e2397f3323cf1303c287ccac0ac788b32a`.
- Verdict: DOCUMENTATION-LEVEL PASS for F02-R3 and C136. IMPLEMENTATION READINESS NOT ESTABLISHED. F07 NOT VERIFIED. INDEPENDENT REVIEW REQUIRED.
- F01 and F05-R2 consistency rechecked. Automatic detection of unobserved full-root rollback remains NOT PROVIDED.
- C01–C136 remain NOT IMPLEMENTED / NOT EXECUTED; F07 NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; pinned producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED.
- No source implementation, tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes or destructive operations occurred.
- Next step: retarget issue #138 to exact contract blob `77457a11aaf5b91f11aa8ea66cbf1414f7d9723a` for genuinely independent review. This self-review is not independent.
- Guardrails unchanged: T0 independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no destructive data operations without separate explicit approval.


## Latest follow-up — P1.21 adversarial self-review of P1.20 (2026-11-09)

- Re-read the handoff, exact P1.20 normative contract and P1.20 self-review from the active branch before reviewing.
- Exact contract blob reviewed: `77457a11aaf5b91f11aa8ea66cbf1414f7d9723a`.
- New review: `docs/reviews/t1/P1_21_SELF_REVIEW_RECOVERY_EPOCH_AND_RECONCILIATION_RESUMPTION_2026-11-09.md`.
- Review commit: `7a51ddcfc94513f584f5e9350609cdc944817910`.
- Verdict: **REQUEST CHANGES** — two residual contract-level ambiguities:
  - F02-R4 HIGH: recovery epoch is required by §§18.3/21.5/22.11 and C136, but no authoritative identity/schema/persistence/binding exists in the source-root initialization, generation-counter or recovery-checkpoint schemas.
  - F01-R2 HIGH: recovery clauses require “fresh reconciliation”, but §22.1 forbids `RECONCILED_COMPLETE` and `reconciliation_evidence_ref` in current v1.1. Clarify that v1.1 recovery can at most resume isolated/unsealed collection with UNKNOWN health; canonical eligibility requires a separately versioned, independently reviewed and owner-approved completeness profile.
- F02-R3, F02-R2 rollback boundary, F05-R2 namespace separation and C136's limited fail-closed purpose remain consistent at documentation level.
- F07 NOT VERIFIED; Binance REST completeness semantics NOT ACCEPTED; pinned producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; implementation and C01–C136 execution NOT VERIFIED / NOT EXECUTED.
- Issue #138 remains OPEN and still targets P1.20 contract blob `77457a11aaf5b91f11aa8ea66cbf1414f7d9723a`; independent comments: 0. Do not retarget until the approved documentation corrections and another exact-SHA self-review are complete.
- No source implementation, tests, GitHub Actions dispatch, REST request, VPS/runtime, T1 activation, T0/T2 changes or destructive operation.
- Next step: documentation-only correction of F02-R4 and F01-R2, add negative fixtures, then self-review exact new SHA. Independent review and all authorization gates remain mandatory.
- T0 remains independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no destructive data operations without separate explicit approval.

## Latest completed work — P1.22 (2026-11-09)

- User approved automatic correction of P1.21 findings, negative-fixture specification, exact-SHA self-review, and conditional retargeting of issue #138 only if self-review passed.
- Normative contract: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md`.
- Final contract blob SHA: `20e8b31db364a15b73359810664f7e079aa86bc7`.
- Contract update commits (same existing branch, sequential):
  - `d2faa88f0af30adabf898483dbf039420b78d5a6` — define recovery epoch identity, root initialization binding, counter/checkpoint binding, and v1.1 resumption boundary.
  - `b1ddb3fe4b588a6adb7d751b43ccc6f9caa328ba` — align six-key counter / twelve-key initialization precedence and checkpoint snapshot.
  - `542e7c80d0a3fd5b933645f2eb6af58ae3d143b2` — close owner-approval record schema and immutable GitHub commit reference.
  - `98ea1474800ff81bba50f47e8636326baaacd628` — correct initialization-schema field delimiter.
- F02-R4: recovery_epoch_id is a distinct UUIDv4; root initialization is exactly twelve keys; immutable recovery-epoch record is closed schema; rollback recovery binds a separate immutable, commit-pinned owner approval record; generation publication counter is six keys; recovery checkpoint and historical counter snapshots bind the same epoch.
- F01-R2: “fresh reconciliation” is clarified as post-recovery structural/source-identity validation only. Current v1.1 permits at most separately approved isolated UNKNOWN/unsealed collection; no RECONCILED_COMPLETE, reconciliation_evidence_ref, canonical seal, completeness watermark, T0 promotion or aggregation. Canonical resumption requires a new versioned completeness profile, accepted oracle, independent review and explicit owner approval.
- Added negative fixture specifications C137–C140 for missing/reused epoch, identity mismatch across root/counter/checkpoint, invalid/mismatched owner approval, and attempted canonical promotion under v1.1.
- P1.22 self-review: `docs/reviews/t1/P1_22_SELF_REVIEW_RECOVERY_EPOCH_SCHEMA_AND_V1_1_RESUMPTION_2026-11-09.md`.
- Self-review commit: `f755c620c4f40c040466490b9cb63d91ac63ebf3`; blob SHA: `f3fca61dfd5d139e97a8b25fb34023c7e2f629ed`.
- Verdict: DOCUMENTATION-LEVEL PASS for F02-R4, F01-R2 and C137–C140 specifications. Same-session review, NOT independent. Implementation readiness NOT ESTABLISHED.
- Static checks: initialization/epoch/approval schemas; six-key counter; checkpoint epoch binding; §22.4/§22.9/§22.10 precedence; rollback boundary; UNKNOWN/unsealed-only recovery; C136–C140; F05 namespace rule — PASS.
- C01–C140 remain NOT IMPLEMENTED / NOT EXECUTED. F07 NOT VERIFIED. Binance REST completeness semantics NOT ACCEPTED. Pinned producer decimal defect CONFIRMED / NOT FIXED. Producer FINAL_ONLY/product identity NOT VERIFIED. No implementation, executable test suite, GitHub Actions run/artifact, REST, VPS/runtime or T1 activation.
- Issue #138 retarget is permitted by this self-review gate and is to be updated to exact contract blob `20e8b31db364a15b73359810664f7e079aa86bc7` for genuinely independent review. Same-session self-review is not independent.
- Guardrails unchanged: T0 independent/canonical; no T1 writes to T0; no T0/T2 changes; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no destructive data operations without separate explicit approval.

## Latest follow-up — P1.23 adversarial self-review of P1.22 (2026-11-09)

- Re-read the active-branch handoff, exact P1.22 contract, P1.22 review, and issue #138 before this review.
- Exact contract blob reviewed: `20e8b31db364a15b73359810664f7e079aa86bc7`.
- Review file: `docs/reviews/t1/P1_23_SELF_REVIEW_OWNER_APPROVAL_AUTHORITY_2026-11-09.md`.
- Review commit: `a0bbbc81c22a539ecaaee6fa6bc8fdff22d2bdd8`.
- Verdict: **REQUEST CHANGES — F02-R5 HIGH**. The P1.22 rollback-recovery approval record is content-pinned but the contract does not authenticate the named `approver_github_login` or prove that the actor had authority to approve the exact recovery decision. A repository writer could create a self-asserted JSON approval, set the owner's login, and pin its commit/blob digest. A commit SHA and file digest prove content identity/integrity, not human approval authority.
- Required before claiming enforceable approval: define an owner-controlled cryptographic signature/allowlist or a verifiable GitHub review/approval evidence process tied to exact commit/path/blob and actor authority; specify trusted authority source, role/allowlist, revocation/rotation, replay prevention and fail-closed behavior. Keep this separate from any independent anti-rollback anchor.
- P1.22 F02-R4/F01-R2 contract corrections remain documentation-level PASS within their narrower scope. F02-R5 is a new unresolved blocker; do not claim rollback-recovery approval is enforceable.
- Issue #138 remains OPEN and must continue targeting exact contract blob `20e8b31db364a15b73359810664f7e079aa86bc7` for independent review. Add F02-R5 to independent-review questions; do not retarget to a new contract SHA until a separately approved correction and exact-SHA self-review pass.
- No contract source changed in P1.23. No implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, trading or destructive operations.
- Existing blockers unchanged: F07 NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C140 NOT IMPLEMENTED / NOT EXECUTED.
- Guardrails unchanged: T0 independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no destructive data operations without separate explicit approval.

## Latest completed work — P1.24 (2026-11-09)

- User approved automatic correction of P1.23 F02-R5, negative fixtures, exact-SHA adversarial self-review, and conditional issue #138 retarget only if self-review passed.
- Normative contract file: docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md.
- Final contract blob SHA: dd33b60649d8881ca935d34b62b8b54b6d0e9d42.
- Contract commits:
  - ddb4693d83443d42d13884c03502a7513bf91aaa — define twelve-key Ed25519-signed approval record and external approver trust policy.
  - a990c76cc0418d2920fbf858c561e7c83ad6ee30 — align recovery-epoch record with signature/policy verification.
  - 5e76d65399c76e8221ffe320e11adf5a870e0192 — bind key validity to trusted verifier clock at verification time; keep signed approval timestamp audit-only; order C139–C145 fixtures.
- F02-R5 correction: self-asserted GitHub login is no longer authority. Approval requires Ed25519 signature over canonical JCS eleven-field payload (all twelve record fields except signature), key ID = SHA-256 of raw Ed25519 public key, and login-to-key match in an administrator-provisioned external trust policy.
- External trust policy is a closed JCS schema outside source root and all source-root restore/clone/snapshot sets. It defines public keys, authorized logins, validity intervals, ACTIVE/REVOKED status, policy digest, ownership/mode/no-symlink checks, rotation, immediate revocation and fail-closed behavior. No GitHub-metadata fallback or source-root policy fallback.
- approved_at_utc is signed audit metadata only; it does not prove signature creation time. Key validity is checked using verifier trusted clock at verification time. Signature/trust policy are not an independent monotonic anti-rollback anchor; compromise of external admin trust root/key remains an explicit out-of-profile threat.
- Added C141–C145 negative fixture specifications for malformed/forged signature or altered payload, unknown/wrong key and login mapping, revoked key, invalid external trust policy, and unavailable crypto/trusted clock. C137–C145 remain design-only.
- P1.24 self-review file: docs/reviews/t1/P1_24_SELF_REVIEW_SIGNED_RECOVERY_APPROVAL_2026-11-09.md.
- Self-review commit: ff0ad7782288ea6bc778f5b79482fb43113fc422; blob SHA: 43f8a505a52045469b1c7fd68bb0f73fc9450117.
- Verdict: DOCUMENTATION-LEVEL PASS for F02-R5 and C141–C145. Same-session review, NOT independent. No cryptographic keypair/signature/policy was generated or verified; checks are static contract consistency only.
- Existing blockers unchanged: F07 NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C145 NOT IMPLEMENTED / NOT EXECUTED.
- Issue #138 may now be retargeted to exact contract blob dd33b60649d8881ca935d34b62b8b54b6d0e9d42 for genuinely independent review; P1.24 self-review blob is 43f8a505a52045469b1c7fd68bb0f73fc9450117. Independent review remains pending.
- No implementation, executable tests, GitHub Actions run/artifact, REST, VPS/runtime, T1 activation, T0/T2 changes, strategy/AI/ledger/risk changes, trading or destructive operations.
- Guardrails unchanged: T0 independent/canonical; no T1 writes to T0; paper-only; AI_EXECUTION_ENABLED=false; no live orders; no OKX fallback/replacement; no destructive data operations without separate explicit approval.

## Latest follow-up — P1.25 adversarial self-review of P1.24 (2026-11-09)

- Re-read the active-branch handoff, exact P1.24 contract, P1.24 review and issue #138 before this review.
- Exact contract blob reviewed: `dd33b60649d8881ca935d34b62b8b54b6d0e9d42` (unchanged; no normative contract edits in P1.25).
- Review file: `docs/reviews/t1/P1_25_SELF_REVIEW_TRUST_POLICY_ROLLBACK_AND_APPROVAL_REPLAY_2026-11-09.md`.
- Review commit: `40d7233e439c1de93424e24075e662632eec5921`.
- Review blob: `a3b6561cc077ff97acbf3198a20e70aa78378a15`.
- Verdict: **REQUEST CHANGES — F02-R6 HIGH, F02-R7 MEDIUM, F02-R8 MEDIUM.**
- F02-R6 HIGH: external approver trust policy has no monotonic revision/latest-policy digest or append-only revocation anchor. A stale but internally valid external policy backup can restore a revoked key to ACTIVE; self-digest and outside-source-root placement prove neither freshness nor rollback resistance.
- F02-R7 MEDIUM: decision_record_id and root/epoch binding exist, but durable one-time consumption or explicit same-epoch idempotency/replay semantics are not specified. Define replay domain and add duplicate/cross-root/cross-epoch/crash-retry fixtures.
- F02-R8 MEDIUM: revocation invalidates previously recorded approvals, but verification lifecycle and effect on pending, accepted and active recovery epochs are unspecified. Define verification points, quarantine transitions and post-acceptance behavior.
- P1.24 F02-R5 signature structure remains present, but its complete approval lifecycle is NOT CLOSED at contract level. P1.24 DOCUMENTATION-LEVEL PASS is limited to signed-approval authority design and C141–C145 specification.
- Do not retarget issue #138 to a new SHA until F02-R6/R7/R8 are corrected, fixtures added and a new exact-SHA self-review passes. Issue #138 remains pointed to P1.24 contract blob `dd33b60649d8881ca935d34b62b8b54b6d0e9d42` and must include these follow-up findings.
- No implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, trading or destructive data operations.
- Existing blockers unchanged: F07 NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C145 NOT IMPLEMENTED / NOT EXECUTED.
- Guardrails unchanged: T0 independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no destructive data operations without separate explicit approval.

## Latest follow-up — P1.26 corrections and self-review (2026-11-09)

- User authorized automatic correction/self-review iterations until issue #138 can be retargeted after a self-review PASS.
- P1.26 normative contract commit: `2a2e07d7a781d837f90fc8a366d9db80414872aa`.
- Exact contract blob SHA: `312f3062cdacbdbaa2480ef5a0b3fa8d7693bcec`.
- P1.26 addresses P1.25 findings F02-R6/R7/R8 at documentation level: policy revision/previous digest plus an external monotonic ERA policy head; atomic one-time decision consumption bound to approval/root/epoch/scope tuple with exact-retry idempotency; recovery-epoch binding to signed consumption receipt; revalidation at open/read/write/transition gates and quarantine after revocation is observed.
- Added C146–C156 specifications for stale-policy restore, policy revision fork/skip, ERA unavailable/stale, exact retry, tuple reuse, crash windows, revocation timing, stale cache and malformed/replayed receipts.
- P1.26 self-review file: `docs/reviews/t1/P1_26_SELF_REVIEW_ERA_POLICY_FRESHNESS_REPLAY_REVOCATION_2026-11-09.md`.
- Self-review commit: `cc9f96583913677fd95c0323b6e3bac075bf8f80`; exact review blob SHA: `ab2ce3daaaeb59993b3bd3f76fa7e4b279f4c2b3`.
- Verdict: **REQUEST CHANGES — F02-R9 HIGH**. ERA is security-critical but no closed response/receipt schemas, signed payload boundary, exact signature/key-ID encoding, nonce/replay binding, trust bootstrap/rotation or independently auditable durability protocol are specified. Prose requirements do not provide an implementable/verifiable ERA wire contract.
- Do not retarget issue #138 until F02-R9 is corrected, negative fixtures are added, and a new exact-SHA self-review passes. Issue #138 remains targeted at P1.24 contract SHA `dd33b60649d8881ca935d34b62b8b54b6d0e9d42`; independent review pending.
- No ERA implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, trading or destructive data operations.
- Residual blockers unchanged: F07 NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C156 NOT IMPLEMENTED / NOT EXECUTED.
- Guardrails unchanged: T0 independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no destructive data operations without separate explicit approval.

## P1.27 — ERA protocol specification and follow-up self-review (2026-11-09)

- Contract commit: `7f40cf53687801dc4f4410c6ad61d5d347577ea2`.
- Exact contract blob: `19b6ce968776c6ff017966573ce53cbd3d33daa5`.
- Added ERA_V1 protocol, closed signed response envelope, separate ERA trust bootstrap/key, policy-head/advance/consumption payload schemas, nonce binding, caller roles, compare-and-advance, exact retry and monotonicity requirements.
- Added C157–C166 for envelope tampering, bootstrap failure, policy-head/advance errors, unauthorized role, durability/reuse, exact retry, key rotation and stale response replay.
- P1.27 self-review file: `docs/reviews/t1/P1_27_SELF_REVIEW_ERA_PROTOCOL_RECEIPT_SCHEMAS_2026-11-09.md`.
- Review commit: `559ab93b6e636907371c26f831359cd6afea52f7`; review blob: `002f466f8e17e92afedb37dd5b26da3fae69ce37`.
- Verdict: **REQUEST CHANGES — F02-R10 HIGH**. The recovery-epoch schema pins the ERA consumption payload but not the signed response envelope that authenticates it. The payload itself has no signature; after restart or ERA unavailability, durable epoch evidence cannot prove the ERA signature/authority sequence/operation. Require an immutable evidence bundle or explicit envelope ref/digest, bind exact payload digest, persist/fsync before epoch publication, verify after restart, and add negative fixtures.
- Issue #138 remains targeted at P1.24 SHA until F02-R10 is corrected and a new exact-SHA self-review passes.
- No ERA implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, trading or destructive data operations.
- Existing blockers unchanged: F07 NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C166 NOT IMPLEMENTED / NOT EXECUTED.
- Guardrails unchanged: T0 independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no destructive data operations without separate explicit approval.

## P1.28 — Signed ERA evidence bundle and follow-up self-review (2026-11-09)

- Contract commit: `66360c48824eb4ed1485bb56405e2dd7a850c6bf`.
- Exact contract blob: `b6c613c41613a409dca741d9ce64bdad4670c293`.
- Recovery epoch now binds an immutable evidence-bundle reference/digest instead of only an unsigned receipt payload.
- Bundle contains exact canonical consume-request bytes/digest, receipt-payload bytes/digest, signed response-envelope bytes/digest and bundle digest. Nonce, operation, ERA identity, payload digest, tuple, signature and policy head are cross-checked. Bundle no-replace/file-fsync/parent-fsync precedes epoch publication; offline verification after restart is specified, while fresh live ERA policy/revocation check remains required.
- Added C167–C170.
- P1.28 self-review file: `docs/reviews/t1/P1_28_SELF_REVIEW_SIGNED_ERA_EVIDENCE_BUNDLE_2026-11-09.md`.
- Review commit: `71bb31107d526e179efed750a68a1f24b6d8fd9f`; review blob: `bb4a35286f6058ba92e2ac1b5d439a02153f3284`.
- Verdict: **REQUEST CHANGES — F02-R11 MEDIUM**. ERA key trust entries lack authenticated revocation-effective authority sequence. Offline historical signature verification and current authorization after revocation are ambiguous. Define pre/post/equal-sequence behavior; retain historical cryptographic evidence but deny new authorization after revocation; fail closed if revocation ordering is unavailable; add fixtures.
- Issue #138 remains targeted at P1.24 contract SHA until F02-R11 is corrected and exact-SHA self-review passes.
- No ERA implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, trading or destructive data operations.
- Existing blockers: F07 NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C170 NOT IMPLEMENTED / NOT EXECUTED.
- Guardrails unchanged: T0 independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no destructive data operations without separate explicit approval.

## P1.29 — ERA key revocation sequence and follow-up self-review (2026-11-09)

- Contract commit: `2345c1dfa4da9cfab734c60daeb9ea224107bd2e`.
- Exact contract blob: `bfb8331d459b4caeb081af67c84d6ab2cc23edb3`.
- Added `revoked_at_authority_sequence` to ERA trust-key entries and separated historical signature verification from current authorization. Pre-revocation envelope can remain historical evidence only; equal/post-revocation sequence rejects; revoked key cannot authorize new recovery/gated operations; accepted epoch is quarantined before its next gated operation after revocation is observed.
- Added C171–C174.
- P1.29 self-review file: `docs/reviews/t1/P1_29_SELF_REVIEW_ERA_KEY_REVOCATION_SEQUENCE_2026-11-09.md`.
- Review commit: `7cca787862d8d164f2bb4cb5c65a7aa57c7415b8`; review blob: `e533d8a41eb2de1ce6d6cf462f5d139603a97870`.
- Verdict: **REQUEST CHANGES — F02-R12 MEDIUM**. The revocation-effective sequence in the external ERA trust file is not bound to a signed ERA revocation event. ERA operation enum and receipt schemas lack REVOKE_ERA_KEY. Add exact signed revocation operation/receipt, atomic sequence semantics, trust-file binding, crash recovery and fixtures.
- Issue #138 remains targeted at P1.24 contract SHA until F02-R12 is corrected and exact-SHA self-review passes.
- No ERA implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, trading or destructive data operations.
- Existing blockers: F07 NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C174 NOT IMPLEMENTED / NOT EXECUTED.
- Guardrails unchanged: T0 independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no destructive data operations without separate explicit approval.

## P1.30 — Signed ERA key revocation and follow-up self-review (2026-11-09)

- Contract commit: `57f96ab0b6507f73473f180056cdbf5bc48dbfaf`.
- Exact contract blob: `fef90de3176dffd7bd9979d46b68f976ceb5c878`.
- Added `REVOKE_ERA_KEY`, closed request and root-key-signed revocation receipt payload; revocation sequence is bound to response-envelope authority sequence and host trust entry.
- Added C175–C179.
- P1.30 self-review file: `docs/reviews/t1/P1_30_SELF_REVIEW_ERA_SIGNED_KEY_REVOCATION_2026-11-09.md`.
- Review commit: `fa25dac64327b6fb136cfcb5bf01ee7ce691c9dd`; review blob: `e91b070b3858cba122b8977129f47c78d67d2810`.
- Verdict: **REQUEST CHANGES — F02-R13 HIGH; F02-R14 MEDIUM.** Trust file pins revocation receipt payload but not the signed response envelope; after restart root-key signature/authority sequence cannot be verified. ERA root-key rotation and compromise recovery are undefined.
- Required next: bind exact signed envelope (or immutable evidence bundle) into trust-file revocation evidence, define durable publication/readback; define root-key rotation as separately approved offline transition and compromise quarantine; add fixtures.
- Issue #138 remains targeted at P1.24 SHA until F02-R13/R14 are corrected and exact-SHA self-review passes.
- No ERA implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, trading or destructive data operations.
- Existing blockers: F07 NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C179 NOT IMPLEMENTED / NOT EXECUTED.
- Guardrails unchanged: T0 independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no destructive data operations without separate explicit approval.

## P1.31 — ERA revocation evidence bundle and root-key boundary (2026-11-09)

- Contract commit: `dbb489a37b940a70711019759010952e69ab930f`.
- Exact contract blob: `dcdd4d3aa1743b169c9ab3f3cf7e1a32627c616e`.
- Operational ERA key trust entry now pins immutable revocation evidence bundle containing exact request, root-key-signed receipt payload and response envelope, with cross-digests and durable publication/readback ordering.
- Root-key rotation is explicitly offline/separately approved; no automated old-root fallback; suspected root compromise requires quarantine/manual independent re-provisioning.
- Added C180–C182.
- P1.31 self-review file: `docs/reviews/t1/P1_31_SELF_REVIEW_ERA_REVOCATION_BUNDLE_AND_ROOT_ROTATION_2026-11-09.md`.
- Review commit: `0dea77ba9bfcd7ea3f962e89d0f894ffdbd2a240`; review blob: `d8d823b5ea3a5778196ffa0ddaf53836e433090c`.
- Verdict: **REQUEST CHANGES — F02-R15 HIGH**. Contract requires fresh live ERA key-revocation status checks and recovery after interrupted trust-file update, but ERA operation enum has no READ_ERA_KEY_STATUS request/payload schema. Add root-key-signed status response, local/remote consistency rules and negative fixtures.
- Issue #138 remains targeted at P1.24 SHA until F02-R15 is corrected and exact-SHA self-review passes.
- No ERA implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, trading or destructive data operations.
- Existing blockers: F07 NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C182 NOT IMPLEMENTED / NOT EXECUTED.
- Guardrails unchanged: T0 independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no destructive data operations without separate explicit approval.

## P1.32 — Live ERA key-status operation and follow-up self-review (2026-11-09)

- Contract commit: `ea6fc3e74ae5803e0ff48f03ca3a9300b10c0376`.
- Exact contract blob: `57f1d6a7126de56b4ccd4707d8039dc0032d7e7e`.
- Added `READ_ERA_KEY_STATUS` with nonce-bound request and root-key-signed status payload; remote/local state reconciliation; remote REVOKED/local ACTIVE triggers evidence validation and quarantine; remote ACTIVE/local REVOKED or any mismatch triggers split-brain quarantine; unavailable/stale/unknown fails closed.
- Added C183–C188.
- P1.32 self-review file: `docs/reviews/t1/P1_32_SELF_REVIEW_ERA_LIVE_KEY_STATUS_2026-11-09.md`.
- Review commit: `4bbfb837cd0200336ae9b8509e136a6bf6ddd608`; review blob: `dccc923e60d33e9749bea2063d97e94c25993615`.
- Verdict: **REQUEST CHANGES — F02-R16 MEDIUM**. ERA_KEY_STATUS_V1 claims exactly seven keys but also requires an eighth `revocation_evidence_bundle_jcs_base64url` field. Correct cardinality/types and add missing/extra/malformed-field fixture.
- Issue #138 remains targeted at P1.24 SHA until F02-R16 is corrected and exact-SHA self-review passes.
- No ERA implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, trading or destructive data operations.
- Existing blockers: F07 NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C188 NOT IMPLEMENTED / NOT EXECUTED.
- Guardrails unchanged: T0 independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no destructive data operations without separate explicit approval.

## P1.33 — ERA status schema correction and follow-up self-review (2026-11-09)

- Contract commit: `e88de095e30211fbe43dedf422dec6f5152785c1`.
- Exact contract blob: `bcf78f3a70233aeb666fee468897f162405d03a0`.
- ERA_KEY_STATUS_V1 now has exactly eight always-present keys, explicit ACTIVE/REVOKED nullability, canonical base64url bundle encoding and digest verification.
- Added C189.
- P1.33 self-review file: `docs/reviews/t1/P1_33_SELF_REVIEW_ERA_KEY_STATUS_SCHEMA_2026-11-09.md`.
- Review commit: `c9fba0035689245f8f17577cc31aa9fe6c127552`; review blob: `a798eb4333af4a145c9a766cbf8fd9967cacf121`.
- Verdict: **REQUEST CHANGES — F02-R17 LOW**. Fixture IDs C146–C189 are out of numerical order (C171–C189 precede C166–C170; C179 appears after C189). Reorder and verify each ID exactly once.
- Issue #138 remains targeted at P1.24 SHA until F02-R17 is corrected and exact-SHA self-review passes.
- No ERA implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, trading or destructive data operations.
- Existing blockers: F07 NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C189 NOT IMPLEMENTED / NOT EXECUTED.
- Guardrails unchanged: T0 independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no destructive data operations without separate explicit approval.

## P1.34 — Fixture ordering correction and exact-SHA self-review PASS (2026-11-09)

- Contract commit: `aaeff086a4320cee1e3ed521324bed179120dbce`.
- Exact contract blob SHA: `0b4bef0ca9e0fdef7524dc3766cc32d897fa64ea`.
- Reordered C146–C189 into strict numeric order.
- Static inventory check: exactly 44 fixture lines; every ID C146–C189 exactly once; no omissions/duplicates; strictly ascending; terminal range C137–C189.
- P1.34 self-review: `docs/reviews/t1/P1_34_SELF_REVIEW_FIXTURE_ORDER_AND_ERA_APPROVAL_LIFECYCLE_2026-11-09.md`.
- Review commit: `e63cf519e5fb70c7072adbff1d632a47ddef3589`; exact review blob: `302939ee72397fa6893eaffb23f4042625b60edc`.
- Verdict: **DOCUMENTATION-LEVEL PASS for F02-R6 through F02-R17 corrections and C146–C189 specifications.** Same-session static adversarial review only; NOT independent. It does not prove ERA implementation/cryptography/durability, filesystem semantics, Binance completeness or runtime readiness.
- All P1.25–P1.33 findings F02-R6 through F02-R17 are addressed at contract-text level in exact contract blob `0b4bef0ca9e0fdef7524dc3766cc32d897fa64ea`.
- This PASS permits retargeting issue #138 to the exact P1.34 contract SHA for genuinely independent review. It does not close issue #138 or authorize implementation.
- Residual blockers unchanged: F07 NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; ERA/root-key/monotonic store NOT IMPLEMENTED / NOT VERIFIED; C01–C189 NOT IMPLEMENTED / NOT EXECUTED.
- No Actions run/artifact, executable tests, REST, VPS/runtime, T1 activation, T0/T2 changes, trading or destructive data operations.
- Guardrails unchanged: T0 independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no destructive data operations without separate explicit approval.



## Latest review — P1.35 (2026-11-09)

- Exact contract blob reviewed: `0b4bef0ca9e0fdef7524dc3766cc32d897fa64ea`.
- P1.34 self-review blob: `302939ee72397fa6893eaffb23f4042625b60edc`.
- Review: `docs/reviews/t1/P1_35_SELF_REVIEW_MANIFEST_HISTORY_RECOVERY_CHECKPOINTS_2026-11-09.md`.
- Finding: F02-R18 HIGH — §21.5/§5.2 replace the single fixed `manifest.json` on each publication, while §22.11.2 requires every checkpoint's exact historical manifest to remain available and validate. No immutable historical-manifest storage model is defined.
- Verdict: REQUEST CHANGES. Whole-contract documentation acceptance blocked until the historical manifest retention/binding model and negative/crash fixtures are specified and exact-SHA self-reviewed.
- Issue #138 remains OPEN and must not be retargeted as PASS. Independent review remains pending.
- No source implementation, executable tests, Actions dispatch, REST/VPS/runtime, T1 activation, T0/T2 change, trading or destructive data operation was performed or authorized.
- Residual blockers unchanged: F07 NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; ERA services NOT IMPLEMENTED / NOT VERIFIED; C01–C189 NOT IMPLEMENTED / NOT EXECUTED.


## Latest review — P1.36 (2026-11-09)

- Normative contract: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md`.
- Exact contract blob SHA: `1957eee80d5f6eb80889506514aaecf4b6a912cb`.
- Latest contract update commit: `d76c6e285db414d52a247f62c43f7c96c2ceb434`.
- P1.35 finding F02-R18 HIGH is corrected: every immutable per-publication receipt now carries the exact historical manifest bytes in canonical `manifest_jcs_base64url`, with digest binding, canonical encoding and bounded parsing. Recovery validates historical manifests from immutable receipts rather than the replaceable active `manifest.json`.
- Publication lock release now follows successful `fsync(commits_dir_fd)`, aligned with §22.6.1 commit-acceptance linearization.
- C190–C197 specify historical manifest retention, malformed/missing evidence, digest/schema mismatch, conflicting history and crash cases. C146–C197 inventory checked: 52 entries, strictly ascending, unique.
- Self-review: `docs/reviews/t1/P1_36_SELF_REVIEW_IMMUTABLE_RECEIPT_MANIFEST_HISTORY_2026-11-09.md`.
- Self-review commit: `e452737a94223e4f808934f84018e863093cdab3`.
- Exact self-review blob SHA: `163928749d5c2d756fb6aa98af6e1859bd95c7f6`.
- Verdict: DOCUMENTATION-LEVEL PASS for F02-R18 and directly coupled publication/checkpoint requirements only; same-session, NOT independent.
- Issue #138 is retargeted to exact P1.36 contract/review SHAs for genuinely independent review; it remains OPEN/PENDING.
- No source implementation, executable tests, GitHub Actions dispatch/artifact, REST, VPS/runtime, filesystem durability experiment, T1 activation, T0/T2 change, trading or destructive data operation was performed or authorized.
- Residual blockers unchanged: F07 NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; ERA services NOT IMPLEMENTED / NOT VERIFIED; C01–C197 NOT IMPLEMENTED / NOT EXECUTED.
- Guardrails unchanged: T0 independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no destructive data operations without separate explicit approval.


## Latest completed work — P1.37

- P1.36 exact-SHA adversarial self-review identified F02-R19 HIGH: §22.4's exact closed receipt key set omitted `manifest_jcs_base64url`, despite §5.2, §21.5 and §22.11.2 requiring the field. A parser following §22.4 would reject the receipt required by P1.36.
- P1.36 review also exposed F02-R20 MEDIUM: §22.8 still listed C01–C124 although the current contract's fixture inventory had expanded through C197.
- Corrected the existing contract in place on the existing branch; no branch divergence:
  - Contract path: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md`
  - Contract update commit: `a1d28543f5b0b77ee84b34871f77d42a87aa87e6`
  - Exact contract blob SHA: `9125e89b227fd9fa8364a02188d0be54ec3dd2ef`
  - §22.4 now defines all twelve receipt keys including `manifest_jcs_base64url`, exact canonical unpadded base64url rules, decode/re-encode, byte bounds, complete §21.5 validation and digest binding.
  - §22.8 now records C01–C197 as design scenarios only, NOT IMPLEMENTED / NOT EXECUTED.
- P1.37 same-session adversarial self-review:
  - Path: `docs/reviews/t1/P1_37_SELF_REVIEW_RECEIPT_SCHEMA_COHERENCE_2026-11-09.md`
  - Review commit: `dc5bba967fa6f8316d254b4c057b58755fbf97ed`
  - Exact review blob SHA: `2f4e036e4b0db7395588424783e6319e28779344`
  - Verdict: DOCUMENTATION-LEVEL PASS for F02-R19, F02-R20 and directly coupled P1.36 receipt/checkpoint requirements only. Same-session, NOT independent.
- Exact SHA readback verified both contract and review blobs. No source implementation, executable tests, GitHub Actions dispatch, REST request, VPS/runtime or filesystem experiment was performed. No workflow run/artifact is claimed.
- Status: P1.37 DOCUMENTATION-LEVEL PASS; independent review PENDING; F07 NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; implementation NOT AUTHORIZED; T1 activation NOT AUTHORIZED.
- Issue #138 is to remain OPEN and target exact P1.37 contract/review blobs for independent adversarial review. Do not treat this same-session PASS as independent closure.
- Guardrails unchanged: T0 remains independent/canonical; no T1 writes to T0; no T0/T2 changes; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no destructive data operations.
- Next step: obtain genuinely independent review of exact P1.37 blobs via issue #138. No implementation, executable fixtures, Actions, REST, VPS/runtime or T1 activation before separate gates and approvals.


## Latest completed work — P1.38

- Re-read the P1.37 contract, self-review, handoff and issue #138. Found F02-R21 MEDIUM: the contract header still identified the document as P1.14 despite P1.37 corrections and the P1.37 independent-review target.
- Corrected only the contract status line to `P1.37 REVISION — DESIGN ONLY — NOT APPROVED FOR IMPLEMENTATION`; implementation prohibition is unchanged.
- Contract update commit: `c96f56ae6e583e7fe15f420f5a0f78d3df0fc0c6`.
- Exact contract blob SHA: `b7b6786125be507c3ad4c29521830e5fe2a3b1b9`.
- P1.38 self-review: `docs/reviews/t1/P1_38_SELF_REVIEW_CONTRACT_REVISION_METADATA_2026-11-09.md`.
- Self-review commit: `ec9585e4d75ff933cc373bd5c8d4548c43defe7e`.
- Exact self-review blob SHA: `b8e5a3095a03c6b65dd9142cb06de9bc9dfd7155`.
- Verdict: DOCUMENTATION-LEVEL PASS for F02-R21 and rechecked F02-R19/R20 directly coupled requirements; same-session, NOT independent.
- Exact SHA readback verified both contract and review blobs. No source implementation, executable tests, GitHub Actions dispatch, REST request, VPS/runtime or filesystem experiment was performed. No workflow run/artifact is claimed.
- Status: P1.38 DOCUMENTATION-LEVEL PASS; independent review PENDING; F07 NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; implementation NOT AUTHORIZED; T1 activation NOT AUTHORIZED.
- Next step: retarget issue #138 to exact P1.38 contract/review blobs, keep OPEN for genuinely independent review.
- Guardrails unchanged: T0 remains independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no destructive data operations without separate explicit approval.


## Latest review — P1.38 second-pass adversarial review

- Re-read the exact P1.37 contract blob `9125e89b227fd9fa8364a02188d0be54ec3dd2ef` across §§5.2, 21.5, 22.2, 22.4, 22.6, 22.6.1 and 22.9–22.11; cross-checked C100–C197 and current status statements.
- No new actionable contract defect was identified in the bounded receipt/checkpoint/recovery scope. P1.38 verdict: DOCUMENTATION-LEVEL PASS, same-session only; not independent.
- To preserve the active branch, the P1.38 second-pass result was appended to the existing review file on the current branch:
  - Path: `docs/reviews/t1/P1_37_SELF_REVIEW_RECEIPT_SCHEMA_COHERENCE_2026-11-09.md`
  - Update commit: `8dc365de8c2baad8ac9f0006afd1aa21c0be9a41`
  - Exact updated review blob: `450909e836ad0e4cf4b25d745d17f1140ff79a20`
- The exact contract blob remains `9125e89b227fd9fa8364a02188d0be54ec3dd2ef`; no contract correction was needed in P1.38.
- Tool-path incident: a separate P1.38 review file was inadvertently created on the repository default ref rather than the active feature branch:
  - Commit: `e02cbe14c506c5f02ace6c250862e726a2ad57e5`
  - File blob: `3fa2f4725b5e7711b95716774fe3b5a6b2cf6509`
  - Verified by fetching the file with the default ref; it was not present on the active feature branch. It was not merged/cherry-picked into the feature branch. No deletion or rewrite of the default ref was attempted. Treat this as an isolated unplanned documentation commit requiring separate disposition; do not infer the active branch moved.
- Issue #138 is to target the exact P1.37 contract blob and the updated review blob above, remain OPEN, and continue to request genuinely independent review. A same-assistant second pass cannot satisfy independence.
- Residual gates unchanged: F07 NOT VERIFIED; Binance REST completeness NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; FINAL_ONLY/product identity NOT VERIFIED; implementation and T1 activation NOT AUTHORIZED; C01–C197 NOT IMPLEMENTED / NOT EXECUTED.
- No GitHub Actions run/artifact, executable tests, REST request, VPS/runtime or filesystem experiment was performed. No source, T0/T2, strategy, trading or data operation changed. T0 remains independent/canonical; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no destructive operations.


## Authoritative latest review state — P1.38 contract / P1.39 second pass

This section supersedes the immediately preceding “P1.38 second-pass adversarial review” paragraph where it described the P1.37 contract blob as the current target. That pass was performed against a stale snapshot after the active branch had already advanced.

- Current contract path: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md`
- Current exact contract blob SHA: `b7b6786125be507c3ad4c29521830e5fe2a3b1b9`
- Contract update commit: `c96f56ae6e583e7fe15f420f5a0f78d3df0fc0c6`
- Change: status metadata only, from stale P1.14 REVISION DRAFT to P1.37 REVISION; DESIGN ONLY / NOT APPROVED FOR IMPLEMENTATION preserved.
- P1.38 review path: `docs/reviews/t1/P1_38_SELF_REVIEW_CONTRACT_REVISION_METADATA_2026-11-09.md`
- P1.38 review update includes a P1.39 second-pass appendix:
  - Update commit: `ca419a70fb3134be518d636eeff3e233ff4f5073`
  - Exact review blob SHA: `920ac39b53c90f591bb6d1164ddac86ec5c99029`
  - P1.39 verdict: DOCUMENTATION-LEVEL PASS for the metadata-only correction and directly coupled receipt-schema/fixture-inventory regression checks; same-session, NOT independent.
- P1.37 contract/review second-pass work recorded above is historical and is NOT the current issue #138 target.
- Issue #138 currently targets P1.38 and remains OPEN. It must be retargeted to the exact contract blob `b7b6786125be507c3ad4c29521830e5fe2a3b1b9` and updated review blob `920ac39b53c90f591bb6d1164ddac86ec5c99029`, with a genuinely independent review still PENDING.
- The unplanned default-ref file/commit incident remains as recorded above; it is not part of the active feature branch target and no default-ref deletion/rewrite was attempted.

Guardrails and blockers remain unchanged: F07 NOT VERIFIED; Binance REST completeness NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C197 NOT IMPLEMENTED / NOT EXECUTED; implementation and T1 activation NOT AUTHORIZED. No Actions, executable tests, REST, VPS, filesystem or runtime experiment was performed. T0 remains independent/canonical; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no destructive data operations.


## Latest completed work — P1.40 / P1.41

- Fresh adversarial readback found F02-R22 HIGH: issue #138 title said P1.38 but its persisted body still contained the historical P1.34 review target. The previous retarget-success claim was therefore incorrect.
- P1.40 finding record: `docs/reviews/t1/P1_40_SELF_REVIEW_ISSUE_138_TARGET_INTEGRITY_2026-11-09.md`.
  - Finding record initial commit: `0dcc4f51ee93fcc244771083dd13b20749ca6761`.
  - Corrected exact-SHA record commit: `63b8433c254ed70d791a4bdb18fa197a73f45da0`.
  - Exact review blob SHA: `456daf7c53c60a5238b4f66f17e51f39c6212d4e`.
  - Verdict before correction: REQUEST CHANGES — F02-R22 HIGH.
- Replaced issue #138 body with a single authoritative P1.40 target, then fetched it again. Readback confirmed exact contract SHA `b7b6786125be507c3ad4c29521830e5fe2a3b1b9`, exact P1.40 review SHA `456daf7c53c60a5238b4f66f17e51f39c6212d4e`, OPEN state, zero comments, no stale P1.34 SHA and no stale P1.37/P1.38 current-target headings.
- P1.41 exact readback review: `docs/reviews/t1/P1_41_SELF_REVIEW_ISSUE_138_RETARGET_READBACK_2026-11-09.md`.
  - Commit: `8c19149bfe55e2414a33d9443afa42313221f1ee`.
  - Exact review blob SHA: `8a7120915851a74d56362abfc75b3e2a34bcb7d1`.
  - Verdict: DOCUMENTATION/PROCESS-LEVEL PASS for F02-R22 correction and persisted issue-body readback; same-session, NOT independent.
- Contract remains exact blob `b7b6786125be507c3ad4c29521830e5fe2a3b1b9`, commit `c96f56ae6e583e7fe15f420f5a0f78d3df0fc0c6`; DESIGN ONLY / NOT APPROVED FOR IMPLEMENTATION.
- Handoff update is documentation/evidence only. No source implementation, executable tests, GitHub Actions dispatch, REST request, VPS/runtime or filesystem experiment was performed. No workflow run/artifact is claimed.
- Next step: retarget issue #138 to the exact P1.40 contract/review plus P1.41 verification record; keep OPEN for genuinely independent review.
- Blockers unchanged: independent review PENDING; F07 NOT VERIFIED; Binance REST completeness NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C197 NOT IMPLEMENTED / NOT EXECUTED; implementation and T1 activation NOT AUTHORIZED.
- Guardrails unchanged: T0 remains independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no destructive data operations.


## Latest completed work — P1.42

- Re-read the exact P1.41 contract and issue #138 state. Issue #138 remains OPEN with zero comments; no genuinely independent reviewer response is present.
- Found F02-R23 HIGH: §9 C84 permitted acceptance of a visible receipt before `fsync(commits_dir_fd)`, contradicting §22.6.1.
- Corrected C84 and directly coupled C103 to require UNCONFIRMED state before the commit barrier and full §22.6.1 recovery validation, commits/generation directory fsyncs, durable recovery-checkpoint publication and its directory barriers.
- Contract update commit: `1557e9080e364d32a313694b5222ead8c790acce`.
- Exact current contract blob SHA: `3510c6a187c2677e0ad54060d1164a84984705c2`.
- Contract status: `P1.42 REVISION — DESIGN ONLY — NOT APPROVED FOR IMPLEMENTATION`.
- Adversarial readback confirms old unsafe C84 wording is absent; C84/C103 require the normative recovery barrier; §22.6.1 still defines successful commits-directory fsync as the only normal commit-acceptance linearization point.
- Found F02-R24 MEDIUM: §9 says retain C01–C24 from v1, but C02–C23 are not enumerated in the current contract and no exact original-v1 source path/commit/blob is pinned. The P1.3 base artifact at commit `0e2cbec07b1289950a7aa7ec1b99ef0ec7f6302c` also contains only the retention instruction, not those definitions. Do not invent the missing fixtures. Inventory completeness remains NOT VERIFIED pending the exact source or a verified restoration.
- P1.42 self-review: `docs/reviews/t1/P1_42_SELF_REVIEW_RECEIPT_BARRIER_AND_FIXTURE_TRACEABILITY_2026-11-09.md`.
  - Review commit: `cbf296da2b78fc3fb37f2765710755c18de13134`.
  - Exact review blob SHA: `5b790c38a811f7d54a93a7de9a83f22f72acac1f`.
  - Verdict: REQUEST CHANGES. F02-R23 is resolved at documentation level; F02-R24 remains open. Same-session review, NOT independent.
- Issue #138 remains OPEN and still points to the previous P1.41 contract blob. Do not retarget it to claim PASS until F02-R24 is resolved and a new adversarial pass succeeds; independent review remains a separate gate.
- No executable tests, GitHub Actions dispatch, REST request, VPS/runtime or filesystem experiment was performed. No workflow run/artifact is claimed.
- No source implementation, producer/adapter change, T0/T2 change, T1 activation, trading action or destructive data operation occurred.
- Unchanged blockers: F07 NOT VERIFIED; Binance REST completeness NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; FINAL_ONLY/product identity implementation NOT VERIFIED; manifest/receipt/counter/checkpoint/ERA/trust-policy/ExchangeInfo implementation NOT IMPLEMENTED / NOT VERIFIED; C01–C197 NOT IMPLEMENTED / NOT EXECUTED.
- Guardrails unchanged: T0 independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement; no destructive operations.


## User authorization — bounded automatic retargeting of issue #138

On 2026-11-09, the user explicitly approved the permissions needed to retarget issue #138 automatically. Scope:
- Authorized: update the title/body of existing issue #138 to the exact latest verified contract, review and handoff blob SHAs on the existing feature branch; fetch the persisted issue afterward and verify the target; record the operation in this handoff.
- Authorized when a new revision is actually ready: repeat the same retarget/readback process after its review record and handoff are committed and exact blob SHAs are verified. A REQUEST CHANGES target may be retargeted to accurately track the current revision; do not mislabel it PASS.
- Not authorized: close issue #138, mark an independent review PASS, fabricate reviewer feedback, change reviewers/assignees/labels, create a new issue/PR/branch, merge, dispatch GitHub Actions, modify source/runtime/T0/T2, activate T1, place orders, or perform destructive data operations.
- Current issue #138 was retargeted to P1.42 and remains OPEN. Persisted body identifies contract blob `3510c6a187c2677e0ad54060d1164a84984705c2`, P1.42 review blob `5b790c38a811f7d54a93a7de9a83f22f72acac1f`, and handoff blob to be verified after this update.
- Current review remains REQUEST CHANGES because F02-R24 is OPEN. This authorization does not waive any quality gate or independent-review requirement.


## User authorization correction — revoke automatic retarget; unblock remediation

Recorded 2026-11-09 from the user's clarification. This section supersedes the preceding “User authorization — bounded automatic retargeting of issue #138” permission grant.

### Revocation
- The prior permission for automatic retargeting of issue #138 is REVOKED immediately.
- Do not change issue #138 title/body or otherwise retarget it unless the user gives a new, explicit instruction for that specific retarget operation.
- Issue #138 must remain OPEN; do not close it or misstate review status.

### Authorized remediation scope
The user's intent is to grant the permissions needed to resolve the currently recorded BLOCKED items, not to automate issue retargeting. The following bounded work is authorized on existing repositories/branches only:
- Search repository history, refs, tags, and existing artifacts for the authoritative original C01–C24 fixture definitions; recover only from verifiable source evidence. Do not invent missing fixture definitions.
- Edit design documents, schemas, fixture inventories, source code, tests, and CI workflows necessary to address the recorded contract/producer blockers, while preserving T0 as an independent canonical data asset and keeping T1/T2 boundaries intact.
- In the existing T1 collector repository/branch associated with PR #1, investigate and correct the confirmed decimal serialization / parse-to-zero defect and implement or clarify FINAL_ONLY and product-identity behavior, with deterministic regression tests and exact evidence.
- Run repository-local tests and GitHub Actions workflows needed for validation; inspect workflow results and artifacts; update the existing handoff/evidence records with exact source SHAs, run IDs, artifact IDs, and PASS/BLOCKED/NOT VERIFIED status.
- Use unauthenticated, read-only public Binance REST requests solely to establish source semantics/completeness evidence where needed. No exchange credentials or authenticated endpoints.
- Run filesystem primitive/durability tests only in disposable isolated test directories or CI environments. Such tests must not target or mutate the canonical T0 database, existing VPS data, or user data.

### Still prohibited / requires separate explicit approval
- Any deployment, VPS login/configuration or runtime operation; starting/stopping feeders; changing systemd/autostart; modifying T0/T1/T2 runtime state or canonical databases.
- Any destructive operation against existing data, including deletion, archive, cleanup, vacuum, compaction, backup expiry, restore-overwrite, or destructive fault injection.
- Any test against the actual VPS target filesystem/device/provider that writes, renames, locks, fsyncs, or otherwise mutates existing paths. Read-only inspection may be proposed, but do not perform remote access unless an available authorized connector and exact scope are established.
- T1 activation, production operation, live trading, real orders, exchange keys, OKX fallback/replacement, or changes to the strategy/risk engine.
- Creating branches, PRs, issues, merging, changing reviewers/assignees/labels, or closing issue #138.
- Claiming independent review PASS based on same-session self-review. A genuinely independent review remains a separate quality gate.

### Required execution discipline
- Work in dependency order; fix the smallest blocker first and add negative/crash/regression fixtures.
- After each completed unit, self-review adversarially, run the relevant tests/CI, capture exact evidence, and update this handoff on the existing branch.
- Mark environment-dependent items NOT VERIFIED until evidence comes from the actual target environment. CI simulation does not prove VPS filesystem/provider semantics.
- Keep paper-only posture and `AI_EXECUTION_ENABLED=false`; no live orders.
- This authorization does not waive independent review, contract acceptance, or any safety/quality gate.


## Latest completed work — P1.43: recover authoritative C01–C24 fixture definitions

This section supersedes the P1.42 handoff statement that C01–C24 source definitions could not be located. The source has now been found and verified.

- Recovered source: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_AND_INGESTION_ADAPTER_DESIGN_2026-11-09.md`.
- Exact archived source blob SHA: `41a543f9772d890a47d5ebb923668609f5b1e7ea`.
- Provenance verified at parent commit `4d797bbb286e3e8fdc6c04ee7af70ec2fa7baeee` and P1.3 commit `0e2cbec07b1289950a7aa7ec1b99ef0ec7f6302c`; both refs return the same source blob SHA. The original C01–C24 rows are lines 156–179.
- Restored all 24 original scenario IDs and descriptions in §9.1 of the normative v1.1 contract, with explicit current v1.1 dispositions and §20.1 precedence. The archival source remains non-normative wherever it conflicts with v1.1.
- C07's former WINDOW_GAP expectation is explicitly superseded; WINDOW_GAP remains reserved/unassignable. C03/C24 are reconciled to producer-side FINAL_ONLY filtering. C17 retains exact decimal preservation. C22/C23 retain T0 isolation and no venue fallback.
- Contract update commits: `e93b3f779cd74d16335751965b8ad10d6a8f2b21` and continuation clarification `87ddd9ed93ab0ec0969625a2e8279c5ce61674ab`.
- Exact final normative contract blob SHA: `bafe555b6e3941bed4188575c7b7591c4ce3b473`.
- P1.43 self-review: `docs/reviews/t1/P1_43_SELF_REVIEW_RECOVERED_V1_FIXTURE_INVENTORY_2026-11-09.md`.
- Self-review commit: `d30f69f574624c0f090e3c8dad50bb25cfc227d2`.
- Exact self-review blob SHA: `0b4dd7f52bf0b6945b7e2a223246ba544813d628`.
- Static inventory check: C01–C197 = 197 definitions, 197 unique IDs, no missing IDs or duplicate definition rows. C01–C24 each appear exactly once. Documentation-level self-review verdict PASS for F02-R24 traceability/restoration only; same-session, NOT independent.
- Status: F02-R24 RESOLVED AT DOCUMENTATION/TRACEABILITY LEVEL; independent review PENDING. C01–C197 remain design scenarios only, NOT IMPLEMENTED / NOT EXECUTED. No workflow run or artifact is claimed.
- No issue retargeting was performed. Issue #138 remains OPEN and continues to reference its prior target until a new explicit user instruction for that specific retarget.
- No fixture code, tests, GitHub Actions dispatch, REST request, VPS/runtime or filesystem experiment, source implementation, T0/T2 mutation, T1 activation, trading action or destructive operation occurred.
- Remaining blockers unchanged: F07 NOT VERIFIED; Binance REST completeness NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; FINAL_ONLY/product identity implementation NOT VERIFIED; manifest/receipt/counter/checkpoint/ERA/trust-policy/ExchangeInfo implementation NOT IMPLEMENTED / NOT VERIFIED.
- Next step: proceed to the producer decimal defect on the existing T1 collector branch, with golden tests, without claiming compliance until CI evidence is recorded. Keep target-filesystem durability NOT VERIFIED and do not access or mutate the VPS/canonical T0 data.


## Latest completed work — P1.44: T1 kline decimal-loss correction

- Continued on existing T1 collector branch `feature/t1-connection-sidecar-integration-20261107`, PR #1 remains OPEN / DRAFT / NOT MERGED.
- Baseline T1 source SHA: `6e20fe94f3ad64cc450e73def80a167fe371e49e`.
- Confirmed defect path: `src/websocket/message_handler.rs::process_kline` called `format_decimal_str`, which parsed strings through `f64` and normalized to 12 decimals; `src/utils/csv_writer.rs::write_kline` repeated the float conversion and used `unwrap_or(0.0)`.
- Added regression tests first. TDD RED run `42644618882` at test-only SHA `c0a8a6fe506d6c8bf4596dbf1e0b8d0c15bf7ae2`: 43 passed / 3 failed as intended. Logs show exact precision loss and malformed/non-finite input acceptance.
- Fix commits:
  - Writer commit `268c4e85b5eef45f4f5d5788391057e341b012ed`; writer blob at that checkpoint `aa88bfb9f8b4d71bf70dd5c9333b527cf34b5d8e`.
  - Decimal helper commit / tested source checkpoint `ad03560b6409de3c28688fb25d57fa49aed66a9f`; `src/models.rs` blob `9b195b921eda2863f3769eaac34b3bd0bae48bd1`.
- Behavior: `format_decimal_str` now preserves the input lexeme; `write_kline` validates all eight decimal fields before opening/creating a file, then writes exact source strings without `f64` conversion. Malformed/non-finite numeric input returns an error; invalid input does not create a CSV file. No new dependency.
- Green GitHub Actions run `42644995874`, event `push`, exact tested source SHA `ad03560b6409de3c28688fb25d57fa49aed66a9f`: SUCCESS, 5/5 jobs PASS. Collector library 46/46; sidecar library 12/12; sidecar integration 27/27; formatting, Clippy, release build, Docker, dashboard backend/frontend and security jobs PASS.
- CI artifact `13686259637`, digest `sha256:eea348cc8cc370b9368abfc661655fa607aa0cb0ae0d9530ee81e081eecd1e04`, expires `2026-11-16T15:30:10Z`. Artifact is not deployment authorization.
- Added two additional lexical-validator tests (plain/exponent acceptance and malformed/non-finite rejection) at T1 commit `bbd591895421e383af83d68afc921ebc6df2a1d4`, then added T1 evidence doc at commit `c502fa1032c71c8b34cc09a6c5cca8eb79996d13`. These commits do not change the implementation logic tested at `ad03560...`.
- Exact current T1 branch HEAD: `c502fa1032c71c8b34cc09a6c5cca8eb79996d13`; current writer blob `c41cc7c13fc320e4083058fe6fe5683dc5c213d5`; current models blob `9b195b921eda2863f3769eaac34b3bd0bae48bd1`.
- The two workflow attempts for exact current HEAD `c502fa1...` ended `startup_failure` before job creation: `42645569066` (push) and `42645581768` (pull_request), both zero jobs. They are not test failures, but the additional two lexical tests and exact current HEAD remain NOT VERIFIED.
- T1 evidence doc: `docs/evidence/T1_KLINE_DECIMAL_PRESERVATION_2026-11-09.md`, blob `e7d0b03cef7800f94e13b6d1e761cb50bf3770d5`.
- P1.44 code self-review: `docs/reviews/t1/P1_44_SELF_REVIEW_T1_KLINE_DECIMAL_PRESERVATION_2026-11-09.md`; review commit `8b758f1d95dceeac8994fd79bf84364b1bf03285`; exact review blob `22f4080a93bebb0e31e674b563daea71827f8b99`. Verdict: bounded code self-review PASS at tested SHA `ad03560...`; same-session, NOT independent. Current HEAD remains NOT VERIFIED.
- Status: decimal-loss behavior FIXED and CI-VERIFIED at `ad03560...`; latest T1 branch HEAD / added edge tests NOT VERIFIED pending a fresh workflow run. No PR merge, deployment, VPS/runtime operation, T1 activation, T0/T2 mutation, live order, exchange credential use or destructive data operation.
- Remaining blockers unchanged: FINAL_ONLY/product identity implementation NOT VERIFIED; Binance REST completeness NOT ACCEPTED; target filesystem/provider durability F07 NOT VERIFIED; no production readiness claim.
- Next step: obtain a successful GitHub Actions run for exact T1 branch HEAD `c502fa1...` (or a later HEAD) so the added lexical edge tests are verified; only then proceed to FINAL_ONLY/product identity implementation review. Keep PR #1 OPEN/DRAFT and do not activate T1.


### P1.44 latest-head test fixture correction

- Adversarial review addendum corrected the test fixture for embedded-newline rejection: the runtime input is now an actual newline, not a literal backslash followed by `n`.
- T1 collector commit: `bb70a28d21486cb844d6fb8536be310172502abd`.
- Exact current T1 branch HEAD: `bb70a28d21486cb844d6fb8536be310172502abd`.
- Current writer blob SHA: `6fa31c4b5874f2ca874db47b2cb3c35dfc02953c`; models blob remains `9b195b921eda2863f3769eaac34b3bd0bae48bd1`.
- Workflow run `42645946681` ended `startup_failure` with zero jobs. Exact current HEAD and the added edge tests remain NOT VERIFIED. Implementation behavior remains verified only at `ad03560b6409de3c28688fb25d57fa49aed66a9f` by green run `42644995874`.
- P1.44 review addendum commit: `c6995836efb8e9dc11732c1162666c12b6bcceb5`; exact updated review blob `7a4fefc2d35b90daedf90c156ccf679546abef7e`.
- No issue retargeting, PR merge, deployment, VPS/runtime operation, T1 activation, T0/T2 mutation or destructive operation occurred.


## Latest continuation — T1 Actions startup investigation (2026-11-09)

- Reopened and read the current handoff before continuing. Automatic retargeting of issue #138 remains REVOKED. No issue #138 update or retarget occurred; issue remains OPEN.
- T1 collector repo/branch: `kenznguyen/binance-futures-collector` / `feature/t1-connection-sidecar-integration-20261107`.
- Inspected exact workflow `.github/workflows/ci.yml`, blob `8329039c807d63cf6834ca9c85fbd0cd99e474d4`. It contains push triggers for `main` and the T1 feature branch, plus pull_request; no path filters or job-level conditions explain the empty run.
- The T1 evidence record was updated at commit `4566cffbbcf8495182abbc0d3496fdc65709ac14`. This exact HEAD then produced:
  - Run `42646416010` (push): `startup_failure`, zero jobs.
  - Run `42646425898` (pull_request): `startup_failure`, zero jobs.
- Both associated check suites show `latest_check_runs_count=0`, `rerequestable=false`; GitHub jobs API returns an empty list. No runner step or Rust test ran.
- Available GitHub connector operations include rerun-failed-jobs and rerun-single-job, but not full-workflow rerun. Since these startup-failure runs have zero jobs and are not rerequestable, the connector cannot retry them. No workaround or workflow mutation was applied.
- Latest exact T1 branch HEAD at investigation: `4566cffbbcf8495182abbc0d3496fdc65709ac14`; PR #1 remains OPEN/DRAFT, not merged.
- Latest T1 evidence doc blob from the previous evidence update: `920e33a8df746faacdd95daf08dadc7d2a6940d5`.
- Latest P1.44 review addendum commit: `5ce97e785d4726120e133d934f90bb4bb15b0408`; exact review blob: `0633286bafc112408e213f5d1f20b19575fbe43a`.
- Status: implementation behavior remains CI-verified only at tested source SHA `ad03560b6409de3c28688fb25d57fa49aed66a9f` by green run `42644995874`; the added lexical edge tests and exact latest T1 HEAD remain NOT VERIFIED. Repeated startup failures are an Actions provisioning/platform blocker, not a test failure and not a source PASS.
- Next step: wait for GitHub Actions service/provisioning to recover or use an explicitly available authorized workflow retry path; then obtain a green run against the exact latest T1 HEAD before closing the P1.44 test-verification gate. Do not change CI configuration without evidence of a repository workflow defect.
- No issue retarget, PR merge, new branch/PR/issue, deployment, VPS/runtime operation, T1 activation, T0/T2 mutation, live order, exchange credential use or destructive data operation.


## P1.44 — GitHub Actions dispatcher investigation update (2026-11-09)

### Observed signature

T1 collector repository `kenznguyen/binance-futures-collector`, branch `feature/t1-connection-sidecar-integration-20261107`:
- Current exact HEAD: `4566cffbbcf8495182abbc0d3496fdc65709ac14`.
- Latest run `42646416010` (push) reports `path=BuildFailed`, empty workflow name, `conclusion=startup_failure`, zero jobs.
- Latest PR run `42646425898` reports the same signature.
- Jobs API returns an empty list. No runner assignment, step logs, test execution or artifacts.
- Workflow file `.github/workflows/ci.yml` remains unchanged, blob `8329039c807d63cf6834ca9c85fbd0cd99e474d4`; its push and pull_request triggers and job definitions are present.
- The failed run payload exposes synthetic workflow ID `412243529`. The connector's allowlist rejects direct GET of `/actions/workflows/{workflow_id}`, so its registration state (active/deleted) could not be independently confirmed.

### Diagnosis confidence

- This exact `BuildFailed` / empty-name / `startup_failure` / zero-job signature is reported by multiple GitHub Community discussions as a possible orphaned/synthetic Actions workflow registration or dispatcher/control-plane problem. Relevant reports: https://github.com/orgs/community/discussions/206103 and https://github.com/orgs/community/discussions/209847.
- This is corroborating pattern evidence only. It does NOT prove workflow ID `412243529` is deleted/orphaned or establish the root cause in this repository.
- No repository YAML defect or Rust source defect is evidenced by these runs; no runner ever started.

### Safe operating decision

- STOP generating further commits on the affected T1 branch solely to trigger CI. New pushes are producing more zero-job startup failures and no test evidence.
- Do not toggle repository Actions, delete/recreate workflows, alter billing/settings, change workflow YAML, create throwaway repositories, or attempt undocumented registry repair.
- Preserve PR #1 OPEN/DRAFT and current T1 source HEAD. Do not merge or activate T1.
- Recommended recovery path: submit the evidence packet to GitHub Support through the repository/account owner's authorized support channel, requesting investigation of Actions workflow registration/dispatcher for synthetic workflow ID `412243529`. Include run IDs `42646416010`, `42646425898`, exact branch HEAD, workflow blob, and zero-job evidence. No support ticket has been filed by this assistant.
- The connector cannot perform a full-workflow rerun; the affected runs have zero jobs and are not rerequestable.

### Status

- T1 decimal fix implementation: CI PASS only at source SHA `ad03560b6409de3c28688fb25d57fa49aed66a9f`, run `42644995874`.
- Added lexical edge tests and current exact T1 HEAD: NOT VERIFIED.
- P1.44 exact-head verification gate: BLOCKED by Actions startup/dispatcher behavior.
- Next: restore Actions dispatch through GitHub Support or another explicitly authorized recovery path, then run CI against an exact recorded HEAD. Only after that proceed to FINAL_ONLY/product identity.
- No T0/T2 changes, VPS/runtime access, T1 activation, real orders, destructive data operation, issue retarget or PR merge.


## L4 Provenance — Personal Non-Commercial Scope Record (2026-11-09)

- Recorded the owner's established personal/non-commercial system direction and translated it into a bounded L4 provenance scope proposal.
- Decision record: `docs/decisions/D-2026-11-09-L4-PROVENANCE-PERSONAL-SCOPE.md`.
- Decision-record commit: `68c8498013a08288c96a2d29c5a3884529061851`.
- Exact decision-record blob SHA after read-back: `d8a4b7e1b7dd6bc2923fbd37e93565a6f10a553d`.
- Scope: L4-Minimum proposes owner-controlled signing, exact-object binding, independent offline verification, independent evidence custody, append-only evidence history, key/trust lifecycle controls and claim discipline. Multi-tenant/SaaS, customer SLA, commercial compliance claims, multi-TSA quorum and dedicated WORM are deferred unless a concrete personal risk or obligation justifies them.
- This is a scope proposal, not ratification of each technical control and not an implementation acceptance. L4 remains BLOCKED / NOT VERIFIED for implementation and operational acceptance.
- Evidence baseline read: P1.8.67 blob `50654f3f4f4caa509598e4393e2634ea977df5dd`; P1.8.68 blob `9ae0c50830644d21d850da4c4d246a2837f62fc6`; P1.8.69 blob `caf0943865b096a0d592ae0718472754424991d0`; P1.8.76 blob `f559f642b48f1e7ea1e7f37935d00273d53ba161`; P1.8.141 blob `c20616d79f6dcedde08128f589a5c0e04d6257f1`; P1.8.152 blob `e1a4d95af216e94a58fa5528850fcd0c1ff465f8`.
- Existing limitations preserved: V07 BLOCKED; V08 OPEN/BLOCKED; Restore OPEN/BLOCKED; mutation fencing/adapter, runtime consumer/copy inventory and Option C technical enforcement NOT VERIFIED; lifecycle negative vectors NOT RUN. P1.8.153 remains the documented next lifecycle gate and is not displaced by this scope note.
- Tests NOT RUN; GitHub Actions NOT DISPATCHED; workflow run/artifact NONE. This is a documentation-only change.
- No source/runtime/schema/API/VPS/T0/T1/T2/DB/Feeder/ledger/strategy/risk changes; no permission or key operation; no TSA/provider call; no staging, restore, fault injection, archive, cleanup, compaction, vacuum, backup expiry, replica removal or deletion.
- Option C — No Destructive Authority — remains in force; GitHub permission inventory remains PAUSED; T0 remains independent; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.


## L4-Minimum scope approval and acceptance matrix (2026-11-09)

- Owner explicitly approved the L4-Minimum personal/non-commercial provenance scope in conversation on 2026-11-09. Approval covers scope and documentation-level acceptance profile only; it is not implementation or runtime authorization.
- Updated decision record: `docs/decisions/D-2026-11-09-L4-PROVENANCE-PERSONAL-SCOPE.md`; update commit `c4e71562d5f42ba45053c2b40ce80b11c3917646`; exact blob SHA `6b96c2c37a4989b7ceba291d027a3f8459eecb3b`.
- Created acceptance matrix: `docs/evidence/p1-8/L4-MINIMUM-PROVENANCE-ACCEPTANCE-MATRIX.md`; commit `d14d1c98fdad38d18447e0ec82e5eb11ae487dc5`; exact blob SHA `f39bef0c391e13a3656130f0e74f0e7a385b0c39`.
- Matrix defines L4M-01 through L4M-10: owner evidence custody; signing separation from T0; exact-object binding; independent offline verification; independent readback/recovery; key/trust lifecycle; append-only evidence history; claim discipline; independent review; fail-closed verdict semantics. It includes adversarial test groups and a minimum evidence package.
- Matrix status: DOCUMENTATION PASS only. No fixtures/tests executed, no GitHub Actions dispatch, no independent technical review. Requirements remain NOT IMPLEMENTED / NOT VERIFIED; L4 implementation and operational acceptance remain BLOCKED.
- Next L4-specific gate: independent review of the matrix against P1.8.36 and current lifecycle constraints, without runtime/secret/permission access. This does not replace the separate lifecycle next step P1.8.153.
- Existing boundaries unchanged: no source/runtime/schema/API/VPS/T0/T1/T2/DB/Feeder/ledger/strategy/risk changes; no key/trust-root/permission operation; no TSA/provider calls; no staging, restore, fault injection, workflow dispatch or destructive operation.
- Option C — No Destructive Authority — remains in force; GitHub permission inventory remains PAUSED; T0 remains independent; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.


## T1 isolated manual VPS validation — exact HEAD 4566cff (2026-11-09)

- Recorded bounded manual test receipt: `docs/evidence/t1/T1_MANUAL_VPS_TEST_RECEIPT_2026-11-09.md`.
- Receipt commit: `8a4e6174310f5ecb1d595330855ebd0143b6a0a3`; receipt blob SHA after read-back: `ed5c3fa6a4cf8ca6ea77dfd9d0eacedc3c8e5182`.
- Tested T1 source SHA: `4566cffbbcf8495182abbc0d3496fdc65709ac14`; isolated checkout: `/home/ubuntu/t1-test`, detached HEAD. Build target and evidence logs were stored under `/tmp/t1-manual-target-4566cffbbcf8495182abbc0d3496fdc65709ac14` and `/tmp/t1-manual-evidence-4566cffbbcf8495182abbc0d3496fdc65709ac14`.
- Manual Rust validation ran all 7 commands declared by the T1 CI workflow: collector Clippy PASS; collector fmt FAIL; collector release build PASS; collector tests PASS; sidecar fmt PASS; sidecar Clippy PASS; sidecar tests PASS.
- Test logs show collector 48 + 1 passed and sidecar 12 + 27 passed; 88 total test cases PASS, 0 FAIL. The collector test output also contains a zero-test target.
- Formatting finding: `cargo fmt --all --check` reports formatting-only diff at `src/utils/csv_writer.rs:1303`, in `decimal_lexical_validation_rejects_non_finite_and_malformed_forms`. No source fix was made in this pinned-SHA test.
- Log SHA-256 values, exit codes, generated lockfile metadata, cleanup evidence, and Actions run IDs are recorded in the receipt. Raw logs remain on the VPS evidence directory; they are not uploaded as GitHub artifacts.
- A Cargo-generated untracked `crates/connection-sidecar/Cargo.lock` (SHA-256 `c6fa4823bb25ac00873464ed733eb0816e962ffc370e13451dc291f160b01bdc`) was removed only after explicit owner approval. Final verification: HEAD unchanged at `4566cffbbcf8495182abbc0d3496fdc65709ac14`, clean detached checkout, generated file absent.
- Exact-HEAD GitHub Actions runs remain pre-job `startup_failure`, zero jobs: push `42646416010`, pull_request `42646425898`. No GitHub Actions tests or artifacts are claimed for this HEAD.
- Status: manual validation **PARTIAL PASS (6/7 commands)**; GitHub Actions exact HEAD **BLOCKED**; independent review **NOT VERIFIED**; T1→T0/T2 integration **NOT VERIFIED**; T1 activation/deployment **NOT AUTHORIZED / NOT PERFORMED**.
- No collector launch, Binance connection, exchange credentials, T0/T1 runtime or canonical data mutation, source modification, PR merge, issue #138 retarget, workflow configuration change, or live order occurred.
- Next step: preserve exact-HEAD evidence and investigate Actions dispatcher recovery through an owner-authorized supported path. Do not create further T1 commits solely to provoke CI. Any formatting correction requires separate scope approval and a new exact-SHA validation. Keep T1 inactive and integration unaccepted.
- This documentation update does not claim a CI run or artifact; it records the manual evidence only.

## T0 personal-use scope and de-commercialization boundary (2026-11-09)

- Recorded the owner-confirmed single-owner, non-commercial T0 scope in `docs/decisions/D-2026-11-09-T0-PERSONAL-USE-SCOPE-AND-DECOMMERCIALIZATION.md`.
- Decision commit: `ee026149c402f349686f770faf0ef0bc5d6d566c`.
- Scope exclusions: multi-tenant/customer isolation; subscription/billing/payment; customer-facing audit portal; commercial customer SLA/support; customer onboarding/licensing/package management; compliance/certification whose sole purpose is commercialization.
- The record distinguishes scope exclusions from proven code presence: the bounded inventory did not establish these subsystems in T0, and repository-wide absence remains NOT VERIFIED.
- Preserved owner-data controls: canonical source/market identity, candle validation/provenance, atomic writes, lease/generation fencing, read-only API, least privilege/authentication, backup/recovery, evidence and L4-Minimum controls.
- PostgreSQL/TimescaleDB and isolated Kraken Spot adapter are DEFER / REVIEW, not presumed commercial and not approved for removal. Android commercial-readiness/privacy/terms documents remain outside T0 scope and are retained separately.
- Dependency inventory reviewed includes T0 README/API/storage/PostgreSQL/write gateway/Kraken adapter files; T0 security, staging, provider and consumer-architecture docs; Android commercial documents. Repository-wide dependency graph remains incomplete.
- Status: owner scope CONFIRMED; first-pass inventory PARTIAL; repository-wide absence of commercial capabilities NOT VERIFIED; physical removal NOT AUTHORIZED.
- Tests NOT RUN; GitHub Actions NOT DISPATCHED; no workflow run/artifact claimed. Documentation-only change; no code, workflow, runtime, VPS, DB, T0/T1/T2, credential, permission or data changes.
- Option C — No Destructive Authority — remains in force. `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Next: read-only repository-wide dependency audit for excluded commercial groups and separate consumer/dependency audit for PostgreSQL/TimescaleDB and Kraken Spot. Independent review and exact-scope approval are required before any removal.

## T0 de-commercialization first-pass dependency audit (2026-11-09)

- Extended `docs/decisions/D-2026-11-09-T0-PERSONAL-USE-SCOPE-AND-DECOMMERCIALIZATION.md` with the read-only dependency audit.
- Audit update commit: `1ae7ca5822661eb1ff7530b7d2ff2d0f06043d09`; final decision-record blob SHA: `8381c6556e84cfc004a08372edcda7e76b03308c`.
- GitHub code search returned no matches for tenant, billing, subscription, customer, SLA/support tier, payment/onboarding/entitlement, Stripe/invoice, or multi_tenant. One `license` match was historical Android SDK license acceptance. Important limitation: the connector code search targets the default branch, not the active feature branch; repository-wide absence is therefore NOT VERIFIED.
- PostgreSQL/TimescaleDB is actively wired in current branch source: storage factory, Feeder runtime composition, lease adapter, fenced write gateway, runtime contracts, disposable lifecycle tests, manual validation gate, and psycopg dependency. Classification: DEFER / REVIEW; not a commercial feature and not approved for removal.
- Kraken Spot has a separate adapter, dedicated SQLite store, isolated read API, three test modules, and three manual workflow gates. Classification: DEFER / REVIEW pending actual research-consumer/value assessment; not a commercial feature and not approved for removal.
- No current component meets REMOVE-CANDIDATE threshold. Android commercial readiness/privacy/terms remain outside T0 and are retained separately.
- Status: scope decision CONFIRMED; first-pass dependency audit PARTIAL; commercial capability absence repository-wide NOT VERIFIED; PG/Kraken retain/remove decisions DEFERRED; no source removal authorized.
- No tests, workflow dispatch, VPS/runtime/database inspection or mutation occurred. No workflow run/artifact is claimed. Documentation-only updates; no source/config/API/schema/credential/permission/data changes.
- Next: independent adversarial review of the scope decision and audit evidence; if it passes, a separate consumer/value review for Kraken Spot and a maintenance/cost review for PostgreSQL. No removal until exact-scope owner approval.

## T0 de-commercialization adversarial self-review (2026-11-09)

- Added §9 to `docs/decisions/D-2026-11-09-T0-PERSONAL-USE-SCOPE-AND-DECOMMERCIALIZATION.md`.
- Review commit: `179dc51ec989d48fa89c6082c311f43e8ea72a2e`; decision-record blob SHA: `f4198dd51e5bf58e07aba34a6fa1ab2d8d9bef6b`.
- Review was an adversarial self-review by the same assistant/work session that authored the record; it is NOT independent second-reviewer acceptance.
- Verdict: CONDITIONAL PASS for the written single-owner scope boundary; BLOCKED for independent audit acceptance and any removal.
- SR-01 HIGH: GitHub code search targets the default branch, not the active feature branch; therefore cannot prove absence of commercial features on the current branch.
- SR-02 MEDIUM: active-branch recursive tree path scan found only generic `market_data/test_support.py` among keyword-like path matches; path names alone do not prove content absence.
- SR-03 MEDIUM: bounded inventory is not a full dependency graph across all 636 files, generated configuration, Android, T1/T2, deployment scripts or runtime environment.
- SR-04 LOW: PG/Kraken source/test/workflow wiring is proven, but active owner runtime/research use is not.
- SR-05 LOW: Android legal/distribution documents remain outside T0; no deletion/legal conclusion implied.
- No critical contradiction found in the written scope boundary. Commercial capability absence remains NOT VERIFIED; dependency audit remains PARTIAL; no REMOVE-CANDIDATE; no source removal authorized.
- No tests or Actions were run. No runtime, VPS, DB, data, key, permission or workflow changes.
- Next: branch-pinned content/config/workflow/dependency audit, PostgreSQL/Kraken consumer/value mapping, and review by a genuinely independent second reviewer.

## T0 branch-pinned de-commercialization content audit (2026-11-09)

- Added §10 to `docs/decisions/D-2026-11-09-T0-PERSONAL-USE-SCOPE-AND-DECOMMERCIALIZATION.md`.
- Audit commit: `6340f42473adba3de4217fc54755321502c244fe`; decision record blob SHA: `97c13bcc8b6389ec576a338bd54f79b17f2a4621`.
- Exact audited branch HEAD before this documentation update: `a1053f40a2f762af52237401da2a0d00c4e813b1`; recursive tree read was complete (`truncated=false`, 636 tracked paths).
- Fetched all 13 active GitHub Actions workflows at that exact commit; no excluded commercial capability terms found.
- Fetched and keyword-reviewed core T0 runtime source (API/storage/Postgres/Feeder/store/write gateway/Kraken adapter-store-API); no customer commercial subsystem terms found. The certificate match is PostgreSQL TLS certificate/hostname verification.
- Fetched and reviewed key T2 HTTP bridge/dashboard files; no excluded commercial capability terms found.
- Reviewed Android commercial readiness/privacy/terms/README and Gradle/manifest. Commercial-readiness/paid commercialization checklist is Android product documentation, not T0; Android legal/product docs retained separately.
- Resolved keyword false positives: WebSocket “subscription set” in futures README; cloud provider billing/invoice/payment in staging research; model certification in architecture; generic test_support filename. None establishes customer commercial functionality.
- Rechecked T0 architecture/security/staging docs. TLS/certificates and infrastructure-cost controls are security/operational controls, not commercial customer services.
- PostgreSQL/TimescaleDB remains DEFER / REVIEW due to real source/runtime/test/workflow dependencies. Kraken Spot remains DEFER / REVIEW due to isolated adapter/store/API/tests/workflows; active personal research consumer/value is still NOT VERIFIED.
- Verdict: no commercial T0 subsystem found in inspected branch-pinned surfaces. This is a bounded content audit, not a semantic review of every blob among 636 paths. Repository-wide absence remains NOT VERIFIED; earlier HIGH blocker narrowed but not closed. Archived workflows, all non-T0 modules, Android implementation, deployment/runtime files and external consumer repos remain incomplete.
- No tests or Actions were run; no workflow run/artifact. No provider calls, VPS/runtime/DB inspection or mutation. No code/config/workflow/data changes beyond decision/handoff documentation.
- No REMOVE-CANDIDATE. No deletion or destructive operation authorized. Option C — No Destructive Authority — remains in force.
- Next: finish content review of remaining relevant non-T0 modules/archived workflows/deployment files and map actual PG/Kraken consumers; then obtain a genuinely independent reviewer. Do not remove anything before independent acceptance and exact-scope owner approval.


## T1 post-rustfmt manual VPS revalidation — 2026-11-09

- Receipt updated: [T1 manual VPS test receipt](docs/evidence/t1/T1_MANUAL_VPS_TEST_RECEIPT_2026-11-09.md), documentation commit `35fd00cb6640fed0f2054d1d057522ec5a7db485`, receipt blob `75bf4bd77379ecfe0b9678809407a86e8fceb5ab`.
- Isolated checkout baseline HEAD: `4566cffbbcf8495182abbc0d3496fdc65709ac14` (detached).
- Formatting-only local patch: `src/utils/csv_writer.rs`, 14 insertions / 2 deletions; patch SHA-256 `90cee952837cf753bf872c2cb19f75e1157dc5c64eb937d58c62cbe796a31ec6`. No production logic changed.
- Re-run of all 7 CI Rust commands: **7/7 exit code 0**; collector 49 tests + sidecar 39 tests = **88 PASS / 0 FAIL**. Rustfmt and Clippy checks, release build, and both test suites passed.
- Raw logs remain on VPS at `/tmp/t1-manual-evidence-postfmt-4566cffbbcf8495182abbc0d3496fdc65709ac14`; SHA-256 manifest is in the receipt. No GitHub Actions artifact exists for this manual run.
- Generated untracked sidecar Cargo.lock was verified by size/hash and removed under the user's explicit authorization. Final checkout had only the intended modified Rust source file and no generated lockfile.
- **Status:** bounded manual validation PASS for baseline plus uncommitted formatting patch. This is not a new commit SHA, not GitHub Actions CI PASS, and not independent review.
- GitHub Actions dispatcher remains BLOCKED / NOT VERIFIED; runs `42646416010` and `42646425898` were pre-job startup failures with zero jobs. No support packet/ticket was prepared or submitted (user skipped that step).
- T1 → T0/T2 integration remains NOT VERIFIED; T1 activation/deployment NOT AUTHORIZED / NOT PERFORMED.
- No T1 source commit/push, collector launch, Binance connection, credentials, runtime mutation, PR merge, issue retarget, or workflow configuration change.
- Next: preserve the local patch and evidence. Before any source commit/push or new CI attempt, obtain explicit scope approval; do not create T1 commits solely to trigger the currently blocked dispatcher.


## T0 de-commercialization follow-on deployment and consumer audit (2026-11-09)

- Read handoff before work; confirmed branch HEAD at audit start: `ae545616ed5c35767d6f3c00ad77f4deac7bb79f`; tree SHA `755db16daeef9454c23bae36789afc6953522214`; recursive tree complete, 636 tracked paths, `truncated=false`.
- Extended `docs/decisions/D-2026-11-09-T0-PERSONAL-USE-SCOPE-AND-DECOMMERCIALIZATION.md` §11 with branch-pinned deployment/archived-workflow and PostgreSQL/Kraken consumer evidence.
- Decision-record update commit: `0fc395cfa780125812338f4d79da8fa229716650`; exact updated blob SHA: `a79c1128d393a48e0c47f20579602ff96de26093`.
- PostgreSQL finding: code supports a complete optional T0 runtime path (candle store + DB-clock lease + fenced write gateway); SQLite remains default. Runtime/deployed backend selection NOT VERIFIED. Classification KEEP AS SUPPORTED OPTIONAL BACKEND; defer adoption/cost decision.
- Kraken finding: isolated adapter, separate SQLite store and separate read API, dedicated tests and manual gates. No in-repository T1/T2/Futures consumer demonstrated in the bounded path/file review; external/manual consumer and owner research value NOT VERIFIED. Classification DEFER / REVIEW; no removal candidate.
- Archived workflow/deployment review is PARTIAL. Archived workflow README states Codemagic runs jobs, conflicting with owner's current GitHub Actions-primary/Codemagic-deprecated direction; Codemagic config remains tracked but external account state/execution NOT VERIFIED.
- CI-policy defect found: `ci/test_ci_policy.py` blob `42b2c4164b28e1dac32457f36435d05207350714` asserts `.github/workflows/` has no YAML files, while the pinned tree contains 13 active workflow YAML files. Codemagic's canonical-market-data workflow invokes CI policy tests via `ci/test_*.py` discovery. Likely exact-tree failure if that legacy Codemagic workflow runs; NOT EXECUTED. Separate CI-maintenance scope required; no change made.
- Tests NOT RUN; GitHub Actions NOT DISPATCHED; no workflow run/artifact. No VPS/runtime/database/data/key/permission/provider operation. No source/config/workflow/deployment mutation. No deletion or destructive operation.
- Status: branch-pinned path inventory COMPLETE; semantic audit PARTIAL; PostgreSQL implementation dependency confirmed but actual runtime use NOT VERIFIED; Kraken external/manual consumer NOT VERIFIED; CI policy inconsistency FOUND; repository-wide commercial absence NOT VERIFIED; independent second review BLOCKED; no REMOVE-CANDIDATE; Option C remains in force.
- Next: separate CI-policy reconciliation; finish Kraken external/manual consumer/value inventory; obtain genuinely independent second review before any removal proposal.


## T1 formatting-only Rustfmt commit — 2026-11-09

- Owner-authorized formatting-only source commit on existing T1 branch `feature/t1-connection-sidecar-integration-20261107`.
- T1 parent SHA `4566cffbbcf8495182abbc0d3496fdc65709ac14`; new commit `f3bae0cfbc26aa694a4d6c9476965121818d3567` ([commit](https://github.com/kenznguyen/binance-futures-collector/commit/f3bae0cfbc26aa694a4d6c9476965121818d3567)).
- Single changed path `src/utils/csv_writer.rs`; 14 insertions / 2 deletions, formatting-only adjustment to an existing test. GitHub commit diff and file read-back verified; new file blob `0a4455134de9b353b4a7c25ffc6f0a252ca2c5a0`.
- Manual test evidence: 7/7 Rust commands PASS, 88 PASS / 0 FAIL on parent SHA plus the exact same local patch (patch SHA-256 `90cee952837cf753bf872c2cb19f75e1157dc5c64eb937d58c62cbe796a31ec6`). The newly committed SHA itself was not checked out/retested: exact-SHA verification NOT VERIFIED.
- Workflow run lookup for new SHA returned no runs; Actions CI status for new SHA NOT VERIFIED. Existing dispatcher incident remains unresolved; do not claim CI PASS.
- Receipt updated in main repo: `docs/evidence/t1/T1_MANUAL_VPS_TEST_RECEIPT_2026-11-09.md`, documentation commit `d86a473389dce79b8a663e30ee4f34668c55b408`, blob `e8ff995c13b05fdea35effbc35f0bc416ca2304b`.
- No collector launch, Binance connection, exchange credentials, T0/T2 or T1 runtime mutation, PR merge, issue retarget, or deployment.
- Next: verify new exact SHA in an isolated checkout and rerun the bounded Rust checks if permitted; retain T1 inactive. Do not attempt to bypass or reconfigure the Actions dispatcher.


## T0 de-commercialization — commercial-scope content audit phase 1 (2026-11-09)

- Read-only source audit pinned to commit `1569dde41f8219cd6fbc9a52d126450715a7995a`; tree SHA `4a0ec1c235aa0c12fa071b2a5c485b807a9f063a`; recursive tree complete, 636 blobs.
- Evidence: `docs/evidence/COMMERCIAL_SCOPE_CONTENT_AUDIT_2026-11-09.md`; creation commit `8812a7a21de142654b27beaf2d2bd56537a93f88`.
- Decision record appended §12: commit `8e3e94095f76063c44bb67c015de28a8fbf15a13`; new blob SHA `c7891def00458604158984a00634d131060a1737`.
- Inspected key root/service/API/dashboard/paper-ledger/T0/T2/FreqAI/Futures Intelligence/Android source surfaces, all 13 active workflows, all 8 archived workflow YAML files, Codemagic and key dependency manifests.
- No commercial implementation identified in inspected surfaces across multi-tenancy, customer billing/subscription, customer portal, commercial SLA/support tiers, onboarding/licensing/entitlements or commercial-only certification.
- Important distinction: paper ledger has `account_id` columns, but `paper_accounts.account_id` is constrained to 1 and migration inserts only account 1; this is one internal PAPER account, not multi-tenant evidence. API uses shared environment Bearer tokens, not inspected per-customer identity/tenant authorization.
- Android `COMMERCIAL_READINESS.md` is a future release/paid-commercialization checklist, not an implementation. Provider billing/invoice/payment language is infrastructure-cost research. Android Terms licence references are ownership/third-party notices.
- All six repository-wide absence claims remain NOT VERIFIED; this is a bounded content audit and not a semantic review of every tracked blob or external deployment/account/consumer.
- Tests NOT RUN; Actions NOT DISPATCHED; no workflow run/artifact. No source/config/dependency/workflow/runtime/data/credential/key/permission changes; no VPS/DB/provider operations.
- No REMOVE-CANDIDATE or removal proposal. Option C — No Destructive Authority — remains in force.
- Next: continue remaining source/config/docs/deployment and external-boundary review; maintain path/symbol coverage; do not promote repository-wide absence claims without complete evidence.


## T0 commercial-scope remaining core/integration source audit — phase 2 (2026-11-09)

- Read current handoff before work. Branch-pinned source audit used commit `7d885115e04c2196d0051356acbe7521fdb12f1e`; recursive tree `1ab56aebdec79bd07d9305fd52a7c51235d2780c`, `truncated=false`, 637 tracked blobs.
- Inspected 16 remaining high-level source/config/doc files: root README/app/bot/Telegram commands; integrations README/Codemagic client/Hummingbot bridge; pipeline contracts/API/decision; Android release helper scripts; dashboard bootstrap; synthetic-evidence README. Exact paths and blob SHAs are recorded in `docs/evidence/COMMERCIAL_SCOPE_REMAINING_SOURCE_AUDIT_2026-11-09.md`.
- No excluded commercial capability terms or implementation were identified in these 16 inspected files.
- No application source file from this phase qualifies as a commercial-only REMOVE-CANDIDATE.
- `android-app/COMMERCIAL_READINESS.md` remains a documentation-only potential candidate for explicit path-level review; it is not an executable subsystem. Android privacy/terms and release engineering are not automatically removable.
- Evidence report creation commit: `dd87444326415a8467eb194860a1e00a3434c550`.
- This remains a bounded audit, not a semantic review of all 637 blobs. Six-group repository-wide absence remains NOT VERIFIED. No source or docs were deleted; no tests or Actions were run; no runtime/VPS/database/data/credential/key/permission changes. No workflow run/artifact claimed.
- Status: phase-2 bounded review PASS; repository-wide audit PARTIAL; independent second review NOT PERFORMED; no implementation REMOVE-CANDIDATE established; no deletion authorized/performed. Option C remains in force.
- Next: finish the remaining documentation/configuration/test surfaces with coverage accounting; then independent second review. Any documentation deletion must name exact path(s), preserve Android legal/privacy obligations, and be authorized separately before mutation.


## T0 commercial-scope documentation/configuration review — phase 3 (2026-11-09)

- Read handoff first. Exact source commit `2e4af7a218f06be5666f0e56cda9f1df825d9ab9`; recursive tree complete, 638 tracked blobs.
- Inspected 23 documents covering architecture/runbooks, T0 staging/provider research, lifecycle/security, PostgreSQL/Kraken design, Codemagic docs and Android commercial/privacy/terms documents. Exact blob SHAs and findings are in `docs/evidence/COMMERCIAL_SCOPE_DOCUMENTATION_AUDIT_PHASE3_2026-11-09.md`.
- Infrastructure provider billing/payment/provisioning language is infrastructure cost/security research, not customer billing. Keep these controls.
- PostgreSQL/Kraken docs are technical data capability docs, not commercial services. Retain pending their separate consumer/architecture decision.
- Exact documentation-only candidate identified: `android-app/COMMERCIAL_READINESS.md` (blob `9532b34f4a7c1dcac571b9ba4fe5064fa2cfc324`), a future public-release/paid-commercialization checklist. Proposed REMOVE only after independent second review and explicit owner approval.
- `android-app/PRIVACY_POLICY.md` and `android-app/TERMS_OF_USE.md` are NOT removal candidates in this phase; retain pending any separate legal/privacy/ownership review.
- Evidence report commit: `7d1bce2c91b2c5af5facfbb6158733d762745497`.
- No source/config/docs/dependency/workflow/runtime/data/credential/key/permission mutation except this audit record and handoff. No deletion. Tests NOT RUN; Actions NOT DISPATCHED; no run/artifact.
- Status: phase-3 bounded documentation review PASS; one documentation candidate identified but NOT APPROVED; repository-wide six-group absence NOT VERIFIED; independent second review NOT PERFORMED. Option C remains in force.
- Next: request genuinely independent second review of the exact candidate and full audit evidence; if accepted, obtain explicit approval for deleting only `android-app/COMMERCIAL_READINESS.md`. Continue residual source/docs coverage accounting. No other deletion is in scope.


## Commercial candidate self-review correction (2026-11-10)

- Re-read the complete `android-app/COMMERCIAL_READINESS.md` (blob `9532b34f4a7c1dcac571b9ba4fe5064fa2cfc324`) against the owner personal-use scope decision.
- Corrected Phase-3 overbroad disposition: the file is mixed-purpose, not wholly commercial. It contains retained personal-use assurance content: Android device QA, M15/H1 alert and Python parity checks, reconnect/background/recovery checks, performance/accessibility checks, signing-key and CI-secret custody, artifact signature/SHA-256 verification, install/upgrade/migration hygiene, privacy/risk/source-attribution/provider-terms checks.
- Whole-file deletion is REJECTED. Remove or rewrite only clearly commercial/customer/public-store commercialization items after checking actual distribution context. Preserve internal QA, security, privacy and release engineering controls.
- Self-review evidence: `docs/evidence/COMMERCIAL_SCOPE_CANDIDATE_SELF_REVIEW_2026-11-10.md`; commit `3e6bec20d809e3d937c7d80826d72131dc0920f6`.
- This is same-assistant self-review, NOT an independent second review. No source edit or deletion performed. No tests or Actions run. No runtime/data/credential/key/permission/workflow changes.
- Status: whole-file REMOVE CANDIDATE withdrawn; revised disposition = REWRITE / PRUNE COMMERCIAL-ONLY CONTENT, preserve personal-use controls. Repository-wide six-group absence remains NOT VERIFIED.
- Next step: search references to the document and produce a minimal replacement/pruning diff, then obtain independent review before applying it. Any store-specific legal requirements remain conditional on actual distribution and applicable law.


## Android personal-use checklist pruning proposal (2026-11-10)

- Re-read handoff and source on active branch before continuing.
- Inspected current candidate `android-app/COMMERCIAL_READINESS.md` (blob `9532b34f4a7c1dcac571b9ba4fe5064fa2cfc324`), Android README (blob `0289d6a94ca70d2eeacef8b6ebedf40ca31aa3d9`), active Android paired release workflow (blob `b6f6b3deccc01f27fb3c00b0bb5657033508be5c`), and release/build/APK verification scripts (blobs `bea2164a5a264f4cda8bd47908f5e61805f86ab9`, `2a122c3b9385f74722292841e6d5f2067a159d92`, `9131207cdcc2fcda95b3aae2a6d97cb5255c6e9c`, `8a2bf3b1d3b173c8ec67c1e88541fa43f1cd316d`).
- Confirmed checklist is mixed-purpose. Internal QA, Python parity, Android lifecycle/recovery, signing-key custody, CI secret hygiene, artifact SHA/signer verification, privacy, risk disclosure and attribution must remain.
- Created a proposed replacement/pruning document: `docs/evidence/ANDROID_PERSONAL_USE_CHECKLIST_PRUNING_PROPOSAL_2026-11-10.md`; proposal commit `8d3fad75be397b20612dc9d13b21a72ed89d5a54`.
- Proposal keeps the existing source path to avoid unnecessary rename/reference churn; removes only commercial/customer-specific work; public-store obligations are conditional on future owner decision to distribute publicly.
- Search limitation: GitHub code search covers the default branch, not this feature branch; no claim of exhaustive reference absence is made. Feature branch tree at the inspected HEAD was complete (640 blobs), but full content-level reference/dependency proof remains incomplete.
- Separate issue noted: `android-app/README.md` says Codemagic runs build/test jobs, while current owner direction is GitHub Actions primary and Codemagic deprecated/legacy fallback. Not changed; separate scoped documentation correction required.
- Status: proposal drafted; NOT APPLIED. Independent second review NOT PERFORMED. Owner approval to replace source file NOT YET GIVEN. Tests NOT RUN; Actions NOT DISPATCHED; no artifact.
- No source/runtime/VPS/DB/data/credential/key/permission/workflow changes.
- Next: independent reviewer evaluates proposal and source context; after review, obtain explicit owner approval before updating the source checklist. Keep Option C; no destructive action.


## Android checklist converted to personal-use QA (2026-11-10)

- Owner explicitly approved replacing the contents while retaining exact path `android-app/COMMERCIAL_READINESS.md`.
- Updated only that file. New content covers Android M15/H1 QA; deterministic Android/Python engine parity; reconnect/background/process-restart/recovery/notification behavior; signing-key custody and GitHub Actions secrets; exact source SHA, APK identity, signature and SHA-256 verification; privacy, risk disclosure and third-party attribution; public-store requirements only if the owner later explicitly chooses public distribution.
- Removed pricing, paid/free packaging, refunds, payments/billing, subscriptions/customer licensing, customer support/onboarding/provisioning, commercial sales/rollout and customer-facing service commitments.
- Source before update blob: `9532b34f4a7c1dcac571b9ba4fe5064fa2cfc324`.
- Updated file blob: `cbea17bb36300193b6e4cf05780a35d01c7d7500`.
- Source update commit: `d24207badf1350d1a710540e2bb9b5eceed29bf9`.
- No file rename or deletion. No other source/config/workflow/runtime/VPS/database/data/credential/key/permission changes.
- Tests NOT RUN; GitHub Actions NOT DISPATCHED; no run/artifact. Documentation-only change; test status is NOT VERIFIED, not PASS.
- This applies the owner's explicit content instruction. It is not an independent second review; no independent reviewer claim is made.
- Next: verify branch HEAD and exact file content/blob, then optionally reconcile Android README's Codemagic/GitHub Actions description in a separate scoped change. Keep paper-only boundary and Option C.


- Follow-up content verification found that an initial `Explicitly excluded` paragraph still repeated commercial-category terms. Removed that paragraph so the checklist contains no pricing/refund/subscription/customer-support/commercial-rollout checklist section or residual category list.
- Final checklist blob: `ec9d8bd800c17b11ce4807df5464aaa3634ec80d`; correction commit: `0a2f9ccb1624e737e78afc7de8b09a5169691753`.
- Final content check verifies required personal-use sections present and commercial category terms absent. Handoff is updated below; final branch HEAD verification follows.


## T0 TSA and WORM read-only audit — 2026-11-10

- Read handoff first; verified branch `feature/t0-centralized-data-feeder-p1-20261101`, source HEAD `326ebd3723587323aa39660777becd44ed273105`, tree `4c48cfa3ea45c339f8c6b395f06ca6533252ba32`, complete (`truncated=false`, 711 entries).
- Added bounded read-only audit: `docs/evidence/T0_TSA_WORM_READ_ONLY_AUDIT_2026-11-10.md`.
- TSA: P1.8.67/P1.8.68 target architecture is documentary/static PASS; P1.8.77 source mapping shows no signed T0 checkpoint, timestamp outbox, RFC 3161 client/verifier or TSA evidence archive. TSA production remains BLOCKED; owner decision required between dataset/checkpoint proof (A), signed-object historical verification (B), or separately versioned A+B.
- WORM: no WORM adapter/lock configuration in T0 `market_data` source/migrations. Forward-evidence Root A/Root B WORM architecture is a separate evidence subsystem, not T0 canonical candle storage. AWS S3 Compliance Mode is a preferred Root A candidate; GCS/Azure are Root B disposable-test candidates; Cloudflare R2 is lower assurance. No provider selected, provisioned or tested.
- Synthetic-only `synthetic_evidence/trust_lifecycle.py` explicitly marks retention `GIT_HISTORY`, `immutability=NOT_WORM`, Actions artifact retention 7 days. Local SQLite Root B is a synthetic model, not provider WORM.
- Owner-ratified RET-01 B protects T0 canonical data from routine/automatic/scheduled deletion; this is policy, not technical WORM. Option C — No Destructive Authority — remains in force.
- Source/runtime/VPS/DB/Feeder/provider/key/permission changes: NONE. Tests NOT RUN; Actions NOT DISPATCHED; no run/artifact. No TSA/OCSP calls, provider contact, restore, fault injection, archive, cleanup or deletion.
- Status: bounded read-only audit COMPLETE; TSA production BLOCKED; WORM in T0 NOT IMPLEMENTED/NOT VERIFIED; provider qualification NOT RUN; runtime copy/provider inventory NOT VERIFIED; independent review of this audit NOT PERFORMED.
- Next: owner decision on TSA evidence subject and WORM scope before any implementation or provider qualification proposal. Preserve T0 canonical data and recovery copies; no destructive action.


## T1 exact-commit manual VPS validation — 2026-11-10

- Exact tested T1 source SHA: `f3bae0cfbc26aa694a4d6c9476965121818d3567`, isolated detached checkout `/home/ubuntu/t1-verify-f3bae0cf`.
- All 7 Rust checks completed with exit code 0 on that exact commit: collector format, collector Clippy, release build, collector tests, sidecar format, sidecar Clippy, sidecar tests.
- Test totals: collector 48 + 1; sidecar 12 + 27 = **88 PASS / 0 FAIL**.
- Raw logs and their seven SHA-256 hashes are recorded in `docs/evidence/t1/T1_MANUAL_VPS_TEST_RECEIPT_2026-11-09.md`; logs remain on VPS at `/tmp/t1-verify-evidence-f3bae0cf-postcleanup`. No Actions artifact exists.
- Root filesystem after build: 736 MB free; `/tmp`: 3.5 GB free. The old 2.7 GB baseline build target was explicitly removed after confirming no active Cargo/Rust process.
- Cargo regenerated an untracked `crates/connection-sidecar/Cargo.lock` after the run. Its exact current hash/removal is pending verification; do not treat the worktree as clean yet. No tracked source changes were reported.
- **Status:** exact-SHA manual validation PASS (7/7, 88/0); GitHub Actions exact-SHA NOT VERIFIED; T1→T0/T2 integration NOT VERIFIED; T1 activation/deployment NOT AUTHORIZED / NOT PERFORMED.
- No collector launch, Binance connection, exchange credentials, live order, T0/T1 runtime mutation, PR merge, issue retarget, or workflow configuration change.
- Next: verify the regenerated untracked lockfile's size/hash against the previously authorized Cargo-generated file before removing only that exact file; then verify clean checkout. Preserve all seven logs and do not run another build. Keep existing branch and record evidence only.


## T0 L4-Minimum read-only assurance audit — 2026-11-10

- Read current handoff first. Source branch HEAD before audit record: `cad0453a93f7092ca490a54dc09b7d84dae5d4d4`; recursive tree complete, 712 entries (`truncated=false`).
- Owner-approved L4-Minimum acceptance matrix: `docs/evidence/p1-8/L4-MINIMUM-PROVENANCE-ACCEPTANCE-MATRIX.md`, blob `f39bef0c391e13a3656130f0e74f0e7a385b0c39`; scope decision `docs/decisions/D-2026-11-09-L4-PROVENANCE-PERSONAL-SCOPE.md`, blob `6b96c2c37a4989b7ceba291d027a3f8459eecb3b`.
- Added bounded read-only audit: `docs/evidence/T0_L4_MINIMUM_READ_ONLY_AUDIT_2026-11-10.md`; creation commit `f547d29c2d0633fccbecd992b791ecc65a232818`.
- Ten-control disposition: L4M-01 owner custody NOT VERIFIED; L4M-02 owner signing separation NOT VERIFIED; L4M-03 exact-object binding PARTIAL (synthetic/design only); L4M-04 offline verification PARTIAL (CI/synthetic only); L4M-05 independent readback/recovery PARTIAL (temporary synthetic SQLite only); L4M-06 key/trust lifecycle PARTIAL (synthetic policy only); L4M-07 append-only history PARTIAL (synthetic only; Git history explicitly NOT_WORM); L4M-08 claim discipline PASS at documentary/synthetic scope only; L4M-09 independent review PENDING/NOT VERIFIED; L4M-10 fail-closed PARTIAL (synthetic tests only).
- T0 source mapping P1.8.77/P1.8.78 reconfirmed: candle-oriented store/Feeder; fenced writes; `datasetVersion` is a read-window response hash, not a signed checkpoint; no T0 signed checkpoint, signing lifecycle, TSA outbox/verifier/archive or WORM adapter/config in inspected `market_data` source/migrations.
- P1.8.23 CI evidence remains synthetic-only: source SHA `082cc68b14148829c01fc63558f6781fa006756b`, workflow run `42557957929`, 3/3 jobs and 162/162 tests PASS, 13/13 synthetic fault vectors PASS; artifacts `13648297207` and `13648187759`, recorded expiry `2026-11-16T03:43:37Z`. Retention manifest explicitly labels `GIT_HISTORY`, `NOT_WORM`, 7-day Actions artifact.
- L4-Minimum does not mandate external TSA or dedicated WORM; these are L4-Extended. Their absence is not itself an L4-Minimum failure. Required owner evidence custody/readback and trustworthy verification are still unproven.
- Lifecycle remains open per P1.8.152: RET-01/02 policy-only; RET-03, RET-06–10 open/not verified; V07 BLOCKED; V08/Restore OPEN/BLOCKED; mutation fence/adapter and runtime copy inventory NOT VERIFIED; 87 lifecycle negative vectors NOT RUN; Option C technical enforcement NOT VERIFIED; GitHub permission inventory PAUSED.
- Overall: bounded audit COMPLETE; L4 profile OWNER-APPROVED; L4 technical/operational acceptance BLOCKED/NOT VERIFIED. L4M-08 is documentary PASS only; no control is promoted to T0 production PASS.
- No tests run for this audit; Actions NOT DISPATCHED; no new workflow run/artifact. No source/schema/runtime/VPS/Feeder/database/data/provider/credential/key/permission change, no operational inventory, no TSA/OCSP call, no restore/fault injection, no archive/cleanup/deletion.
- Paper-only; `AI_EXECUTION_ENABLED=false`; Option C — No Destructive Authority — remains in force.
- Next: independent review of the exact L4 acceptance matrix and audit report; then define a T0 evidence object/checkpoint and owner-controlled signing/custody boundary before considering any implementation. Do not claim independent review by the report author.


## T0 L4-Minimum adversarial static review — 2026-11-10

- Added `docs/evidence/T0_L4_MINIMUM_ADVERSARIAL_REVIEW_2026-11-10.md`.
- Review commit: `80e9429b0f63ea58b96a51a42ce53b88aa95ab50`; review blob SHA: `a7aec29330d71cb4d34193d6db81b8e20eb295f1`.
- Exact inputs: acceptance matrix blob `f39bef0c391e13a3656130f0e74f0e7a385b0c39`; audit report blob `cfecb7428508adf23e6b9e71dc0dfe1e0e38080c`; scope decision blob `6b96c2c37a4989b7ceba291d027a3f8459eecb3b`.
- Same-session adversarial static review identified F-01–F-06: (F-01) bind owner evidence custody explicitly to T0/VPS and GitHub outage domains; (F-02) define an independently retained latest-head anchor for freshness/rollback claims; (F-03) keep historical trust-at-time UNKNOWN absent qualifying time/revocation evidence; (F-04) distinguish tamper-evident append-only history from WORM/absolute immutability; (F-05) specify reviewer competence and conflict evidence; (F-06) define aggregate verdict precedence across all ten controls.
- Scope clarified: no independence of market-data sources is required; independent evidence custody/readback and independent reviewer remain separate L4 assurance requirements. TSA and dedicated WORM remain non-mandatory L4-Extended capabilities.
- Result: matrix readiness PARTIAL; findings open. This is explicitly NOT a genuinely independent third-party review and does not satisfy L4M-09. Genuine independent review remains PENDING.
- No tests, Actions workflow, source/runtime/VPS/DB/keys/permissions/data changes or destructive actions. Option C remains; paper-only; `AI_EXECUTION_ENABLED=false`.
- Next: correct matrix wording for F-01–F-06, then obtain a genuinely independent review of the corrected matrix and exact audit report. Keep L4 technical/operational acceptance BLOCKED / NOT VERIFIED.


## L4-Minimum Acceptance Matrix — F-01–F-06 and lifecycle-aligned revision (2026-11-10)

- Updated existing path `docs/evidence/p1-8/L4-MINIMUM-PROVENANCE-ACCEPTANCE-MATRIX.md`; no parallel matrix or branch created.
- Update commit: `9c96d0fa4a664d553719c273b9c2ff36fef247de`.
- New matrix blob SHA after read-back: `53591e9e3790b4d0b18787ff66bf36a3d45138e9`.
- Previous matrix blob: `f39bef0c391e13a3656130f0e74f0e7a385b0c39`.
- F-01: L4M-01 now requires an owner-controlled evidence copy outside both T0/VPS and GitHub failure domains; GitHub-unavailable readback is part of the PASS condition.
- F-02: L4M-03 now requires a separately authenticated owner-controlled latest-head/monotonic anchor for freshness; without it freshness is UNKNOWN/NOT VERIFIED, not inferred from sequence/generation.
- F-03: L4M-06 separates cryptographic signature validity, current trust and historical trust-at-time; absent qualifying time/revocation evidence yields UNKNOWN/NOT ESTABLISHED. TSA remains non-mandatory for L4-Minimum.
- F-04: L4M-07 claims tamper-evident append-only history, not WORM/absolute immutability; it requires independently retained evidence to detect rewriting/replacement and states the storage-administrator trust assumption.
- F-05: L4M-09 now requires reviewer competence, independence from relevant lifecycle/evidence roles, conflict assessment and direct examination of exact immutable artifacts; conflicted contributors cannot issue the independent disposition.
- F-06: L4M-10 now requires every mandatory control L4M-01–L4M-10 to PASS on the same immutable baseline; no averaging or compensating control; BLOCKED/NOT VERIFIED/PENDING/UNKNOWN precedence is explicit.
- Lifecycle crosswalk added against P1.8.143 (blob `6f4451f1eb193e763970581bcd6d8a782508acfd`), P1.8.144 (`f3002ba709f874936ca434c883ef855d2f11784a`) and P1.8.152 (`e1a4d95af216e94a58fa5528850fcd0c1ff465f8`).
- RET-01 B preserved: T0 canonical data and availability/recovery copies protected; no routine/automatic/scheduled deletion. RET-02 B preserved: only enumerated noncanonical classes/individually identified copies may enter future read-only exact-object/version assessment; no class/object is automatically eligible.
- Explicitly states L4 evidence is governance/provenance evidence: no default TTL or self-deletion after read/use/verification/consumption/ACK. A retention floor is not deletion approval. Unknown obligations/copies/holds/dependencies remain RETAIN/BLOCKED.
- RET-03–RET-10, V07, V08, Restore, mutation-fence and Option C enforcement retain P1.8.152 status. P1.8.153 remains the next documented lifecycle gate and is not displaced.
- Read-back verification confirmed new blob `53591e9e3790b4d0b18787ff66bf36a3d45138e9` and key F-01–F-06/lifecycle/Option C/no-TTL/no-self-delete clauses.
- Status: DOCUMENTATION UPDATE COMPLETE; F-01–F-06 ADDRESSED IN MATRIX WORDING; lifecycle crosswalk recorded; **NOT INDEPENDENTLY REVIEWED**. P1.8.152 reviewer-control residual remains open; L4M-09 and overall L4 acceptance remain PENDING/BLOCKED as applicable.
- Tests NOT RUN; GitHub Actions NOT DISPATCHED; no workflow run/artifact. No source, schema, API, runtime, VPS, DB, data, provider, identity, key, trust-root, permission, inventory, test, restore, archive, cleanup, vacuum, compaction, backup expiry, replica removal or deletion operation.
- Option C — No Destructive Authority — remains in force; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.


## L4-Minimum Acceptance Matrix — F-07/F-08 correction and self-review (2026-11-10)

- Updated the existing file in place: `docs/evidence/p1-8/L4-MINIMUM-PROVENANCE-ACCEPTANCE-MATRIX.md`; no new matrix, branch or parallel document.
- Update commit: `e3fe05ec85f20c58e9b8b0513bf016f7d4b6f4fc`.
- New matrix blob SHA after read-back: `8f9e34acb4e9ae0b89d5e7163566ab2982d99c63`; previous blob SHA: `53591e9e3790b4d0b18787ff66bf36a3d45138e9`.
- F-07: latest-head/monotonic anchor is explicitly included in L4M-01 owner-custody inventory and must be retained/readable outside both T0/VPS and GitHub failure domains. L4M-03 binds freshness to the exact anchor digest and independently verified custody/readback. G1/G2 require anchor readback under T0/VPS outage, GitHub outage and simultaneous outage; missing/stale/rolled-back/inaccessible anchor yields UNKNOWN/NOT VERIFIED.
- F-08: evidence baseline must be frozen and identified by canonical manifest digest and closure record before independent review. Reviewer disposition is a separate linked evidence record referencing the exact baseline ID/digest; it is not inserted into or used to mutate the frozen baseline. Aggregate verdict binds the frozen baseline and its separate review disposition.
- Same-session self-review/read-back: F-07 anchor custody binding, exact digest binding, outage scenarios and fail-closed semantics checked; F-08 freeze-before-review, separate digest-bound disposition, no baseline mutation, evidence package fields and sequencing checked. Required policy constraints F-01–F-06, RET-01/02, no-default-TTL/no-self-delete and Option C remain present.
- Self-review is NOT independent. Matrix status remains **NOT INDEPENDENTLY REVIEWED**; qualifying L4M-09 review PENDING. L4 technical/operational acceptance remains BLOCKED / NOT VERIFIED.
- Tests NOT RUN; GitHub Actions NOT DISPATCHED; no workflow run/artifact. No source, schema, API, runtime, VPS, DB, data, provider, identity, key, trust-root, permission, inventory, restore, archive, cleanup, vacuum, compaction, backup expiry, replica removal or deletion operation.
- Option C — No Destructive Authority — remains in force; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Next: obtain a genuinely qualifying independent review of the exact revised matrix and related evidence; do not promote any acceptance status based on this self-review.


## L4-Minimum follow-on self-review — F-09 audit/matrix version lineage (2026-11-10)

- Cross-checked current Acceptance Matrix against the bounded read-only audit report and personal-scope decision.
- Self-review finding F-09: the audit report is a historical snapshot and explicitly references the then-current matrix blob `f39bef0c391e13a3656130f0e74f0e7a385b0c39`, while the current matrix had advanced through F-01–F-08 to blob `8f9e34acb4e9ae0b89d5e7163566ab2982d99c63`. This is historically accurate, not a defect in the old report, but the review package needed an explicit version-lineage rule to prevent treating the old matrix as current.
- Corrected the existing matrix in place; no new matrix/report/branch. Update commit: `12fe524c1434dc3fe22bcdaaa791074b9b2e376a`; new matrix blob after final verdict read-back: `990efb74810059754a6d9eaf6564a025dabb3431` (intermediate blob `4de23da056b96e0eaf4a3525ad221195da6ed977`). The current verdict line explicitly records F-01–F-09 as addressed in wording while preserving NOT INDEPENDENTLY REVIEWED.
- Added evidence-package requirement for a review-input lineage manifest with exact SHA-256 values; explicitly preserves the historical audit report unchanged; requires reviewer to examine both the exact audit report and current matrix and reconcile their lineage. Review sequencing now freezes the exact combined review-input baseline before independent review.
- Self-review: F-09 wording and lineage binding added; F-07/F-08 requirements retained; RET-01/02, no-default-TTL/no-self-delete and Option C retained. This is same-session self-review only, NOT independent review.
- Current matrix status remains **NOT INDEPENDENTLY REVIEWED**; L4M-09 remains PENDING; overall L4 implementation/operational acceptance remains BLOCKED / NOT VERIFIED.
- No tests, GitHub Actions, source/runtime/VPS/database/data/key/trust-root/permission/provider/restore/archive/cleanup/deletion operations. Option C remains in force; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Next: freeze a manifest for the exact review inputs and obtain a genuinely qualifying independent review. The handoff's P1.8.153 reference still has no exact artifact path/identity in the inspected handoff text; do not invent or execute that gate until its exact record is located and reconciled.


## P1.8.153 preparation — P1.8.152 bounded self-review and artifact identification (2026-11-10)

- Located the exact next-gate source: `docs/evidence/p1-8/P1.8.152-retention-and-lifecycle-residual-finding-reconciliation.md`, blob SHA `e1a4d95af216e94a58fa5528850fcd0c1ff465f8`. P1.8.153 is described as a future independent review artifact; no P1.8.153 file exists in the inspected `docs/evidence/p1-8/` directory listing. Do not fabricate a completed independent review.
- Read-only self-review cross-checked P1.8.143 (`6f4451f1eb193e763970581bcd6d8a782508acfd`), P1.8.144 (`f3002ba709f874936ca434c883ef855d2f11784a`), P1.8.146 (`5efb0ae86d88ede5627ed7b77322463c39fb737e`), P1.8.147 (`4bc99b2886fce32efd54efb2294732655fc63253`), P1.8.148 (`baea1eb363a06ea7e804fe986777b31e9b693513`), P1.8.149 (`cce7aa0bf9c7b6048b61ef5c436433e3ac0c01c4`), P1.8.150 (`f23fbcfdc85c82b95271d835a1e452e4a9863db2`) and P1.8.151 (`64902f09d0f5576a47da44dbb194a56e18d727c2`).
- Self-review findings: (1) P1.8.152's RET-01 B / RET-02 B, no-TTL/no-automatic-deletion, protected T0/ledger/governance records and Option C boundaries align with P1.8.143–144; (2) its LDA-01 through LDA-09 statuses are consistent with the cited scope and evidence; (3) P1.8.147 expressly leaves IR147-01 open; P1.8.149 says substantially addressed but not closed; P1.8.151 explicitly closes IR149-01 only and does not explicitly issue a separate closure disposition for IR147-01. Therefore P1.8.152 is correct to keep IR147-01 unresolved pending a reviewer who directly examines the combined chain and expressly decides closure; (4) actual reviewer identity, independence and competence remain NOT VERIFIED; (5) 87 lifecycle negative vectors, runtime inventory, adapter, restore and mutation enforcement remain NOT VERIFIED/NOT RUN as recorded.
- No contradiction found that justifies changing P1.8.152 in this self-review. The residual IR147-01 status must not be silently promoted to CLOSED by inference from IR149-01.
- This is same-session self-review only, NOT independent review and NOT P1.8.153. A genuinely qualifying reviewer must examine exact immutable artifacts, evidence role/conflict declarations and competence for the claim; if unavailable, status remains INDEPENDENT_REVIEW_REQUIRED / BLOCKED.
- No tests, Actions, runtime/identity/permission/provider inventory, source/runtime/database/data/key/trust-root changes, restore, fault injection, archive, cleanup, vacuum, compaction, backup expiry, replica removal or deletion. Option C remains in force; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Next: obtain the qualifying independent review of P1.8.152 and the P1.8.143–P1.8.151 chain, explicitly decide IR147-01 closure or retain it OPEN with exact missing criteria. Do not write the independent review disposition as the same reviewer/contributor.


## Follow-on self-review correction — matrix self-versioned SHA (2026-11-10)

- Second-pass self-review found SR-02 in the F-09 wording: the matrix embedded blob SHA `8f9e34acb4e9ae0b89d5e7163566ab2982d99c63` as the purported current matrix, but the F-09 update had already changed its blob to `990efb74810059754a6d9eaf6564a025dabb3431`. This is a self-versioned-document reference defect; the embedded hash became stale as soon as the matrix changed.
- Corrected the existing matrix in place. It no longer hard-codes a purported current matrix SHA. It requires the external frozen review-input manifest to identify the exact matrix blob SHA, while retaining the historical audit report SHA `cfecb7428508adf23e6b9e71dc0dfe1e0e38080c` and its historical matrix reference `f39bef0c391e13a3656130f0e74f7a385b0c39`. The audit report remains unchanged.
- Matrix correction commit: `4058e166ddf14d3480b9aa5f14d2c6e9ecd233be`; matrix blob after read-back: `ed3056d81edfaf163205a172cf5ad22e230d7b41`.
- Read-back checks: no self-referential current SHA; external frozen manifest authoritative; historical audit SHA/reference retained; audit report unchanged; F-01–F-09 verdict still NOT INDEPENDENTLY REVIEWED; lifecycle/Option C protections retained. Same-session self-review only.
- Scope limitation noted: the prior statement that LDA-01–LDA-09 were “consistent” is a documentary cross-check of P1.8.152 against the P1.8.141 baseline, not an operational revalidation; P1.8.141 explicitly prohibits treating its static mapping as runtime inventory or execution proof. No operational evidence was inspected.
- No tests, Actions, runtime/provider/personnel/identity/permission inventory, source/runtime/database/data/key/trust-root/permission changes, restore, fault injection, archive, cleanup, vacuum, compaction, backup expiry, replica removal or deletion. Option C remains in force; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Status: SR-02 CORRECTED IN WORDING; matrix remains NOT INDEPENDENTLY REVIEWED; L4M-09 PENDING; overall L4 BLOCKED / NOT VERIFIED. Next: freeze the external review-input manifest and obtain a qualifying independent reviewer; do not infer reviewer availability or identity.


## T0 Evidence Object / Checkpoint Contract v1 — initial contract draft (2026-11-10)

- User authorized moving to Evidence Object/Checkpoint Contract work. Read the current handoff first; starting branch HEAD was `e010beefa1ddc5469ae5be4c5dc9a3f8b676a541`.
- Added `docs/architecture/T0_EVIDENCE_OBJECT_CHECKPOINT_CONTRACT_V1.md` in the existing branch. Commit: `c63c98dccb43789964c7945943027c288ccddd76`; current file blob SHA after read-back: `b58a02356b6c87c010d4ff2298aaa519b2cba1b7`.
- Contract defines Evidence Object, Checkpoint Manifest, per-timeframe candle partition commitments, snapshot boundary, durability evidence, canonical serialization candidate, detached signature envelope, owner-controlled signing boundary, custody receipt, offline verification, independent latest-head/rollback anchor, orthogonal status dimensions, aggregate verdict and 20 minimum negative cases.
- Explicitly preserves distinctions: digest != authenticity; signature != trusted historical time; API `datasetVersion` != checkpoint; successful DB commit observation != proven host/power-loss durability; local clock != trusted time; GitHub history/Actions artifact != independent custody. 15m and 1h remain separate partitions; no fabricated global watermark.
- Contract is documentation-only. No schema/source/API/Feeder/writer changes, no tests, no Actions, no runtime/VPS/DB/data/provider/identity/key/trust-root/permission operation. No TSA/WORM provider selected or contacted. No restore/fault injection/archive/cleanup/vacuum/compaction/backup expiry/replica removal/deletion.
- Open decisions remain: canonicalization vectors/library, DB snapshot mechanism, durable commit receipt, issuer/signer authority, algorithm/key custody lifecycle, independent custody/readback, latest-head anchor, offline verifier packaging, retention/hold mapping, and TSA necessity for any specifically scoped historical-time claim.
- Status: CONTRACT DRAFTED; NOT IMPLEMENTED; owner decisions and independent review required. L4M-09 remains pending; overall L4 remains BLOCKED / NOT VERIFIED. Option C — No Destructive Authority — remains; T0 canonical/recovery data protected; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Next bounded step: contract consistency review against T0 Candle Contract v1, P1.8.67–P1.8.78, L4-Minimum matrix and lifecycle decisions; then resolve owner decisions before synthetic fixtures or source implementation.


### Contract self-review correction — eliminate recursive manifest binding (2026-11-10)

- Same-session static self-review found SR-01: the initial Checkpoint Manifest table embedded `manifest_object_ref` inside the manifest while also requiring the Evidence Object digest to hash the serialized manifest. That creates a recursive/self-referential digest dependency.
- Corrected §4.2: manifest object ID/digest binding is external, in the Evidence Object descriptor/receipt; the serialized manifest does not contain its own object ID/digest. Clarified that `content_root` commits only to canonical partition descriptors and ordered row commitments, excluding the external descriptor, signature envelope, custody receipt and verification records.
- Correction commit: `b6cc97b769d0c348bb6b8065e13da343601fbe35`; contract blob after read-back: `9e89e69de69fbe352bfef9d2d5107a719117294f`.
- Re-review confirms the self-reference is removed and the object digest can be computed over finite canonical bytes. Remaining contract gaps are intentionally OPEN: exact content-root construction/test vectors, serializer profile implementation, backend snapshot mechanism and durability receipt semantics, issuer/signer/custody/anchor authority. No source implementation is implied.
- Documentation-only; no tests/Actions, runtime/VPS/DB/data/provider/identity/key/trust-root/permission operations or destructive actions. Option C remains; paper-only; `AI_EXECUTION_ENABLED=false`.
- Status: SR-01 CORRECTED IN WORDING; contract remains DRAFT / NOT IMPLEMENTED / NOT INDEPENDENTLY REVIEWED.


### Contract consistency crosswalk — TSA boundary (2026-11-10)

- Cross-checked the draft against P1.8.67/P1.8.68 and P1.8.77/P1.8.78. Added §13.1 to preserve the explicit distinction between A (dataset/checkpoint proof-of-existence) and B (P1.8.36/V07 exact signed-object historical verification).
- Explicitly records that the owner has not selected A, B or two separately versioned evidence products; the new contract does not authorize TSA requests and does not claim P1.8.36 compatibility merely by defining a signature envelope.
- Preserves P1.8.67 invariants: TSA optional/asynchronous/outside T0 write path; only timestamp after separately proven durable commit; TSA failure/UNKNOWN cannot roll back a valid T0 data commit.
- Latest contract update commit: `ff6a75bda9037eec3d15f5de3518681da002c0ab`; latest contract blob: `1973191e79c36c12424b06bd66b3796c948523f0`.
- Static consistency review only; no independent reviewer, tests, Actions, provider, runtime, key, trust-root or destructive operation. Contract remains DRAFT / NOT IMPLEMENTED / NOT INDEPENDENTLY REVIEWED.


## T0 Evidence Object / Checkpoint Contract v1 — G0.2 exact candle source mapping (2026-11-10)

- Scope: documentation-only source mapping in the existing branch; no standalone artifact titled “T0 Candle Contract v1” was found. The executable Candle value object/serializer, SQLite schema/read path, PostgreSQL migration/read path and README together define the inspected candle contract.
- Inspected source blobs:
  - market_data/store.py: 4e1b0c54bd56455abe5be0e5c7d0807e63e0bc78
  - market_data/storage.py: 13fe1ae01ebb5318b69e69eef3e512d207f74c49
  - market_data/postgres.py: 2fe27fe2d066dda0c192a381b72d27404487b800
  - market_data/migrations/001_initial_timescale.sql: 777d884d217004569e97821a76b506572ee8f5b7
  - market_data/README.md: 660a2f0f4f88c0de4fa8c1be3c4af96df282de0e
  - P1.8.77 source map: 35057494b5b3c240e636cfdea3505e8870361ca5
  - P1.8.78 static review: 4794a531befa0bf1ce2fbb428ae466fcb6a280a9
- Physical columns are exchange, market_type, symbol, timeframe, open_time_ms, OHLCV, available_at_ms; PostgreSQL also has nullable ingestion_batch_id, not populated by the inspected canonical writer. closeTimeMs, isClosed, availabilityKind, quality and source are serializer-derived, not persisted columns. 15m and 1h remain separate partitions.
- Read semantics: aligned bounded [startMs,endMs), optional asOfMs filters available_at_ms, sorted open_time_ms, coverage/gaps derived from interval membership; datasetVersion is a response-window digest, not a checkpoint. PostgreSQL read uses REPEATABLE READ READ ONLY; SQLite read_window uses a read transaction. This does not establish a multi-timeframe checkpoint snapshot or durability proof.
- G0.2 finding F-01: RESOLVED for the inspected source baseline. No live DB/runtime parity inferred. Remaining G0 gaps include F-02 canonical bytes/content-root and F-03 exact completeness oracle; snapshot/durability and other owner decisions remain open.
- Contract update commit: 2451b2a452ad1a36fb6aae0b8bda1cc88790c7f1; contract blob after read-back: 00e0281eba256523d324b8762f4798fcbae3ef20.
- Self-review: source/readme/migration field mapping cross-checked; persisted versus derived fields distinguished; no schema fields invented. Same-session static review only, NOT independent review.
- Tests: NOT RUN (documentation-only). GitHub Actions: NOT DISPATCHED. No source/schema/runtime/VPS/database/data/provider/identity/key/trust-root/permission operations. No TSA/WORM calls, restore, fault injection, archive, cleanup, vacuum, compaction, backup expiry, replica removal or deletion.
- Authorization: user granted automatic approval within G0–G3. This does not authorize G4 implementation or G5 runtime/provider operations. Option C remains; AI_EXECUTION_ENABLED=false; paper-only; no live orders.
- Status: G0.2 PASS (source mapping only); G0 overall PARTIAL/OPEN; contract NOT IMPLEMENTED; independent review required. Next: G0.3 canonical byte profile and exact canonicalization vectors, followed by G0.4 completeness oracle.



## T0 Evidence Object / Checkpoint Contract v1 — G0.3 canonical byte profile (2026-11-10)

- Under the user's automatic-approval delegation for G0–G3, selected RFC 8785 JCS with strict T0 schema restrictions as profile T0-JCS-1. No production library/runtime selected.
- Canonical wire rules: UTF-8 JCS without BOM/trailing newline; reject duplicate keys/invalid Unicode/unknown schema fields; no JSON numeric values; logical integers and timestamps serialize as canonical decimal strings; decimals use a strict nonnegative normalized grammar; null/omission and array order are schema-fixed.
- Row identity commits only persisted candle fields (market identity, timeframe, open_time_ms, OHLCV, available_at_ms); serializer-derived closeTimeMs/isClosed/availabilityKind/quality/source and nullable/unpopulated ingestion_batch_id are excluded from physical row identity.
- Defined domain-separated SHA-256 for Evidence Object, candle row leaf, empty row tree, Merkle parent, partition leaf and checkpoint content_root; odd Merkle nodes are promoted unchanged. 15m and 1h remain separately ordered partitions.
- Normative single-row JCS vector: 193 bytes; row leaf ca1d9eae5d9ae2022ccfe5226cc06f3429f5c1428e04e1d1c54b1f83c56fa32f; empty row-tree root ccf8ef877bb093aa73ae77a02b9200985c41519920c83b515a0a4a99561e73f7.
- Contract design commit: ab683ea8b576a8a63bbb7f3f2d505fdee8615366; initial G0.3 blob cc64f3eda4ce84b39a949f813fe04805fcfef424. Same-session consistency self-review found and corrected conflicts with the earlier generic digest definition and row commitment description. Correction commit: a8eabc07613e2da8802e1a672eb83e4afe005a30; contract blob after correction: 42afa35b0d8d902520c567190361985bb58920a9.
- G0.3 disposition: F-02 RESOLVED AT CONTRACT-DESIGN LEVEL. Production JCS library and full cross-implementation vector suite remain NOT SELECTED/NOT VERIFIED; executable conformance deferred to G2. No code/tests/Actions were run.
- G0.2 remains PASS for source mapping only. F-03 completeness oracle remains OPEN; SQLite/PostgreSQL multi-partition snapshot and durable commit receipt remain open. G0 overall PARTIAL/OPEN.
- No source/schema/runtime/VPS/database/data/provider/identity/key/trust-root/permission operation; no TSA/WORM calls, restore, fault injection, archive, cleanup, vacuum, compaction, backup expiry, replica removal or deletion. Option C remains; AI_EXECUTION_ENABLED=false; paper-only; no live orders.
- Next: G0.4 define exact completeness oracle and its boundary conditions. G0.3 is contract-design/self-review only, NOT independently reviewed.



## T0 Evidence Object / Checkpoint Contract v1 — G0.4 completeness oracle (2026-11-10)

- Defined exact partition domain for 15m/1h using aligned half-open [start_ms,end_ms), interval Δ and expected set E={start_ms+k×Δ | 0≤k<N}.
- Defined row membership and validation: exact market/timeframe identity, in-range/aligned timestamps, unique ascending rows, exact exclusive close boundary, available_at_ms not before close, Candle validation; no fill/interpolation/synthetic rows or silent correction.
- Verdicts: COMPLETE iff returned set equals E; INCOMPLETE iff valid rows are a strict subset; INVALID for malformed/duplicate/off-grid/out-of-range/invalid rows; UNKNOWN for missing bytes, truncation, read/page failure or unestablished required snapshot. INVALID cannot be downgraded.
- Defined maximal aligned gap coalescing and exact missing_count arithmetic; as_of_ms is part of selection semantics and missing reasons are not inferred.
- Checkpoint COMPLETE requires every partition COMPLETE and snapshot consistency PASS. M15/H1 never merged. Digest does not prove completeness.
- Normative M15 example [0,2700000), Δ=900000: {0,1800000} yields gap [900000,1800000), missing_count=1; duplicate/off-grid examples are INVALID; no rows is INCOMPLETE; missing page is UNKNOWN.
- Contract update commit: 3e4fcbaeac745939d6b67b6171c7b030f04c2342; blob after update: 5a976cc1ddf99f1d4193ee704364a95c156564df.
- G0.4/F-03 PASS at contract-design level only; executable/property-based tests deferred to G2. Snapshot consistency is separate and still open. Self-review only; not independent review.
- No code/tests/Actions, canonical DB/runtime/VPS/data/provider/key/trust-root/permission access or mutation. No TSA/WORM, restore, fault injection or destructive operation. Option C remains; AI_EXECUTION_ENABLED=false; paper-only; no live orders.
- Next: G0.5 define backend-specific multi-partition snapshot protocol and its observable evidence.



## T0 Evidence Object / Checkpoint Contract v1 — G0.5 snapshot and G0.6 durability boundary (2026-11-10)

- G0.5 defines one backend/database identity and one pinned read-only transaction for all partitions. SQLite profile: one read-only connection, explicit BEGIN, first SELECT pins snapshot, all timeframe/range queries on same connection; snapshot token NOT_EXPOSED. PostgreSQL profile: one connection, REPEATABLE READ READ ONLY transaction, same connection for all partitions; record server/database/schema identity and only record a snapshot token if actually exposed.
- Current read_window facades open their own connection/transaction per call and are therefore insufficient for a multi-partition common snapshot when invoked separately. No runtime implementation or DB access occurred.
- G0.6 separates COMMIT_OBSERVED, COMMIT_REJECTED, COMMIT_OUTCOME_UNKNOWN, DATA_PRESENT_MATCH, DATA_PRESENT_CONFLICT and DATA_ABSENT_AT_READBACK. Matching readback cannot prove the original transaction committed.
- Defined immutable post-commit Commit Receipt binding exact operation/batch and exact-row readback. Receipt is not to be stored only in same DB/VPS/GitHub if used as independent custody evidence.
- Durability remains separate: COMMIT_OBSERVED + READBACK_MATCH do not prove process/OS/power/host/volume/provider failure survival. DURABILITY_PROFILE_VERIFIED requires exact effective config, provider/storage failure-domain semantics, disposable fault testing, independent review and preserved evidence.
- Selected TSA use case A remains blocked from submission until a qualifying DURABILITY_PROFILE_VERIFIED receipt exists and separate G5/provider authorization is granted. TSA remains asynchronous and outside T0 ingestion.
- Contract update commit: f99fcb12e5a3b184465b353c06b7a4ea27af9ab4; blob after update: 081a48094e8ae366c5e25304f7e17f1396c68e4a.
- G0.5/G0.6 are contract-design specifications only; implementation and deployment qualification NOT VERIFIED. No tests/Actions, canonical DB/runtime/VPS/storage/provider/key/trust-root/permission operation, TSA/WORM, restore, fault injection or destructive action. Option C remains; AI_EXECUTION_ENABLED=false; paper-only; no live orders.
- Next: G1 role/authority decisions for A (issuer, absent signer, independent custodian, latest-head anchor, offline verifier, retention boundary) without selecting or provisioning providers.



## T0 Evidence Object / Checkpoint Contract v1 — G1 owner decisions for A (2026-11-10)

- G1 architecture decisions recorded under user's G0–G3 automatic-approval delegation:
  - Initial evidence subject A — Dataset/checkpoint proof-of-existence.
  - B / P1.8.36 signed-object historical verification deferred to a separate future contract/version.
  - A has no signer/signature envelope; no signer authenticity or owner-intent claim.
  - Issuer is a dedicated read-only checkpoint-builder role, distinct from T0 writer, signer, custodian, anchor administrator and verifier.
  - Custody must be owner-controlled and outside T0/VPS and GitHub failure domains, with exact-object readback; provider/account/region not selected.
  - Latest-head anchor is separate, owner-controlled, authenticated and monotonic; provider/implementation not selected.
  - Offline verifier is standalone and deterministic; missing trust/policy/anchor material remains UNKNOWN.
  - Independent reviewer must be genuinely separate; same-session self-review is not independent.
  - RET-01 B / RET-02 B, Option C, no default TTL and no automatic delete-after-use remain unchanged.
- Policy crosswalk: P1.8.80 blob a38710c9d01e5409ce989cc73f791c94bc73773f; L4-Minimum matrix blob ed3056d81edfaf163205a172cf5ad22e230d7b41. Dedicated WORM and multi-TSA quorum are not L4-Minimum requirements; independent custody/readback, offline verification and independent review remain required.
- Contract update commit: 661e2392630be0134a94d18e09fff14c8b6eaec7; blob after update: daedf2fe41b4d590ad755f56898d157a9af3e878.
- G1 disposition: PASS for architecture/claim/role boundaries. Provider/account/region/runtime identity/anchor/custody technology/TSA provider are intentionally not selected; no resource provisioning or external call.
- G0.2 source mapping PASS; G0.3/G0.4 contract-design PASS; G0.5/G0.6 protocols specified but not implemented/qualified. Current backend durability NOT VERIFIED. G0 static crosswalk/closure and G3 independent review remain outstanding.
- No code/schema/runtime/VPS/database/data/provider/identity/key/trust-root/permission operation; no tests/Actions; no TSA/WORM, restore, fault injection or destructive operation. Option C remains; AI_EXECUTION_ENABLED=false; paper-only; no live orders.
- Next: G2 synthetic-only fixtures and deterministic negative/conformance tests, strictly isolated from canonical T0 and all external providers; independent G3 review remains a separate gate.



## T0 Evidence Object / Checkpoint Contract v1 — G2 synthetic-only implementation (2026-11-10)

- Added isolated synthetic reference oracle: synthetic_evidence/t0_checkpoint_contract.py, commit 51f4269b9bb3877ecfe571ddaae829e44ee48629, blob f8f4d5d0917c8b1f2a58762418ab1f4bf16523e0.
- Added deterministic test suite: synthetic_evidence/test_t0_checkpoint_contract.py, commit 7e86e40cd078fe9b6e5322097152ec078e19b67b, blob a6578b3f1c2687b894182c5256b6f9b0d7911a51.
- Added dedicated offline GitHub Actions workflow: .github/workflows/t0-evidence-contract-g2.yml, commit a33a99bb26c569127aea9d153f95795df2c9c045, blob 5e22648c38fd3c6e631f912010de1489bb78f9b5.
- The synthetic module implements restricted JCS serialization, strict parsing, Candle row validation, object/row/partition/checkpoint digest roots, Merkle odd-node promotion, and partition completeness oracle. No market_data import or external integration.
- Local development copy: TDD RED when module absent; draft synthetic suite then 28/28 PASS. This is not an exact-commit checkout run. Final GitHub blobs were fetched back and hashes matched.
- Workflow commit combined-status query returned an empty status list; workflow run ID and artifact were not established. Exact committed-SHA Actions result remains NOT VERIFIED.
- G2 status: IMPLEMENTATION ADDED; LOCAL DRAFT TESTS PASS; EXACT COMMITTED-SHA/ACTIONS NOT VERIFIED; G2 NOT CLOSED. No tests against canonical T0 DB, no source/schema/runtime/VPS/provider/key/trust-root changes.
- Contract G2 record commit: f333533455eaf26f73b9e44a8cf162ec6ac1cfe0; contract blob: df828c878958b6eeaf4e6f2d6ca6ec2886b9449b.
- No live orders; AI_EXECUTION_ENABLED=false; paper-only; Option C remains. G4 and G5 not authorized.
- Next: self-review G2 artifacts and prepare a frozen G3 review-input manifest; no independent review is claimed or inferred.



## T0 Evidence Object / Checkpoint Contract v1 — G2 self-review corrections (2026-11-10)

- Self-review finding G2-SR-01: the synthetic completeness oracle returned UNKNOWN immediately when input_complete=false, masking known malformed rows. Corrected to validate every available row first; known malformed rows remain INVALID, while otherwise-valid partial input is UNKNOWN. Regression test added.
- Self-review finding G2-SR-02: prior mixed-timeframe test used a 1h row timestamp not aligned to 1h, so it could pass for the wrong reason. Corrected to use a valid aligned 1h row and assert the mixed-timeframe rejection specifically.
- Self-review finding G2-SR-03: checkpoint_object_digest accepted arbitrary bytes despite the canonical-byte contract. It now verifies strict canonical bytes before computing the digest.
- Test correction commit: 8882ef2e31d55eb726f9322a57096fa544797c2b; test blob: beffd8c4a6cb2682c9fe0acb09cd2b182c2fde7c.
- Source correction commit: 8affc8b9aa12f17a969bc34c395b3b66b5871829; source blob: 9efd800189e15d35e231530d703499d40d9d7e5d.
- Local 28/28 test result predates these three corrections and MUST NOT be attributed to the final blobs. No post-correction exact-SHA test run has been verified. Combined commit status for source correction SHA returned no status checks; Actions run/artifact remain NOT VERIFIED.
- Contract G2 update commit: 3ae31cace87ae1596a126ce83618c7455021c9f3; contract blob: 0d98a3dcbb0d403b213b5efcae0c882ac5461578.
- Status remains G2 NOT CLOSED. No canonical T0 DB/data, runtime/VPS, provider, identity/key/trust-root, TSA/WORM, restore, fault injection or destructive action. Option C remains; AI_EXECUTION_ENABLED=false; paper-only; no live orders.
- Next: freeze exact G3 review inputs and request a genuinely independent review. Do not claim G3 PASS or use self-review as a substitute.



## T0 Evidence Object / Checkpoint Contract v1 — G3 review package frozen (2026-11-10)

- Prepared exact review-input manifest: docs/evidence/t0/T0_EVIDENCE_CHECKPOINT_G3_REVIEW_INPUTS_2026-11-10.md.
- Manifest commit: 888f0033e669bee68894d7243a9aa579ace11b57; blob after read-back: c5ee25d46440bb391dd34b164a497aa64130b83d.
- Frozen baseline commit before manifest: 593d4c7a1362aef47ce47f3cd07df75d73dc585e.
- Manifest pins exact blobs for contract, G2 source/tests/workflow, T0 Candle source/migration/README, P1.8.67/.68/.77/.78, P1.8.80, L4-Minimum matrix and P1.8.152.
- Review instructions require reviewer identity, competence, conflicts and independence declaration; exact blob inspection; independent RFC 8785 conformance review; completeness/snapshot/durability/authority/retention review; and explicit finding dispositions.
- G3 remains PENDING / NOT VERIFIED. No qualifying independent reviewer identity or competence was established, and no independent review report exists. This manifest is not a review report, independent custody or PASS certificate.
- G2 remains NOT CLOSED: post-correction exact-SHA test execution and GitHub Actions run/artifact NOT VERIFIED. G4/G5 remain NOT AUTHORIZED.
- No canonical DB/data/runtime/VPS/provider/identity/key/trust-root/TSA/WORM/restore/fault-injection/destructive operation. Option C remains; AI_EXECUTION_ENABLED=false; paper-only; no live orders.



## T0 Evidence Object / Checkpoint Contract v1 — G2 exact-SHA Actions verification (2026-11-10)

- Read-only GitHub verification record: `docs/evidence/t0/T0_EVIDENCE_G2_EXACT_SHA_ACTIONS_VERIFICATION_2026-11-10.md`.
- Evidence record commit: `da0bbb8c0a965ac1b6c79cae6beaddffa5365bd6`; blob: `93ca198752c9d0eff30a64572f02d3ac3debc231`.
- Verified exact GitHub blobs: source `9efd800189e15d35e231530d703499d40d9d7e5d`; tests `beffd8c4a6cb2682c9fe0acb09cd2b182c2fde7c`; workflow `5e22648c38fd3c6e631f912010de1489bb78f9b5`; G3 manifest `c5ee25d46440bb391dd34b164a497aa64130b83d`.
- G2 workflow run `42672254786` for test-correction SHA `8882ef2e31d55eb726f9322a57096fa544797c2b`: FAILURE, API reports 0 jobs / 0 artifacts.
- G2 workflow run `42672280358` for final source-correction SHA `8affc8b9aa12f17a969bc34c395b3b66b5871829`: FAILURE, API reports 0 jobs / 0 artifacts.
- Run log endpoint returned empty content through available read interface; failure stage/reason NOT ESTABLISHED. No test verdict can be inferred. Combined status contexts for source/test/workflow/head were empty. Historical P1.8 run `42557957929` is a different workflow and cannot substitute.
- Disposition: blob identity PASS; exact final-tree test execution NOT VERIFIED; G2 Actions BLOCKED; G2 NOT CLOSED; G3 PENDING / NOT VERIFIED. No independent reviewer report exists.
- No canonical T0 DB/data/runtime/VPS/provider/identity/key/trust-root/permission operations; no provider calls, restore, fault injection, destructive actions or workflow dispatch. Option C remains; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders. G4/G5 not authorized.
- Next: establish why the G2 workflow terminates before creating jobs/artifacts. Correct only the isolated G2 workflow if a concrete cause is identified; then require a successful exact-source run and retained artifact before closing G2 or proceeding to G3 disposition.


## T0 Evidence Contract G2 — post-incident status (2026-11-10)

- Public GitHub Status currently reports All Systems Operational; the Nov 9 Webhooks/Actions incident is listed as resolved. This supports recovery of the platform but does not retroactively repair failed workflow runs.
- Read-only recheck: G2 runs 42672254786 (head 8882ef2e31d55eb726f9322a57096fa544797c2b) and 42672280358 (head 8affc8b9aa12f17a969bc34c395b3b66b5871829) remain FAILURE, each with 0 jobs and 0 artifacts.
- Branch HEAD at this update: 054a7acdf589317252feb2392dc18c9c0be905d0. G2 workflow blob remains 5e22648c38fd3c6e631f912010de1489bb78f9b5; it contains one synthetic-only job, compile, unittest, and always-upload evidence steps. No workflow configuration defect has been established.
- User-supplied GitHub Status screenshot shows an incident with Actions and Checks API and elevated errors; timing aligns with failed run creation. Exact internal root cause remains NOT ESTABLISHED.
- No source/workflow change, workflow dispatch/rerun, canonical DB/data, runtime/VPS, provider, credential, identity/key/trust-root, restore, fault-injection or destructive action performed.
- Status: GitHub platform incident resolved; historical G2 runs remain unusable; exact final-source SHA test execution NOT VERIFIED; G2 NOT CLOSED; G3 PENDING / NOT VERIFIED.
- Next: obtain a fresh successful exact-SHA G2 Actions run after platform recovery and retain its source-SHA/test artifact. No dispatch/rerun was initiated in this step. G4/G5 remain NOT AUTHORIZED; Option C remains; AI_EXECUTION_ENABLED=false; paper-only; no live orders.


## T0 components outside L4-Minimum scope audit (2026-11-10)

- Read-only scope audit: `docs/evidence/T0_COMPONENTS_OUTSIDE_L4_MINIMUM_AUDIT_2026-11-10.md`.
- Audit commit: `1b1a1643a25e54e21d29bc89b56b3953198ce76c`; blob verified on branch: `7bfc509b9eb918750b3a25acc18f8d4f989d387f`.
- Reviewed controlling L4 matrix, existing T0 L4 audit and adversarial review, TSA/WORM audit, T0 checkpoint contract, Shared Data Foundation, HTTPS front-door design, PostgreSQL role/provider decision, PostgreSQL atomic writer proposal, P1.8.80 and P1.8.152.
- Classified TSA/RFC3161, multi-TSA quorum, dedicated WORM/Root A-Root B topology, independent market-data source corroboration/multi-venue consensus, paid assurance and commercial controls as outside L4-Minimum. HTTPS front door, PostgreSQL provider/role qualification, D2-D4 durability and production DR are separate T0 engineering/operations gates, not L4 provenance controls. Retention floors and automated lifecycle mutation remain separate and non-executable under Option C.
- Reaffirmed mandatory L4M-01–L4M-10 controls; exclusions do not waive independent evidence custody/readback, owner signing separation, exact-object/freshness anchor, offline verification, key/trust lifecycle, tamper-evident history, claim discipline or genuinely independent review.
- Audit status: documentary scope classification PASS; no independent review, tests, workflow dispatch, runtime/VPS/DB/provider/key/permission operation or destructive action. L4 implementation/operational acceptance remains BLOCKED / NOT VERIFIED.
- No source/runtime changes. Option C remains; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.


## T0 Scope Minimization Review (2026-11-10)

- Read-only source/document scope review: `docs/evidence/T0_SCOPE_MINIMIZATION_REVIEW_2026-11-10.md`.
- Review commit: `ae2c20ecc26c653eed0af56594732f4a0f579814`; blob verified on branch: `43c919521352cd3c2b00ba6da891a8675a6c5ed6`.
- Proposed active T0 baseline: Binance USD-M BTCUSDT M15/H1 canonical SQLite, fenced single writer/lease, fail-closed recovery/integrity, bounded read-only Candle API, T2 contract and core regression tests.
- Classified PostgreSQL provider/migration, Kraken Spot research, public HTTPS/DNS/proxy, checkpoint G0-G3 expansion, TSA/WORM/Root A-Root B, lifecycle registry/scheduler/archive/retention implementation, and Daily Baseline/dual reconstruction integration as parked/separate tracks. No deletion or source changes.
- Protected core: canonical market identity, candle validation, fenced writer/lease, fail-closed recovery, read-only boundary, API bounds/auth, tests, evidence provenance, canonical data/recovery copies and no automatic delete-after-use.
- Findings SM-01–SM-10 cover active-scope inflation, market-domain mixing, evidence expansion, optional backend complexity, premature public API, lifecycle proliferation, forward-evidence conflation, recovery-domain leakage, false simplification and premature cleanup.
- Status: documentary/source inventory PASS; active T0 baseline PROPOSED pending owner ratification; dependency/call graph PARTIAL; live consumer/runtime inventory NOT VERIFIED; G2 exact-SHA NOT VERIFIED; G3 PENDING; L4-Minimum operational acceptance BLOCKED / NOT VERIFIED.
- No source/test/workflow/schema/runtime/VPS/database/provider/key/permission change; no tests, dispatch, archive, vacuum, compaction, backup expiry, replica removal, cleanup or deletion. Option C remains; AI_EXECUTION_ENABLED=false; paper-only; no live orders.
- Next: dependency map for parked candidates, followed by a separate proposal to reconcile active README/index. No removal without evidence and explicit approval.


## T0 Dependency Mapping — first-pass static inventory (2026-11-10)

- Exact inspected branch HEAD before audit commit: `cf0b66580cadfda54945e6c327f75b4cfb075bc4`.
- Added first-pass read-only map: `docs/evidence/T0_DEPENDENCY_MAPPING_FIRST_PASS_2026-11-10.md`.
- Audit commit: `42138ff2ef4b1e2741ef266cd28c4fe4a36b9f78`; audit blob after read-back: `79b6970c20365953c9250ce38fcdbda2054cdd2f`.
- Current branch HEAD after audit commit: `42138ff2ef4b1e2741ef266cd28c4fe4a36b9f78`.
- Confirmed from exact-branch source: `market_data.feeder_service` is executable entry point and composes runtime; `build_production_runtime` selects configured backend; SQLite and PostgreSQL writer paths are distinct; `sync_window` is shared by Feeder and one-shot CLI; `market_data.api` is bounded read-only API; FreqAI context uses HTTP Candle client.
- First-pass KEEP: Feeder/runtime, Candle contract/store, storage selection abstraction, write gateway, sync logic, read-only API, SQLite bootstrap/migrations, T0/T2 parity contract.
- PARK: PostgreSQL provider activation/qualification (source remains directly referenced by optional backend composition); Kraken Spot research domain (isolated source/storage/API with dedicated tests/manual gates); connectivity probe; synthetic checkpoint feature expansion after current G2/G3 gates.
- No component classified CANDIDATE FOR RETIREMENT. No deletion or disabling is supported by current evidence.
- T0 workflows reference core Feeder/gateway/recovery/API tests, T2 consumer tests, PostgreSQL/TimescaleDB tests, Kraken manual gates, connectivity probe, systemd/API integration and G2 synthetic evidence. Workflow presence does not prove current branch protection or execution success.
- Limitations: selected exact-branch blobs/workflows inspected; repository-wide call graph and live runtime/deployment consumer inventory NOT VERIFIED. GitHub code-search connector is default-branch scoped and was not treated as exact-branch proof. No tests, workflow dispatch, runtime/VPS/DB/provider access.
- Status: exact tree/blob identity PASS; core runtime composition PASS for inspected source; workflow/test map PARTIAL; global consumers NOT VERIFIED; live runtime NOT VERIFIED; L4-Minimum remains BLOCKED / NOT VERIFIED; G2 exact-SHA NOT VERIFIED; G3 PENDING.
- Option C remains; no automatic deletion/TTL/archive/cleanup/vacuum/compaction/backup expiry/replica removal. `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Next: extend exact-branch consumer search across all source/configuration files and inspect workflow triggers/branch-protection dependencies. Then prepare a separate retirement proposal; no retirement or source change without explicit approval.


### T0 Dependency Mapping — supplemental consumer boundary findings (2026-11-10)

- Supplemental audit commit: `e1351fe4eeaccbd29fc3d07dc811661ebf4bf050`.
- Updated audit blob: `13929b6aa6fa1e84412bdfaf06e5b3a6344eb638`.
- Confirmed Android chart/scanner path `MarketEngine.fetchCandles()` calls Binance Futures REST directly and MarketEngine opens Binance Futures WebSocket streams. `ChartMarketSession` and `ScannerMarketFeed` consume that MarketEngine path. Android market/chart/scanner is therefore not established as a T0 API consumer.
- Android `FiveLayerApi` has a separate configurable `baseUrl` and `candles` route, but server mapping to `market_data.api /v1/candles` is NOT VERIFIED.
- Python FreqAI bridge uses `CandleHttpClient -> /v1/candles`, the confirmed T0 HTTP consumer boundary; deployed endpoint remains NOT VERIFIED.
- T0 README explicitly states it has not replaced the existing Python bot/backtest OKX source or direct APK source.
- Implication: do not claim T0 is already the sole canonical source for all app/strategy consumers. Android/Python migration remains PARK and must preserve existing behavior until separately designed/tested/approved.
- No Android/Python source changed. No test/workflow/runtime/VPS/DB/provider operation.
- Overall mapping remains PARTIAL; complete repository-wide call graph and live deployment consumer inventory NOT VERIFIED. No retirement candidate. Next: map configurable FiveLayer API baseUrl and backend route ownership from exact-branch configuration/deployment source; then inspect remaining Python bot/backtest source references. No consumer migration or deletion without explicit authorization.


## Scope correction — Android Chart/Scanner and Python bot/backtest (2026-11-10)

- Owner clarified that Android Chart/Scanner and Python bot/backtest do **not** belong to Hệ thống 5 tầng.
- The previous handoff entry that listed them as retirement candidates/migration targets is superseded and must not be followed.
- Exclude these components and their direct Binance Futures/OKX data paths from the five-layer architecture inventory, dependency-retirement backlog and T0 migration plan. They are contextual observations only.
- Do not migrate them to T0 or remove/disable their source as part of Hệ thống 5 tầng.
- T0's confirmed Python consumer boundary remains `freqai_bridge/CandleHttpClient -> /v1/candles`; this is distinct from the out-of-scope Python bot/backtest.
- No Android/Python source, workflow, configuration, runtime, VPS, database or data was changed.
- Corrected audit commit: `f3cfb063c1b1585bb51ac6ee592fd0de34fb6e4e`; audit blob SHA: `62aecd9e14b2f966c54a57ac6ae42a588cce0180`.
- Next: continue T0 dependency mapping only for components actually inside Hệ thống 5 tầng.

## Hệ thống 5 tầng — internal dependency mapping second pass (2026-11-10)

- Exact source baseline inspected: `4063d289dbf5287d9685c628ef9386a13474a7d3`.
- Added `docs/evidence/FIVE_LAYER_INTERNAL_DEPENDENCY_MAPPING_SECOND_PASS_2026-11-10.md`; initial audit commit `85714de0dce54135f9495d431bcd0c710ccd41c5`, self-review correction commit `b853c7df00b21d8aba3886f28f46bf63ad1965f1`, final audit blob `d47755e49e0e752153eddc831ea8893ce500e009`.
- Scope is only in-system T0–T4. Android Chart/Scanner and Python bot/backtest remain OUT OF SCOPE and must not be included in five-layer retirement/migration work.
- Mapped source edges: T0 Feeder/store/API; T1 collector CSV importer and separate connection sidecar; T2 FreqAI HTTP Candle client and independent Strategy Core signal path; T3 dual-ledger paper simulation and read-only Hummingbot Order Book adapter; T4 React frontend/common API.
- Findings F5-01: FreqAI bridge uses T0 HTTP, but `pipeline.api` reads canonical storage directly for its own candle/Core/equity/quality paths. Uniform T0 API boundary is NOT ESTABLISHED.
- F5-02: T0 candle and paper ledger paths use `MARKET_DATA_DB`; logical table separation exists, but physical storage/failure-domain isolation is NOT ESTABLISHED.
- F5-03: T1 CSV importer is source-defined; active collector files and connection-sidecar integration NOT VERIFIED.
- F5-04: Hummingbot adapter is GET-only Order Book snapshot; T3 paper ledger simulates fills and has no live order client.
- F5-05: T4 Gateway is an architecture decision; edge proxy implementation/deployment NOT VERIFIED.
- F5-06: Strategy Core and general ledger source defaults include leverage 13 and entry margin 50%; these conflict with recorded conservative Core risk direction and require risk-contract reconciliation. Effective environment values NOT VERIFIED.
- F5-07 (refined self-review): common API `ledger()` constructs default MANUAL PaperLedger; evaluate path calls `record_equity()` before `submit()`. On a migrated DB, MANUAL submit rejects with `DUAL_LEDGER_MIGRATION_ACTIVE_MANUAL_WRITE_BLOCKED`; scoped record_equity rejects with `DUAL_LEDGER_ACCOUNT_EQUITY_REQUIRES_SHARED_RECONCILIATION`. The API maps ValueError to HTTP 400 INVALID_INPUT. Existing `pipeline/test_api.py` exercises a fresh legacy fixture, not a migrated DB. `dual-ledger-red.yml` does not trigger on `pipeline/**` and does not run `pipeline/test_api.py`. SOURCE-CONFIRMED incompatible call path; migrated API behavior NOT EXECUTED/runtime NOT VERIFIED. Proposed temporary-DB regression reproduction is documented in the audit; no test code or fix implemented.
- Classification: KEEP core T0–T4 modules; PARK unresolved integrations/boundaries; no in-scope component marked retirement candidate.
- No tests or GitHub Actions run, no source/schema/workflow/runtime/VPS/database/exchange changes. L4-Minimum remains BLOCKED / NOT VERIFIED; G2 exact-SHA NOT VERIFIED; G3 independent review PENDING.
- Option C remains; no automatic deletion/TTL/archive/cleanup/vacuum/compaction/backup expiry/replica removal. `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Next safe increment: implement/execute only an isolated temporary-SQLite regression test for F5-07 after approval, and update the GitHub Actions path filter/test command so `pipeline/test_api.py` is actually exercised. Do not change API/ledger behavior until the regression is demonstrated and the shared account-equity/risk contract is approved. Continue F5-01/F5-02/F5-06 design-only reconciliation separately.

## T1 producer-to-consumer dependency trace (2026-11-10)

- Static trace report: `docs/evidence/T1_PRODUCER_TO_CONSUMER_DEPENDENCY_TRACE_2026-11-10.md`; blob `7eff3b98b94296dffc48e6badd59e38ea0ca1120`.
- Inspected baseline: `5480ba9cfc138e1f629b2ba11d897dacb464a36c`.
- T1 CSV observation path is a CLI importer reading explicit CSV paths from external collector source pinned at `bc4f0ef633fbeee4a49defd72827f17162693805`; it produces a validated `OBSERVED_ONLY` JSON snapshot with per-file hashes. No in-repo scheduler/watcher or continuous capture invocation established.
- Snapshot is consumed by `pipeline.api.intelligence_snapshot()` from `INTELLIGENCE_REPORT_PATH`; decision uses trade flow only after freshness/quality gates. The snapshot remains `complete=false`, `connectionStatus=UNVERIFIABLE`; local file hashes do not prove upstream completeness or authenticity.
- Rust sidecar writer and Python validator are separate offline components; neither is integrated into pinned upstream collector, importer, feed quality or decision gating. Sidecar digest is unsigned and requires separately trusted custody.
- T1 1m kline source contract v1.1 is a distinct DESIGN ONLY / NOT APPROVED data product; it is not the current trades/funding/OI/liquidation importer and no accepted adapter/promotion path was found.
- Findings T1-DEP-01..05 cover CLI-only orchestration, observation-vs-completeness distinction, sidecar integration gap, unsigned sidecar trust boundary, and separate unimplemented 1m kline contract.
- Static source boundary trace PASS for inspected paths; complete repo/runtime inventory PARTIAL. Actual collector, CSV files, snapshot, runtime scheduling, live continuity and trusted sidecar custody NOT VERIFIED.
- No source/test/workflow/VPS/DB/collector/exchange/runtime operation performed; no tests or Actions dispatched. L4-Minimum remains BLOCKED / NOT VERIFIED. G2/G3 status unchanged. `AI_EXECUTION_ENABLED=false`; paper-only; no live orders. Option C unchanged.
- Next safe increment: static-only T4 route/auth/control dependency map. F5-07 remains explicitly deferred at user request; do not implement its regression test until reauthorized.


## T4 route / auth / control dependency mapping (2026-11-10)

- Static mapping report: `docs/evidence/T4_ROUTE_AUTH_CONTROL_DEPENDENCY_MAPPING_2026-11-10.md`.
- Report commit: `8ab4150a059802c034019e4ef3e5d8e416c44ba4`; report blob: `536dbe3beb749afe41614d04e960a89508a2ce44`.
- Exact source baseline inspected: `5309e93e59f51f561ecb5ede16d8225158b00c1b`.
- Mapped public `/health` and static `/control/*`, authenticated GET routes using `MARKET_DATA_TOKEN`, and paper control POST routes using distinct `CONTROL_TOKEN`. Backend enforces method allowlist, bounded body, constant-time bearer comparison, distinct read/control token and 30/minute shared control budget.
- React polls nine GET endpoints every five seconds; control actions use the separate control token. Tokens are held in React state in inspected source; API requests use bearer headers, omit cookies, reject redirects and cap response size.
- Finding T4-RA-01: Gateway implementation/deployment and direct-port exposure NOT VERIFIED.
- T4-RA-02: React accepts any configured HTTPS API origin; no approved Gateway host allowlist/pinning. Source-level credential-destination risk; no actual token leak established.
- T4-RA-03: frontend/development proxy use `/v1/*`, while Gateway architecture target describes `/api/t0/*`, `/api/t1/*`, `/api/t2/*`; route translation contract NOT IMPLEMENTED.
- T4-RA-04: shared static read/control secrets are separate, but per-user identity, granular roles, expiry, rotation and revocation protocol are NOT ESTABLISHED in inspected source.
- T4-RA-05: health and dashboard static shell are public; actual edge exposure NOT VERIFIED.
- T4-RA-06: paper controls remain backend-owned and Core/AI evaluation submits through PaperLedger; UI gating is not an authorization boundary. F5-07 remains DEFERRED and was not retested.
- Status: selected source/blob identity PASS; static route/method/auth inventory PASS; Gateway route contract PARTIAL; runtime topology, edge controls and credential custody NOT VERIFIED. No tests or Actions run; no independent review claimed.
- No source/test/workflow/permission/secret/proxy/DNS/firewall/VPS/database/ledger/risk/runtime change. Option C unchanged; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Next safe increment: reconcile the `/api/*` Gateway namespace with current `/v1/*` handlers and define an approved-origin/credential-destination contract, documentation-only. Do not implement or deploy the Gateway without separate approval.


## T0 simplification — dependency and retirement gate review second pass (2026-11-10)

- Added read-only audit: `docs/evidence/T0_SIMPLIFICATION_DEPENDENCY_REVIEW_SECOND_PASS_2026-11-10.md`.
- Audit commit: `a0ad4570c1e063e84905c136ebd03c11dd802506`; exact blob SHA to be verified by read-back.
- Inspected branch HEAD baseline: `d584a31c936d8c1d50370a3c74d4c737c853c881`.
- Confirmed active SQLite dependency chain: `feeder_service -> build_production_runtime -> storage factory -> build_runtime -> FeederRuntime/Scheduler/RecoveryCoordinator -> sync_window -> SQLiteWriteGateway + LeaseStore -> SQLite WAL keeper`; bounded read-only `market_data.api` uses the storage facade and T2 FreqAI consumer uses `CandleHttpClient -> /v1/candles`.
- Reaffirmed KEEP: Feeder/runtime, Candle contract/store, shared sync function, SQLite fenced writer, WAL keeper, SQLite storage facade, read-only API, explicit initializer/migrations and regression tests.
- PostgreSQL is runtime-optional but not fully isolated: direct imports exist in `storage.py` and `feeder_service.py`, optional composition is present, and `requirements-market-data.txt` installs psycopg unconditionally. Disposition PARK; do not remove adapter, migrations, tests or driver yet.
- Kraken Spot is a separate research domain with isolated store/API/tests; exclude it from canonical T0 active acceptance, but preserve it. No deletion candidate established.
- Binance connectivity probe is manual support-only, not part of Feeder ingestion; keep outside always-on runtime.
- `sync.py` combines shared ingestion function with one-shot CLI and ShadowWriteGateway; do not split until full import/test/CLI compatibility is mapped.
- Checkpoint Evidence G0–G3 remains a separate assurance workstream, not a basic ingestion prerequisite; preserve records and blockers, freeze feature expansion.
- T0-SM7: broad `market_data/**` trigger in `t0-single-writer-gateway-red.yml` couples research-domain changes to core T0 validation. Do not narrow before all job commands, branch protection and test denominator are reviewed.
- Status: selected source/workflow mapping PASS; full repo call graph, all workflow jobs, branch protection, deployed package/runtime and live consumers NOT VERIFIED. Tests/Actions NOT RUN. Independent review NOT PERFORMED. No code/test/workflow/package/schema/runtime/VPS/DB/provider/key/permission/data changes.
- Option C unchanged; no automatic TTL/delete/archive/cleanup/vacuum/compaction/backup expiry/replica removal. `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Next: documentation-only T0 Active Scope Index distinguishing active SQLite, parked PostgreSQL, separate Kraken research, support probe and separate checkpoint assurance. No code deletion or workflow narrowing.


## T0 Active Scope Index — documentation-only increment (2026-11-10)

- Added `docs/T0_ACTIVE_SCOPE_INDEX.md`.
- Index commit: `0a4edd648588fbce4fcf1bfe481546a447f218ef`.
- Exact index blob SHA after read-back: `15391f262e1cf6379535141463546615809f153c`.
- Source baseline before the index: `3811277f746a4cc4a777b25da68e8e56b63b5229`.
- Separates five workstreams: canonical Binance USD-M BTCUSDT M15/H1 SQLite/Feeder/read-only API (ACTIVE); PostgreSQL (PARKED optional backend); Kraken Spot (separate preserved research domain); Binance connectivity probe (support-only); Evidence Object / Checkpoint G0–G3 (separate assurance workstream).
- Explicitly preserves the active SQLite writer/lease/recovery/API and regression-test boundary. No component retirement, PostgreSQL removal, Kraken deletion, workflow narrowing or test-denominator reduction is authorized.
- Records Option C — No Destructive Authority — and the prohibition on TTL/delete-after-use/cleanup/archive/compaction/vacuum/backup expiry/replica removal. Android Chart/Scanner and Python bot/backtest remain outside the five-layer system.
- README reconciliation was intentionally deferred: `market_data/README.md` documents the canonical Candle API and PostgreSQL adapter details but does not serve as a global T0 scope index. No README was overwritten and no cross-reference was added in this increment.
- Status: index content created and exact blob read back; documentation-only scope PASS. Tests / GitHub Actions NOT RUN / NOT DISPATCHED. Independent review NOT PERFORMED. Full repository call graph, all workflow jobs, branch protection, deployed package/runtime and live consumers remain NOT VERIFIED.
- No source, test, workflow, package, schema, runtime, VPS, database, provider, key, permission or data changes. No PR or merge. `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Next safe step: separately review navigation/cross-references and decide whether a concise link belongs in `market_data/README.md`; do not alter package dependencies, workflow triggers or acceptance denominators.


## T0 Documentation Cross-reference Review — 2026-11-10

- Reviewed `docs/T0_ACTIVE_SCOPE_INDEX.md`, `market_data/README.md`, repository `README.md`, and `docs/FIVE_LAYER_ARCHITECTURE.md` on the active branch.
- Added a concise navigation link from `market_data/README.md` to the T0 Active Scope Index. The README remains the technical contract/run guide; the index remains the global T0 scope authority.
- README update commit: `4aeec0819bc2a7cf73d15df7a89906e6644415f8`; new README blob SHA: `19485ce933e15433c412a54ab15d9cbc1860dfd7`; prior blob: `660a2f0f4f88c0de4fa8c1be3c4af96df282de0e`.
- Cross-reference review found no reason to overwrite the technical README or alter package/workflow/runtime content. The architecture document still contains legacy references to Android Chart Pro as a client and to the separate Python bot/backtest in its broader historical/design narrative. Because these statements are outside the narrow T0 navigation change and require a separate architecture-scope reconciliation, they were not silently rewritten here; treat them as documentation drift to review in a separately scoped task.
- Repository root README also retains legacy Codemagic-centric runner descriptions that conflict with the current GitHub Actions operating preference; not changed in this T0-only increment.
- Status: T0 index navigation link PASS; technical README/index role separation PASS; architecture/root README broader reconciliation NOT VERIFIED / DEFERRED. Tests and GitHub Actions NOT RUN / NOT DISPATCHED. Independent review NOT PERFORMED.
- No source, test, workflow, package, schema, runtime, VPS, database, provider, key, permission or data changes. No PR or merge. Option C — No Destructive Authority — unchanged; no TTL/delete-after-use/cleanup/archive/compaction/vacuum/backup expiry/replica removal.
- Next step: separately reconcile `docs/FIVE_LAYER_ARCHITECTURE.md` and repository `README.md` against the approved five-layer scope and GitHub Actions operating model, without reintroducing Android Chart/Scanner or Python bot/backtest as five-layer dependencies. Do not change code or workflows during that documentation review.


## Five-Layer Architecture Scope Reconciliation — 2026-11-10

- Scope: documentation-only reconciliation of `docs/FIVE_LAYER_ARCHITECTURE.md` and repository `README.md` on the existing branch.
- Architecture document now states the explicit exclusion boundary: Android Chart/Scanner and Python bot/backtest are separate systems, not T0–T4 components, consumers, dependencies, rollout targets or acceptance scope. T4 is React Dashboard/control plane only; APK references were removed from the five-layer flow and implementation plan. Legacy context is retained only as an exclusion statement.
- Architecture update commit: `6eedeb135746ca3dc136feebcdd9ea80f939070a`; new blob SHA: `70e9cd84341ac245a5c6cfa86fa35cd9d8150ec6`.
- Root README now identifies GitHub as source/evidence storage and GitHub Actions as the project's workflow runner; Codemagic is labeled legacy/out-of-scope runner context. The README separates five-layer components from Android Chart/Scanner, Python bot/backtest, Telegram and legacy backtest UI.
- Root README update commit: `fbd8db6262ef9a7bdae55324041b36c17e487042`; new blob SHA: `65f58a94bd0f38e38e2d52d7d0d218c9df52242a`.
- Status: documentation scope reconciliation PASS at text level. No claim that all current GitHub Actions workflows, branch protections, secrets or runtime execution were independently audited; those remain NOT VERIFIED. Tests and GitHub Actions NOT RUN / NOT DISPATCHED. Independent review NOT PERFORMED.
- No source, test, workflow, package, schema, runtime, VPS, database, provider, key, permission or data changes. No PR or merge. Option C — No Destructive Authority — unchanged; no TTL, delete-after-use, cleanup, archive, compaction, vacuum, backup expiry or replica removal.
- Next step: perform a read-only inventory of `.github/workflows` and referenced workflow documentation to establish the actual GitHub Actions execution map; do not dispatch workflows or modify workflow files without separate approval.


## GitHub Actions Execution Map — Read-only Audit (2026-11-10)

- Exact source baseline: `6ab6a11e88aff3b5a12cebe2adce74bc28e8da31` on `feature/t0-centralized-data-feeder-p1-20261101`.
- Audit: `docs/evidence/GITHUB_ACTIONS_EXECUTION_MAP_READ_ONLY_AUDIT_2026-11-10.md`.
- Audit commit: `6b00d7eca68d9422a9c6b43ec6d2d1251aea8b69`; audit blob SHA: `21cf79f9005809fef43de7f2746c4952a83d08f1`.
- Exact branch `.github/workflows/` contains 14 YAML files. Workflow inventory, trigger/job classification and exact blob SHAs are recorded in the audit.
- F-01 CONFIRMED: `t0-single-writer-gateway-red.yml` uses broad `market_data/**` and `pipeline/**` filters and runs a mixed T0/T1/paper/PostgreSQL job set. Do not narrow triggers or jobs until the complete test denominator and job dependencies are reviewed.
- F-02 CONFIRMED / NOT EXECUTED: `t0-manual-validation.yml` has a Scaleway SSH preflight gate using protected SSH secrets and a remote pinned-host-key connection. This remains a manual external operation; no dispatch or SSH connection was made.
- F-03 STATIC CONFLICT CONFIRMED / NOT EXECUTED: `ci/test_ci_policy.py` asserts there are no active GitHub Actions YAML files, but the exact branch contains 14. `codemagic.yaml` still declares a push-triggered `canonical-market-data` workflow that runs `unittest discover -s ci`, which includes this conflicting test. External Codemagic account/trigger execution state NOT VERIFIED. Do not modify CI tests/config without separate approval.
- F-04 METADATA OBSERVED: active branch endpoint returned `protected=false`, protection disabled and no required status-check contexts. Organization/repository rulesets and effective governance NOT VERIFIED.
- F-05 boundary: workflow definitions do not establish workflow execution PASS, G2 exact-SHA, L4-Minimum, or production readiness. Workflow runs/artifacts, external Codemagic state, secrets/effective permissions and reusable-workflow call sites remain NOT VERIFIED.
- Tests NOT RUN; GitHub Actions NOT DISPATCHED; independent review NOT PERFORMED. No source/test/workflow/config/secret/permission/runtime/VPS/DB/provider/data changes. No PR or merge.
- Option C — No Destructive Authority — unchanged; no deletion, TTL, cleanup, archive, compaction, vacuum, backup expiry or replica removal.
- Next gate: prepare a separate documentation-only CI ownership and test-denominator decision record for F-01/F-03. No workflow trigger, CI policy test, Codemagic config, branch protection, secret or dispatch changes without separate approval.


## CI Ownership and Test Denominator Decision Record — 2026-11-10

- Added `docs/evidence/CI_OWNERSHIP_AND_TEST_DENOMINATOR_DECISION_2026-11-10.md` as a documentation-only proposal addressing GitHub Actions ownership, legacy Codemagic disposition, F-03 CI policy contradiction and F-01 mixed-workflow test denominator.
- Decision record commit: `154079695cd65424e532b0de360d35abbb9a4108`; exact blob SHA verified below.
- Proposed target: GitHub Actions is the sole canonical five-layer CI runner; Codemagic remains PARKED/legacy with no deletion or deactivation until its external app/webhook/workflow state is separately inventoried. This is a proposal, not a claim that Codemagic is disabled.
- F-03: recommend eventual replacement of the obsolete “no active GitHub Actions YAML” assertion with explicit ownership/evidence invariants. No CI test or Codemagic config changed.
- F-01: recorded job-level coverage preservation for T0 core, T2/paper consumer, T1 importer, Rust sidecar and parked PostgreSQL/TimescaleDB. No job, trigger, path filter or test denominator was changed.
- Required future evidence contract records workflow/blob SHA, trigger/filter, exact source SHA, all job conclusions, test counts, artifacts/digests, operation class and PASS/PARTIAL/BLOCKED/NOT VERIFIED status.
- Status: documentation proposal PASS; owner approval PENDING; implementation NOT AUTHORIZED. Tests NOT RUN; GitHub Actions NOT DISPATCHED; workflow runs/artifacts NOT VERIFIED; Codemagic external state NOT VERIFIED; independent review NOT PERFORMED.
- No source/test/workflow/config/secret/permission/ruleset/branch-protection/runtime/VPS/DB/provider/data changes. No PR or merge. Option C unchanged; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders.
- Next gate: owner decision on D-01–D-05, especially external Codemagic disposition. Do not implement F-01/F-03 or dispatch workflows until separately approved.


## Owner approval — CI Ownership and Test Denominator D-01–D-05 (2026-11-10)

- Owner explicitly approved all five decisions as proposed in `docs/evidence/CI_OWNERSHIP_AND_TEST_DENOMINATOR_DECISION_2026-11-10.md`.
- Decision record update commit: `a8ddba3f31cd669dbe32a10370384bfe59ec679c`; updated blob SHA: `68c14033f32bdd8bbbd675ed58ea8157f95dcb3d`.
- D-01 APPROVED: GitHub Actions is the sole canonical CI/workflow runner for the five-layer project; GitHub remains source/history/evidence storage; acceptance requires exact-SHA runs and complete job/artifact evidence.
- D-02 APPROVED: Codemagic PARKED / legacy / no new five-layer dependency / no deletion yet. External app/webhook/branch-filter/workflow/environment-group/execution state remains NOT VERIFIED. No disable/delete or external account access is authorized.
- D-03 APPROVED: replace the obsolete no-GitHub-Actions test assumption with explicit ownership/evidence invariants as the target. Editing the test remains NOT AUTHORIZED until active test denominator and Codemagic ownership are mapped.
- D-04 APPROVED: preserve the complete denominator across T0, T1 importer, T1 sidecar, T2/paper, optional parked PostgreSQL/TimescaleDB and remaining cross-domain contracts. No job/test/path-filter reduction authorized.
- D-05 APPROVED: adopt the proposed domain-separated workflow organization as target design, subject to complete mapping and separate implementation authorization.
- Approval is policy/design-only. It does NOT authorize workflow/test/config edits, Codemagic metadata access/deactivation, workflow dispatch/rerun, branch/ruleset/permission/secret changes, SSH/VPS/provider/database/runtime operations, or destructive actions.
- Status: D-01–D-05 OWNER-APPROVED; implementation NOT AUTHORIZED / NOT STARTED; tests NOT RUN; GitHub Actions NOT DISPATCHED; Codemagic external state NOT VERIFIED; rulesets/effective permissions NOT VERIFIED; independent review NOT PERFORMED.
- No source/test/workflow/config/secret/permission/ruleset/branch-protection/runtime/VPS/DB/provider/data changes; no PR or merge. Option C unchanged; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Next safe step: prepare a documentation-only implementation plan for F-03 and F-01, preserving the full test denominator and listing all preconditions. Do not implement or dispatch until a separate implementation authorization is given.


## T0 simplification — optional PostgreSQL packaging isolation review (2026-11-10)

- Added documentation-only static review: `docs/evidence/T0_OPTIONAL_POSTGRES_PACKAGING_ISOLATION_REVIEW_2026-11-10.md`.
- Report commit: `b2713ba95cf42bc16db18792cc562d62e0a9e1f3`.
- Exact source baseline inspected: `27d22fe1c3103732eaa9da8a36e22d77b19d4688`.
- Confirmed `requirements-market-data.txt` installs both CCXT and `psycopg[binary]` unconditionally, while SQLite is the selected default. `market_data/storage.py` and `feeder_service.py` import PostgreSQL adapter modules at module load; inspected `postgres.py` imports the psycopg driver inside the connection function.
- Confirmed the current workflow uses the shared requirements file for SQLite/T0 tests and disposable PostgreSQL/TimescaleDB qualification jobs. A careless removal of psycopg would break the latter.
- Finding: a SQLite/base requirements set plus a separate PostgreSQL qualification requirements set is a valid design candidate; no evidence supports deleting PostgreSQL adapter, migrations, SQL, tests or integration jobs. Lazy adapter imports are a separate optional refactor and are deferred.
- Required next mapping: repository-wide references to requirements files, psycopg, PostgreSQL tests/entry points, local setup instructions and every workflow install command. Then design the dependency split and clean-environment import tests without running runtime/exchange operations.
- Status: inspected source observations PASS; full install-path/workflow consumer inventory NOT VERIFIED; clean SQLite-only import test NOT RUN; tests NOT RUN; GitHub Actions NOT DISPATCHED; independent review NOT PERFORMED. G2 NOT VERIFIED; G3 PENDING; L4-Minimum BLOCKED / NOT VERIFIED.
- No source/test/workflow/package/config/runtime/VPS/database/provider/permission/data changes; no destructive operation. Option C unchanged; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Next safe step: read-only repository-wide dependency/install-path inventory; no package or workflow edits until separately authorized.


## Five-Layer scope exclusion — Android Chart/Scanner and Python bot/backtest (2026-11-10)

- Recorded explicit scope boundary in `docs/evidence/FIVE_LAYER_SCOPE_EXCLUSION_ANDROID_PYTHON_2026-11-10.md`.
- Decision record commit: `3a2d8f328de558483d5ed00e840a6672b4b6a0ca`.
- Android Chart/Scanner and Python bot/backtest are OUT OF SCOPE: not T0–T4 components, producers/consumers, dependencies, deployment/rollout or acceptance/test-denominator inputs. Repository co-location creates no integration obligation.
- Updated `README.md` to make the exclusion explicit and link the decision record. README commit: `8eacc9dbb63364601f7b2a5654847d512fea6640`; blob: `bcb524b9862f99f8257c07b4e495856a5fdf7cb7`.
- Updated `docs/T0_ACTIVE_SCOPE_INDEX.md` to state the same boundary. Index commit: `d80e319e18d2d9a7e75a848c551ac065f2f07f2b`; blob: `70c13603ec4f9d499273f2412c4106fcbc346af2`.
- `docs/FIVE_LAYER_ARCHITECTURE.md` already explicitly excludes both systems from architecture, dependency, rollout, validation and acceptance; it was not changed in this increment.
- Exclusion does not delete, disable, migrate or refactor Android/Python assets, source code, data or their legacy workflows. Telegram and old backtest dashboard remain separate repository assets as well.
- Tests NOT RUN; GitHub Actions NOT DISPATCHED; independent review NOT PERFORMED. No source, workflow, package, data, runtime, VPS, database, provider, secret, permission or Codemagic changes. No PR/merge.
- Next step: read-back consistency check of the decision record, README, T0 index, architecture and this handoff; no implementation is needed for this scope decision.

- Follow-up README clarification: the repository workflow table is explicitly labeled as a whole-repository inventory, not the Five-Layer CI scope; Android, Telegram, backtest and scanner workflows are marked OUT OF SCOPE. Commit: `82c564784e626cef3a0e31cd64225ed36ef6f5f1`; README blob: `f74128561ff1cf56af63214c84e1d8915bd8c5a2`.


## T0 PostgreSQL dependency/install-path inventory — 2026-11-10

- Added read-only inventory: `docs/evidence/T0_POSTGRES_DEPENDENCY_INSTALL_PATH_INVENTORY_2026-11-10.md`.
- Inventory commit: `4e1ed20658cadc27f25b370843c7f8fd5461c634`.
- Exact active branch HEAD inspected before the inventory: `92ab5e937ed8eba5e5ce1f1f4b19dcdc85b235d8`; previous packaging baseline `27d22fe1c3103732eaa9da8a36e22d77b19d4688`; compare showed 8 commits ahead, 0 behind and no source/workflow changes since the previous baseline.
- Enumerated 662 repository blobs and fetched all 14 active-branch GitHub Actions workflow definitions plus the relevant requirements, storage/feeder/PostgreSQL/migration modules, six PostgreSQL test modules, setup helper, TimescaleDB test script, Codemagic config and market-data README.
- Confirmed consumers: `t0-manual-validation.yml`, `p5-3-11-g2-integration-green.yml`, two isolated TimescaleDB jobs in `t0-single-writer-gateway-red.yml`, explicit psycopg install/import in `t0-postgres16-grantor-repro.yml`, legacy `codemagic.yaml` jobs, `ci/setup-python.sh`, `ci/test-timescaledb.sh`, and SQLite install instructions in `market_data/README.md`.
- Confirmed direct runtime psycopg import remains lazy inside `market_data/postgres.py::connection`; `storage.py` and `feeder_service.py` import PostgreSQL adapter classes at module scope. `migrations.py` uses the adapter connection.
- Identified six PostgreSQL qualification modules to preserve: `test_postgres_provider_bootstrap`, `test_postgres_write_gateway`, `test_postgres_feeder_runtime`, `test_postgres_feeder_runtime_lifecycle`, `test_postgres_role_privileges`, and `test_timescaledb`.
- Status: source/workflow observations PASS for fetched files; exact all-repository textual occurrence count PARTIAL / NOT VERIFIED because GitHub code search is default-branch indexed and no branch-local shell grep/checkout was available. No additional match is claimed absent based on incomplete search.
- Clean SQLite-only import test NOT RUN; tests NOT RUN; GitHub Actions NOT DISPATCHED; independent review NOT PERFORMED. G2 NOT VERIFIED; G3 PENDING; L4-Minimum BLOCKED / NOT VERIFIED.
- No source/test/workflow/package/config/runtime/VPS/database/provider/secret/permission/data changes. No PR or merge. PostgreSQL adapter/migrations/tests/workflows remain PARKED/PRESERVED; no test denominator reduction.
- Next gate: complete branch-local exact text search for all requirements/psycopg/PostgreSQL entry-point/install references, reconcile any additional matches, then prepare dependency split design and per-job install matrix. Independent review required before implementation.


## Legacy Python and workflow retirement — 2026-11-10

- Owner authorized removal limited to `bot.py`, `backtest.py`, `telegram_commands.py`, their legacy workflow definitions and direct execution/dispatch dependencies from the shared repository.
- Exact inspected source baseline on `feature/t0-centralized-data-feeder-p1-20261101`: `3838b452ac96f5d82c6071f2ae826ff954d9c4bc`.
- Manifest: `docs/evidence/LEGACY_PYTHON_WORKFLOW_RETIREMENT_MANIFEST_2026-11-10.md`.
- The three requested paths under `.github/workflows/` were absent at the inspected branch SHA. Their archived copies under `ci/archive/github-actions/` and active Codemagic workflow blocks in `codemagic.yaml` were identified and removed instead; all other active `.github/workflows/*.yml` workflows remain untouched.
- Removed Python entry points: `bot.py`, `backtest.py`, `telegram_commands.py`; wrapper/test/client and archive dependencies are itemized in the manifest.
- Preserved T0 health API in `app.py`, T0–T4 code/data/tests, Android Paper client, all other active workflows, and standalone `backtest_rsi_percent_b_h1_adx.py`. The old dashboard remains a manual JSON/CSV viewer only.
- No repository/branch/history rewrite, external repository, secrets, caches, artifacts, external Codemagic state, Render deployment, VPS, database, exchange or canonical data was deleted or changed.
- Source commit: `4617c3f74bc7a0119094fc4890e7ca0d8d6ed53f`; tree: `db43e502a3fe75835da8ed24fca453f2fa04cfc3`.
- Post-commit read-back: PASS — all 11 authorized paths are absent; all 14 active `.github/workflows/*.yml` files remain; T0 health routes and other retained components are present.
- Tests NOT RUN; GitHub Actions NOT DISPATCHED; commit status contexts empty; no workflow run/artifact claimed. External Codemagic state NOT VERIFIED; independent review NOT PERFORMED. Existing unrelated CI policy contradiction F-03 remains outside this scope.
- Next step: obtain separate authorization for focused retirement and T0/API regression validation in GitHub Actions. No runtime or external cleanup is authorized by this source retirement.


## T0 simplification — PostgreSQL packaging reassessment (2026-11-10)

- Added read-only reassessment: `docs/evidence/T0_SIMPLIFICATION_POSTGRES_PACKAGING_REASSESSMENT_2026-11-10.md`.
- Exact inspected source baseline: `4d3945e37d74b8ce81227db3265a80dd85f29c24`; tree: `b344c6b09f00e6a7abd7a2c5456f3d39f6608365`.
- Reassessed the earlier candidate to split SQLite/base and PostgreSQL requirements. Recommendation: PARK the split; keep `requirements-market-data.txt` unchanged. The dependency over-install is real on some paths, but the benefit of removing one of two direct dependencies is not established against added requirements-file, workflow-branch and legacy-consumer complexity.
- Current branch blobs were recorded for the shared requirements, storage/feeder/PostgreSQL modules, manual/G2/T0 Gateway workflows, Codemagic config and market-data README. The previous install-path inventory predates the latest source retirement; current Codemagic SHA was re-read.
- PostgreSQL adapter, migrations, SQL, six qualification modules and disposable integration jobs remain preserved. No dependency, workflow, source or test change.
- Status: inspected files/install commands PASS; exhaustive branch-local occurrence scan NOT VERIFIED; clean SQLite-only import test NOT RUN; tests NOT RUN; GitHub Actions NOT DISPATCHED; independent review NOT PERFORMED. G2 NOT VERIFIED; G3 PENDING; L4-Minimum BLOCKED / NOT VERIFIED.
- No runtime/VPS/database/provider/secret/permission/data operation. Option C unchanged; paper-only; no live orders.
- Next safe step: continue read-only review of active SQLite startup/configuration ownership for proven duplication. Do not refactor or edit workflows without a separately established candidate and regression map.


## T0 L4-Minimum / L4-Extended branch separation assessment — 2026-11-10

- Added architecture/branching recommendation: `docs/evidence/T0_L4_MINIMUM_EXTENDED_BRANCHING_ASSESSMENT_2026-11-10.md`.
- Assessment commit: `a4678fd14d4b5450c745224dedfd83e980fff3b7`.
- Assessment baseline branch HEAD: `4d3945e37d74b8ce81227db3265a80dd85f29c24`.
- Controlling L4-Minimum matrix blob: `ed3056d81edfaf163205a172cf5ad22e230d7b41`; T0 components-outside-L4-Minimum audit blob: `7bfc509b9eb918750b3a25acc18f8d4f989d387f`.
- Recommendation: retain the existing `feature/t0-centralized-data-feeder-p1-20261101` branch as the T0 + L4-Minimum continuity/delivery line. Defer creation of `feature/l4-extended-provenance` until all L4M-01–L4M-10 controls PASS on one frozen evidence baseline and a qualifying independent review disposition references that exact baseline.
- L4-Extended candidate scope is limited to additive optional assurance: claim-specific RFC 3161 TSA and its required trust/revocation interoperability, optional multi-TSA/quorum, dedicated WORM/Object Lock, and optional dual-root/Root A–Root B evidence topology. TSA stays asynchronous/outside Feeder commit path; WORM must not be conflated with SQLite canonical candle storage.
- Explicitly classified PostgreSQL/TimescaleDB, HTTPS front door, D2–D4 durability, production DB restore/DR, Kraken/source corroboration, G0–G3 checkpoint qualification and lifecycle/retention as separate workstreams, not automatic L4-Extended scope.
- Extended branch must preserve the complete L4M acceptance/test denominator; Extended tests are additive; no automatic merge back to the minimum line. Any adoption requires explicit owner approval, independent review and compatibility evidence.
- Status: architecture recommendation PASS; L4-Minimum implementation/operational acceptance BLOCKED / NOT VERIFIED; qualifying independent review PENDING; Extended implementation DEFERRED / NOT STARTED.
- No branch was created. No source/test/workflow/package/runtime/VPS/database/provider/key/trust-root/permission/data changes; no PR/merge/rebase/history rewrite; no workflow dispatch. Option C — No Destructive Authority — unchanged.
- Next gate: continue L4-Minimum on the existing branch, close matrix review findings, produce exact evidence for L4M-01–L4M-10, and obtain qualifying independent review. Only then request authorization to create the Extended branch from the exact accepted baseline.


## Latest owner decision — L4-Minimum independent-review waiver (2026-11-10)

- Owner decision: `docs/decisions/D-2026-11-10-L4-INDEPENDENT-REVIEW-WAIVER.md`.
- Decision commit: `40a8c1b11372d341b7979e2fc2079fd12923ac57`.
- Decision: mandatory independent human/third-party review is removed from L4-Minimum only. The 2026-11-09 scope decision remains an unchanged historical record; the 2026-11-10 decision supersedes its reviewer requirement prospectively for L4-Minimum.
- Acceptance matrix updated: `docs/evidence/p1-8/L4-MINIMUM-PROVENANCE-ACCEPTANCE-MATRIX.md`.
- Matrix update commit: `672f3b25c0065326656b0833f642049152838c5e`; new matrix blob: `31bb02ec25aa29794306167ae0e66abcfb1b8f79`.
- L4M-09 remains as a traceability ID but is OWNER-WAIVED / NOT MANDATORY, neither PASS nor FAIL, and excluded from the mandatory denominator. Active controls: L4M-01–L4M-08 and L4M-10 (nine controls).
- Aggregate L4-Minimum PASS now requires all nine active controls PASS on the same frozen baseline and a separate owner disposition referencing its exact digest. No independent reviewer disposition is required.
- Technical independence remains mandatory: evidence custody outside T0/VPS and GitHub, separate-environment offline verification, independent evidence readback, signer separation, authenticated freshness and tamper-evident history.
- Assurance limitation: owner self-assessment is not independent assurance. No independent audit, third-party review, certification or reviewer-confirmed acceptance claim is permitted.
- Scope boundary: P1.8.152/P1.8.153 reviewer requirements remain unchanged and open; this waiver does not close lifecycle findings. Option C and all operational/destructive authorization boundaries remain unchanged.
- Status: owner policy change recorded; matrix updated. Technical implementation/evidence for the nine active controls remains NOT VERIFIED / BLOCKED. No tests or GitHub Actions dispatched; no source/runtime/VPS/database/key/permission/data/destructive changes.
- Next step: read back the decision, matrix and handoff; then reconcile F-01–F-09 and P1.8.152/P1.8.153 without importing the waived L4 reviewer requirement into the separate lifecycle workstream.


### L4 reviewer-waiver documentation reconciliation

- Final matrix correction commit: `bb4f63424961faa2edca911e111d709e18edd849`; final matrix blob SHA: `c109bd162dbd4744876392ee6f625bc9478da7de`.
- Decision status alignment commit: `246c7d99a7e18844d10fd2472ed612aa43ac8aa8`; final decision blob SHA: `75e057ba482d81f6a9d896ace2b017807c9396d9`.
- The matrix now explicitly uses an owner-assessment baseline and separate owner disposition; the nine active mandatory controls are L4M-01–L4M-08 and L4M-10. L4M-09 is OWNER-WAIVED / NOT MANDATORY and is not counted as PASS.
- Corrected the matrix's self-referential baseline instruction: the external frozen manifest identifies the exact matrix blob; the matrix does not hard-code a potentially stale current blob SHA.
- Corrected execution-sequence numbering. No tests or Actions were run.
- Final policy scope remains narrow: P1.8.152/P1.8.153 reviewer gates are not waived or closed. No independent assurance claim is allowed for L4-Minimum owner self-assessment.
- Next work: reconcile F-01–F-09 against the revised matrix and separately preserve open P1.8.152/P1.8.153 lifecycle findings; do not require a qualifying independent reviewer for L4-Minimum itself.


## F-01–F-09 and P1.8.152/P1.8.153 documentary reconciliation (2026-11-10)

- Added `docs/evidence/T0_L4_F01_F09_P1_8_152_153_RECONCILIATION_2026-11-10.md`.
- Reconciliation commit: `1fcb7823defade349e3a2f8217ef6d5bc40db95f`.
- Read-only source HEAD: `3b2de476cb130cd414a956f3c16830f57237ec8a`; recursive tree `a2a3c1381561fd98c346336fb52f18edc29372fe`, complete.
- F-01–F-04 and F-06 are addressed in current matrix wording, but operational proof/acceptance is NOT VERIFIED. F-05 reviewer requirement is superseded only for L4-Minimum by the owner waiver; it is not counted in the nine-control denominator and does not waive lifecycle reviewer requirements.
- F-07–F-09 originating source records/criteria were not located in the complete inspected branch tree. They remain NOT VERIFIED; no closure inferred.
- P1.8.152 blob `e1a4d95af216e94a58fa5528850fcd0c1ff465f8`: PARTIAL — lifecycle design not closed. RET-03 and RET-06–RET-10 remain open/not verified or non-executable; V07 BLOCKED; V08/Restore OPEN/BLOCKED; LDA-05/06/08 not verified; LDA-07 87 negative vectors NOT RUN; LDA-09 documentary alignment but formal closure pending lifecycle review.
- P1.8.152 §7 recommends P1.8.153 as independent review of P1.8.152 and residual reviewer-control closure assessment. No P1.8.153 record exists in the complete current branch tree: NOT CREATED / NOT EXECUTED / NOT VERIFIED.
- The L4M-09 waiver does not waive P1.8.152/P1.8.153 lifecycle reviewer requirements. No lifecycle waiver is recorded.
- Overall L4-Minimum remains BLOCKED / NOT VERIFIED. No tests, Actions, runtime/permission/provider/data inventory or destructive operation performed.
- Next step: identify the authoritative F-07–F-09 source records; separately determine whether to authorize the P1.8.153 lifecycle task. Preserve Option C, no-live-orders and all existing lifecycle statuses.


## Latest owner decision — lifecycle independent-review waiver (2026-11-10)

- Owner decision: `docs/decisions/D-2026-11-10-LIFECYCLE-INDEPENDENT-REVIEW-WAIVER.md`.
- Decision commit: `0389b15f2e72557519793ba3941d9ff440970983`.
- The owner waived mandatory independent human/third-party review across the T0 retention/lifecycle workstream covered by P1.8.141–P1.8.153 and the linked RET/LDA/IR reviewer-control chain.
- P1.8.153 is OWNER-WAIVED / NOT REQUIRED as a mandatory gate; it is NOT EXECUTED and is not claimed PASS. Do not create P1.8.153 solely to repeat the waived independent review.
- IR147-01 and the reviewer-dependent portion of LDA-09 are waived as review gates only. Their substantive retention-floor, technical, inventory, adapter, enforcement, restore and evidence criteria remain OPEN / BLOCKED / NOT VERIFIED as applicable.
- Current L4 acceptance matrix aligned: `docs/evidence/p1-8/L4-MINIMUM-PROVENANCE-ACCEPTANCE-MATRIX.md`; update commit `a0f24c1daaeefabda4e85100c220259d601e07f9`; final blob SHA `2ba85af550fb7e369ea39ade6d73878d78dbf6bc`.
- P1.8.152 and earlier lifecycle records remain unchanged as historical records.
- Retained controls: explicit owner approval gates; Option C — No Destructive Authority; T0 canonical-data and protected-class exclusions; RET-03–RET-10 substantive requirements; technical/environmental independence for verification where required; exact-object binding; inventory; mutation fencing; fail-closed behavior; negative tests; restore/reconciliation evidence. “Independent verifier” in RET-10 remains a technical separation requirement, not a waived human reviewer.
- No technical control is promoted to PASS by this waiver. Owner self-assessment is not independent assurance; no third-party review, certification or reviewer-confirmed acceptance claim is permitted.
- No tests or GitHub Actions dispatched; no source/runtime/VPS/database/identity/permission/provider/data/inventory/staging/restore/fault-injection or destructive operation. Option C, T0 protection, paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.
- Next step: continue lifecycle residual assessment under the revised owner policy; keep all substantive statuses and execution prohibitions intact.


## Lifecycle reviewer-waiver reconciliation and residual dependency plan — 2026-11-10

- Prospective lifecycle waiver aligned into the F-01–F-09 / P1.8.152–153 crosswalk by addendum; historical as-of sections preserved. Crosswalk commit `3e9b78dfb1485ee5ad3a12ab2c1c8f8865333659`; final blob SHA `3d084c04cd9712ed05d790ce5c431e988b64ce32`.
- Created `docs/evidence/p1-8/T0_LIFECYCLE_RESIDUAL_DEPENDENCY_AND_ACCEPTANCE_PLAN_2026-11-10.md`; commit `98780188c73edff0badc71b46b017c0c0bead6f7`. It sequences documentary class/floor inputs, V07/RET-10, V08, mutation fencing, restore, inventory/enforcement and negative vectors without promoting any residual status.
- Immediate next bounded task: Stage A documentary clarification of RET-03 and RET-07 class-specific floor inputs. Do not invent numeric floors; identify missing owner/legal/operational basis and stop where inputs are insufficient.
- Reviewer gate: lifecycle independent human review OWNER-WAIVED / NOT MANDATORY; P1.8.153 OWNER-WAIVED / NOT REQUIRED, NOT EXECUTED, NOT PASS. Owner assessment is not independent assurance; RET-10 technical/environmental verifier separation remains required.
- Residuals preserved: RET-03/06/07/08 OPEN; RET-04 NON-EXECUTABLE; RET-05 technical enforcement NOT VERIFIED; RET-09 NOT VERIFIED; RET-10 OPEN/NOT VERIFIED; V07 BLOCKED; V08/Restore OPEN/BLOCKED; LDA-05/06 NOT VERIFIED; LDA-07 87 vectors NOT RUN; LDA-08 HOLD/NOT VERIFIED; F-07–F-09 NOT VERIFIED.
- No tests/Actions, source/runtime/VPS/database/provider/permission/inventory/staging/restore/fault-injection or destructive operations. Option C, T0 protection, paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## Stage A RET-03 / RET-07 documentary clarification (2026-11-10)

- Added `docs/evidence/p1-8/T0_RET03_RET07_RETENTION_FLOOR_INPUT_GAP_ANALYSIS_2026-11-10.md`.
- Document commit: `d5095f4c64a9715cb12719d899269c70f3d1e679`; verified content blob SHA: `e26d056f9f0c2ea57a9951a650b29af11939c422`.
- Read-only source baseline before the document: `9c93e0c4f5ab211df660feb6a538cc27bf6b83da`; source record blob SHAs are enumerated in the analysis.
- RET-03 class boundary clarified: only T1 raw observations, T2 ephemeral inference outputs, T4 deterministic caches/read models/materializations and individually identified noncanonical copies may enter a future read-only exact-object/version assessment under RET-02 B. No class/object is made deletion-eligible by this analysis.
- T0 canonical data and availability/recovery copies, CORE_LEDGER, AI_LEDGER, required T3 reconstruction/audit records, governance evidence while needed, and unknown/unclassified/orphaned/incompletely inventoried data remain protected/excluded.
- RET-03 inputs still missing: source-backed purpose/obligation basis, accountable owner, exact scope, start/terminal events, duration rationale, trusted-time/order, dependency/hold and copy-graph closure, compliance evidence and explicit owner disposition. No numeric floor/TTL selected.
- RET-07 evidence groups separated into policy/approval, assessment manifests, dependency/hold, tombstone/state-transition, audit/security/incident, copy/restore, verification/acceptance and external-recipient evidence. Terminal/reopen/successor semantics, competent release authority, clock basis, evidence-store/custody requirements and owner-approved duration remain missing. No expiry rule selected.
- Reviewer waiver is only a reviewer-gate waiver; it does not waive substantive evidence requirements or create expiry authority. Owner assessment is not independent assurance.
- Status: STAGE A DOCUMENTARY CLARIFICATION COMPLETE; RET-03 OPEN; RET-07 OPEN; no legal determination, operational inventory, tests, Actions, implementation or destructive operation.
- Tests NOT RUN; GitHub Actions NOT DISPATCHED; no workflow run/artifact. Option C and all prior residual statuses unchanged.
- Next step: obtain source-backed owner inputs for one eligible data class or evidence group at a time; if authoritative basis or competent determination is absent, record the gap and stop. No numeric values or legal rules may be inferred.


## Stage A.2 — T1 RET-03 owner-input resolution (2026-11-10)

- Added `docs/evidence/p1-8/T1_RET03_OWNER_INPUT_RESOLUTION_2026-11-10.md`.
- Document commit: `1a9b98dd723639078e208510adfa29cea54176dc`; verified content blob SHA: `061ea9340e07a9f633a8864928c945f44adc5295`.
- Source branch baseline: `c0823759c96362d79174b90d29ec4bde1c9b8ef3`; exact source evidence blobs are enumerated in the document.
- T1 paths separated: existing trades/funding/open-interest/liquidations CSV importer; proposed 1m Binance USD-M kline source-file product (v1.1 DESIGN ONLY / NOT APPROVED FOR IMPLEMENTATION); connection-lifecycle sidecar (separate offline evidence, not a market-data feed); T0 canonical candles remain independently owned.
- Static trace confirms importer is pull/CLI driven; snapshot is OBSERVED_ONLY / complete=false / continuity UNVERIFIED / connection UNVERIFIABLE. Trade flow is consumed after quality gates; funding/OI/liquidations are exposed for dashboard/downstream analysis in the inspected decision path. File hashes do not prove transport completeness.
- Actual CSV files/locations/rotation, producer runtime/schedule, complete consumer and copy inventory, obligation start/end events, holds and authoritative owner/legal/operational sources remain NOT VERIFIED / NOT PROVIDED.
- RET-03 T1 status: OPEN / FLOOR_NOT_ESTABLISHED. No numeric floor/TTL selected. No T1 object made deletion-eligible. Central policy no-delete-after-read remains controlling.
- Tests NOT RUN; GitHub Actions NOT DISPATCHED; no workflow run/artifact. External T1 repo/VPS/runtime/CSV/DB/provider/exchange/consumers not accessed. No source/runtime/permission/data or destructive changes.
- Option C, T0 independence, protected classes, paper-only and `AI_EXECUTION_ENABLED=false` unchanged.
- Next step: obtain owner-supplied authoritative inputs for the four existing CSV feeds (purpose/owner, exact source scope, obligations, start/end events, consumer dependencies, holds and duration rationale). If not supplied, keep RET-03 OPEN and do not infer a floor. Any operational inventory requires separate bounded authorization.


## Latest completed work — Stage A.3 T2 RET-03 Owner Input Resolution (2026-11-10)

- Added `docs/evidence/p1-8/T2_RET03_OWNER_INPUT_RESOLUTION_2026-11-10.md` as a documentation-only static class/lineage and consumer-dependency analysis.
- Analysis source baseline HEAD: `d5921afe81fc4ad801f445726e42ca37ba939358`; source blob SHAs are pinned in the new record.
- T2 map distinguishes T0 canonical inputs, training data, features/labels, training manifests, model/run/evaluation artifacts, provenance/context/prediction JSON, final AI paper intents, AI ledger/risk state, and T3 reconstruction evidence.
- Confirmed the prediction output path is a replaceable latest-output slot, not an append-only history. The final paper intent carries model/strategy/inference dataset/snapshot identifiers but does not carry `trainingDatasetVersion`, `trainedThroughMs`, `trainingCompletedAtMs`, or the prediction value. No immutable external lookup binding was established in the inspected source set.
- Research config contains `purge_old_models=2` and `expired_hours=2`; their effective runtime semantics and actual effects are NOT VERIFIED. These settings are not an approved retention policy and no pruning was executed or authorized.
- Actual training source/dataset manifest, model/run/evaluation artifacts, prediction history, paper DB/runtime, consumer registry, copy/backup/recipient graph, holds, terminal events and duration bases remain NOT VERIFIED / NOT PROVIDED.
- Status: T2 static class/lineage map COMPLETE; RET-03 OPEN / FLOOR_NOT_ESTABLISHED; no numeric floor/TTL selected. No object is deletion-eligible.
- Tests NOT RUN; GitHub Actions NOT DISPATCHED; no workflow run or artifact claimed. No training/backtest, runtime/VPS/DB/provider/consumer/copy inventory, config/source/workflow/permission change, model pruning or destructive action.
- Boundaries unchanged: Option C, lifecycle independent-review waiver, T0 independence, separate CORE_LEDGER/AI_LEDGER, paper-only, `AI_EXECUTION_ENABLED=false`.
- New T2 analysis document commit: `2ee2eec6aae971563e5378363cff7338dc88a2c1`.
- Next step: Stage A.4 T3 RET-03 owner-input resolution, focused on signal/risk/order/fill/reconciliation and paper-outcome reconstruction dependencies; keep ledger and required T3 records protected and do not infer retention periods.


## Stage A.4 — T3 RET-03 Owner Input Resolution (2026-11-10)

- Added `docs/evidence/p1-8/T3_RET03_OWNER_INPUT_RESOLUTION_2026-11-10.md` as a documentation-only source/contract trace of signal, risk decision, paper order, fill, reservation, replay and reconciliation obligations.
- Source baseline HEAD: `77c6892efb7107f91c2aa5d20e33187e856a36a9`; exact source blob SHAs are pinned in the report.
- Confirmed at source level: strategy decision emits PAPER intent; the dual-ledger writer persists orders and shared risk reservations; each simulated fill is written to an append-only account event journal with canonical payload digest and source book snapshot reference; replay loader validates execution/funding/mark coverage and replay engine reconstructs Core, AI and Legacy ledger values.
- Gaps: no complete durable signal/WAIT/rejected-decision history established; no separate immutable full risk-evaluation journal established; order and reservation rows are mutable current-state records; the traced replay execution stream accepts FILL events and does not establish complete replay of order/risk/reservation lifecycle transitions; independent second evidence root and actual copy/restore graph NOT VERIFIED.
- The reconstruction contract requires two distinct evidence roots and full replay coverage; source/design contracts are not operational proof. Book snapshot IDs/digests do not prove original source-byte custody or upstream completeness.
- T3 protected scope includes CORE_LEDGER, AI_LEDGER, LEGACY_UNATTRIBUTED, signals/intents, risk decisions/config and Kill Switch history, order lifecycle, fills, reservations, fees/funding/marks/equity, cutover snapshots, event/audit journals, coverage, replay/reconciliation/correction evidence and required backups/restore/independent copies. Unknown/uninventoried copies remain protected.
- T3 RET-03 remains OPEN / FLOOR_NOT_ESTABLISHED. No numeric floor, TTL, grace or expiry rule selected; no object deletion-eligible. Order/reservation expiry is not proof that all decision, accounting, replay, audit or recovery obligations ended.
- Tests NOT RUN; GitHub Actions NOT DISPATCHED; no workflow run/artifact. No runtime/database/VPS/provider/consumer/copy inventory, legal determination, restore, reconciliation execution, source/schema/config/permission change or destructive operation.
- Option C, lifecycle reviewer waiver boundaries, T0 independence, separate ledgers, paper-only and `AI_EXECUTION_ENABLED=false` unchanged.
- T3 analysis commit: `52302aee66db92d45a30b84fa589c098c4c33a84`; report blob SHA verified by read-back.
- Next step: Stage A.5 T4 RET-03 Owner Input Resolution for dashboard/read models/exports/caches and their dependencies on protected T0–T3 records. Keep all unknown copies protected and do not select numeric floors without source-backed owner inputs.


## Stage A.5 — T4 RET-03 Owner Input Resolution (2026-11-10)

- Added `docs/evidence/p1-8/T4_RET03_OWNER_INPUT_RESOLUTION_2026-11-10.md` as a documentation-only static trace of the current five-layer React `control_dashboard`, common API read paths, data dependencies, caches/build/export surfaces and retention ownership.
- Source baseline HEAD: `0052c7821f8e01379d4d6a69acad8d2340b044fb`; exact selected source blob SHAs are pinned in the report.
- Scope excludes Android Chart/Scanner and the legacy standalone backtest `dashboard/index.html`; neither is treated as the current five-layer T4 application.
- Confirmed: React dashboard polls nine read endpoints every five seconds while visible; state and bearer tokens are held in memory, not browser persistent storage per README; request/API cache directives are no-store; charts are derived from bounded API responses; no explicit export/download function was found in selected current T4 React source.
- T0 candle responses remain T0-owned canonical data; T1 intelligence report/CSV evidence remains T1-owned; T2 prediction/model provenance remains T2-owned; paper/audit/ledger/risk state remains T3-owned. T4 view limits/polling/request limits do not define source retention.
- Critical finding T4-RET-01: GET `/v1/equity` calls `equity_snapshot()` and `PaperLedger.record_equity()`, which persist `paper_equity_history` and `paper_daily_baselines`. UI polling may invoke this path repeatedly; actual deployment/frequency NOT VERIFIED. These records are T3 risk/reconstruction evidence, not disposable T4 cache. Do not change or delete them in this workstream.
- Hummingbot order-book process cache is three seconds in source; candidate ephemeral only after runtime/copy and T3 fill-reference closure. Fill-referenced book evidence remains protected.
- Gateway remains architecture-only: route/auth mapping exists, but route translation to the target Gateway namespace, deployment, TLS/firewall and runtime origin remain NOT VERIFIED. Actual dist hashes, browser/proxy/CDN/service-worker/log/screenshot/download/export copies and consumers remain NOT VERIFIED.
- T4 RET-03 OPEN / FLOOR_NOT_ESTABLISHED. No numeric floor/TTL selected; no object deletion-eligible. No retention value inferred from 3-second cache, 5-second polling, request timeout, 50-row audit view, 240-point chart, API limits or build tooling.
- Tests NOT RUN; GitHub Actions NOT DISPATCHED; no workflow run/artifact. No build/deployment/runtime/browser/proxy/consumer/copy inventory, legal determination, source/schema/config/workflow/permission/runtime/data change or destructive operation.
- Option C, lifecycle reviewer waiver boundaries, T0 independence, separate ledgers, required T3 reconstruction evidence, paper-only and `AI_EXECUTION_ENABLED=false` unchanged.
- T4 analysis commit: `ab8585cd9e1a00762a9254edb7ce58c622f42194`; report blob SHA verified by read-back.
- Next step: Stage A.6 — consolidate T0–T4 RET-03 owner-input gaps into one documentary class/obligation matrix and identify which missing owner inputs can be resolved from authoritative repository records versus which require explicit owner/operational/legal evidence. Do not select numeric floors or authorize lifecycle actions.


## Stage A.6 — T0–T4 RET-03 Consolidated Owner-Input Matrix (2026-11-10)

- Added `docs/evidence/p1-8/T0_T4_RET03_CONSOLIDATED_OWNER_INPUT_MATRIX_2026-11-10.md` as a documentation-only consolidation of Stage A.1–A.5.
- Frozen source baseline HEAD before this increment: `1f0ec96fb1a99406a484e6c4057db616583ec35e`.
- Pinned report blobs: A.1 `e26d056f9f0c2ea57a9951a650b29af11939c422`; A.2 `061ea9340e07a9f633a8864928c945f44adc5295`; A.3 `8d5a4172a28044539c8ccf451866b197735d1617`; A.4 `1b73122e1d7eb6d582462a3d8013d7b6f4f6edcb`; A.5 `cc6c0d9f193b1abb8194a6865cac43f9e8667466`.
- Consolidates T0 canonical/recovery protection; T1 raw CSV, proposed 1m kline and connection-sidecar separation; T2 ephemeral inference versus model/training/decision lineage; T3 signals/risk/orders/reservations/fills/ledgers/equity/replay; and T4 presentation/cache versus persistent T3 side effects and unknown deployment/export copies.
- Maps cross-layer dependencies and identifies non-terminal events: read/ACK/consumption, job completion, prediction replacement, order expiry/cancel, fill completion, replay completion, cache TTL, dashboard polling and display limits.
- Separates further repository-document reconciliation from owner/operational/legal evidence that is not present. No numeric floor, TTL, positive terminal event or deletion eligibility is inferred.
- Result: T0–T4 documentary matrix PASS within inspected report scope; RET-03 OPEN / FLOOR_NOT_ESTABLISHED; RET-07 OPEN; full consumer/copy/restore inventory NOT VERIFIED; owner/legal/operational inputs NOT PROVIDED.
- Tests NOT RUN; GitHub Actions NOT DISPATCHED; no workflow run/artifact claimed. No runtime/VPS/DB/provider/legal/inventory probes, source/schema/config/workflow/permission/data changes, or destructive operations.
- Option C unchanged; T0 remains independent; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false`.
- Matrix file commit: `403c993f6d74aac9620e3d0fbbd26219a201c34f`; matrix blob SHA verified by read-back: `4f51bd8a959b47df3c38275d70dd414d4a317ad7`.
- Handoff update commit before this read-back note: `5f1d4a7e9fa39aca6b736f7bda7aacde1a0d46cd`; handoff blob read-back: `2cdadbdc233543cb319da10b5adf09f28c236e79`.
- Next step: only a bounded documentary search for already-committed authoritative owner/obligation records that resolve specific missing inputs; where none exist, record NOT PROVIDED and stop for that class. RET-06/RET-08 remain separate Stage A items; Stage B/C require separate scope/authorization.


## Stage A.7 — Governance and Owner-Source Reconciliation (2026-11-10)

- Added `docs/evidence/p1-8/STAGE_A7_GOVERNANCE_OWNER_SOURCE_RECONCILIATION_2026-11-10.md` as a documentation-only review of pinned lifecycle governance records and bounded repository discovery.
- Frozen baseline HEAD: `85256312da7bcf3d06f91abc404b63deb1e89aa0`.
- Confirmed lifecycle independent-review waiver blob `555951e36f6365012cb5b9e48ba24e455b775d16` authorizes only waiver of the human-review gate; it does not provide class-specific retention purpose, owner/custodian, obligation, numeric duration, start/terminal event or deletion authority.
- Confirmed lifecycle dependency plan blob `bfbd3ae5ec49e644632c72a1865745628ef574f3` is a planning/acceptance document, not an authoritative legal/operational retention schedule. RET-03/07, RET-06 and RET-08 remain open.
- Reviewed consolidated T0–T4 matrix blob `4f51bd8a959b47df3c38275d70dd414d4a317ad7`, crosswalk blob `3d084c04cd9712ed05d790ce5c431e988b64ce32`, P1.8.152 historical blob `e1a4d95af216e94a58fa5528850fcd0c1ff465f8` and T1 owner-input report blob `061ea9340e07a9f633a8864928c945f44adc5295`.
- No new authoritative class-specific owner/obligation source was found in the pinned governance set. T1 report references Central Data Lifecycle Policy design blob `9fd46c029cff643ccc35492fd09620581f6eff35`, but exact current-branch document path/content and approval status were not independently resolved; not treated as normative.
- Bounded GitHub code search uses default-branch index and is not exhaustive for this feature branch; no exhaustive-negative repository claim is made. F-07–F-09 remain NOT VERIFIED.
- Result: review-waiver and Option C boundaries confirmed; class-specific owner/obligation, numeric floors, start/terminal events, RET-06 values and RET-08 authority protocol remain NOT PROVIDED / OPEN; RET-09 inventory NOT VERIFIED.
- Tests NOT RUN; Actions NOT DISPATCHED; no runtime/VPS/DB/provider/legal/permission/consumer/copy probes; no source/schema/config/workflow/permission/runtime/data changes or destructive actions.
- Stage A.7 report commit: `5f975ed000ca53b0b0c78db9186182500dbaf81d`; report blob and final handoff commit to be verified by read-back.
- Automatic owner approval applies to bounded documentary work across Stage A only. Continue Stage A.8 by specifying RET-06 and RET-08 required input/decision fields and fail-closed outcomes, without selecting values or authorizing exceptions. Stage B/C remain outside approval.


## Stage A.8 — RET-06 / RET-08 Documentary Input Contracts (2026-11-10)

- Added `docs/evidence/p1-8/STAGE_A8_RET06_RET08_DOCUMENTARY_INPUT_CONTRACTS_2026-11-10.md` as documentary requirements only.
- Frozen baseline HEAD: `21b4f9f5aba3392760ca7f6e7069262abd8ce662`.
- RET-06 contract enumerates policy/authorization identity, grace semantics/value, cancellation authority and race ordering, authorization lifetime/revocation, evidence freshness, trusted clock, revision binding, expiry behavior, evidence and recovery/replay requirements. All owner values remain NOT PROVIDED; V07, RET-05/LDA-05, V08, RET-07 and Restore dependencies remain unresolved.
- RET-08 contract enumerates request categories and required requester/authority/jurisdiction/scope/deadline/conflict/decision/execution/evidence fields; defines a preserve/verify/escalate/fail-closed sequence. No competent authority register, legal/security protocol, exception or break-glass path is approved.
- Explicitly separates request receipt/validation/decision from execution authority. Emergency/legal/security label, deadline or request does not bypass Option C, protected classes, RET-06, owner approval or technical gates.
- Result: RET-06 and RET-08 documentary requirements PASS; substantive values/authority remain NOT PROVIDED / OPEN. No legal interpretation, numeric value, runtime implementation or mutation authority.
- Tests NOT RUN; Actions NOT DISPATCHED; no runtime/legal-system/provider/permission/copy probes, source/schema/config/workflow/permission/data changes or destructive actions.
- Stage A.8 report commit: `c4d751504145d2650a53dab9bc74da1a79eef2f9`; report blob and handoff commit to be verified by read-back.
- Next: Stage A.9 — consolidate RET-03/06/07/08 into a single Stage A acceptance checklist and owner-input register; distinguish documentary completeness from unresolved owner/legal/operational inputs. If no authoritative source exists, preserve NOT PROVIDED and close Stage A as blocked on substantive inputs. No Stage B/C work without separate authorization.


## Stage A.9 — Lifecycle Stage A Acceptance Checklist (2026-11-10)

- Added `docs/evidence/p1-8/STAGE_A9_LIFECYCLE_STAGE_A_ACCEPTANCE_CHECKLIST_2026-11-10.md` consolidating Stage A.1–A.8 artifacts, acceptance criteria, unresolved owner-input register and exit disposition.
- Frozen baseline HEAD: `afd060c1eb8361184ba7bc4835716acb0b9144ac`.
- Documentary T0–T4 class/dependency map, RET-06 and RET-08 requirements vocabulary and governance boundary are complete within pinned source scope.
- Stage A is **DOCUMENTARILY COMPLETE BUT SUBSTANTIVELY BLOCKED**: RET-03 numeric floors/terminal events and RET-07 evidence floors have no owner/obligation source; RET-06 values/trusted-time profile are NOT PROVIDED; RET-08 competent authority/jurisdictional protocol is NOT PROVIDED; RET-09 inventory NOT VERIFIED; F-07–F-09 NOT VERIFIED.
- Lifecycle statuses unchanged: RET-03 OPEN/FLOOR_NOT_ESTABLISHED; RET-04 NON-EXECUTABLE; RET-05 technical enforcement NOT VERIFIED; RET-06 OPEN; RET-07 OPEN; RET-08 OPEN; RET-09 NOT VERIFIED; RET-10 OPEN/NOT VERIFIED; V07 BLOCKED; V08 OPEN/BLOCKED; Restore OPEN/BLOCKED; LDA-05/06 NOT VERIFIED; LDA-07 NOT RUN; LDA-08 HOLD/NOT VERIFIED; LDA-09 reviewer gate waived, documentary only; IR147-01 reviewer gate waived, substantive floor OPEN; L4-Minimum BLOCKED/NOT VERIFIED.
- No retention policy acceptance, numeric values, deletion eligibility or destructive authority resulted from Stage A completion.
- Tests NOT RUN; Actions NOT DISPATCHED; no runtime/VPS/DB/provider/legal/permission/consumer/copy probes; no source/schema/config/workflow/permission/runtime/data changes or destructive operations.
- Stage A.9 report commit: `c30f1f2a15e6665fbf78c5fe4b8bf3a1bdffef20`; report blob and final handoff commit to be verified by read-back.
- Next: stop at Stage A boundary. Collect the explicit owner/operational/competent legal inputs listed in the checklist. Stage B or C requires separate explicit authorization; automatic Stage A approval does not extend to either.


## Stage B.1 — T0 Lifecycle Technical Contract Assessment (2026-11-10)

- Owner explicitly approved Stage B.1 assessment only. Scope: documentary assessment of V07 trusted time/revocation, V08 durable checkpoint/seal ordering, RET-10 adapter/separate verifier, RET-05/LDA-05 mutation fencing and Restore/Recovery.
- Added `docs/evidence/p1-8/STAGE_B1_T0_LIFECYCLE_TECHNICAL_CONTRACT_ASSESSMENT_2026-11-10.md`.
- Frozen source baseline HEAD: `851f67881420d0e646d1663221a1de10bed03c59`.
- Pinned controlling plan blob: `bfbd3ae5ec49e644632c72a1865745628ef574f3`; lifecycle independent-review waiver blob: `555951e36f6365012cb5b9e48ba24e455b775d16`; Stage A.9 checklist blob: `dd67a21b741416889f8d0a1d16b205f3d7fdbcec`; Stage A.8 RET-06/08 contract blob: `286f47ef2d9e3d2a177218bd2544f09683a7bbcf`.
- Assessment result: V07 BLOCKED/NOT VERIFIED; V08 OPEN/BLOCKED; RET-10 OPEN/NOT VERIFIED; RET-05 policy boundary approved but technical enforcement NOT VERIFIED; LDA-05 NOT VERIFIED; Restore OPEN/BLOCKED. Requirements and dependencies are documented, but no technical contract is qualified and no status promoted to PASS.
- Bounded fetch did not locate dedicated standalone current-branch contract files at anticipated paths; this is not an exhaustive repository-absence claim. No source implementation was qualified.
- Dependency sequence proposed: B.2 V07; B.3 V08; B.4 RET-10; B.5 RET-05/LDA-05; B.6 Restore. Each later increment requires separate approval.
- Tests NOT RUN; Actions NOT DISPATCHED; no runtime/VPS/DB/provider/permission/consumer/copy/backup/legal probes; no source/schema/config/workflow/permission/runtime/data changes or destructive actions.
- Human independent review remains owner-waived; technical/environmental verifier separation remains mandatory. Option C and protected classes unchanged.
- Stage B.1 report commit: `970c7c303f0eb2dc23622d350897f269c1592bce`; report blob and final handoff commit to be verified by read-back.
- Next proposed increment: B.2 documentary V07 trust/time/revocation contract specification only. No provider/key/trust-root selection, numeric freshness/clock threshold, implementation, tests, Actions or runtime probes without separate explicit approval.


## Stage B.2–B.6 — T0 Lifecycle Technical Contract Package (2026-11-10)

- Owner approved automatic completion of all Stage B documentary increments B.2–B.6 on the existing branch. Approval does not extend to Stage C or implementation/execution.
- Added five contract documents: B.2 V07 trusted time/revocation; B.3 V08 checkpoint/seal/watermark/correction; B.4 RET-10 adapter and technically separate verifier; B.5 RET-05/LDA-05 mutation-fence state machine; B.6 Restore/Recovery oracle, epoch/fencing and measurement contract.
- Exact read-back blob SHAs: B.2 `40fccef3d95a52a32008a70e378603be79a49966`; B.3 `8a88a89d7d751904f7c78221b543f9135fb985fc`; B.4 `5e0423d923a15a5a6c8d4ac55b3ad36985ce5149`; B.5 `a6bb72708d03854f7b8b1a3ca7fc78c565a19af2`; B.6 `6511bb848663fe07c4d1d73010653f93e07b539c`.
- Added consolidated package/acceptance record: `docs/evidence/p1-8/STAGE_B_T0_LIFECYCLE_TECHNICAL_CONTRACT_PACKAGE_2026-11-10.md`; commit `8cbe2ec0fa064bc6fa09aa51423be3b9bc70ca9e`; blob SHA `cc95d07017b8b2ca78da5257512fe5e53d655f13`.
- Documentary Stage B package: COMPLETE. Technical qualification is not established. V07 BLOCKED/NOT QUALIFIED/NOT VERIFIED; V08 OPEN/BLOCKED/NOT QUALIFIED/NOT VERIFIED; RET-10 OPEN/NOT QUALIFIED/NOT VERIFIED; RET-05 technical enforcement NOT VERIFIED; LDA-05 NOT VERIFIED; Restore OPEN/BLOCKED/NOT VERIFIED.
- No PASS promotion. RET-03/06/07/08 owner-input gaps remain OPEN/NOT PROVIDED; RET-09/LDA-06 NOT VERIFIED; LDA-07 NOT RUN; LDA-08 HOLD/NOT VERIFIED.
- Tests NOT RUN; GitHub Actions NOT DISPATCHED; no runtime/VPS/DB/storage/provider/permission/consumer/copy/backup/legal probes; no source/schema/API/adapter/scheduler/workflow/secret/key/permission/runtime/data changes.
- No staging, restore, fault injection, provider/key operation, or destructive lifecycle operation. Option C and protected data classes unchanged. AI_EXECUTION_ENABLED=false; no live orders.
- Independent human review remains owner-waived; technical/environmental verifier separation remains mandatory. No independent assurance claim.
- Next: stop at Stage B documentary boundary. Stage C, implementation, test execution, provider selection, permissions review/change, staging or runtime work requires separate bounded owner authorization.


## Stage C.1 — Read-Only Repository Inventory and Enforcement Evidence Baseline (2026-11-10)

- Owner explicitly approved automatic Stage C. Began with a bounded read-only GitHub repository/configuration inventory on the existing branch; no runtime, secret-value, permission-change or destructive access.
- Frozen source commit inspected: `d82475036f4bb731ea8ae65a4338d814e2e1399b`; recursive Git tree returned 745 entries, not truncated.
- Added `docs/evidence/p1-8/STAGE_C1_READ_ONLY_REPOSITORY_INVENTORY_2026-11-10.md`; commit `c4a8a62964850203513dc2054d74e7a31e441b52`; read-back blob SHA `f541d035e318bfe628da0d6a14fcb44b2e2ddb10`.
- Frozen evidence includes P1.8.141 blob `c20616d79f6dcedde08128f589a5c0e04d6257f1`, P1.8.152 blob `e1a4d95af216e94a58fa5528850fcd0c1ff465f8`, P1.8.90 blob `8014ef15f347d255ee3d02f6f28847a02db27aff`, P1.8.94 blob `4588379d8e101ee496bcf8927186c6c989e6c6a6`, L4 matrix blob `2ba85af550fb7e369ea39ade6d73878d78dbf6bc`, synthetic workflow blob `bbe9361cbbeed4f881edc4ce4fbe727d6937ad78`, CI decision blob `68c14033f32bdd8bbbd675ed58ea8157f95dcb3d`, CI policy test blob `f5ef5213c8356cacc441b59ec8e1a06ccd4a61da`.
- LDA-06: repository tree/static candidate surfaces inventoried only. Live consumers, actual dependencies, database/WAL/snapshot copies, VPS backups, replicas, exports, caches, recipients, provider-side copies and restore paths remain NOT VERIFIED. No completeness claim.
- LDA-08: 14 workflow YAML files statically inventoried. Connected GitHub principal metadata reports repository admin permission; this does not establish workflow-job, runner, OIDC, environment or provider effective permissions. Repository rulesets query returned an empty list; branch-protection read returned HTTP 403, therefore effective branch protection NOT VERIFIED. Secret references were identified by name only; no secret values read. P1.8 synthetic workflow has `id-token:write` and `attestations:write`; T0 manual validation and Android release workflows reference secret names and were not dispatched.
- LDA-07: 87 vector IDs confirmed in P1.8.94. P1.8.90 requires isolated synthetic fixtures, disposable storage, deterministic concurrency, independent oracle and artifact provenance; TEST-01–08 remain open. Existing synthetic evidence workflow is not proven to implement all 87 lifecycle vectors. Tests NOT RUN; Actions NOT DISPATCHED.
- Stage C.1 disposition: LDA-06 PARTIAL / NOT VERIFIED; LDA-07 NOT RUN; LDA-08 HOLD / NOT VERIFIED. No PASS promotion. Option C, protected data and paper-only posture unchanged.
- No secret values, runtime/VPS/DB/provider/Codemagic/recipient/backup/replica access; no workflow/runner/branch/ruleset/secret/permission changes; no source/schema/API/adapter/runtime/data changes; no destructive operations.
- Next: static source-level consumer/dependency crosswalk; inspect workflow job steps and permission boundaries without secret values; map existing tests to all 87 vector IDs and identify uncovered vectors. Do not dispatch/run until runner, isolation, independent oracle, fixtures, artifact provenance and cleanup containment are evidenced. External/provider/runtime inventory and permission mutations remain out of this read-only baseline.


## Stage C.2 — Static Consumer/Dependency Crosswalk and Negative-Vector Test Mapping (2026-11-10)

- Continued owner-approved Stage C with read-only GitHub source/test/workflow inspection. Frozen source commit remains `d82475036f4bb731ea8ae65a4338d814e2e1399b`.
- Added `docs/evidence/p1-8/STAGE_C2_STATIC_CONSUMER_AND_VECTOR_CROSSWALK_2026-11-10.md`; commit `c19e32e90e6dd08edacda6c7cf4ad1cdebcdfd34`; read-back blob SHA `91a3f081dd22045b735c282ef9a014ba47f6db57`.
- Static crosswalk recorded T0 fenced SQLite writer/read API; T1 CSV importer/snapshot; T2 T0 HTTP candle consumer/artifact; T3 SQLite paper ledger and pure replay reconciliation; T4 API client. This is source-declared relationships only; live consumers and full copy graph remain NOT VERIFIED.
- Inspected synthetic test modules for cross-process atomicity, durability/recovery, event signatures, generator, provenance, reservation lifecycle, shared risk, T0 checkpoint, trust anchor/lifecycle/root pin and durable Root B checkpoint. They cover adjacent technical contracts, not the lifecycle negative-vector suite.
- P1.8.94 states 87 unique lifecycle vector IDs, all NOT_RUN. No direct executable binding from inspected synthetic test methods to lifecycle NEG IDs was established. Bounded GitHub code searches for representative IDs returned no indexed matches, but search is not exhaustive for this feature branch. No coverage percentage or PASS inferred.
- Inspected P1.8 synthetic workflow: unittest discovery for synthetic_evidence, deterministic fixture generation, Sigstore trusted-root/attestation, separate attestation verification and append-only evidence archive commit. It requests id-token:write and attestations:write; it is not a dedicated 87-vector runner and dispatch is not read-only. No Actions run dispatched.
- Existing `ci/test_ci_policy.py` still asserts no active GitHub Actions workflows, conflicting with the 14 workflow YAMLs; CI ownership decision records this unresolved contradiction. No edits/tests.
- LDA-06 PARTIAL / NOT VERIFIED; LDA-07 NOT RUN; LDA-08 HOLD / NOT VERIFIED; V07/V08/Restore remain blocked/not qualified. Option C and protected T0/T3/CORE_LEDGER/AI_LEDGER evidence unchanged.
- GitHub integration branch-protection endpoint returned HTTP 403 in C.1. To close this bounded LDA-08 metadata gap, request only repository `Administration: read-only` (or equivalent branch-protection/rulesets read access). Do not grant Administration write, Contents write, Secrets write or Actions write for this inspection. Until granted, branch protection remains NOT VERIFIED.
- Tests/compile/dry-run/fault injection NOT RUN; Actions NOT DISPATCHED; no secret values read; no runtime/VPS/DB/provider/Codemagic/recipient/backup/replica probes; no permission/secret/workflow/runner/source/schema/runtime/data changes; no destructive operations.
- Next: complete remaining static path-level consumer crosswalk and vector-by-vector mapping register. Any test harness implementation, Actions execution, external/runtime inventory or permission mutation requires a separate bounded authorization and TEST-01–08 prerequisite evidence.


## Stage C.3 — Lifecycle Negative-Vector Mapping Register (2026-11-10)

- Owner approval interpreted as authorization to continue bounded documentary Stage C work only. It does not grant repository permission changes, test execution, Actions dispatch, runtime/provider access or destructive authority.
- Reconciled P1.8.90 (47 distinct IDs; blob `8014ef15f347d255ee3d02f6f28847a02db27aff`) and P1.8.94 (70 distinct IDs; blob `4588379d8e101ee496bcf8927186c6c989e6c6a6`): 17 IDs appear only in P1.8.90, 40 only in P1.8.94, deduplicated union = 87 distinct IDs.
- Added `docs/evidence/p1-8/STAGE_C3_LIFECYCLE_NEGATIVE_VECTOR_MAPPING_REGISTER_2026-11-10.md`; commit `3efd18dec0b6c36bdb61292e86c7c7d12c560dbd`. Register records all 87 vector IDs, nearest existing synthetic test modules where relevant, and explicit distinction between domain adjacency and direct test coverage.
- Static mapping result: no direct executable binding to any lifecycle vector ID established in inspected test sources. This is NOT proof of repository-wide absence; GitHub code search is not exhaustive. 87/87 remain NOT_RUN; no coverage credit assigned to adjacent-domain tests.
- TEST-01–05 and TEST-07 remain OPEN / NOT ESTABLISHED; TEST-06 has adjacent Sigstore machinery but lifecycle run binding NOT ESTABLISHED; TEST-08 separate exact test authorization NOT GRANTED by this documentary mapping approval.
- LDA-07 NOT RUN; LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED. V07/V08/RET-10/Restore remain BLOCKED or NOT VERIFIED. Option C unchanged.
- No tests/compile/dry-run/fault injection, Actions dispatch, secrets read, runtime/VPS/DB/provider/recipient/backup/replica probes, permission/workflow/source/schema/adapter/runtime/data changes, or destructive operations.
- Next bounded work: complete remaining static source/path crosswalk and prepare precise prerequisite closure proposals for TEST-01–07; do not implement or run harness until prerequisites are evidenced and TEST-08 exact scope is separately approved. Branch-protection metadata still requires GitHub Administration: read-only (or equivalent) to resolve HTTP 403; no such grant asserted.


## Stage C.4 — TEST-01–07 Prerequisite Closure Plan (2026-11-10)

- Added `docs/evidence/p1-8/STAGE_C4_TEST_PREREQUISITE_CLOSURE_PLAN_2026-11-10.md` as a documentation-only prerequisite plan. File commit: `9b763c13c640c9ef8f7be574360b2bb0e3ea6d74`.
- Defines evidence-bearing entry gates for TEST-01 runner, TEST-02 synthetic adapters, TEST-03 isolation, TEST-04 independent oracle, TEST-05 deterministic concurrency, TEST-06 lifecycle-specific provenance and TEST-07 synthetic-only cleanup containment.
- Specifies cross-cutting fail-closed, synthetic namespace, no-secret/no-network, protected-root invariance, independent observation, reproducibility, vector-level coverage and abort invariants.
- TEST-08 remains a separate exact-scope owner authorization gate. This plan does not authorize implementation, tests, dry-run, fault injection, Actions dispatch, permission changes, secrets access, runtime/provider/VPS/database probes or destructive operations.
- Current states remain TEST-01–05 OPEN / NOT ESTABLISHED; TEST-06 PARTIAL / NOT ESTABLISHED; TEST-07 OPEN / NOT ESTABLISHED; TEST-08 NOT GRANTED. LDA-07 NOT RUN (87/87); LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED.
- No test, compile, dry-run, fault injection or Actions dispatch. No source/schema/adapter/workflow/runner/permission/runtime/data changes. No secret values read. Option C and protected T0/T3/CORE_LEDGER/AI_LEDGER evidence remain unchanged.
- Next: keep implementation blocked; resolve prerequisite evidence one bounded contract at a time. Before any harness execution, obtain TEST-08 exact authorization and prove all relevant TEST-01–07 gates. No automatic promotion from documentary completion to execution.


## Stage C.5 — TEST-01 Lifecycle Runner Contract (2026-11-10)

- Added `docs/evidence/p1-8/STAGE_C5_TEST01_LIFECYCLE_RUNNER_CONTRACT_2026-11-10.md`; documentation-only contract commit `b76e743a378a56062d44c4da71eb68077e7c9c6e`.
- Defines manifest fields, strict validation, explicit vector selection, one-to-one vector/test mapping, per-vector result schema, run-level exit semantics, deterministic discovery/order/retries, reproducibility, evidence completeness and fail-closed isolation assumptions.
- Runner must have no cleanup capability; network DENY_ALL; synthetic adapters only; no secrets; no path/backend fallback to canonical systems. T0 canonical data/recovery copies, CORE_LEDGER, AI_LEDGER and T3 reconstruction/audit evidence remain protected.
- TEST-01 status: CONTRACT DOCUMENTED / IMPLEMENTATION NOT ESTABLISHED; not closed. TEST-02–05 and TEST-07 remain OPEN / NOT ESTABLISHED; TEST-06 PARTIAL / NOT ESTABLISHED; TEST-08 NOT GRANTED. LDA-07 NOT RUN (87/87); LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED.
- No implementation, tests, compile, dry-run, fault injection or Actions dispatch. No secrets/runtime/VPS/database/provider/recipient/backup/replica access. No source/schema/adapter/workflow/runner/permission/runtime/data changes; no destructive operation.
- Next bounded step: Stage C.6 TEST-02 Synthetic Adapter Interface Contract. No implementation or execution until prerequisites are evidenced and TEST-08 exact scope is separately approved.


## Latest completed work — Stage C.6 / TEST-02

- Added documentation-only contract: `docs/evidence/p1-8/STAGE_C6_TEST02_SYNTHETIC_ADAPTER_INTERFACE_CONTRACT_2026-11-10.md`.
- Report commit: `295a62e68859ed49e6dde13ef58b82812f6c05de`; report blob SHA to be verified by read-back.
- Defines language-neutral interfaces for synthetic object store, metadata registry, hold/authorization resolution, copy inventory/lineage, checkpoint/manifest/watermark, append-only audit/event sink, and namespace/capability resolver.
- Specifies immutable run/namespace/object/version identities; create-only object writes; exact-version reads; registry CAS; separate hold and authorization decisions; bounded lineage/inventory; idempotency and fencing; typed fail-closed errors; append-only evidence; no implicit backend discovery/fallback.
- Explicitly excludes destructive/cleanup capabilities, production backends, secrets, network, runtime probes and provider access. Logical adapter boundaries do not prove OS/container/network isolation; TEST-03 remains open.
- TEST-02: CONTRACT DOCUMENTED / IMPLEMENTATION NOT ESTABLISHED; not closed. TEST-03–05 and TEST-07 remain open; TEST-06 PARTIAL; TEST-08 NOT GRANTED and requires separate exact-scope authorization.
- LDA-07 remains NOT RUN; 87/87 lifecycle vectors remain NOT RUN. LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED.
- No tests, compile, dry-run, fault injection, Actions dispatch, secrets/permission/runtime/VPS/database/provider/recipient/backup/replica access, or source/schema/adapter/workflow/runner/permission/runtime/data changes. No destructive operation.
- Next bounded documentary step: Stage C.7 — TEST-03 Isolation Boundary Contract. Do not implement or execute until prerequisite evidence and separate exact execution authorization are established.


## Latest completed work — Stage C.7 / TEST-03

- Added documentation-only isolation contract: docs/evidence/p1-8/STAGE_C7_TEST03_ISOLATION_BOUNDARY_CONTRACT_2026-11-10.md.
- Report commit: 7fe77c51e39895406354ca385b751a3ecda32b16; report blob SHA verified by read-back.
- Defines trust zones and boundaries for controller/manifest, executor, synthetic resources, independent oracle, evidence zone and host/runner.
- Specifies non-privileged process identity; no host namespaces/sockets/devices; filesystem and mount allowlist; traversal/symlink/hard-link/mount escape denial; initial network DENY_ALL; no DNS/proxy/tunnel/socket bypass; no secrets or ambient identity; pinned dependencies/configuration; run-bound synthetic storage; GitHub Actions least-privilege and ephemeral-runner requirements.
- Defines ISO-01–ISO-12 evidence package, ISO-T01–ISO-T15 future acceptance assertions, stop conditions and closure criteria.
- Contract is not proof of effective isolation. TEST-03: CONTRACT DOCUMENTED / EFFECTIVE ISOLATION NOT VERIFIED; not closed. TEST-04/05/07 remain open; TEST-06 PARTIAL; TEST-08 NOT GRANTED and requires separate exact-scope authorization.
- LDA-07 remains NOT RUN; 87/87 lifecycle vectors remain NOT RUN. LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED.
- No tests, compile, dry-run, fault injection, provisioning, Actions dispatch, secrets/permission/runtime/VPS/database/provider/recipient/backup/replica access, source/workflow/runner/permission/runtime/data changes or destructive operation.
- Next bounded documentary step: Stage C.8 — TEST-04 Independent Oracle Contract. Do not implement or execute until prerequisites and separate exact execution authorization are established.


## Latest completed work — Stage C.8 / TEST-04

- Added documentation-only independent oracle contract: docs/evidence/p1-8/STAGE_C8_TEST04_INDEPENDENT_ORACLE_CONTRACT_2026-11-10.md.
- Report commit: f8196ef23d02bec38cd29c63793fc509cb596370; report blob SHA verified by read-back.
- Defines role separation across owner/specification authority/controller/executor/observer/evaluator/evidence publisher; frozen expected-state package; independent read-only observations; exact object/version and namespace binding; deterministic comparison; PASS/FAIL/INDETERMINATE and run-level BLOCKED/NOT RUN semantics.
- Specifies evidence provenance and append-only integrity, replay without re-execution, disagreement handling, protected-root invariance, ORA-01–ORA-15 evidence package and ORA-T01–ORA-T15 future acceptance assertions.
- Contract does not establish an existing independent oracle. TEST-04: CONTRACT DOCUMENTED / INDEPENDENT ORACLE NOT ESTABLISHED; not closed. TEST-01/02 implementation not established; TEST-03 effective isolation not verified; TEST-05/07 open; TEST-06 partial; TEST-08 not granted.
- LDA-07 remains NOT RUN; 87/87 lifecycle vectors remain NOT RUN. LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED.
- No tests, compile, dry-run, fault injection, provisioning, Actions dispatch, secrets/permission/runtime/VPS/database/provider/recipient/backup/replica access, source/schema/adapter/workflow/runner/permission/runtime/data changes or destructive operation.
- Next bounded documentary step: Stage C.9 — TEST-05 Deterministic Concurrency Contract. Do not implement or execute until prerequisites and separate exact execution authorization are established.


## Latest completed work — Stage C.9 / TEST-05

- Added documentation-only deterministic concurrency contract: docs/evidence/p1-8/STAGE_C9_TEST05_DETERMINISTIC_CONCURRENCY_CONTRACT_2026-11-10.md.
- Report commit: d4e4ee8fbd5610ef18d99e083cdff9d77b67a85b; report blob SHA verified by read-back.
- Defines explicit consistency-model declaration; immutable/materialized bounded schedules; deterministic barriers/interleavings; competing writers; duplicate delivery/idempotency; retry after ambiguous acknowledgement; lease/epoch fencing and stale-owner rejection at mutation boundary; causal event ordering; checkpoint/cursor races; reader visibility; synthetic crash/restart boundaries.
- Specifies independent TEST-04 oracle binding, PASS/FAIL/INDETERMINATE/BLOCKED/NOT RUN semantics, abort behavior, evidence package CON-01–CON-15 and future acceptance assertions CON-T01–CON-T15.
- Contract does not select a concurrency algorithm or prove current systems are race-safe. TEST-05: CONTRACT DOCUMENTED / DETERMINISTIC CONCURRENCY NOT ESTABLISHED; not closed. TEST-01/02 implementation not established; TEST-03 effective isolation not verified; TEST-04 independent oracle not established; TEST-06 partial; TEST-07 open; TEST-08 not granted.
- LDA-07 remains NOT RUN; 87/87 lifecycle vectors remain NOT RUN. LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED.
- No tests, compile, dry-run, fault injection, provisioning, Actions dispatch, secrets/permission/runtime/VPS/database/provider/recipient/backup/replica access, source/schema/adapter/workflow/runner/permission/runtime/data changes or destructive operation.
- Next bounded documentary step: Stage C.10 — TEST-06 Lifecycle-Specific Provenance Contract. Do not implement or execute until prerequisites and separate exact execution authorization are established.


## Latest completed work — Stage C.10 / TEST-06

- Added documentation-only lifecycle-specific provenance contract: `docs/evidence/p1-8/STAGE_C10_TEST06_LIFECYCLE_SPECIFIC_PROVENANCE_CONTRACT_2026-11-10.md`.
- Report commit: b917c89e3b89935530b009fea35372ac3cc6839f; report blob SHA to be verified by read-back.
- Defines the complete source/spec/vector → manifest → principal/process → operation/attempt → synthetic resource/version → event/independent observation → oracle assertion/verdict → artifact/publication chain.
- Separates completeness, integrity, authenticity, attribution, causal consistency, independence and reproducibility; explicitly states that hashes, signatures, workflow attestations and artifact upload alone do not establish all these properties.
- Specifies immutable identifier classes, versioned canonical provenance envelopes, exact source/spec/run/namespace/resource bindings, effective principal/capability evidence, event causality, replay/substitution/gap/fork detection, append-only corrections, trust/time claim limits, deterministic verifier sequence, PRV-01–PRV-17 evidence package and PRV-T01–PRV-T18 future acceptance assertions.
- Does not select a serialization, digest/signature algorithm, attestation provider, TSA, trust root or key-management technology. No implementation or test coverage is claimed.
- TEST-06: CONTRACT DOCUMENTED / LIFECYCLE-SPECIFIC PROVENANCE NOT ESTABLISHED; not closed. TEST-01/02 implementation not established; TEST-03 effective isolation not verified; TEST-04 independent oracle not established; TEST-05 deterministic concurrency not established; TEST-07 open; TEST-08 NOT GRANTED.
- LDA-07 remains NOT RUN; 87/87 lifecycle vectors remain NOT RUN. LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED.
- No tests, compile, dry-run, fault injection, provisioning, Actions dispatch, secrets/permission/runtime/VPS/database/provider/recipient/backup/replica probes, source/schema/adapter/workflow/runner/permission/runtime/data changes or destructive operations.
- Next bounded documentary step: Stage C.11 — TEST-07 Synthetic-Only Cleanup Containment Contract. Option C remains active; TEST-08 exact-scope authorization is still required before any lifecycle test execution.


## Latest completed work — Stage C.11 / TEST-07

- Added documentation-only synthetic-only cleanup containment contract: `docs/evidence/p1-8/STAGE_C11_TEST07_SYNTHETIC_ONLY_CLEANUP_CONTAINMENT_CONTRACT_2026-11-10.md`.
- Report commit: f20a3c0aae94ebac8add5f66c9e449f81a3084a4; report blob SHA to be verified by read-back.
- Defines resource classification, immutable run-bound synthetic namespace, exact target manifest, complete inventory/lineage, independent pre/post observation, role separation, two-phase plan/execution authorization, fail-closed abort and append-only evidence requirements.
- Explicitly preserves Option C — No Destructive Authority. No cleanup/deletion/archive/expiry/compaction/vacuum capability, implementation, dry-run, test or execution is authorized or introduced. Any future destructive operation requires separate exact owner approval; TEST-08 remains a separate execution gate.
- Protected T0 canonical data/recovery copies, CORE_LEDGER, AI_LEDGER, required T3 reconstruction/audit evidence, governance history, backups/replicas/snapshots/exports and unknown/unclassified objects remain ineligible.
- Specifies CLN-01–CLN-16 evidence package and CLN-T01–CLN-T16 future acceptance assertions. Contract does not prove current isolation, inventory completeness or cleanup containment.
- TEST-07: CONTRACT DOCUMENTED / CLEANUP CONTAINMENT NOT ESTABLISHED; not closed. TEST-01/02 implementation not established; TEST-03 effective isolation not verified; TEST-04 independent oracle not established; TEST-05 deterministic concurrency not established; TEST-06 lifecycle provenance not established; TEST-08 NOT GRANTED.
- LDA-07 remains NOT RUN; 87/87 lifecycle vectors remain NOT RUN. LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED.
- No tests, compile, dry-run, fault injection, provisioning, Actions dispatch, cleanup/deletion/destructive operation, secrets/permission/runtime/VPS/database/provider/recipient/backup/replica probes or source/schema/adapter/workflow/runner/permission/runtime/data changes.
- Next bounded documentary step: Stage C.12 — Consolidated TEST-01–07 Contract Traceability and Cross-Contract Consistency Review. This remains documentation-only; no implementation or execution authority follows automatically.


## Latest completed work — Stage C.12 / TEST-01–07 Cross-Contract Review

- Added documentation-only owner static consistency review: `docs/evidence/p1-8/STAGE_C12_TEST01_07_CROSS_CONTRACT_TRACEABILITY_REVIEW_2026-11-10.md`.
- Review commit: 68b1f2c7149634b802084e9c2ab63aa329916400; report blob SHA to be verified by read-back.
- Reviewed Stage C.4 and TEST-01–07 contracts C.5–C.11 as one architecture: runner, synthetic adapters, isolation, independent oracle, deterministic concurrency, lifecycle provenance and cleanup containment.
- Result: no blocking cross-contract contradiction found. Synthetic-only boundaries, protected roots, no-cleanup runner/adapter capabilities, independent observation, deterministic replay, append-only evidence, fail-closed verdicts and separate TEST-08 authorization are mutually consistent at the documentary level.
- Recorded four open integration findings: C12-F01 integrated schema/field registry (HIGH); C12-F02 87-vector-to-TEST-01–07 assertion traceability matrix (HIGH); C12-F03 immutable evidence-destination identity/retention binding (MEDIUM); C12-F04 editorial clarification to PRV-T04 (LOW).
- This is OWNER STATIC CONSISTENCY REVIEW, not Independent Review, technical verification or implementation assurance. TEST-01–07 remain NOT CLOSED. TEST-08 NOT GRANTED.
- 87/87 lifecycle vectors remain NOT RUN. LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED.
- No tests, compile, dry-run, fault injection, provisioning, Actions dispatch, secrets/permission/runtime/VPS/database/provider/recipient/backup/replica probes, source/schema/adapter/workflow/runner/permission/runtime/data changes or destructive operations.
- Next bounded documentary steps: C.13 integrated schema/field and evidence-destination contract map; C.14 87-vector applicability/assertion traceability matrix; C.15 consolidated owner static review and closure-readiness register. No implementation or execution authority follows automatically. Option C and TEST-08 gate remain unchanged.


## Latest completed work — Stage C.13 / Integrated Schema and Evidence-Destination Map

- Added documentation-only logical field map: `docs/evidence/p1-8/STAGE_C13_INTEGRATED_SCHEMA_FIELD_AND_EVIDENCE_DESTINATION_MAP_2026-11-10.md`.
- Report commit: 86f068f724975eb340f83a18e8e8d0b40d247106; report blob SHA to be verified by read-back.
- Defines the proposed logical `LIFECYCLE_EVIDENCE_CHAIN_V1` profile, common record envelope, TEST-01 root manifest, source/spec/vector, principal/process, operation/attempt, resource/event, observation/oracle, provenance/artifact/publication and TEST-07 cleanup-plan entity maps.
- Defines cardinality, immutable reference, cross-run/namespace rejection, causal lineage, denominator and append-only rules.
- Defines immutable evidence destination identity, trust zone, effective access policy, append-only publisher/verifier roles, retention/hold protection and separation from cleanup candidate namespaces. No provider, storage technology, retention value or permission is selected.
- C12-F01 and C12-F03 are RESOLVED AT LOGICAL DOCUMENTARY MAP LEVEL ONLY. Executable schemas, canonicalization, destination provider/effective permissions, retention and recovery evidence remain OPEN/NOT VERIFIED.
- C12-F02 remains OPEN for Stage C.14 87-vector applicability/assertion traceability. C12-F04 remains OPEN for Stage C.15 editorial correction.
- TEST-01–07 remain NOT CLOSED; TEST-08 NOT GRANTED; 87/87 lifecycle vectors remain NOT RUN. LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED.
- No tests, compile, dry-run, fault injection, provisioning, Actions dispatch, secrets/permission/runtime/VPS/database/provider/recipient/backup/replica probes, source/schema/adapter/workflow/runner/permission/runtime/data changes or destructive operations.
- Next bounded documentary step: Stage C.14 — 87-vector applicability and TEST-01–07 assertion traceability matrix. No implementation or execution authority follows automatically; Option C and TEST-08 remain unchanged.


## Latest completed work — Stage C.14 / 87-Vector Applicability Matrix

- Added documentation-only 87-row family-level matrix: `docs/evidence/p1-8/STAGE_C14_87_VECTOR_TEST01_07_APPLICABILITY_TRACEABILITY_MATRIX_2026-11-10.md`.
- Report commit: 2a52255fa9d5f55c0098c6fb2839bfe07d643ede; report blob SHA to be verified by read-back.
- Reconciled the exact 87 vector rows from Stage C.3 and mapped provisional candidate TEST-01–07 gates by control family.
- Explicit limitation: Stage C.3 register contains IDs/family labels/nearest modules but not the complete normative precondition/action/expected-state definition for each vector. Exact assertion IDs and N/A decisions were therefore not invented.
- Matrix result: 87/87 family-level candidate rows; 0/87 exact vector-to-assertion mappings established; 0/87 executed. Adjacent-domain tests receive no coverage credit.
- C12-F02 is PARTIALLY ADDRESSED only; exact source-catalogue semantic reconciliation and assertion-level mapping remain OPEN.
- TEST-01–07 remain NOT CLOSED; TEST-08 NOT GRANTED; LDA-07 87/87 NOT RUN; LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED.
- No tests, compile, dry-run, fault injection, provisioning, Actions dispatch, secrets/permission/runtime/VPS/database/provider/recipient/backup/replica probes, source/schema/adapter/workflow/runner/permission/runtime/data changes or destructive operations.
- Next bounded documentary step: Stage C.15 — reconcile exact source catalogue definitions, correct PRV-T04 wording, and produce the owner static closure-readiness register. If exact source definitions cannot be retrieved from the repository evidence, retain the vector mappings as BLOCKED/UNRESOLVED rather than infer semantics.


## Latest completed work — Stage C.15 / Owner Static Closure-Readiness Review

- Added owner static closure-readiness review: `docs/evidence/p1-8/STAGE_C15_OWNER_STATIC_CLOSURE_READINESS_REVIEW_2026-11-10.md`.
- Report commit: 4a73a11596a7dbe3aaaa29206b430c8920fa1e43; report blob SHA to be verified by read-back.
- C12-F01 resolved at logical field-map level by C.13; C12-F02 resolved at design-traceability level by revised C.14; C12-F03 resolved at logical evidence-destination contract level by C.13; C12-F04 corrected in C.10 PRV-T04 wording. None of these resolutions is technical closure.
- Exact P1.8.90/P1.8.94 blobs were fetched and reconciled: 87/87 source vector definitions matched; revised C.14 contains 87 unique rows with source scenario, expected result and proposed TEST-01–07 assertion references.
- Lifecycle execution remains 0/87; 87/87 NOT_RUN. TEST-01–07 remain NOT CLOSED; TEST-08 NOT GRANTED.
- Stage C.1–C.15 documentary package is complete for the currently approved scope. No automatic implementation/execution follows. A separate owner decision is required before any implementation proposal, tests, Actions dispatch, permission changes, runtime/provider probes or destructive operations.
- LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED; branch-protection read gap remains HTTP 403 with no permission change.
- Option C remains active; no cleanup/deletion/archive/expiry/compaction/vacuum or other destructive action was authorized or performed.
- No tests, compile, dry-run, fault injection, provisioning, Actions dispatch, secrets/permission/runtime/VPS/database/provider/recipient/backup/replica probes, source/schema/adapter/workflow/runner/permission/runtime/data changes or destructive operations.
- Next gate: Stage C documentary scope complete. Any further work requires a separately scoped owner decision; TEST-08 and all technical prerequisite gates remain mandatory.

## Stage C.15 reconciliation — canonical records and duplicate-file correction

The canonical Stage C.1–C.15 documentary sequence is complete. The following later revisions supersede earlier snapshots recorded above:

- **C.14 exact source-to-assertion revision:** commit `04634a8800748a1f724ad990be59bd1eb1568c1b`; canonical report `docs/evidence/p1-8/STAGE_C14_87_VECTOR_TEST01_07_APPLICABILITY_TRACEABILITY_MATRIX_2026-11-10.md`; blob `12bba6c475fc2ad8c4e2246e75034ede22d3bc20`. Exact P1.8.90/P1.8.94 definitions matched 87/87; design-level TEST-01–07 assertion mapping 87/87; executable lifecycle binding 0/87; execution 0/87. This supersedes the earlier C.14 family-level-only status and the earlier 0/87 exact-mapping statement above.
- **C.10 PRV-T04 editorial correction:** commit `b169cc74647eaad639504c96576ce0e865f7c3a3`; current C.10 blob `3fc63ae95b130d27de82cd615e9a79f6939fd62b`. Wording is now “Executor cannot self-author or forge authoritative observer/oracle/publisher records.” This is editorial only; role separation is not technically verified.
- **Canonical C.12:** `docs/evidence/p1-8/STAGE_C12_TEST01_07_CROSS_CONTRACT_TRACEABILITY_REVIEW_2026-11-10.md`; blob `2205caf4c177fa036eafd26ec65569a3c40e0aaf`.
- **Canonical C.15:** `docs/evidence/p1-8/STAGE_C15_OWNER_STATIC_CLOSURE_READINESS_REVIEW_2026-11-10.md`; commit `4a73a11596a7dbe3aaaa29206b430c8920fa1e43`; blob `7c7e49b722d4808c764b4a262b5ec7c79dd48b13`. It is the authoritative owner static closure-readiness review and records Stage C.1–C.15 documentary completion.

### Non-canonical duplicate files created during a later continuation

Two additional documentation files were created after their canonical Stage reports already existed. They are retained unchanged for repository-history transparency, but are **not canonical Stage C records**, do not supersede the reports above, and must not be used as the authoritative status source:

| Non-canonical file | Creation commit | Blob SHA | Canonical record to use |
|---|---|---|---|
| `docs/evidence/p1-8/STAGE_C12_TEST01_TEST07_CONTRACT_TRACEABILITY_AND_CONSISTENCY_REVIEW_2026-11-10.md` | `c480b47a51d2a1962540427f35dbc0cfb3f50ad4` | `c0f71695b3225f1e896a2bd0e8463c7dd5bd5e1e` | `STAGE_C12_TEST01_07_CROSS_CONTRACT_TRACEABILITY_REVIEW_2026-11-10.md` |
| `docs/evidence/p1-8/STAGE_C15_OWNER_STATIC_CLOSURE_READINESS_REGISTER_2026-11-10.md` | `6defe3ad77ef82a83fff01dfad7a4a9fef167efa` | `da7677065efe6d17699c77ff77fb1a61561e3e9a` | `STAGE_C15_OWNER_STATIC_CLOSURE_READINESS_REVIEW_2026-11-10.md` |

No deletion or overwrite was attempted because Option C remains active. Future handoffs and reports must cite only the canonical C.12 and C.15 paths above.

## Final Stage C status

- Stage C.1–C.15: DOCUMENTARY PACKAGE COMPLETE.
- TEST-01–07: CONTRACT DOCUMENTED; TECHNICAL CLOSURE NOT ESTABLISHED.
- TEST-08: NOT GRANTED.
- C12-F01/F03: RESOLVED AT LOGICAL DOCUMENTARY MAP LEVEL ONLY.
- C12-F02: RESOLVED AT DESIGN-LEVEL VECTOR/ASSERTION TRACEABILITY ONLY.
- C12-F04: RESOLVED EDITORIALLY ONLY.
- LDA-07: 87/87 NOT RUN; no executable lifecycle coverage.
- LDA-06: PARTIAL / NOT VERIFIED.
- LDA-08: HOLD / NOT VERIFIED; branch-protection read gap remains HTTP 403; no permission change.
- Option C: ACTIVE; no destructive authority.
- No tests, compile, dry-run, fault injection, Actions dispatch, runtime/provider/VPS/database probes, permission changes, implementation or destructive operations were performed.

**Stage C is complete for the approved documentary scope. Any next activity requires a separate owner decision; implementation, execution, TEST-08 and destructive authority are not granted by Stage C approval.**

## Latest completed work — Stage D.0–D.5 / Implementation Readiness and Execution Authorization Proposal

- Added documentation-only package: `docs/evidence/p1-8/STAGE_D0_D5_IMPLEMENTATION_READINESS_AND_EXECUTION_AUTHORIZATION_PROPOSAL_2026-11-10.md`.
- Report commit: `f1e38b7673c77842c3cc0aea1f5cbeb2773d0f62`; report blob SHA recorded after read-back.
- Owner approved automatic execution of Stage D steps within the previously proposed D.0–D.5 documentary scope. The package records prerequisite status, implementation dependency order, least-privilege permission design, the future TEST-08 request contract and owner disposition.
- D.1 conclusion: implementation/execution readiness BLOCKED. TEST-01/02 implementation NOT ESTABLISHED; TEST-03 NOT VERIFIED; TEST-04 NOT ESTABLISHED; TEST-05 NOT ESTABLISHED; TEST-06 NOT ESTABLISHED; TEST-07 NOT ESTABLISHED; TEST-08 NOT GRANTED; LDA-07 87/87 NOT RUN; LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED.
- D.2 documents a proposed dependency order only; no implementation authority.
- D.3 defines least-privilege principal boundaries and evidence-destination requirements; no permission change, secrets access or provider selection.
- D.4 records the minimum fields for a future exact-scope TEST-08 request. No vector subset, runner, run count, destination or isolation proof was approved; TEST-08 remains NOT GRANTED.
- D.5 records Stage D documentary completion and the remaining owner decision boundary.
- No code/schema/adapter/runner/workflow/permission/runtime/data changes; no tests, compile, dry-run, fault injection or Actions dispatch; no VPS/T0/T1/DB/provider/secret probes; no provisioning; no destructive operation. No workflow run or artifact is claimed.
- Option C remains ACTIVE. TEST-08 remains NOT GRANTED. AI execution remains disabled; no live orders.
- Next step: a separate owner decision is required before preparing any bounded implementation proposal. Stage D completion does not authorize implementation or execution.


## Latest completed work — Stage E.0–E.5 / Bounded Implementation Proposal

- Added documentation-only proposal: `docs/evidence/p1-8/STAGE_E0_E5_BOUNDED_IMPLEMENTATION_PROPOSAL_2026-11-10.md`.
- Report commit: `ac67d75aa4f45e4f03c9fe1c92d992deadcb2bcf`; report blob SHA and final content were verified by GitHub read-back.
- Owner approved automatic execution of Stage E only within the documentary E.0–E.5 scope.
- E.1 defines bounded future scope for TEST-01–07; E.2 records proposed dependency order; E.3 defines acceptance/evidence criteria; E.4 defines fail-closed risks and stop conditions; E.5 records owner disposition and next gate.
- Result: DOCUMENTARY PROPOSAL COMPLETE. Implementation readiness BLOCKED; execution NOT AUTHORIZED.
- TEST-01/02 implementation NOT ESTABLISHED; TEST-03 NOT VERIFIED; TEST-04/05/06/07 NOT ESTABLISHED; TEST-08 NOT GRANTED; LDA-07 87/87 NOT RUN; LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED.
- Option C remains ACTIVE. No cleanup/deletion/archive/expiry/compaction/vacuum authority. `AI_EXECUTION_ENABLED=false`; no live orders.
- No source/schema/adapter/runner/workflow/permission/runtime/data changes; no tests, compile, dry-run, fault injection or Actions dispatch; no secrets, VPS/T0/T1/DB/provider/recipient/backup/replica probes; no provisioning or destructive operation. No workflow run or artifact is claimed.
- Next gate: separate owner authorization for a bounded implementation proposal and, independently, exact-scope TEST-08 authorization before any lifecycle test execution. Stage E approval does not grant either.


## Latest completed work — Stage F.0–F.5 / Prerequisite Closure Review

- Added documentation-only review: `docs/evidence/p1-8/STAGE_F0_F5_PREREQUISITE_CLOSURE_REVIEW_2026-11-10.md`.
- Report commit: `b488d29421db8e33e113760b4f7b3242a51a76c3`; report blob SHA verified by GitHub read-back.
- Owner approved automatic execution of Stage F only within the documentary F.0–F.5 scope.
- F.1 consolidated prerequisite inventory and classified documentary closure separately from owner decisions and technical evidence.
- F.2 reviewed logical schema/canonicalization, synthetic resource/namespace and principal/capability prerequisites.
- F.3 reviewed evidence-destination identity, effective permissions, append-only/versioning, retention/hold, recovery and independent verifier requirements.
- F.4 reconciled the C.14 status: 87/87 source definitions and design mappings; 0/87 executable bindings; 0/87 executed; all 87 remain NOT RUN.
- F.5 defined a future dependency sequence and owner disposition. No technical gate was upgraded.
- Result: DOCUMENTARY PREREQUISITE REVIEW COMPLETE; overall implementation readiness BLOCKED; execution NOT AUTHORIZED.
- TEST-01/02 NOT ESTABLISHED; TEST-03 NOT VERIFIED; TEST-04/05/06/07 NOT ESTABLISHED; TEST-08 NOT GRANTED; LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED; LDA-07 87/87 NOT RUN.
- No code/schema/adapter/runner/workflow/permission/runtime/data changes; no tests, compile, dry-run, fault injection or Actions dispatch; no secrets/runtime/VPS/T0/T1/DB/provider/recipient/backup/replica probes; no provisioning or destructive operation. No workflow run or artifact is claimed.
- Option C remains ACTIVE; `AI_EXECUTION_ENABLED=false`; no live orders.
- Next gate: owner decision package for unresolved canonicalization/schema profile, synthetic resource/principal boundary and evidence destination/verifier. Any implementation, probes or lifecycle execution require separate scope and authorization; TEST-08 remains mandatory.


## Latest completed work — Stage G.0–G.5

- Completed documentary-only owner decision package: `docs/evidence/p1-8/STAGE_G0_G5_OWNER_DECISION_PACKAGE_2026-11-10.md`.
- Report creation commit: `fd4b57f4773edac585c68ecea319114deb9314ba`.
- Scope: G.1 proposes RFC 8785 JCS + SHA-256 with strict conformance; G.2 proposes layered per-run synthetic isolation; G.3 defines distinct least-privilege principals/capabilities; G.4 compares evidence destinations and recommends a provider-neutral hybrid model with independent exact-version verifier; G.5 records six pending owner decisions.
- All six G-DEC decisions remain PENDING; recommendations are not owner-approved technical baselines.
- Status: Stage G documentary package COMPLETE; technical readiness BLOCKED; implementation and execution NOT AUTHORIZED. TEST-08 NOT GRANTED; TEST-01/02/04/05/06/07 NOT ESTABLISHED; TEST-03 NOT VERIFIED; LDA-07 87/87 NOT RUN; LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED.
- Option C — No Destructive Authority remains ACTIVE; `AI_EXECUTION_ENABLED=false`; no live orders.
- No code/schema/adapter/runner/workflow/permission/runtime/data changes; no tests, compile, dry-run, fault injection, Actions dispatch, secrets/runtime/provider/VPS/database/recipient/backup/replica probes, provisioning or destructive operations. No workflow run or artifact is claimed.
- Next step: owner disposition of G-DEC-01 through G-DEC-06; only after explicit decisions may a versioned technical contract be prepared. Any implementation and lifecycle execution require separate authorization.


## Latest completed work — Stage H.0–H.5

- Completed documentary-only owner decision resolution: `docs/evidence/p1-8/STAGE_H0_H5_OWNER_DECISION_RESOLUTION_2026-11-10.md`.
- Report creation commit: `fe0dd096eb375d6c7b008392fa57562df787aa84`.
- G-DEC-01 APPROVED direction: RFC 8785 JCS + SHA-256; exact conformance profile, parser/number/Unicode rules and golden vectors remain OPEN.
- G-DEC-02 APPROVED target: layered per-run synthetic isolation; concrete topology, policies and effective isolation proof remain OPEN.
- G-DEC-03 APPROVED target: distinct least-privilege executor, adapter, observer/oracle, publisher and verifier principals; identity provider, credentials and effective capability proof remain OPEN.
- G-DEC-04 APPROVED direction: provider-neutral hybrid Git index + separately versioned evidence payload destination; no provider/account selected.
- G-DEC-05 APPROVED: independent exact-version byte/digest/schema/provenance/causal-closure verifier; implementation and trust roots remain OPEN.
- G-DEC-06 PARTIALLY RESOLVED: governance requirements for retention/hold/recovery approved; all durations, providers and operational mechanisms remain OPEN.
- Stage H documentary decision resolution COMPLETE; technical readiness BLOCKED; implementation and execution NOT AUTHORIZED. TEST-08 NOT GRANTED; TEST-01/02/04/05/06/07 NOT ESTABLISHED; TEST-03 NOT VERIFIED; LDA-07 87/87 NOT RUN; LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED.
- Option C — No Destructive Authority remains ACTIVE; `AI_EXECUTION_ENABLED=false`; no live orders.
- No source/code/schema/adapter/runner/workflow/permission/runtime/data changes; no tests, compile, dry-run, fault injection, Actions dispatch, secrets/runtime/provider/VPS/database/recipient/backup/replica probes, provisioning, external evidence publication or destructive operation. No workflow run or artifact is claimed.
- Next step: prepare a versioned documentary technical contract from the approved directions while retaining all OPEN parameters. Implementation requires separate explicit approval; lifecycle execution additionally requires TEST-08.


## Latest completed work — Stage I.0–I.5 / Versioned Technical Contract

- Added documentary draft baseline: `docs/evidence/p1-8/STAGE_I0_I5_VERSIONED_TECHNICAL_CONTRACT_2026-11-10.md`.
- Contract ID/version: `H5-LIFECYCLE-TECHNICAL-CONTRACT` / `1.0.0-draft`; not frozen, not implemented, not executable.
- Report creation commit: `3757f58b2c91296e51d1867c602f58d001705527`.
- I.1 specifies the JCS + SHA-256 direction, source-byte digest distinction, domain-separated identifiers, schema evolution and required conformance fixtures; exact profile/library and numeric/Unicode rules remain OPEN.
- I.2 defines run/namespace binding, resource classification and layered synthetic isolation; concrete technology and effective isolation proof remain OPEN.
- I.3 defines distinct principal roles, identity binding and capability requirements; provider/credential mechanism and effective permission proof remain OPEN.
- I.4 defines logical evidence envelope, verifier inputs/checks/results and provider-neutral destination boundary; exact field schema, trust roots and provider remain OPEN.
- I.5 defines retention/recovery decision fields and preserves 87-vector traceability: 87/87 design-mapped, 0/87 executable, 87/87 NOT RUN.
- C.13 exact canonical path could not be resolved by current GitHub lookup; field-level crosswalk is explicitly OPEN / NOT VERIFIED, not claimed complete.
- Stage I documentary draft COMPLETE; technical readiness BLOCKED; implementation and execution NOT AUTHORIZED. TEST-08 NOT GRANTED; TEST-01/02/04/05/06/07 NOT ESTABLISHED; TEST-03 NOT VERIFIED; LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED.
- Option C — No Destructive Authority remains ACTIVE; `AI_EXECUTION_ENABLED=false`; no live orders.
- No code/schema/adapter/runner/workflow/permission/runtime/data changes; no tests, compile, dry-run, fault injection, Actions dispatch, secrets/runtime/provider/VPS/database/recipient/backup/replica probes, provisioning, external evidence publication or destructive operation. No workflow run or artifact is claimed.
- Next step: documentary contract reconciliation/revision to resolve C.13 source crosswalk and adjudicate OPEN fields. Implementation requires separate explicit approval; lifecycle execution additionally requires TEST-08.


## Latest completed work — Stage J.0–J.6 / Contract Reconciliation and Freeze-Readiness Review

- Added documentary reconciliation: `docs/evidence/p1-8/STAGE_J0_J6_CONTRACT_RECONCILIATION_FREEZE_READINESS_REVIEW_2026-11-10.md`.
- Report commit: `a20cb631242b19118d30d9ba22abd78c5e8004de`.
- Resolved the exact C.13 canonical path: `docs/evidence/p1-8/STAGE_C13_INTEGRATED_SCHEMA_FIELD_AND_EVIDENCE_DESTINATION_MAP_2026-11-10.md`, blob `c43c8bfbccaf698d6670f33fab66ee12d2072a7f`; Stage I's earlier path lookup limitation is corrected.
- Reconciled C.13 common envelope, root manifest, source/vector, principal/process, operation/attempt/event, observation/oracle, provenance/artifact/publication, cleanup and destination entities against Stage I. Logical crosswalk DOCUMENTARY PASS; implementation fields remain OPEN.
- Confirmed Stage H decisions are consistent with Stage I/J; SHA-256/JCS direction is approved while exact conformance remains OPEN.
- Preserved C.14 denominator: 87/87 design-mapped, 0/87 executable, 87/87 NOT RUN; C.15 finding dispositions unchanged.
- Freeze readiness: NOT READY. J-OPEN-01–11 remain contract blockers; LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED. TEST-08 NOT GRANTED.
- Stage J documentary reconciliation COMPLETE; technical readiness BLOCKED; implementation and execution NOT AUTHORIZED.
- Option C — No Destructive Authority remains ACTIVE; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- No code/schema/adapter/runner/workflow/permission/runtime/data changes; no tests, compile, dry-run, fault injection, Actions dispatch, secrets/runtime/provider/VPS/database/recipient/backup/replica probes, provisioning, external evidence publication or destructive operation. No workflow run or artifact is claimed.
- Next step: Stage K — Owner Adjudication of Contract Freeze Blockers, documentary-only. Any implementation requires separate explicit approval; lifecycle execution additionally requires TEST-08.


## Latest completed work — Stage K.0–K.6 / Owner Adjudication Decision Package

- Added documentary decision package: `docs/evidence/p1-8/STAGE_K0_K6_OWNER_ADJUDICATION_DECISION_PACKAGE_2026-11-10.md`.
- Report commit: `d15740eecee8c2b39a4e254f1b3ea13ad9beac4a`.
- Classified J-OPEN-01–13 as owner policy, technical specification, combined, or external evidence requirements.
- Preserved Stage H approvals: JCS + SHA-256 direction; layered per-run isolation; distinct least-privilege principals; Git index + separate versioned evidence payload; independent exact-version verifier; retention governance.
- Recorded conservative proposals only; no owner-specific provider, library, identity service, retention duration, recovery objective or numeric threshold was selected by inference.
- J-OPEN-01–11 remain OPEN; J-OPEN-12 TEST-08 NOT GRANTED; J-OPEN-13 LDA-06 PARTIAL / NOT VERIFIED and LDA-08 HOLD / NOT VERIFIED.
- Contract freeze NOT READY; technical readiness BLOCKED; implementation and execution NOT AUTHORIZED.
- Option C — No Destructive Authority remains ACTIVE; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- No code/schema/adapter/runner/workflow/permission/runtime/data changes; no tests, compile, dry-run, fault injection, Actions dispatch, secrets/runtime/provider/VPS/database/recipient/backup/replica probes, provisioning, external evidence publication or destructive operation. No workflow run or artifact is claimed.
- Next recommended stage: Stage L — Contract Profile Specification Draft, documentary-only, retaining TBD markers and requiring explicit owner decisions before freeze.


## Latest completed work — Stage L.0–L.7 / Contract Profile Specification Draft

- Added companion documentary profile: `docs/evidence/p1-8/STAGE_L0_L7_CONTRACT_PROFILE_SPECIFICATION_DRAFT_2026-11-10.md`.
- Report commit: `ff4a1789b50f973adfd5c749cdc5a06e6c9cb080`.
- Base contract remains `H5-LIFECYCLE-TECHNICAL-CONTRACT` 1.0.0-draft; companion profile `1.1.0-profile-draft` is not frozen, executable or implemented.
- Consolidated candidate JCS/SHA-256 profile, common evidence envelope, digest reference, record families, operation/attempt and observation/verdict invariants, resource classifications, isolation/principal boundaries, evidence destination/verifier, time/causal ordering and retention/authority constraints.
- Explicit TBD markers retained for library/version, numeric/Unicode profile, digest/ID envelope, exact schema, clock/sequence semantics, retry/correction state machine, isolation topology, identity provider, evidence provider, verifier trust roots and retention/recovery values.
- C.14 denominator preserved: 87/87 design-mapped, 0/87 executable, 87/87 NOT RUN. No test or production status upgraded.
- Contract freeze NOT READY; TEST-08 NOT GRANTED; LDA-06 PARTIAL / NOT VERIFIED; LDA-08 HOLD / NOT VERIFIED.
- Option C — No Destructive Authority remains ACTIVE; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- No executable schema, code, adapter, runner, workflow, permission, credential, provider, runtime or data changes; no tests, compile, dry-run, fault injection, Actions dispatch, probes, provisioning or destructive operations. No workflow run or artifact is claimed.
- Next recommended stage: Stage M — Profile Consistency and Test-Traceability Review, documentary-only.


## Latest continuation — T0 L4-Extended branch separation (2026-11-10)

- Recorded scope and branch-separation plan in `docs/evidence/T0_L4_EXTENDED_BRANCH_SEPARATION_PROGRESS_2026-11-10.md`.
- T0 Core + L4-Minimum remain on `feature/t0-centralized-data-feeder-p1-20261101`; planned Extended branch is `feature/l4-extended-provenance`.
- Extended scope: RFC3161 TSA, OCSP/CRL, Multi-TSA/quorum, WORM/Object Lock, Root A/B. PostgreSQL/TimescaleDB, public HTTPS and DR remain separate/PARKED.
- Extended branch creation is intentionally BLOCKED until a frozen, accepted L4-Minimum commit exists. L4-Minimum remains BLOCKED / NOT VERIFIED; L4M-01–08 mandatory, L4M-09 owner-waived, L4M-10 owner self-assessment; all nine applicable controls must PASS on one frozen evidence baseline.
- Branch search found no existing `feature/l4-extended-provenance`; no branch was created and no code was moved/deleted.
- No tests or Actions dispatch; no runtime/VPS/DB/data/secrets/permissions/network changes. No workflow run/artifact claimed. Option C ACTIVE; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders.
- Next gate: close L4-Minimum acceptance on one frozen evidence baseline, then create Extended from that exact commit SHA.


## Latest continuation — L4-Minimum policy and historical audit reconciliation (2026-11-10)

- Added `docs/evidence/T0_L4_MINIMUM_POLICY_HISTORICAL_AUDIT_RECONCILIATION_2026-11-10.md` to reconcile current policy against historical read-only/adversarial/scope audits.
- Current matrix blob is `2ba85af550fb7e369ea39ade6d73878d78dbf6bc`; controlling owner waiver excludes L4M-09. Nine active controls are L4M-01–08 and L4M-10.
- Historical audits remain unchanged. Their prior independent-review blocker statements describe earlier policy; the outside-scope audit's contrary wording is superseded prospectively for L4-Minimum only. Other lifecycle/security/operational reviewer gates are not waived.
- L4M-01–08 and L4M-10 remain NOT VERIFIED / BLOCKED as applicable. Aggregate acceptance remains BLOCKED pending one frozen baseline with nine PASS controls and owner disposition.
- Extended branch creation remains blocked pending accepted/frozen L4-Minimum commit. No source/runtime/data/permission changes; no tests or Actions dispatch; Option C ACTIVE; paper-only; no live orders.


## Latest continuation — L4-Minimum nine-control evidence acquisition register (2026-11-10)

- Added `docs/evidence/T0_L4_MINIMUM_NINE_CONTROL_EVIDENCE_ACQUISITION_REGISTER_2026-11-10.md`.
- Register separates design/synthetic/CI evidence from owner-controlled and production evidence for active controls L4M-01–08 and L4M-10. L4M-09 remains owner-waived.
- Acquisition order prioritizes L4M-01 custody plus L4M-03 latest-head anchor, then L4M-02 signer separation, L4M-04/05 offline verification and readback, L4M-06/07 trust and tamper-evident history, L4M-08 claim review, and L4M-10 frozen baseline/owner disposition.
- L4M-01/02 remain NOT VERIFIED; L4M-03–07 remain PARTIAL synthetic/design only; L4M-08 documentary PASS only; L4M-10 NOT VERIFIED/PENDING owner assessment. Aggregate remains BLOCKED / NOT VERIFIED.
- No owner storage evidence was accessed or read back. No tests, Actions dispatch, runtime/VPS/DB/data/key/provider/permission changes or destructive operations. Option C ACTIVE; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders.
- Next gate: owner-supplied sanitized L4M-01 custody evidence and L4M-03 latest-head anchor, followed by L4M-02 signer-separation evidence.


## Latest continuation — L4M-01/L4M-03 owner evidence intake contract (2026-11-10)

- Added `docs/evidence/T0_L4M01_L4M03_OWNER_EVIDENCE_INTAKE_CONTRACT_2026-11-10.md` to make the next owner-supplied evidence handoff precise and redaction-safe.
- L4M-01 intake requires an existing owner-controlled copy outside T0/VPS and GitHub, package inventory/byte counts, per-file SHA-256 manifest, custody provenance and exact-package readback evidence. Availability claims are limited to actually observed failure scenarios.
- L4M-03 intake requires exact checkpoint byte/digest identity, schema/dataset/sequence semantics, existing signature metadata if available, and the separately authenticated latest-head anchor linked into the same L4M-01 custody inventory. Sequence/generation alone is insufficient; missing anchor means freshness UNKNOWN.
- No evidence received or verified; no owner storage access. No credentials/private keys/private URLs requested. No tests, outage simulation, signing, runtime/VPS/DB/provider/permission changes, Actions dispatch or destructive operations. Option C ACTIVE; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders.
- Next gate remains owner-supplied sanitized evidence for existing L4M-01 custody and L4M-03 anchor. L4M-01 NOT VERIFIED; L4M-03 PARTIAL synthetic/design only; aggregate L4-Minimum BLOCKED.


## Latest continuation — L4M-01/L4M-03 existing trust evidence non-substitution (2026-11-10)

- Added `docs/evidence/T0_L4M01_L4M03_EXISTING_TRUST_EVIDENCE_NON_SUBSTITUTION_2026-11-10.md` after checking the existing P1.8.14 Sigstore trust-anchor report, T0 checkpoint contract v1 and G3 review-input manifest against the active L4 evidence requirements.
- Determination: P1.8.14 remains a valid historical synthetic CI-artifact attestation result, but GitHub-hosted artifacts/runners do not establish owner custody outside the GitHub failure domain, owner readback during GitHub outage, offline verification, a signed T0 canonical checkpoint or an owner-controlled monotonic latest-head anchor.
- T0 checkpoint contract remains DRAFT/documentary; G3 manifest remains review-input-only with independent review not performed. Neither supplies production checkpoint/anchor evidence.
- L4M-01 remains NOT VERIFIED; L4M-03 remains PARTIAL synthetic/design only and freshness UNKNOWN / NOT VERIFIED. No controls promoted; aggregate remains BLOCKED.
- No tests, Actions dispatch, owner storage access, signing, runtime/VPS/DB/provider/key/permission/network changes or destructive operations. Option C ACTIVE; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders.
- Next gate remains owner-supplied sanitized evidence for an already-existing L4M-01 package and L4M-03 latest-head anchor. If absent, record NOT AVAILABLE; do not manufacture evidence.


## Latest continuation — L4M-02 signer-separation existing-evidence assessment (2026-11-10)

- Added `docs/evidence/T0_L4M02_SIGNER_SEPARATION_EXISTING_EVIDENCE_ASSESSMENT_2026-11-10.md` after read-only inspection of the synthetic Ed25519 verifier/tests, Sigstore trust-root documentation, P1.8.14 and the active evidence register.
- Finding: synthetic verifier is explicitly verifier-only; tests create ephemeral keys; P1.8.14 authenticates a GitHub workflow's synthetic archive. None establishes an owner-authorized T0 signer, private-key custody/recovery boundary, or that T0 runtime/admin credentials cannot invoke/authorize signing.
- L4M-02 remains NOT VERIFIED. No production signer is inferred absent beyond the reviewed source/document scope. No key operations, signing, permission probes, tests, provider calls, Actions dispatch, runtime/VPS/DB/network changes or owner-system access.
- Next admissible input: sanitized owner references for an already-existing signer role/fingerprint, custody/recovery boundary, authorization policy and T0 credential separation. If none exists, record NOT AVAILABLE; any new signer design or operation needs separate approval.
- L4M-01 remains NOT VERIFIED; L4M-03 remains PARTIAL synthetic/design only; aggregate L4-Minimum BLOCKED. Option C ACTIVE; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders.


## Latest continuation — L4M-08 claim discipline assessment (2026-11-10)

- Added `docs/evidence/T0_L4M08_CLAIM_DISCIPLINE_DOCUMENTARY_ASSESSMENT_2026-11-10.md`.
- Assessment commit: `936b04a567695b512a837b05b644e7c7e429299e`; report blob SHA: `702f7ee2d26edeeb5f9e59081da6d9339088fb74`.
- Reviewed exact matrix blob `2ba85af550fb7e369ea39ade6d73878d78dbf6bc`, evidence register blob `4ec993d23a7b6d282350d0dea0add0254cac87cb`, policy reconciliation blob `531b9b4b42337439697ac27286486ced8d19df25`, and L4M-02 assessment blob `ea32f996cf5053fc8f320b9dc325bd242da1c034`.
- Bounded documentary review found no overclaim in those four exact documents: signature validity, timestamp, Sigstore/CI, synthetic tests, ACK/consumption, tamper-evident history and independent-assurance claims remain explicitly scoped.
- L4M-08 remains DOCUMENTARY PASS ONLY; complete owner-controlled package claim inventory is absent and exact frozen-package revalidation remains required. Aggregate L4-Minimum remains BLOCKED / NOT VERIFIED.
- No tests, verifier execution, Actions dispatch, owner storage readback, signing/key/provider/runtime/VPS/DB/data/permission/network changes or destructive lifecycle action. No workflow run/artifact claimed.
- Option C ACTIVE; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Next gate: L4M-10 readiness assessment, but do not freeze a baseline or issue owner acceptance while L4M-01–07 evidence remains incomplete. Owner evidence remains the critical dependency.


## Latest work — T0 → T2 GitHub evidence collection (2026-11-10)

- Added `docs/evidence/T0_T2_GITHUB_EVIDENCE_COLLECTION_2026-11-10.md`.
- Commit: `33c33d46a8d77a7f18d74639145b5abf3d8b4f4d`; verified report blob: `adb218ce054ed721e11aa0c5a13e31993740949b`.
- Retrieved GitHub evidence for historical T0 Feeder runtime, T0 API → T2 loopback runtime, repository source parity, four historical Actions runs, job conclusions and artifact metadata.
- Historical bounded T0→T2 gate dated 2026-11-09 remains PASS; T0 Feeder runtime report remains PARTIAL PASS. These are historical operator-provided observations, not current runtime evidence.
- Inspected 13 runtime-relevant source blobs remain identical in the previously reviewed comparison. Branch exists; current deployed VPS SHA, process-loaded bytes, current listener/service state and current environment remain NOT VERIFIED.
- GitHub Actions job records retrieved for runs `42508364088`, `42508364089`, `42508364090`, `42508364114`; listed jobs report completed/success. Historical artifacts were found with expiry `2026-11-15T18:07:17Z`; no new workflow was dispatched.
- Current G1 PARTIAL / NOT VERIFIED; G2/G3/G5 HISTORICAL PASS but current NOT VERIFIED; G4 PARTIAL / NOT VERIFIED; G6 NOT RUN.
- No SSH/VPS/DB/network probe, test, compile, Actions dispatch, runtime/service/data/secret/permission change or destructive action. No current VPS evidence was generated.
- Next gate: collect owner-supplied sanitized current T0/T2 source SHA, service identity/launch, bind/endpoint, redacted config/token-presence, status/log and alternate data-path evidence. A new G6 read requires separate explicit approval.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders. T0 canonical SQLite protected; PostgreSQL/TimescaleDB PARKED; T1 not activated.


## Supplemental CI artifact byte inspection (2026-11-10)

- Downloaded and inspected four existing GitHub Actions artifacts; no workflow was dispatched and no tests were run in this step.
- Updated evidence report `docs/evidence/T0_T2_GITHUB_EVIDENCE_COLLECTION_2026-11-10.md`; update commit `c3a16dbb571da8296c82a2203fa42411e8f73892`; verified report blob `ac6fedfc3b0e7c315ec23e5e4f23d19de3beb929`.
- Artifact ZIP SHA-256:
  - `13627939321`: `d91536d963cd58738b9c892a62d01cd0d346f3288abc2a700574b527c76bad66`
  - `13628397213`: `7b5b4ac30fc6387bbddae6b284a94e528769c61356d98a2f3aff7346cf4db027`
  - `13628521899`: `1a0f61f396c6fb4c7f57382d9b635cd958c97008e541de28178a9e31827d4a98`
  - `13627924430`: `7a14b9cf72c1396ca194b21f081d6c88f08e8769e937b18bdc82374fdef684d0`
- Inspected log evidence: T0 full suite 298 tests; gateway behavior 77; health/readiness 21; gateway contract 10; process restart 2; T2 HTTP consumer regression 31. T2 strategy load reports `ChartProFreqaiResearch` OK under Freqtrade 2026.9.
- T0 systemd feeder/API integration log reports PASS; T0 SQLite read-only WAL sandbox reports PASS. The latter explicitly scopes itself to `DISPOSABLE_GITHUB_RUNNER_ONLY`; it is not VPS evidence.
- CI evidence is stronger at artifact-byte level, but current deployed SHA/listener/config/process and data-path remain NOT VERIFIED. G1 PARTIAL; G2/G3/G5 historical only; G4 PARTIAL; G6 NOT RUN.
- No SSH/VPS/DB/network probe, new tests, compile, workflow dispatch, source/runtime/data mutation or destructive action.
- Next step remains owner-supplied sanitized current VPS evidence. If unavailable, do not upgrade any current deployment gate to PASS.


## Latest continuation — expose Scaleway SSH preflight dispatch from main (2026-11-10)

- Copied the already-reviewed `.github/workflows/t0-manual-validation.yml` from `feature/t0-centralized-data-feeder-p1-20261101` to `main`; this was the only file changed on `main`.
- Main commit: `9cb38cdd995158704fe2993e277396bb9bf4b50a`; workflow blob after GitHub readback: `395ae93274a9202f14ab63d528be5cd582c30149`.
- Diff is limited to adding the `scaleway-ssh-preflight` manual gate, excluding that gate from the existing generic job, and adding the two SSH contract/preflight jobs. Existing manual gates were retained.
- Main readback confirms the gate option and both jobs. The matching remote script and contract test are present on the feature branch, not on main; therefore dispatch must select `feature/t0-centralized-data-feeder-p1-20261101` in the GitHub branch selector so the workflow checks out the matching source tree. Do not select `main` for the SSH run.
- No workflow was dispatched, no SSH connection was attempted, and no artifact/run exists from this change. Secrets/environment configuration and VPS forced-command installation remain NOT VERIFIED.
- Status: workflow exposure on main PASS (GitHub commit/readback); SSH preflight execution NOT RUN. No T0 runtime, database, data, trading or VPS mutation.
- Next step: manually run `T0 Manual Validation` from Actions with branch `feature/t0-centralized-data-feeder-p1-20261101` and gate `scaleway-ssh-preflight`; inspect run and artifact before changing deployment status.


## Latest continuation — sanitized Scaleway SSH preflight diagnostics (2026-11-10)

- Owner approved a narrowly scoped diagnostic workflow change after SSH preflight run `42773990222` exited 255 with an empty remote output log and no surfaced SSH client stderr.
- Only workflow source changed: `.github/workflows/t0-manual-validation.yml`; no remote command, SSH security option, secret, VPS, runtime, database or data changes.
- Workflow commit sequence on `feature/t0-centralized-data-feeder-p1-20261101`:
  - `0c8f0a9105d05b903c0a45fb670a7f7714466cc6` — add sanitized diagnostic classification and artifact files.
  - `69a795af30deda9a8403836eb3fe74d98dd6d7c5` — correct contract assertion to inspect the artifact upload path.
  - `a20be6d68a065351b42d7a6f7fe526b308f72cb4` — normalize newline encoding in generated diagnostic files.
- Final workflow blob SHA: `a0c466e4e2a25d034593cdc262c3cabb8f998b28`.
- Final diagnostic artifact additions: `preflight-ssh-diagnostic.txt` (classification labels + exit code only) and `preflight-ssh-exit-code.txt`. Raw `$RUNNER_TEMP/ssh-client-stderr.log` is not uploaded.
- Static GitHub readback confirms pinned host-key checks, `IdentitiesOnly=yes`, key-only authentication, no agent/port forwarding, no TTY, 60-second timeout and the existing forced-command SSH target remain unchanged.
- Compare against pre-change source `897faa0f058d4c98506d79d263927a4a11a56060`: branch ahead 3, behind 0; compare reports only `.github/workflows/t0-manual-validation.yml` changed (57 additions, 5 deletions).
- Review status: STRUCTURAL REVIEW PASS; test execution NOT VERIFIED; workflow dispatch NOT RUN. The inline contract check has not yet been executed by GitHub Actions. No claim is made about current VPS state or SSH connectivity.
- Overall diagnostic change status: PARTIAL / NOT VERIFIED pending a manual `scaleway-ssh-preflight` run on this feature branch and inspection of the resulting artifact.
- Next step: owner manually dispatches `T0 Manual Validation` with branch `feature/t0-centralized-data-feeder-p1-20261101` and gate `scaleway-ssh-preflight`; then inspect the contract job, SSH job and sanitized artifact. Do not rerun against `main` and do not broaden the remote command.


## Latest continuation — Scaleway SSH preflight authentication diagnosis (2026-11-10)

- Owner supplied workflow run `42792435714` for the approved `scaleway-ssh-preflight` gate.
- Workflow run: completed / FAILURE; event `workflow_dispatch`; branch `feature/t0-centralized-data-feeder-p1-20261101`; exact checkout/source SHA `ff1f1768cab1b899494910df1b9ba0d98d35835f`.
- Job `P1 SSH preflight contract checks`: PASS. Job `P1 authenticated Scaleway read-only preflight`: FAILURE. The isolated acceptance job was SKIPPED.
- SSH client exit code: `255`. Sanitized diagnostic artifact classifies `SSH_STDERR_CLASS=AUTHENTICATION_REJECTED`; raw SSH stderr was intentionally not uploaded. This narrows the failure to SSH authentication rejection but does not identify whether the private/public key pair, SSH username, or key provisioning/authorization is the cause.
- Artifact: `p1-scaleway-ssh-preflight-42792435714`; artifact ID `13752555729`; size 863 bytes; SHA-256 `7c8e1ed37861d9df1bc7f0b7fe32cbf2cbbdf48fe01fe1f167a70fa647c0d902`; expires `2026-11-17T09:38:40Z`. Contents inspected: source SHA, empty remote log, verdict `P1_SSH_PREFLIGHT=PARTIAL_OR_BLOCKED_EVIDENCE`, authentication-rejected classification and exit code 255.
- Forced-command output was not received. No VPS state, service, listener, SQLite integrity, feeder PID, API or deployed source SHA was verified. No remote write, restart, database/data mutation or destructive operation occurred.
- Status: workflow contract PASS; SSH preflight BLOCKED by authentication rejection; VPS runtime state NOT VERIFIED.
- Next step: compare the fingerprint of the public key corresponding to the exact private key stored in `SCW_SSH_PRIVATE_KEY` with the restricted key entry in the intended account's `authorized_keys`, and confirm the configured SSH username. Do not disclose or upload private key material or passphrases. Keep strict host-key checking and forced-command restrictions unchanged. Any secret/key/authorized_keys change requires separate explicit approval.
- No workflow rerun is authorized by this record. No arbitrary SSH shell or remote command is authorized. `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.



## Latest continuation — vận hành ưu tiên SQLite, PostgreSQL tùy chọn được tạm dừng (2026-11-10)

- Owner quyết định PostgreSQL chỉ là backend tùy chọn; không cần tiếp tục phát triển ở giai đoạn hiện tại.
- PostgreSQL/TimescaleDB được đặt trạng thái PARKED: giữ nguyên adapter, mã nguồn và kiểm thử hiện có; không mở rộng tính năng/lifecycle acceptance, không migration Canonical T0 và không bật PostgreSQL làm backend vận hành.
- Canonical T0 tiếp tục dùng SQLite. Bảo toàn dữ liệu và tính độc lập của T0; ưu tiên kiểm định single-writer, lease/fencing, recovery, backup/restore và độ ổn định feeder/API theo phạm vi đã được phê duyệt.
- Thứ tự ưu tiên tiếp theo: (1) SQLite T0; (2) T1 collector và luồng nhập dữ liệu; (3) T0–T1–T2 integration; (4) Strategy Core RSI + ADX + Smart DCA và AI Strategy LONG/SHORT độc lập; (5) Shared Risk Engine/Kill Switch; (6) paper-only reliability và independent out-of-sample.
- GitHub Actions tiếp tục là nơi chạy kiểm định; GitHub lưu source, handoff và evidence. VPS chỉ là mục tiêu vận hành T0; trạng thái runtime hiện tại vẫn NOT VERIFIED. Android là kênh giám sát, không phải máy vận hành chính.
- Quyết định này chỉ thay đổi ưu tiên công việc, không thay đổi source/runtime/database. Không chạy workflow, không SSH/VPS, không migration, không restart Feeder, không thay đổi cấu hình/secret và không giao dịch thật.
- Evidence: handoff được cập nhật trên branch hiện có `feature/t0-centralized-data-feeder-p1-20261101`; baseline source commit gần nhất đã xác minh trước cập nhật là `0c8498ac530cdcbb750b0864881e018572a31fe6`; handoff blob trước cập nhật là `d20b4279012ccc2b3ea409bafd8743330d9b1440`.
- Status: DECISION RECORDED; code/test execution NOT RUN; SQLite VPS runtime NOT VERIFIED; PostgreSQL PARKED.
- Next step: tiếp tục rà soát SQLite T0 theo evidence đã có, xác định đúng gate còn thiếu trước khi dispatch bất kỳ workflow nào. Không thực hiện SSH preflight hoặc thay đổi runtime nếu chưa có phê duyệt riêng.


## 2026-11-10 — T0 SSH preflight workflow parity (selective port)

- Scope: port only the encrypted-key SSH preflight workflow hardening from the previously successful branch; preserve the T0 branch and its existing manual validation gates.
- Target branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Latest source commit: `ffc7caa7b62dbc0000e55c2f91659f5d681c6b4c`.
- Updated files:
  - `.github/workflows/t0-manual-validation.yml` blob `ee2eb9db57bf3a8da188eab6c68d9639e062b11e`.
  - `ci/test_t0_ssh_preflight_contract.py` blob `74e4d28315860049bb7b25cf84f34a12027ac334`.
  - `ops/ssh/t0-readonly-preflight.sh` unchanged; blob remains `39de5aa7602cdf7dc301ff6bc65a68fad417ea84`.
- Changes: support encrypted SSH private key using a short-lived ssh-agent (300s), verify pinned key fingerprint, scope secrets to the steps that need them, clean up temporary secret files/agent, add PR contract-only execution, and add manual gate `scaleway-ssh-contract-only` that does not invoke the authenticated SSH job.
- Preserved prior successful evidence: run [42791255299](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42791255299), source SHA `7e635a6462c29456f1adb2e7ddcd01443909a5ac`; artifact [13750314557](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42791255299/artifacts/13750314557), SHA-256 `26b0564a006d19150a9ab8cda5ec1bcf40a3e77ad6a7483bc7798e9bf540e17c`. The prior artifact reported SSH exit 0, key unlock/fingerprint PASS, SQLite integrity PASS, API 8788 loopback-only, and remote source SHA `9ae2eeae4ece3d657781b68e96b6f4509cd95f24`.
- Validation: source-level review confirms the SSH job runs only for `workflow_dispatch` gate `scaleway-ssh-preflight`; PR and `scaleway-ssh-contract-only` execute the contract job only. Automated GitHub Actions contract-only run has **NOT RUN** yet; test result is therefore **NOT VERIFIED**.
- Status: **PARTIAL** — selective source port committed; CI execution pending. Do not infer PASS from the previous branch's successful run.
- Explicit limits: no VPS connection, no SSH preflight rerun, no runtime/service/Feeder changes, no canonical SQLite access or migration, no PostgreSQL work, no live trading.
- Next step: run GitHub Actions workflow `T0 Manual Validation` on this branch with gate `scaleway-ssh-contract-only`; inspect exact checked-out SHA, job conclusion and artifact. Only after that evidence passes should any further workflow promotion be considered.


## 2026-11-10 — T0 SSH preflight contract-only CI verification

- Owner supplied workflow run [42813723910](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42813723910).
- Workflow job `P1 SSH preflight contract checks` (job ID `129821369757`): **SUCCESS**. The log confirms checkout of exact source commit `3cadf2e5b483a5fb3beb93b5a3f94db33c880fdb`.
- Executed checks: `bash -n ops/ssh/t0-readonly-preflight.sh` PASS; `python -m unittest ci.test_t0_ssh_preflight_contract -v` PASS, 5/5 tests; inline workflow diagnostic/artifact contract assertions PASS.
- `T0 manual isolated acceptance` (job ID `129821372078`) and `P1 authenticated Scaleway read-only preflight` (job ID `129821445560`) were both **SKIPPED**, as required for the contract-only gate. No artifacts were produced.
- Status: T0 SSH preflight workflow contract and focused tests **PASS** at source SHA `3cadf2e5b483a5fb3beb93b5a3f94db33c880fdb`. Authenticated SSH/VPS preflight and T0 runtime acceptance remain **NOT RUN / NOT VERIFIED** in this run.
- No VPS/SSH connection, runtime/service/Feeder operation, canonical SQLite access/migration, PostgreSQL work, T1 activation, trading, or data mutation occurred.
- Next step: do not promote runtime status based on contract CI. Any authenticated Scaleway read-only preflight requires a separate explicit owner approval and must use the dedicated `scaleway-ssh-preflight` gate; keep the remote command strictly read-only.


## 2026-11-10 — Approved Scaleway SSH read-only preflight PASS

- Owner explicitly approved running the dedicated `scaleway-ssh-preflight` gate. Workflow run [42814402445](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42814402445) completed with conclusion **SUCCESS**.
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`; exact workflow checkout/source SHA: `8ad36cae8aa971a537a6f363902f86046aa32e5e`; event `workflow_dispatch`; run attempt 1.
- Jobs:
  - `P1 SSH preflight contract checks`, job ID `129823665846`: **SUCCESS**. `bash -n ops/ssh/t0-readonly-preflight.sh` PASS; focused unittest suite PASS, 5/5; inline sanitized diagnostic/artifact contract assertions PASS.
  - `P1 authenticated Scaleway read-only preflight`, job ID `129823736309`: **SUCCESS**.
  - `T0 manual isolated acceptance`, job ID `129823667801`: **SKIPPED** by design for this gate.
- Authenticated SSH diagnostic: encrypted private key unlock PASS; pinned SSH key fingerprint PASS; SSH stderr class `STDERR_EMPTY`; SSH exit code `0`.
- Inspected remote read-only output from artifact:
  - `P1_SSH_PREFLIGHT_VERSION=1` and end marker present.
  - VPS hostname: `btcquant-t0-t1-test-01`; SSH user: `ubuntu`.
  - VPS deployed/source SHA reported by remote: `9ae2eeae4ece3d657781b68e96b6f4509cd95f24`.
  - Feeder PIDs observed: `22045,22046`.
  - API 8788 endpoint: `127.0.0.1:8788`; status `LOOPBACK_ONLY`.
  - Canonical SQLite integrity: `PASS`.
  - Workflow verdict: `P1_SSH_PREFLIGHT=PASS_READ_ONLY_PREFLIGHT`.
- Artifact: `p1-scaleway-ssh-preflight-42814402445`; artifact ID `13762564163`; size 1,066 bytes; SHA-256 `f6303919c69b05d412722492f05b8dd3aefa1a655043fa98029a94fee5ee8c28`; expires `2026-11-17T12:16:53Z`. All five files were downloaded and inspected: `ci-source-sha.txt`, `preflight-remote.log`, `preflight-verdict.txt`, `preflight-ssh-diagnostic.txt`, `preflight-ssh-exit-code.txt`.
- Status: **PASS — authenticated SSH read-only preflight snapshot** at run time. SSH connectivity/authentication, pinned key, host identity verification (strict host-key checking), remote forced-command protocol, observed Feeder PIDs, API loopback binding, and SQLite integrity were verified at this snapshot.
- Scope/limits: this is a point-in-time read-only snapshot, not continuous monitoring or proof of current runtime after the run. The isolated T0 acceptance job was skipped; no full recovery/lease/fencing or data-delivery acceptance is claimed. No restart, configuration change, service mutation, DB write, migration, data deletion, PostgreSQL work, T1 activation, or trade occurred.
- Next step: preserve this evidence and continue with the next separately scoped SQLite T0 validation. Do not infer broader runtime acceptance from this preflight; any operation beyond read-only inspection requires separate approval.

## 2026-11-10 — Approved isolated SQLite lease/fencing CI gate added

- Owner explicitly approved a narrowly scoped workflow change to begin SQLite T0 validation with lease/fencing.
- Existing branch retained: `feature/t0-centralized-data-feeder-p1-20261101`.
- Workflow commit: `a3ec0d7a9e826eb95ea2f434dee9b5b27b3ca16c`.
- Updated file: `.github/workflows/t0-manual-validation.yml`; prior blob `ee2eb9db57bf3a8da188eab6c68d9639e062b11e`; new blob `c1161d75587affb0994692022223a3c091e40f67`.
- Added manual gate `sqlite-lease-fencing`, running only in GitHub Actions against the runner's disposable temporary SQLite databases through:
  - `market_data.test_feeder_lease`
  - `market_data.test_write_gateway`
  - `market_data.test_feeder_lifecycle`
- The gate writes a focused test log and `SQLITE_LEASE_FENCING=PASS` verdict artifact only after the unittest command succeeds. Workflow readback verified the gate option, conditional execution, exact test command and artifact paths.
- No production source, test logic, runtime configuration, VPS, canonical SQLite database, service, secret, T1/T2 integration or trading behavior was changed.
- Validation status: **WORKFLOW STRUCTURE PASS** by GitHub readback. **TEST EXECUTION NOT RUN**; no Actions run or artifact exists yet. This is not a G1 PASS.
- G1 acceptance remains pending the owner-dispatched `sqlite-lease-fencing` workflow run, exact checkout SHA, successful test result and artifact inspection.
- G2 recovery and G3 data-flow gates have not been added; they remain deferred until G1 evidence is reviewed. No workflow dispatch was performed in this change.
- Next step: manually dispatch `T0 Manual Validation` on this same branch with gate `sqlite-lease-fencing`; inspect job conclusion, test count/log and artifact before deciding whether to proceed to recovery.


## G4 runtime acceptance design correction — endpoint separation (2026-11-10)

- Follow-up source inspection found an endpoint-separation issue that must be resolved before implementing or dispatching G4.
- `market_data/api.py` is the canonical candle WSGI service (historically port 8788). Its `GET /health` is only a generic service response `{"ok": true, "service": "canonical-market-data"}`; it does not expose `/health/live`, `/health/ready`, or `/health/data`. Its authenticated `GET /v1/candles` requires `MARKET_DATA_TOKEN` and a bounded query.
- Detailed feeder health endpoints `/health/live`, `/health/ready`, `/health/data`, and the aggregate `/health` are implemented in Flask `app.py`, a separate application. Current repository evidence does not establish that this Flask app is running on the VPS or identify its bound port. Do not assume port 8788 serves these endpoints.
- G4 must therefore discover/verify service binding before issuing endpoint-specific requests. The canonical candle API and detailed feeder-health API are separate acceptance subjects. Missing/unidentified detailed-health listener must be reported as `NOT_VERIFIED`, not silently mapped to port 8788.
- Read-only SQLite inspection must use a URI with `mode=ro`, set `PRAGMA query_only=ON`, and issue SELECT/PRAGMA integrity checks only. Do not call lease mutation helpers or create schema. The lease row must be interpreted using the existing owner/generation/expiry contract; missing or expired lease is a failed runtime gate.
- The prior proposed G4 endpoint mapping to `127.0.0.1:8788/health/data` is withdrawn. No script, workflow, VPS, SSH forced-command, `authorized_keys`, process, or canonical DB was changed by this correction.
- Next repository-only step: add a test-first G4 contract that verifies endpoint separation, read-only SQLite access, allowlisted invocation, fail-closed missing configuration, and sanitized evidence. Run on GitHub Actions before any VPS installation. VPS installation remains gated on an explicit, compatible deployment path and must not widen SSH access.
- Current status: endpoint/source inspection **PASS**; G4 implementation **NOT STARTED**; VPS G4 runtime **NOT VERIFIED**; T1 remains NOT ACTIVATED; PostgreSQL remains PARKED; `AI_EXECUTION_ENABLED=false`; paper-only.


## G4a — isolated read-only SQLite probe contract added (2026-11-10)

- Scope is repository/CI only. This stage defines and tests a sanitized SQLite snapshot primitive; it is **not** the live VPS G4 acceptance and does not install or invoke anything on the VPS.
- Test-first contract file: `ci/test_t0_runtime_acceptance.py`. It creates only disposable temporary SQLite fixtures and covers integrity, canonical lease state, owner fingerprint redaction, expired/missing lease fail-closed behavior, missing DB non-creation, unchanged DB bytes, endpoint separation and M15/H1 watermark calculations.
- Probe: `ci/t0_runtime_acceptance.py`. It requires an existing database, opens SQLite URI `mode=ro`, enforces `PRAGMA query_only=ON`, checks `integrity_check`, reads the canonical `binance-btcusdt-canonical` lease and M15/H1 candle watermarks, and returns only a truncated owner fingerprint (never the raw owner). It does not create schema or call acquire/heartbeat/release/write helpers.
- Endpoint separation test preserves the source distinction: candle WSGI app on the historical 8788 service exposes generic `/health` and authenticated `/v1/candles`; detailed `/health/data` belongs to the separate Flask feeder-health app. The probe does not assume that Flask listener exists on the VPS.
- Workflow adds path-scoped G4 contract detection and an isolated GitHub-hosted job. The job requires G1, G2 and G3 jobs to succeed in the same run, has `contents: read`, `persist-credentials: false`, empty DB/token/exchange credential environment, no SSH secrets, no VPS access, and uploads source SHA, test log and verdict. It is explicitly labeled `DISPOSABLE_FIXTURE_ONLY`.
- Files/blob SHAs at the latest G4 workflow commit:
  - `.github/workflows/t0-manual-validation.yml`: `a4c37d91daa4a6555270bd5cbabe8c9c081641f4`.
  - `ci/t0_runtime_acceptance.py`: `82629f083d40c8b5f90a3e72c86ab5d46bedb4e1`.
  - `ci/test_t0_runtime_acceptance.py`: `f82fd24dc21118bf8a1930a8235ccfa54da6458c`.
  - `ci/test_t0_ssh_preflight_contract.py`: `7eabbe273487b72aa0025df04756c5c9a6a3344a`.
- Workflow source commit `c3e4283361d4702c867540a109d0b2a0f068cb8b` triggered run [42822851406](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42822851406). At handoff update time the run was pending; test execution, job conclusions and artifacts are **NOT VERIFIED**. An earlier run [42822774540](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42822774540) was triggered before the final dependency-install correction and is not accepted as final evidence.
- Current status: G4a implementation committed; G4a CI **PENDING / NOT VERIFIED**. This does not establish runtime freshness, real lease state, actual VPS API authentication, watermark progression over time, or process stability. G4 VPS execution remains **NOT AUTHORIZED / NOT VERIFIED** until a safe deployment path is established and separately approved.
- No VPS/SSH/forced-command/authorized_keys changes, canonical SQLite access, process restart, T1 activation, PostgreSQL work, data deletion, or trading action occurred. T1 NOT ACTIVATED; PostgreSQL PARKED; `AI_EXECUTION_ENABLED=false`; paper-only.
- Next step: inspect run `42822851406` jobs and artifact. If G4a CI passes, continue with separate HTTP/API contract probes and a deployment-path review; do not label the VPS runtime PASS.


## G4a CI evidence — isolated read-only SQLite probe contracts PASS (2026-11-10)

- Final automated run [42822851406](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42822851406): event `push`, branch `feature/t0-centralized-data-feeder-p1-20261101`, exact checkout/source SHA `c3e4283361d4702c867540a109d0b2a0f068cb8b`, overall conclusion **SUCCESS**.
- Job results:
  - G1 lease/fencing job `129852909252`: **17/17 workflow/isolation contract tests PASS** and **55/55 lease/fencing/write-gateway/lifecycle tests PASS**.
  - G2 recovery job `129853080651`: **64/64 recovery/scheduler/lifecycle tests PASS**.
  - G3 data-flow job `129853274221`: **87/87 tests PASS** (17 workflow contracts + 2 E2E + 10 sync + 13 API + 45 T2 HTTP consumer).
  - G4a read-only runtime probe contract job `129853501017`: **25/25 tests PASS** (17 workflow/isolation contracts + 8 disposable-SQLite/API-separation probe tests); verdict `G4_READ_ONLY_SQLITE_CONTRACT=PASS`.
  - G4 scope detection and all prerequisite scope jobs: SUCCESS. SSH preflight and manual VPS acceptance jobs: SKIPPED, as required for this isolated run.
- Artifacts from the same source SHA:
  - G1 artifact ID `13766943924`, SHA-256 `88c7f56fc6b692945da1416297ed852a4112b6465871853da6f4cfe65675cc38`.
  - G2 artifact ID `13766978835`, SHA-256 `9928ea5dfbc522b2252111b44536a803fc6be08e9e583eadada24e66d99f5488`.
  - G3 artifact ID `13766769313`, SHA-256 `77aeb28e288d64a11408c9a991565ff51c1702ed5a3d3c7536c495c71c5988d0`.
  - G4a artifact ID `13767153847`, SHA-256 `832a74be2687aed4f753e02727cfb6a3054f72af737026f622b950e3c95d5c26`; [artifact](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42822851406/artifacts/13767153847).
  - All four artifacts expire `2026-11-17T13:15:23Z`.
- Disposition: G1/G2/G3 isolated CI gates revalidated PASS on source SHA `c3e428...`; G4a read-only SQLite probe/API-separation contracts PASS. This proves only disposable GitHub-runner behavior. It does **not** prove current VPS lease, SQLite state, candle freshness, authenticated API response, watermark progression, or process stability. VPS G4 runtime remains **NOT VERIFIED**.
- No SSH/VPS connection, forced-command or `authorized_keys` change, probe installation, canonical DB read/write, service restart, T1 activation, PostgreSQL work, data deletion, or trading action occurred. T1 NOT ACTIVATED; PostgreSQL PARKED; `AI_EXECUTION_ENABLED=false`; paper-only.
- Next step: define and test separate bounded HTTP probes for the canonical candle API and the explicitly configured detailed feeder-health API; missing Flask listener configuration must remain NOT VERIFIED. Then review a deployment mechanism that preserves forced-command allowlisting. No VPS installation or runtime invocation without separate explicit approval.
