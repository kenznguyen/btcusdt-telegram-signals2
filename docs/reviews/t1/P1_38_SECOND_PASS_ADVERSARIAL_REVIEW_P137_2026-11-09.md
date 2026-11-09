# P1.38 — Second-pass adversarial review of P1.37

Date: 2026-11-09
Review type: Fresh second-pass, same-session static adversarial self-review; NOT an independent third-party review.
Branch: feature/t0-centralized-data-feeder-p1-20261101
Exact normative contract blob reviewed: 9125e89b227fd9fa8364a02188d0be54ec3dd2ef
P1.37 review blob examined: 2f4e036e4b0db7395588424783e6319e28779344

## Verdict

**DOCUMENTATION-LEVEL PASS — no new actionable contract defect found in the P1.37 correction set or the directly coupled receipt/checkpoint/recovery rules examined.**

This is not genuinely independent review: the same assistant/session cannot supply a different reviewer identity or independent expertise. It is a new adversarial pass with explicit cross-section checks, not a substitute for the independent reviewer requested by issue #138.

## Review scope and evidence

Reviewed the exact contract blob `9125e89b227fd9fa8364a02188d0be54ec3dd2ef`, not merely the mutable branch name. Cross-checked:

1. §5.2 publication ordering and receipt creation.
2. §21.5 manifest and receipt serialization, exact byte bounds, embedded-manifest encoding and identity binding.
3. §§22.2, 22.4, 22.6 and 22.6.1 publication counter, closed receipt schema, no-replace publication and commit-acceptance/recovery barriers.
4. §§22.9–22.11 initialization, recovery epoch, checkpoint, historical receipt and ExchangeInfo evidence schemas.
5. C100–C197 additions and the current §22.8 / §22.11.5 implementation-status statements.
6. Guardrails and all remaining implementation, filesystem, REST and producer blockers.

### Specific P1.37 regression checks

- The receipt schema in §22.4 contains exactly twelve top-level keys: `receipt_version`, `source_root_id`, `generation_sequence`, `generation_id`, `publication_sequence`, `manifest_sha256`, `manifest_jcs_base64url`, `data_file_identity`, `committed_offset_bytes`, `committed_record_count`, `watermark_open_time_exclusive_ms`, and `data_prefix_sha256`.
- `manifest_jcs_base64url` is not an unknown extension: §5.2, §21.5, §22.4, §22.11.2 and C190–C197 consistently require and consume it.
- The encoded maximum of 87,382 characters is consistent with unpadded base64url encoding of 65,536 bytes. The decoded byte range, canonical decode/re-encode, UTF-8/JCS parser and SHA-256 binding are all explicit.
- The complete receipt byte bound remains 1–131,072 bytes, and the manifest bound remains 1–65,536 bytes.
- Historical recovery uses the exact manifest bytes embedded in each immutable receipt; it does not substitute the replaceable active `manifest.json`.
- Checkpoints bind exact receipt bytes with `receipt_sha256` and the historical manifest digest with `manifest_sha256`; checkpoint recovery epoch is separately bound to root initialization and the immutable recovery-epoch record.
- Publication ordering requires manifest directory fsync before receipt creation, no-replace receipt installation, commits-directory fsync while the writer lock is held, and lock release only after successful completion.
- §22.8 reports C01–C197 as design scenarios only, NOT IMPLEMENTED / NOT EXECUTED; §22.11.5 makes the same non-implementation status explicit.
- No stale C01–C124 current-inventory claim was found in the current normative summary.

## Findings

No new actionable P1.37-level contract defect identified in this pass.

This conclusion is bounded to static document consistency. It is not a claim that every historical requirement across the entire 161 KB document has been independently proven correct, nor that the design is implementable or safe at runtime.

## Residual blockers and limits — unchanged

- F07 target filesystem/mount/device/provider identity and actual `flock`, `renameat2(RENAME_NOREPLACE)`, file-fsync and directory-fsync behavior: NOT VERIFIED.
- Binance REST completeness/no-trade/boundary/pagination/finality/correction semantics: NOT ACCEPTED.
- Pinned producer f64 conversion, fixed 12-decimal formatting and parse-error-to-zero defect: CONFIRMED / NOT FIXED.
- Producer FINAL_ONLY/product identity implementation: NOT VERIFIED.
- Manifest, receipt, publication counter, recovery checkpoint, recovery-epoch/approval verifier, external trust-policy loader, ERA service, monotonic store and ExchangeInfo evidence store: NOT IMPLEMENTED / NOT VERIFIED.
- C01–C197: contract design scenarios only; NOT IMPLEMENTED / NOT EXECUTED.
- No GitHub Actions run/artifact, executable tests, REST request, VPS/runtime or filesystem experiment was performed or claimed.
- No source change, T0/T2 change, T1 activation, live order, deletion or destructive operation occurred.

## Status and next gate

- P1.37 contract: DOCUMENTATION-LEVEL PASS retained.
- P1.38 second-pass self-review: DOCUMENTATION-LEVEL PASS.
- Genuinely independent review: PENDING on issue #138; this review does not satisfy that requirement.
- Issue #138 must remain OPEN and target the exact contract blob above plus this exact review blob after commit/readback.
- Implementation and T1 activation remain NOT AUTHORIZED.
- T0 remains independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.
