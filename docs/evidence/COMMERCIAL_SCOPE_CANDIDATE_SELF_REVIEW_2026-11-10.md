# Self-review — Android commercial-readiness removal candidate

Date: 2026-11-10 UTC  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Reviewed source: `android-app/COMMERCIAL_READINESS.md`  
Source blob: `9532b34f4a7c1dcac571b9ba4fe5064fa2cfc324`

## Review question

Is the complete file exclusively commercial functionality/documentation and safe to delete under the personal-use scope?

## Result: REJECT WHOLE-FILE DELETION

The previous Phase-3 audit correctly identified commercial/public-store material, but its REMOVE CANDIDATE classification was too broad. The document is mixed-purpose:

### Retain as personal-system assurance / internal release engineering

- Device QA for M15/H1 alerts, reconnect, quiet hours, notification permissions and process termination.
- Indicator/event timestamp parity against the Python engine using identical candle fixtures.
- Performance, accessibility, screen-size, localization, startup and recovery checks.
- Signing-key custody, protected CI secrets, debug/release artifact separation, signature and SHA-256 verification.
- Install/upgrade/data migration testing and versioning/rollback hygiene where APK distribution is still used.
- Privacy policy, risk disclosure, source attribution/licence notices and provider terms checks where applicable to the personal app.

These controls are not inherently commercial. Removing them would weaken reliability, software supply-chain security, privacy or owner assurance.

### Commercial-only material that can be removed or rewritten

- Public store submission and store listing requirements that are only relevant to public distribution.
- Paid/free feature decisions, pricing, refunds, customer support coverage and paid commercialization rollout.
- Closed beta/customer feedback and public-production rollout steps, unless separately retained as internal test/release practices.
- Publisher/customer-facing contact and public release obligations only where not required by actual distribution channel or law.

Even these lines require context-sensitive pruning: store policy/legal obligations may apply if the owner actually distributes the app publicly; they are not automatically obsolete merely because the system is personal-use.

## Corrected disposition

- Whole-file deletion: **REJECT**.
- Better option: replace the mixed document with a personal-use Android QA, security and internal-release checklist; remove only clearly commercial/customer/store commercialization tasks.
- Exact path may remain `android-app/COMMERCIAL_READINESS.md` with a new internal-purpose title/content, or be renamed only after reference/dependency search.
- No edit or deletion performed in this review.
- Previous Phase-3 REMOVE CANDIDATE classification is superseded by this review.

## Scope and limitations

This is a self-review by the same assistant that produced the earlier audit, not an independent second review. It must not be represented as independent reviewer acceptance. This review inspected the full candidate document and the existing personal-use scope decision; it did not perform a repository-wide reference/dependency search for this path.

No tests run, no GitHub Actions dispatched, no artifacts created. No source, runtime, data, credential, key, permission or workflow changes.