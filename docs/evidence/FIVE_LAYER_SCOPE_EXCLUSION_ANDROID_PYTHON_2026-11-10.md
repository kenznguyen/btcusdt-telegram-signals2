# Five-Layer Scope Exclusion Decision — Android Chart/Scanner and Python Bot/Backtest

- Date: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Decision type: owner-directed scope boundary clarification; documentation only.

## 1. Decision

**Android Chart/Scanner and Python bot/backtest are OUT OF SCOPE of the Five-Layer System.**

They are separate systems/assets that may coexist in the same GitHub repository. Repository co-location does not make them part of T0, T1, T2, T3 or T4.

## 2. Exclusion boundary

The excluded systems must not be treated as any of the following:

- Five-Layer architecture components or responsibilities.
- T0–T4 runtime services, producers, consumers, clients or dependencies.
- Five-Layer deployment, rollout, operational readiness or acceptance requirements.
- Five-Layer data/API/strategy parity, migration or shared-state obligations.
- Required inputs to the Five-Layer test denominator or canonical CI acceptance, except where a clearly documented repository-level shared dependency is independently proven and explicitly scoped.

Their source code, data, build workflows and legacy integrations remain separate repository assets. This decision does not delete, disable, migrate, refactor, or alter those assets.

## 3. Repository and CI treatment

- GitHub continues to store the repository's source and history.
- GitHub Actions remains the canonical workflow runner for the Five-Layer System, subject to the approved CI ownership decisions.
- Android, Python bot/backtest, Telegram and legacy backtest workflows may remain in the repository for their own systems. Their presence or successful execution must not be reported as Five-Layer layer acceptance.
- Codemagic configuration and historical workflows remain legacy/out-of-scope assets; no external account, webhook, credential, trigger or application change is authorized.
- Any shared workflow or dependency that appears to cross this boundary must be mapped and reviewed before changing its path filters, jobs, tests or dependencies. Do not reduce the approved Five-Layer test denominator.

## 4. Authoritative documentation

- `docs/FIVE_LAYER_ARCHITECTURE.md`: architectural exclusion boundary.
- `docs/T0_ACTIVE_SCOPE_INDEX.md`: confirms excluded systems are not T0 dependencies.
- `README.md`: repository-level separation between Five-Layer components and independent systems.
- `docs/PROJECT_SESSION_HANDOFF.md`: records this decision and its implementation boundary.

## 5. Status

- Scope decision: RECORDED.
- Documentation consistency: UPDATED / READ-BACK REQUIRED.
- Source code, data, Android/Python projects, workflow definitions, package files and external Codemagic state: UNCHANGED.
- Tests: NOT RUN.
- GitHub Actions: NOT DISPATCHED.
- Independent review: NOT PERFORMED.
- No deletion, disablement, migration, cleanup or destructive action authorized.

## 6. Future change gate

Any future proposal to integrate either excluded system into the Five-Layer System requires a separate explicit scope decision and dependency/security/data-contract review. Until then, they remain outside Five-Layer architecture, dependency mapping, deployment and acceptance.
