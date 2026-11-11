# T0 Signature A2.2 Stage I — GitHub Actions Workflow Inspection

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Inspection source HEAD: `7c47352403c1aa9d7b9447b9e995f34a3f89400e`

## 1. Scope and authorization

This record documents read-only inspection of the existing GitHub Actions workflow inventory and candidate execution patterns after the owner approved inspection to determine a safe Stage I TDD path.

Governing Stage I approval:
- `docs/decisions/OWNER_APPROVAL_T0_SIGNATURE_A2_2_STAGE_I_2026-11-11.md`
- Blob: `04c6deb7b04c6cef10a8e696c9bd63af69264c2a`
- Governing A2.2 contract blob: `41d41cd23f73a6e552b9ceca5ebbb39c46934e7d`

No workflow was dispatched or rerun. No workflow, source, test, secret, permission, branch-protection, runtime or T0 file was changed as part of the inspection. CI execution remains NOT AUTHORIZED by the Stage I approval record; this inspection approval did not authorize execution.

## 2. Exact source and inventory

- Active branch HEAD at inspection: `7c47352403c1aa9d7b9447b9e995f34a3f89400e`.
- Handoff read from this branch: `docs/PROJECT_SESSION_HANDOFF.md`, blob `e6d5eb2301ecfadd11a9d8e793a1ff63c3830789`.
- Recursive Git tree read from tree `887ff44aa2ebfbb3e97dd9e758bbbd5bd9cd674f`; response reported `truncated=false`.
- The tree contains 15 workflow files under `.github/workflows/`; no Stage I-specific workflow or isolated Stage I package/test directory exists at this source HEAD.
- The existing `synthetic_evidence/` directory is the P1.8 implementation and is explicitly not an acceptable location for the separate Stage I package/tests.

## 3. Candidate workflow assessment

### 3.1 P1.8 synthetic evidence workflow — NOT SUITABLE

File: `.github/workflows/p1-8-synthetic-evidence.yml`  
Blob: `bbe9361cbbeed4f881edc4ce4fbe727d6937ad78`

Reasons:
- It grants `id-token: write` and `attestations: write`, beyond Stage I's needs.
- It obtains the Sigstore trusted root, performs remote GitHub CLI operations, creates and verifies attestations, and builds retention evidence.
- Its path filters target `synthetic_evidence/**` and P1.8 documentation, not a separate A2.2 Stage I package.
- Reusing it would couple the small synthetic contract harness to P1.8 trust/attestation operations and violate least-privilege isolation.

### 3.2 T0 Evidence Contract G2 workflow — SUITABLE AS A PATTERN, NOT A DIRECT RUNNER

File: `.github/workflows/t0-evidence-contract-g2.yml`  
Blob: `5e22648c38fd3c6e631f912010de1489bb78f9b5`

Positive characteristics:
- `permissions: contents: read` only.
- Python-only compile and deterministic unittest commands.
- Explicitly blank market-data, database and exchange credential variables.
- Exact-source SHA recording and test-log artifact upload.
- No attestation, deployment, VPS or provider operation.

Limitations:
- Its current path filters and commands target two files inside `synthetic_evidence/`; it does not discover or run the new Stage I package.
- It currently does not set `persist-credentials: false` on checkout; a new Stage I workflow should do so.
- Its existing test command is not evidence that Stage I has been implemented or tested.

### 3.3 T2 HTTP consumer workflow — NOT A PREFERRED TEMPLATE

File: `.github/workflows/t2-http-consumer-red.yml`  
Blob: `7690780e076c317345879dcef081951e78cf2c6a`

It installs runtime dependencies from package indexes and covers a different subsystem. Stage I should avoid inheriting unrelated dependencies or test scope.

## 4. Recommended safe execution path

A dedicated Stage I workflow is preferable to modifying P1.8 or broadening another domain workflow.

Proposed properties for a future workflow (not yet authored):
1. Dedicated filename, e.g. `.github/workflows/t0-signature-a2-2-stage-i.yml`.
2. Trigger only on the existing active branch and changes to the separately named Stage I package/tests plus the workflow itself; optionally a narrowly scoped manual dispatch only if separately approved.
3. `permissions: contents: read`; no OIDC, attestations, deployment, secrets or write permissions.
4. Checkout the exact triggering SHA with `persist-credentials: false`.
5. Pinned Python version; no third-party installation unless a dependency is explicitly selected and pinned in the approved Stage I implementation.
6. Clear all database/exchange credentials and set `AI_EXECUTION_ENABLED=false`.
7. Compile only the Stage I package/tests, run only its deterministic tests, enforce the expected test denominator, and upload source SHA, command, test log and compact verdict.
8. Ensure test execution is offline and uses temporary/in-memory fixtures only. The workflow must not call the existing P1.8 trust-root/attestation/retention steps.
9. Report workflow job conclusions and artifact metadata separately; a green run means only Stage I synthetic contract conformance.

The Stage I package path and exact test command must be established before the workflow diff is finalized. The approval record calls for a package/test directory separate from `synthetic_evidence`; it does not prescribe the directory name.

## 5. Disposition

- Existing workflow inventory inspection: **PASS**.
- Reuse of P1.8 synthetic evidence workflow: **REJECTED**.
- G2 workflow as a least-privilege template: **CONDITIONAL PASS**.
- Direct execution path using an existing workflow without changing its scope: **NOT AVAILABLE**.
- Dedicated Stage I workflow required if GitHub Actions is to execute the new package: **RECOMMENDED**.
- Workflow authoring: **NOT APPROVED / NOT STARTED** pending presentation and approval of the exact diff.
- Workflow dispatch/rerun: **NOT AUTHORIZED / NOT RUN**.
- Stage I implementation: remains owner-approved but not started; the earlier local clone attempt was blocked by DNS.
- Tests, CI runs and artifacts for Stage I: **NOT RUN / NONE**.

## 6. Prohibited operations remain unchanged

No production cryptography, real keys/signatures, root enrollment, Path A/B activation, trust-store mutation, Trust Policy/Anchor instances, durable anchor/custody publication, CI secrets, deployment, VPS/SSH/systemd, Feeder/API, SQLite/canonical T0, trading changes or destructive operations.
