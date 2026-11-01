# Implementation Plan: Browser Automation Controller v1

## Overview

Introduce a per-build Browser Automation Controller for the Five-Layer System. The controller exists only inside a Codemagic build, routes API-capable work through official provider APIs first, and uses an isolated Playwright worker only for authorized UI-only operations. GitHub remains source/PR storage; Codemagic runs tests, builds, and automation. No always-on service is created.

The approved contract and request schema are:
- `docs/architecture/BROWSER_AUTOMATION_CONTROLLER_V1.md`
- `schemas/browser-automation-task-v1.schema.json`

## Architecture decisions

- **Lifecycle:** instantiate and terminate the controller within one Codemagic build.
- **No daemon/server:** no persistent web service, queue service, browser profile, or cross-build session.
- **API-first:** official GitHub and Codemagic APIs are preferred; Playwright is a UI fallback.
- **One authorization boundary:** all automation tasks validate and authorize before dispatch.
- **Fail closed:** unknown provider state, permission mismatch, invalid schema, missing credentials, or failed verification never reports success.
- **Idempotency:** retries reuse the same intent key and reconcile provider state before repeating side effects.
- **Evidence:** redacted manifests and digests are exported as Codemagic artifacts.
- **Safety:** no CAPTCHA/MFA bypass, live trading, unapproved merge, deploy, delete, publish, or permission escalation.
- **Project separation:** no changes to Five-Layer trading logic, Shared Risk Manager, paper execution boundary, or BTC Chart Pro.

## Task list

### Phase 1 — Contract and schema (documentation only)
- [x] Task 1: Approve and document the internal v1 contract.
- [x] Task 2: Add the JSON Schema for normalized v1 task requests.
- [x] Task 3: Record the implementation plan and ordered task checklist.
- [ ] Checkpoint: inspect the documentation/schema diff and confirm no runtime files changed.

### Phase 2 — Controller core
- [ ] Task 4: Add schema loading and strict request validation.
- [ ] Task 5: Add authorization policy, provider/action allowlists, and fail-closed behavior.
- [ ] Task 6: Add task lifecycle/status model and idempotency handling.
- [ ] Checkpoint: unit tests cover invalid payloads, forbidden permissions, duplicate intents, timeout, and unknown outcomes.

### Phase 3 — API adapters and verification
- [ ] Task 7: Define provider adapter protocol and retain/reuse the existing Codemagic API adapter.
- [ ] Task 8: Add GitHub API adapter operations required by approved tasks.
- [ ] Task 9: Verify build source SHA and artifact SHA-256 against the requested values.
- [ ] Checkpoint: API adapter tests use fakes; no real provider write is performed by unit tests.

### Phase 4 — Playwright UI fallback
- [ ] Task 10: Add an isolated per-build Playwright worker.
- [ ] Task 11: Enforce origin/path/workspace allowlists and permitted UI actions.
- [ ] Task 12: Implement safe user-interaction pause semantics for authentication and confirmation.
- [ ] Checkpoint: tests prove forbidden navigation, secret extraction, CAPTCHA/MFA bypass, and unauthorized writes are rejected.

### Phase 5 — Audit and evidence
- [ ] Task 13: Add redacted structured audit records.
- [ ] Task 14: Export screenshots/manifests only when authorized and calculate evidence SHA-256.
- [ ] Checkpoint: scan logs/artifacts for secret leakage and verify evidence provenance.

### Phase 6 — Codemagic integration
- [ ] Task 15: Add an explicit Codemagic workflow entry point for one-build controller execution.
- [ ] Task 16: Map credentials only from secure environment groups and verify workflow source SHA.
- [ ] Checkpoint: Codemagic build/test results are tied to the exact branch commit; do not add GitHub Actions.

### Phase 7 — Incremental migration
- [ ] Task 17: Migrate one approved browser-only task at a time through the controller.
- [ ] Task 18: Verify API-first routing and confirm migrated tasks no longer invoke TinyFish.
- [ ] Checkpoint: review each migration before moving the next task.

## Verification strategy

- All tests and builds execute on Codemagic, not GitHub Actions.
- Start with focused unit tests for each vertical slice, then run the relevant repository suites.
- Verify the Codemagic build's source commit SHA against the branch/PR head SHA.
- For build/artifact verification, compare exact provider-reported identifiers and SHA-256 values.
- Keep test providers mocked unless a separately authorized integration test explicitly requires a non-production account.
- Never use production credentials or data for tests.

## Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| A timeout hides a completed provider-side write | Duplicate or inconsistent actions | Mark outcome UNKNOWN and reconcile provider state before retry |
| Playwright reaches an unintended origin | Credential/session exposure | Strict origin/path allowlists and redirect validation |
| Secrets leak through logs or screenshots | Account compromise | Redaction, minimal evidence, secure environment groups |
| UI changes cause false success | Incorrect task completion | Verify provider state/postconditions, not only UI text |
| Controller becomes a persistent service | Operational/security scope expansion | Enforce per-build lifecycle; no server or external queue |
| Scope spills into trading or app behavior | Risk to existing system | Keep Five-Layer runtime, strategy, paper execution, and BTC Chart Pro out of scope |

## Open questions

- Exact Codemagic workflow trigger/input contract will be finalized after inspecting current `codemagic.yaml` conventions during Phase 6.
- Exact provider API scopes will be selected per task and documented before enabling any write operation.
