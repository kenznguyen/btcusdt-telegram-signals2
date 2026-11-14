# D07.9 V2 Contract Proposal — Explicit Unknowns and Evidence-Bounded Claims

Date: 2026-11-14
Status: DESIGN PROPOSAL — NOT IMPLEMENTED
Scope: Additive schema evolution; preserve V1 unchanged.

## 1. Decision

Do not weaken `TARDIS_COLLECTOR_LINEAGE_V1` or manufacture values to satisfy it. Introduce a separately versioned V2 contract that can represent incomplete provenance without treating missing facts as valid evidence.

V2 is a provenance assertion record, not an attestation that a named provider or collector actually produced the bytes. A structurally valid V2 record may legitimately result in an overall `NOT_VERIFIED` disposition.

V1 remains available for existing records and tests. No V1 record is silently upgraded or reinterpreted.

## 2. Core data model

Every material provenance claim is represented as an assertion with:
- `status`: `KNOWN`, `UNKNOWN`, `UNAVAILABLE`, or `NOT_APPLICABLE`.
- `value`: required and non-null only when status is `KNOWN`; otherwise null.
- `basis`: `OWNER_REPORTED`, `LOCAL_OBSERVATION`, `CRYPTOGRAPHIC_CHECK`, `PROVIDER_ATTESTATION`, or `INDEPENDENT_ATTESTATION`.
- `evidenceRefs`: zero or more opaque references. References identify evidence objects; they do not themselves prove the claim.
- `limitation`: required for `UNKNOWN` and `UNAVAILABLE`; null for `KNOWN` unless a bounded qualification is needed.

A claim with basis `OWNER_REPORTED` must never be promoted to provider-attested or independently verified by schema validation. Schema validation checks representation, not truth.

## 3. Required record sections

- `schemaVersion`: constant `SOURCE_LINEAGE_RECORD_V2`.
- `recordId`, `packageId`, `createdAt`.
- `subject`: raw package file path, byte length, SHA-256 and preservation/readback assertions.
- `retrieval`: immediate retrieval channel, actor assertion, retrieval time assertion, and upstream-origin assertion. The immediate channel and original upstream source are separate claims.
- `provider`: provider identity, dataset, feed, venue and export/request identifiers as assertions. No provider name is required to be KNOWN.
- `collector`: collector identity, software, execution, host, start/end time, transport and network-egress as assertions.
- `custody`: zero or more evidenced custody events. Empty events are valid structurally but force custody coverage to `NOT_VERIFIED`; never synthesize an event solely to satisfy minimum cardinality.
- `dependencies`: known/unknown dependencies with explicit materiality assertions and reasons.
- `assessment`: declared boundary, unresolved claims, review disposition and reviewer evidence.
- `supersedes`: explicit nullable predecessor reference and reason.

## 4. Status derivation (fail closed)

Structural validity is separate from provenance disposition:
- `STRUCTURE_VALID`: V2 document conforms to its JSON Schema.
- `NOT_VERIFIED`: any material source, collector, acquisition, custody, issuer, completeness or evidence-index claim is UNKNOWN/UNAVAILABLE, or referenced evidence has not been independently resolved.
- `BLOCKED`: contradictory declarations, malformed values, unsafe paths, digest mismatch, invalid chronology, or an explicitly known disqualifying shared material dependency.
- `SUPPORTED_WITHIN_BOUNDARY`: may be emitted only by a separate assessment layer after required evidence references are resolved and the declared boundary is explicit. It is not equivalent to global truth or completeness.
- No schema-only path may produce collector-independence PASS, issuer-authenticity PASS, or completeness PASS.

Missing evidence is not automatically a structural error. Contradictory or malformed evidence remains a structural/semantic error.

## 5. Mapping of currently available BTCUSDT evidence

| Claim | V2 representation |
|---|---|
| Immediate retrieval channel | KNOWN / `CHATGPT` / OWNER_REPORTED |
| Owner says no other source was used | KNOWN / owner statement / OWNER_REPORTED |
| Original upstream source before ChatGPT | UNKNOWN |
| Direct Tardis export | UNKNOWN |
| Tardis provider receipt / request / job | UNAVAILABLE — not supplied |
| Collector identity and execution | UNKNOWN |
| Pre-ChatGPT custody events | UNKNOWN; no events asserted |
| D07.8 raw file byte length and SHA-256 | KNOWN / CRYPTOGRAPHIC_CHECK, bounded to existing package readback evidence |
| Equality of ChatGPT-retrieved bytes to D07.8 v4 raw object | KNOWN / CRYPTOGRAPHIC_CHECK |
| Binance issuer authenticity | UNKNOWN |
| Authoritative expected funding set / completeness | UNKNOWN |

The intended Tardis pilot context must be retained only as historical context, not as an authenticated provider assertion.

## 6. V2 validation requirements

1. JSON Schema rejects unknown properties and invalid enum/status/value combinations.
2. A KNOWN claim requires a value and a non-empty basis. An UNKNOWN/UNAVAILABLE claim requires null value and a non-empty limitation.
3. OWNER_REPORTED is an assertion provenance, never an evidence-resolution result.
4. Empty custody events are allowed but custody coverage derives to NOT_VERIFIED.
5. Chronology checks apply only when the relevant timestamps are KNOWN; never invent dates to satisfy ordering.
6. Raw-file byte length and SHA-256 must be lowercase/positive and can be compared to the D07.8 manifest/readback by a separate validator.
7. Provider identity, collector identity, request IDs, host, transport and egress can remain UNKNOWN without making the JSON structurally invalid.
8. Any evidence reference must resolve through the existing D07.11 safe-path/readback boundary before it can support a verified claim.
9. The evidence reference index's own origin/authority/immutability remains a separate trust limitation.
10. No V2 validation result can authorize Paper Ledger bootstrap, Runner/One-shot, T0 writes or execution.

## 7. Required TDD matrix before implementation

- Minimal structurally valid record with unknown upstream source and zero custody events => schema valid; provenance NOT_VERIFIED.
- Owner-reported ChatGPT channel does not promote upstream source or provider identity.
- UNKNOWN/UNAVAILABLE with null value and reason accepted.
- UNKNOWN/UNAVAILABLE without reason rejected.
- KNOWN with null value rejected.
- KNOWN with missing basis rejected.
- OWNER_REPORTED claim cannot be emitted as PROVIDER_ATTESTATION by derivation.
- Empty custody events => custody NOT_VERIFIED, not synthetic event.
- Known chronology reversed => BLOCKED.
- Unknown timestamps do not trigger fabricated chronology comparisons.
- Raw SHA mismatch against D07.8 manifest => BLOCKED.
- Raw SHA exact match => byte integrity PASS only within package boundary.
- Unsafe reference path / symlink / missing target => BLOCKED or NOT_VERIFIED according to existing D07.11 semantics.
- Missing evidence index authority => independence remains NOT_VERIFIED.
- V1 fixtures and validator behavior remain unchanged.

## 8. Migration and compatibility

- Keep `schema.v1.json`, V1 validator, fixtures and historical CI unchanged.
- Add `schema.v2.json`, V2 validator and separate V2 tests/workflow.
- Do not rewrite the provisional V1 draft as if it had passed V1. Preserve it as historical evidence of the failed fit between current facts and V1 constraints.
- V2 record must be stored in a clearly named `drafts/` location until its schema, validator and tests pass.
- The first V2 record may record the current ChatGPT retrieval facts, but must be labeled owner-reported and structurally valid only; its provenance disposition remains NOT_VERIFIED.

## 9. Non-goals and safety boundary

No new acquisition, network request, Tardis login/export, VPS access, T0 read/write, package mutation, raw-data transfer, evidence-index construction, D07.11 real-data resolution, ledger import, Runner/One-shot, credentials, live execution or order placement. No data deletion.

## 10. Approval gate

This document is a proposed contract only. Implementation is a separate increment after owner review/approval of the V2 field contract and status semantics. No code, schema, validator, tests, CI or existing V1 record has been changed in this design step.
