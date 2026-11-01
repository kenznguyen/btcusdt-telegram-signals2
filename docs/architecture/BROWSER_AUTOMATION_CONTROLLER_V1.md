# Browser Automation Controller — Internal Contract v1

**Status:** Approved baseline  
**Contract version:** 1.0  
**Execution host:** Codemagic build  
**Deployment model:** Ephemeral, per-build controller; no always-on server

## 1. Purpose and boundaries

The Browser Automation Controller (BAC) is the single orchestration boundary for user-authorized browser and provider automation tasks in the Five-Layer System. It is created for one Codemagic build, executes the accepted task, records verifiable evidence, and exits with that build. It is not a daemon, hosted service, queue server, or persistent browser session.

GitHub stores source, branches, pull requests, and documentation. Codemagic runs all builds, tests, and operational automation. No GitHub Actions workflow is introduced by this contract.

The controller does not change the Five-Layer trading architecture, strategy behavior, Shared Risk Manager, paper execution boundary, or BTC Chart Pro. No live exchange orders, auto-trading, production deployment, release publication, PR merge, destructive operation, or permission escalation is allowed by default.

## 2. Architecture

1. **Task intake:** accept a versioned task request from an approved Codemagic workflow/input.
2. **Validation:** validate schema, identifiers, target, timeout, and requested permissions.
3. **Authorization:** enforce provider/resource/action allowlists and least privilege. Reject any unapproved write, upload, delete, merge, deploy, publish, or financial action.
4. **Route selection:** use an official provider API adapter whenever it supports the requested operation; use Playwright only for UI-only operations.
5. **Execution:** run the selected adapter/worker inside the current Codemagic build workspace.
6. **Verification:** inspect provider state and compare it with the requested target/expected commit or artifact digest.
7. **Evidence:** emit a redacted result manifest and approved evidence files as Codemagic artifacts.
8. **Exit:** terminate the controller and browser context when the build ends. Do not persist browser profiles or session cookies between builds.

All automation entry points must go through the controller. Application layers must not call Playwright directly.

## 3. Task request

The canonical request is JSON and must validate against `schemas/browser-automation-task-v1.schema.json`.

Example:

```json
{
  "contract_version": "1.0",
  "idempotency_key": "stable-intent-id",
  "task_type": "CODEMAGIC_BUILD_VERIFY",
  "execution_mode": "API_FIRST",
  "target": {
    "provider": "codemagic",
    "resource": "build",
    "repository": "kenznguyen/btcusdt-telegram-signals2",
    "branch": "feature/android-five-layer-control",
    "expected_commit_sha": "9ba7074edde48f50e70c2dfaabb1bc06e3a0196e"
  },
  "permissions": {
    "read": true,
    "write": false,
    "upload": false,
    "delete": false
  },
  "timeout_seconds": 600
}
```

Rules:

- `task_id` is generated internally by the controller after task acceptance; it is not part of an external task request and is rejected if supplied by a caller.
- `idempotency_key` represents one stable user intent. A retry with the same key must not create a second non-idempotent action.
- `expected_commit_sha` is required for build verification and must be checked against the provider-reported build source SHA.
- Credentials, API tokens, passwords, cookies, and private keys must never appear in the request. Resolve secrets only from Codemagic secure environment groups at runtime.
- Requests are rejected if their provider, resource, task type, URL, file path, or permissions are outside configured allowlists.
- The v1 JSON Schema is Draft 2020-12, rejects unknown fields at every object boundary, and validates browser target URLs as HTTPS. Schema or validator loading failures fail closed.
- An omitted permission is not implicitly granted.

## 4. Task result

The canonical result is JSON:

```json
{
  "contract_version": "1.0",
  "task_id": "task-id",
  "status": "SUCCEEDED",
  "provider": "codemagic",
  "execution_mode": "API",
  "started_at": "2026-11-01T00:00:00Z",
  "finished_at": "2026-11-01T00:01:00Z",
  "result": {
    "build_id": "provider-build-id",
    "commit_sha": "verified-commit-sha"
  },
  "evidence": [],
  "error": null
}
```

A task may be reported as `SUCCEEDED` only after provider state and all required postconditions are verified. A command returning exit code zero is not sufficient proof on its own. A timeout does not prove that the provider-side operation did not happen; the controller must reconcile state before retrying.

### Status values

- `QUEUED`: accepted, not yet executing.
- `RUNNING`: execution started.
- `WAITING_FOR_USER`: user action is required, such as completing an allowed interactive authentication step.
- `SUCCEEDED`: provider state and required postconditions verified.
- `FAILED`: operation failed and the failure is known.
- `CANCELLED`: cancellation confirmed.
- `UNKNOWN`: outcome cannot yet be established; reconcile before retrying.

## 5. Internal Python interface

The initial implementation must expose a small internal interface equivalent to:

```python
class BrowserAutomationController:
    def validate_task(self, request): ...
    def authorize_task(self, request): ...
    def execute_task(self, request): ...
    def get_task_status(self, task_id): ...
    def cancel_task(self, task_id): ...
    def verify_result(self, request, result): ...
    def export_evidence(self, task_id): ...
```

The interface is internal to a Codemagic build. It is not a network API and must not create a long-running web server.

## 6. Execution adapters

### API adapters — preferred

Use official provider APIs for GitHub branch/commit/PR operations and Codemagic build start/status/artifact operations. Keep the existing Codemagic API adapter where it already meets the contract; do not replace API calls with browser clicks.

### Playwright worker — UI fallback only

Allowed capabilities, subject to task authorization:

- Navigate only to configured provider origins and URL paths.
- Read visible text, page state, and permitted attributes.
- Click, type, and select controls for explicitly authorized tasks.
- Upload/download only within the approved build workspace and task file allowlist.
- Capture screenshots and record URL, timestamp, and SHA-256 for evidence.
- Verify the resulting UI/provider state after each consequential action.

The worker must not:

- Visit arbitrary URLs or follow untrusted redirects outside the allowlist.
- Extract, print, persist, or export cookies, passwords, access tokens, or browser storage.
- Bypass CAPTCHA, MFA, access controls, or user confirmation.
- Perform unapproved merge, deployment, deletion, release publication, permission changes, or financial/exchange actions.
- Reuse a browser profile or authenticated session across Codemagic builds.

If interactive authentication requires the user, pause as `WAITING_FOR_USER` or stop safely. The worker must not attempt to defeat the authentication flow.

## 7. Security and audit

- Store provider credentials only in Codemagic secure environment groups with least-privilege scopes.
- Never embed secrets in GitHub source, YAML literals, logs, screenshots, artifacts, Android APKs, or task payloads.
- Enforce provider, origin, path, action, and workspace allowlists.
- Use isolated ephemeral browser contexts and build workspaces.
- Redact secrets and sensitive page content from logs/evidence.
- Record task ID, idempotency key (or a safe digest), actor/source, provider, action, target, expected and observed commit SHA, timestamps, status, and evidence digests.
- Keep evidence minimal and retain it according to Codemagic artifact policy.
- Fail closed on invalid schema, missing credentials, unknown provider state, permission mismatch, or verification mismatch.

## 8. Initial migration map

| Operation | Preferred mechanism |
| --- | --- |
| GitHub branch, commit, PR, source files | GitHub API |
| Codemagic build start/status/artifact metadata | Codemagic API |
| Artifact download and SHA-256 verification | Codemagic artifact/API + local build worker |
| Provider login, UI-only forms, upload/download UI | Playwright worker |
| UI screenshots and post-action visual checks | Playwright worker |

The controller is an orchestration boundary, not a reason to move existing API-backed tasks into a browser.

## 9. Delivery phases

1. Contract and schema documentation (this change only).
2. Controller core: request parsing, schema validation, authorization, status model, and idempotency.
3. API adapters and provider-state verification.
4. Playwright worker with strict allowlists and user-interaction pause semantics.
5. Audit/evidence export and SHA-256 verification.
6. Codemagic workflow integration and Codemagic-only validation.
7. Migrate individual browser tasks in small, reviewable increments.

No runtime implementation is included in phase 1.

## 10. Acceptance criteria

- Controller lifecycle is bounded to one Codemagic build; no always-on server is added.
- API-first routing is enforced; Playwright is only a UI fallback.
- Every task validates against the versioned schema and passes authorization.
- Retries honor idempotency; timeout/unknown outcomes are reconciled before retry.
- Build verification compares the exact provider-reported commit SHA with the requested SHA.
- Evidence is redacted, digestible, and stored as build artifacts.
- Secrets never appear in source, requests, logs, screenshots, or artifacts.
- CAPTCHA/MFA/access-control bypass is prohibited.
- No trading execution, production deployment, merge, or release publication is enabled by this contract.
- Tests and builds run on Codemagic; GitHub remains source/PR storage.
- Five-Layer System and BTC Chart Pro remain separate.

## 11. Change control

Contract-breaking changes require a new contract version and explicit review. Runtime implementation must conform to this document and schema; implementation must not silently weaken permissions, verification, idempotency, or security rules.
