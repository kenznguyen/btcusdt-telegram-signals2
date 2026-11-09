# P1.11 — Same-session self-review of revised T1 Source Contract

Date: 2026-11-09
Review type: Same-session adversarial self-review; NOT independent.
Verdict: **REQUEST CHANGES — CONTRACT HAS FALSE-PASS AND FENCING/SCHEMA GAPS; IMPLEMENTATION NOT READY.**

## 1. Exact reviewed inputs

- Repository: kenznguyen/btcusdt-telegram-signals2
- Branch: feature/t0-centralized-data-feeder-p1-20261101
- Normative design blob SHA: 32cf231227c52590ad1365473c6c742ab7dbc64a
- Archival v1 blob SHA: c64d6da7b16e608ef5ccebafabce03e51960cfcc
- P1.10 same-session review blob SHA: 1abbb75e52df88b354191668ce2b276a322f4411
- Pinned T1 producer source SHA: 6e20fe94f3ad64cc450e73def80a167fe371e49e
- Independent review issue: #138, OPEN at time of review; no reviewer comments.

This is a same-session review and cannot satisfy the independent-review gate.

## 2. Findings

### F01 — CRITICAL: Manifest schema still permits RECONCILED_COMPLETE without an accepted completeness profile

Evidence:
- §4.2 declares source_health enum RECONCILED_COMPLETE | UNKNOWN | INVALIDATED and requires a reconciliation_evidence_ref when RECONCILED_COMPLETE is claimed.
- §4.3, §§14–15 and §21.3 state that Binance REST is not an accepted completeness oracle, no-trade/boundary/pagination/finality/correction semantics remain unresolved, and no current evidence profile can establish complete coverage.
- §21.5 still permits source_health=RECONCILED_COMPLETE in the strict manifest schema and only requires a retrievable evidence reference. It does not require the parser to reject RECONCILED_COMPLETE under the current profile or define an accepted evidence-profile identifier/schema.

Risk: a producer can publish a syntactically valid manifest with RECONCILED_COMPLETE and an arbitrary/retrievable evidence reference. A consumer implementation following only the field schema could accept a false completeness claim, even though the narrative says the oracle is not accepted. This is a direct false-PASS path.

Required correction:
- Under current v1.1 profile, make RECONCILED_COMPLETE unassignable and reject any manifest claiming it; allow only UNKNOWN/INVALIDATED (and quarantine/pending represented by the defined state model).
- Bind any future completeness claim to an explicit, versioned, independently approved evidence_profile_id and exact evidence schema. Enabling it requires a new contract/profile version and explicit approval.
- Add a negative fixture: validly canonical/JCS manifest with RECONCILED_COMPLETE plus arbitrary evidence_ref must be rejected, with no watermark, receipt or canonical eligibility.

### F02 — HIGH: publication_sequence allocation/recovery is not specified as durably monotonic

Evidence:
- §21.5 requires publication_sequence to be strictly increasing within a generation.
- §5.1 specifies durable allocation for generation_sequence, but not for publication_sequence.
- §5.2 requires unique receipt filename per generation/publication sequence and immutable receipts, but does not define how the next publication sequence is reserved across a crash before/after manifest rename, receipt rename or receipt loss.

Risk: after a crash, the writer may reuse a sequence based on the last visible manifest while an orphan receipt for that sequence exists, or skip/reuse values inconsistently if receipt visibility/durability differs. The design does not define whether sequence is derived from durable state, all receipts, or an append-only allocator.

Required correction:
- Define a publication-sequence allocator with explicit durable ordering and crash recovery, including orphan temp files/receipts and sequence reservation before manifest publication.
- Specify that sequence values are never reused once potentially published; ambiguity quarantines the generation.
- Add crash-window fixtures for allocation, manifest replacement, receipt rename, receipt loss and restart.

### F03 — HIGH: advisory lock contract does not bound topology or define safe initialization/race behavior

Evidence:
- §5.1 says the lock file is pre-created/stable, advisory, shared by readers and exclusive for writers, but does not state a supported single-host/local-filesystem topology.
- The document says target filesystem/provider semantics must be verified but does not define which lock API/semantics are required, or how concurrent first-time initialization is serialized.
- §21.2 says all cooperating processes use the same filesystem object but does not define how a process proves it opened the canonical lock inode rather than a replaced/path-substituted object.

Risk: advisory-lock semantics differ across local filesystems, network filesystems and multi-host mounts. Locking may be process-scoped, host-scoped or unreliable under provider failover. Concurrent initialization, stale mount behavior or lock-path replacement can create split-brain despite the prose rule.

Required correction:
- Explicitly restrict v1.1 to a single-host, verified local filesystem unless a separately tested multi-host profile is approved.
- Define lock API, open flags/no-follow behavior, stable lock identity verification, ownership/permissions, initialization serialization and behavior after remount/provider failover.
- If topology or semantics cannot be proven, fail closed before writer or reader access.
- Add two-process and (if claimed) multi-host contention/crash fixtures. Runtime filesystem evidence remains separately required.

### F04 — HIGH: strict manifest schema is not yet machine-unambiguous

Evidence:
- §21.5 lists fixed values in prose (e.g. exchange_id=binance, interval=1m) rather than defining a complete normative JSON Schema/field-by-field grammar.
- UUIDv4, timestamps, hashes and data_file_identity members are described but canonical textual formats and allowed character sets are not fully specified.
- The receipt schema is a field inventory, but exact types, canonical UUID representation, filename grammar and duplicate/extra-file rules are not fully enumerated.
- The generation counter state itself has no complete closed schema or integrity/recovery contract.

Risk: independent implementations may accept different manifests/receipts as valid; parser differentials and path/identity ambiguities can cause false acceptance or inconsistent recovery.

Required correction:
- Publish a complete machine-readable closed schema or equivalent field-by-field normative grammar for manifest, receipt, generation counter and ExchangeInfo evidence envelope.
- Define canonical UUID/hash/timestamp/path encodings, exact enums and constants, object key sets, receipt filename, sequence bounds and counter recovery.
- Specify hard-link policy concretely (e.g. expected link count) and stable file identity semantics for the supported platform.
- Add parser differential and malformed/canonicalization fixtures.

### F05 — HIGH: ExchangeInfo evidence reference is not fully specified as immutable evidence

Evidence:
- §21.5 requires exchange_info_evidence_ref to resolve to an immutable raw ExchangeInfo snapshot and validates snapshot/record digests.
- It does not specify the immutable storage mechanism, retrieval authorization, exact raw-byte digest convention, evidence envelope schema, retention/availability behavior, or whether the referenced object can be replaced at the same identifier.

Risk: a mutable or unavailable reference can undermine the product-identity proof even when the manifest digests are syntactically valid.

Required correction:
- Define content-addressed immutable evidence retrieval: digest over exact raw response bytes, immutable identifier derived from digest, exact symbol-record extraction/canonicalization rules, request endpoint/parameters/time and HTTP response metadata.
- If evidence is missing, changed or unavailable, reject the generation; never trust the reference label alone.
- Add replacement, missing-reference, mismatched-digest and duplicate-symbol-record fixtures.

### F06 — MEDIUM: “immutable receipt” and one-valid-receipt rule need explicit storage enforcement

Evidence:
- §21.5 calls receipts immutable and says duplicate receipts for a sequence or ambiguity cause quarantine.
- §5.2 writes receipt temp then renames it, but does not define no-replace semantics for final receipt publication or how overwrite/unlink of an existing receipt is prevented.
- Reader wording “exactly one valid receipt that matches” needs explicit handling for multiple valid receipts, orphan temp files, extra receipt files and unknown sequence entries.

Risk: a faulty or malicious writer may replace a receipt for an already published sequence, or implementations may differ in how they handle extra/orphan receipt files.

Required correction:
- Require atomic no-replace publication for receipt filenames, reject if the destination exists, and define directory scan/sequence consistency rules.
- Treat any conflicting, replaced, missing or unexpected receipt as quarantine; do not overwrite.
- Add duplicate-sequence, receipt replacement, orphan-temp and extra-file fixtures.

### F07 — HIGH: deterministic crash tests cannot by themselves prove the filesystem durability premise

Evidence:
- §§5.2 and 21.1 rely on data fsync, manifest rename, parent-directory fsync, then receipt publication. The document correctly says target semantics are unverified.
- No implementation, filesystem test, provider/mount profile or crash/recovery result exists for the intended deployment target.

Risk: the protocol's safety depends on storage honoring the exact fsync/rename/lock ordering. Unit tests or process-kill tests on an unrelated filesystem cannot prove power-loss or provider-failure durability.

Required correction:
- Keep implementation and promotion blocked until the exact target filesystem, mount options, device/provider, lock primitive and crash model are recorded and independently reviewed.
- Require a separately authorized test plan for process crash and host/power/provider interruption, with durable evidence and explicit claim level. Never infer D2–D4 from process-level tests.

## 3. Existing findings revalidated

- REST completeness oracle: BLOCKED. Binance REST does not yet prove no-trade minutes, boundary semantics, complete pagination, finality or correction immutability.
- Decimal preservation: BLOCKED. Pinned producer source still converts numeric strings through f64, formats 12 decimal places and maps parse errors to 0.0. This remains a confirmed producer defect.
- FINAL_ONLY and interval/product identity: contract requirements exist, but pinned producer implementation and regression evidence are NOT VERIFIED.
- C01–C99: design-only fixture catalog; NOT IMPLEMENTED / NOT EXECUTED.
- T1 source-file adapter, manifest/receipt parser and lock implementation: NOT IMPLEMENTED.
- T1 activation: NOT AUTHORIZED.

## 4. Overall assessment

P1.10 materially improved the design by separating manifest visibility from commit acceptance, introducing receipt-gated publication, defining cooperative writer/reader locking, reserving gap classifications and tightening product identity. However, the design is not implementation-ready.

F01 is a critical false-PASS path: the manifest schema still allows a completeness state that the current evidence profile cannot justify. F02–F05 are material protocol/schema ambiguity. F06 requires immutable no-replace semantics. F07 remains an operational proof gate.

**Verdict: REQUEST CHANGES.** Resolve F01–F06 in the contract, then perform another static consistency review. Independent review of the corrected exact SHA remains mandatory before implementation consideration.

## 5. Guardrails and scope

Read-only GitHub review and review-record documentation only. No T1 source edits, adapter implementation, test execution, Binance REST request, GitHub Actions dispatch, VPS/runtime, T1 activation, T0/T2 changes, strategy/AI/ledger/risk changes, live orders, data deletion, archive, cleanup, vacuum, compaction, backup expiry, restore or destructive operation.

T0 remains independent and canonical. No T1 writes to T0. Paper-only; AI_EXECUTION_ENABLED=false; no live orders; no OKX fallback/replacement.

## 6. Next steps

1. Correct F01 first: make RECONCILED_COMPLETE unassignable in current v1.1.
2. Specify durable publication_sequence allocation and no-reuse recovery.
3. Bound lock topology and define lock initialization/identity semantics.
4. Complete strict schemas for manifest, receipt, generation counter and ExchangeInfo evidence.
5. Enforce no-replace immutable receipt publication.
6. Update C100+ negative/crash/parser fixtures; these remain planned until implemented and run.
7. Re-review corrected SHA; independent review remains a separate mandatory gate.

No implementation or T1 activation is authorized by this self-review.
