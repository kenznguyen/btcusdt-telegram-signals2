# Canonical market data — tầng 0

Kho nến dùng chung cho các tầng phân tích. Bản đầu hỗ trợ **Binance USDⓈ-M perpetual BTCUSDT**, khung **15m/1h**, SQLite mặc định và adapter PostgreSQL/TimescaleDB tùy chọn. API WSGI vẫn chỉ đọc. Bộ đồng bộ lấy OHLCV qua CCXT; không cần API key sàn. Chưa thay nguồn OKX của Python bot/backtest hay nguồn trực tiếp trong APK.

## Chạy đồng bộ

Từ thư mục gốc repository, dùng Python 3.10+:

```bash
python3 -m venv .venv-market-data
.venv-market-data/bin/pip install -r requirements-market-data.txt
.venv-market-data/bin/python -m market_data.sync \
  --db .data/market-data.sqlite3 --timeframe 15m \
  --start-ms 1793232000000 --end-ms 1793239200000
.venv-market-data/bin/python -m market_data.sync \
  --db .data/market-data.sqlite3 --timeframe 1h \
  --start-ms 1793232000000 --end-ms 1793239200000
```

Ví dụ lấy khoảng **2026-10-29 00:00–02:00 UTC**, đầu gồm/cuối loại trừ. Chọn cửa sổ đã đóng phù hợp khi chạy. `start-ms`/`end-ms` phải thẳng biên khung giờ UTC và mỗi lần tối đa 2.000 nến (20,8 ngày M15 hoặc 83,3 ngày H1). Chia khoảng lớn thành nhiều cửa sổ kề nhau. CLI in số nến mới, `datasetVersion` và độ bao phủ; khoảng thiếu vẫn hiển thị, không được coi là tải thành công đầy đủ chỉ vì tiến trình thoát mã 0.

Đây là tác vụ một lần; gọi lại để đồng bộ cửa sổ mới hoặc tải lại khoảng thiếu. CCXT bật rate limiting và timeout, kiểm tra metadata đúng `BTC/USDT:USDT`, linear/swap/USDT settlement, và lấy giờ công khai của sàn. Chỉ nhận nến đóng trước cả mốc giờ sàn ở đầu lượt đồng bộ và giờ máy chủ khi nhận phản hồi. Đồng hồ máy chủ phía trước sàn không được làm nến đang chạy trở thành nến đã đóng.

Mỗi page tối đa 1.000 nến được ghi nguyên tử. Nếu page sau lỗi, các page trước vẫn còn; CLI thoát khác 0 và cho phép thử lại cửa sổ. Nến cùng khóa và OHLCV được bỏ qua; nến cùng khóa nhưng OHLCV khác khiến cả page bị rollback. Không âm thầm sửa lịch sử. Việc xử lý bản sửa từ sàn cần một thay đổi có kiểm soát riêng.

SQLite tiếp tục là mặc định. Sau khi đã áp dụng schema TimescaleDB trong một database staging riêng, có thể đồng bộ trực tiếp bằng `--postgres` thay cho `--db`. DSN chỉ được đọc từ biến môi trường, không truyền trên command line:

```bash
export MARKET_DATA_DATABASE_URL='postgresql://...'
python3 -m market_data.migrations
python3 -m market_data.sync --postgres --timeframe 15m \
  --start-ms 1793232000000 --end-ms 1793239200000
```

Không đưa DSN vào shell history hoặc commit. Lệnh `python3 -m market_data.migrations` áp dụng schema migration có checksum, fail-closed nếu nội dung migration đã áp dụng bị thay đổi. Repository không tự tạo schema khi khởi tạo hoặc đọc; chỉ lệnh migration tường minh mới tạo schema.


## API đọc

Cấu hình trong môi trường chạy, không commit giá trị token:

| Biến | Nội dung |
| --- | --- |
| `MARKET_DATA_DB` | Đường dẫn SQLite; vẫn là backend mặc định và là database paper ledger trong chế độ hỗn hợp |
| `MARKET_DATA_DATABASE_URL` | Tùy chọn PostgreSQL/TimescaleDB DSN; chỉ chọn backend market data, không bao giờ dùng cho paper ledger |
| `MARKET_DATA_TOKEN` | Token riêng chỉ đọc, dùng header Bearer |
| `PORT` | Port phát triển, mặc định 8788 |

Tạo token bằng `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'`, lưu trong cấu hình máy chủ. Chạy từ gốc repo:

```bash
python3 -m market_data.api
```

Máy chủ phát triển chỉ bind `127.0.0.1`. Khi triển khai, cài Gunicorn đã khai báo trong `requirements-web.txt`, đặt sau HTTPS reverse proxy và chạy:

```bash
gunicorn --bind 127.0.0.1:8788 --workers 1 --threads 4 --timeout 20 market_data.api:application
```

### `GET /v1/candles`

Header: `Authorization: Bearer <MARKET_DATA_TOKEN>`.

```text
/v1/candles?symbol=BTCUSDT&timeframe=15m&startMs=1793232000000&endMs=1793239200000
```

`symbol`, `timeframe`, `startMs`, `endMs` là bắt buộc. Có thể thêm `asOfMs` để chỉ đọc nến được kho ghi nhận khả dụng trước hoặc đúng thời điểm đó. Không nhận tham số lặp, tham số lạ, token trong URL hoặc khoảng vượt 2.000 nến. Phân trang bằng các cửa sổ thời gian kế tiếp; không cắt ngầm dữ liệu rồi báo thành khoảng thiếu.

Phản hồi gồm:

| Trường | Ý nghĩa |
| --- | --- |
| `exchange`, `marketType`, `symbol`, `timeframe` | Định danh cố định của nguồn futures; không trộn spot/OKX |
| `startMs`, `endMs`, `asOfMs` | Phạm vi đọc, UTC milliseconds, `[startMs,endMs)` |
| `candles` | Nến đã đóng theo thứ tự tăng dần |
| `coverage.expected`, `returned`, `complete` | Số ô nến kỳ vọng, số nến có thật, có thiếu hay không |
| `coverage.gaps` | Các đoạn thiếu `{startMs,endMs}`, cùng quy ước đầu gồm/cuối loại trừ |
| `datasetVersion` | SHA-256 nội dung và phạm vi đọc, bao gồm provenance/thời điểm khả dụng; không phải hash toàn bộ database |
| `generatedAtMs` | Thời điểm tạo phản hồi; không dùng làm thời điểm cập nhật nến |

Mỗi nến có `openTimeMs`, `closeTimeMs` (biên cuối **loại trừ**), các chuỗi decimal `open/high/low/close/volume`, `isClosed=true`, `availableAtMs`, `availabilityKind=FIRST_OBSERVED`, `quality=VALIDATED`, `source=ccxt.binanceusdm` cùng định danh thị trường/khung. `VALIDATED` xác nhận các điều kiện hình dạng/OHLC/thời gian đã kiểm tra, không chứng nhận độ chính xác tuyệt đối của sàn.

Các số decimal được lưu và trả về không tính toán qua float trong kho. CCXT thường đã parse OHLCV thành float; chuyển `str(value)` không khôi phục được chữ số nguồn đã mất. Trường hợp cần lưu nguyên văn payload sàn phải bổ sung raw adapter riêng.

### Ngữ nghĩa thời gian và chất lượng

- `availableAtMs` là giờ máy chủ khi nhận page từ sàn ở lần ghi đầu tiên. Import lại không thay mốc này, kể cả khi truyền mốc sớm hơn.
- Import lịch sử hôm nay không chứng minh nến đã được hệ thống biết trong quá khứ. `asOfMs` trước thời điểm import sẽ trả thiếu; không bịa thời điểm khả dụng để backtest đẹp hơn.
- Dữ liệu lịch sử vẫn dùng được cho nghiên cứu OHLCV với giả định khả dụng được công bố riêng. Chưa cung cấp chứng nhận replay point-in-time/walk-forward hay adapter Freqtrade tự động.
- API trả HTTP 200 với `complete=false` cho khoảng thiếu hoặc kho trống. Consumer phải kiểm tra coverage; không tự forward-fill hoặc gán số 0.
- Khóa nến gồm sàn/thị trường/cặp/khung/thời gian mở. OHLC hữu hạn, giá dương, volume không âm và ràng buộc high/low được kiểm tra trước khi ghi và khi đọc.

### Lỗi và health

| HTTP | Mã lỗi |
| --- | --- |
| 400 | `INVALID_QUERY` |
| 401 | `UNAUTHORIZED` |
| 404 | `NOT_FOUND` |
| 405 | `METHOD_NOT_ALLOWED` |
| 503 | `UNCONFIGURED` hoặc `STORE_UNAVAILABLE` |

API không tạo database khi thiếu file, không gọi sàn trong request và không có endpoint ghi/lệnh giao dịch. `GET /health` chỉ báo tiến trình hoạt động, không xác nhận database đã có dữ liệu hay feed đang chạy. Lỗi không trả token, đường dẫn SQLite hoặc nội dung exception.

## Kiểm chứng

Kiểm thử SQLite và contract chạy trên Codemagic với workflow `canonical-market-data`. Kiểm thử TimescaleDB thật chạy riêng, thủ công bằng workflow `market-data-postgres-integration`. Trước khi chạy, tạo variable group `market_data_postgres_test` trong Codemagic và thêm `MARKET_DATA_TEST_DATABASE_URL` (Secret) cùng `MARKET_DATA_TEST_DB_CONFIRMATION` (tên database test chính xác). Database phải là database kiểm thử riêng có extension TimescaleDB; test từ chối database không có tên chứa `test` hoặc confirmation không khớp. GitHub chỉ lưu source/PR; mọi action/test chạy trên Codemagic. Xem [hướng dẫn Codemagic](../docs/CODEMAGIC_SETUP.md) để cài đặt tài khoản và tải log/artifact.

```bash
python3 -m unittest market_data.test_store market_data.test_sync market_data.test_api market_data.test_repository integrations.test_hummingbot_bridge -v
```

Các kiểm thử dùng SQLite thật, handler WSGI thật và giả lập duy nhất kết nối CCXT ngoài hệ thống. Có kiểm tra pagination, metadata thị trường, nến đang chạy, dữ liệu sai/trùng/xung đột, timestamp khả dụng, gaps, hash và xác thực. Không cần CCXT cho bộ kiểm thử offline; cài gói và kết nối Binance thật là kiểm chứng riêng, chưa được suy ra từ test giả lập.

Nguồn adapter: [CCXT binanceusdm](https://github.com/ccxt/ccxt/blob/master/python/ccxt/binanceusdm.py), [Binance fetch_ohlcv/fetch_time](https://github.com/ccxt/ccxt/blob/master/python/ccxt/binance.py), [Freqtrade data download](https://github.com/freqtrade/freqtrade/blob/develop/docs/data-download.md). Bước sau: xuất dataset dùng chung cho nghiên cứu Freqtrade/FreqAI và nối đặc trưng trinh sát theo [kiến trúc 5 tầng](../docs/FIVE_LAYER_ARCHITECTURE.md).
