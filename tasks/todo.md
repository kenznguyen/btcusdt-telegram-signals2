# Browser Automation Controller v1 — Task Checklist

## Phase 1 — Contract and schema
- [x] Contract v1 documented in `docs/architecture/BROWSER_AUTOMATION_CONTROLLER_V1.md`.
- [x] Request JSON Schema added at `schemas/browser-automation-task-v1.schema.json`.
- [x] Implementation phases and acceptance criteria recorded in `tasks/plan.md`.
- [x] Review documentation/schema-only diff; confirm no runtime code or workflow changed.

## Phase 2 — Controller core

**Implemented slice:** `integrations/browser_automation/` provides strict v1 schema validation, trusted authorization context, allowlist enforcement, and a no-side-effect `prepare_task` boundary. No execution adapters or server are started. Codemagic test execution is still pending verification.
- [x] Add strict schema validation and normalized request model.
- [x] Add authorization policy and allowlist enforcement.
- [ ] Add task lifecycle/status model and idempotency/reconciliation behavior.
- [x] Author tests for accepted/rejected requests, permission escalation, URL/path allowlists, and fail-closed preparation.
- [ ] Run and verify the controller tests on Codemagic; confirm the build source SHA.

## Phase 3 — Provider APIs and verification
- [ ] Add adapter protocol and preserve the existing Codemagic API adapter.
- [ ] Add only the required GitHub API operations.
- [ ] Verify build commit SHA and artifact SHA-256.
- [ ] Add adapter tests with mocked provider responses.

## Phase 4 — Playwright fallback
- [ ] Add isolated per-build browser worker.
- [ ] Enforce origin, path, action, and workspace allowlists.
- [ ] Add WAITING_FOR_USER handling; never bypass CAPTCHA/MFA.
- [ ] Add tests for prohibited navigation and actions.

## Phase 5 — Audit and evidence
- [ ] Add redacted audit events.
- [ ] Export approved evidence and SHA-256 manifest.
- [ ] Verify no credentials or sensitive browser state enter logs/artifacts.

## Phase 6 — Codemagic integration
- [ ] Add explicit one-build controller workflow.
- [ ] Read secrets only from Codemagic secure environment groups.
- [ ] Run tests/build in Codemagic and verify exact source SHA.

## Phase 7 — Migration
- [ ] Migrate browser-only operations incrementally.
- [ ] Confirm migrated execution no longer depends on TinyFish.
- [ ] Review each migration before continuing.

## Global safety gates
- [ ] No always-on server, daemon, persistent browser profile, or cross-build session.
- [ ] API-first; Playwright only when an API cannot perform the operation.
- [ ] No live trading, auto-trading, production deployment, unapproved merge, delete, or release publication.
- [ ] No GitHub Actions; Codemagic is the execution environment.
- [ ] Five-Layer System and BTC Chart Pro remain independent.
