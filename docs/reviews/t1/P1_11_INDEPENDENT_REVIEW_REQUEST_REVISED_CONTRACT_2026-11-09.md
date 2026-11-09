# P1.11 — Independent review request for revised T1 Source Contract

Date: 2026-11-09
Type: Independent review request only; no independent review received.

## Exact review target

- Normative contract: docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md
- Exact contract blob SHA: 32cf231227c52590ad1365473c6c742ab7dbc64a
- Archival v1 blob SHA: c64d6da7b16e608ef5ccebafabce03e51960cfcc
- P1.9 self-review blob: 8c433a59b6c1e5dd793a82f81616d06cc066883c
- P1.10 same-session review blob: 1abbb75e52df88b354191668ce2b276a322f4411
- Pinned T1 producer source SHA: 6e20fe94f3ad64cc450e73def80a167fe371e49e

## Changes requiring independent challenge

P1.10 updates publication commit ordering using an immutable receipt created only after manifest rename and parent-directory fsync; requires stable kernel advisory writer-exclusive/reader-shared locking; makes generation allocation durable before append; reserves WINDOW_GAP and GAP_DETECTED under current profile; binds FINAL_ONLY to event interval/subscription validation; prohibits symbol-exception bypass; and defines strict JCS manifest, receipt, file identity and path-validation schemas. Planned fixtures now extend through C99.

The reviewer must specifically challenge every crash point, receipt visibility, advisory lock semantics on the intended target filesystem, paused/stale writer behavior, generation rollback/root restore, exact ExchangeInfo evidence, strict manifest schema, C82–C99 completeness and all prior P1.3/P1.5/P1.7 fail-closed rules.

## Issue

- GitHub issue #138: https://github.com/kenznguyen/btcusdt-telegram-signals2/issues/138
- Current title: P1.11 — Independent adversarial review of revised T1 Source Contract
- State at update: OPEN.
- The issue contains exact SHAs, required questions, reviewer output and guardrails. The update is a request, not an independent review or approval.

## Known blockers

- REST completeness oracle NOT ACCEPTED.
- Decimal-preservation defect in pinned producer CONFIRMED and NOT FIXED.
- Target filesystem/provider durability and advisory lock semantics NOT VERIFIED.
- Producer interval/product identity and manifest/receipt implementation NOT VERIFIED.
- C01–C99 are design fixtures only, NOT IMPLEMENTED/EXECUTED.
- Implementation NOT AUTHORIZED; T1 activation NOT AUTHORIZED.

Review request only. No source changes, tests, REST, Actions, VPS/runtime, T0/T2, T1 activation or destructive data operations. Paper-only; AI_EXECUTION_ENABLED=false; no live orders; T0 remains independent/canonical.
