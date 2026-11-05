# Five-layer repository maintenance

## Protected scope

- T0 is an independent canonical data asset. Do not alter production storage,
  feeder activation, lease/fencing, migrations or exchange access without
  explicit authorization and recorded acceptance evidence.
- T1 futures intelligence remains read-only market-data analytics.
- T2 preserves RSI + ADX + Smart DCA Strategy Core and the independent AI
  signal path. Do not bypass Shared Risk Engine / Kill Switch.
- T3 remains paper-only. `AI_EXECUTION_ENABLED=false`; no live order placement.
- T4 is a rebuild target. Preserve its current source/data until a separately
  approved rebuild scope; current PR cleanup uses only a non-blocking boundary
  check.
- Android is the single Five-layer Paper Client. BTC Chart Pro is maintained
  separately.

## Source and CI

- GitHub stores source, branches, PRs and evidence.
- GitHub Actions is the active CI runner. Workflows must test the exact PR head
  SHA and use least-privilege permissions.
- No legacy Telegram command service, Flask dashboard bridge, Codemagic adapter
  or Codemagic workflow is part of this repository runtime.
- The Hummingbot adapter is a separate read-only market-data integration. It
  does not place orders or depend on a dashboard or notification bridge.

## Change acceptance

For each meaningful change, record:
1. Scope and protected boundaries.
2. Tests, checks and evidence.
3. Exact source SHA, workflow run and artifact identifiers/digests when present.
4. PASS / BLOCKED / NOT VERIFIED status.
5. Next step and remaining restrictions.

Commit to the existing task branch where practical. Avoid unnecessary branch
or PR divergence. Do not merge without explicit user approval.

## Recovery and safety

- Preserve backup/restore branches and data until a verified restore procedure
  and archive evidence exist.
- Do not weaken CI gates to obtain a passing result.
- Do not claim production readiness, signer continuity, device installation,
  data freshness or strategy profitability without matching evidence.
