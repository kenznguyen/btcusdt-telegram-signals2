# Futures Intelligence — tầng 1

Module này đọc CSV **đã thu thập thật** từ
[`waynemason1/binance-futures-collector` tại `bc4f0ef`](https://github.com/waynemason1/binance-futures-collector/tree/bc4f0ef633fbeee4a49defd72827f17162693805),
tạo snapshot JSON có kiểm tra dữ liệu để API/decision layer dùng chung. Nó không
tự khởi động collector, không tải dữ liệu mẫu, không cần API key và không đặt lệnh.

Chỉ nhận `exchange=binance`, `market=futures`, `symbol=btcusdt`. Header được đối
chiếu với `src/constants.rs` và `src/utils/csv_writer.rs` của commit đã pin.
Đặc biệt, CSV Open Interest dùng cột **`mark_price`**, dù struct Rust nội bộ có
field `price`.

## Import một cửa sổ

Từ thư mục gốc repository, ví dụ đọc khoảng 00:00–00:05 UTC ngày 2026-10-29:

```bash
python3 -m futures_intelligence.import_collector \
  --start-ms 1793232000000 --end-ms 1793232300000 \
  --trades /capture/futures/trades/btcusdt/2026-10-29/btcusdt_trades_2026-10-29.csv \
  --funding /capture/futures/funding_rates/btcusdt/2026-10-29/btcusdt_funding_rates_2026-10-29.csv \
  --open-interest /capture/futures/open_interest/btcusdt/2026-10-29/btcusdt_open_interest_2026-10-29.csv \
  --liquidations /capture/futures/liquidations/btcusdt/2026-10-29/btcusdt_liquidations_2026-10-29.csv \
  --large-trade-threshold 1000000 \
  --output .data/intelligence.json
```

Đường dẫn phải trỏ tới capture thực tế, có thể bỏ các feed chưa có. Mỗi flag CSV
có thể lặp để đọc nhiều ngày. Không truyền cùng file hai lần. Cửa sổ là
`[startMs,endMs)`, tối đa một ngày; tổng tối đa 100.000 hàng qua các feed và tối
đa 16 file/feed. File tối đa 64 MiB; field tối đa 128 ký tự.

Timestamp CSV và `datetime_utc` phải biểu diễn cùng thời điểm UTC milliseconds.
Rows khác sàn/cặp/loại thị trường hoặc timestamp tương lai bị từ chối. Numeric
payload trong cửa sổ phải hữu hạn và hợp lệ; không sửa hoặc bỏ qua giá trị sai để
làm kết quả trông đầy đủ. Lệnh import lỗi không ghi đè snapshot trước đó.

`availableAtMs` lấy từ đồng hồ máy chủ khi import, không có flag CLI để gán về
quá khứ. Import dữ liệu cũ hôm nay không biến sự kiện cũ thành tín hiệu mới:
consumer phải kiểm tra cả `windowEndMs` lẫn `availableAtMs`.

## Chỉ số và giới hạn ý nghĩa

| Trường | Cách tính / ý nghĩa |
| --- | --- |
| `fundingRate`, `fundingAtMs` | Giá trị và thời điểm **sample** funding gần nhất trong cửa sổ; không phải thời điểm settlement hoặc dòng tiền đã thanh toán |
| `openInterestBase` | Open Interest ở sample cuối, đơn vị BTC |
| `openInterestChangeBase` | Sample cuối trừ sample đầu, chỉ có khi ít nhất hai sample khác thời điểm |
| `takerBuyQuote`, `takerSellQuote` | Tổng price × quantity theo **aggressor side** của aggregate trades, đơn vị USDT |
| `netTakerQuote` | Mua chủ động trừ bán chủ động trong cửa sổ; không gắn nhãn CVD liên tục |
| `largeTradeQuote` | Tổng notional các aggregate trade đạt `largeTradeThresholdQuote`; không phải giao dịch ví cá voi/on-chain |
| `observedLiquidationBuyQuote` | Tổng `value` các forced **BUY** quan sát được; thường tương ứng vị thế short bị thanh lý |
| `observedLiquidationSellQuote` | Tổng `value` các forced **SELL** quan sát được; thường tương ứng vị thế long bị thanh lý |

Trade ID trùng chỉ được tính một lần; cùng ID nhưng payload mâu thuẫn làm import
thất bại, kể cả khi hai payload có cùng notional. `is_buyer_maker=1` phải tương
ứng `side=sell`; `0` tương ứng `buy`. Gaps giữa các aggregate trade ID được ghi
trong `coverage.trades.tradeIdGaps`.

Funding/OI sample trùng thời điểm chỉ được bỏ qua khi nội dung khớp. Liquidation
schema không có ID sự kiện duy nhất, nên module giữ từng row quan sát được;
không tự bịa cơ chế dedup có thể xóa nhầm hai sự kiện thật giống nhau. Dữ liệu
liquidation Binance là sample stream, không được coi là toàn bộ thanh lý sàn.

Collector ghi số qua f64 với 12 chữ số sau dấu chấm. Module dùng Decimal cho
tổng/chênh lệch, nhưng không khôi phục độ chính xác nguồn đã mất. Kiểm tra
`value ≈ price × quantity` và `oi_value ≈ mark_price × open_interest` dùng sai số
tối đa `max(1e-8, abs(product) × 1e-9)` để phản ánh cách ghi của nguồn.

## Coverage và tính toàn vẹn

Mỗi feed có `status` (`MISSING`, `NO_ROWS`, `OBSERVED`), số row, số bản sao bỏ
qua, thời điểm sự kiện đầu/cuối, `continuityStatus` và `complete=false`.
Trade ID gaps được đánh dấu `GAPS_DETECTED`; không có gap quan sát được vẫn chỉ
là `UNVERIFIED`, không phải bằng chứng kết nối liên tục. `connectionStatus` luôn
là `UNVERIFIABLE`: schema CSV đã pin không ghi heartbeat hoặc disconnect events,
nên importer không thể xác nhận lúc nào collector mất kết nối. Không được suy
đoán `CONNECTED` chỉ từ việc có row hoặc `DISCONNECTED` chỉ từ việc không có row.
Muốn phân biệt mất kết nối thực sự cần bổ sung heartbeat/reconnect event từ collector
và pin schema/commit mới; hiện tại đây là giới hạn nguồn, không phải lỗi importer.

Snapshot mới ghi `collectorCommit` và `inputFiles` theo từng feed. Mỗi file có
basename, SHA-256, kích thước byte, số dòng đọc và số dòng nằm trong cửa sổ.
Đường dẫn máy chủ không được đưa vào artifact. `snapshotId` bao phủ cả provenance
này; checksum file cho phép đối chiếu lại capture gốc nhưng không phải chữ ký
xác thực từ collector. Snapshot v1 cũ không có trường provenance vẫn đọc được,
nhưng không có bằng chứng checksum file.

Freshness API được tính động từ thời điểm hiện tại và event/sample mới nhất:
trades 60 giây; funding 630 giây (poll 300 giây + jitter và một chu kỳ bỏ lỡ);
open interest 1.230 giây (poll 600 giây + jitter và một chu kỳ bỏ lỡ).
Đây là ngưỡng theo các interval mặc định trong `config.example.toml` của collector
đã pin; nếu vận hành thay interval, policy freshness phải được review đồng bộ.
Liquidation là event stream thưa, không có heartbeat trong CSV nên hiển thị
`UNVERIFIABLE` thay vì gọi một event cũ là disconnect. Các ngưỡng này chỉ dùng
đánh giá chất lượng snapshot, không thay đổi chiến lược hoặc risk limits.

Feed chưa có hoặc không có row trong cửa sổ trả chỉ số **null**, không gán giả
bằng 0. Khi trade observations có thật, phía không có aggressor trade có thể có
tổng 0; đây là tổng trong tập quan sát, không phải chứng nhận toàn thị trường.

`quality=OBSERVED_ONLY` và `source` chứa commit nguồn. `snapshotId` là
`identity('intelligence:', payload_without_snapshotId)`. Đây là hash nội dung,
không phải chữ ký xác thực nguồn. File được viết vào file tạm cùng thư mục, flush
và `os.replace` để consumer không thấy JSON đang ghi dở.

API có thể gọi:

```python
from futures_intelligence.import_collector import validate_snapshot

validated = validate_snapshot(snapshot, now_ms)
```

Hàm kiểm tra market/schema/timestamp/coverage/numeric totals/provenance/hash. Nó cho phép
history cũ để hiển thị; API quality tính freshness từng feed và decision layer
chỉ phát tín hiệu khi trade flow đang FRESH, không có trade ID gap hoặc duplicate
và toàn bộ snapshot vượt qua validation.

AI decision hiện chỉ dùng trade flow đã qua quality gate làm đầu vào T1. Funding,
OI và liquidation được công bố cho Dashboard/downstream analysis nhưng chưa là
điều kiện định hướng lệnh; Strategy Core RSI/ADX/Smart DCA không bị thay đổi.

## Connection Event Sidecar v1 — offline contract only

The separate `connection_events` module validates an append-only JSONL sidecar
for WebSocket lifecycle evidence. It is deliberately not wired into the legacy
CSV importer. The importer continues to report `connectionStatus=UNVERIFIABLE`
until a trusted collector-side event writer and a separately reviewed integration
are implemented.

Each event carries `schemaVersion`, unique `eventId`, exact `sourceCommit`,
process `sessionId`, per-socket `connectionId`, `batchId`, `route`
(`public`/`market`), `eventType`, and UTC `eventAtMs`. Supported event
types are `CONNECTED`, `PING_SENT`, `PONG_RECEIVED`, `DISCONNECTED`, and
`RECONNECT_SCHEDULED`. Ping/Pong records pair through `heartbeatId`; disconnect
records require a reason; reconnect records require a positive attempt and delay
no greater than 60 seconds.

Example offline validation call:

```python
from futures_intelligence.connection_events import load_and_validate_connection_events

result = load_and_validate_connection_events(
    "/capture/session-001/connection-events.jsonl",
    expected_sha256="trusted-manifest-sha256",
    expected_source_commit="collector-source-commit-sha",
    expected_session_id="collector-session-001",
    window_start_ms=1_700_000_000_000,
    window_end_ms=1_700_000_060_000,
    max_heartbeat_gap_ms=60_000,
    capture_finalized=True,
    capture_complete_through_ms=1_700_000_060_000,
    expected_connections=[{"batchId": 0, "route": "public"},
                          {"batchId": 0, "route": "market"}],
)
```

The validator requires a sealed capture segment and a trusted
`capture_complete_through_ms` watermark at or beyond the requested window end;
this prevents a truncated event-file tail from being treated as proof that no
disconnect occurred. It checks file checksum, source/session identity, ordered
unique events, connection state transitions, Ping/Pong pairing, heartbeat
coverage, and expected batch/routes. It returns conservative states:
`VERIFIED_CONNECTED`, `DISCONNECTED`, `HEARTBEAT_GAP`,
`UNVERIFIABLE`, or `OUTSIDE_WINDOW`. A verified result requires a connection
already open at the start of the half-open window, matching Pong evidence spanning
the window, no excessive heartbeat gap, and no disconnect inside the window.
Missing expected routes and partial-window sessions fail closed.

The sidecar is bounded to 64 MiB, 16 KiB per line, and 100,000 events. SHA-256
only detects changes relative to a trusted expected digest; it is not a signature
or proof of collector authenticity.

Test offline with:

```bash
python3 -m unittest futures_intelligence.test_connection_events -v
```

**Important:** the currently pinned upstream Rust collector
`bc4f0ef633fbeee4a49defd72827f17162693805` does not write this sidecar.
All sidecar tests use synthetic temporary files. No live collector, WebSocket,
exchange, or database is involved. The validator is not operational continuity
proof and must not be used to promote current CSV snapshots from
`UNVERIFIABLE`.

Full schema and producer requirements:
`docs/evidence/t1/T1_CONNECTION_EVENT_SIDECAR_CONTRACT_2026-11-07.md`.

## Kiểm chứng

```bash
python3 -m unittest futures_intelligence.test_import_collector -v
python3 -m futures_intelligence.import_collector --help
```

Kiểm thử dùng CSV thật trên filesystem tạm với fixture có nhãn, không gọi sàn.
Capture live và tính liên tục của collector chưa được kiểm chứng trong môi
trường này. Không có dữ liệu fixture nào được tự phục vụ khi khởi động module.

Nguồn đã đối chiếu:
[SCHEMA](https://github.com/waynemason1/binance-futures-collector/blob/bc4f0ef633fbeee4a49defd72827f17162693805/docs/SCHEMA.md),
[header constants](https://github.com/waynemason1/binance-futures-collector/blob/bc4f0ef633fbeee4a49defd72827f17162693805/src/constants.rs),
[CSV writer](https://github.com/waynemason1/binance-futures-collector/blob/bc4f0ef633fbeee4a49defd72827f17162693805/src/utils/csv_writer.rs),
[message handler](https://github.com/waynemason1/binance-futures-collector/blob/bc4f0ef633fbeee4a49defd72827f17162693805/src/websocket/message_handler.rs).


## Rust collector-side connection sidecar writer

A portable offline Rust reference writer is available at
`futures_intelligence/collector_sidecar_writer`. It writes append-only JSONL
lifecycle events, fsyncs each event before returning, correlates Ping/Pong IDs,
records the exact subscription set in a finalized manifest, and calculates
the sidecar SHA-256.

It is not yet integrated into the upstream collector. See
`futures_intelligence/collector_sidecar_writer/README.md` for the API and
`docs/evidence/t1/T1_COLLECTOR_SIDECAR_WRITER_IMPLEMENTATION_2026-11-07.md`
for exact-source CI evidence and integration blockers. Existing importer
`connectionStatus` remains `UNVERIFIABLE`.
