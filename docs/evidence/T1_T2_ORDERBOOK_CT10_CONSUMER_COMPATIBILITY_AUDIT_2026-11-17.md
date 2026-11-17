# T1 → T2 Order Book V1 — CT-10 Consumer Compatibility Audit

Date: 2026-11-17
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/core-operational-proof-20261112`
Audited branch HEAD: `e403e4863ad8a297dc605a612e7bce8164de88fc`
Scope: read-only inspection of the T2 consumer schema, HTTP reader, Bundle validation boundary and existing tests. No source, test, workflow, runtime, T0, T1 or VPS changes.

## 1. Exact files inspected

| File | Blob SHA |
|---|---|
| `core_runtime/orderbook_contract.py` | `1620c9f21b1f3df3c2fb65833f2afd80374bf6a5` |
| `core_runtime/orderbook_http.py` | `89e5129eea4c9e7ceaa4439a546daf112d15c3e3` |
| `core_runtime/input_bundle.py` | `19fb3065da1e7d40c8b4376fe3b51e11c8cc8f87` |
| `core_runtime/bundle_inputs.py` | `f78ebde30413a3329063a2c68c457fe862a50c5e` |
| `core_runtime/one_shot.py` | `ea9eb870f5a3871657d9dc6f6ca1ccf55a0b3f8d` |
| `core_runtime/test_orderbook_http.py` | `6edb8dea8ea208c229439b2655f1ed03c173e055` |
| `core_runtime/test_input_bundle_contract.py` | `e6c331ea791108b5b18eda0eae4cff91d314bd27` |

## 2. CT-10 findings

### Closed V1 schema — source audit PASS

- `validate_snapshot()` requires exact equality between the received JSON keys and the frozen V1 required-field set. Missing and additional fields are rejected as `SNAPSHOT_SCHEMA_INVALID`.
- `bundle_inputs._t1_source_document()` accepts only the exact native T1 field set or the exact documented projected Bundle shape with the exact `t1Evidence` field set.
- `input_bundle._validate_book()` independently requires exact `orderBook` and `t1Evidence` key sets.
- Wrong field types, invalid decimal representations, incomplete books, identity mismatch and invalid sequence/freshness conditions are rejected by the existing validators.

Disposition: V1 is closed-world, not forward-compatible with arbitrary additive fields. A new field must not be silently accepted by an existing V1 consumer. If a future change requires an additive field, it needs an explicit versioned contract decision (normally V2), plus producer/consumer compatibility tests. This audit does not change the frozen V1 contract.

### snapshotId verification — layered behavior

- `orderbook_contract.validate_snapshot()` checks that `snapshotId` is a non-empty string; it does not recompute the digest.
- `OrderBookHttpClient.fetch()` parses strict JSON (including duplicate-key rejection), then calls `validate_snapshot()`. Its returned object has therefore passed schema/semantic validation, but this method alone does not establish cryptographic snapshot identity.
- `bundle_inputs.normalize_orderbook_snapshot()` also calls `validate_snapshot()` and projects the fields; it does not independently recompute `snapshotId`.
- The Core decision Bundle boundary does recompute it: `input_bundle._validate_book()` reconstructs the complete native T1 snapshot from projected bid/ask levels plus `t1Evidence`, removes `snapshotId`, hashes compact sorted-key JSON with SHA-256, and compares the result with the supplied `snapshotId`. A mismatch is rejected as `ORDER_BOOK_T1_SNAPSHOT_ID_MISMATCH`.
- `one_shot.run_once()` calls `validate_bundle()` before invoking the Strategy Core producer. Thus the inspected Core One-shot path reaches the digest-verifying Bundle gate before strategy production.

Important boundary: do not treat the standalone result of `OrderBookHttpClient.fetch()` or `normalize_orderbook_snapshot()` as a fully digest-verified Core decision input. The inspected One-shot path relies on the subsequent Bundle validator.

## 3. Existing test coverage and remaining precision

- `test_orderbook_http.py::test_unknown_missing_or_wrong_identity_fields_fail_closed` covers an unknown field, a missing required field, wrong symbol and wrong contract version.
- `test_input_bundle_contract.py::test_t1_projection_must_match_published_snapshot_levels` mutates projected levels without updating the source snapshot identity and asserts rejection.
- `test_input_bundle_contract.py::test_t1_unverified_continuity_is_rejected` mutates T1 evidence without updating its source snapshot identity and asserts rejection.
- These are fail-closed tamper tests, but the inspected tests do not provide a dedicated assertion of the stable `ORDER_BOOK_T1_SNAPSHOT_ID_MISMATCH` error code for a syntactically valid, incorrect digest. That is a test precision gap, not evidence that the Bundle digest check is absent.
- No test was executed in this read-only audit. Existing historical CI evidence remains scoped to its recorded exact SHA; it is not re-labelled as a run on this audit HEAD.

## 4. Verdict

| Item | Status |
|---|---|
| V1 missing/unknown-field rejection | PASS — source audit; HTTP regression exists |
| Arbitrary additive V1 compatibility | NOT SUPPORTED — intentional closed schema |
| Bundle-bound snapshotId recomputation | PASS — source audit |
| One-shot validation before Core producer | PASS — source audit |
| Dedicated stable-error assertion for snapshotId mismatch | NOT VERIFIED / coverage improvement identified |
| T1 process-to-T2 process runtime delivery | NOT VERIFIED |
| T1 runtime acceptance | NOT VERIFIED |
| T1→T2 live integration | BLOCKED / NOT VERIFIED |

## 5. Next bounded step

Under a separate test-change approval, add one focused T2 regression that supplies a syntactically valid but incorrect `snapshotId` and asserts the exact `ORDER_BOOK_T1_SNAPSHOT_ID_MISMATCH` error at the Bundle validation boundary. Keep the V1 exact-key behavior unchanged. Then run focused and Core First exact-SHA GitHub Actions workflows and record test counts, run IDs and artifacts.

No T1 source changes, T1 activation, T0 access/change, VPS operation, systemd/autostart, Core Runner expansion, AI Strategy activation, exchange credentials or live orders are authorized by this audit.
