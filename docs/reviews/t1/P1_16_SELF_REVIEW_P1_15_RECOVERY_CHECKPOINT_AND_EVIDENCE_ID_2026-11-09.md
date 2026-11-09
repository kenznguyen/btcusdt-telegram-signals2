# P1.16 — Self-review of P1.15 recovery checkpoint and evidence identity corrections

Date: 2026-11-09
Review type: Same-session adversarial static self-review; NOT independent.
Exact normative contract blob SHA: `f78dc4410db61755149cb6a7e0c440330bc80741`
Latest contract commit: `69559bb0363934158351d794a48e17555f0222a8`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

## Verdict

**DOCUMENTATION-LEVEL PASS for the requested F02-R1 and F05-R1 corrections and fixture specifications C125–C132. IMPLEMENTATION READINESS NOT ESTABLISHED. F07 NOT VERIFIED. INDEPENDENT REVIEW REQUIRED.**

This review is same-session and does not satisfy issue #138.

## Scope and checks

### F02-R1 — Recovery checkpoint and rollback boundary

PASS at documentation level:
- §22.11.1 defines the recovery-checkpoint directory/path, one immutable checkpoint per publication sequence, a closed 17-key schema, canonical JCS/strict parser rules, exclusive temporary creation, file fsync, no-replace installation and directory fsync.
- §22.11.2 binds each checkpoint to exact receipt/manifest/data-prefix digests and an embedded five-key publication-counter snapshot plus its digest. It defines monotonic consistency checks against the current counter, complete receipt directory and all checkpoints.
- §22.11.3 defines restart ordering: revalidate all state, repeat commits/generation fsync barriers, install or revalidate the checkpoint candidate, then fsync recovery-checkpoints and generation directories before recovery acceptance.
- A checkpoint/counter stored in one root is explicitly NOT an independent anti-rollback anchor. Full-root copy/restore without an independently trusted monotonic external anchor means continuity is NOT PROVEN and the root must be quarantined. The design does not claim protection against full-root rollback, host compromise or privileged tampering.
- C125–C130 specify malformed schema, identity/sequence mismatch, digest mismatch, counter regression, fsync/crash and copied-root negative cases.

### F05-R1 — Raw-body versus envelope identities

PASS at documentation level:
- §22.11.4 gives separate storage namespaces and meanings for Raw-body object ID and Envelope-record ID.
- The manifest's `exchange_info_evidence_ref` is explicitly the Envelope-record ID; it cannot be satisfied by the Raw-body ID.
- The envelope's `raw_body_sha256` binds the exact raw HTTP response bytes.
- To avoid a self-referential digest, Envelope-record ID is computed from the canonical envelope projection with `evidence_id` omitted; the stored envelope remains canonical JCS and verification reproduces that projection digest.
- Resolution order and wrong-namespace/swap rejection are specified.
- C131–C132 cover reference namespace confusion, projection digest failure and raw-body mismatch.

### Internal consistency checks

- §22.9 now defers the `evidence_id` construction to §22.11.4; it no longer claims that the self-containing final envelope bytes are hashed directly.
- §22.11.4 resolution wording uses the projection-digest method; no sentinel construction remains.
- C127 names the counter-snapshot digest, matching the checkpoint schema.
- C129 requires revalidation and repeat directory barriers after a crash before checkpoint-directory fsync.
- §22.11.2 explicitly recognizes that local checkpoint/counter state cannot detect a full-root rollback without an independent anchor; no stronger guarantee is claimed.

## Remaining limitations and blockers

- F07 remains NOT VERIFIED: target filesystem/mount/device/provider identity and actual flock, renameat2, file-fsync and directory-fsync behavior have not been tested.
- Binance REST completeness/no-trade/boundary/pagination/finality/correction semantics remain NOT ACCEPTED.
- Pinned producer f64 conversion, fixed 12-decimal formatting and parse-error-to-zero defect remains CONFIRMED / NOT FIXED.
- Producer FINAL_ONLY/product identity implementation and regression evidence remain NOT VERIFIED.
- Manifest, receipt, publication counter, recovery checkpoint, ExchangeInfo evidence store and adapter remain NOT IMPLEMENTED.
- C01–C132 are design scenarios only; NOT IMPLEMENTED / NOT EXECUTED.
- No GitHub Actions run or artifact is claimed.

## Authorization boundary

Documentation and review only. No source changes, tests, GitHub Actions dispatch, Binance REST request, VPS/runtime, T1 activation, T0/T2 changes, strategy/AI/ledger/risk/trading changes, deletion, archive, cleanup, vacuum, compaction, backup expiry, restore or destructive operation.

T0 remains independent/canonical. No T1 writes to T0. Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.

## Next step

Retarget issue #138 to this exact contract blob SHA and request genuinely independent adversarial review. Do not implement or activate T1 until independent review, F07 evidence and separate owner approval gates are satisfied.
