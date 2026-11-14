# PAPER Ledger Evidence Gap Register — 2026-11-14

## 1. Scope and disposition

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Active branch: `feature/core-operational-proof-20261112`
- Baseline branch HEAD before this documentation commit: `0bbfbf054baf0c0bf8bfc10c1ff84f9298e5b359` (verified from the branch ref).
- Scope: documentation-only inventory of evidence and prerequisites for a future PAPER Ledger readiness assessment.
- Current overall disposition: **BLOCKED / NOT VERIFIED**.
- No VPS/SSH/read-only inspection, source synchronization, configuration creation, database access or creation, migration, bootstrap, preflight execution, Runner/One-shot/Continuous Runner, T0 access, credential operation, exchange request, live execution or real order occurred.
- No source-code or workflow changes are included. No tests or CI were run for this documentation-only register.

This register distinguishes (a) source contract facts, (b) missing owner/environment evidence, and (c) prohibited inferences. A missing evidence item is not proof that the underlying object does not exist or that a configuration is wrong.

## 2. Source contracts reviewed

| Source | Blob SHA | Relevant contract |
|---|---|---|
| `core_runtime/preflight.py` | `70f6237ccc701555bc9add51962e08eb1c8e454c` | Exact config schema; PAPER mode; JSON boolean AI disabled; explicit ledger path; no exchange credentials; existing ledger; account risk snapshot must be ready unless explicitly in diagnostic mode |
| `core_runtime/ledger_path_guard.py` | `f5b260165de7a5dd840f6d53a0e5ac59ee3ab328` | Reject T0 database/lease aliases and overlaps; PAPER_DB/PAPER_TRADING_DB aliases must match the configured ledger |
| `paper_execution/bootstrap.py` | `2a75724d0071ecc340617bfc52f4198c09926c92` | Fail-closed new-account bootstrap; exact manifest; evidence byte/hash/content binding; funding reconciliation; equity cutover; owner declaration; dual-ledger readiness and risk snapshot |
| `paper_execution/funding.py` | `03122cc7ddd81f284093bfea1daf5dbec5d9b02b` | Append-only funding provenance/coverage, immutable evidence, reconciliation and cutover persistence |
| `paper_execution/owner_attestation.py` | `5032cc32264f2603f541db0606a03a7131d579a2` | Manual owner declaration binds source/snapshots/hashes; explicitly does not authenticate owner identity, source authenticity, truth, freshness, completeness or privileged authorization |

These are GitHub source-file blob identities observed during this review. They are not evidence that the same code is deployed on any host.

## 3. Gap register

### G-01 — Exact deployed source identity and parity

- **Status:** BLOCKED / NOT VERIFIED.
- **Known evidence:** The prior source audit recorded owner-reported VPS SHA `9aac55b60bec0180cf639086139fc95bf4dabd32`, 43 commits behind the then-audited GitHub HEAD `c5903f2165bc8315ecbf9ba956de193e00d1ff76`.
- **Gap:** No current deployment source identity has been established. The earlier comparison is historical and must not be described as a current host observation.
- **Acceptance evidence:** A separately authorized, source-matched verification record that identifies the exact deployed commit and its relation to the approved GitHub source. This register does not authorize VPS inspection or synchronization.
- **Prohibited inference:** GitHub branch HEAD or CI PASS does not prove deployed source parity.

### G-02 — Core PAPER configuration

- **Status:** NOT VERIFIED.
- **Source contract:** `core_runtime/preflight.py` accepts exactly one of:
  - Base keys: `mode`, `ai_execution_enabled`, `ledger_path`.
  - Runner keys: the base keys plus `risk_limits`, `max_book_age_ms`, `max_position_base`.
- **Required values:** `mode == "PAPER"`; `ai_execution_enabled` is the JSON boolean `false`; non-empty explicit ledger path. Unknown or missing keys fail closed. Relative paths resolve against the config file's parent.
- **Additional runtime boundary:** No non-empty `BINANCE_API_KEY`, `BINANCE_API_SECRET`, `OKX_API_KEY`, or `OKX_API_SECRET`; environment `AI_EXECUTION_ENABLED` must remain false. The dedicated ledger preflight requires the environment variable to be explicitly false.
- **Gap:** No verified Core deployment config and no current source-matched environment evidence.
- **Acceptance evidence:** Exact config bytes and SHA-256, schema/value validation against the source SHA, and separately authorized confirmation of relevant environment state. Secrets must never be copied into this evidence register.
- **Prohibited inference:** A research/FreqAI config is not a Core Runner config; absence of variable names in a historical listing is not proof of current runtime values.

### G-03 — Ledger target identity and isolation

- **Status:** NOT VERIFIED for any actual target; source contract PASS at the reviewed source.
- **Source contract:** Target must be explicit, an existing regular non-symlink file for read-only inspection, and isolated from `MARKET_DATA_DB` and `T0_FEEDER_LEASE_DB` by equality, same-file alias and parent/child overlap checks. Configured `PAPER_DB` and `PAPER_TRADING_DB` must resolve to the same canonical Ledger path.
- **Gap:** No actual approved Ledger path has been evidenced in a verified deployment configuration.
- **Acceptance evidence:** Config-bound canonical path record plus protected-path isolation result, collected only under a separately authorized scope.
- **Prohibited inference:** Do not inspect, open, create, migrate, repair, checkpoint, vacuum, copy or otherwise touch T0 to establish this gate.

### G-04 — Actual PAPER Ledger existence and schema readiness

- **Status:** NOT VERIFIED.
- **Source contract:** Readiness requires an existing database, expected dual-ledger migrations/tables, separate strategy scopes, PAPER account state, `liveTradingSupported == false`, and `riskReady == true`. Read-only inspection must not create a missing database.
- **Gap:** No verified artifact proves an actual Ledger exists at the intended path or has the required schema/state.
- **Acceptance evidence:** A bounded, separately authorized read-only inspection result tied to exact deployed source SHA and exact canonical path, without changing database state.
- **Prohibited inference:** CI fixtures and disposable SQLite integration tests do not prove an actual environment Ledger exists or is ready.

### G-05 — Initial PAPER capital and account funding basis

- **Status:** MISSING.
- **Source contract:** Bootstrap requires a positive `initialCapitalQuote` and evidence whose exact bytes, SHA-256, snapshot ID and expected content match the manifest.
- **Gap:** No accepted account-specific initial-capital snapshot or source record is available in the reviewed evidence.
- **Acceptance evidence:** Genuine account-level PAPER funding declaration/snapshot with amount, USDT denomination, observation time, source identity, snapshot ID and exact payload hash; its relationship to the PAPER account must be clear.
- **Prohibited inference:** Market candles, funding-rate CSVs, synthetic fixtures, guessed capital, or a manually typed amount alone do not prove account funding.

### G-06 — Funding-event population and reconciliation

- **Status:** MISSING / BLOCKED.
- **Source contract:** Bootstrap requires funding coverage with a declared expected population and a persisted reconciliation whose status is `COMPLETE_WITHIN_DECLARED_POPULATION`. The manifest binds funding source, snapshot, time window and payload hash.
- **Gap:** No valid account-level funding cashflow evidence and independently supportable expected population/reconciliation are present.
- **Acceptance evidence:** Exact source snapshot and declared population for the relevant PAPER account and time interval; a reconciliation that matches the contract and does not overclaim global completeness.
- **Prohibited inference:** Funding-rate observations are not funding cashflows. An empty expected population is not acceptable merely because it makes reconciliation easy; its scope must be justified by genuine evidence.

### G-07 — Equity cutover snapshot

- **Status:** MISSING.
- **Source contract:** Bootstrap requires a cutover snapshot bound to initial capital, realized PnL, fees, funding, account equity, mark price, candle close time, observed time, dataset version, funding coverage start, source and config version. The present bootstrap path expects the initial cutover to reconcile with zero realized PnL, zero fees, zero funding and account equity equal to initial capital.
- **Gap:** No genuine cutover snapshot or evidence supports those exact initial-state assumptions.
- **Acceptance evidence:** Account-specific snapshot with exact bytes/hash, snapshot ID, valuation mark/time, dataset identity and arithmetic reconciliation of all equity components. If any initial-state assumption is false, do not force it into this bootstrap contract; stop for a separately reviewed contract decision.
- **Prohibited inference:** A market mark alone is not account equity evidence.

### G-08 — Owner declaration bound to evidence

- **Status:** MISSING.
- **Source contract:** Manual owner attestation must bind exact source SHA, funding snapshot/hash and cutover snapshot/hash, with reviewed time within the manifest time window.
- **Gap:** No attestation tied to genuine accepted funding and cutover evidence is present.
- **Acceptance evidence:** A human declaration over the exact reviewed evidence package and source SHA.
- **Limit:** The implementation explicitly reports owner identity NOT_AUTHENTICATED, source authenticity NOT_VERIFIED, factual truth NOT_VERIFIED, completeness NOT_VERIFIED, freshness NOT_VERIFIED and privileged action authorization NOT_GRANTED.
- **Prohibited inference:** Owner declaration is not an independent signature, issuer authentication, completeness proof or bootstrap/Runner authorization.

### G-09 — D07 provenance limitation

- **Status:** CLOSED — NOT_VERIFIED; not an active acquisition task.
- **Known disposition:** D07.8 package structure and byte identity are valid only within its recorded package boundary. D07.9 V2 remains an explicit-unknown historical draft. D07.11 Stage A inventory/threat model is complete within reviewed evidence. Upstream origin, collector identity/execution, pre-ChatGPT custody, independent issuer/custodian, authenticity, global completeness and factual truth remain NOT_VERIFIED. D07.2 remains BLOCKED_SHARED_LINEAGE. D07 provenance path is CLOSED — NOT_VERIFIED.
- **Impact:** D07 material cannot be promoted into account funding provenance or used to satisfy G-05/G-06 by inference.
- **Boundary:** Do not restart acquisition, network retrieval, VPS/filesystem search, Stage B, key generation, signing, index/resolver work or implementation under this register. Reopening requires a new explicit owner decision based on genuinely new evidence.

### G-10 — Source-matched readiness and Runner authorization

- **Status:** NOT RUN / NOT AUTHORIZED.
- **Gap:** No actual Ledger readiness result exists, and no separate One-shot execution approval has been given.
- **Acceptance sequence:** Close applicable evidence gaps; evaluate bootstrap eligibility; if separately authorized, create a new PAPER Ledger using the fail-closed bootstrap contract; verify readiness; then request a separate, bounded One-shot approval. Continuous Runner remains a later, separate gate.
- **Prohibited inference:** Passing source tests, preparing this register, or accepting an owner declaration does not authorize bootstrap, One-shot, Continuous Runner, systemd/autostart, exchange access, AI execution or live orders.

## 4. Critical path and dependency order

1. Resolve whether genuine account-specific initial-capital evidence can be supplied (G-05).
2. Establish account-specific funding cashflow and a defensible expected population/reconciliation (G-06). Do not reuse D07 market-data material as account cashflow proof.
3. Establish a matching initial equity cutover snapshot (G-07).
4. Bind the exact evidence and source SHA in a manual owner declaration, preserving its stated non-claims (G-08).
5. Separately settle exact deployment source/config/path evidence under an explicitly authorized scope (G-01 through G-03). This register does not authorize VPS inspection or synchronization.
6. Only after the evidence is accepted, make a separate decision on whether bootstrap is eligible. Bootstrap itself is not authorized by this register.
7. After a Ledger exists, readiness inspection and One-shot/Runner authorization remain separate gates (G-04 and G-10).

## 5. Current gate summary

| Gate | Status | Can this register close it? |
|---|---|---|
| GitHub source contracts | PASS for reviewed source only | Recorded; no deployment claim |
| Deployed source parity | BLOCKED / NOT VERIFIED | No |
| Core PAPER deployment config | NOT VERIFIED | No |
| Actual Ledger path/existence/schema | NOT VERIFIED | No |
| Initial capital evidence | MISSING | No |
| Funding population/reconciliation | MISSING / BLOCKED | No |
| Equity cutover evidence | MISSING | No |
| Bound owner declaration | MISSING | No |
| D07 provenance | CLOSED — NOT_VERIFIED | No; reopening requires new owner decision |
| Actual Ledger readiness | NOT VERIFIED | No |
| Runner runtime | NOT RUN / NOT AUTHORIZED | No |

## 6. Explicit non-actions and next decision

This document records gaps only. It does not authorize or perform:
- VPS or SSH access, including read-only parity checks;
- source synchronization or deployment;
- configuration or environment creation/change;
- Ledger creation, bootstrap, migration, inspection, repair or deletion;
- T0 access or mutation;
- D07 provenance reopening or further data acquisition;
- One-shot, Continuous Runner, service/autostart or systemd;
- exchange credentials, exchange connectivity, AI execution, live trading or real orders;
- cleanup, retention, vacuum, compaction or deletion.

**Recommended disposition:** retain PAPER Ledger as **BLOCKED / NOT VERIFIED**. The next substantive owner input should be genuine account-specific initial-capital and funding/cutover evidence, not a fabricated manifest or synthetic placeholder. If such evidence is unavailable, keep the Ledger blocked and proceed with design/research work that does not depend on a funded PAPER account.
