# D07.9 — Collector Lineage Evidence Record Contract

Date: 2026-11-14  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Status: **CONTRACT DESIGN ONLY — NO REAL TARDIS EVIDENCE ACQUIRED OR VERIFIED**

## 1. Purpose and compatibility boundary

This record carries the collector-path, acquisition, custody, transformation and dependency evidence required by D07.9. It is a separate, immutable sidecar linked to one D07.8 evidence package by the exact `packageId`.

It does **not** extend, replace, reinterpret or require changes to the D07.8 manifest schema or its validator. D07.8 remains responsible for its existing package, issuer/collector labels, instrument, time, coverage and file inventory contract. The D07.9 record supplies additional provenance evidence without making the D07.8 validator authoritative for it.

One D07.9 record describes one acquisition/custody lineage for one D07.8 package. If acquisition or custody facts materially change, create a new record ID and preserve the prior record; do not overwrite history. A corrected record must include `supersedesRecordId` and a reason.

## 2. Normative envelope

The record is UTF-8 JSON. The schema version is the literal `TARDIS_COLLECTOR_LINEAGE_V1`. All fields below are required unless explicitly marked nullable/optional. Unknown fields are rejected in V1. Timestamps are UTC RFC 3339 strings with an explicit `Z` or numeric offset; preserve source-native timestamps separately rather than converting away the original value.

```json
{
  "schemaVersion": "TARDIS_COLLECTOR_LINEAGE_V1",
  "recordId": "immutable-unique-id",
  "packageId": "exact-D07.8-package-id",
  "createdAt": "2026-11-14T10:00:00Z",
  "custodian": {
    "actorRef": "non-secret-owner-or-service-reference",
    "role": "OWNER|OPERATOR|SERVICE",
    "organizationRef": "non-secret-organization-reference"
  },
  "provider": {
    "name": "TARDIS",
    "dataset": "exact-provider-dataset",
    "feed": "exact-provider-feed-or-channel",
    "venue": "BINANCE",
    "sourceReference": "documentation-revision-or-reference"
  },
  "acquisition": {
    "method": "PROVIDER_EXPORT|PROVIDER_API|OWNER_SUPPLIED_FILE",
    "actorRef": "non-secret-actor-reference",
    "process": "process-name-and-version",
    "hostEnvironmentRef": "non-secret-host-environment-reference",
    "startedAt": "2026-11-14T09:00:00Z",
    "completedAt": "2026-11-14T09:05:00Z",
    "transport": "HTTPS_DOWNLOAD|PROVIDER_API|LOCAL_TRANSFER",
    "channel": "documented-channel-name",
    "providerPeriod": {
      "start": "provider-native-start",
      "end": "provider-native-end",
      "semantics": "provider-documented-interval-semantics",
      "timezone": "UTC"
    },
    "requestReference": "non-secret-request-or-job-reference",
    "requestReferenceUnavailableReason": null,
    "networkEgressRef": "non-secret-egress-policy-reference",
    "networkEgressUnavailableReason": null
  },
  "rawFiles": [
    {
      "d07_8Path": "exact-relative-path-from-D07.8-files",
      "mediaType": "text/csv",
      "byteLengthAtReceipt": 1234,
      "sha256AtReceipt": "64-lowercase-hex",
      "preservedOriginal": true
    }
  ],
  "custody": {
    "receiptAt": "2026-11-14T09:05:00Z",
    "receiptActorRef": "non-secret-actor-reference",
    "storageRef": "non-secret-storage-location-reference",
    "accessControlRef": "non-secret-access-policy-reference",
    "readbackAt": "2026-11-14T09:06:00Z",
    "readbackStartedAt": "2026-11-14T09:05:30Z",
    "readbackActorRef": "non-secret-actor-reference",
    "readbackProcess": "independent-readback-process-and-version",
    "readbackRunRef": "unique-readback-execution-reference",
    "readbackEnvironmentRef": "non-secret-readback-environment-reference",
    "readbackStorageRef": "preserved-copy-storage-reference",
    "readbackEvidenceRef": "immutable-readback-log-or-attestation-reference",
    "readbackFiles": [
      {
        "d07_8Path": "exact-relative-path-from-D07.8-files",
        "byteLength": 1234,
        "sha256": "64-lowercase-hex",
        "method": "INDEPENDENT_READBACK"
      }
    ],
    "custodyEvents": [
      {
        "eventId": "unique-event-id",
        "eventType": "RECEIVED|COPIED|READ_BACK|TRANSFERRED|SEALED",
        "at": "2026-11-14T09:05:00Z",
        "actorRef": "non-secret-actor-reference",
        "fromStorageRef": null,
        "toStorageRef": "non-secret-storage-location-reference",
        "evidenceRef": "immutable-log-or-attestation-reference"
      }
    ]
  },
  "transformation": {
    "performed": false,
    "parserSourceSha": null,
    "configurationFingerprint": null,
    "executedAt": null,
    "fieldMappingRef": null,
    "normalizedOutputFiles": []
  },
  "dependencies": [
    {
      "dependencyId": "dependency-id",
      "category": "ISSUER|COLLECTOR|STORAGE|CONTROL_PLANE|NETWORK|TRANSFORMATION|TIME_AUTHORITY",
      "systemRef": "non-secret-system-reference",
      "relationship": "description-of-dependency",
      "sharedWithBinanceRestCapture": "YES|NO|UNKNOWN",
      "materialToCollectorSeparation": "YES|NO|UNKNOWN",
      "evidenceRef": "evidence-reference-or-explicit-unknown",
      "unknownReason": null
    }
  ],
  "assessment": {
    "declaredBoundary": "precise scope of collector-path comparison",
    "unknowns": ["explicit unresolved dependency"],
    "reviewDisposition": "NOT_REVIEWED|BLOCKED|NOT_VERIFIED|SUPPORTED_WITHIN_BOUNDARY",
    "reviewerRef": null,
    "reviewedAt": null,
    "rationaleRef": null
  },
  "supersedesRecordId": null,
  "supersessionReason": null
}
```

The JSON above is illustrative. Values are not evidence merely because they are present. Every `*Ref` must resolve to retained, reviewable evidence or be explicitly marked unknown under the rules below.

## 3. Field and validation rules

### 3.1 Identity and package binding

- `recordId` is unique and immutable.
- `packageId` must exactly equal one D07.8 package's `packageId`; no fuzzy matching or filename-derived binding.
- Each `rawFiles[].d07_8Path` must map one-to-one to a D07.8 `files[].path`. Duplicate paths, unbound files or implicit path rewriting are invalid.
- `provider.name` must be `TARDIS` for this contract; `provider.venue` must be `BINANCE`. This describes the candidate collector and issuer claim, not authenticated identity.
- No passwords, API keys, access tokens, cookies, private URLs containing credentials, personal data or secret material may be stored. Use opaque references to approved secret managers/logs without exposing secret values.

### 3.2 Acquisition and time

- `startedAt` must be less than or equal to `completedAt`; `createdAt` cannot precede the recorded acquisition completion unless the record explicitly documents a later correction using a supersession record.
- Provider-native period strings and semantics must be preserved exactly as documented. A normalized UTC interval does not replace source-native interval meaning.
- `requestReference`, process, host/environment and network-egress references must be independently resolvable; self-asserted labels alone do not prove separate collection paths.
- The acquisition method/transport/channel must be consistent with the cited provider evidence. Contradictions block assessment.

### 3.3 Raw-byte custody

- Every D07.8 file included in the lineage record has exact byte length and SHA-256 measured at receipt.
- `preservedOriginal` must be true for raw source bytes. Derived/normalized files belong in `transformation.normalizedOutputFiles`, never in place of raw files.
- Readback entries must match the same D07.8 paths and recompute the exact byte length and SHA-256 from bytes read from the preserved copy.
- The readback method must not merely reuse the manifest's declared digest. Missing bytes, missing readback, duplicate paths, length mismatch or digest mismatch blocks custody integrity.
- Custody events are append-only, uniquely identified and chronologically ordered. A copy/transfer event records both source and destination references. Missing actor/time/evidence references remain unresolved; they are not inferred.

### 3.4 Transformation provenance

- If `performed=false`, parser/configuration/execution/field-mapping values must be null and normalized output list empty.
- If `performed=true`, parser source SHA, configuration fingerprint, execution time, field mapping reference and at least one normalized output descriptor are required.
- Raw bytes remain unchanged. A parser must not overwrite raw files.
- A parser or configuration change creates a new derived output and lineage record or a clearly versioned superseding record; it never silently rewrites prior provenance.

### 3.5 Dependency inventory and independence

- Inventory all known issuer, collector, storage, control-plane, network, transformation and time-authority dependencies relevant to the declared comparison.
- `sharedWithBinanceRestCapture` is tri-state: YES, NO or UNKNOWN. UNKNOWN is fail-closed and prevents a positive collector-separation disposition.
- A YES for a dependency that is material to collection/custody/control separation blocks a claim of separate collector path. A shared Binance issuer is expected and must be recorded as a common issuer; it prevents independent-issuer claims but does not by itself mean the collector processes are the same.
- Empty dependency arrays, omitted systems, distinct names, distinct files or distinct host labels do not prove independence.
- A positive disposition is allowed only after a reviewer evaluates referenced evidence and states the precise boundary. It means only separate collector path relative to the identified Binance REST capture, not independent issuer truth or global completeness.

### 3.6 Review status

- Initial status is `NOT_REVIEWED`.
- `BLOCKED` means known evidence or dependency conflicts prevent the claimed separation/custody condition.
- `NOT_VERIFIED` means required evidence is absent, unknown or not independently reviewable.
- `SUPPORTED_WITHIN_BOUNDARY` is permitted only with non-null reviewer, review time, rationale reference, no unresolved material dependency, and evidence references for each required area.
- This field does not alter D07.2 or D07.7 result fields and cannot promote issuer authenticity, observation corroboration, freshness, enumeration/global completeness or factual truth.

## 4. Status derivation (not owner attestation)

A future validator may report independent dimensions; it must not accept a caller-supplied aggregate PASS. At minimum:

| Dimension | Minimum condition | Otherwise |
|---|---|---|
| Record structure | Exact V1 schema and valid types/relationships | BLOCKED |
| D07.8 binding | Exact package ID and one-to-one raw-file path binding | BLOCKED |
| Receipt byte evidence | Valid receipt length/hash declarations | NOT_VERIFIED until exact bytes are checked |
| Byte custody/readback | Exact preserved bytes independently read and recomputed hashes/lengths match | BLOCKED or NOT_VERIFIED |
| Collector-path evidence | Complete dependency inventory, reviewable actor/process/control/storage evidence, no unresolved material shared path | NOT_VERIFIED or BLOCKED |
| Issuer independence | Binance REST and Tardis Binance observations | NOT_AVAILABLE_SAME_ISSUER |
| Completeness/freshness/authenticity/truth | Separate authoritative evidence for each claim | NOT_VERIFIED unless separately established |

A structurally valid record is never equivalent to byte-integrity PASS or collector-independence PASS. D07.7 remains the sole comparator contract for exact settlement observation corroboration.

## 5. Negative and adversarial contract cases

Any future implementation must reject or fail closed for at least these cases:

1. Missing or unknown `schemaVersion`; unsupported V1 extra fields.
2. Duplicate `recordId`; empty `packageId`; package ID not present in D07.8.
3. D07.8 path missing, duplicated, traversal-like, or not one-to-one with raw file entries.
4. Two differently named collector IDs resolving to the same process, operator, storage, control plane or acquisition job.
5. Empty dependency list used to claim independence; any material dependency marked UNKNOWN.
6. Shared collector/control/storage dependency marked YES but assessment claims `SUPPORTED_WITHIN_BOUNDARY`.
7. Provider/venue substitution (non-Tardis collector or non-Binance issuer) under this schema.
8. Missing actor, process, host/environment, acquisition time, transport/channel or provider-period semantics.
9. Acquisition completion before start; timezone-naive or malformed timestamp; impossible event ordering.
10. Secrets or credential-bearing values included in evidence fields.
11. Missing raw file at receipt, zero/invalid length, malformed digest, duplicate path or D07.8 path mismatch.
12. Tampered/truncated preserved bytes; readback digest/length mismatch; readback digest copied from manifest without recomputation.
13. Custody event missing actor/time/evidence reference; duplicate event ID; non-chronological custody history; transfer with missing source/destination.
14. `performed=false` while parser/configuration/output fields are populated; `performed=true` while required provenance is absent.
15. Parser source/configuration changed but old normalized output is reused without provenance versioning.
16. Missing dependency inventory for shared upstream issuer, control plane, storage, network, transformation or time authority.
17. Positive review disposition with unresolved material dependencies or missing reviewer/rationale evidence.
18. Positive collector independence used to promote issuer independence, completeness, freshness, authenticity or factual truth.
19. Binance REST and Tardis observations treated as independent issuers.
20. A D07.7 overlap PASS used to conceal unmatched rows, missing expected settlements or absent population authority.

Positive controls must also prove that two distinct collector paths can be recorded without falsely asserting independent issuers, and that an unresolved dependency produces NOT_VERIFIED rather than an inferred PASS.

## 6. Versioning and lifecycle

- V1 is immutable once accepted as an evidence record; corrections create a new `recordId`.
- A superseding record identifies the prior record and gives a non-empty reason. The old record remains available and unchanged.
- Breaking field/type/meaning changes require a new schema version and a separately reviewed migration contract. Do not silently reinterpret V1.
- D07.8 package IDs and D07.9 record IDs are separate namespaces. A package may have multiple lineage records only when each represents a distinct, explicitly explained acquisition/custody lineage; ambiguity blocks assessment.
- This contract defines no retention/deletion authority. Evidence retention and deletion require a separate policy and approval.

## 7. Current disposition and limits

- D07.9 lineage record: **DESIGNED — NOT IMPLEMENTED**.
- D07.8 manifest and validator: **UNCHANGED**.
- No Tardis acquisition, API access, parser, source-specific verifier, ledger import/write, T0/VPS operation or live execution is authorized by this document.
- Real byte custody, collector independence, overlap, issuer authenticity, freshness, enumeration/global completeness and factual truth remain **NOT VERIFIED**.
- D07.2 `BLOCKED_SHARED_LINEAGE` remains unchanged; D07 remains **PARTIAL**; PAPER ledger bootstrap remains **BLOCKED / NOT APPROVED**.


## 8. V1 schema review clarifications (normative; supersedes any broader wording above)

The following clarifications close the schema-review findings without changing the D07.8 manifest or validator.

### 8.1 Exact raw-file set binding

- `rawFiles[].d07_8Path` must map to the complete set of D07.8 manifest `files[].path` entries under the package's canonical `raw/` directory. The sidecar must not omit any raw entry and must not add any path absent from that set.
- `custody.readbackFiles` must contain exactly the same path set as `rawFiles`, with no duplicates. Each readback length and recomputed digest must equal the corresponding receipt length and digest.
- D07.8 entries under `derived/`, `transforms/` and `checksums/` are not raw source inputs and must not be listed in `rawFiles`. Derived outputs remain described under `transformation.normalizedOutputFiles`. A different D07.8 raw-directory convention requires a separately versioned/reviewed rule.

### 8.2 Nullable acquisition references

- `requestReference` and `networkEgressRef` may be null only when their paired `requestReferenceUnavailableReason` or `networkEgressUnavailableReason` is non-empty. If the reference is present, its unavailable-reason field must be null.
- This supports owner-supplied/offline files without fabricating a request ID or network egress. The acquisition actor, process and host/environment remain required.
- Every non-null `*Ref` resolves to retained, access-controlled, reviewable evidence. The literal `UNKNOWN` is not a valid evidence reference. Unknown states use the explicit tri-state fields and a non-empty reason.
- `custodian.organizationRef` may be null only for an individual custodian with `role=OWNER` and an explicit reason. `assessment.reviewerRef`, `reviewedAt` and `rationaleRef` may be null only while `reviewDisposition=NOT_REVIEWED`. `supersedesRecordId` and `supersessionReason` must either both be null (original record) or both be non-empty (correction).

### 8.3 Independent readback

- Readback means a second file-open/read/hash operation against the preserved storage copy after acquisition has completed. It must run in a distinct process execution with a unique `readbackRunRef`, not reuse the acquisition process's in-memory byte buffer.
- Record `readbackStartedAt`, `readbackAt` (completion), `readbackActorRef`, `readbackProcess`, `readbackEnvironmentRef`, `readbackStorageRef` and `readbackEvidenceRef`. The readback run reference must differ from the acquisition execution reference.
- A same-host readback is permitted only when the separate process/run and reopening of the preserved copy are evidenced. This proves byte equality/readability of the preserved copy only; it does not authenticate Tardis or prove collector independence/completeness.

### 8.4 Dependency materiality and deterministic review status

Each dependency includes `materialToCollectorSeparation=YES|NO|UNKNOWN` in addition to `sharedWithBinanceRestCapture=YES|NO|UNKNOWN`:
- `YES/YES` (shared and material) => `BLOCKED` for a separate collector-path claim.
- `UNKNOWN` materiality, or shared state UNKNOWN while materiality is YES/UNKNOWN => `NOT_VERIFIED`; no positive disposition.
- `NO` materiality may be accepted only with reviewer rationale and evidence explaining why the dependency cannot create a common-mode failure within the declared boundary.
- The common Binance issuer is recorded as shared, but is non-material to the narrow collector-path separation claim; it remains disqualifying for any independent-issuer claim.
- Deterministic precedence: schema/type/path violation => `BLOCKED`; known shared material dependency => `BLOCKED`; missing evidence or unresolved material dependency => `NOT_VERIFIED`; `SUPPORTED_WITHIN_BOUNDARY` only when every required evidence area is reviewable and no material shared/unknown dependency remains.

### 8.5 Additional required negative cases

Future validation must additionally reject/fail closed for: omitted D07.8 raw file; a `derived/` file listed as raw; mismatch between receipt/readback path sets; null request/network references without reasons; populated reference plus populated unavailable reason; readback reusing the acquisition process/run or in-memory buffer; positive disposition with unknown materiality; and inconsistent nullability/supersession pairs.

These are documentation-level clarifications only. They do not implement a validator, alter D07.8, or authorize Tardis acquisition or parser work.
