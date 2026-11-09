# P1.42 — Adversarial self-review: receipt barrier and fixture traceability

Date: 2026-11-09
Review type: Same-session adversarial self-review; NOT an independent third-party review.
Branch: feature/t0-centralized-data-feeder-p1-20261101

## Exact input

- Contract path: docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md
- Previous contract blob: b7b6786125be507c3ad4c29521830e5fe2a3b1b9
- Corrective contract commit: 1557e9080e364d32a313694b5222ead8c790acce
- Corrective contract blob: 3510c6a187c2677e0ad54060d1164a84984705c2
- Issue #138: https://github.com/kenznguyen/btcusdt-telegram-signals2/issues/138

## Review scope

Adversarial review of receipt publication/recovery linearization, directly coupled C84/C103 fixtures, normative precedence, fixture inventory traceability, closed receipt schema, historical manifest binding and stated verification limits.

## Finding F02-R23 — HIGH — RESOLVED AT DOCUMENTATION LEVEL

Before correction, §9 C84 allowed acceptance of a visible receipt before the commits-directory fsync completed. This contradicted §22.6.1, which makes successful fsync(commits_dir_fd) the normal commit-acceptance linearization point and treats a post-crash visible receipt as UNCONFIRMED until the full recovery barrier and durable recovery checkpoint complete.

Correction in contract blob 3510c6a187c2677e0ad54060d1164a84984705c2:
- C84 now prohibits reader acceptance before the commits-directory fsync barrier.
- After crash/restart, C84 requires full §22.6.1 validation, commits/generation directory fsync, durable recovery-checkpoint publication and its directory barriers; otherwise quarantine.
- C103 now states the same recovery requirements and preserves permanent sequence consumption.
- Contract status metadata advanced to P1.42 REVISION — DESIGN ONLY — NOT APPROVED FOR IMPLEMENTATION.

Readback checks:
- Exact blob SHA matches 3510c6a187c2677e0ad54060d1164a84984705c2.
- The previous unsafe C84 acceptance wording is absent.
- C84 explicitly states UNCONFIRMED and no reader may accept before the writer's exclusive-lock barrier.
- C103 requires the complete §22.6.1 recovery sequence and durable recovery checkpoint.
- §22.6.1 still defines successful commits-directory fsync as the only normal commit-acceptance linearization point.
- No changes were made to the receipt schema, checkpoint schema, source-health policy or authorization boundary.

## Finding F02-R24 — MEDIUM — REQUEST CHANGES

§9 line 165 says “Retain C01–C24 from v1 and add”, but this v1.1 contract does not enumerate C02–C23 and does not identify the exact v1 source artifact by repository path, commit SHA or blob SHA. A scan of this 966-line contract finds definitions for C01 and C24 onward, but no definitions for C02–C23. The P1.3 base artifact at commit 0e2cbec07b1289950a7aa7ec1b99ef0ec7f6302c also contains only the instruction to retain C01–C24; it does not supply the missing definitions.

This makes the claimed C01–C197 inventory non-self-contained and prevents a reviewer from verifying completeness, uniqueness, expected behavior and disposition of the inherited C02–C23 scenarios. The missing fixtures must not be reconstructed from memory or invented.

Required correction:
1. Locate the exact original v1 artifact containing C01–C24 and pin its path, commit and blob SHA; or
2. Restore the exact C02–C23 definitions from a verifiable source into the current contract, preserving their original semantics and reconciling any superseded behavior with the current normative profile.
3. Re-run fixture inventory checks for C01–C197, including uniqueness, no missing IDs, and explicit supersession mapping where semantics changed.

Until this is resolved, fixture-catalog completeness is NOT VERIFIED. Do not claim C01–C197 as a fully reviewable/self-contained inventory.

## Cross-checks

- §22.4 receipt schema: exactly twelve keys, including manifest_jcs_base64url.
- §21.5 manifest binding and embedded exact manifest bytes: unchanged.
- §22.11.1–§22.11.3 checkpoint and historical-manifest recovery: unchanged; checkpoint binds exact receipt and embedded manifest, not the replaceable active manifest path.
- §22.10 precedence: §22.6.1 remains the sole recovery acceptance barrier; no weaker fallback is introduced.
- §22.8 still correctly states C01–C197 are design-only and not implemented/executed, but its inventory completeness claim remains blocked by F02-R24.
- No source implementation, executable tests, GitHub Actions dispatch, REST request, VPS/runtime or filesystem experiment was performed.

## Verdict

**REQUEST CHANGES**.

F02-R23 is corrected and passes documentation-level adversarial readback. F02-R24 remains open because C02–C23 have no exact source artifact reference or definitions in the current contract. Overall contract review is not PASS. Issue #138 must not be retargeted to claim a clean PASS until F02-R24 is resolved and a new same-session adversarial pass succeeds; genuinely independent review remains separately required.

## Unchanged blockers and guardrails

- F07 target filesystem/mount/device/provider identity and actual flock, renameat2(RENAME_NOREPLACE), file-fsync and directory-fsync behavior: NOT VERIFIED.
- Binance REST completeness/no-trade/boundary/pagination/finality/correction semantics: NOT ACCEPTED.
- Pinned producer f64 conversion, fixed 12-decimal formatting and parse-error-to-zero defect: CONFIRMED / NOT FIXED.
- Producer FINAL_ONLY/product identity implementation: NOT VERIFIED.
- Manifest/receipt/counter/checkpoint/ERA/trust-policy/ExchangeInfo implementation: NOT IMPLEMENTED / NOT VERIFIED.
- C01–C197: design scenarios only; NOT IMPLEMENTED / NOT EXECUTED; inherited C02–C23 source traceability NOT VERIFIED.
- No Actions run/artifact, executable tests, REST request, VPS/runtime or filesystem experiment is claimed.
- Implementation and T1 activation remain NOT AUTHORIZED.
- T0 remains independent/canonical; no T1 writes to T0; paper-only; AI_EXECUTION_ENABLED=false; no live orders; no OKX fallback/replacement; no destructive data operations.
