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
qua, thời điểm sự kiện đầu/cuối và `complete=false`. Có observations không chứng
minh capture đầy đủ trước sự kiện đầu, sau sự kiện cuối hoặc trong khoảng mất
kết nối. Một khoảng có trade ID gaps bằng 0 vẫn chưa chứng nhận toàn bộ tape.

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

Hàm kiểm tra market/schema/timestamp/coverage/numeric totals/hash. Nó cho phép
history cũ để hiển thị; decision layer chịu trách nhiệm giới hạn tuổi dữ liệu.

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
