# D07.9 V1 synthetic validator

This package validates the TARDIS_COLLECTOR_LINEAGE_V1 sidecar against a supplied
D07.8 manifest envelope. It is an offline, synthetic-only contract validator.

## Run

```sh
python -m pip install -r d07_9_lineage/requirements.txt
python -m json.tool d07_9_lineage/schema.v1.json >/dev/null
python -m unittest d07_9_lineage.test_validator -v
```

## API

```python
from d07_9_lineage.validator import validate_lineage_record

result = validate_lineage_record(record, d07_8_manifest)
```

The D07.8 envelope supplied to the function must include `packageId` and
`files[].path`. The optional `seen_record_ids` iterable can be used by a
caller maintaining a record registry to reject duplicate record IDs.

## Status boundary

- `BLOCKED`: invalid schema/type/path/relationship, secret-like content,
  known shared material dependency, or explicit blocked review.
- `NOT_VERIFIED`: incomplete dependency inventory, unresolved dependencies,
  or no accepted review disposition.
- A sidecar may declare `SUPPORTED_WITHIN_BOUNDARY`, but this validator only
  records that declaration in `declaredReviewDisposition`. Because it does not
  resolve evidence references, the returned `status` and
  `collectorIndependence` remain `NOT_VERIFIED`. A separate evidence-review
  gate is required before any collector-path claim can be promoted.

The validator never opens `*Ref` values, accesses a provider, reads preserved
raw bytes, recomputes hashes, or writes to a ledger/database. Consequently
`evidenceReferenceResolution`, `byteIntegrity`, `collectorIndependence`,
`issuerAuthenticity`, `observationCorroboration`,
`enumerationCompleteness`, `freshness`, `globalCompleteness` and
`factualTruth` remain `NOT_VERIFIED` in every result. Binance remains the
common issuer, so `issuerIndependence` is always
`NOT_AVAILABLE_SAME_ISSUER`.

All CI fixtures are synthetic. No Tardis endpoint, credential, D07.2/D07.8
verifier, ledger, T0 or VPS is used.
