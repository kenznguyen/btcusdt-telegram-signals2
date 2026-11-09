# P1.37 — Exact-SHA adversarial self-review: receipt schema coherence

Date: 2026-11-09
Review type: Same-session adversarial static self-review; NOT independent.
Branch: feature/t0-centralized-data-feeder-p1-20261101
Exact normative contract blob reviewed: 9125e89b227fd9fa8364a02188d0be54ec3dd2ef
Prior review: P1.36, blob 163928749d5c2d756fb6aa98af6e1859bd95c7f6
Prior contract: 1957eee80d5f6eb80889506514aaecf4b6a912cb

## Verdict

**DOCUMENTATION-LEVEL PASS for the P1.36 receipt-embedded historical-manifest correction, the directly coupled closed-schema rules, and the fixture inventory status statement.**

This is a same-session review, not an independent review. It does not establish implementation readiness, executable fixture correctness, target-filesystem durability, Binance completeness, or runtime safety. It does not close F07 or any producer/REST blocker.

## Findings against the prior exact contract

### F02-R19 HIGH — receipt schema omitted the new embedded-manifest field

P1.36 required `manifest_jcs_base64url` in §5.2 step 7 and §21.5, and recovery in §22.11.2 required every receipt to carry and validate that field. However, §22.4 declared an exact closed receipt key set that omitted `manifest_jcs_base64url`, while also prohibiting unknown keys. A conforming §22.4 parser would therefore reject every P1.36 receipt that conformed to §21.5. The contract had no simultaneously satisfiable receipt schema.

**P1.37 correction:** §22.4 now explicitly enumerates all twelve receipt keys, including `manifest_jcs_base64url`, and binds its type, canonical unpadded base64url alphabet, no-padding/no-whitespace rule, exact decode/re-encode, decoded byte range, complete §21.5 manifest validation, digest equality and encoded-length maximum. It retains the complete receipt byte bound and exact filename/sequence binding.

### F02-R20 MEDIUM — stale fixture inventory in §22.8

The contract's terminal fixture status in §22.11.5 was C01–C197, but §22.8 still reported only C01–C124 as the complete design-only inventory. This made the current authorization/evidence summary stale and understated the actual contract fixture scope.

**P1.37 correction:** §22.8 now reports C01–C197 as design scenarios only, NOT IMPLEMENTED / NOT EXECUTED.

## Exact-SHA adversarial checks

Reviewed exact blob `9125e89b227fd9fa8364a02188d0be54ec3dd2ef`, not a mutable branch assumption.

- Compared the §5.2 receipt publication requirement, §21.5 receipt schema, §22.4 normative closed receipt schema and §22.11.2 recovery parser requirements.
- Confirmed the §22.4 receipt key inventory now contains twelve fields and includes the historical manifest bytes field required by §5.2, §21.5, §22.11.2 and C190–C197.
- Confirmed §22.4 now specifies canonical encoding and bounds for the embedded manifest and does not permit extra receipt keys.
- Confirmed §22.11.2 still binds exact receipt bytes through checkpoint `receipt_sha256`, and the historical manifest digest through receipt/checkpoint `manifest_sha256`.
- Confirmed the §22.8 inventory now matches the terminal C01–C197 design-only status in §22.11.5.
- Rechecked the P1.36 publication ordering: manifest directory fsync precedes receipt creation; no-replace receipt installation precedes commits-directory fsync; lock release follows successful commits-directory fsync.
- Rechecked that historical manifests are recovered from immutable receipt bytes, not the replaceable active `manifest.json`.
- Rechecked that the current v1.1 profile still forbids `RECONCILED_COMPLETE`, canonical sealing/eligibility and completeness-watermark advancement under §22.1.
- No source, executable test, Actions, REST, VPS, filesystem or runtime claim was inferred from this documentation review.

## Residual blockers — unchanged

- F07 target filesystem/mount/device/provider identity and actual `flock`, `renameat2(RENAME_NOREPLACE)`, file-fsync and directory-fsync behavior: NOT VERIFIED.
- Binance REST completeness/no-trade/boundary/pagination/finality/correction semantics: NOT ACCEPTED.
- Pinned producer f64 conversion, fixed 12-decimal formatting and parse-error-to-zero: CONFIRMED / NOT FIXED.
- Producer FINAL_ONLY/product identity implementation: NOT VERIFIED.
- Manifest, receipt, publication counter, recovery checkpoint, recovery-epoch/approval verifier, external trust-policy loader, ERA service, monotonic store and ExchangeInfo evidence store: NOT IMPLEMENTED / NOT VERIFIED.
- C01–C197: contract design scenarios only; NOT IMPLEMENTED / NOT EXECUTED.
- No GitHub Actions run/artifact, executable tests, REST request, VPS/runtime experiment or filesystem durability claim is made.

## Status and guardrails

- F02-R18: corrected at contract level; prior P1.36 DOCUMENTATION-LEVEL PASS retained within its limited scope.
- F02-R19: corrected at contract level; P1.37 DOCUMENTATION-LEVEL PASS.
- F02-R20: corrected as a documentation inventory/status consistency issue; P1.37 DOCUMENTATION-LEVEL PASS.
- Same-session self-review only; independent review remains PENDING.
- Issue #138 must be retargeted only to the exact P1.37 contract and review blobs after this review record is committed and read back. It must remain OPEN for genuinely independent review.
- Implementation and T1 activation: NOT AUTHORIZED.
- No source code, T0/T2, strategy/AI/ledger/risk, trading or data operation changed.
- No destructive data operation or test performed.

T0 remains independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.


---

## P1.38 — Second-pass adversarial review (2026-11-09)

Review type: Fresh second-pass, same-session static adversarial self-review; NOT an independent third-party review.
Exact normative contract blob re-reviewed: `9125e89b227fd9fa8364a02188d0be54ec3dd2ef`.

**Verdict: DOCUMENTATION-LEVEL PASS.** No new actionable P1.37-level contract defect was identified in the directly coupled receipt/checkpoint/recovery rules examined.

This second pass cross-checked §§5.2, 21.5, 22.2, 22.4, 22.6, 22.6.1 and 22.9–22.11, plus C100–C197 and the current implementation-status statements.

Regression checks:
- §22.4 contains exactly twelve receipt keys, including `manifest_jcs_base64url`; the same field is required by §5.2/§21.5 and consumed by §22.11.2/C190–C197.
- The 87,382-character maximum is consistent with unpadded base64url encoding of 65,536 bytes. Decode/re-encode, UTF-8/JCS validation, manifest digest binding and receipt/manifest shared-field matching are specified.
- Receipt byte bounds remain 1–131,072; embedded manifest bytes remain 1–65,536.
- Historical manifest recovery uses immutable receipt-embedded bytes, not the replaceable active `manifest.json`.
- Checkpoints pin exact receipt bytes using `receipt_sha256` and the historical manifest using `manifest_sha256`; recovery epoch is separately bound to initialization and immutable epoch records.
- Publication order retains manifest directory fsync, no-replace receipt installation, commits-directory fsync under the writer lock, and lock release only after success.
- §22.8 and §22.11.5 consistently state C01–C197 are design-only, NOT IMPLEMENTED / NOT EXECUTED.

No new finding was raised. This is a bounded static document-consistency pass, not proof that every historical clause is correct, that the design is implementable, or that runtime durability/completeness is established.

Residual gates unchanged: F07 NOT VERIFIED; Binance REST completeness NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; schemas/services/parsers/fixtures NOT IMPLEMENTED / NOT VERIFIED; C01–C197 NOT IMPLEMENTED / NOT EXECUTED. No Actions, executable tests, REST, VPS, filesystem or runtime experiment was performed.

**Independent review remains PENDING.** A same-assistant review cannot become genuinely independent by being repeated. Issue #138 must remain OPEN. Implementation and T1 activation remain NOT AUTHORIZED. T0 remains independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.
