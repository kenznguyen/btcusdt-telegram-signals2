# Chạy thử Data Lake trên máy tính

Gói này chạy PostgreSQL 17 và FastAPI bằng Docker Compose trên máy tính của bạn.
API chỉ mở tại `127.0.0.1`; PostgreSQL không mở cổng ra host. Collector được bật
riêng sau khi kiểm tra API. Gói không khởi động FreqAI, Hummingbot hoặc đặt lệnh.

## 1. Chuẩn bị và khởi động

Cần Docker Desktop/Docker Engine đang chạy, Docker Compose v2 và Python 3.10+.
Chuyển checkout sang nhánh **`feature/local-data-lake`**, mở terminal tại thư mục
gốc repository. Nếu máy dùng tên lệnh `python3`, thay `python` bằng `python3`.

```bash
python -m data_lake.local_setup
docker compose --env-file .data/local-lake.env -f deploy/data-lake/compose.yaml up -d --build
python -m data_lake.local_setup --check
```

Lần build image đầu cần tải image/dependency. Chạy lại lệnh kiểm tra sau khi
container khởi động. Kết quả ban đầu mong đợi:

```json
{"service":"canonical-data-lake","ready":true,"freshData":false}
```

`ready: true` nghĩa là API đọc được schema DB bằng tài khoản chỉ đọc.
`freshData: false` là bình thường khi kho chưa có nến mới, không phải lỗi khởi động.
`/health` chỉ báo tiến trình; `/ready` yêu cầu token và kiểm tra khả năng đọc kho.

Nếu cổng 8788 đang được dùng, chọn cổng khi tạo cấu hình lần đầu:

```bash
python -m data_lake.local_setup --port 8899
```

Tệp cấu hình đã tồn tại sẽ được giữ nguyên, không tự đổi mật khẩu/token hoặc cổng.
Nếu cần đổi cổng sau đó, chỉ sửa `LAKE_API_PORT` trong tệp cục bộ rồi chạy lại
`compose up -d`. Không đặt các biến `LAKE_*` khác trong shell để ghi đè cấu hình.

## 2. Nạp một ít dữ liệu thật

Sau khi API sẵn sàng, chạy một lượt lấy tối đa 20 nến đóng cho mỗi khung M15/H1:

```bash
docker compose --env-file .data/local-lake.env -f deploy/data-lake/compose.yaml run --rm collector refresh --bars 20
python -m data_lake.local_setup --check
```

Lệnh này gọi nguồn Binance public bằng CCXT có rate limit. Nếu nguồn không truy
cập được, collector báo lỗi và giữ dữ liệu thiếu; không sinh nến mẫu. `freshData`
chỉ đạt khi đủ hai nến đóng mới nhất ở cả hai khung tại thời điểm kiểm tra.

Để đồng bộ nền mỗi 60 giây, bật profile collector:

```bash
docker compose --env-file .data/local-lake.env -f deploy/data-lake/compose.yaml --profile collector up -d
```

Collector mặc định xem 2.000 slot gần nhất và chỉ tải đoạn còn thiếu. Có thể
backfill lịch sử bằng cùng container writer; ví dụ tháng 1/2026:

```bash
docker compose --env-file .data/local-lake.env -f deploy/data-lake/compose.yaml run --rm collector backfill --timeframe 15m --start-ms 1767225600000 --end-ms 1769904000000
```

## 3. Dữ liệu và tài khoản

PostgreSQL lưu dữ liệu trong volume `lake-data` của project `chart-lake-local`.
Bootstrap khởi tạo idempotent bằng code schema hiện có; chạy lại không xóa nến.
API dùng `lake_reader` với quyền SELECT và transaction mặc định chỉ đọc.
Collector dùng `lake_collector`; mật khẩu owner chỉ có ở PostgreSQL/bootstrap.

Lệnh setup tạo **`.data/local-lake.env`** với bốn bí mật riêng và cổng API:
`LAKE_OWNER_PASSWORD`, `LAKE_READER_PASSWORD`, `LAKE_WRITER_PASSWORD`,
`LAKE_READ_TOKEN`, `LAKE_API_PORT`. Chỉ `LAKE_READ_TOKEN` được ánh xạ thành
`MARKET_DATA_TOKEN` bên trong API. Trên POSIX tệp được tạo với mode 0600;
Windows dùng quyền truy cập của tài khoản lưu checkout.

Giữ tệp này cùng với volume đã khởi tạo. Xóa/đổi mật khẩu trong tệp không tự đổi
mật khẩu owner của một DB đã tồn tại. Tệp bị Git/Docker build context bỏ qua;
setup không in nội dung bí mật. Không chia sẻ tệp hoặc đầu ra `docker compose config`
đầy đủ; dùng `config --quiet` nếu chỉ cần kiểm tra cấu hình.

## 4. Xem trạng thái và dừng

```bash
docker compose --env-file .data/local-lake.env -f deploy/data-lake/compose.yaml ps --all
docker compose --env-file .data/local-lake.env -f deploy/data-lake/compose.yaml logs --tail 100 api bootstrap
docker compose --env-file .data/local-lake.env -f deploy/data-lake/compose.yaml --profile collector down
```

Lệnh dừng trên giữ nguyên volume và tệp bí mật. Không thêm `-v` nếu muốn giữ DB.
Để chạy lại, dùng lệnh `up -d` ở bước đầu với chính tệp cấu hình cũ.

Địa chỉ `127.0.0.1` này dành cho chương trình trên máy tính. APK trên điện thoại
cần một địa chỉ HTTPS truy cập được; gói thử nghiệm này không thay đổi yêu cầu
HTTPS của APK. Hợp đồng nến, features và xuất Freqtrade nằm trong
[runbook Data Lake](../../data_lake/README.md).

## Kiểm thử

Nhánh này chạy regression và PostgreSQL trên Codemagic. Kiểm thử mới kiểm tra
readiness với DB thật và quyền reader không thể ghi, kể cả khi tắt mặc định
read-only của session. Workflow thủ công **`local-data-lake-smoke`** build/chạy
Compose trên Linux, kiểm tra API rỗng đúng trạng thái, xác thực và collector chưa
bật. Runner Linux trên Codemagic yêu cầu bật billing; đây là kiểm tra tùy chọn,
không cần để bạn chạy gói trên máy tính. Chưa chạy container thành công thì chưa
thể suy ra image đã được xác minh chỉ từ việc YAML hợp lệ.
