# D07.1 — Independent Expected Funding Population Provenance Contract

Date: 2026-11-14  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Design baseline HEAD: `9cf1510ad21c73a23c2964f230a650b953e76481`  
Disposition: **DESIGN CONTRACT ONLY — no source integration, real evidence ingestion or runtime behavior change**

## 1. Purpose and boundary

D07 compares an expected funding-event population with events observed by the paper ledger. D07 currently proves only `COMPLETE_WITHIN_DECLARED_POPULATION`; caller-supplied identifiers and labels do not establish actual independence, issuer identity, global completeness, freshness or factual truth.

D07.1 defines the evidence required before a future implementation may describe an expected population as independently enumerated and may verify that the exact source evidence bytes were read back. This document is source-neutral: it does not select an exchange, bank, provider, API, file format, authentication method or trust technology.

This is a documentation/design increment. It does not implement a source adapter, network client, parser, signature verifier, bootstrap path or database migration. It does not authorize access to real accounts, external services, credentials, production databases or VPS.

## 2. Claims must remain separate

A future evidence record MUST represent these dimensions independently; success in one dimension MUST NOT promote another:

| Dimension | Meaning | Default until separately evidenced |
|---|---|---|
| Source identity | Stable identity of the system/provider that emitted the record | `NOT_VERIFIED` |
| Issuer authenticity | Evidence that the bytes were issued by the claimed source | `NOT_VERIFIED` |
| Source-byte integrity | Exact captured bytes match the declared digest | `NOT_VERIFIED` |
| Readback | Verifier independently re-reads the captured bytes and recomputes the digest | `NOT_VERIFIED` |
| Enumeration completeness | All pages/records in the declared query scope were enumerated | `NOT_VERIFIED` |
| Independence | Expected enumeration is independent of the ledger-observed population and its upstream lineage | `NOT_VERIFIED` |
| Freshness | Evidence is recent enough for a separately defined cutoff/age policy | `NOT_VERIFIED` |
| Factual truth | Source statements correspond to the real-world account/events | `NOT_VERIFIED` |

SHA-256 proves byte equality only when the bytes are available for recomputation. A digest alone does not prove source identity, issuer authenticity, completeness, independence, freshness or truth. A successful readback is not an authenticity check.

## 3. Required provenance envelope

A future versioned envelope MUST bind the following fields to one immutable evidence snapshot:

### 3.1 Source and authority declaration

- `contractVersion` and a unique `evidenceSnapshotId`.
- Stable `sourceId`, human-readable source name, source type and claimed issuer.
- The precise source interface or document class used (for example, an API report or statement export), without embedding credentials or secret-bearing URLs.
- Declared basis for believing the source is authoritative for the account and funding-event domain.
- Acquisition actor/process identity and acquisition method.
- Explicit declaration of whether the source shares an upstream producer, database, export job, cache, credentials/control plane or transformation pipeline with the observed ledger data.

These are declarations until supported by evidence. Names, labels, separate IDs and separate files alone MUST NOT qualify as independence or issuer authentication.

### 3.2 Query and population scope

- Account reference in a non-secret, privacy-minimized form; never API keys, access tokens, passwords or private signing material.
- Symbol/instrument and quote/settlement currency.
- Exact half-open event-time interval `[startAtMs, endAtMs)`, timezone/clock basis and timestamp semantics.
- Query filters, event types, status filters and any exclusions.
- Source-side snapshot/as-of time, retrieval time and declared event cutoff.
- Expected record count or source-reported totals when available, with the exact meaning and scope of each count.
- Stable snapshot/cursor identifiers needed to reproduce or audit the enumeration.

A query that cannot be bounded to the same interval, currency and event definition as D07 MUST NOT be reconciled as equivalent.

### 3.3 Exact source bytes and readback

- Exact raw evidence bytes captured before parsing, with media type, byte length and SHA-256 over those exact bytes.
- A durable, immutable evidence locator or content-addressed reference, with access control handled outside the manifest.
- Capture timestamp and a record of how the bytes were obtained.
- Parser name/version and exact parser source revision/digest used to derive normalized events.
- A readback record identifying the verifier, readback time, exact byte length and recomputed SHA-256.

The verifier MUST read the referenced bytes independently of the parser's in-memory input and compare the recomputed digest and byte length with the envelope. If bytes are missing, inaccessible, mutable without version identity, truncated or digest-mismatched, readback MUST fail closed. A digest copied from the acquisition process without re-reading bytes is not readback evidence.

### 3.4 Enumeration and pagination evidence

For paginated or cursor-based sources, preserve an ordered page manifest containing, at minimum:

- page ordinal and page/cursor identity;
- request scope or a secret-redacted canonical request fingerprint;
- response byte digest and byte length for each page;
- next-cursor/continuation state;
- whether the page is terminal according to the source protocol;
- per-page record count and any source-reported total.

The enumeration record MUST show a valid terminal condition, no missing cursor transition, no repeated page/cursor, no unexplained overlap or gap, and consistency between page totals and normalized population totals where the source provides such totals. If the source offers no verifiable terminal condition or the pagination protocol cannot be reconstructed, completeness remains `NOT_VERIFIED`; a successful HTTP response or a locally reached page limit is not proof of completion.

For non-paginated exports, preserve the source's documented export-completion indicator or equivalent evidence and bind it to the exact export bytes.

## 4. Independence assessment

Independence is a lineage/control assessment, not a string comparison. A future reviewer MUST document:

1. Which system generated the expected population.
2. Which system generated the ledger-observed population.
3. Their upstream data providers and transformation paths.
4. Shared infrastructure, credentials, operators, caches, storage, jobs and control planes that could create common-mode omission or corruption.
5. Why the expected enumeration could detect an omission in the observed path rather than merely repeat the same omitted data.
6. Evidence supporting the assessment and the limits of that evidence.

If both populations derive from the same source extract, shared database, copied manifest, common transformation output or otherwise non-independent lineage, the result MUST remain `DECLARED_NOT_VERIFIED` (or a more restrictive blocked state). Different labels, IDs, timestamps or custodians do not change this.

A reviewer may classify independence only within the precise declared interval, account scope, event types and source versions. No global or future-period inference is allowed.

## 5. Fail-closed acceptance rules

A future implementation MUST block an independent-completeness claim if any of the following applies:

- required provenance fields are absent, ambiguous, unknown or contradictory;
- the exact source bytes cannot be independently read back;
- byte length or SHA-256 differs;
- query scope, interval, currency, timestamp semantics or event filters do not match the D07 comparison contract;
- pagination/continuation evidence is incomplete, repeated, inconsistent or lacks a verifiable terminal condition;
- source-reported totals disagree with enumerated totals without an explained and evidenced rule;
- expected and observed populations share a lineage that prevents the expected population from independently detecting omissions;
- source identity/authority or issuer-authenticity evidence is being inferred from a digest, URL, label or caller declaration;
- records are missing, unexpected, duplicated or content-mismatched under D07;
- evidence is stale relative to a separately approved freshness policy;
- the source evidence or parser revision cannot be reproduced/audited.

The implementation MUST preserve separate statuses and reason codes for source-byte integrity, readback, enumeration completeness, independence, issuer authenticity and D07 event reconciliation. It MUST NOT collapse them into a single `verified=true` flag.

## 6. Required output semantics

Until a future exact source profile and verification procedure are separately approved:

- D07 result remains `COMPLETE_WITHIN_DECLARED_POPULATION` only.
- `sourceIdentity=NOT_VERIFIED`.
- `issuerAuthenticity=NOT_VERIFIED`.
- `sourceByteIntegrity=NOT_VERIFIED`.
- `sourceByteReadback=NOT_VERIFIED`.
- `enumerationCompleteness=NOT_VERIFIED`.
- `independence=DECLARED_NOT_VERIFIED`.
- `freshness=NOT_VERIFIED`.
- `factualTruth=NOT_VERIFIED`.
- `globalCompleteness=NOT_VERIFIED`.

A future successful readback may change only the source-byte integrity/readback dimensions that it actually proves. It MUST NOT automatically promote issuer authenticity, independence, freshness, factual truth or global completeness.

## 7. Minimum future test matrix

Before any adapter or runtime integration is proposed, tests should cover:

- exact-byte digest and byte-length match;
- missing, inaccessible, truncated, replaced and digest-mismatched evidence bytes;
- parser revision mismatch and deterministic normalized population output;
- wrong interval, currency, timezone/timestamp semantics and query filters;
- complete pagination, missing page, repeated cursor, cursor loop, premature terminal marker and inconsistent totals;
- duplicate/overlapping pages and unexplained gaps;
- shared upstream lineage and false independence declarations;
- source identity/issuer claims without supporting evidence;
- stale snapshots and future-dated timestamps;
- D07 missing/unexpected/duplicate/content mismatch outcomes;
- preservation of each independent status dimension and fail-closed result.

Tests must use synthetic bytes and temporary storage. No production credentials, real account statements, live provider calls or VPS access are part of this matrix.

## 8. Approval gates and explicit non-authorization

This contract does not choose or approve a real source. A later source-specific proposal must name the provider/source, exact account and event scope, access method, evidence custody/readback location, privacy handling, issuer-authenticity claim, independence rationale, freshness policy, parser/versioning plan, test fixtures and rollback/recovery boundary. That proposal requires separate owner approval before connection or real-data access.

No signature scheme, key generation/import/custody, DSSE/Ed25519 verifier, KMS/HSM, credential workflow, production bootstrap, non-empty historical funding import, database migration or runtime execution is authorized here.

## 9. D07.1 disposition

- Source-neutral provenance contract: **DOCUMENTED**.
- Source-specific provider selection: **NOT APPROVED / NOT SELECTED**.
- External source-byte acquisition/readback: **NOT IMPLEMENTED / NOT RUN**.
- Actual independence, issuer authenticity, completeness, freshness and factual truth: **NOT VERIFIED**.
- Production bootstrap: **BLOCKED / NOT APPROVED**.
- Runtime/code behavior: **UNCHANGED**.
