# Paper execution — tầng 3

`PaperLedger` mô phỏng lệnh limit BTCUSDT USDⓈ-M trên độ sâu đang hiển thị từ
Hummingbot. Module chỉ dùng SQLite/Decimal và **không có HTTP client, API key sàn
hoặc hàm gửi lệnh thật**. `liveTradingSupported` luôn là `false`.

```python
from paper_execution.ledger import PaperLedger

ledger = PaperLedger(".data/market-data.sqlite3",
                     max_position_base="0.01", fee_rate="0.0005")
result = ledger.submit(validated_paper_intent, hummingbot_snapshot, now_ms)
state = ledger.snapshot()
```

Khởi tạo local là thao tác riêng, không thực hiện trong HTTP GET:

```bash
python3 -m paper_execution --db .data/market-data.sqlite3
```

CLI có tham số `--max-position-base`, `--fee-rate`, `--max-spread-bps`; cấu hình risk
là tham số của từng instance `PaperLedger`, không phải một chính sách được CLI lưu
vĩnh viễn. Backend phải truyền đúng cấu hình đã chọn khi tạo writer. Client chỉ đọc
dùng `read_snapshot(db_path)` (SQLite `mode=ro`), không gọi constructor để tự tạo
state. Đọc khi thiếu database/tables/state báo lỗi, không tạo ledger rỗng.

Intent và snapshot theo [`pipeline/CONTRACTS.md`](../pipeline/CONTRACTS.md).
Tham số `targetPositionBase` là vị thế ròng mục tiêu có dấu, không phải khối lượng
lệnh mới: `+` là long và `-` là short. Ledger tính chênh lệch với vị thế hiện tại.
Lệnh mới bị từ chối nếu hệ thống pause, intent hết hạn, vượt giới hạn vị thế,
spread vượt ngưỡng cấu hình hoặc còn lệnh OPEN/PARTIALLY_FILLED chưa được hủy.
Các giới hạn này là cấu hình của mô phỏng, chưa phải chính sách được duyệt cho live.

Snapshot phải đúng nguồn Hummingbot/binance_perpetual/BTCUSDT, có hai phía hợp lệ,
không chéo, tối đa 20 mức/phía, không quá cũ (30 giây) hoặc trước đồng hồ máy chủ
quá xa (5 giây). Timestamp là lúc lấy snapshot, **không chứng nhận thời điểm sự
kiện cuối của sàn, hàng đợi khớp lệnh hoặc chuỗi cập nhật đã đồng bộ**.

## Mô hình khớp

- BUY tiêu thụ ask từ thấp lên cao, SELL tiêu thụ bid từ cao xuống thấp, chỉ trong
  giới hạn giá và không vượt khối lượng hiển thị.
- Phần chưa khớp ở trạng thái OPEN hoặc PARTIALLY_FILLED. Không có background fill
  hay giả định rằng lệnh limit chắc chắn sẽ được khớp trong tương lai.
- Đường MANUAL/legacy cũ giữ cơ chế snapshot đơn-lần. Với Dual Ledger, Core/AI
  và đường Legacy reduction theo dõi lượng đã khớp ở từng mức giá trong cùng snapshot.
  Mỗi transaction trừ cả Core/AI level reservations và Legacy consumptions trước khi
  tính lượng còn hiển thị; tổng fill không vượt depth của snapshot. Đây chỉ là mô hình
  paper trên snapshot, không chứng minh thanh khoản hoặc khả năng khớp lệnh thật.
- Phí bằng quote notional thực sự mô phỏng đã khớp nhân fee rate. Tính toán dùng
  Decimal với precision 80, không dùng float cho tiền trong ledger.
- Giá vốn/PnL được cập nhật theo từng fill ở từng mức giá, để fill đóng vị thế cũ
  và fill mở vị thế đảo chiều không bị gộp sai vào VWAP toàn lệnh. VWAP chỉ là giá
  trung bình hiển thị của order.
- `realizedPnlQuote` là PnL đã thực hiện **trước phí**. `feesQuote` gồm phí tất cả
  fill; `netRealizedPnlQuote` bằng realized trừ toàn bộ phí đó, gồm phí vào của vị
  thế còn mở. Không báo chỉ số này như equity, PnL toàn tài khoản hoặc lợi nhuận live.

## State và tính lặp

Các bảng `paper_*` được thêm vào cùng SQLite mà không thay bảng nến. Mỗi submit
claim intent ID, cập nhật vị thế/fill/phí và ghi audit trong một giao dịch SQLite
`BEGIN IMMEDIATE`; các tiến trình đồng thời không khớp trùng cùng một intent.
ID/payload giống nhau trả lệnh đã lưu; ID giống nhưng payload khác bị lỗi.
Sau cancel, submit lại cùng intent trả trạng thái CANCELED hiện có và không mở lại.
State lưu trên đĩa được kiểm tra tính hữu hạn của Decimal, dấu của phí, quan hệ
giữa vị thế/giá vốn và cờ pause trước khi đọc hoặc submit. State hỏng/mất row báo
`sqlite3.DatabaseError`; constructor không tự tái tạo row đã mất thành FLAT.

`set_paused(True, now_ms)` chặn intent mới, giữ các lệnh/vị thế đã có.
`cancel(order_id, now_ms)` chỉ hủy phần chưa khớp; không đảo ngược fill hoặc phí.
Pause/cancel không đồng nghĩa đóng vị thế. Ledger không cung cấp lệnh flatten tự
động hay nút bật live. Snapshot hiển thị tối đa 100 lệnh gần nhất.


## LEGACY_UNATTRIBUTED close-only reconciliation

Schema migration v2 adds `paper_legacy_book_consumptions` separately from the
Core/AI risk-reservation tables. Records reference the paper order, book snapshot,
side/price/consumed quantity, reconciliation ID and a `sha256:` digest. Database
constraints enforce the digest format and prevent updates/deletes of recorded
consumption evidence.

`reduce_legacy_unattributed(db_path, intent, book, now_ms, ...)` is a PAPER-only
module API for reducing or flattening an existing `LEGACY_UNATTRIBUTED` position.
It rejects increases and reversals, does not create Core/AI risk reservations, and
does not reassign ownership. A valid reduction remains permitted while the shared
Kill Switch is active. It uses `BEGIN IMMEDIATE` and records each filled book level
so subsequent Core/AI orders see only the remaining visible depth. The caller must
supply a reconciliation ID and a lowercase `sha256:` digest of the external
reconciliation evidence; format validation does not independently verify the
underlying evidence bytes.

This API is not an owner-reassignment mechanism, production migration command,
backtest, exchange adapter or live execution path. `ai_execution_enabled=false`
remains mandatory.


## Reservation expiry and restart recovery

Migration v3 adds nullable expires_at_ms to paper_risk_reservations and an expiry
index. New Core/AI orders persist validUntilMs in the order document and the same
admission-time deadline in their reservation. A pending or partial reservation
expires only after now_ms is later than validUntilMs; its order becomes EXPIRED and
only the unfilled remaining margin/notional is released. Filled position, PnL, fees
and consumed book depth are not rolled back.

Expiry is swept transactionally before a scoped Core/AI submit or cancel, so a
restart does not reset the deadline. Retrying the original intent returns the
persisted EXPIRED order. Read-only snapshots never perform expiry writes. Historical
active reservations with no trustworthy expiry timestamp remain active and continue
to block same-ledger replacement; they require explicit cancel/reconciliation rather
than an invented deadline.

## Kiểm chứng

```bash
python3 -m unittest paper_execution.test_ledger -v
```

Kiểm thử bao gồm persistence/restart, fill/partial fill, lệnh limit không chạm giá,
retry cùng ID, payload xung đột, pause/cancel, input sai/hết hạn, chống dùng lại
snapshot, phí/PnL khi giảm và đảo chiều vị thế, submit đồng thời. Các kiểm thử chỉ
dùng SQLite thật và dữ liệu fixture; chưa chứng nhận tính đúng với fill của sàn.


## Funding provenance v4 and verified account cutover v5

Migration v4 adds source and recorded timestamps to funding events and creates
append-only funding-coverage evidence. The API record_funding_event(...) is
idempotent by event ID, rejects payload conflicts, stores source/snapshot identity
and a lowercase SHA-256 digest, and prevents update/delete. Positive funding amounts
are costs; negative amounts are credits. If a historical funding amount is known
but its strategy owner is not, record it under LEGACY_UNATTRIBUTED, never Core or AI.
An existing funding row without source provenance is marked LEGACY_UNVERIFIED and
keeps account risk readiness blocked.

The API record_funding_coverage(...) records VERIFIED, UNKNOWN or DISABLED intervals.
UNKNOWN coverage is not interpreted as zero and demotes account risk readiness.
DISABLED is accepted only with PAPER_TEST_CONFIGURATION and a persisted
configuration version, snapshot identity and payload digest. Coverage metadata and
event hashes are provenance references; the ledger does not fetch or independently
re-hash external statement bytes.

Migration v5 adds one immutable paper_account_equity_cutovers record per account.
The API record_account_equity_cutover(...) requires contiguous funding coverage for
the declared reconciliation interval, fresh mark and closed-candle timestamps,
dataset identity, source/snapshot/hash/config provenance, and explicit expected
statement totals for capital, realized PnL, fees, funding and account equity. It
reconciles Core + AI + Legacy ledgers and legacy account adjustments, verifies
funding event totals against each ledger, and computes mark-to-market equity. Only
a successful cutover establishes HWM and the UTC daily baseline and sets risk
readiness.

Account snapshots and new exposure admissions require v4/v5 and a persisted
cutover. Any UNKNOWN funding interval overlapping the cutover window keeps
readiness false and blocks exposure increases, even if a stale readiness flag was
manually set. Valid reductions remain available under the existing shared-risk
policy. A cutover is one-time and immutable; a different second cutover requires a
separately reviewed reconciliation/reset procedure.

Both migrations are additive and execute only when a scoped Core/AI writer opens
an isolated test database. No persistent account database migration is implied.

## Dual Ledger bootstrap và Manual Owner Attestation — test/CI only

`python -m paper_execution --db <new-paper-db.sqlite3> --bootstrap-manifest <manifest.json>` chỉ tạo database PAPER mới chưa tồn tại. Manifest phải bind đúng source SHA, funding snapshot, equity cutover và một file Manual Owner Attestation riêng. Attestation được kiểm tra theo exact-byte SHA-256, schema đóng, timestamp và các ID/hash của đúng hai snapshot; sai hoặc thiếu bằng chứng phải dừng trước khi tạo database.

Attestation v1 chỉ ghi nhận tuyên bố thủ công rằng người khai báo đã xem xét đúng funding/equity snapshots. `OWNER_DECLARATION` là nội dung khai báo, không phải xác thực danh tính. Không có chữ ký mật mã hoặc issuer authentication. Kết quả luôn giữ:
- source authenticity, factual truth, completeness và freshness: `NOT_VERIFIED`;
- privileged action authorization: `NOT_GRANTED`;
- cryptographic signature: `NOT_USED`.

Theo D09, một commit/action được GitHub xác thực có thể được ghi nhận là `PLATFORM_ATTRIBUTED_OWNER_ACTION`; điều này chỉ là quy thuộc nền tảng cho hành động GitHub, không biến file attestation thành chữ ký Owner và không cấp quyền bootstrap production. Manual review attestation, privileged-action authorization và trust administration là ba phạm vi tách biệt.

Các test chỉ dùng fixture tổng hợp và SQLite tạm trong GitHub Actions. Không dùng VPS, không tạo database production, không chạm T0, không chạy Runner/One-shot và không gửi lệnh. Bootstrap production vẫn BLOCKED cho đến khi có evidence thực tế được kiểm chứng độc lập và một phê duyệt riêng đúng phạm vi.


## D07 persisted funding population reconciliation and readiness gate

The D07 integration uses `paper_execution.funding_reconciliation.reconcile_funding_population`
to compare a caller-supplied expected funding inventory with a deterministic
enumeration of `paper_funding_events` from the paper ledger. Both populations
must use the same half-open interval `[startAtMs, endAtMs)` and quote currency.
Event amounts must be exact Decimal strings; binary floats are rejected. Event
order is canonicalized before reconciliation identity is calculated, and each
population is limited to 100,000 events.

A successful comparison is only `COMPLETE_WITHIN_DECLARED_POPULATION`. It does
not prove global completeness, freshness, actual source independence or issuer
authenticity. The output retains `DECLARED_NOT_VERIFIED` / `NOT_VERIFIED`
claims for those dimensions.

### Funding event and coverage sequence

1. Stage funding events before marking the interval VERIFIED. Staging an event
   sets `riskReady=false`; it does not authorize exposure.
2. Call `record_funding_reconciliation(db_path, expected_population=..., recorded_at_ms=...)`.
   This persists the immutable reconciliation certificate and audit record.
3. Only a matching COMPLETE certificate can be supplied as
   `reconciliation_id` to `record_funding_coverage(status="VERIFIED")`.
   Interval, USDT currency, expected snapshot ID, timestamp and current observed
   population digest must match.
4. Once an interval is VERIFIED, additional funding events in that interval are
   blocked by the API and a SQLite trigger. A new event must be staged in an
   uncovered interval and reconciled before that interval is certified.
5. Account equity cutover and the read-only account risk snapshot recheck the
   certificate against the current observed event population. Stale or missing
   evidence fails closed.

Reconciliation and coverage do not set readiness true; only a successful account
equity cutover may establish `riskReady`.

Schema migration v10 creates the immutable reconciliation table, evidence hash,
audit trail, coverage/event guards and event-time index. Existing VERIFIED
coverage without a certificate demotes readiness and is not silently upgraded.

### Bootstrap limitation

The bootstrap manifest requires `fundingExpectedPopulation`, which is included
in the exact funding evidence document and covered by its SHA-256 and manual
Owner attestation. Fresh-account bootstrap v1 accepts only an empty expected
funding-event list. Importing non-empty historical funding events is not
implemented.

This is synthetic test/CI integration only. `independence=DECLARED_NOT_VERIFIED`,
`globalCompleteness=NOT_VERIFIED`, `freshness=NOT_VERIFIED` and
`issuerAuthenticity=NOT_VERIFIED` remain explicit. Real external source
authentication and completeness are not established; production bootstrap
remains blocked.


## D07.1 source-neutral expected-population provenance contract

Before any future independent-completeness claim, see
[`docs/evidence/D07_1_EXPECTED_FUNDING_POPULATION_PROVENANCE_CONTRACT_2026-11-14.md`](../docs/evidence/D07_1_EXPECTED_FUNDING_POPULATION_PROVENANCE_CONTRACT_2026-11-14.md).
The contract separates source identity, issuer authenticity, exact-byte integrity,
independent byte readback, pagination/enumeration completeness, lineage independence,
freshness and factual truth. A SHA-256 digest or successful readback does not
authenticate the issuer or prove completeness. No source adapter, real-data access,
signature/key workflow, database migration or runtime behavior is authorized by
that design document. D07 continues to claim only
`COMPLETE_WITHIN_DECLARED_POPULATION`; production bootstrap remains blocked.


## D07.2 synthetic evidence-byte readback verifier

`paper_execution.funding_provenance.verify_funding_source_evidence` validates
a strict source-evidence envelope and re-reads each local page file to verify
exact byte length and SHA-256. It checks declared cursor-chain structure and
fails closed on missing/tampered files, unsafe paths, duplicate pages/cursors,
invalid terminal markers, inconsistent source totals and declared shared
lineage. A passing result proves only the captured local bytes were read back
unchanged and the manifest is structurally consistent. It does not authenticate
the issuer or prove actual pagination completeness, source independence,
freshness or factual truth; those remain NOT VERIFIED.


## D07.3 PAPER funding population model

`paper_execution.funding_model.build_expected_funding_population` builds a
D07-compatible `EXPECTED_FUNDING_EVENTS` population from explicit PAPER
position snapshots and public BTCUSDT funding-rate observations. For a linear
USDT perpetual, the signed simulated funding cost is:

`funding_cost = signed_position_base * mark_price * funding_rate`

Positive amounts are PAPER funding costs; negative amounts are credits. At
each settlement, the model selects the latest snapshot at or before settlement
for each of `STRATEGY_CORE`, `AI_FREQAI` and `LEGACY_UNATTRIBUTED`. Missing
or stale snapshots fail closed (default maximum age 60 seconds). Zero positions
produce no event. Inputs use bounded exact Decimal strings; event IDs, payload
hashes and population snapshot IDs are deterministic.

This is a deterministic PAPER accounting model, **not** an assertion that the
result matches a real Binance account's funding cashflows. It performs no
network access, credential access, account-data access, order placement or
ledger writes.

The function accepts caller-supplied snapshots and funding-rate observations. Each numeric input is limited to 80 significant digits; the Decimal arithmetic context is 240 digits and canonical formatting does not round through the ambient Decimal context.
A read-only source adapter/replay of historical PAPER positions, public-rate
acquisition, controlled staging into `paper_funding_events`, and end-to-end
coverage integration are not implemented by this increment. Until those
pieces are completed and tested, D07 remains PARTIAL and must not be used to
claim actual-source independence, global completeness, issuer authenticity,
freshness or production readiness.


## D07.4 Binance USDⓈ-M public funding page parser

`paper_execution.binance_public_funding.parse_binance_usdm_funding_rate_page` parses captured bytes from the public `GET /fapi/v1/fundingRate` market-data endpoint. It accepts only BTCUSDT Regular funding records and verifies the declared page byte length and SHA-256 before parsing. It rejects Special rate types, malformed/duplicate JSON keys, invalid numeric types, duplicate or out-of-order timestamps, out-of-scope events and pages over 1,000 records. It binds normalized records to the D07.2 evidence snapshot ID and emits the funding-model input schema.

The parser is offline only: no HTTP client, API key, account data, network request or scheduler. Binance documents inclusive start/end query parameters, ascending results, a 1,000-record maximum, and response fields including fundingTime, fundingRate, markPrice and rateType: [official endpoint documentation](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History). D07.2 still does not prove issuer authenticity or global enumeration completeness.


## D07.5 PAPER position projection

`paper_execution.funding_position_projection.build_paper_position_snapshots` is a pure function that projects signed positions at funding settlement times from the three immutable cutover ledger snapshots, execution-journal FILL events and contiguous declared VERIFIED EXECUTION coverage. It verifies canonical execution payload hashes, rejects late/uncovered events and ambiguous fills exactly at settlement, and emits deterministic snapshots accepted by `funding_model.py`.

This function does not read or write SQLite; it accepts caller-supplied rows. A read-only SQLite adapter is still required. Coverage status remains declared evidence, not independent proof of journal completeness. The current implementation replays the event list for each settlement; incremental replay is required before large population use.


Funding sign convention: `amountQuote = signedPositionBase × markPrice × fundingRate` represents **cost** (positive = debit, negative = credit), not account income. This matches the ledger equity equation, which subtracts accumulated funding cost. Binance states that a positive rate means longs pay and shorts receive: [official explanation](https://www.binance.com/en/support/faq/detail/98488a516eb84e3eb34605683dffd554).


The position projector now processes sorted settlements incrementally: each event and coverage row is consumed at most once per strategy, and event-to-coverage lookup uses binary search. The daily UTC replay function retains its original UTC-boundary requirement.
