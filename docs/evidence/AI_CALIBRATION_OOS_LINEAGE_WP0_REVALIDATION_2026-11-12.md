# WP0 — Canonical OOS Bundle Revalidation

Date: 2026-11-12 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Exact inspected source HEAD: `7d5deb084cd7007fa9d120d8fee0ac3858aa6517`
Recursive Git tree SHA: `4384f6e6721628840b843f7c08e98f68ed51705f`
Recursive Git tree entries: 993
Tree response truncated: false
Status: **BLOCKED — canonical OOS bundle contract/payload/producer still not identified**

## 1. Scope

Read-only GitHub inspection only. Re-read `docs/PROJECT_SESSION_HANDOFF.md`, verified branch metadata, inspected the complete recursive Git tree, and re-read the owner authorization, prior WP0 inventory, OOS implementation scope, OOS validator, calibration registry verifier, AI risk policy, and AI Strategy Contract workflow.

No source, tests, workflow, dependency, dataset, database, T0 endpoint, runtime, VPS, exchange, or external provider was changed or accessed.

## 2. Revalidation result at exact current HEAD

- Branch HEAD is exactly `7d5deb084cd7007fa9d120d8fee0ac3858aa6517`; it has not advanced since the owner-authorization commit.
- Complete recursive tree contains 993 entries and is not truncated.
- No tracked path identifies a canonical `T0_M15_H1_DATASET_BUNDLE_V1` schema, manifest, immutable payload, or producer.
- The tree does contain synthetic P1.8 evidence bundles. They are unrelated synthetic verification artifacts and cannot substitute for BTCUSDT canonical research data.
- The prior WP0 inventory at `f012305b9c13d0deb7ec1bdfeda22a2affb7a5d2` is consistent with this current path-level revalidation. It remains a historical static inventory; this note refreshes its exact source/tree baseline.

This is a repository-only finding. It does not prove whether a bundle exists outside the tracked GitHub tree.

## 3. Existing interfaces are not an equivalent bundle contract

- `freqai_bridge/context.py` and `freqai_bridge/http_candles.py` provide bounded read-only T0 M15 candle access for inference. They do not define immutable training/OOS bundle bytes or sample-level lineage.
- Current research strategy/config describes M15 features and a four-candle forward-return label; it does not establish the named M15/H1 bundle, an H1 feature lineage, deterministic sample membership, a three-way train/calibration/evaluation partition, or a frozen horizon-plus-feature-window embargo.
- `pipeline/oos_evaluation.py` remains a structural record validator. It does not independently establish canonical lineage, sample-level embargo, reproducibility, trusted time, statistical acceptability, or admission.
- `pipeline/calibration_registry.py` returns `SIGNATURE_VERIFIED_ONLY`; signature/integrity verification does not establish registry ACTIVE/revocation, trusted time, OOS quality, or trade admission.
- `risk_policy.py` still defines Core leverage 13x and shared order margin budget 1%; it does not define an AI confidence-to-leverage policy or numeric AI admission thresholds.

Relevant current blobs:
- OOS validator: `756f7d2707051cb7f90bd5b7c62ff4d6f269f21d`
- Calibration registry verifier: see branch file `pipeline/calibration_registry.py` (read-only inspection)
- Risk policy: `91b46513041033cbcd7e939ed081b71714c82ff3`
- AI Strategy Contract workflow: `4deebeae9bc33a4bc7aa2a84e57633b0ab5d8b1d`
- Owner authorization record: `8ae71f731fc4a59f1f4174ca0a6122f739ef1988`

## 4. Authorization reconciliation

The 2026-11-12 owner authorization explicitly approves the three work-package categories: OOS lineage/provider and real OOS work; registry ACTIVE/revocation, trusted time and key lifecycle; and AI admission/leverage policy.

That authorization does not permit inventing a missing canonical dataset schema. It explicitly says to stop and request the exact contract decision if the canonical producer/contract/payload cannot be verified. It also excludes T0/T1/T2 changes, canonical data mutation, VPS/runtime/deployment, live trading, and fabricated numeric thresholds.

The older OOS scope proposal's statement that code implementation was not authorized is superseded for the three approved work-package categories by the newer owner authorization. Its technical stop conditions against hypothetical schemas remain applicable.

## 5. Required owner disposition to unblock OOS data work

One of these must be established before WP1/WP2/WP3 can proceed:

1. **Existing bundle route:** identify the authoritative location/reference and approved read-only access method for the already-existing canonical bundle, including how its immutable bytes and producer contract can be verified; or
2. **Derived bundle route:** explicitly authorize a bounded read-only derived bundle specification and producer path that preserves T0 as canonical, including the exact source fields/timeframes, sample identity, timestamp semantics, feature/label windows, canonical serialization and digest domain.

No T0/VPS/database access, export, bundle creation, training, calibration, or real OOS evaluation is implied by this inventory note.

## 6. Disposition

- WP0 repository path inventory: **PASS** at exact HEAD `7d5deb084cd7007fa9d120d8fee0ac3858aa6517`.
- Canonical bundle contract/payload/producer discovery: **BLOCKED**.
- Sample-level lineage, chronological split, embargo, reproducibility and real OOS: **NOT VERIFIED**.
- AI admission eligibility: **false / fail-closed**.
- No source tests or CI workflow were run; this increment is evidence/documentation-only.
- No VPS/runtime, T0/T1/T2, Core, CANCEL, database, ledger, Shared Risk, Kill Switch, or trading behavior changed.

Next: continue the independent registry/trusted-time/key and AI policy contract inventory within the approved scope, while OOS remains stopped at the exact missing bundle decision.
