# Android checklist pruning proposal — 2026-11-10

## Decision sought

Replace the mixed-purpose `android-app/COMMERCIAL_READINESS.md` with a personal-use QA and release-assurance checklist. Do not delete the existing file wholesale.

## Evidence inspected

- Candidate source blob: `9532b34f4a7c1dcac571b9ba4fe5064fa2cfc324`.
- `android-app/README.md` blob: `0289d6a94ca70d2eeacef8b6ebedf40ca31aa3d9`.
- `.github/workflows/android-release-pair.yml` blob: `b6f6b3deccc01f27fb3c00b0bb5657033508be5c`.
- `ci/release-android.sh` blob: `bea2164a5a264f4cda8bd47908f5e61805f86ab9`.
- `ci/setup-android.sh` blob: `2a122c3b9385f74722292841e6d5f2067a159d92`.
- `ci/verify-android-apks.py` blob: `9131207cdcc2fcda95b3aae2a6d97cb5255c6e9c`.
- `ci/test_android_apks.py` blob: `8a2bf3b1d3b173c8ec67c1e88541fa43f1cd316d`.

## Findings

1. Candidate contains essential personal-use QA, Python parity, Android lifecycle/recovery, signing custody, artifact integrity, privacy and attribution checks. Whole-file deletion would remove these controls.
2. Existing Android README and CI tooling confirm exact-source build evidence, signer checks, APK identity checks and unit-test gates are relevant engineering controls, not merely commercial functionality.
3. Public-store, paid rollout, pricing/refunds, customer support and customer-facing commitments are commercial/distribution-specific. Keep only conditional public-distribution compliance language if that distribution path is ever chosen.
4. The Android README currently describes Codemagic as the build/test execution platform, while the current owner direction says GitHub Actions is primary and Codemagic is deprecated/legacy fallback. This is a separate documentation consistency issue. Do not silently rewrite it as part of this candidate pruning without a separate scoped review.
5. GitHub code search only covers the default branch; therefore search results cannot prove absence of references on this feature branch. The current branch tree was inspected (640 tracked blobs, not truncated); no exhaustive content-level reference/dependency proof has been completed.

## Proposed replacement content

The complete proposed replacement is recorded below. It is intentionally limited to personal-use QA, release engineering, privacy/data obligations and conditional public distribution. No source edit is made by this proposal.

# Proposed replacement — Android Personal-Use QA and Release Assurance

Status: PROPOSAL ONLY — NOT APPLIED  
Date: 2026-11-10 UTC  
Replaces conceptually: `android-app/COMMERCIAL_READINESS.md`  
Current source blob: `9532b34f4a7c1dcac571b9ba4fe5064fa2cfc324`

## Purpose and operating boundary

This checklist supports the owner's personal/internal Android application. The app is a chart, signal-monitoring and paper-simulation client; it does not place exchange orders and must not request exchange trading API keys.

## Product and device QA

- [ ] Test M15/H1 alerts against deterministic, fully closed candle fixtures.
- [ ] Compare indicators, signal decisions and event timestamps with the Python engine using identical input data and documented tolerances.
- [ ] Test reconnect, stale-data handling, quiet hours, notification permission denial, process termination, device reboot and Android background/foreground-service restrictions.
- [ ] Verify alert history persistence, duplicate suppression, restart recovery and bounded local history.
- [ ] Verify simulated/paper state is clearly labeled and cannot submit exchange orders.
- [ ] Test supported Android versions, screen sizes, accessibility, localization, startup and recovery.
- [ ] Record device/OS/build/source SHA, test fixture identity, outcomes and unresolved defects for each meaningful test session.

## Build and release engineering

- [ ] Build from an exact, clean Git commit; record full source SHA and toolchain versions.
- [ ] Keep debug/test artifacts distinct from signed release artifacts.
- [ ] Store signing credentials only in protected GitHub Actions secrets; never commit keystores, passwords or private signing material.
- [ ] Use the owner-controlled existing signing identity; verify APK signer certificate fingerprint against the expected certificate before accepting a release artifact.
- [ ] Record SHA-256, package ID, version, signer fingerprint and source SHA for each accepted artifact.
- [ ] Ensure temporary signing material is restricted and removed after the build.
- [ ] Test install, upgrade, uninstall/reinstall and local-data migration on supported Android versions.
- [ ] Keep versioning, changelog, rollback/recovery notes and reproducible build evidence.
- [ ] Do not describe a build as device-validated or release-ready based only on a successful CI build.

## Privacy, data and third-party obligations

- [ ] Keep the privacy policy and terms accurate for actual app behavior, local persistence, network access and data sharing.
- [ ] Disclose material risks and clearly distinguish paper simulation from real trading.
- [ ] Preserve source attribution, third-party license notices and applicable market-data provider terms.
- [ ] Do not imply guaranteed returns, audited trading performance or exchange endorsement.
- [ ] Revisit privacy/consent disclosures before adding analytics, crash reporting or any new data collection.
- [ ] If public distribution is later chosen, separately review then-current store, regional legal and platform requirements before distribution; this is conditional and does not imply a current public-release plan.

## Explicitly excluded from this personal-use checklist

- Pricing, paid/free feature packaging, subscription or payment processing.
- Refund policy and customer billing.
- Customer support tiers, customer onboarding, licensing and customer account provisioning.
- Commercial beta/customer rollout, sales claims and commercial service commitments.
- Public-store listing and marketing work unless the owner separately chooses public distribution.

## Acceptance rule

A checklist item is PASS only with evidence tied to the exact source SHA and artifact/device context. Otherwise mark BLOCKED or NOT VERIFIED. No checklist result authorizes live trading, exchange order placement, changes to canonical T0 data, or weakening of system risk controls.


## Proposed disposition

- Whole-file deletion: REJECT.
- Exact source path: retain `android-app/COMMERCIAL_READINESS.md` and replace its content only after review/approval; retaining the path avoids unnecessary rename/reference churn.
- Remove only clearly commercial/customer-specific material.
- Preserve internal QA, signing-key custody, CI secret hygiene, artifact integrity, privacy, risk disclosure and attribution.
- Independent second review: REQUIRED and NOT YET PERFORMED.
- Owner approval for applying the replacement: NOT YET GIVEN in this proposal.
- Tests: NOT RUN. GitHub Actions: NOT DISPATCHED. Artifacts: none.
- No source, runtime, VPS, database, data, credentials, keys, permissions or workflows changed.
