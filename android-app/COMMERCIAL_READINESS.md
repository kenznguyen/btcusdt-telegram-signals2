# BTCUSDT Chart Pro — Commercial Readiness Checklist

**Current state:** Pre-release / internal testing. The CI debug APK is not a signed production release.

## Product scope

- [x] Signal-only chart and simulation product; no order placement.
- [x] Bollinger Bands (20, 2) on the live chart.
- [x] Chart-specific alert controls, local alert history and basic history statistics.
- [x] Standalone RSI M15 threshold notification feature removed.
- [x] Volume Profile removed.
- [ ] Device QA for M15/H1 alerts, reconnect, quiet hours, notification permission and process termination.
- [ ] Compare indicators and event timestamps with the Python engine on identical candle fixtures.
- [ ] Verify performance, accessibility, screen sizes, localization and app startup/recovery.
- [ ] Add a user-facing error/help flow for stale data, connection loss and notification permission denial.

## Release engineering

- [ ] Set the final application ID and publisher-owned signing key strategy before first public release. Changing application ID later creates a separate app; losing the signing key can prevent updates.
- [ ] Store signing credentials only in protected CI secrets; never commit keystores or passwords.
- [ ] Create a release workflow that assembles a signed AAB/APK only when protected signing secrets are available.
- [ ] Test installation, upgrade, uninstall and data migration on supported Android versions.
- [ ] Keep debug artifacts separate from production artifacts; verify the signature and SHA-256 of each release.
- [ ] Establish versioning, changelog, rollback and support procedures.

## Store and legal requirements

- [ ] Publish a final privacy policy at a stable public HTTPS URL with publisher identity and contact details.
- [ ] Review current Google Play policies, Data safety declarations, financial-feature classifications and target API requirements before submission.
- [ ] Provide terms of use, risk disclosure, source attribution/licence notices and a support contact.
- [ ] Do not imply guaranteed returns or call simulated results audited trading performance.
- [ ] Review Binance name/logo usage and the market-data provider's applicable terms; do not imply endorsement.
- [ ] Decide supported regions, age rating, languages, paid/free features, refund policy and customer support coverage.
- [ ] If collecting payments or adding analytics/crash reporting later, update privacy disclosures and consent flows as required.

## Suggested staged rollout

1. **Internal alpha:** install debug builds only; test alert correctness and device/background behavior.
2. **Closed beta:** signed release candidate, crash/bug triage, documented feedback channel and no unsupported performance claims.
3. **Store review:** complete legal/policy checks, production signing, store listing, screenshots, privacy URL and Data safety declarations.
4. **Limited production:** staged rollout with monitoring and a rollback plan.
5. **Paid commercialization:** introduce pricing only after support, refunds, licensing, privacy and store billing requirements are settled.

This checklist is operational guidance, not legal advice or a claim that the app already meets store requirements.
