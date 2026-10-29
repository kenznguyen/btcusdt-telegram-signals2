# Chạy thử hệ thống 5 tầng — paper v1

Đã có mã nguồn nối cả năm tầng qua API và paper ledger. Đây là bản tích hợp
**paper**, chưa phải hệ thống đã triển khai/kiểm chứng trên server thực tế.
Không có endpoint đặt lệnh thật. Thiếu dữ liệu/model hợp lệ thì trả `WAIT`.

| Tầng | Mã nguồn | Hiện trạng |
| --- | --- | --- |
| 0 | `market_data/` | Kho SQLite, đồng bộ nến CCXT và API M15/H1 |
| 1 | `futures_intelligence/` | CSV collector → funding/OI/taker delta/thanh lý quan sát; có coverage/hash |
| 2 | `freqai_bridge/`, `pipeline/decision.py` | Strategy chỉ xuất dự báo FreqAI; xác minh canonical window, provenance và freshness trước tạo intent |
| 3 | `paper_execution/` | Lệnh/vị thế/phí/PnL mô phỏng có lưu bền vững, pause/cancel và idempotency |
| 4 | `control_dashboard/`, `pipeline/api.py` | React và API chung; quyền đọc và điều khiển paper tách riêng; APK dùng được endpoint Order Book chung |

## 1. Runtime và CI

**GitHub chỉ lưu source/PR. Codemagic chạy kiểm thử/build** theo `codemagic.yaml`:

- `canonical-market-data`: kiểm thử Python cũ và toàn luồng paper mới.
- `five-layer-dashboard`: npm frozen install không chạy dependency scripts, Node tests, build React và npm audit. Artifact `control_dashboard/dist/**`.
- `freqai-strategy-smoke`: chạy thủ công, cài Freqtrade/FreqAI 2026.9 và kiểm tra load strategy; không train, không kết nối exchange/trade.
- Các workflow Android và legacy vẫn giữ theo [CODEMAGIC_SETUP.md](CODEMAGIC_SETUP.md).

Nhánh tích hợp mới: `feature/five-layer-paper`. Chọn nhánh có YAML mới khi Start
new build. Không coi YAML hay kiểm thử giả lập là chứng cứ build/install/model
training đã thành công.

API, collector và FreqAI shadow cần chạy ở server/process có ổ đĩa bền vững;
Codemagic là runner tác vụ hữu hạn, không dùng làm host scanner/API liên tục.
Mã v1 cung cấp các lệnh ingestion theo cửa sổ; lịch đồng bộ liên tục, retention,
giám sát vận hành và HA chưa được triển khai.

## 2. Chuẩn bị tầng 0 và paper ledger

Dùng Python 3.10+ từ thư mục gốc repo:

```bash
python3 -m venv .venv-market-data
.venv-market-data/bin/pip install -r requirements-market-data.txt -r requirements.txt -r requirements-web.txt -r requirements-ci.txt
```

Chạy [đồng bộ CCXT](../market_data/README.md) cho BTCUSDT, 15m/1h, trên cửa sổ
đã đóng. Ghi vào `.data/market-data.sqlite3`. Kho API không tự tải nến trong HTTP
request. Giai đoạn đầu chỉ một writer đồng bộ có kiểm soát; nến xung đột bị từ
chối thay vì sửa lịch sử.

Khởi tạo paper account **rõ ràng bằng CLI**, không thông qua GET:

```bash
.venv-market-data/bin/python -m paper_execution --db .data/market-data.sqlite3
```

GET `/v1/paper` chỉ đọc database/ledger đã khởi tạo. Thiếu/hỏng state báo 503,
không tạo lại tài khoản zero hoặc làm mất vị thế cũ. Các lệnh điều khiển chỉ
thực thi khi có store và control token hợp lệ.

## 3. Tầng 1: dữ liệu quan sát thật

Chạy collector được chọn tại commit đã pin theo [hướng dẫn upstream](https://github.com/waynemason1/binance-futures-collector/tree/bc4f0ef633fbeee4a49defd72827f17162693805).
Chỉ bật BTCUSDT và giữ dữ liệu thô ở server. Adapter hiện nhận đúng header CSV
upstream, không nhận JSON tùy ý hoặc giả là đã kết nối Rust collector.

Xem [futures_intelligence/README.md](../futures_intelligence/README.md) để nhập
các file của cửa sổ cần phân tích:

```text
python -m futures_intelligence.import_collector
  --start-ms <UTC-ms-đầu-cửa-sổ> --end-ms <UTC-ms-cuối-cửa-sổ>
  --trades <CSV-trades> --funding <CSV-funding>
  --open-interest <CSV-OI> --liquidations <CSV-liquidations>
  --output .data/intelligence.json
```

Các cờ feed là tùy chọn; feed thiếu có giá trị null và trạng thái MISSING.
Header, thị trường, số hữu hạn, timestamp UTC, trade-ID trùng/xung đột và gap
được kiểm tra. Artifact được thay nguyên tử và có content hash. Giá trị funding,
OI và thanh lý giữ riêng với taker flow; giao dịch lớn không được gọi là dòng
tiền ví cá voi on-chain.

Coverage là **OBSERVED_ONLY**, không chứng nhận toàn bộ tape/đầu-cuối cửa sổ.
Decision v1 cần observed trades không có gap ID phát hiện được và trade cuối
còn mới; dữ liệu thiếu/cũ không được điền 0. CSV nhập tối đa 100.000 dòng và
64 MiB/file; dùng export theo cửa sổ cho file capture lớn. Chưa có tailer streaming
được kiểm chứng. Không dùng live order book của collector để chứng nhận execution.

## 4. Tầng 2: FreqAI thật và provenance

Làm theo [freqai_bridge/README.md](../freqai_bridge/README.md): cài đúng
Freqtrade/FreqAI **2026.9**, chuẩn bị lịch sử, chạy nghiên cứu và model shadow.
Strategy `ChartProFreqaiResearch` gọi FreqAI thật và tắt native entry/exit;
không biến Freqtrade thành executor thứ hai.

Producer đọc cùng SQLite, chọn hai nến M15 vừa đóng và so OHLCV với DataFrame
FreqAI. Đặt provenance sidecar từ job train thật: model fingerprint/version,
training dataset hash, cutoff gồm cả label horizon, thời điểm train xong và
identifier. Không tự suy các trường này từ đồng hồ hiện tại. Chưa có bộ tự động
trích xuất/kiểm chứng provenance cho mọi kiểu saved model.

Output mặc định: `.data/freqai-prediction.json`. Missing/outlier prediction,
sidecar thiếu, nguồn nến không khớp hoặc model quá mới/cũ sẽ tạo unavailable/WAIT.
Không có model demo, không thay dự báo AI bằng một quy tắc chỉ báo rồi gắn nhãn AI.

## 5. Tầng 3: Hummingbot snapshot và mô phỏng

Cấu hình Hummingbot API theo [integrations/README.md](../integrations/README.md).
Các Basic credentials chỉ ở server. API chung sử dụng cùng request market-data
đã kiểm tra; không gọi endpoint tạo/hủy lệnh thật.

Paper engine áp dụng limit với độ sâu đang hiển thị, cap khối lượng, spread và
vị thế; có khớp một phần, lệnh pending, cancel, pause, phí và PnL theo từng mức
giá. Cùng intent/same payload trả kết quả cũ; cùng ID/khác payload bị từ chối.
Không tái sử dụng một snapshot đã tạo fill cho intent khác. Lệnh pending chặn
target cạnh tranh cho đến khi được hủy. Không tự khớp tiếp qua các snapshot sau.

Đây là mô hình snapshot, không mô phỏng được đầy đủ queue position, latency,
margin/leverage hoặc liquidation của tài khoản thật. Timestamp Hummingbot là lúc
lấy snapshot, không phải chứng cứ sequence đã đồng bộ.

## 6. API chung và React

Đặt biến server, không commit token:

| Biến | Nội dung |
| --- | --- |
| `MARKET_DATA_DB` | SQLite đã có canonical data/paper ledger |
| `MARKET_DATA_TOKEN` | Quyền đọc API |
| `CONTROL_TOKEN` | Token **khác** token đọc; chỉ điều khiển paper |
| `INTELLIGENCE_REPORT_PATH` | File JSON tầng 1 đã publish |
| `FREQAI_REPORT_PATH` | File JSON dự báo thật đã publish |
| `HB_API_URL`, `HB_API_USER`, `HB_API_PASSWORD` | Kết nối Hummingbot phía server |
| `PAPER_TARGET_BASE` | Target mỗi hướng, mặc định 0.001 BTC |
| `PAPER_MAX_POSITION_BASE` | Giới hạn vị thế paper, mặc định 0.01 BTC |
| `PAPER_FEE_RATE` | Phí mô phỏng, mặc định 0.0005 |
| `PAPER_MAX_SPREAD_BPS` | Spread tối đa paper, mặc định 50 bps |
| `CONTROL_DIST_PATH` | Thư mục React dist, mặc định `control_dashboard/dist` |

Các giá trị mặc định là cấu hình mô phỏng, không phải chiến lược giao dịch đã
được đánh giá. Dùng cùng chính sách khi có nhiều API worker; thay cấu hình phải
được review. Client không được gửi giá/model/book hoặc chuyển `mode=LIVE` vào API.

```bash
gunicorn --bind 127.0.0.1:8789 --workers 1 --threads 4 --timeout 30 pipeline.api:application
```

Đặt sau HTTPS reverse proxy; dùng disk volume bền vững và giới hạn request tại
proxy. Các quyền điều khiển có ngân sách chung SQLite 30 request/phút UTC cho
mỗi store. GET có bearer riêng; không mở CORS wildcard. Không đặt API key sàn ở UI.

Build React bằng [control_dashboard/README.md](../control_dashboard/README.md)
hoặc tải `dist` artifact từ Codemagic, rồi mở `/control/`. Token chỉ giữ trong
bộ nhớ tab. Nếu dist chưa build, server trả DASHBOARD_NOT_BUILT; không phục vụ UI giả.
Vite dev có proxy `/v1` về `127.0.0.1:8789` nên không cần đổi CORS.

Các endpoint nằm trong [pipeline/CONTRACTS.md](../pipeline/CONTRACTS.md).
Nút Evaluate chỉ dùng dữ liệu server đã kiểm tra. Pause ngăn intent mới;
cancel hủy phần paper còn pending, không xóa fill/position. Không có nút flatten
tự động hoặc live order. Readiness phân biệt CONFIGURED/OBSERVED/WAIT với READY.

APK hiện có thể trỏ nguồn Hummingbot vào base URL API chung và dùng token đọc
với `/v1/order-book?symbol=BTCUSDT`. Giao diện native chưa được chuyển toàn bộ
sang dashboard này; chưa tạo hoặc xác minh APK mới trong thay đổi này.

## 7. Kiểm chứng và phần còn cần chạy thật

```bash
python3 -m unittest market_data.test_store market_data.test_sync market_data.test_api -v
python3 -m unittest discover -s integrations -p 'test_*.py' -v
python3 -m unittest discover -s ci -p 'test_*.py' -v
python3 -m unittest futures_intelligence.test_import_collector pipeline.test_decision pipeline.test_api paper_execution.test_ledger freqai_bridge.test_exporter -v
cd control_dashboard
npm test
```

Kiểm thử toàn luồng dùng CSV fixture, SQLite/WSGI/Decimal thật và prediction/book
fixture ở biên ngoài. Có kiểm thử replay idempotent, trạng thái thiếu/cũ/tương lai,
at-rest corruption, quyền đọc/ghi, rate budget, multiple-price reversal và restart.
Không coi fixture là dữ liệu model/exchange đã chạy thật.

Chưa xác minh: cài/chạy Freqtrade/FreqAI, train model/provenance, connector
Hummingbot/Binance thật, frozen npm install/build/audit/browser render, hosting
và vận hành liên tục. Môi trường hiện không tải được npm registry. Codemagic đã
được cấu hình cho kiểm thử backend, install/build/audit React và kiểm tra nạp
strategy; train model, kiểm tra browser và triển khai server là các bước riêng.
