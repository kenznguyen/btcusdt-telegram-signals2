# Forward Evidence Synthetic Fixture Readiness Review (P1.7)

Date: 2026-11-07  
Scope: documentation-only review of P1.5 and P1.6 before any generator implementation.  
Disposition: **CONDITIONALLY READY FOR A SEPARATELY APPROVED SYNTHETIC-ONLY GENERATOR AFTER THE BLOCKING SPECIFICATION GAPS BELOW ARE CLOSED. NOT READY FOR PROVIDER TESTS OR PERSISTENT CAPTURE.**

## 1. Executive result

P1.6 establishes the right boundary (synthetic-only, fixed seed/time, reproducibility descriptor, event cohorts, scale profiles, byte/throughput/restore measurements). It is not yet precise enough to implement interoperable deterministic bytes without implementer choices.

This review identifies 10 specification gaps. The amendments in §3 define deterministic choices for fixture generation and measurement. They do not implement code, approve code implementation, select a provider, authorize provider access, or change runtime policy.

## 2. Blocking gaps and dispositions

| ID | Gap in P1.6 | Required deterministic resolution |
|---|---|---|
| R1 | HMAC counter stream names a PRF but not exact input bytes, counter width/endian, output slicing or field encoding. | Use HMAC-SHA-256 keyed by the exact 32-byte seed. Message bytes: ASCII `SYNTH-EVIDENCE-PRF-V1\n` || uint16be(domain UTF-8 byte length) || domain bytes || uint16be(stream UTF-8 byte length) || stream bytes || uint64be(sequence) || uint16be(field-path byte length) || field-path bytes || uint32be(sample_index). Output is full 32-byte digest; derive more bytes by incrementing uint32be(block_index) appended to the message. Reject lengths outside uint16 and counters outside declared widths. |
| R2 | Event ID UUIDv5 input string has no escaping/canonical stream ID grammar. | Restrict synthetic stream IDs to ASCII `[A-Z0-9-]{1,64}`; UUIDv5 name is UTF-8 `stream_id + ":" + sequence20`, where sequence is exactly 20 decimal digits. Fixed namespace UUID is part of run descriptor. |
| R3 | Event class percentages alone do not ensure causal/economic validity (e.g. fill before accepted order). | Generate deterministic scenario bundles/state machines first (intent→risk→reservation→order→fill/fee→position; funding/mark; baseline; recovery). Allocate event counts by largest remainder only among optional independent observations within each bundle. Required causal events are additional; report both requested target and actual emitted count. Never create impossible state transitions merely to hit percentages. |
| R4 | Inter-stream sorting can conflict with monotonic sequence and commit order. | Generate `committed_at` nondecreasing per stream, with deterministic tie-break `committed_at_ms, stream_id, sequence20`. Sequence is authoritative within stream. `occurred_at` may be earlier/later and is never used to reorder a committed stream. Late-event vectors are isolated fault fixtures. |
| R5 | Segment stream scope and byte-cap accounting are ambiguous. | One segment contains exactly one stream ID and contiguous sequences. Byte cap counts exact stored segment bytes including framing but excluding manifest. Segment close occurs before adding an event that would exceed cap; an individual event larger than cap is a rejected fixture case. |
| R6 | Manifest pre-upload content cannot contain provider object version IDs not yet allocated. | Define two objects: signed pre-upload `segment_manifest_core` with content identity only; append-only signed `storage_receipt` after read-back binds provider/account/bucket/key/version-or-generation/retention. Never mutate the pre-upload manifest. Provider-specific receipt remains unmeasured in local fixture mode. |
| R7 | P1.5 defines event hash/signature bytes but not exact manifest canonicalization/hash/signature profile. | For synthetic local tests only, use the same JCS profile and UTF-8/no-BOM/no-trailing-newline rules over `manifest_core`; hash domain `BTCUSDT-PAPER-MANIFEST-V1\n`; signature domain `BTCUSDT-PAPER-MANIFEST-SIGNATURE-V1\n` || raw 32-byte manifest hash. Do not claim production approval. |
| R8 | Deterministic test-key derivation is not specified and private keys must not be archived. | Prefer fixed published RFC 8032 test vectors for crypto conformance. If fixture-specific signatures are required, derive a 32-byte Ed25519 seed from a separate domain-separated HMAC label in process memory only; record public-key fingerprint and derivation profile, never persist or export seed/private key. This is disposable test-only material, not a key-custody design. |
| R9 | Daily volume formula uses (S_{i,mean}) but table omits mean; Root A/B totals need explicit dimensions. | Measure per-class arithmetic mean and min/p50/p90/p95/p99/max. Report raw, compressed, manifest, checkpoint, audit, retained-version, retry/read-back and restore bytes separately per root. State whether a statistic is event-core or full transport envelope. |
| R10 | Root B synthetic replay fixture may be mistaken for proof of independent storage/process trust boundary. | Local harness may test deterministic reducer/replay semantics only. Label it `LOCAL_REPLAY_SIMULATION`; it cannot pass Root B isolation, separate-admin, WORM, provider durability or clean-room provider restore gates. |

## 3. Frozen deterministic fixture profile for a future approved generator

The following profile closes the above ambiguities for synthetic reproducibility only:

### 3.1 PRF byte contract

- Seed: exactly 32 bytes, represented in run descriptor as 64 lowercase hex characters.
- HMAC: HMAC-SHA-256; key is the seed bytes.
- Domain and field strings: UTF-8, length-prefixed as unsigned 16-bit big-endian byte lengths; reject >65,535 bytes.
- Sequence: unsigned 64-bit big-endian; fixture sequence is additionally constrained to 1..10^20−1 and serialized in event as 20-digit zero-padded decimal string.
- Sample and block counters: unsigned 32-bit big-endian, starting at zero.
- Message composition is exactly as specified in R1; no implicit separators or Unicode normalization beyond the fixed ASCII domain prefix and UTF-8 encoding.
- For requested output longer than 32 bytes, append block index and recompute HMAC; concatenate blocks and truncate to requested length.
- Known-answer test vectors MUST be committed before generator acceptance. Include at least empty field path, non-ASCII payload label (UTF-8 bytes), sequence 1, maximum supported sequence, and multi-block output.

### 3.2 Scenario/state-machine profile

- Define versioned scenario templates for Core, AI and Legacy/account-level synthetic streams.
- Every dependent event references existing event IDs and expected prior state.
- Valid baseline fixture contains only legal transitions. Fault injection creates separate derived copies with exactly one declared fault per test vector unless a multi-fault test is explicitly named.
- The class percentage table is a target mix, not a hard invariant. Report target counts, mandatory causal overhead and actual counts. Do not drop mandatory events to force exact percentages.
- UNKNOWN fee/funding/mark values are typed states with omitted amount where schema requires; never use numeric zero as a stand-in.

### 3.3 Stream and segment profile

- Each stream has its own contiguous sequence and hash chain; a segment cannot mix stream IDs.
- Within-stream commit timestamps are nondecreasing. Inter-stream order uses the R4 tuple.
- Segment byte cap includes framing and canonical event transport bytes exactly as defined by the versioned segment framing profile; manifest bytes are excluded and reported separately.
- A segment boundary is a function of the immutable policy and next event bytes. No event is truncated or split.

### 3.4 Manifest and signature profile

- `manifest_core` includes schema version, manifest ID, stream ID, contiguous sequence range, count, first/last event hash, previous manifest hash, segment byte length/digest, source schema/build/config identities, seal timestamp and signature profile ID.
- Local fixture manifest bytes are JCS(`manifest_core`) UTF-8 bytes; hash/signature domains are those in R7.
- `storage_receipt` is a separate append-only object produced only after a provider read-back. It is absent in local-only fixture output; do not fabricate version IDs or retention metadata.
- Published RFC 8032 vectors validate algorithm conformance. Fixture-specific ephemeral key material must never leave process memory or appear in artifacts.

### 3.5 Measurement statistics

For each event class/cohort and each representation (event_core, transport envelope, segment, manifest, compressed object), report:
- sample count, min, arithmetic mean, p50, p90, p95, p99, max and total bytes;
- exact quantile algorithm (nearest-rank: sorted value at rank ceil(p*n), 1-indexed) and deterministic sort tie-break;
- clean baseline and fault-vector results separately;
- raw and compressed sizes separately, with compression ratio definition;
- Root A and Root B synthetic storage projections independently, clearly labeled estimates from measured local bytes rather than provider measurements.

For timing/throughput, retain all samples, warm-up marker, environment, fixture digest and failure output. Five measured runs are a minimum exploratory sample, not a statistically strong p95 claim.

## 4. Approval and test boundary

A future explicit approval, if granted, must be scoped only to:
- a standalone generator using synthetic-only data;
- local temporary output in a disposable workspace;
- unit/property/golden-vector tests and local measurement harness;
- generated outputs that contain no real account data or reusable private keys.

It would NOT authorize:
- modifying T0/T1 production source, database, schema, workflow or runtime;
- opening persistent account DB or external artifacts;
- exchange connectivity, order generation or paper/live execution;
- cloud/provider accounts, credentials, purchase, provisioning or provider tests;
- persistent capture, retention activation, Root A/Root B deployment or risk-policy changes.

The current user message does not itself grant this separate implementation approval. Therefore no generator or benchmark is created/run by this review.

## 5. Acceptance checklist for the review

- [x] P1.6 spec gaps enumerated.
- [x] Deterministic PRF byte framing specified.
- [x] Scenario/state-machine validity separated from event-mix targets.
- [x] Stream sequencing and segment boundaries made unambiguous.
- [x] Pre-upload manifest separated from post-upload storage receipt.
- [x] Synthetic manifest hash/signature profile specified.
- [x] Test-key handling constrained to ephemeral synthetic use.
- [x] Mean and quantile calculation added to measurement profile.
- [x] Root B local replay explicitly excluded from provider-independence evidence.
- [ ] P1.6 spec amended and reviewed against this document.
- [ ] Separate user approval for generator implementation.

## 6. Status

- P1.7 review: DOCUMENTED.
- P1.6 specification readiness: CONDITIONALLY READY; amendment/read-back required.
- Generator: NOT IMPLEMENTED / NOT AUTHORIZED.
- Synthetic benchmark: NOT RUN.
- Provider qualification: NOT AUTHORIZED / NOT RUN.
- Source/schema/workflow/database/runtime: UNCHANGED.
- CI: NOT RUN (documentation-only).
- Historical Dual Reconstruction: UNAVAILABLE / BLOCKED; Option A unchanged.
- T0: PAUSED; PAPER-only; `ai_execution_enabled=false`.

Next step: amend P1.6 specification and acceptance plan with the deterministic profile; then request explicit approval for a local synthetic-only generator. No broader implementation or provider action is implied.
