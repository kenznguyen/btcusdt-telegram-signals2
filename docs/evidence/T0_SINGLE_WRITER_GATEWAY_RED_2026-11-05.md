# T0 Single Writer Gateway — RED Contract Evidence

Date: 2026-11-05 (UTC)

## Scope

Added a source-only contract suite and a GitHub Actions workflow to establish the RED acceptance baseline for PR #134. This increment does not implement the Gateway.

- Branch: `feature/t0-atomic-write-fencing-20261105`
- PR: https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/134
- Branch source SHA tested by the PR workflow: `0ded4b14018118ef491b8bc191d1a04ac1601d21`
- PR merge-ref checkout SHA observed in runner log: `64b3859495921ffc43c581307587f58b3e7f17aa`
- Test module: `market_data/test_single_writer_gateway_red.py`
- Workflow: `.github/workflows/t0-single-writer-gateway-red.yml`

## GitHub Actions evidence

- Run ID: `41975055718`
- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41975055718
- Event: `pull_request`
- Workflow conclusion: `success`; this means the expected-RED classifier passed, not that the Gateway is accepted.
- Job: `Static source-only RED contract classification` — success.
- Python compile: PASS.
- Shadow-only environment preflight: PASS.
- Contract tests: 10 executed; 9 expected assertion failures; 1 pass; 0 errors.
- Passing contract: SWG-D01 read-only consumer connection.
- Confirmed gaps: SWG-A01, SWG-A02, SWG-A03, SWG-A04, SWG-B01, SWG-C01, SWG-E01, SWG-E02, SWG-E03.

Artifact:
- ID: `13391580712`
- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41975055718/artifacts/13391580712
- Size: 16,887 bytes
- GitHub digest: `sha256:4727b57f1fa2a82173878977fbfedaac6dbeedf1d1591d8dbbdd51a5279b0aee`
- Artifact payload checksum has not been independently recomputed; metadata digest only.

## Verification boundary

The first PR-event run used branch head SHA `0ded4b14018118ef491b8bc191d1a04ac1601d21` as run metadata but checked out merge ref `64b3859495921ffc43c581307587f58b3e7f17aa`. It is not a standalone branch-head checkout.

A subsequent push-event run verified the exact branch head:
- Run ID: `41975313806`
- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41975313806
- Event: `push`
- Exact source SHA and runner checkout SHA: `b9855a7b992b76870e024718447e3ca822755b6f`
- Conclusion: `success`
- Job ID: `127072668062`; all steps completed successfully.
- Tests: 10 executed; 9 expected assertion failures; 1 pass; no test errors.
- Artifact ID: `13391173036`
- Artifact URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41975313806/artifacts/13391173036
- Size: 16,888 bytes
- GitHub digest: `sha256:8abe044b53c2e1c2e53923e9f5f2f12c7b8b27e6462b6be0f9dcbabac1e1bd4a`

The exact-head run is a successful expected-RED classification, not a GREEN acceptance. Artifact payload checksum has not been independently recomputed.

No canonical database was opened or created. No Feeder was started. No exchange credentials or network calls were used. No migrations or market-data sync ran. No strategy or execution behavior changed.

## Status

- RED contract harness: PASS (expected-RED classification on exact branch head).
- Gateway implementation: BLOCKED / NOT IMPLEMENTED.
- Exact-head isolated workflow execution: PASS (push event on `b9855a7b...`).
- Canonical write safety: NOT CERTIFIED.
- PR #134: OPEN / DRAFT / NOT MERGED.
- Handoff: NOT UPDATED on this branch because `docs/PROJECT_SESSION_HANDOFF.md` is absent from the PR branch; do not copy or rewrite the main handoff into this implementation PR without resolving the branch/documentation ownership decision.

## Next step

Inventory every write call site and implement a single Gateway API that owns atomic batch writes and lease fencing. Route scheduler, recovery, and any permitted Shadow-only CLI through explicit writer capabilities. Remove or fail-close legacy direct write methods only after all callers and regression tests are mapped. PostgreSQL canonical writes remain disabled until an equivalent same-transaction fencing implementation is independently tested.
