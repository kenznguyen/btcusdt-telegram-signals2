# D07.10 — V1 Schema Validator Synthetic Test Evidence

Date: 2026-11-14  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Tested source SHA: `f693282f3b6b517127d175846a8cc8bc3b2c1170`  
Status: **PASS — SYNTHETIC CONTRACT VALIDATION ONLY**

## 1. Approved scope

Owner-approved work was limited to:
- Machine-readable JSON Schema for `TARDIS_COLLECTOR_LINEAGE_V1`.
- Offline structural and cross-field validator bound to a supplied D07.8 manifest envelope.
- Synthetic positive/negative tests.
- Dedicated GitHub Actions workflow and retained test artifact.
- Documentation and handoff update.

Explicitly excluded: Tardis acquisition/API/credentials, real evidence-reference resolution, real-file parser, D07.2 or D07.8 verifier changes, funding rows, ledger/database writes, T0/VPS access, Runner/One-shot and live execution.

## 2. Source files

| Path | Purpose |
|---|---|
| `d07_9_lineage/schema.v1.json` | Draft 2020-12 exact V1 envelope |
| `d07_9_lineage/validator.py` | Fail-closed structural/semantic validator |
| `d07_9_lineage/test_validator.py` | 37 synthetic tests |
| `d07_9_lineage/requirements.txt` | Isolated pin: `jsonschema==4.25.1` |
| `d07_9_lineage/README.md` | API, invocation and status boundaries |
| `.github/workflows/d07-9-lineage-validator.yml` | Exact-SHA CI, synthetic-only environment and artifact upload |

## 3. Final GitHub Actions evidence

- Workflow: [D07.9 Collector Lineage V1 Synthetic Validator](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43580970861)
- Run ID: `43580970861`; event: `push`; branch: `feature/core-operational-proof-20261112`.
- Exact checkout/source SHA: `f693282f3b6b517127d175846a8cc8bc3b2c1170`.
- Job ID: `132405411263`; conclusion: **SUCCESS**.
- Test result: **37 tests passed**, including JSON Schema Draft 2020-12 meta-schema validation.
- Log summary: `Ran 37 tests`; `OK`.
- Workflow safety markers: `D07_9_SCOPE=SYNTHETIC_FIXTURES_ONLY`; `D07_2_D07_8_LEDGER_T0_VPS=UNCHANGED`; `AI_EXECUTION_ENABLED=false`; database and exchange credential environment variables empty.
- Artifact ID: `14108756629`.
- Artifact name: `d07-9-lineage-validator-f693282f3b6b517127d175846a8cc8bc3b2c1170`.
- Artifact size: 1,662 bytes.
- GitHub upload digest: `sha256:50b08e81c6ac4f6b7872adc784685d658b0afe51b848512ab3afa19c15e5c588`.
- Expiry: `2026-11-21T09:31:42Z`.
- Limitation: the digest is GitHub artifact-upload metadata; artifact payload bytes were not independently downloaded and re-hashed.

## 4. Test coverage summary

1. Valid unreviewed sidecar remains NOT_VERIFIED for byte integrity and collector independence.
2. A reviewer-declared `SUPPORTED_WITHIN_BOUNDARY` remains NOT_VERIFIED until referenced evidence is independently resolved.
3. Missing/unknown schema version and unsupported extra V1 fields.
4. Duplicate record ID (when caller supplies the record registry), empty or mismatched package ID.
5. Complete raw-file set equality with D07.8 `raw/` inventory; duplicate, omitted, derived-as-raw, traversal and readback path mismatch.
6. Request/network reference nullability and unavailable-reason pairing.
7. Timestamp validity, acquisition/readback order, separate process and execution identity.
8. Shared material dependency => BLOCKED; unresolved materiality => NOT_VERIFIED; missing unknown reason => BLOCKED.
9. Full dependency category inventory and Binance common-issuer non-promotion.
10. Secret-like strings, transformation provenance, raw/derived namespace and supersession pair.
11. Custody event identity/order and required readback event.
12. Caller-supplied aggregate PASS is rejected.

## 5. Fail-closed interpretation

The validator checks schema, declared references and internal relationships only. It does not dereference any `*Ref`, verify custody evidence, read preserved bytes or recompute SHA-256. It never promotes:
- `evidenceReferenceResolution`
- `byteIntegrity`
- `collectorIndependence`
- `issuerAuthenticity`
- `observationCorroboration`
- `enumerationCompleteness`
- `freshness`
- `globalCompleteness`
- `factualTruth`

All remain **NOT_VERIFIED**. `issuerIndependence` remains `NOT_AVAILABLE_SAME_ISSUER` for Binance REST versus Tardis-collected Binance observations.

## 6. TDD history and corrections

- RED run [43580428017](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43580428017): expected failure before validator implementation.
- Initial GREEN run [43580510663](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43580510663): 32/32.
- Hardening runs [43580653567](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43580653567) and [43580708667](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43580708667): failed while new assertions exposed missing unknown-reason and review-time handling; findings were corrected.
- Expanded run [43580769251](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43580769251): 37/37.
- Final exact-source run [43580970861](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43580970861): 37/37 PASS.

## 7. Final disposition

- D07.10 schema/validator/synthetic CI gate: **PASS — structural contract behavior only**.
- D07.8 manifest and validator: **UNCHANGED**; D07.8 design blob remains `13330cb21e15fcbad05f4ea557c352f892d3143e`.
- D07.2: `BLOCKED_SHARED_LINEAGE`, unchanged.
- D07 overall: **PARTIAL**.
- PAPER ledger bootstrap: **BLOCKED / NOT APPROVED**.
- Real Tardis custody, collector independence, overlap, issuer authenticity, freshness, completeness and factual truth: **NOT VERIFIED**.
- Full repository/PaperLedger regression: **NOT RUN** in this increment.
- No Tardis data/API, credentials, real files, funding rows, ledger/database, D07.2/D07.8 verifier, T0/VPS, Runner/One-shot or live execution was used.
