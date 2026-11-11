# T0 Structure Assessment — L4-Minimum Core and Separate L4-Extended Branch

- Date: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Existing branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Branch HEAD observed for this assessment: `4d3945e37d74b8ce81227db3265a80dd85f29c24`
- Current controlling L4-Minimum matrix: `docs/evidence/p1-8/L4-MINIMUM-PROVENANCE-ACCEPTANCE-MATRIX.md`, blob `ed3056d81edfaf163205a172cf5ad22e230d7b41`.
- Scope audit: `docs/evidence/T0_COMPONENTS_OUTSIDE_L4_MINIMUM_AUDIT_2026-11-10.md`, blob `7bfc509b9eb918750b3a25acc18f8d4f989d387f`.
- Owner scope decision: `docs/decisions/D-2026-11-09-L4-PROVENANCE-PERSONAL-SCOPE.md`, blob `6b96c2c37a4989b7ceba291d027a3f8459eecb3b`.
- Assessment type: architecture/branching recommendation only. No branch created and no source, test, workflow, runtime or data changed.

## 1. Executive recommendation

**RECOMMEND: KEEP THE EXISTING BRANCH DEDICATED TO T0 + L4-MINIMUM DELIVERY; DEVELOP L4-EXTENDED ON A SEPARATE FUTURE BRANCH, CUT ONLY FROM A FROZEN L4-MINIMUM PASS BASELINE.**

Do not create or start implementing the L4-Extended branch yet. Current L4-Minimum technical/operational acceptance is BLOCKED / NOT VERIFIED; qualifying independent review is still pending. A branch split now would separate Git history but would not create a verified minimum baseline and could make later integration ambiguous.

The existing branch remains the continuity branch. Do not rename it, rebase it, rewrite history, or create parallel branches for the minimum work.

## 2. Target structure

### A. T0 core — remains the canonical operational data foundation

Keep in the minimum delivery line:
- Binance USD-M BTCUSDT M15/H1 canonical source.
- SQLite canonical storage.
- Single fenced writer/lease and fail-closed recovery/integrity behavior.
- Read-only Candle API and the approved T2 consumer contract.
- Required regression tests and operational safety boundaries.

PostgreSQL/TimescaleDB remains PARKED/PRESERVED, not deleted. Kraken Spot remains separate research. Binance connectivity probe remains support-only. Evidence Object / Checkpoint G0–G3 remains a separate assurance workstream and must not be silently treated as completed by the branch split.

### B. L4-Minimum — mandatory provenance assurance baseline

Keep all ten controls L4M-01–L4M-10 in the current delivery/acceptance line:
1. Owner-controlled evidence custody outside both T0/VPS and GitHub failure domains, including latest-head anchor and outage readback.
2. Signing authority separated from T0 runtime/admin credentials.
3. Exact-object binding and authenticated freshness/latest-head anchor.
4. Deterministic offline verification with separately controlled trust policy.
5. Independent evidence readback/recovery without implying production database restore.
6. Key/trust lifecycle and honest historical trust-at-time semantics.
7. Tamper-evident history, independent manifest/copy and explicit storage-admin assumptions; no unsupported WORM claim.
8. Bounded provenance claims.
9. Competent, genuinely independent reviewer with conflict assessment.
10. Fail-closed per-control and aggregate acceptance on one frozen immutable baseline plus separately retained review disposition.

No L4M control may be moved to the Extended branch merely to make the minimum appear smaller.

### C. L4-Extended — optional additive assurance capabilities

Potential separate branch scope, only when later justified and approved:
- Optional RFC 3161 TSA integration for a specifically defined object and time claim.
- TSA policy/profile and certificate/OCSP/CRL interoperability needed for that selected claim.
- Optional multi-TSA/quorum/failover.
- Dedicated WORM/Object Lock or stronger immutable evidence storage.
- Optional dual-root/Root A–Root B evidence topology and provider-exit assurance.
- Additional timestamp and evidence-root assurance beyond the minimum claim set.

These must remain additive and asynchronous. TSA must not enter the T0 Feeder/canonical write critical path. WORM/evidence storage must not be confused with or imposed on the SQLite canonical candle database. L4-Extended must not weaken, replace or redefine L4M controls.

## 3. Explicit exclusions — do not put everything outside L4-Minimum into L4-Extended

The following are separate workstreams, not automatically L4-Extended:
- PostgreSQL/TimescaleDB backend/provider qualification.
- Public HTTPS front door, DNS, reverse proxy and TLS deployment.
- D2–D4 host/storage power-loss durability qualification.
- Production database restore, RPO/RTO and multi-region DR.
- Kraken Spot or independent market-data-source corroboration; the latter is explicitly outside L4-Minimum.
- T0 Evidence Object / Checkpoint G0–G3 qualification.
- Retention lifecycle, cleanup, TTL, archive, compaction, vacuum, backup expiry or deletion.

These remain separately classified and governed by their own gates. In particular, Option C — No Destructive Authority — remains unchanged; no lifecycle/destructive capability is authorized by this structure proposal.

## 4. Branch strategy

### Phase 0 — current state

- Continue on `feature/t0-centralized-data-feeder-p1-20261101` for T0 core and L4-Minimum only.
- Keep L4-Extended as a documented deferred backlog; no TSA/WORM/provider implementation is pulled into the current branch's acceptance denominator.
- No new branch, cherry-pick, merge, rebase or history rewrite now.
- Complete the corrected L4-Minimum matrix review, implementation evidence, G1–G3 evidence as applicable, and qualifying independent review.

### Phase 1 — freeze the minimum baseline

Create a baseline tag/immutable reference only after:
- all mandatory L4M-01–L4M-10 controls are PASS;
- all required evidence references and test results bind to one frozen baseline;
- the qualifying independent reviewer issues a separate disposition referencing the exact baseline digest;
- aggregate L4-Minimum verdict is PASS.

A documentation PASS or synthetic CI PASS is insufficient.

### Phase 2 — cut the Extended branch

Only after Phase 1, create a branch such as `feature/l4-extended-provenance` from the exact L4-Minimum PASS commit/tag.

Rules:
- L4-Extended changes are isolated to additive modules/contracts/tests/docs.
- Existing T0 canonical storage, Feeder, lease, recovery and Candle API contracts remain unchanged unless a separately reviewed compatibility change is approved.
- L4-Minimum tests and acceptance denominator remain mandatory and unchanged on the Extended branch.
- Extended-specific tests are additive and separately reported.
- No automatic merge back into the minimum line. Merge/cherry-pick requires explicit owner approval, independent review, compatibility evidence and a decision whether the new capability changes any provenance claim.
- If Extended work is abandoned, the minimum branch remains independently buildable and acceptable.

### Phase 3 — optional adoption

Adopt an Extended capability only when there is a concrete personal risk, evidentiary claim or legal requirement that the minimum profile cannot satisfy. Select one capability at a time; do not bundle TSA, multi-TSA and WORM into a single mandatory programme.

## 5. Main risks and mitigations

| Risk | Mitigation |
|---|---|
| Branch split before L4M is accepted creates two incomplete baselines | Cut Extended only from frozen L4M PASS |
| L4-Extended work changes T0 canonical write path | Keep TSA asynchronous and outside Feeder commit path; prohibit coupling by contract |
| “Outside L4M” is misread as “L4-Extended” | Keep PostgreSQL, HTTPS, durability, DR, G0–G3 and lifecycle as separate workstreams |
| Extended branch silently weakens minimum tests | Preserve the full L4M denominator; Extended tests are additive |
| Merge causes acceptance scope creep | No automatic merge; require explicit owner approval and independent review |
| WORM is claimed from GitHub history or CI artifacts | Require actual medium qualification; otherwise claim tamper-evident only |
| TSA signature is treated as proof of durable DB commit | Bind timestamp to the exact defined object/commit boundary; do not infer durability |

## 6. Current status and authorization boundary

- Architecture recommendation: **PASS — proposed target structure**.
- L4-Minimum technical/operational acceptance: **BLOCKED / NOT VERIFIED**.
- Qualifying independent review: **PENDING**.
- L4-Extended implementation: **DEFERRED / NOT STARTED**.
- Branch creation: **NOT PERFORMED; wait for L4-Minimum PASS baseline**.
- Tests: **NOT RUN by this assessment**.
- GitHub Actions: **NOT DISPATCHED**.
- No source/test/workflow/package/runtime/VPS/database/provider/key/trust-root/permission/data changes.
- No PR, merge, branch creation, rebase or history rewrite.
- Option C — No Destructive Authority — remains in force; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders.

## 7. Next gate

Continue L4-Minimum on the existing branch. First reconcile the controlling matrix and its open review findings, then produce exact evidence for each mandatory control and obtain qualifying independent review. Only after aggregate L4-Minimum PASS should the owner authorize cutting `feature/l4-extended-provenance` from that exact accepted baseline.


## Superseding owner governance decision — Option C revoked (2026-11-11)

The owner revoked **Option C — No Destructive Authority** on 2026-11-11. Any earlier statement in this historical record that Option C is ACTIVE, remains in force, is unchanged/current, or prohibits all destructive authority is superseded. Current status: **REVOKED**.

This revocation removes Option C as a blanket prohibition but does not authorize any particular destructive operation. Deletion, archive, cleanup, expiry, vacuum, compaction, backup/replica removal, export mutation or provider operation still requires a separately explicit, scoped approval with exact target/data class, preconditions, expected effect, dependencies, verification and recovery/rollback plan. T0 canonical data, lease/fencing, ledgers, audit/reconstruction/recovery, custody and trust evidence remain protected unless separately approved. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged. No L4 control or technical-enforcement status is promoted by this decision.
