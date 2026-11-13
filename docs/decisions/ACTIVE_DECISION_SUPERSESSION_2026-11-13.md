# Active Decision Supersession — 2026-11-13

This record clarifies which previously discussed decisions must no longer be treated as active constraints. It does not rewrite or delete historical evidence.

## Superseded / removed from the active decision set

1. **10% margin per order** — obsolete. Do not use it as a current risk limit or implementation requirement.
2. **Maximum 3 or 5 simultaneous positions** — obsolete. Neither value is an active position-count limit. Do not reintroduce either as a default or inferred constraint.
3. **“T2 must not create/use a data source that replaces T0”** — removed as an active architectural decision. Do not present this sentence as a currently binding owner decision or use it as a standalone blocker.

## Decisions that remain distinct

- The currently recorded Shared Risk Engine limit remains **1% account equity margin for a new order**, unless separately superseded by the owner.
- T0's status as an independent canonical data asset and its protection against unapproved mutation/deletion remain in force. Removing the T2/T0 source-replacement rule does not authorize changes to T0 data, storage, runtime, or deployment.
- This supersession does not itself approve a new T2 data-source design, fallback path, synthetic data path, or runtime change. Such implementation still requires its own scoped design/approval and verification.
- Paper-only posture remains in force: `AI_EXECUTION_ENABLED=false`; no live trading or real orders.

## Handoff reconciliation — 2026-11-13

Compared the active `docs/PROJECT_SESSION_HANDOFF.md`, archived `docs/archive/PROJECT_SESSION_HANDOFF_HISTORY_2026-11-10.md`, and this decision record.

- The active handoff's opening governance override says Option C — No Destructive Authority was revoked on 2026-11-11. A later L4-Minimum paragraph still says “Option C — No Destructive Authority remains ACTIVE.” That later sentence is stale and conflicts with the opening override. The opening dated governance override controls; the stale sentence must not be treated as active authority. This conflict is recorded here for correction in the handoff.
- The active handoff's T0 canonical-data protection is a separate protection and remains active. It must not be confused with the removed T2/T0 source-replacement rule.
- Historical T0→T2 G1/G2/G3 CI evidence in the archive remains historical repository-level evidence only. It does not establish current VPS/runtime state, current deployment parity, or authorize deployment.
- Archived SSH preflight/VPS observations are historical. The current handoff states the Scaleway VPS was deleted on 2026-11-11 and no replacement VPS is established; the old observations must not be represented as current runtime status.
- The current Core First workstream and its latest Continuous Runner test/CI status are governed by the current dated addenda in the active handoff, not by older T0/T2 workstream status in the archive.
- This comparison was a targeted governance/evidence reconciliation, not a byte-for-byte audit of every archived file or every historical commit. No historical records were deleted or rewritten.

## Historical record handling

Older documents, backtests, and archived handoffs may continue to contain the superseded 10% assumption, 3/5-position alternatives, or the former T2/T0 restriction as historical context. Preserve those records for auditability. They must not be copied into current requirements without an explicit owner decision.

## Status

- 10% margin/order as active policy: **SUPERSEDED**
- 3/5 simultaneous-position cap as active policy: **SUPERSEDED**
- T2/T0 source-replacement prohibition as active policy: **REMOVED**
- 1% new-order margin limit: **REMAINS ACTIVE**
- T0 independent-asset and no-unapproved-mutation protections: **REMAINS ACTIVE**
- New T2 source architecture: **NOT DECIDED / NOT AUTHORIZED BY THIS RECORD**
- Option C blanket prohibition: **REVOKED; stale contrary sentence in active handoff identified**
