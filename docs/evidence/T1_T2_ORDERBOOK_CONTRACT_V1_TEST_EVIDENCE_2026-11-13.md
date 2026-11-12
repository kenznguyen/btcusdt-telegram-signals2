# T1 → T2 Order Book V1 — Isolated Test Evidence

Date: 2026-11-13
Status: **PASS — T2-side isolated contract gate**
Scope: deterministic synthetic fixtures and pure T2-side contract validation only.

## 1. Exact source and files

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/core-operational-proof-20261112`
- Tested source commit / exact checkout SHA: `09fc9b3125af2eb4dbb434e3c18faa05dd8c62ed`
- Contract implementation: `core_runtime/orderbook_contract.py`, blob `1620c9f21b1f3df3c2fb65833f2afd80374bf6a5`
- Test suite: `core_runtime/test_orderbook_contract.py`, blob `935a3f2c8467e4f56cc683a7c0afcaba8fbeee00`
- Dedicated isolated workflow: `.github/workflows/t1-t2-orderbook-contract.yml`
- Combined Core operational workflow: `.github/workflows/core-live-data-operational-proof.yml`

## 2. Verified test results

The combined Core operational workflow run #99 checked out the exact source SHA above and ran the T1→T2 Order Book V1 suite as a dedicated step.

- Workflow run: [43275721183](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43275721183)
- Workflow conclusion: **SUCCESS**
- Job: `operational-proof`, conclusion **SUCCESS**
- All 17 job steps: **SUCCESS**
- Test result: **32/32 PASS**, 0 failures, 0 errors; runtime 0.014 s.
- Embedded `core-operational-source-sha.txt`: exact match `09fc9b3125af2eb4dbb434e3c18faa05dd8c62ed`.
- Embedded status:
  - `T1_T2_ORDERBOOK_V1=PASS`
  - `T1_T2_ORDERBOOK_V1_TESTS=32_PASS`
  - `T1_T2_ORDERBOOK_V1_SIDE_EFFECT_GATE=PASS`

Coverage:
- Decimal exactness: 5 tests (preserves precision without binary float; rejects JSON numbers, negative/unbounded and noncanonical/nonfinite values; constrains zero quantity to delta removal).
- Sequence/re-anchor: 10 tests (REST anchor bridge; first event bridge; subsequent `pu == previous u`; old/duplicate watermark behavior; exact delta updates; malformed/gapped candidates; bounded three-attempt re-anchor).
- Reconnect/generation/atomic publication: 4 tests (reconnect invalidates old generation; monotonic generation; no partial candidate publication; readers observe only a whole old or new snapshot).
- Freshness/depth/snapshot acceptance: 10 tests (both source and observation age; 250 ms future skew; 20 levels per side; crossed/locked book; duplicate prices; order; required identity/watermark; complete immutable snapshot).
- Fail-closed side-effect gate: 3 tests (invalid or stale data cannot invoke producer/ledger/risk-admission callbacks; valid snapshot crosses the gate once in order).

## 3. Artifact and integrity

- Artifact name: `core-first-code-operational-proof-43275721183`
- Artifact ID: `13971365776`
- Size: 7,723 bytes
- GitHub artifact digest: `sha256:37bbe961cd97121aafb9866496fd4364f7cb1c33494c2a54422e18c430f7e5dd`
- Expiry: `2026-11-19T18:02:46Z`
- Payload downloaded and ZIP SHA-256 independently computed: `37bbe961cd97121aafb9866496fd4364f7cb1c33494c2a54422e18c430f7e5dd`.
- Independent payload hash **MATCHES** GitHub artifact digest.
- ZIP integrity/readback: **PASS**; embedded source SHA and T1→T2 test status read back and verified.

## 4. Safety boundaries evidenced by CI

- `AI_EXECUTION_ENABLED=false`.
- `PAPER_ONLY=PASS`.
- `CANONICAL_T0_TOUCHED=false`.
- `EXCHANGE_CREDENTIALS_USED=false`.
- `REAL_ORDERS_SENT=false`.
- `VPS_OR_PERSISTENT_RUNTIME_USED=false`.
- Test fixtures are synthetic/disposable; no T1/T0 runtime or network source was used.

## 5. Disposition and limits

- T1→T2 V1 contract semantics: **DESIGN FROZEN FOR REVIEW**.
- T2-side Decimal parser / sequence validator / snapshot acceptance: **PASS — isolated tests 32/32**.
- Invalid/stale data fail-closed before producer, ledger and risk-admission callbacks: **PASS — test evidence**.
- Artifact provenance and payload integrity: **PASS** for the exact source SHA above.
- T1 source implementation: **NOT IMPLEMENTED**.
- T1 runtime publication, reconnect/re-anchor behavior and generation fencing in the real collector: **NOT VERIFIED**.
- Transport/storage atomicity between real T1 and T2: **NOT IMPLEMENTED / NOT VERIFIED**.
- T2 live T1 reader/integration: **BLOCKED**.
- Core one-shot decision runner: **NOT IMPLEMENTED**.
- No production/runtime readiness or trading capability is implied by these tests.

## 6. Next step

Review the T1 collector source against the frozen V1 contract and produce a bounded gap assessment / implementation plan. Do not modify T1, activate T1, access T0/VPS, implement the Core runner, enable AI execution, or send live orders without separate explicit approval.
