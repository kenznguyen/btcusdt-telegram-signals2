# P1.36 — Exact-SHA adversarial self-review: immutable receipt manifest history

Date: 2026-11-09
Review type: Same-session adversarial static self-review; NOT independent.
Branch: feature/t0-centralized-data-feeder-p1-20261101
Exact normative contract blob reviewed: 1957eee80d5f6eb80889506514aaecf4b6a912cb
Prior finding: P1.35 F02-R18 HIGH
Prior review blob: adc899f646b49a18f995689d57bb3c7b27a43533

## Verdict

**DOCUMENTATION-LEVEL PASS for F02-R18 and its directly coupled publication/checkpoint requirements.**

This PASS is limited to the historical-manifest retention contradiction, receipt/checkpoint binding, publication commit ordering and C190–C197 design fixtures. It is not an independent review and does not establish implementation readiness, target-filesystem durability, Binance completeness or runtime safety. It does not supersede any earlier blocker outside this scope.

## P1.35 finding and correction

### F02-R18 HIGH — closed

P1.35 found that the single active `manifest.json` is replaced by later publications while historical recovery checkpoints require their exact manifest bytes to remain verifiable.

P1.36 resolves this at the immutable receipt layer:

1. §5.2 step 7 requires each immutable per-publication receipt to contain both `manifest_sha256` and `manifest_jcs_base64url`, carrying the exact canonical manifest bytes published for that sequence.
2. §21.5 defines the receipt as a closed schema with exact byte bounds, a canonical unpadded base64url alphabet/encoding, decode/re-encode equality, complete manifest-schema validation and exact digest verification.
3. §22.11.2 requires recovery to validate every final receipt and recover each historical manifest from that receipt, not from the replaceable active `manifest.json`.
4. Recovery checkpoints continue to pin exact receipt bytes using `receipt_sha256` and pin the same manifest digest using `manifest_sha256`; their recovery epoch remains independently bound to root initialization and the immutable recovery-epoch record.
5. §5.2 step 9 now requires successful `fsync(commits_dir_fd)` before releasing the exclusive lock, aligned with §22.6.1. A visible but not directory-synchronized receipt cannot be accepted by a reader.
6. C190–C197 cover historical publication replacement, missing/invalid/noncanonical embedded manifests, digest mismatch, schema/binding mismatch, duplicate/conflicting receipt history and crash ordering.

This avoids relying on the active manifest path for historical evidence and retains each publication's exact manifest within its immutable receipt.

## Adversarial checks performed

- Re-fetched the exact contract blob under review: `1957eee80d5f6eb80889506514aaecf4b6a912cb`.
- Checked §5.2 publication order against §22.6.1 commit-acceptance linearization; lock release is after commits-directory fsync.
- Checked §21.5 receipt closed schema against manifest field inventory and receipt/checkpoint digests.
- Checked historical receipt bytes are retained independently of active manifest replacement.
- Checked checkpoint `receipt_sha256` and `manifest_sha256` bind to the same exact receipt/manifest evidence.
- Checked recovery epoch binding is not incorrectly inferred from a manifest/receipt field that their v1.1 schemas do not define.
- Checked manifest and receipt pre-parse byte bounds and base64url maximum encoded length.
- Checked C146–C197 are strictly ascending and appear exactly once: 52 entries, no duplicates.
- Checked C190–C197 are present exactly once; no stale C01–C189 or C137–C189 terminal inventory statement remains.
- Checked that the original C01–C99 and C100–C189 fixture scopes remain in place.

## Residual limitations — unchanged

- F07 target filesystem/mount/device/provider identity and actual `flock`, `renameat2(RENAME_NOREPLACE)`, file-fsync and directory-fsync behavior: NOT VERIFIED.
- Binance REST completeness/no-trade/boundary/pagination/finality/correction semantics: NOT ACCEPTED.
- Pinned producer f64 conversion, fixed 12-decimal formatting and parse-error-to-zero: CONFIRMED / NOT FIXED.
- Producer FINAL_ONLY/product identity implementation: NOT VERIFIED.
- Manifest, receipt, publication counter, recovery checkpoint, recovery-epoch/approval verifier, external trust-policy loader, ERA service and ExchangeInfo evidence store: NOT IMPLEMENTED / NOT VERIFIED.
- C01–C197: contract design scenarios only; NOT IMPLEMENTED / NOT EXECUTED.
- No GitHub Actions run/artifact, executable tests, REST request, VPS/runtime experiment or filesystem durability claim is made.

## Status and guardrails

- P1.35 F02-R18: corrected at contract level; P1.36 DOCUMENTATION-LEVEL PASS for this finding and directly coupled rules.
- Independent review: PENDING. Issue #138 remains the independent review gate.
- Implementation and T1 activation: NOT AUTHORIZED.
- No source code, T0/T2, strategy/AI/ledger/risk, trading or data operation changed.
- No destructive data operation or test performed.

T0 remains independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.
