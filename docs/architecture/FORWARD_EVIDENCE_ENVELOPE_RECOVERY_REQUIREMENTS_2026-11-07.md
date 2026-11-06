# Forward Evidence Envelope & Minimum Recovery Requirements (P1.5)

Date: 2026-11-07  
Scope: vendor-neutral, documentation-only contract for prospective PAPER evidence capture. This is a proposed interface and recovery policy, not an implementation or operational approval.

## 1. Decision status and boundaries

- This document defines a canonical synthetic evidence envelope, segment manifest, Root A/Root B acknowledgement contract, minimum recoverable event classes, and candidate recovery/retention objectives.
- No provider, region, account, budget, retention period, RPO/RTO target, observer-lag threshold, signature-key custody model, or production serialization library is selected.
- No source, test, schema, workflow, persistent database, runtime, storage resource, credential, or provider configuration is changed.
- Synthetic examples must contain no real account identifiers, exchange credentials, personal data, or canonical account history.
- Root A remains the append-only event journal. Root B remains an independently operated observer/reducer that consumes committed Root A envelopes and never queries mutable account database rows.
- Assurance is at most LEVEL 1 while both roots share the upstream event emitter. It is not independent exchange/economic-source verification.
- Historical Dual Reconstruction remains UNAVAILABLE / BLOCKED; Option A strict predecessor chain remains unchanged. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.

## 2. Normative language and references

The terms MUST, MUST NOT, SHOULD, SHOULD NOT and MAY describe this proposed contract.

Reference standards considered:
- RFC 8785, JSON Canonicalization Scheme (JCS): deterministic JSON representation for hashing/signing. It is an Informational RFC, not an Internet Standards Track specification.
- RFC 8032, EdDSA: specifies Ed25519/Ed448 signature variants and test vectors. It is also Informational; selecting Ed25519 below is a design proposal, not an implemented cryptographic choice.
- RFC 3339, Internet timestamps: timestamp syntax. This contract narrows it to UTC with a fixed millisecond fraction for event timestamps.

The standards provide building blocks, not a complete event protocol. Exact application domain separation, field semantics, decimal representation, stream sequencing, key lifecycle and recovery behavior are defined here and still require implementation review.

## 3. Canonical event envelope

### 3.1 Required logical structure

Each committed event consists of an immutable `event_core` and a cryptographic `integrity` block. The signature is calculated over the exact canonical bytes defined below; it is not included in the bytes it signs.

```json
{
  "event_core": {
    "envelope_version": "1",
    "event_id": "lowercase-uuid",
    "stream_id": "opaque-stable-stream-id",
    "sequence": "00000000000000000042",
    "event_type": "PAPER_FILL_PARTIAL",
    "schema_version": "paper-fill/1",
    "producer": {
      "service": "paper-execution",
      "instance_id": "opaque-instance-id",
      "build_sha": "full-source-commit-sha",
      "config_sha256": "64-lowercase-hex"
    },
    "scope": {
      "account_domain": "paper-account",
      "ledger": "CORE_LEDGER",
      "strategy_id": "RSI_ADX_SMART_DCA",
      "strategy_version": "immutable-version-id"
    },
    "time": {
      "occurred_at": "2026-11-07T00:00:00.123Z",
      "committed_at": "2026-11-07T00:00:00.130Z",
      "clock_source": "host-clock",
      "clock_uncertainty_ms": "5"
    },
    "causality": {
      "correlation_id": "opaque-id",
      "causation_event_ids": [],
      "intent_id": "opaque-id",
      "idempotency_key": "opaque-key"
    },
    "payload": {},
    "provenance": {
      "fact_class": "SOURCE_FACT",
      "source_type": "PAPER_ENGINE",
      "source_snapshot_id": "opaque-snapshot-id",
      "source_sha256": "64-lowercase-hex"
    },
    "previous_event_hash": "64-lowercase-hex-or-genesis"
  },
  "integrity": {
    "hash_algorithm": "SHA-256",
    "event_hash": "64-lowercase-hex",
    "signature_algorithm": "Ed25519",
    "signing_key_id": "opaque-key-version-id",
    "signature": "base64url-no-padding"
  }
}
```

This is an illustrative shape, not a frozen JSON Schema. Fields that are not applicable must use the explicit null/omission rules in §3.4; producers must not invent placeholder values.

### 3.2 Field contract

| Field | Requirement |
|---|---|
| envelope_version | Required string; version of the outer envelope contract |
| event_id | Required globally unique lowercase UUID; never reused |
| stream_id | Required stable opaque ID for one ordered producer/ledger stream |
| sequence | Required zero-padded 20-digit decimal string, starts at 1 per stream; never reused or reset |
| event_type / schema_version | Required allowlisted event type and immutable payload schema version |
| producer | Required service, process instance, exact source build SHA and config digest |
| scope | Required account domain, ledger owner and strategy identity/version; account domain must be pseudonymous |
| occurred_at | Required source/event time in UTC RFC3339 with exactly three fractional digits and trailing Z |
| committed_at | Required journal commit time in the same format; assigned at commit, not caller supplied |
| clock_source / uncertainty | Required clock provenance and measured/declared uncertainty; unknown uncertainty is explicit UNKNOWN, never zero |
| causality | Required correlation and idempotency identity; causation list may be empty only when event is a root event |
| payload | Required event-specific typed payload; no free-form financial numbers |
| provenance | Required distinction between source fact and derived projection, plus source identity where applicable |
| previous_event_hash | Required previous committed event hash for this stream; genesis uses a documented fixed sentinel |
| integrity | Required algorithm IDs, exact key version and signature; no implicit algorithm negotiation |

### 3.3 Numeric and time representation

- Monetary amounts, prices, quantities, rates, fees, funding amounts, leverage and fractional ratios MUST be decimal strings, never JSON floating-point numbers. Include currency/asset, unit, and scale/precision metadata where needed.
- Sequence numbers, 64-bit IDs, millisecond counters and other integers outside the interoperable IEEE-754 safe-integer range MUST be strings. This contract uses strings for sequence and clock uncertainty consistently.
- Decimal strings MUST use a single normalized grammar: optional leading minus, integer digits, optional decimal point and fractional digits; no exponent, leading plus, separators, NaN or Infinity. Whether trailing fractional zeros are preserved is schema-defined and must not be normalized after commitment.
- UTC timestamps MUST use RFC 3339 syntax narrowed to `YYYY-MM-DDTHH:mm:ss.sssZ`. Preserve original source timestamp separately if supplied with an offset; convert only through a deterministic, recorded normalization rule.
- Event time and commit time are distinct. Ordering MUST NOT silently replace event time with commit time. Clock uncertainty and late-arrival status are retained.
- Unicode strings are preserved as supplied; no implicit Unicode normalization.

### 3.4 Canonical bytes and null/omission semantics

Proposed canonicalization: UTF-8 JSON using RFC 8785 JCS, with duplicate property names rejected, recursively sorted object properties, and array order preserved.

Additional profile restrictions:
1. No JSON floating-point values are permitted in financial payloads or integer identity fields. Use decimal/integer strings as specified above.
2. No NaN, Infinity, duplicate keys, invalid Unicode, or implementation-specific number coercion is accepted.
3. Required fields cannot be omitted or null.
4. Optional fields are either omitted or explicitly null according to the event's immutable schema; the two representations are not interchangeable.
5. Unknown extension fields are rejected unless the schema version explicitly allows a namespaced extension map.
6. The canonical byte sequence is the UTF-8 encoding of the JCS serialization of `event_core` only. No BOM, trailing newline, or extra whitespace.
7. A verifier MUST canonicalize independently and compare the resulting bytes/hash; it MUST NOT trust a producer-supplied hash without recomputation.

This profile avoids the RFC 8785 IEEE-754 number precision boundary for financial values by representing exact decimals and large integers as strings. A production implementation must pass the RFC 8785 test vectors plus project-specific cross-language golden vectors before any capture is enabled.

### 3.5 Hash chain and signature

Define:
- `canonical_event_bytes = UTF8(JCS(event_core))`
- `event_hash = SHA256(UTF8("BTCUSDT-PAPER-EVENT-V1\\n") || canonical_event_bytes)`
- `signature_message = UTF8("BTCUSDT-PAPER-EVENT-SIGNATURE-V1\\n") || raw_32_byte_event_hash`
- `signature = Ed25519.Sign(private_key_for_key_id, signature_message)`

The event hash includes `previous_event_hash`, binding the stream chain. The integrity block is excluded from the canonical event bytes to avoid self-reference. The signature binds the event hash to a named key version.

Rules:
- Hashes are lowercase hexadecimal; signatures are base64url without padding.
- A stream's first event references a fixed, documented genesis sentinel; every subsequent event references the preceding committed event hash.
- The same event ID with identical canonical bytes is an idempotent duplicate. The same event ID with different bytes is a hard integrity fault.
- A sequence already committed with different event ID/hash is a hard integrity fault.
- Missing sequence, duplicate sequence, wrong predecessor hash, invalid signature, unknown/revoked key at event time, or canonicalization mismatch blocks evidence readiness.
- SHA-256 proves byte consistency, not origin authenticity. Signature verification depends on trustworthy key enrollment, custody, rotation and revocation evidence.
- Proposed signature algorithm: Ed25519 per RFC 8032. This is NOT a final key-custody decision. Private keys MUST NOT be stored beside event objects or in the same writer credential boundary.
- Key rotation is represented by a separately signed key-registry event/manifest with effective time, key ID, public key fingerprint, authorized scope and predecessor key reference. Revocation records are append-only and retained. Historical verification uses the key status applicable at signing time; missing key history means NOT VERIFIED.
- Key compromise requires an explicit compromise interval and affected event range. Re-signing old events does not erase the original trust failure.

### 3.6 Corrections, duplicates and late events

- Committed events are immutable. Corrections, cancellations, restatements and supersessions are new events referencing the original event ID/hash and a reason code.
- An event arriving after its logical event time is retained with its original `occurred_at`, actual `committed_at`, and explicit late-arrival classification.
- A late event that changes a closed UTC boundary, daily baseline, HWM, fee/funding attribution or reconstructed position invalidates the affected checkpoint/candidate until replay and independent verification complete.
- No event is backdated by rewriting commit time. No stream sequence is backfilled by editing earlier records.
- Out-of-order delivery is buffered only within a bounded policy. A gap is visible and blocks checkpoint sealing/readiness; timeout thresholds remain undecided.
- Delivery retries retain the same event ID and canonical bytes. A retry must never allocate a new event ID for the same committed economic fact.

## 4. Event taxonomy and minimum recoverable evidence

### 4.1 Required event classes

| Domain | Minimum event types / payload facts |
|---|---|
| Strategy intent | signal/intent created, strategy identity/version, side, instrument, decision inputs and source snapshot IDs |
| Risk admission | admission/rejection, risk-policy version, equity/exposure/DD/daily-loss inputs, limits, reservation ID and decision reason |
| Reservation | created, resized, consumed, released, expired; amount, currency, owner ledger, intent and idempotency key |
| Order lifecycle | submitted-to-paper-engine, accepted/rejected, partial/full fill, cancel, replace, expire; client/order IDs and state transitions |
| Fill | fill ID, order ID, side, quantity, price, quote value, fee and fee currency, liquidity/fill model, timestamp and source snapshot |
| Position / ledger | open, increase, reduce, close, DCA, reversal, realized/unrealized PnL attribution, average entry and remaining quantity |
| Funding | funding accrual/payment, interval, rate, amount, currency, source and coverage; UNKNOWN is not zero |
| Fee / adjustment | fee, rebate, correction, Legacy account-level adjustment and immutable owner/provenance |
| Mark / valuation | mark price, instrument, source, snapshot ID, timestamp, quality/staleness and valuation method |
| Risk state | Kill Switch state transitions, reason, actor/source, policy version, effective time; HWM and daily UTC baseline establishment/advancement |
| Configuration | strategy/risk/fill/funding model version, parameter digest, activation/deactivation and source build identity |
| Recovery / audit | checkpoint sealed/invalidated, replay started/completed/failed, observer acknowledgement, reconciliation result and operator action |

All event payloads must include instrument, quote/base units, ledger ownership and strategy provenance when relevant. Account-level legacy adjustments are explicitly account-level and must not be silently assigned to Core or AI.

### 4.2 Source facts versus derived projections

- `SOURCE_FACT`: immutable facts emitted at the decision/execution boundary (intent, admission, reservation, order/fill, fee/funding accrual, Kill Switch transition, configuration activation).
- `DERIVED_PROJECTION`: reproducible outputs (position projection, average entry, realized/unrealized PnL, equity, exposure, HWM, daily loss, checkpoint state).
- Derived events MUST reference every input event ID/hash, reducer version, configuration digest and calculation precision. They cannot replace source facts.
- A checkpoint is a derived artifact with a coverage manifest. It is not a substitute for the underlying event stream.
- Market marks are source observations with explicit source/time/quality; resulting valuation is derived and records the exact mark event IDs used.
- If required source facts are absent, a projection must preserve UNKNOWN and fail readiness; it must not synthesize zero fees, funding, missing fills or empty positions.

### 4.3 Minimum recovery completeness

A replayable account requires, at minimum:
1. Verified opening capital and cutover state, or a fully verified predecessor chain from genesis.
2. Complete Core, AI and Legacy/account-level ownership streams.
3. All intents, risk decisions, reservations and order lifecycle transitions.
4. Every partial/full fill and every reduce/close/reversal/DCA transition.
5. Fees, rebates, funding and adjustments with exact amounts, units, source provenance and coverage intervals.
6. Mark/valuation inputs sufficient to reproduce open-position equity at the checkpoint time.
7. Strategy, risk, fee, funding and fill-model versions plus immutable config/build digests.
8. Kill Switch, HWM and daily UTC baseline transitions, including the source equity snapshot.
9. Stream sequence/hash coverage, signed manifests, key registry/revocation history and Root A/Root B acknowledgements.
10. A separately retained checkpoint and deterministic reducer version for independent Root B reconstruction.

Any required category missing, UNKNOWN, stale beyond approved limits, or not covered by both roots means recovery status is NOT VERIFIED/BLOCKED. A test fixture cannot satisfy account-history completeness.

## 5. Segment manifest and durable acknowledgement

### 5.1 Sealed segment manifest

Events are batched into bounded immutable segments. Each sealed manifest MUST bind:
- manifest schema/version and globally unique manifest ID;
- stream ID, ledger scope, first/last sequence, event count;
- first/last event hash and previous segment manifest hash;
- exact canonical byte length and SHA-256 of the segment object;
- event schema versions and source build/config digests represented;
- segment creation/seal timestamps and clock uncertainty;
- signing algorithm, key ID and signature over the exact manifest canonical bytes;
- object identity after upload: provider/account/container/bucket/key plus immutable version ID or generation;
- retention mode, retain-until timestamp and legal-hold state as read back from the provider;
- Root A durable-write result and Root B receipt/checkpoint coverage references.

The manifest itself is immutable and version-addressed. A mutable `latest` pointer may be used only as a convenience index and MUST NOT be authoritative. The authoritative chain follows signed manifest hashes and exact object versions/generations.

### 5.2 Root A and Root B protocol

1. Producer constructs event, validates schema, allocates stream sequence and computes canonical bytes/hash/signature.
2. Root A journal durably commits the event and stream head using an atomic append/outbox boundary. A database state transition cannot be reported committed unless its corresponding evidence event is durably committed.
3. Root A seals bounded segments and records exact object version/generation, size, digest and retention metadata after read-back.
4. Root B consumes only committed envelopes from Root A's delivery/outbox interface; it does not query mutable account DB rows or derive its input from Root A's mutable projection tables.
5. Root B independently verifies schema, signature, sequence, predecessor hash, object bytes and coverage, then applies its separately versioned reducer and writes a separately retained checkpoint/receipt.
6. A Root B receipt identifies stream, contiguous sequence range, last event hash, reducer version, checkpoint digest, source manifest IDs and timestamp.
7. Acknowledgement is idempotent. A lost acknowledgement is retried without double-applying the event.

The exact atomic outbox mechanism (same transaction boundary, durable local journal, or another mechanism) remains an interface/design decision. It must prevent both a committed economic transition with no evidence event and a committed event falsely reported as an applied transition.

### 5.3 Root B independence boundary

Root B must have:
- a separate process/runtime identity and reducer implementation/version;
- a separate storage namespace and separately controlled credentials/admin boundary;
- no read permission to the mutable account DB;
- independent verification and checkpoint output;
- separately retained audit/key-registry/restore evidence.

Root B still shares upstream emitter trust unless another independent economic source is introduced. Do not describe this arrangement as Level 2 verification.

## 6. Recovery objectives and fail-closed behavior

### 6.1 Candidate objective definitions

| Objective | Proposed definition | Status |
|---|---|---|
| RPO-A | Zero loss of events acknowledged as durably committed by Root A | Candidate target; requires crash/power-loss and provider durability qualification |
| RPO-B | Root B checkpoint may lag Root A only within an explicitly approved event/time bound; no silent gaps | Threshold NOT DECIDED |
| RTO-A | Time from restart/fault declaration until Root A journal integrity and append readiness are re-established | Target NOT DECIDED |
| RTO-B | Time from Root B restart until contiguous consumption and checkpoint parity are re-established | Target NOT DECIDED |
| Restore RTO | Time to restore both roots into a clean-room environment and reproduce verified checkpoint digests | Target NOT DECIDED |
| Detection time | Maximum time to detect sequence gap, hash fault, stalled observer, stale mark or retention-policy drift | Threshold NOT DECIDED |

RPO-A zero is a proposed design target, not a claim about provider durability. A locally spooled but uncommitted event is not a Root A durable commit and cannot be counted as zero-RPO evidence.

### 6.2 Candidate service tiers (not selected)

Use measured fault-injection and restore results to choose targets. Candidate observation bands for planning only:
- Tier 1: recovery/observer lag target within 1 minute;
- Tier 2: within 5 minutes;
- Tier 3: within 15 minutes.

These are comparison bands, not approved service levels or runtime thresholds. Do not reuse the earlier unapproved 5-minute warning / 15-minute block as a default.

### 6.3 Fail-closed policy proposal

- Root A unavailable, append/hash chain broken, sequence gap, signature/key verification failure, object retention mismatch, or durable commit uncertain: block all new exposure increases immediately.
- Root B unavailable, behind, unable to verify, or checkpoint stale: independent verification is unavailable. Under the reliability-first proposal, block new exposure increases immediately until Root B catches up to the approved contiguous watermark and checkpoint verifies.
- Reductions and closures remain allowed only when their own evidence transition can be durably recorded and all required safety checks pass. If no safe durable evidence path exists, do not claim the reduction/closure committed; invoke only a separately approved emergency handling policy.
- A local encrypted spool is bounded transport/recovery staging, not an authoritative root. Spool-only acknowledgement never authorizes exposure increase.
- Never discard unacknowledged events to make the queue appear healthy. Spool full, disk full, key unavailable, clock uncertainty beyond policy, or retention lock failure blocks increases and raises a visible readiness fault.
- Recovery must replay idempotently, prove contiguous coverage and reconcile Root A/Root B before readiness can return.
- No automatic epoch activation, HWM reset, daily baseline reset or risk-limit relaxation occurs after recovery.

### 6.4 Spool and backpressure requirements

The spool must define maximum bytes, maximum age, maximum event count, per-stream quotas, encryption-at-rest, integrity check, fsync/commit semantics, replay order, retry policy and operator alert. All limits are TBD pending measured synthetic workload and PC disk constraints. On reaching any limit, stop exposure increases; do not overwrite oldest unacknowledged evidence. The PC spool is not the authoritative archive and loss of the PC must not destroy already acknowledged remote roots.

## 7. Retention, privacy and key lifecycle

### 7.1 Retention categories

Retention is not one global number. Decide separately for:
- raw signed event segments and their exact object versions;
- sealed manifests, hashes and Root A/Root B receipts;
- checkpoints, reducer versions and replay reports;
- provider administrative/audit logs and billing evidence;
- public keys, key-registry history, rotation/revocation/compromise records and verification metadata;
- encrypted spool copies and operational diagnostics.

### 7.2 Candidate retention horizons

For cost and recovery modeling only, compare 1-year, 3-year, 7-year and indefinite retention. None is selected. Indefinite retention has unbounded storage growth and may conflict with data minimization. A finite retention choice must still cover the intended audit/recovery horizon and any applicable legal hold. Do not infer a legal minimum or maximum without confirming jurisdiction and applicable rules.

The user's personal paper-trading purpose does not by itself establish that a specific financial-record retention statute applies. Legal/regulatory applicability, privacy, cross-border transfer and tax/accounting obligations require a separate jurisdiction-specific review before retention is approved.

### 7.3 Privacy and encryption

- Store opaque account/instance identifiers; avoid names, email, device identifiers, secrets, exchange API keys and unnecessary personal data.
- Separate encryption-at-rest keys from event-signing keys. Encryption protects confidentiality; signatures establish event origin/integrity under the key trust model.
- Define independent backup/recovery of encryption keys and public verification keys. Loss of a decryption key can make retained WORM evidence unusable; loss of a signing key must not prevent verification of already signed events if public key history is retained.
- Key destruction must never be used to simulate deletion of retained evidence or to conceal a compromise.
- Exact data residency, cross-border transfer and key custody remain undecided until provider/region and jurisdiction review.

## 8. Synthetic measurement and qualification

Before any cost quote or provider test, generate deterministic synthetic fixtures only:
- event mix covering all required classes, with realistic decimal string lengths and payload distributions;
- small/median/large event-size cohorts and burst scenarios;
- batching/segment sizes, manifest/signature overhead, object count and retry/version behavior;
- audit and checkpoint size;
- Root B reducer lag, replay throughput and full clean-room restore volume/time;
- spool growth under Root B outage and recovery drain rate.

Record fixture generator version/commit, deterministic seed, event counts by type, canonical byte sizes (min/median/p95/max), segment sizes, daily byte/object projection, hash/signature CPU time, observer throughput and restore duration. Hashes and results must be reproducible from fixture source and exact SHA.

No real account DB, account history, exchange connection, production runtime, provider account or persistent storage is needed for this measurement phase. No synthetic benchmark result is claimed by this document.

## 9. Required acceptance tests to add to P1.1 plan

Add vendor-neutral tests for:
1. RFC 8785 JCS golden vectors and cross-language byte-for-byte equivalence.
2. Project profile rejection of floats, unsafe integers, duplicate keys, invalid Unicode, NaN/Infinity and ambiguous null/omission.
3. Exact domain-separated event hash and signature vectors; tampered payload/hash/signature/key ID rejection.
4. Per-stream genesis, sequence monotonicity, predecessor hash, duplicate retry and same-ID/different-bytes rejection.
5. Late event and append-only correction/supersession behavior across UTC boundary.
6. Manifest canonicalization/signature, segment byte count/digest and exact immutable object version/generation binding.
7. Root B input isolation: prove it cannot query mutable account DB and can replay only committed Root A envelopes.
8. Root B duplicate acknowledgement, crash-before/after-checkpoint and idempotent replay.
9. Required event-class coverage, source-vs-derived provenance and UNKNOWN fee/funding/mark handling.
10. Root A/Root B outage, spool-full, disk-full, key-loss, retention drift, lag and backpressure fail-closed behavior.
11. RPO/RTO, observer catch-up and clean-room restore measurements against separately approved thresholds.
12. Retention-expiry, legal-hold and key lifecycle verification under approved policy.
13. Synthetic volume/cost worksheet reconciliation from actual canonical byte sizes and request counts.

These are design test requirements only. No tests have been executed and no runtime behavior is certified.

## 10. Open decisions requiring explicit approval

1. Canonical event profile and final JSON Schema/versioning policy.
2. Ed25519 or another reviewed signature scheme; signing-key custody, hardware boundary, recovery and compromise process.
3. Atomic journal/outbox implementation and the precise durable-commit boundary.
4. Stream topology and ownership of account-level events versus Core/AI/Legacy streams.
5. Root B lag watermark and outage policy; whether any bounded degraded mode is ever acceptable.
6. RPO-A/RPO-B, RTO-A/RTO-B, restore RTO and detection thresholds.
7. Spool bytes/age/event caps and PC storage role.
8. Retention horizon by evidence category, legal hold and jurisdiction.
9. Provider pair, account/admin owners, region, residency and cross-border transfer.
10. Approved monthly and one-time test budget.
11. Synthetic event-size/volume measurement and restore throughput.
12. Privacy classification, encryption-key custody and key rotation/revocation.

No default is silently selected by the order of this list.

## 11. P1.5 result

- Envelope and manifest contract: DOCUMENTED PROPOSAL.
- Canonicalization: RFC 8785 JCS profile proposed; NOT IMPLEMENTED / NOT TESTED.
- Hash/signature: domain-separated SHA-256 + Ed25519 proposed; key custody NOT DECIDED.
- Recovery event coverage: DOCUMENTED.
- RPO/RTO and Root B lag: candidate definitions documented; thresholds NOT DECIDED.
- Fail-closed: reliability-first policy proposed; NOT IMPLEMENTED.
- Retention: 1/3/7-year and indefinite comparison horizons only; NOT SELECTED.
- Synthetic size/throughput benchmark: NOT RUN.
- Provider/account/region/budget/provisioning/provider tests: NOT APPROVED / NOT RUN.
- Source/schema/workflow/database/runtime: UNCHANGED.
- CI: NOT RUN (documentation-only).
- Historical Dual Reconstruction: UNAVAILABLE / BLOCKED; Option A unchanged.
- T0: PAUSED; PAPER-only; `ai_execution_enabled=false`.

Next permitted step: review this contract and unresolved decisions, then prepare a deterministic synthetic fixture specification and measurement worksheet. Implementation, provider qualification, persistent capture and any risk-policy change require separate explicit approval.

## 12. References

- RFC 8785 — JSON Canonicalization Scheme: https://www.rfc-editor.org/rfc/rfc8785
- RFC 8032 — Edwards-Curve Digital Signature Algorithm: https://www.rfc-editor.org/rfc/rfc8032
- RFC 3339 — Date and Time on the Internet: https://www.rfc-editor.org/rfc/rfc3339
