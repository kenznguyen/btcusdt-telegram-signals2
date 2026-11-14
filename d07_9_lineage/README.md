# D07.9 V1 synthetic validator and D07.11 resolver

This package validates the TARDIS_COLLECTOR_LINEAGE_V1 sidecar against a
D07.8 manifest envelope. D07.9 validates structure and declared relationships.
D07.11 separately resolves evidence references and independently reads the
preserved raw files. Both gates are offline and synthetic-only in CI.

## Run

```sh
python -m pip install -r d07_9_lineage/requirements.txt
python -m json.tool d07_9_lineage/schema.v1.json >/dev/null
python -m unittest discover -s d07_9_lineage -p 'test_*.py' -v
```

## D07.9 structural API

```python
from d07_9_lineage.validator import validate_lineage_record

result = validate_lineage_record(record, d07_8_manifest)
```

The D07.8 envelope supplied to the function must include packageId and
files[].path. The optional seen_record_ids iterable can be used by a caller
maintaining a record registry to reject duplicate record IDs.

## D07.11 evidence resolution and byte readback

```python
from d07_9_lineage.evidence_resolver import resolve_lineage_record

result = resolve_lineage_record(
    record=lineage_sidecar,
    d07_8_package=d07_8_manifest,
    evidence_root=preserved_evidence_root,
    reference_index=reviewed_reference_index,
)
```

The resolver:
- Collects non-null sidecar fields ending in Ref or Reference and requires an
  exact entry for each in the supplied reference index.
- Resolves only safe relative paths below the configured evidence root.
  Absolute paths, traversal/empty segments, Windows drive paths and symlinks
  are rejected. Readback uses a separate Python process and no-follow
  directory/file descriptors to avoid symlink traversal races.
- Requires the D07.8 manifest files[] entries themselves to contain the exact
  raw path, byteLength and lowercase SHA-256. It does not accept a separate
  caller-supplied hash map as a substitute for the manifest.
- Requires the sidecar rawFiles and custody.readbackFiles path sets to equal
  the complete D07.8 raw/ path set. Receipt and independent-readback
  declarations must match the manifest.
- Reopens each reference target and raw file in the readback subprocess,
  recomputes byte length and SHA-256, then compares the result with the
  reference index or D07.8 manifest respectively.
- Returns PASS only for evidence-reference resolution and raw-byte equality.
  Missing targets/metadata return NOT_VERIFIED; unsafe paths, invalid
  declarations and digest/length mismatches return BLOCKED.

The reference index is an offline mapping from each opaque reference string to
a relative path, byteLength and sha256. Its own origin, authority and
immutability are not authenticated by this resolver. A PASS does not prove
that a reference is factually true, that the cited evidence supports the
sidecar claim, or that the evidence is independently controlled.

## Status boundary

- BLOCKED: invalid schema/type/path/relationship, unsafe reference path,
  conflicting declaration, malformed manifest metadata, known shared
  material dependency, or explicit blocked review.
- NOT_VERIFIED: missing/unavailable reference target, incomplete manifest
  metadata, unresolved dependency, or no accepted review disposition.
- D07.11 PASS means only that indexed evidence files were opened and their
  hashes/lengths matched declarations, and that preserved raw bytes matched
  D07.8 manifest entries. It does not issue collector independence PASS.
- collectorIndependence, issuer authenticity, observation corroboration,
  freshness, enumeration/global completeness and factual truth remain
  NOT_VERIFIED. Binance remains the common issuer, so issuerIndependence is
  NOT_AVAILABLE_SAME_ISSUER.

All CI fixtures are synthetic. No Tardis endpoint, credential, D07.2 verifier,
real D07.8 package, ledger, T0 or VPS is used. No database or ledger writes
are performed.


## D07.9 V2 explicit-unknown contract

V2 is additive and does not change the V1 schema or validator. Its JSON Schema
is `schema.v2.json`; its separate structural/semantic validator is
`validator_v2.py`; its synthetic tests are `test_validator_v2.py`.

Each provenance claim uses:
- `status`: `KNOWN`, `UNKNOWN`, `UNAVAILABLE`, or `NOT_APPLICABLE`.
- `value`: non-null only for `KNOWN`; null for the other statuses.
- `basis`: owner-reported, local observation, cryptographic check, provider
  attestation, or independent attestation.
- `limitation`: required for UNKNOWN/UNAVAILABLE/NOT_APPLICABLE.
- `evidenceRefs`: references only; they are not authenticated by schema
  validation.

A V2 document may be `STRUCTURE_VALID` while its provenance disposition is
`NOT_VERIFIED`. Empty custody event arrays are structurally valid and always
leave custody coverage NOT_VERIFIED. OWNER_REPORTED claims are never promoted
to provider or independent attestation by this validator.

When supplied a D07.8 manifest, V2 compares the subject path, byte length and
SHA-256 against the matching manifest entry. A match yields only
`byteIntegrity=PASS_WITHIN_PACKAGE_BOUNDARY`; it does not prove upstream
origin, provider authenticity, collector identity/independence, custody,
global completeness or factual truth. Evidence references and the reference
index still require the separately bounded D07.11 resolver and trust review.

Run V1 regression and V2 tests together:

```sh
python -m pip install -r d07_9_lineage/requirements.txt
python -m unittest d07_9_lineage.test_validator d07_9_lineage.test_validator_v2 -v
```

The dedicated GitHub Actions workflow is
`.github/workflows/d07-9-v2-explicit-unknown.yml`. CI fixtures are synthetic;
no real package, network, VPS, T0, ledger or execution system is accessed.
