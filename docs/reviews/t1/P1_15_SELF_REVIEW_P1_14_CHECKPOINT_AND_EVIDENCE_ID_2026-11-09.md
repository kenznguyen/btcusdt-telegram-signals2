# P1.15 — Follow-up adversarial self-review of P1.14 T1 contract

Date: 2026-11-09
Review type: Same-session static adversarial self-review; NOT independent.
Exact normative contract blob SHA: `59d8988a368a5bfffa94eacf7fbb8d769aea9b60`
Contract commit: `5745248abed4fb02fa1a15688b1ba17771eaaa46`
Reviewed prior self-review blob: `64ca44a5549ad51e66c9dc5d0e0dd4947e826552`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

## Verdict

**REQUEST CHANGES — P1.14 closes the previously identified F04 schema-precedence conflict at documentation level, but F02 recovery-checkpoint semantics and F05 evidence-reference identity remain insufficiently unambiguous. Implementation readiness is NOT ESTABLISHED. Independent review remains REQUIRED.**

This review is same-session and does not satisfy issue #138.

## Findings

### F02-R1 — Recovery checkpoint lacks a closed, independently verifiable contract
Severity: HIGH
Disposition: OPEN — REQUIRED

§22.6.1 requires a durable recovery checkpoint binding receipt digest, manifest digest, generation and sequence. It also requires exclusive temporary creation, file fsync, atomic installation and parent-directory fsync. However, the contract does not define:
- the checkpoint's exact path, closed schema, canonical encoding and version;
- whether checkpoints are immutable/no-replace or replaceable, and how multiple/obsolete checkpoints are enumerated;
- the exact relationship between checkpoint state and `publication-counter.json`, including monotonic/high-water validation;
- how recovery detects checkpoint rollback or loss when the checkpoint and counter are restored/copied together from the same source root;
- explicit negative fixtures for missing, malformed, regressed, conflicting, copied or generation-mismatched checkpoints.

This matters because the recovery checkpoint is the durable proof used to resolve a visible receipt whose original commits-directory fsync cannot be proven. A checkpoint that is merely durable in the same rollback domain may not prove that it is the latest accepted checkpoint. The document correctly says the initialization record is not an anti-rollback anchor and that root restore/copy cannot claim continuity without an independently trusted latest counter/checkpoint, but it does not define what that trusted checkpoint is or how its independence is established.

Required correction: define a versioned closed checkpoint record and exact storage/atomicity rules; define the trust/rollback boundary and fail-closed behavior when latest-state continuity cannot be proven; add deterministic fixtures for missing/corrupt/old/copied/ahead/conflicting checkpoints and counter disagreement. Do not imply protection against full host/root rollback unless an independent anchor is specified and approved.

### F05-R1 — Raw-body object identity and envelope identity are not explicitly separated
Severity: MEDIUM
Disposition: OPEN — REQUIRED

§22.5 describes the ExchangeInfo evidence object's identifier as the SHA-256 of the exact raw HTTP response body. §22.9 separately defines `evidence_id` as `sha256:<64 lowercase hex>` and says the envelope's own content-addressed ID is the SHA-256 of the canonical envelope bytes; that envelope also contains `raw_body_sha256`. The manifest field `exchange_info_evidence_ref` is described as resolving to the exact raw snapshot, but the contract does not explicitly state whether it references the raw-body object ID, the envelope ID, or a typed pair of references.

These are legitimately different digests. Without an explicit namespace and resolution rule, an implementation could use the envelope digest where the raw object digest is expected, or vice versa, while each digest independently validates.

Required correction: name the two identities distinctly (for example, raw-body object digest and envelope-record digest); define the exact manifest reference target; define the envelope's binding to the raw-body object path/bytes and the lookup/verification order; add fixtures for swapped IDs, envelope digest mismatch, raw-body digest mismatch and reference-type confusion.

## Rechecked items

- F04: PASS at documentation level for the specific former six-key/eleven-key initialization-schema conflict. §22.9 is authoritative and §§22.4/22.10 explicitly defer/supersede.
- F02: receipt acceptance linearization point and directory recovery fsync sequence are stated in §22.6.1. The checkpoint proof contract remains incomplete as described in F02-R1.
- F05: raw response bytes, digesting before parse, exact symbol-record slice, duplicate-key rejection and header allowlist are specified. The identity relationship between raw-body object and envelope record remains ambiguous as described in F05-R1.
- F01: current-profile `RECONCILED_COMPLETE` and `reconciliation_evidence_ref` are forbidden; watermark is non-authoritative progress only. Contract-level pass; no parser proof.
- F03: single-host/local-POSIX/flock profile is specified; target filesystem/mount/provider behavior remains NOT VERIFIED.
- F06: no-replace receipt publication is specified; implementation and target primitive availability remain NOT VERIFIED.
- C117–C124: scenarios are specified only; NOT IMPLEMENTED / NOT EXECUTED. C117–C120 do not cover the checkpoint rollback/corruption cases identified above.

## Unchanged blockers and evidence limits

- F07: target filesystem/mount/device/provider identity and flock/renameat2/file-fsync/directory-fsync behavior NOT VERIFIED.
- Binance REST completeness/no-trade/boundary/pagination/finality/correction semantics NOT ACCEPTED.
- Pinned producer f64 conversion, fixed 12-decimal formatting and parse-error-to-zero defect CONFIRMED / NOT FIXED.
- Producer FINAL_ONLY/product identity implementation and regression evidence NOT VERIFIED.
- Manifest, receipt, publication counter, recovery checkpoint, ExchangeInfo evidence store and adapter NOT IMPLEMENTED.
- C01–C124 are design scenarios only; NOT IMPLEMENTED / NOT EXECUTED.
- No GitHub Actions run or artifact is claimed.

## Required next actions

1. Correct F02-R1 by specifying the checkpoint contract and rollback/trust boundary, then add negative fixtures.
2. Correct F05-R1 by separating raw-body and envelope identities and defining the exact manifest reference.
3. Re-review the new exact contract blob and update issue #138 only when its target SHA is final.
4. Obtain genuinely independent written review before any implementation consideration.

## Authorization boundary

Review/documentation only. No source changes, test execution, GitHub Actions dispatch, Binance REST request, VPS/runtime, T1 activation, T0/T2 changes, strategy/AI/ledger/risk/trading changes, deletion, archive, cleanup, vacuum, compaction, backup expiry, restore or destructive operation.

T0 remains independent/canonical. No T1 writes to T0. Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.
