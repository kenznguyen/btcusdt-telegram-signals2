# P1.40 — Adversarial self-review: issue #138 target integrity

Date: 2026-11-09
Review type: Same-session adversarial process/evidence review; NOT independent.
Branch: feature/t0-centralized-data-feeder-p1-20261101

## Exact inputs

- Contract path: docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md
- Contract blob SHA: b7b6786125be507c3ad4c29521830e5fe2a3b1b9
- Contract update commit: c96f56ae6e583e7fe15f420f5a0f78d3df0fc0c6
- Review path: docs/reviews/t1/P1_38_SELF_REVIEW_CONTRACT_REVISION_METADATA_2026-11-09.md
- Review blob SHA at inspection: 920ac39b53c90f591bb6d1164ddac86ec5c99029
- Handoff blob SHA at inspection: 7b2eac4bf1622433eb6d6d566570fbc399e91039
- Issue: https://github.com/kenznguyen/btcusdt-telegram-signals2/issues/138

## Verdict

**REQUEST CHANGES — F02-R22 HIGH.**

### F02-R22 HIGH — Issue #138 body did not carry the claimed current review target

The issue title was P1.38, but its fetched body still began with the historical P1.34 target and contained the old P1.34 contract SHA. The body did not contain the P1.38 exact contract/review SHA as its authoritative target. Therefore the previous claim that issue #138 had been retargeted was not supported by the actual issue body readback.

This is a process/evidence integrity defect: an independent reviewer following the issue could review the wrong contract. A title-only update is insufficient. The issue body must be replaced with a single unambiguous current target, exact blob SHAs, required scope, known blockers and guardrails, then fetched again to verify the persisted body. Historical target records may be linked from handoff/review history, but must not remain as competing instructions in the active issue body.

### Corrective action

- Replace issue #138 body with one authoritative P1.40 target section.
- Pin exact contract blob SHA `b7b6786125be507c3ad4c29521830e5fe3b1b9` only if readback confirms it; otherwise use the actual fetched SHA.
- Pin this review record's exact blob SHA after commit/readback.
- Verify issue title, OPEN state, body target SHAs and absence of stale P1.34/P1.37/P1.38 current-target instructions.
- Update handoff with exact issue-body readback and all relevant commit/blob SHAs.

## Rechecked boundaries

The contract remains DESIGN ONLY / NOT APPROVED FOR IMPLEMENTATION. Existing P1.37/P1.38/P1.39 documentation-level findings do not constitute independent review or implementation readiness.

Unchanged blockers:
- F07 target filesystem/mount/device/provider identity and actual flock, renameat2(RENAME_NOREPLACE), file-fsync and directory-fsync behavior: NOT VERIFIED.
- Binance REST completeness/no-trade/boundary/pagination/finality/correction semantics: NOT ACCEPTED.
- Pinned producer f64 conversion, fixed 12-decimal formatting and parse-error-to-zero: CONFIRMED / NOT FIXED.
- Producer FINAL_ONLY/product identity implementation: NOT VERIFIED.
- Schemas/services/parsers/evidence stores and C01–C197 fixtures: NOT IMPLEMENTED / NOT VERIFIED; C01–C197 NOT EXECUTED.
- No GitHub Actions run/artifact, executable tests, REST request, VPS/runtime or filesystem experiment is claimed.

No source implementation, test execution, Actions dispatch, REST request, VPS/runtime, T0/T2 change, T1 activation, trading action or destructive data operation is authorized or performed. T0 remains independent/canonical; paper-only; AI_EXECUTION_ENABLED=false; no live orders.
