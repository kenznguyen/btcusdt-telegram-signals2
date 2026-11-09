# T1 Manual VPS Test Receipt — 2026-11-09

## Scope and safety boundary

- Purpose: manually execute the Rust validation commands declared by `.github/workflows/ci.yml` against an isolated checkout because GitHub Actions for the exact T1 HEAD is failing before job creation.
- Repository: `kenznguyen/binance-futures-collector`.
- Tested source SHA: `4566cffbbcf8495182abbc0d3496fdc65709ac14`.
- Checkout: `/home/ubuntu/t1-test`, detached HEAD.
- Evidence directory: `/tmp/t1-manual-evidence-4566cffbbcf8495182abbc0d3496fdc65709ac14`.
- Build target directory: `/tmp/t1-manual-target-4566cffbbcf8495182abbc0d3496fdc65709ac14`.
- Toolchain: rustc 1.99.1, cargo 1.99.1, rustfmt 1.10.0-stable, Clippy 0.1.99; cc/gcc 15.2.0, GNU Make 4.4.1, ld 2.46.
- This was an isolated manual test only. No collector was launched, no Binance connection was made, and no T0/T1 runtime or canonical data was modified.

## Exact command set and exit codes

Commands correspond to the Rust validation steps in the T1 CI workflow:

| Check | Command | Exit |
|---|---|---:|
| Collector format | `cargo fmt --all --check` | 1 — FAIL |
| Collector Clippy | `cargo clippy --all-targets --all-features -- -D warnings` | 0 — PASS |
| Collector release build | `cargo build --release --locked` | 0 — PASS |
| Collector tests | `cargo test --all` | 0 — PASS |
| Sidecar format | `cargo fmt --manifest-path crates/connection-sidecar/Cargo.toml --all -- --check` | 0 — PASS |
| Sidecar Clippy | `cargo clippy --manifest-path crates/connection-sidecar/Cargo.toml --all-targets -- -D warnings` | 0 — PASS |
| Sidecar tests | `cargo test --manifest-path crates/connection-sidecar/Cargo.toml --all-targets` | 0 — PASS |

## Test counts

Captured from the saved test logs:

- Collector: 48 passed + 1 passed; 0 failed. An additional target reported 0 tests.
- Sidecar: 12 passed + 27 passed; 0 failed.
- Total executed test cases: 88 passed, 0 failed. Zero-test targets are excluded from the total.

## Formatting finding

- `cargo fmt --all --check` failed at `src/utils/csv_writer.rs:1303`.
- Rustfmt requests the fixture array in `decimal_lexical_validation_rejects_non_finite_and_malformed_forms` and the `assert!` call to be wrapped across multiple lines.
- This is a formatting-only failure in the captured output. No source correction was made during this pinned-SHA test.
- The exact diff is retained in `collector_fmt.log` in the evidence directory.

## Log SHA-256 manifest

| File | SHA-256 |
|---|---|
| `collector_clippy.log` | `0eaab8558140a856e4fb8c7afbfb30a33cdfe7c1c508dafd52535d847cdcffae` |
| `collector_fmt.log` | `139b065879544c75a769c9256c6fd69e36b15eb5760d9e84e9a0e3150c7d9a0a` |
| `collector_tests.log` | `f6bb2544145c516d0c4b70e544dc3d7aa75e845e682838fd84e6b6e00487f416` |
| `release_build.log` | `7ed715f6fcbbd044e023bb56a21da5d96ad75e4da313ef7f09b18c52a6d7405a` |
| `sidecar_clippy.log` | `3d2f068d6ebcfad5b11ff42c74f330efc7e1a0d54124c6080f65efffbce45e2b` |
| `sidecar_fmt.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `sidecar_tests.log` | `a617c8945f06d635f04d7f9ea9b8dbaab72e9107229c61c2d4ffcc6236e0e8b8` |
| Passing `*.exit` files | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| `collector_fmt.exit` | `4355a46b19d348dc2f57c046f8ef63d4538ebb936000f3c9ee954a27460dd865` |

The log hashes above are transcribed from the operator-provided terminal evidence. The raw logs remain on the VPS at the evidence directory path above; they are not attached to this GitHub document.

## Generated lockfile and checkout cleanup

- Running the sidecar manifest commands produced an untracked file: `crates/connection-sidecar/Cargo.lock`.
- File size: 4,905 bytes.
- SHA-256 before removal: `c6fa4823bb25ac00873464ed733eb0816e962ffc370e13451dc291f160b01bdc`.
- `git ls-tree HEAD crates/connection-sidecar/Cargo.lock` returned no entry; `git check-ignore` returned no rule.
- The owner explicitly authorized removal of this exact generated untracked file from the isolated checkout.
- Final operator verification: HEAD remained `4566cffbbcf8495182abbc0d3496fdc65709ac14`; `git status --short --branch` returned only `## HEAD (no branch)`; the generated lockfile was absent.
- No tracked source file was changed.

## GitHub Actions exact-HEAD status

For exact source SHA `4566cffbbcf8495182abbc0d3496fdc65709ac14` in the T1 repository:

- Push run: `42646416010` — `startup_failure`, zero jobs.
- Pull request run: `42646425898` — `startup_failure`, zero jobs.
- These failures occurred before runner/job creation. They are not Rust test failures and provide no GitHub Actions test result or artifact.
- Manual validation does not replace GitHub Actions exact-HEAD validation.

## Final status

- Manual Rust validation: **PARTIAL PASS (6/7 commands)**.
- Test cases: **88 PASS / 0 FAIL**.
- Formatting: **BLOCKED** by collector rustfmt check.
- GitHub Actions exact HEAD: **BLOCKED** by pre-job startup failure.
- Exact T1 HEAD manual test evidence: captured for `4566cffbbcf8495182abbc0d3496fdc65709ac14`.
- T1 → T0/T2 integration: **NOT VERIFIED**.
- T1 activation/deployment: **NOT AUTHORIZED / NOT PERFORMED**.
- No live orders, exchange credentials, T0/T2 mutation, runtime operation, PR merge, issue retarget, or workflow configuration change occurred.

## Next step and restrictions

1. Preserve this receipt and raw logs as the manual-test evidence set.
2. Resolve the GitHub Actions dispatcher/startup blocker through an owner-authorized GitHub Support path or another supported recovery path; do not mutate workflow YAML or repository settings without evidence.
3. Separately authorize any formatting-only source correction, then validate a new exact SHA when Actions can dispatch.
4. Keep T1 inactive and integration NOT VERIFIED until separate evidence and approval exist.

This receipt records a bounded manual test. It is not an independent review, CI PASS, integration acceptance, deployment approval, or production-readiness claim.


## Post-rustfmt manual revalidation — 2026-11-09

A formatting-only correction was applied in the isolated VPS checkout after the initial run. The tested source baseline remained HEAD `4566cffbbcf8495182abbc0d3496fdc65709ac14`; the local working-tree patch was not committed.

- Changed file: `src/utils/csv_writer.rs` only.
- Diff: 14 insertions, 2 deletions; formatting of the existing decimal lexical validation test only. No production logic, fixture values, or assertions were changed.
- Patch SHA-256 (`git diff --binary | sha256sum`): `90cee952837cf753bf872c2cb19f75e1157dc5c64eb937d58c62cbe796a31ec6`.
- `git diff --check`: PASS.
- `cargo fmt --all --check`: PASS.
- All 7 CI Rust commands were rerun with exit code 0: collector fmt, collector Clippy, release build, collector tests, sidecar fmt, sidecar Clippy, sidecar tests.
- Tests: collector 48 + 1; sidecar 12 + 27 = **88 PASS / 0 FAIL**.
- Log directory: `/tmp/t1-manual-evidence-postfmt-4566cffbbcf8495182abbc0d3496fdc65709ac14` (raw logs remain on VPS; not uploaded as GitHub artifacts).
- Log SHA-256: collector_clippy `ca023ed2d5a7ab5dfaa5acfceee8bf6d723a26f057739c8739ddc98012dcd1ca`; collector_fmt `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; collector_tests `cdcf4b9ce2f7e6b904851caef61b1b0c9a77729a8562757752f2cb7f620557ae`; release_build `b8df50626e135effe03e54235f88e7f4e1cf4cc3fcccfc375618b5b6c539a807`; sidecar_clippy `7e905ee46d8a59d95b3d9575e990e83cd4842490676754ea62817d67c22ea68c`; sidecar_fmt `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; sidecar_tests `f21f4f439d759c8dc458a69396d3df091b294f947a5695ac3e1ffdb5ca794b43`.
- Cargo generated untracked `crates/connection-sidecar/Cargo.lock`, 4,905 bytes, SHA-256 `c6fa4823bb25ac00873464ed733eb0816e962ffc370e13451dc291f160b01bdc`; it was verified untracked and explicitly authorized for removal. Final checkout check confirmed it absent.
- Final operator status: detached HEAD `4566cffbbcf8495182abbc0d3496fdc65709ac14`; only ` M src/utils/csv_writer.rs`; no other untracked file. Patch SHA above.

### Updated bounded status

- Manual Rust validation of baseline plus the uncommitted formatting-only patch: **7/7 commands PASS; 88 PASS / 0 FAIL**.
- This is not a test of a new commit SHA and is not GitHub Actions CI PASS.
- GitHub Actions exact-HEAD dispatcher remains **BLOCKED / NOT VERIFIED** (runs `42646416010` and `42646425898`, both pre-job startup failures).
- T1 → T0/T2 integration remains **NOT VERIFIED**; T1 activation/deployment remains **NOT AUTHORIZED / NOT PERFORMED**.
- No source commit/push, collector launch, Binance connection, exchange credentials, runtime mutation, PR merge, issue retarget, or workflow change occurred.
