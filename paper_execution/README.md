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
- Mỗi snapshot đầy đủ được dùng cho tối đa một lần có fill. Một intent khác dùng
  lại chính snapshot đã tiêu thụ bị từ chối; chưa mô phỏng reservation theo từng mức.
  Snapshot mới chỉ là quan sát mới, không chứng minh thanh khoản của thị trường thật
  có thể tái sử dụng — đây là giới hạn của mô hình paper.
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

## Kiểm chứng

```bash
python3 -m unittest paper_execution.test_ledger -v
```

Kiểm thử bao gồm persistence/restart, fill/partial fill, lệnh limit không chạm giá,
retry cùng ID, payload xung đột, pause/cancel, input sai/hết hạn, chống dùng lại
snapshot, phí/PnL khi giảm và đảo chiều vị thế, submit đồng thời. Các kiểm thử chỉ
dùng SQLite thật và dữ liệu fixture; chưa chứng nhận tính đúng với fill của sàn.
