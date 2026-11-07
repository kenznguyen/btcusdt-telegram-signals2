# T1 Collector Security Audit — Exact CI Evidence and Feature Graph Diagnostic

Date: 2026-11-07 (Asia/Ho_Chi_Minh)

## Source and checkout provenance

- Repository: `kenznguyen/binance-futures-collector`.
- PR #1: https://github.com/kenznguyen/binance-futures-collector/pull/1 — OPEN / DRAFT / NOT MERGED.
- PR base: `main` at `bc4f0ef633fbeee4a49defd72827f17162693805`.
- Source SHA audited in run 42344752951: `00cc447e6f39e3e14dfe13eaa88a7a82e40828e3`.
- Exact synthetic merge checkout SHA from both Rust and Security job logs: `1e9a10fb71fef5b2722c4af6bb00f5ad5403d54b` (merge of source SHA above into upstream baseline).
- Security job: `128319958140`; Rust job: `128319958110`.
- CI run: https://github.com/kenznguyen/binance-futures-collector/actions/runs/42344752951.

## Exact cargo-audit findings

The recovered Security job log reports **12 vulnerabilities** and **2 warnings** among 248 locked packages.

### Vulnerabilities (12)

| Crate | Locked version | Advisory | Severity | Fixed version |
|---|---:|---|---|---:|
| quinn-proto | 0.11.16 | RUSTSEC-2026-0338 | Not printed in extracted log block | >=0.11.18 |
| quinn-proto | 0.11.16 | RUSTSEC-2026-0339 | Not printed in extracted log block | >=0.11.17 |
| quinn-proto | 0.11.16 | RUSTSEC-2026-0340 | High 7.5 | >=0.11.18 |
| quinn-proto | 0.11.16 | RUSTSEC-2026-0341 | High 7.5 | >=0.11.17 |
| quinn-proto | 0.11.16 | RUSTSEC-2026-0342 | Not printed in extracted log block | >=0.11.17 |
| rustls | 0.23.43 | RUSTSEC-2026-0285 | Medium 5.3 | >=0.23.45 |
| rustls | 0.23.43 | RUSTSEC-2026-0346 | Medium 4.0 | >=0.23.46 |
| rustls | 0.23.43 | RUSTSEC-2026-0348 | Low 3.7 | >=0.23.46 |
| rustls | 0.23.43 | RUSTSEC-2026-0349 | Low 3.7 | >=0.23.46 |
| rustls-webpki | 0.103.14 | RUSTSEC-2026-0382 | Not printed in extracted log block | >=0.103.16, <0.104.0-alpha.1 (or >=0.104.0-alpha.8) |
| webpki-root-certs | 1.0.9 | RUSTSEC-2026-0383 | Not printed in extracted log block | >=1.0.10 |
| webpki-roots | 1.0.9 | RUSTSEC-2026-0381 | Not printed in extracted log block | >=1.0.10 |

The extracted log directly prints high/medium/low severities only for some advisory records; cells marked otherwise are intentionally not inferred. The exact cargo-audit count is 12 and advisory IDs above are taken from the job output.

### Warnings (2)

| Crate | Locked version | Warning |
|---|---:|---|
| tokio | 1.53.1 | RUSTSEC-2026-0386 — unsoundness: `AsyncFd::new` and related constructors violate I/O safety |
| chacha20 | 0.10.1 | yanked crate version |

Warnings are not counted in the 12 vulnerabilities. They still require explicit disposition; do not ignore them merely to obtain a green run.

## Dependency provenance

At source SHA `00cc447e6f39e3e14dfe13eaa88a7a82e40828e3` and upstream baseline SHA `bc4f0ef633fbeee4a49defd72827f17162693805`:

- Cargo.toml blob SHA is identical: `f373e8b32e090a76399905538742e8b34a669419`.
- Cargo.lock blob SHA is identical: `625a8b8af376511d1d3245fc0ab9f72b138d180e`.

Therefore the audited dependency state is inherited from the pinned upstream baseline; the sidecar PR did not introduce the manifest/lockfile contents. No dependency updates or audit suppressions have been made.

## Feature reachability diagnostic workflow increment

Added a read-only diagnostic step before `cargo audit` in `.github/workflows/ci.yml`:

- Source commit: `32867b89379d3f3fe4227b0fb1bf97e8c7063a03`.
- Workflow blob SHA after update: `d7e8bbd600b438ee7fdc5186a59d6c935c0916c9`.
- New step runs `cargo tree --locked -e features -i` for `quinn-proto`, `rustls`, `rustls-webpki`, `webpki-root-certs`, `webpki-roots`, `tokio`, and `chacha20`.
- It records whether each package is in the default resolved feature graph. It does not change dependencies, alter feature selection, weaken the security gate, or suppress cargo-audit.
- PR head verified by GitHub: `32867b89379d3f3fe4227b0fb1bf97e8c7063a03`.
- New PR workflow run: `42348223722`; security job `128330521398`.
- At evidence capture time, diagnostic step completed SUCCESS; cargo-audit was still IN_PROGRESS. Full step output, feature paths and final run conclusion are NOT VERIFIED yet.
- Dashboard frontend job `128330521390` and backend job `128330521434` were SUCCESS. Collector Rust and Docker jobs were still running.

## Sidecar validation on run 42344752951

Rust job `128319958110`, checked out synthetic merge SHA `1e9a10fb71fef5b2722c4af6bb00f5ad5403d54b`:

- Existing collector library tests: 40 passed.
- Existing collector binary tests: 1 passed.
- Sidecar writer offline tests: 11 passed, 0 failed.
- Collector Format, Clippy, Build, Test, Sidecar format, Sidecar Clippy and Sidecar offline tests all PASS.

## Verdict and next actions

- Exact prior cargo-audit findings: **VERIFIED** from recovered job log.
- Source/checkout provenance: **VERIFIED** for run 42344752951.
- Fork/upstream dependency baseline identity: **PASS**.
- Feature graph reachability: **PENDING** run 42348223722.
- Dependency remediation: **NOT APPLIED**.
- Security gate: **BLOCKED**.
- PR #1: **OPEN / DRAFT / NOT MERGED**.

Next:
1. Retrieve completed output for run 42348223722 and classify each advisory package as default-feature reachable or lockfile-only / optional.
2. Resolve exact Cargo package graph for the yanked `chacha20 0.10.1` and Tokio warning.
3. Propose targeted Cargo-generated lockfile updates only after reachability and current patched versions are confirmed.
4. Run collector, sidecar, dashboard, Docker and full security checks on the resulting exact source SHA.
5. Keep runtime integration blocked until security and all CI gates pass.

Safety limits remain: no collector process, no Binance DNS/TCP/WebSocket connection, no exchange data capture, no database access, no runtime integration, no live orders. `ai_execution_enabled=false`.


## 2026-11-07 Addendum — Completed feature reachability diagnostics (run 42348223722)

- Collector fork source SHA: 32867b89379d3f3fe4227b0fb1bf97e8c7063a03; PR #1 remains OPEN / DRAFT / NOT MERGED, base bc4f0ef633fbeee4a49defd72827f17162693805.
- PR workflow run https://github.com/kenznguyen/binance-futures-collector/actions/runs/42348223722, event pull_request, completed FAILURE. Push run https://github.com/kenznguyen/binance-futures-collector/actions/runs/42348219928, event push, completed FAILURE. Both runs reference the same source SHA.
- PR run exact checkout: synthetic merge commit 43d5030bd9f08da0ab133c778a43eb2a25e80d1d, merging source 32867b89379d3f3fe4227b0fb1bf97e8c7063a03 into base bc4f0ef633fbeee4a49defd72827f17162693805. Rust job 128330521322, security job 128330521398. Push run checks out source SHA directly; Rust job 128330509513, security job 128330509319.
- Both runs: collector format/Clippy/build/tests and sidecar format/Clippy/offline tests PASS; collector library 40/40, binary 1/1, sidecar writer 11/11. Dashboard backend, dashboard frontend and Docker jobs PASS. Security job FAILS at cargo-audit; npm audit steps are SKIPPED. Each run reports 12 vulnerabilities and 2 allowed warnings among 248 locked packages.
- Diagnostic default-graph results (identical in both runs): quinn-proto=PRESENT, rustls=PRESENT, rustls-webpki=PRESENT, webpki-root-certs=PRESENT, tokio=PRESENT, chacha20=PRESENT, webpki-roots=NOT_IN_DEFAULT_GRAPH (cargo tree inverse lookup exits 101). This is a default resolved feature graph check only; it does not establish target-specific absence. Cargo output explicitly recommends --target all to inspect target-specific dependencies. No complete dependency paths were captured for all packages, so path-level reachability remains PARTIAL / NOT VERIFIED.
- Exact audit remains 12 vulnerabilities + 2 warnings. Advisory IDs and locked versions are unchanged from the table above. In particular, webpki-roots 1.0.9 is in Cargo.lock but not the default feature graph; do not assume its advisory is exploitable or irrelevant until all-target graph and dependency source paths are checked. The webpki-root-certs 1.0.9 package is separately PRESENT in the default graph.
- Both workflow runs returned no artifacts. No artifact IDs or digests.
- Workflow diagnostic step itself PASS; security gate remains BLOCKED. No Cargo.toml/Cargo.lock updates, no feature selection changes, no advisory suppressions, no CI gate weakening.
- Next: inspect cargo tree --locked --target all -e features -i for all advisory packages; capture complete reverse dependency paths, distinguish default/target/optional/lockfile-only packages, and inspect the direct dependency source for webpki-root-certs and webpki-roots. Then formulate only Cargo-resolver-generated compatible updates with regression tests. Do not begin collector runtime integration.
- Safety unchanged: no collector runtime, Binance connection, exchange capture, database access, merge, or live execution; ai_execution_enabled=false.


## 2026-11-07 Addendum — All-target dependency graph CI queued

- Added a separate read-only diagnostic step to the fork workflow, preserving the default-graph diagnostic and correcting printf output so tree paths are emitted as real log lines.
- New step runs cargo tree --locked --target all -e features -i for quinn-proto, rustls, rustls-webpki, webpki-root-certs, webpki-roots, tokio and chacha20. No manifest, lockfile, runtime or security gate changes.
- Fork source commit: eda201bb5e659e438b81a09eee7c20cdd749763a; workflow blob SHA a2b82d4b5e08763aa465ec3cb37b15525252a677.
- New push run 42349892441; new PR run 42349896315. Security jobs: push 128335579401, PR 128335591206. At last inspection both all-target diagnostic steps completed SUCCESS, while cargo-audit and other jobs were still running. Final output and run conclusions remain PENDING / NOT VERIFIED.
- PR #1 description updated to source SHA eda201bb5e659e438b81a09eee7c20cdd749763a and the pending run IDs. PR remains OPEN / DRAFT / NOT MERGED.
- Next: wait for both runs to finish; retrieve all-target output and full package paths; confirm source/checkout SHA, test totals, audit result, npm audit status and artifacts. Do not modify dependencies until the all-target graph is understood.


## 2026-11-07 Addendum — Corrected interpretation of all-target diagnostics

- Runs 42349896315 (PR) and 42349892441 (push) completed. Both: collector library 40/40, binary 1/1, sidecar 11/11, dashboard backend/frontend and Docker PASS; cargo-audit FAIL with 12 vulnerabilities + 2 warnings. npm audit was skipped after cargo-audit failed. Both runs returned no artifacts.
- PR run exact synthetic merge checkout SHA: 0c28969 (merge of source eda201bb5e659e438b81a09eee7c20cdd749763a into base bc4f0ef633fbeee4a49defd72827f17162693805). Push run checked out source eda201bb5e659e438b81a09eee7c20cdd749763a.
- The previous all-target diagnostic was not conclusive for every package. quinn-proto returned "warning: nothing to print" despite exit 0, so its printed PRESENT marker is not proof of a dependency path. webpki-roots was ambiguous because Cargo.lock has versions 0.26.11 and 1.0.9; its NOT_FOUND marker only means the unqualified package spec failed with exit 101, not that the advisory version is absent.
- Paths actually emitted by the previous command: rustls 0.23.43 is reachable through reqwest 0.13.1 / hyper-rustls 0.27.9 and tokio-tungstenite 0.30.0; rustls-webpki 0.103.14 via rustls-platform-verifier 0.6.2 → reqwest 0.13.1 and via rustls 0.23.43; webpki-root-certs 1.0.9 via rustls-platform-verifier 0.6.2 → reqwest 0.13.1; tokio 1.53.1 via hyper-util 0.1.20 → reqwest 0.13.1; chacha20 0.10.1 via rand 0.10.2 → tungstenite 0.30.0 → tokio-tungstenite 0.30.0. These are all-target inverse graph paths, not proof every platform compiles or runtime code executes.
- Corrective workflow step now uses exact package IDs (including versions) and no feature-tree output mode: cargo tree --locked --target all -i <crate@version> for all seven advisories. Fork source SHA 22900b860426a5c19622ec6b5ea3673646df2229; workflow blob SHA f966f0040533b28e97897200db0b4638129b349a. New PR run 42350687437 (security job 128337964057) and push run 42350684200 (security job 128337953368) are still IN_PROGRESS at the last poll; exact-version output and final conclusions NOT VERIFIED.
- PR #1 remains OPEN / DRAFT / NOT MERGED. No manifest/lockfile dependency changes, audit suppressions, feature changes or gate weakening.
- Next: wait for exact-version runs; verify quinn-proto@0.11.16 and webpki-roots@1.0.9 paths without ambiguous specs; record final checkout SHA, tests, audit/npm and artifact results. Only then propose narrow Cargo-resolver-generated remediation.


## 2026-11-07 Addendum — Exact-version all-target dependency diagnostics completed

- Collector fork source SHA: `22900b860426a5c19622ec6b5ea3673646df2229`; pinned upstream base: `bc4f0ef633fbeee4a49defd72827f17162693805`.
- PR run [42350687437](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42350687437), security job `128337964057`, checked out synthetic merge SHA `ac53d7b672e91590f16e555f2ef0ffd232ab905c`. Push run [42350684200](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42350684200), security job `128337953368`, checked out source SHA `22900b860426a5c19622ec6b5ea3673646df2229`.
- Both runs: collector library 40/40, binary 1/1, sidecar writer 11/11; Rust format/Clippy/build, dashboard backend/frontend and Docker PASS. Security FAIL at cargo-audit with 12 vulnerabilities + 2 warnings among 248 locked packages. npm audit high/dev steps SKIPPED after cargo-audit failure. Both runs returned no artifacts.
- Exact all-target reverse paths:
  - `rustls@0.23.43`: `reqwest 0.13.1 → hyper-rustls 0.27.9`; also `tokio-tungstenite 0.30.0` via `tokio-rustls 0.26.4`.
  - `rustls-webpki@0.103.14`: via `rustls 0.23.43` and `rustls-platform-verifier 0.6.2 → reqwest 0.13.1`.
  - `webpki-root-certs@1.0.9`: `rustls-platform-verifier 0.6.2 → reqwest 0.13.1`.
  - `webpki-roots@1.0.9`: direct through `reqwest 0.13.1`; separate `webpki-roots 0.26.11` is also present via `tokio-tungstenite 0.30.0`. Exact package query removes prior version ambiguity.
  - `tokio@1.53.1`: direct collector dependency and indirect paths via `hyper-util 0.1.20 → reqwest 0.13.1`, `tokio-tungstenite 0.30.0`, and related Hyper/Tower packages.
  - `chacha20@0.10.1`: `rand 0.10.2 → tungstenite 0.30.0 → tokio-tungstenite 0.30.0`.
  - `quinn-proto@0.11.16`: command exited 0 but emitted only `warning: nothing to print`; no reverse path was emitted. Reachability remains **NOT VERIFIED**; the workflow's PRESENT marker is not valid evidence.
- Audit finding counts and IDs remain unchanged from the verified prior run: 12 vulnerabilities + 2 warnings. The exact-version diagnostics do not prove runtime execution or exploitability; they establish resolved all-target graph paths only.
- Verdict: reverse paths verified for six package IDs; quinn-proto path NOT VERIFIED; security gate BLOCKED; dependency remediation NOT STARTED. No Cargo.toml/Cargo.lock changes, feature changes, audit suppressions or gate weakening.
- PR #1 remains OPEN / DRAFT / NOT MERGED. No collector runtime integration, Binance connection, database access, capture, or live execution.
- Next: investigate quinn-proto package resolution separately (including Cargo.lock package metadata and target/feature-specific dependency edges); then build a narrow Cargo-resolver-generated remediation plan for reachable advisory packages and validate compatibility before changing dependencies.
