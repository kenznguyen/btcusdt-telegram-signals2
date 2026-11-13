# T1 → PaperLedger Compatibility — RED Test Checkpoint

Date: 2026-11-13 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/core-operational-proof-20261112`
Status: **BLOCKED — RED execution NOT VERIFIED**

## Owner authorization
Owner approved the narrowly scoped T1-compatible PaperLedger book-input contract. Approval covers preserving T1 provenance/snapshot identity and exact levels/timestamps while retaining existing risk, Kill Switch, reservation, idempotency, fill and Ledger schema behavior. It does not authorize runtime/VPS activation, AI execution or live orders.

## Changes committed
- Added T1 PaperLedger boundary tests to `paper_execution/test_ledger.py`.
- Tests specify opt-in T1 admission, legacy-path rejection of T1, wrong source/connector/symbol rejection, exact projection binding, snapshot digest mismatch rejection, and stale/future timestamp rejection.
- Test commit: `97ea99be2647c682f10fdca496731805b06ae2d8`.
- Added a focused GitHub Actions workflow `.github/workflows/paper-ledger-t1-compatibility.yml`, restricted to the active branch for push, pull_request, and workflow_dispatch, with read-only repository permissions.
- Workflow commit: `20583fc7542a5373dc39aa30ecc5d6bef527d90e`.
- Branch comparison from prior handoff HEAD `a034729d7c0946f35937e6c29a5c5c8dd7f8a898` to current source `20583fc7542a5373dc39aa30ecc5d6bef527d90e`: ahead 2 / behind 0; no rebase, merge or force-push.

## Verification
- T1 contract reviewed: `T1_T2_ORDERBOOK_V1`, 20 levels per side, VERIFIED continuity, FRESH status, timestamp bounds and snapshot identity.
- Test source is authored, but RED execution is **NOT VERIFIED**. No GitHub Actions run is exposed for either commit by the available run/status queries; combined commit status for workflow commit returned no statuses.
- No production Ledger source behavior has been modified.
- No local checkout/test execution, Runner implementation, database migration, T0/T1/T2 runtime, VPS, service, systemd/autostart, AI execution or live-order operation was performed.
- Workflow run ID, job IDs, artifact IDs and digests: **NOT AVAILABLE / NOT VERIFIED**.

## Required next step
Obtain an observable GitHub Actions run for the exact current branch SHA and confirm the intended RED failure for the new test suite. Only then implement the minimum Ledger validator extension, rerun focused tests to GREEN, add scoped admission/idempotency integration tests, and proceed to One-shot Core Runner. Do not implement Ledger behavior before RED is observed; do not claim GREEN from test authoring or commit existence.
