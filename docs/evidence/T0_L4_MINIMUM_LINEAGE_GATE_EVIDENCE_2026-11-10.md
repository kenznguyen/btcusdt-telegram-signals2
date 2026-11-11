# T0 L4-Minimum — Lineage Gate Evidence Record

Date: 2026-11-10 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

## Scope

Verify the new L4-Minimum GitHub Actions lineage workflow, diagnose failures, and expand repository-only lineage coverage. GitHub-hosted runner only; read-only checkout. No VPS/SSH, canonical SQLite, signer/key, trust-root, artifact retention, T1, PostgreSQL, service, or trading operations.

## Source baseline

- Final checked-out source SHA: `5dc935aa4663bf3b2ccf6075b704189896e45e63`
- Workflow: `.github/workflows/t0-l4-minimum-validation.yml`
- Workflow blob: `c868a786c60b88f1dd30c7e8fd12aab3af4dc221`
- Test: `ci/test_t0_l4_minimum_lineage_contract.py`
- Test blob: `af18ee5ce18bc832519f84b7519beeac56be1400`
- Automation plan blob: `1e057265290b279e5823b0acb8f86df7c8e7a0d3`
- Controlling matrix blob: `75db0d98134fd656d91a8545bc307c56595aebf7`
- Evidence register blob: `cee949666da611a4efca7e7b51aea47ab4b13eff`

## Workflow execution history

| Run | Source SHA | Result | Test result / diagnosis |
|---|---|---|---|
| [42829414892](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42829414892) | `ed82a1cf7bc12429ccc3ddb3c0ab6896f3f854e7` | FAILURE | 6/7; plan referenced stale register blob `c7605704...` instead of `cee94966...` |
| [42829483832](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42829483832) | `d60be930c5b35254fd336de4777ce8058187ed01` | SUCCESS | 7/7 |
| [42829518609](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42829518609) | `0c00055b816e96378ada614236cc05b79e9ef3f5` | SUCCESS | 7/7 |
| [42830499889](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42830499889) | `5b24397773eb957a7efeb0694773b1c0ff446c06` | FAILURE | 10/11; Git blob helper used literal backslash-zero instead of NUL byte |
| [42830696970](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42830696970) | `5dc935aa4663bf3b2ccf6075b704189896e45e63` | SUCCESS | **11/11** |

## Expanded checks

1. Matrix and register references match the current blob SHAs.
2. Recompute Git blob SHA-1 from the checked-out file bytes and compare with the controlling SHA constants.
3. Scan active L4 decision/evidence documents for superseded matrix/register references.
4. Preserve the old register reference only in the explicitly historical non-substitution assessment, which labels the old snapshot historical and says the location requirement is superseded.
5. Verify L4M-01 through L4M-10 are present in both matrix and register.
6. Preserve VPS/GitHub custody boundary, L4M-09 OWNER-WAIVED and L4M-10 owner-only disposition.
7. Workflow path filters include L4 decision/evidence documents so relevant changes rerun the gate.

## Final run artifact

- Job ID: `129879611464`, SUCCESS.
- Artifact: `t0-l4-minimum-lineage-42830696970`
- Artifact ID: `13771616562`
- Size: 1,124 bytes
- Expiry: `2026-11-17T14:06:04Z`
- GitHub Actions upload log SHA-256: `e71871a8872a78d18b3092c087c0de3394d2fe77bb84d732219ed976fac5690e`
- Payload download and independent SHA-256 recomputation: **NOT VERIFIED**. The recorded digest is the upload action's report only.

## Disposition

- L4-Minimum lineage/contract gate: **PASS (11/11, GitHub-hosted CI only)**.
- L4-Minimum aggregate: **BLOCKED / NOT VERIFIED**.
- VPS custody/readback: **NOT VERIFIED**.
- Owner signer/custody assertions: **PENDING EVIDENCE**.
- Artifact inventory/readback collector and canonical SHA-256 manifest: **NOT STARTED**.
- Signature verification and network-disabled offline verification: **NOT STARTED; intentionally deferred** until the artifact inventory/manifest gate is stable.
- L4M-09: **OWNER-WAIVED**.
- Option C — No Destructive Authority: **ACTIVE**.

## Next step

Implement the GitHub-only artifact inventory/readback collector and deterministic SHA-256 manifest as a separate, test-first increment. Require explicit artifact/run allowlisting, source SHA binding, artifact name/ID/expiry capture, exact ZIP byte download and independent digest calculation. Fail closed on missing, expired, substituted, ambiguous or mismatched artifacts. Do not perform signature or offline verification in this increment.

Historical source snapshot note (2026-11-10): this record captures the Evidence Register blob `cee949666da611a4efca7e7b51aea47ab4b13eff` as it existed when this lineage-gate evidence was first assembled. That register revision is superseded by current register blob `4379b5f115c5dac5a2779b857ab8fababf88e4f3`; the old reference is retained only to preserve the exact historical source snapshot, not as a current binding.


## Superseding owner governance decision — Option C revoked (2026-11-11)

The owner revoked **Option C — No Destructive Authority** on 2026-11-11. Any earlier statement in this historical record that Option C is ACTIVE, remains in force, is unchanged/current, or prohibits all destructive authority is superseded. Current status: **REVOKED**.

This revocation removes Option C as a blanket prohibition but does not authorize any particular destructive operation. Deletion, archive, cleanup, expiry, vacuum, compaction, backup/replica removal, export mutation or provider operation still requires a separately explicit, scoped approval with exact target/data class, preconditions, expected effect, dependencies, verification and recovery/rollback plan. T0 canonical data, lease/fencing, ledgers, audit/reconstruction/recovery, custody and trust evidence remain protected unless separately approved. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged. No L4 control or technical-enforcement status is promoted by this decision.
