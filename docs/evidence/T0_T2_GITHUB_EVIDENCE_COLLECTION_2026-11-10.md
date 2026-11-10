# T0 → T2 GitHub Evidence Collection — 2026-11-10

## Scope and method

GitHub-only, read-only evidence acquisition for deployment-parity gates G1–G5. Retrieved repository files, commit metadata, branch existence, workflow job records and artifact metadata. No SSH/VPS/DB/network probe, workflow dispatch, test, compile, service operation or data mutation was performed.

Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

## Evidence collected

### E1 — Repository and source identity

- The target branch exists in GitHub.
- Previously recorded verified branch HEAD: `1083258fe5443469602a10a33a082b0d7178290a`; commit is retrievable and its message is `docs(handoff): correct source parity file count`.
- A fresh GitHub compare from historical runtime source `9ae2eeae4ece3d657781b68e96b6f4509cd95f24` to the branch reports branch status `ahead`, `ahead_by=832`, `behind_by=0`.
- The connector's branch search returns branch identity but not its current ref SHA. Therefore this collection does not independently assert a fresh exact branch-tip SHA.
- Current VPS checkout SHA remains unknown.

### E2 — Runtime source parity

Report: `docs/evidence/T0_T2_REPOSITORY_SOURCE_PARITY_REVIEW_2026-11-10.md`
- Exact report blob: `4f9b35406236bdab1e5c76ef21f719298cdeb1c4`.
- Thirteen inspected runtime-relevant blobs are identical between historical T0 source SHA `9ae2eeae4ece3d657781b68e96b6f4509cd95f24` and the compared GitHub branch snapshot.
- The only selected-path difference is `market_data/README.md`, a documentation-only loopback topology clarification.
- Repository source parity for the inspected file set: PASS.
- Current VPS checkout and process-loaded byte parity: NOT VERIFIED.

### E3 — Historical T0 Feeder runtime

Report: `docs/evidence/T0_FEEDER_RUNTIME_VERIFICATION_20261109.md`
- Exact report blob: `ef632a53490e85d709026651c0af9a22d28883fb`.
- Source SHA reported on VPS: `9ae2eeae4ece3d657781b68e96b6f4509cd95f24`.
- Reported Feeder PID 22046, tmux session `t0-feeder`; post-restart M15/H1 ingestion and lease heartbeat observations.
- Bounded coverage: M15 3/3 and H1 3/3, planner gaps 0.
- Scheduler completed-window state and full recovery-history coverage: NOT VERIFIED.
- Overall report disposition: PARTIAL PASS; evidence is historical operator-provided VPS output, not a new probe.

### E4 — Historical T0 API → T2 loopback runtime

Report: `docs/evidence/t2/T0_T2_LOOPBACK_RUNTIME_VERIFICATION_2026-11-09.md`
- Exact report blob: `568b7d2c5ba6f606221519aba7ee4b298dff34c8`.
- T0 API reported bound to `127.0.0.1:8788`; health 200; missing Bearer token 401; authenticated M15/H1 reads 200.
- Both timeframes returned 2/2 complete closed VALIDATED candles, no gaps.
- M15 ingestion lag 8,558 ms against configured maximum 120,000 ms.
- One-shot T2 context read for 2 M15 bars exited 0; JSON parse PASS.
- The context artifact remained local at `/tmp/t2-canonical-window-20261109T112946Z.json`; it is not a GitHub Actions artifact.
- Process-loaded byte identity was not independently attested.
- This is a bounded historical PASS dated 2026-11-09, not current runtime evidence.

### E5 — GitHub Actions runs and artifacts

The following historical workflow runs were queried directly for jobs and artifacts. All listed jobs returned `completed/success`.

| Workflow run | Verified job | Artifact ID |
|---|---|---:|
| `42508364088` | Static Gateway contract verification; other parallel offline/fixture jobs also completed successfully | `13627939321` gateway contracts; `13628178055` provider bootstrap; `13628691436` Timescale read-only; `13628521899` T0 Feeder/API integration; `13627924430` SQLite read-only sandbox; `13627942657` T1 importer; `13628476107` T1 Rust sidecar; `13628681318` paper consumer |
| `42508364089` | Pinned Freqtrade 2026.9 FreqAI strategy load | `13628397213` |
| `42508364090` | Disposable Feeder API dependency and lifecycle | `13628521899` |
| `42508364114` | Disposable SQLite WAL under systemd ReadOnlyPaths | `13627924430` |

Artifact metadata was returned as not expired at retrieval time, with expiry `2026-11-15T18:07:17Z`. These are historical CI artifacts for source SHA `9ae2eeae4ece3d657781b68e96b6f4509cd95f24`; they do not establish current VPS state. Run IDs and artifact IDs are historical; no new workflow was dispatched.

### E6 — Deployment parity checklist and reconciliation

- Checklist: `docs/evidence/T0_T2_DEPLOYMENT_PARITY_EVIDENCE_CHECKLIST_2026-11-10.md`.
- Reconciliation: `docs/evidence/T0_T2_DEPLOYMENT_PARITY_EVIDENCE_RECONCILIATION_2026-11-10.md`, blob `25aa2cae62fb7a693bc31d80a359fe304555e7ad`.
- The reconciliation explicitly classifies G1–G6 evidence from 2026-11-09 as historical; current source checkout, service/listener, environment/token and current response/freshness remain unverified.

## Gate disposition

| Gate | Evidence available | Current verdict |
|---|---|---|
| G1 — exact deployed source SHA | Historical T0 SHA and current repository source comparison; no current VPS SHA | PARTIAL / NOT VERIFIED |
| G2 — T0 listener and T2 endpoint | Historical loopback listener and endpoint evidence dated 2026-11-09 only | HISTORICAL PASS / CURRENT NOT VERIFIED |
| G3 — token/config/freshness setting | Historical authenticated reads and 120,000 ms setting; no current env evidence | HISTORICAL PASS / CURRENT NOT VERIFIED |
| G4 — canonical SQLite ownership/no fallback | Static inspected T2 migration path and historical read-only service configuration; no current storage enforcement attestation | PARTIAL / NOT VERIFIED |
| G5 — API/data contract and freshness | Historical bounded M15/H1 responses and T2 context read | HISTORICAL PASS / CURRENT NOT VERIFIED |
| G6 — new bounded runtime observation | No new probe authorized or performed | NOT RUN |

## Next evidence required

Owner-supplied sanitized current VPS evidence is still needed for:
1. T0 and T2 checkout branch + exact SHA.
2. T0 API service identity, launch entrypoint and loopback bind.
3. T2 service/container identity and launch entrypoint.
4. Redacted config names/values, token presence only, and T0 SQLite path/backend.
5. Timestamped service status and redacted startup/health logs.
6. Confirmation of any additional T2 SQLite, exchange, cache or alternate-source readers.

Do not disclose secret values. If current evidence is unavailable, retain NOT VERIFIED. A new G6 read-only probe requires separate explicit approval.

## Safety boundary

No code, test, dependency, workflow, permission, secret, runtime, VPS, database, service, network or data changes were made. No cleanup/deletion, PostgreSQL activation, T1 activation, strategy execution, ledger/risk mutation or live order was performed. `AI_EXECUTION_ENABLED=false`; paper-only.


## Artifact byte-level inspection addendum (2026-11-10)

Four GitHub Actions ZIP artifacts were downloaded and inspected locally. The SHA-256 values below identify the exact downloaded ZIP bytes in this inspection session; they are not signatures or independent custody proofs.

| Artifact ID | Downloaded file | SHA-256 | Inspected contents / scope |
|---|---|---|---|
| `13627939321` | `artifact-13627939321.zip` | `d91536d963cd58738b9c892a62d01cd0d346f3288abc2a700574b527c76bad66` | Gateway contract/behavior, health readiness, process restart, and T0 market-data full-suite logs |
| `13628397213` | `artifact-13628397213.zip` | `7b5b4ac30fc6387bbddae6b284a94e528769c61356d98a2f3aff7346cf4db027` | Freqtrade strategy-load and T2 HTTP consumer regression logs |
| `13628521899` | `artifact-13628521899.zip` | `1a0f61f396c6fb4c7f57382d9b635cd958c97008e541de28178a9e31827d4a98` | T0 systemd feeder/API integration logs, events, unit/journal records and scope metadata |
| `13627924430` | `artifact-13627924430.zip` | `7a14b9cf72c1396ca194b21f081d6c88f08e8769e937b18bdc82374fdef684d0` | T0 SQLite read-only WAL/systemd sandbox tests and scope metadata |

### Observed test and integration evidence

- T0 market-data full suite: 298 tests, log reports successful completion.
- Gateway behavior: 77 tests PASS.
- Health/readiness: 21 tests PASS.
- Gateway contract: 10 tests PASS.
- Process restart: 2 tests PASS.
- T2 HTTP consumer regression: 31 tests PASS.
- T2 strategy load: `ChartProFreqaiResearch` reported `OK` under Freqtrade 2026.9; environment log reports Python 3.14.7 and CCXT 4.5.84.
- T0 systemd integration log records feeder readiness generations 1 and 2, API read-only mutation denial, authenticated candle read, restart read, SIGTERM/SIGKILL propagation and orderly reverse shutdown; final verdict `T0_SYSTEMD_FEEDER_API_INTEGRATION=PASS`.
- T0 systemd WAL sandbox explicitly labels target `DISPOSABLE_GITHUB_RUNNER_ONLY`; verdict `T0_SYSTEMD_READONLY_WAL_SANDBOX=PASS`. It records read-only WAL reads PASS, filesystem/SQLite writes DENIED, and cold start without sidecars BLOCKED_AS_EXPECTED.
- T0 systemd artifacts include source SHA `9ae2eeae4ece3d657781b68e96b6f4509cd95f24`.

### Interpretation limits

These are CI/disposable-runner tests and logs, not VPS captures. The `DISPOSABLE_GITHUB_RUNNER_ONLY` label is explicit. They do not prove that the current VPS uses systemd units/configuration represented in these artifacts, that the current API is listening, that current environment variables are correct, or that current process-loaded bytes match the repository. Test counts are per artifact log and may cover overlapping suites; do not sum them into a unique-test total.

### Updated gate interpretation

- Repository/CI evidence depth: strengthened; inspected artifact bytes and recorded local ZIP SHA-256.
- G1 deployed SHA: still PARTIAL / NOT VERIFIED.
- G2/G3/G5: historical runtime evidence only; current VPS state NOT VERIFIED.
- G4: T2 static migration tests and runner integration strengthen code-level evidence, but current deployed data-path enforcement remains NOT VERIFIED.
- G6: NOT RUN.
- No new test or workflow was run; existing artifact logs were inspected only.
