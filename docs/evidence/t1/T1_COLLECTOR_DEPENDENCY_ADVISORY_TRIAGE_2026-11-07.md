# T1 Collector Dependency Advisory Triage — 2026-11-07

## Scope and provenance

- Repository: https://github.com/kenznguyen/binance-futures-collector
- Fork source under review: `00cc447e6f39e3e14dfe13eaa88a7a82e40828e3`.
- Pinned upstream baseline: `bc4f0ef633fbeee4a49defd72827f17162693805`.
- `Cargo.toml` blob SHA on both source and upstream: `f373e8b32e090a76399905538742e8b34a669419`.
- `Cargo.lock` blob SHA on both source and upstream: `625a8b8af376511d1d3245fc0ab9f72b138d180e`.
- Lockfile contains 248 package entries. Manifest and lockfile are byte-identical to pinned upstream; the dependency audit findings are inherited from that baseline, not introduced by the sidecar code.
- Latest CI run: [42344752951](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42344752951), security job `128319958140` failed at `cargo-audit`. Job logs returned HTTP 404 through the available GitHub log API; exact current audit output and complete advisory count are not available. The prior CI run reported 12 vulnerabilities and 2 allowed warnings, but that count is not independently reconciled to this run.

## Static candidate mapping

The following mappings compare exact locked package versions against current RustSec advisory records. They are **candidate matches**, not a reconstruction of the failed `cargo audit` output.

| Locked package | Locked version | Advisory / condition | Fixed version from advisory | Initial assessment |
|---|---:|---|---:|---|
| `quinn-proto` | 0.11.16 | RUSTSEC-2026-0338, 0339, 0340, 0341, 0342, 0343 | >=0.11.18 covers the newest set | Candidate vulnerable lock entry; active feature reachability NOT VERIFIED |
| `rustls` | 0.23.43 | RUSTSEC-2026-0285 | >=0.23.45 | Candidate vulnerable |
| `rustls` | 0.23.43 | RUSTSEC-2026-0346, 0347, 0349 | >=0.23.46 | Candidate vulnerable |
| `rustls` | 0.23.43 | RUSTSEC-2026-0348 | >=0.23.46; only relevant when Brotli feature is enabled | Feature reachability NOT VERIFIED |
| `rustls-webpki` | 0.103.14 | RUSTSEC-2026-0382 | >=0.103.16, <0.104.0-alpha.1 | Candidate vulnerable |
| `webpki-roots` | 1.0.9 | RUSTSEC-2026-0381 | >=1.0.10 | Candidate vulnerable |
| `webpki-root-certs` | 1.0.9 | RUSTSEC-2026-0383 | >=1.0.10 | Candidate vulnerable |
| `tokio` | 1.53.1 | RUSTSEC-2026-0386 (INFO / unsoundness) | >=1.53.3 | Candidate warning; API/function reachability NOT VERIFIED |

Additional controls:
- `h2 0.4.18` is above the RUSTSEC-2026-0258 fix floor (>=0.4.16); that advisory is not a candidate match for the locked version.
- `rand 0.8.7` and `rand 0.10.2` are above the respective RUSTSEC-2026-0097 fix floors (>=0.8.6 and >=0.10.1); that advisory is not a candidate match for these locked versions.
- `webpki-roots 0.26.11` is the compatibility wrapper; the 1.x root package it re-exports must be at least 1.0.10. Do not incorrectly classify 0.26.11 itself as the vulnerable trust store.
- `quinn-proto` appears in the lockfile through the `quinn` dependency of `reqwest`; the manifest does not request the `http3` feature. Cargo.lock presence alone does not prove the QUIC package is in the active compile graph. `cargo tree -e features -i quinn-proto` and `cargo tree -e features -i rustls` are required to establish reachability. Cargo audit may still inspect lockfile packages irrespective of active features.
- Rustls Brotli applicability likewise requires inspecting the resolved feature graph, not guessing from the package version.

## Preliminary remediation candidate (NOT APPLIED)

A narrowly scoped lockfile-generated update candidate, subject to Cargo feature/dependency graph inspection and compatibility testing:

1. `quinn-proto` to >=0.11.18 (prefer a currently available patched stable release, if still compatible with locked `quinn`).
2. `rustls` to >=0.23.46.
3. `rustls-webpki` to >=0.103.16 while remaining below 0.104.0-alpha.
4. `webpki-roots` 1.x / `webpki-root-certs` to >=1.0.10.
5. `tokio` to >=1.53.3 for RUSTSEC-2026-0386, while ensuring no regression to the separately affected 1.54.0 release (RUSTSEC-2026-0384). Select an actually available patched stable version and validate the lockfile resolver result.

No version has been written into Cargo.lock. Do not hand-edit Cargo.lock. Use Cargo's resolver (`cargo update -p <package> --precise <version>` or equivalent targeted updates), inspect the full lockfile diff, and retain all unrelated pins. The exact package list must be reconciled against a fresh `cargo audit` output before calling the remediation complete.

## Required validation before any runtime integration

- Capture complete `cargo audit` output and map every advisory ID/package/version to the lockfile.
- Run `cargo tree -e features -i` for each candidate to establish active feature reachability and document lockfile-only optional dependencies separately.
- Apply only targeted Cargo-generated lockfile updates.
- Run collector `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test --all-targets`, sidecar format/Clippy/11 offline tests, and the full security workflow including npm audit.
- Verify PR source SHA, exact checkout SHA from logs, every job result, artifact metadata and test counts.
- Preserve the original upstream baseline and keep the PR Draft/unmerged until all gates pass and review is complete.

## Status and limits

- Static advisory candidate triage: **PARTIAL / NOT VERIFIED**; complete cargo-audit output is missing.
- Manifest/lockfile provenance equality with upstream baseline: **PASS**.
- Dependency remediation: **NOT STARTED / NOT APPLIED**.
- Feature reachability: **NOT VERIFIED**.
- Security gate: **BLOCKED**.
- Tokio writer-worker/runtime integration: **NOT AUTHORIZED TO START BEFORE SECURITY GATE PASSES**.
- No collector process, Binance connection, database, market-data capture, credentials or live execution. `ai_execution_enabled=false`.

## Public advisory references

- https://rustsec.org/advisories/RUSTSEC-2026-0338.html
- https://rustsec.org/advisories/RUSTSEC-2026-0339.html
- https://rustsec.org/advisories/RUSTSEC-2026-0340.html
- https://rustsec.org/advisories/RUSTSEC-2026-0341.html
- https://rustsec.org/advisories/RUSTSEC-2026-0342.html
- https://rustsec.org/advisories/RUSTSEC-2026-0343.html
- https://rustsec.org/advisories/RUSTSEC-2026-0285.html
- https://rustsec.org/advisories/RUSTSEC-2026-0346.html
- https://rustsec.org/advisories/RUSTSEC-2026-0347.html
- https://rustsec.org/advisories/RUSTSEC-2026-0348.html
- https://rustsec.org/advisories/RUSTSEC-2026-0349.html
- https://rustsec.org/advisories/RUSTSEC-2026-0382.html
- https://rustsec.org/advisories/RUSTSEC-2026-0381.html
- https://rustsec.org/advisories/RUSTSEC-2026-0383.html
- https://rustsec.org/advisories/RUSTSEC-2026-0386.html
