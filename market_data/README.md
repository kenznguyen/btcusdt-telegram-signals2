# Canonical market data — tầng 0

Kho nến dùng chung cho các tầng phân tích. Bản đầu hỗ trợ **Binance USDⓈ-M perpetual BTCUSDT**, khung **15m/1h**, SQLite và API WSGI chỉ đọc. Bộ đồng bộ lấy OHLCV qua CCXT; không cần API key sàn. Chưa thay nguồn OKX của Python bot/backtest hay nguồn trực tiếp trong APK.

## Đồng bộ qua Gateway có fencing

`market_data.sync.sync_window()` chỉ nhận `T0WriteGateway`, `LeaseFence` và `lease_clock` bắt buộc. Không còn đường ghi legacy qua `CandleStore.insert()` hoặc `insert_fenced()` trong luồng đồng bộ. Mỗi page tối đa 1.000 nến được ghi nguyên tử; nếu page sau lỗi, các page trước vẫn còn. `available_at_ms` dùng observation clock; Gateway kiểm tra lease bằng lease clock riêng ngay tại transaction admission.

CLI chỉ chạy khi database SQLite đã được provision và caller cung cấp lease owner/generation đang còn hiệu lực trong chính database đó. CLI không tự tạo database, không tự acquire lease và không fallback sang PostgreSQL:

```bash
python3 -m venv .venv-market-data
.venv-market-data/bin/pip install -r requirements-market-data.txt
T0_FEEDER_OWNER_ID=<active-owner> \
T0_FEEDER_LEASE_GENERATION=<active-generation> \
.venv-market-data/bin/python -m market_data.sync \
  --db <existing-canonical.sqlite3> --timeframe 15m \
  --start-ms 1793232000000 --end-ms 1793239200000
```

Chỉ dùng CLI khi lease đã được cấp bởi runtime được quản lý. Không tự điền generation hoặc giả lập lease. `start-ms`/`end-ms` phải thẳng biên UTC và mỗi lần tối đa 2.000 nến. CCXT bật rate limiting/timeout và xác minh đúng thị trường Binance USD-M BTCUSDT perpetual. Nến chỉ được nhận khi đã đóng theo cả exchange clock và observation clock.

Schema provisioning là thao tác riêng, tường minh qua `CandleStore.initialize_schema()` và `LeaseStore.initialize_schema()` trên một DB được chỉ định rõ. Constructor, read API, runtime lease transaction và Gateway không tự tạo schema hoặc file. Không gọi các hàm provisioning trên canonical DB nếu chưa được phê duyệt.

## API đọc

Cấu hình trong môi trường chạy, không commit giá trị token:

| Biến | Nội dung |
| --- | --- |
| `MARKET_DATA_DB` | Đường dẫn SQLite đã tạo bằng tác vụ sync |
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

CI chạy trên Codemagic với workflow `canonical-market-data`, cấu hình tại `codemagic.yaml`. GitHub chỉ lưu source/PR; không chạy GitHub Actions. Xem [hướng dẫn Codemagic](../docs/CODEMAGIC_SETUP.md) để cài đặt tài khoản và tải log/artifact.

```bash
python3 -m unittest market_data.test_store market_data.test_sync market_data.test_api integrations.test_hummingbot_bridge -v
```

Các kiểm thử dùng SQLite thật, handler WSGI thật và giả lập duy nhất kết nối CCXT ngoài hệ thống. Có kiểm tra pagination, metadata thị trường, nến đang chạy, dữ liệu sai/trùng/xung đột, timestamp khả dụng, gaps, hash và xác thực. Không cần CCXT cho bộ kiểm thử offline; cài gói và kết nối Binance thật là kiểm chứng riêng, chưa được suy ra từ test giả lập.

Nguồn adapter: [CCXT binanceusdm](https://github.com/ccxt/ccxt/blob/master/python/ccxt/binanceusdm.py), [Binance fetch_ohlcv/fetch_time](https://github.com/ccxt/ccxt/blob/master/python/ccxt/binance.py), [Freqtrade data download](https://github.com/freqtrade/freqtrade/blob/develop/docs/data-download.md). Bước sau: xuất dataset dùng chung cho nghiên cứu Freqtrade/FreqAI và nối đặc trưng trinh sát theo [kiến trúc 5 tầng](../docs/FIVE_LAYER_ARCHITECTURE.md).
