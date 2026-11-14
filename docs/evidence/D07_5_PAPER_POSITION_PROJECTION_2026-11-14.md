# D07.5 — PAPER Position Projection from Cutover and Execution History

Date: 2026-11-14  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Disposition: **PURE PROJECTION + READ-ONLY SQLITE ADAPTER CI PASS / END-TO-END FUNDING RECONCILIATION PENDING**

## Scope

Added a pure, fail-closed projection that converts immutable per-strategy cutover snapshots, execution-journal FILL events and declared VERIFIED EXECUTION coverage into as-of position snapshots at funding settlement times. Output matches the position input contract consumed by `funding_model.py`.

No database is opened or mutated by this pure function. No VPS, T0, production database, exchange credentials, real account data, network access, orders or runtime scheduler are used.

## Contract

Added:
- `paper_execution/funding_position_projection.py`
- `paper_execution/test_funding_position_projection.py`

The projector:
- requires exactly one cutover snapshot for each of `STRATEGY_CORE`, `AI_FREQAI`, and `LEGACY_UNATTRIBUTED`, all from the same cutover and timestamp;
- validates the cutover snapshot canonical payload against its stored fields;
- validates execution event canonical JSON and recomputes each event SHA-256;
- replays only FILL events strictly before each settlement; unsupported event types fail closed;
- requires contiguous, non-overlapping, declared VERIFIED EXECUTION coverage from the cutover timestamp through settlement+1ms;
- rejects late events, events recorded beyond the coverage watermark, invalid fee currency, missing coverage, gaps, future evidence and fills exactly at settlement (ambiguous ordering);
- derives deterministic position snapshot IDs from cutover, included event hashes and coverage evidence;
- returns signed position quantities as of each settlement, suitable for the PAPER funding model.

The change to `account_history.replay_ledger_events` is backward-compatible: UTC-day alignment remains required by default; the projector explicitly opts out because funding settlements occur at intraday timestamps.

## Exact-source CI evidence

- TDD RED: run [43522055968](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43522055968), source `42c0a266f46ebb7de4cfa4a2b9354a3aacccccfb`, failed because the projector implementation had not yet been added.
- Final GREEN: run [43522246798](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43522246798), SUCCESS, source SHA `5348e42f508c4864c7629121a4b5356cc68be855`.
- Focused position projection tests: **19/19 PASS**.
- Funding model tests: **19/19 PASS**.
- Binance public funding parser tests: **19/19 PASS**.
- D07.2 provenance tests: **17/17 PASS**.
- Full PaperLedger regression: **540/540 PASS** in 140.597s.
- Artifact `14084001315`, name `dual-ledger-bootstrap-proof-5348e42f508c4864c7629121a4b5356cc68be855`, 16,012 bytes, GitHub ZIP digest `sha256:c8852603a60fede650961ced447f7e2cdec2f1d4911e2234c4520a6e521c48e4`, expires 2026-11-20T22:48:24Z.

## Limitations and next gates

- The pure projector accepts caller-supplied rows; the read-only SQLite adapter now loads the cutover/event/coverage rows from an existing PAPER database using `mode=ro`, `PRAGMA query_only=ON`, and a read transaction. Adapter CI evidence is recorded below.
- Multi-settlement replay is now incremental: each execution event and coverage row is consumed at most once per strategy across sorted settlements; coverage lookup uses binary search. The UTC-day-only `replay_ledger_events` API remains unchanged.
- `VERIFIED` coverage and payload hashes are validated as declared ledger evidence; this does not independently prove that every execution event was captured.
- The offline end-to-end fixture now joins D07.2 byte readback, D07.4 parser, SQLite position projection, D07.3 expected population, a distinct PAPER posting path, persisted observed-event enumeration, reconciliation and VERIFIED funding coverage. The fixture deliberately declares shared upstream lineage; it does not prove independent source completeness or issuer authenticity.

D07.5 pure projection and CI: **PASS**. D07 overall: **PARTIAL**.


### Incremental replay hardening — 2026-11-14
- Refactored projection to maintain per-strategy position, event cursor, coverage cursor and chained evidence digests across sorted settlement times. Each event/coverage row is processed at most once; event-to-coverage lookup uses binary search. This avoids repeated O(settlements × events) replays.
- Exact-source workflow [43523109116](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43523109116): SUCCESS at SHA `904b1cc7cd159f4bdf170fb5149414efef576d2c`.
- Focused projection tests **19/19 PASS**; full PaperLedger regression **540/540 PASS** in 145.984s.
- Artifact `14084346648`, 16,015 bytes, digest `sha256:707d90e49b65e5ccd736f645b398ee367c60ca23868e04ecc790dc57afd95463`, expires 2026-11-20T22:54:59Z.


### D07.5 read-only SQLite adapter — 2026-11-14

- Added `load_paper_position_snapshots_from_db(...)` to load cutover snapshots, execution journal rows and EXECUTION coverage from an existing PAPER SQLite ledger.
- The adapter opens SQLite with `mode=ro`, enables `PRAGMA query_only=ON`, begins a read transaction, validates the required migration checksums/status, table columns and immutability triggers, and delegates to the pure projection. It does not initialize, migrate, repair or write the database.
- Disposable fixture tests verify: projected CORE/AI/LEGACY positions across two settlements; database file SHA-256 unchanged by the read; migration checksum drift fails closed; missing immutability trigger fails closed; missing cutover fails closed; missing database fails closed.
- TDD/CI correction: initial run [43523771077](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43523771077) exposed a test attempting to mutate a migration status protected by an immutability trigger. The test was corrected to simulate checksum drift while preserving the schema's immutability contract.
- Exact GREEN source SHA: `b01685048d203820a90d4b9b3f8f62831fb42b23`; workflow [43523963424](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43523963424), event `push`, branch `feature/core-operational-proof-20261112`, job `132224969794`, SUCCESS.
- Focused tests: adapter 5/5; position projection 19/19; Binance public funding parser 19/19; PAPER funding model 19/19; D07.2 provenance 17/17; D07 reconciliation 14/14; persistence/coverage 12/12; bootstrap 13/13. Full PaperLedger regression: **545/545 PASS** (135.398s).
- Artifact `14083688122`, name `dual-ledger-bootstrap-proof-b01685048d203820a90d4b9b3f8f62831fb42b23`, 16,503 bytes, GitHub-reported ZIP digest `sha256:5ce5d3e482fb404194d192b7f9cee1feb1b95b1f6baec5698b5b006083f3a0ec`, expires `2026-11-20T23:01:48Z`. The artifact payload has not been independently downloaded and re-hashed.
- The adapter reads only disposable test databases in CI. This does not verify any production/VPS database or prove external completeness of execution coverage.
- D07.5 projection + adapter: **PASS in disposable CI**. D07 overall remains **PARTIAL**.

### D07 end-to-end offline fixture — 2026-11-14

- Added `paper_execution/paper_funding_posting.py` as a separate PAPER posting path. It recomputes settlement amounts from normalized projected positions and parsed public-rate observations; it does not call the expected-population builder. It persists through `record_funding_event` and is idempotent by deterministic event ID/payload hash.
- The test fixture exercises: exact local response-byte readback → Binance USD-M parser → read-only SQLite cutover/journal/coverage projection → expected model → distinct posting calculation → persisted observed-event enumeration → reconciliation certificate → VERIFIED funding coverage.
- Fixture positions: CORE opens +0.1 BTC before settlement 1; AI opens -0.2 BTC between settlements; Legacy remains zero. Two funding-rate observations produce three non-zero strategy events. All **3/3** persisted events match expected; no missing, unexpected or duplicate events. First post reports `idempotent=false`; retry reports `idempotent=true` and does not duplicate ledger rows.
- The byte verifier returns byte-integrity/readback PASS while marking the declared shared lineage `BLOCKED_SHARED_LINEAGE`. The reconciliation result remains `independence=DECLARED_NOT_VERIFIED`, `globalCompleteness=NOT_VERIFIED`, `freshness=NOT_VERIFIED`, `issuerAuthenticity=NOT_VERIFIED`.
- This is a synthetic Binance-shaped JSON fixture and a disposable SQLite database, not a live Binance response, real account funding or a production ledger. No network client or scheduler was added.
- TDD: first idempotency contract RED [43551867259](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43551867259), source `cba3ac927a3649937514e385c691fc092b57e639`, caught first-write incorrectly labelled idempotent. The initial partial correction run [43552069567](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43552069567), source `d7bc8120d9bbc401a0dccf4dd68afc2544db16d8`, remained RED because the posting response had not yet propagated the ledger's idempotency result. The next full run [43552076224](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43552076224), source `007011efb8c173d74d0745b9491af000746d5ba5`, passed the focused tests but exposed an existing regression test expecting identical return dictionaries. The regression contract was updated to assert `false` on first write and `true` on retry.
- Final exact-source GREEN: workflow [43552400450](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43552400450), source SHA `d5116c24cd8f9ce987a2df10e6fa310aa70bceba`, job `132317575403`, SUCCESS. Focused tests: bootstrap 13/13; reconciliation 14/14; provenance 17/17; model 19/19; public parser 19/19; pure position projection 19/19; SQLite adapter 5/5; end-to-end 1/1; persistence/coverage 12/12. Full PaperLedger regression **546/546 PASS** in 144.258s.
- Artifact `14097150579`, name `dual-ledger-bootstrap-proof-d5116c24cd8f9ce987a2df10e6fa310aa70bceba`, 16,841 bytes, GitHub-reported digest `sha256:42b4922c5aa4d7ddc0acf99339cd026eafc27fa38727bb6525463fe0cb5fe3e5`, expires `2026-11-21T03:35:14Z`. Artifact payload has not been independently downloaded and re-hashed.
- Collateral exact-SHA verification at the same source: Core-First operational proof [43552400525](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43552400525) SUCCESS, artifact `14097011376`, 11,110 bytes, digest `sha256:8993de1a17f7b3e5b8fbfebdfa949235bcd7206b88add8bb5cfcf1d446612298`; Paper Ledger T1 Compatibility [43552400506](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43552400506) SUCCESS.

### Remaining D07 limits and next gate

- D07's offline PAPER pipeline and persisted reconciliation/coverage path: **PASS within the declared synthetic fixture population**.
- Real public response capture/readback, provider issuer authentication, actual source identity, enumeration completeness, actual upstream independence, freshness, global completeness and factual truth: **NOT VERIFIED**.
- No account-private endpoint, real account funding, exchange credentials, VPS, production DB, T0, Runner/One-shot, live execution or orders were used. No runtime network client or scheduler was added.
- D07 overall remains **PARTIAL**; production bootstrap remains **BLOCKED / NOT APPROVED**. A future source-capture or network-client increment requires a separately bounded approval.
