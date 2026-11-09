# P1.9 — Same-session self-review of final T1 Source Contract v1.1

Date: 2026-11-09
Review type: Same-session adversarial self-review; NOT independent.
Verdict: **REQUEST CHANGES — DESIGN NOT READY FOR IMPLEMENTATION.**

## 1. Exact review inputs

- Normative contract: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md`
- Normative contract blob SHA: `fd640ab36efed6975f1dfaaed750f9d0ae7f708c`
- Archival v1 blob SHA: `c64d6da7b16e608ef5ccebafabce03e51960cfcc`
- P1.3 acceptance profile blob SHA: `a99cf2e21edc4519a2f2d0833c6cdf1e6d768599`
- P1.7 same-session static review blob SHA: `a83bb0246b9480f593516dd410782fc619122127`
- Pinned T1 producer: `kenznguyen/binance-futures-collector@6e20fe94f3ad64cc450e73def80a167fe371e49e`
- Source blobs inspected:
  - `src/utils/csv_writer.rs`: `2c4538dcef7dfa758a854292031239c15f7c282b`
  - `src/websocket/message_handler.rs`: `7d7f221fbf4b31470049baea55584645352f61b7`
  - `src/models.rs`: `993419725268d1308645e3a37c15e9779a9e92cc`
  - `src/rest/client.rs`: `3f2068a07fbf6a6e348fb227274f7b0d54703e8d`
  - `src/collectors/symbol_discovery.rs`: `34e453cbb96d5964d1f58e204bbfbe147041ced6`
  - `src/constants.rs`: `0bf50b5fe02f4f196b38481cde6ecab9e2adb941`

This review inspected the complete v1.1 sections 14–20, archival-v1 precedence, P1.3, P1.7, and the pinned producer paths listed above. It is a same-session review and cannot satisfy issue #138's independence requirement.

## 2. Findings

### P1.9-F01 — CRITICAL: manifest becomes visible before directory durability is established

**Evidence:** v1.1 §5.2 orders: write/sync temporary manifest; atomically rename it over the published manifest; fsync the containing directory; only then expose the new offset/watermark. C36 explicitly recognizes the crash window after rename but before directory sync.

**Problem:** Atomic rename makes the replacement manifest visible to concurrent readers immediately. The document says readers must not see the new watermark until after directory fsync, but it specifies no reader/writer lock, publication barrier, visibility protocol or separate durable commit record that enforces this. A consumer can therefore read and accept the new manifest in the interval after rename but before directory fsync; a power loss can then lose the directory entry update. The intended "only then expose" invariant is not established by the listed operations alone.

**Required change:** Define an enforceable publication visibility protocol. For example, a producer-held exclusive publication lock spanning rename plus directory fsync, with consumers required to acquire the corresponding shared lock before reading; alternatively define another independently durable commit/epoch protocol. Specify lock crash recovery and prove readers cannot accept PREPARED/uncommitted state. Add deterministic ordering tests and an authorized target-filesystem crash test before any durability claim.

Severity: CRITICAL — possible false acceptance of an offset/watermark that has not crossed the claimed directory durability boundary.

### P1.9-F02 — HIGH: exclusive writer ownership and generation fencing are not implementable from the current wording

**Evidence:** v1.1 §5.1 requires exactly one writer, an exclusive ownership mechanism and monotonically allocated durable generations. C45 only says a second writer claiming the same generation must fail.

**Problem:** The contract does not define the ownership primitive, fencing token, stale-owner behavior, lock lifetime, takeover/recovery protocol or how an old process is prevented from resuming writes after a replacement owner starts. A simple lock or PID check may be stale after crashes and does not necessarily fence a paused former owner. Two processes could otherwise race on data/manifest publication or a stale owner could publish after a new generation has begun.

**Required change:** Specify the exact single-writer/fencing model and generation allocation transaction, including stale-owner rejection, crash recovery, lease expiry if used, monotonic generation source, and tests where the former owner resumes after takeover. If the selected filesystem cannot provide the required primitive, fail closed and block the source.

Severity: HIGH.

### P1.9-F03 — HIGH: current contract has no reachable proof path for WINDOW_GAP

**Evidence:** v1.1 §15.2 requires exactly one REST row for every expected minute; a missing REST minute is always SOURCE_HEALTH_UNKNOWN. §16.1 says REST-present/WS-absent is RECONCILIATION_SOURCE_DIVERGENCE and WS-present/REST-absent is SOURCE_HEALTH_UNKNOWN; REST-only rows cannot enter the WS-derived generation. §20.2 says WINDOW_GAP is available only after a valid seal and complete health proof establish a source row is absent.

**Problem:** Under the currently defined evidence profile, any missing REST row blocks RECONCILED_COMPLETE, while any REST/WS asymmetry blocks reconciliation or quarantines. No accepted profile remains that can produce a valid seal and then classify an absent source row as WINDOW_GAP. The state is effectively unreachable, but the normative text still describes it as available. This can create divergent implementations of gap classification.

**Required change:** Explicitly mark WINDOW_GAP unassignable under the current v1.1 profile (just like GAP_DETECTED), or define a separately versioned and approved authoritative gap-evidence profile. State that no current C01–C81 case can assign it. Do not weaken the missing-REST UNKNOWN rule.

Severity: HIGH.

### P1.9-F04 — HIGH: FINAL_ONLY does not yet bind producer interval validation to the actual persisted feed

**Evidence:** pinned `KlineData` contains `interval`, `close_time` and `is_closed` (`models.rs` blob above). `process_kline` filters `is_closed=false`, but does not validate `interval == "1m"`; it drops interval and close_time when constructing `KlineCsv`. The current CSV writer has no versioned manifest/output_mode implementation.

**Problem:** v1.1 requires a manifest declaration `interval=1m` and `output_mode=FINAL_ONLY`, plus regression evidence. The proposed proof is incomplete unless tests establish that the actual subscribed stream/configuration and every accepted event are 1m, that unexpected interval events are rejected, and that the manifest describes the exact writer generation. Filtering provisional events alone does not prove the persisted stream is 1m.

**Required change:** Require producer-side validation of the incoming interval and stream subscription identity, rejection of mismatched intervals, and regression tests proving 1m-only persistence and provisional-event exclusion. Bind the tests/manifest to the exact collector source SHA and generation. Decide whether close_time must be validated against the 1m boundary before persistence; if so, specify the rule.

Severity: HIGH.

### P1.9-F05 — HIGH: BTCUSDT product identity can be bypassed by a hardcoded symbol exception

**Evidence:** pinned `symbol_discovery.rs` first filters exchange metadata by TRADING, PERPETUAL and quote_asset=USDT, but then appends hardcoded `btcusdt` and `dogeusdt` exceptions when the metadata record only has `status == TRADING`.

**Problem:** The exception path does not re-check PERPETUAL and quote_asset=USDT. The v1.1 contract correctly requires exact USD-M product identity, but the pinned producer's discovery allowlist is not itself sufficient proof for the BTCUSDT exception path.

**Required change:** Ensure the manifest producer independently validates the exact BTCUSDT exchange metadata record (contract_type, quote_asset, status and the configured USD-M endpoint/stream family) before writing the generation. The exception list must not bypass identity requirements. Add a fixture where the symbol is TRADING but contract_type or quote_asset is wrong and require SOURCE_IDENTITY_UNPROVEN.

Severity: HIGH.

### P1.9-F06 — MEDIUM: manifest format and reader trust boundary remain underspecified

**Evidence:** v1.1 §§2, 4–7 enumerate manifest fields and digest checks but do not define a complete machine-readable manifest schema, canonical serialization, exact manifest filename/discovery binding to each CSV partition, duplicate/unknown-field handling, path/symlink policy, or reader behavior when more than one candidate manifest exists.

**Problem:** Different producers/adapters could serialize or bind the manifest differently while claiming v1.1 compliance. This is especially risky because the manifest is the authority for file generation, committed offset, source identity and watermark.

**Required change:** Define a versioned strict manifest schema (field types, required/optional fields, canonical digest input, exact file-to-manifest binding, path and symlink policy, unknown-field handling, duplicate-manifest behavior and parser rejection rules) before implementation. Do not imply this is already covered by a list of field names.

Severity: MEDIUM/HIGH.

### P1.9-F07 — MEDIUM: WINDOW_GAP / C46 acceptance fixture wording can be read as premature PASS

**Evidence:** C46 says exact full REST coverage and matching WS values may allow reconciliation evidence to be committed; P1.3 C55 says full coverage is only eligible for further identity/finality checks and is not an unconditional pass.

**Problem:** C46 does not repeat all prerequisites, and can be interpreted as accepting the case based only on row coverage and equality.

**Required change:** Rewrite C46 as conditional: eligible for commit only after all identity, exact request boundary, pagination, finality, source-health, no-conflict, durability and generation-binding gates pass. The fixture must fail if any gate is omitted.

Severity: MEDIUM.

## 3. Existing blockers re-confirmed

- **F01 CRITICAL — REST completeness oracle not accepted.** P1.3 explicitly leaves no-trade behavior, boundary inclusion, finality/correction and pagination unresolved. The endpoint remains a candidate only; `RECONCILED_COMPLETE` remains unavailable.
- **F05 HIGH — confirmed decimal-loss defect.** At pinned `csv_writer.rs`, `write_kline` parses OHLCV/taker fields as `f64`, formats to 12 fractional digits and uses `unwrap_or(0.0)`. Malformed values can become zero and valid decimal strings can be rounded. No producer correction is present in this reviewed SHA.
- **F07 HIGH/operational — filesystem durability NOT VERIFIED.** The sync/rename protocol is a design, not evidence for the actual VPS filesystem, mount, device/provider or crash recovery. P1.9-F01 further shows the visibility ordering is underspecified even at design level.
- **Independent review PENDING.** This review does not satisfy issue #138.

## 4. What passed at document/source inspection level

- Archival v1 explicitly says it is non-normative and v1.1 controls; old per-row finality proposal is marked superseded.
- v1.1 explicitly chooses versioned `FINAL_ONLY` + `interval=1m`; current pinned handler filters `is_closed=false`, but does not yet prove the full manifest/interval contract.
- Missing REST minutes remain UNKNOWN; no-trade inference and synthetic candles are prohibited.
- REST-only rows cannot be silently inserted into the WS-derived generation.
- Health invalidation is sticky in the proposed contract; a failed health-event persistence path blocks offset/manifest/watermark/seal advancement and requires restart quarantine.
- Manifest digest threat claim is limited to accidental corruption; it does not falsely claim authentication or anti-rollback against a local attacker.
- T0 independence, no T1 promotion/write path, paper-only and no-live-order guardrails remain explicit.

## 5. Verification limits

- Read-only GitHub file inspection at the exact blobs listed above.
- No executable tests run; C01–C81 remain design fixtures, not test evidence.
- No Binance REST request made.
- No GitHub Actions workflow dispatched; run ID NONE; artifact NONE.
- No T1 source edits, adapter implementation, VPS/runtime or T1 activation.
- No T0/T2, strategy, AI, ledger, risk-engine or trading changes.
- No deletion, archive, cleanup, vacuum, compaction, backup expiry, restore or destructive operation.

## 6. Disposition and next steps

**P1.9 SELF-REVIEW COMPLETE / REQUEST CHANGES / DESIGN NOT READY FOR IMPLEMENTATION.**

Required next sequence:
1. Resolve P1.9-F01 publication visibility/durability ordering first.
2. Define writer ownership/fencing and manifest schema/binding.
3. Make WINDOW_GAP explicitly unavailable under current profile or add a separately reviewed authoritative gap profile.
4. Bind FINAL_ONLY to interval validation and close-time semantics; close the BTCUSDT identity bypass.
5. Reconcile C46 wording and add regression/failure fixtures.
6. Obtain genuinely independent review against the updated exact SHAs.
7. Keep F01/F05/F07 gates blocked until authoritative evidence, source correction and target-filesystem proof exist.

No implementation, tests, Actions dispatch, REST request, VPS/runtime, T1 activation or destructive data operation is authorized by this review. T0 remains independent/canonical. Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.
