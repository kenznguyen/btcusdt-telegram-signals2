# Android Personal-Use QA and Release Assurance Checklist

**Purpose:** Internal QA, security and release assurance for the owner's personal Android application.

**Operating boundary:** The application is a chart, signal-monitoring and paper-simulation client. It must not place exchange orders or request exchange trading API keys. A successful build or checklist review does not authorize live trading.

## 1. Android QA — M15/H1

- [ ] Verify M15 entry/alert behavior uses fully closed M15 candles and the intended H1 trend context.
- [ ] Verify H1 trend/filter calculations do not consume an incomplete H1 candle.
- [ ] Test LONG and SHORT alert cases, no-signal cases, boundary values and stale/missing candle inputs.
- [ ] Verify alert timestamps, candle open/close times and displayed timeframe labels.
- [ ] Verify alert history persistence, duplicate suppression, bounded history and restart recovery.
- [ ] Verify paper/simulated positions and events are clearly distinguished from real exchange positions and orders.

## 2. Python engine parity

- [ ] Use identical deterministic candle fixtures for Android and Python comparisons.
- [ ] Compare RSI, DMI/+DI/-DI, ADX, trend state and all strategy inputs used by the Android signal engine.
- [ ] Compare LONG/SHORT/NO-SIGNAL decisions, event timestamps and relevant boundary behavior.
- [ ] Document numeric tolerances, fixture identity, expected outputs and any intentional implementation differences.
- [ ] Treat unexplained parity differences as BLOCKED; do not waive them by changing expected fixtures without review.

## 3. Connectivity, background operation and recovery

- [ ] Test normal connection, disconnect, reconnect, timeout, rate-limit response and stale-data handling.
- [ ] Test Android background/foreground transitions, foreground-service restrictions, process termination and device reboot.
- [ ] Test recovery after process restart without replaying obsolete alerts or duplicating events.
- [ ] Test notification permission granted, denied, revoked and restored.
- [ ] Test quiet hours and notification-channel settings where applicable.
- [ ] Record device model, Android version, app version, exact source SHA, test steps, results and unresolved defects.

## 4. Signing key and GitHub Actions secrets

- [ ] Keep the owner-controlled signing keystore and passwords out of Git, source files, logs and artifacts.
- [ ] Store signing credentials only in appropriately protected GitHub Actions secrets; limit workflow access to the required branch/event and job.
- [ ] Never print, upload or expose private signing material. Use restricted temporary runner storage and remove temporary key files after use.
- [ ] Verify the signing alias and expected certificate identity before accepting a signed artifact.
- [ ] Keep debug/test signing separate from the established release signing identity.
- [ ] Do not rotate, replace or migrate the signing identity without a separately approved recovery and compatibility plan.

## 5. Source and APK integrity

- [ ] Build from the exact intended Git commit and record the full 40-character source SHA.
- [ ] Confirm the checked-out commit equals the recorded source SHA used for the build.
- [ ] Verify APK package ID, variant, version code/name and launcher identity.
- [ ] Verify APK signature and compare the signer certificate SHA-256 fingerprint with the expected owner-controlled certificate.
- [ ] Calculate and record SHA-256 for every accepted APK.
- [ ] Bind each artifact's metadata and test evidence to the same source SHA; reject mismatched or incomplete evidence.
- [ ] Retain relevant GitHub Actions run identity, artifact name and test results alongside the source SHA.
- [ ] Do not describe CI success as device validation; record physical-device/emulator test evidence separately.

## 6. Privacy, risk disclosure and third-party attribution

- [ ] Keep the privacy policy and terms accurate for actual app behavior, local persistence, network access and data sharing.
- [ ] Disclose material risks and clearly distinguish paper simulation/research from real trading.
- [ ] Do not imply guaranteed returns, audited performance or exchange endorsement.
- [ ] Preserve third-party source attribution, software licence notices and applicable market-data/provider terms.
- [ ] Reassess privacy disclosures before adding analytics, crash reporting or any new collection/transmission of user or device data.
- [ ] Avoid collecting or transmitting personal data that is not necessary for the app's stated function.

## 7. Conditional public distribution

Public-store and public-distribution obligations are **out of scope for current personal/internal use**. Apply this section only if the owner later explicitly decides to distribute the application publicly.

- [ ] Before public distribution, review then-current store policies, target API requirements, regional legal requirements and required disclosures.
- [ ] Verify publisher identity, privacy-policy publication and store Data safety declarations if required by the chosen distribution channel.
- [ ] Review current platform rules for financial features and market-data branding/attribution.
- [ ] Record the owner's explicit public-distribution decision and the scope of the release review.


## Evidence and status rules

For each completed check, record the exact source SHA, relevant GitHub Actions run and artifact (if any), test/device context, result and evidence location.

Use only:
- **PASS** — supported by recorded evidence tied to the exact source/artifact.
- **BLOCKED** — a required check failed or cannot proceed.
- **NOT VERIFIED** — evidence is missing or insufficient.

Do not infer PASS from a successful build alone. This checklist does not authorize live trading, exchange order placement, changes to canonical T0 data, or weakening of system risk controls.
