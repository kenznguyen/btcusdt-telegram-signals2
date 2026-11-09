# T0 Simplification — Documentation Cross-Reference Review

- Date: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact inspected branch HEAD: `b8b29b806b6bd50839fdd35616eedcebe2c90a84`
- Operation class: READ-ONLY DOCUMENTATION REVIEW
- Scope: verify whether the T0 Active Scope Index is discoverable from maintained repository entry points, and determine whether another navigation layer is justified.
- No source, test, package, workflow, schema, runtime, VPS, database, provider, secret, permission or data changes. No tests or Actions were run.

## 1. Result

**PASS — the active scope index is already linked from both maintained entry points. No additional navigation edit is needed.**

- Root `README.md` links `docs/T0_ACTIVE_SCOPE_INDEX.md` in the architecture/scope introduction.
- `market_data/README.md` links the same index near the beginning and explicitly assigns it responsibility for the overall ACTIVE/PARKED/separate-workstream scope.
- `docs/T0_ACTIVE_SCOPE_INDEX.md` links the scope minimization and second-pass dependency review evidence.

Adding another link or duplicating the scope table would create redundant navigation without improving discoverability.

## 2. Exact source evidence

| Path | Blob SHA | Observed result |
|---|---|---|
| `README.md` | `a542a85cd8404a39d1038d3f234535deb2adf6b4` | Links the T0 index and separates five-layer scope from excluded Android/Python legacy systems |
| `market_data/README.md` | `19485ce933e15433c412a54ab15d9cbc1860dfd7` | Links the T0 index and keeps detailed Candle/API contract in the module README |
| `docs/T0_ACTIVE_SCOPE_INDEX.md` | `70c13603ec4f9d499273f2412c4106fcbc346af2` | Provides canonical active/parked/separate workstream classification and links supporting audits |
| `docs/evidence/T0_SCOPE_MINIMIZATION_REVIEW_2026-11-10.md` | `43c919521352cd3c2b00ba6da891a8675a6c5ed6` | Defines the proposed minimal active T0 responsibility |
| `docs/evidence/T0_SIMPLIFICATION_DEPENDENCY_REVIEW_SECOND_PASS_2026-11-10.md` | `99a372bdf61a775eab61381a52fcb91c81a3a73c` | Defines KEEP/PARK decisions and the next dependency-focused review |

## 3. Reconciled navigation boundary

- Root README: project-level architecture and scope navigation.
- T0 Active Scope Index: canonical T0 scope/disposition summary.
- market_data README: operational Candle/API contract and commands.
- Evidence reports: dated audit findings and limitations.

These documents have complementary roles; no content consolidation is recommended.

## 4. Remaining limitations

- This is a documentation cross-reference review, not proof of source dependency closure.
- Full repository call graph, complete workflow/branch-protection requirements, deployed package/runtime and live consumer inventory remain NOT VERIFIED.
- Existing T0 technical acceptance and L4-Minimum status are unchanged.
- No source retirement, package split, workflow narrowing or runtime change is authorized by this review.

## 5. Status and next step

- Navigation cross-reference: **PASS**.
- Additional README/index edits: **NOT NEEDED**.
- Source dependency/call graph: **NOT VERIFIED**.
- Runtime/deployment/consumer inventory: **NOT VERIFIED**.
- Tests / GitHub Actions: **NOT RUN / NOT DISPATCHED**.
- T0 simplification implementation: **NOT AUTHORIZED**.
- Option C — No Destructive Authority: **ACTIVE**.

Next safe increment: continue a read-only audit of the active SQLite runtime composition, focusing on configuration ownership and duplicated responsibilities. Do not refactor or change behavior until a concrete duplication, complete regression impact and rollback path are demonstrated.
