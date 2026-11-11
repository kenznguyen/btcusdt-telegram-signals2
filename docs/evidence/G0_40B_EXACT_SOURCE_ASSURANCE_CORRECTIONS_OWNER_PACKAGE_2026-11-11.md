# G0.40-B — Exact-Source Assurance Corrections Owner Decision Package

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Baseline source commit: `a68d0096f6a04b9ce25591118a47b89660c0965c`  
Review report: `docs/evidence/G0_40A_SOURCE_REVIEW_G0_41_READINESS_2026-11-11.md`  
Verdict: **PACKAGE READY — IMPLEMENTATION AND D14/CI SCOPE AMENDMENT REQUIRE EXPLICIT OWNER APPROVAL**

## 1. Purpose

Close the three required source-review findings R1–R3 before any G0.41 measurement request. G0.40-A remains PASS for its approved implementation and focused CI scope; this package does not retroactively invalidate the 18/18 test and compile result. It identifies assurance gaps that must be closed before relying on the runner for owner-facing corpus measurement.

## 2. Requested exact implementation scope

Request a narrow G0.40-B authorization for these exact existing/new paths:

1. `tools/s1_measurement_harness.py` — harden capability-boundary validation and report readback binding.
2. `tools/s1_measurement_runner.py` — bind preflight to actual runner/harness source bytes and verified source identity.
3. `tools/test_s1_measurement_runner.py` — add actual-source, provenance mismatch, capability-bypass, and report-tampering regression tests.
4. `.github/workflows/g040-b-exact-source-verification.yml` — isolated exact-source Actions verification for the final G0.40-B source commit and exact blobs.

No other path is requested. The workflow must remain read-only, least-privilege, with checkout credentials not persisted and no secrets.

## 3. Required acceptance criteria

### R1 — Actual source provenance

- Focused tests must obtain the actual checked-out runner and harness source bytes, not placeholder snippets.
- Hashes must be computed from those exact bytes and passed into the preflight checks.
- The exact checkout commit must be asserted independently by the workflow before tests execute and must be the commit recorded in provenance.
- Wrong source bytes, wrong hashes, mismatched commit identity, or altered source must fail closed.
- No placeholder-only test may be counted as proof of exact-source validation.

### R2 — Capability boundary

- Replace the current incomplete denylist assurance with a documented, bounded policy.
- At minimum, tests must cover aliased file APIs (`from io import open as file_open`), archive extraction (`zipfile`/`tarfile`), and external access through `smtplib`, in addition to existing direct `open` and `socket` probes.
- Prefer a narrow import/syntax allowlist for the exact source modules; unknown imports and unsupported dynamic constructs must fail closed.
- If static analysis cannot make the intended guarantee, explicitly narrow the assertion's meaning and do not describe it as proof of runtime isolation.
- The frozen runner/harness themselves must pass the strengthened policy.

### R3 — Report-to-corpus integrity

- Readback must require the exact expected fixture count, unique fixture IDs, exact ordered inventory, and exact corpus digest.
- Recompute aggregates from rows and reject duplicate, missing, extra, reordered, or modified rows.
- Bind the expected digest to the actual parser-input bytes used for that measurement; a merely well-formed 64-character digest is insufficient.
- Add tampered-report tests for duplicate IDs, wrong order, missing/extra rows, modified raw-byte counts, and altered digest.

## 4. Verification plan

After explicit approval and implementation:

1. Test-first changes for R1–R3.
2. Run only the focused unit tests and `py_compile` for the named source/test files.
3. Review exact diff and ensure only the four approved paths changed.
4. Freeze exact source commit and Git blob IDs.
5. Run the isolated G0.40-B GitHub Actions workflow against that exact commit; record run/job/artifact IDs and digests.
6. Update evidence report and `docs/PROJECT_SESSION_HANDOFF.md` on the existing branch.

The workflow may run only the focused verification commands and source identity assertions. No broad CI, dependency installation, benchmark, corpus measurement, or other workflow is included.

## 5. Explicit exclusions

This package does NOT authorize:

- G0.41 corpus generation or measurement, including running `prepare_preflight` as a standalone measurement.
- Numeric D11 ceiling proposal, ratification, or enforcement.
- Parser/verifier production implementation or cryptographic/trust-root decisions.
- Changes to T0, T1, T2, market data, model/training, CORE_LEDGER, AI_LEDGER, Shared Risk Engine, Kill Switch, or strategy behavior.
- VPS/runtime, external/provider/database/network activity outside the narrowly scoped GitHub Actions source checkout.
- Any lifecycle cleanup, deletion, archive, compaction, restore, or destructive action.
- Any live exchange connection or real order.

G0.34 and G0.37-A one-attempt authorizations remain consumed; no retry or reuse. T0 remains independent/protected. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.

## 6. Owner decision requested

Approve or reject the exact G0.40-B four-path scope and R1–R3 acceptance criteria above. No implementation or workflow will be changed until explicit approval is received. G0.41 remains BLOCKED / NOT AUTHORIZED.
