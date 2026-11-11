# G0.40-A — Source Review and G0.41 Readiness Assessment

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Reviewed frozen source commit: `a68d0096f6a04b9ce25591118a47b89660c0965c`  
Runner blob: `784d2b5381fa50007ceba468b8bc81ce045b80c2`  
Runner test blob: `47363d0a30cd12795fe43b22e0b5a22f934854bf`  
Harness blob: `0f713a1cc87f4c0c355d4488f1cf6af4d8f08d98`  
Related Actions run: `43048826022` (18/18 focused tests and compile PASS)  
Verdict: **REVIEW COMPLETE — G0.41 NOT READY; CORRECTIVE WORK REQUIRED**

## 1. Review scope and method

Read-only review of the frozen G0.40-A runner, focused tests, and G0.39 harness. Reviewed tests first, then implementation, across correctness, readability, architecture, security/capability boundaries, and evidence integrity. No source was changed and no test, compile, corpus generation, or measurement was run in this review.

The successful Actions run verifies that the pinned source was checked out and that the focused test/compile commands passed. It does not, by itself, prove that every assurance assertion exercised the actual frozen source bytes.

## 2. Findings

### R1 — Required: test provenance uses placeholder source bytes rather than the frozen source

The focused tests define `HARNESS_SOURCE` and `RUNNER_SOURCE` as short synthetic Python snippets, compute hashes for those snippets, and pass them to `prepare_preflight()`. The tests therefore exercise digest and capability-check behavior against placeholders, not the actual harness and runner files.

The workflow separately asserts the real Git blob IDs, but it does not pass the actual source bytes into the runner's provenance/capability checks. Consequently, the CI PASS does not establish that A-10/A-12/A-13 were evaluated against the actual frozen source. `source_commit` is also a caller-supplied syntactically valid string; the function does not bind it to an independently verified checkout identity.

**Required correction:** provide a separately verified source identity envelope to the preflight invocation; bind the exact checkout commit and actual runner/harness bytes to the recorded provenance; add tests proving altered bytes, wrong blob IDs, and mismatched checkout identity fail closed. Do not treat placeholder-only checks as exact-source verification.

### R2 — Required: capability-boundary AST denylist is bypassable

`validate_capability_boundary()` uses a finite import/call denylist. Examples not covered by the current rules include file extraction through `zipfile.ZipFile.extractall()` or `tarfile.TarFile.extractall()`, and aliased file APIs such as `from io import open as file_open`. For external access, modules such as `smtplib` are not in the forbidden set. The current frozen runner/harness source does not use these APIs, but the validator is not a complete proof of absence of persistence or external access.

The current negative tests cover direct `open()` and direct `socket` imports only, not these bypass classes.

**Required correction:** replace the broad assurance claim with a narrowly specified allowlist/static policy that covers the supported Python syntax and import surface, add regression probes for aliasing and extraction/network APIs, or use an execution boundary that actually denies filesystem/network capabilities. Keep the policy bounded and fail-closed.

### R3 — Required: report readback does not bind report rows to the frozen inventory or corpus digest

`_safe_report_measurement()` validates row shapes, aggregate recomputation, and that `corpus_sha256` has 64 lowercase hexadecimal characters. It does not require unique fixture IDs, exact expected inventory/order, or recompute the digest from the parser-input bytes. A structurally valid report with duplicate fixture IDs and an arbitrary well-formed digest can pass readback if its aggregates are internally consistent.

**Required correction:** bind readback to the expected ordered fixture inventory and exact input digest available to the preflight; verify row uniqueness/count/order and digest equality, and add tampered-report regression tests. Do not claim that aggregate recomputation alone establishes report-to-corpus integrity.

### R4 — Advisory: formatting and explicit contracts

The harness compresses multiple statements onto single lines and uses broad `Any`/untyped mapping boundaries in places. This is not the current G0.41 blocker, but the corrective change should keep validation contracts explicit and avoid expanding the harness unnecessarily.

## 3. Verification evidence and limits

- GitHub Actions run `43048826022`: SUCCESS.
- Exact checkout asserted: `a68d0096f6a04b9ce25591118a47b89660c0965c`.
- Exact runner/test blobs asserted: `784d2b5381fa50007ceba468b8bc81ce045b80c2` / `47363d0a30cd12795fe43b22e0b5a22f934854bf`.
- Focused tests: 18/18 PASS.
- Focused `py_compile`: PASS.
- The Actions run does not address R1–R3; these are review findings about assurance coverage and report semantics, not failures observed in that run.
- No separate corpus measurement was performed.

## 4. Gate disposition

- G0.40-A implementation and focused CI verification: **PASS**, limited to the recorded scope.
- Source review: **REVIEW COMPLETE — REQUIRED FINDINGS R1–R3 OPEN**.
- G0.41 measurement readiness: **BLOCKED** pending owner-approved corrective work and exact-source re-verification.
- Numeric D11 ceilings: **OPEN / NOT RATIFIED**.
- No retry of G0.34 or G0.37-A measurements; their one-attempt authorizations remain consumed.
- No parser/verifier implementation, CI expansion, runtime/VPS, external/provider/database/network, T0/T1/T2, market-data, model, ledger, lifecycle, or destructive operation.

## 5. Recommended next package

Prepare a docs-only G0.40-B owner decision package requesting a narrow correction to the existing runner/harness/tests and exact-source verification. Proposed scope should name the exact files and tests, define R1–R3 acceptance criteria, and keep corpus generation/measurement explicitly excluded. After implementation, focused tests, compile, exact-source CI, and review pass, a separate G0.41 package may request one measurement attempt. G0.41 must not be inferred from this review or the G0.40-A PASS.

T0 remains independent/protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.
