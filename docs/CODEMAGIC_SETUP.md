# Codemagic là nơi chạy tác vụ

GitHub chỉ lưu source/nhánh/PR. Không còn YAML thực thi trong `.github/workflows` ở nhánh này; các bản cũ nằm tại `ci/archive/github-actions`. Artifact mới và log được giữ ở Codemagic. Việc đổi source không tự thay cài đặt trên các nhánh chưa merge hoặc triển khai Render đang chạy phiên bản cũ.

## 1. Kết nối và chọn nhánh

1. Mở application `btcusdt-telegram-signals2` đã thêm vào Codemagic, chọn cấu hình YAML từ repository.
2. Dùng nhánh **`feature/android-five-layer-control`** để build APK có tab 5 tầng. Nhánh `feature/five-layer-paper` chứa bản tích hợp backend/React trước đó. Chỉ chọn `main` sau khi đã merge đủ source và `codemagic.yaml` mới.
3. Bật GitHub webhook của application để Codemagic nhận push. Các workflow tự động giới hạn nhánh/đường dẫn trong YAML, không tạo thêm runner GitHub Actions.
4. Trong **Start new build**, chọn workflow ID bên dưới. Xem log và artifact gắn với source SHA thực tế, không suy ra build đạt chỉ từ việc đã thêm YAML.

Không có công cụ Codemagic hoặc credential được cấu hình trong phiên làm việc này. Các thay đổi là source/configuration để review; chưa xác nhận build hay cài đặt bên ngoài đã thành công.

## 2. Kiểm thử dữ liệu và gateway

Nhánh `feature/five-layer-paper` bổ sung kiểm thử toàn luồng paper và workflow React `five-layer-dashboard`. Workflow thủ công `freqai-strategy-smoke` cài Freqtrade/FreqAI 2026.9 để kiểm tra load strategy, không chạy train/trade. Xem [runbook 5 tầng](FIVE_LAYER_PAPER_RUNBOOK.md) để thiết lập runtime.

Workflow **`canonical-market-data`**:

- Tạo Python venv riêng; cài `requirements-market-data.txt`, `requirements-web.txt`, `requirements-ci.txt`.
- Kiểm tra import CCXT và Flask app.
- Chạy toàn bộ kiểm thử kho nến/sync/API, gateway Hummingbot, client Codemagic và chính sách CI; kiểm tra CLI/syntax.
- Thu `ci-source-sha.txt` và các file `*-tests.log`. Log unittest là log chữ, không gắn nhãn nhầm thành báo cáo JUnit.

Workflow này không cần API key sàn và không gọi Telegram hoặc phát lệnh giao dịch. Kiểm thử giả lập biên HTTP không chứng minh kết nối Codemagic/Binance thật.

## 3. APK debug và release

**`android-chart-pro-debug`** dùng JDK 17, Gradle 8.9 có SHA-256 pin, SDK 35 và Build Tools 34.0.0. Chạy gateway/artifact tests, `testDebugUnitTest` và `testParallelUnitTest`, rồi `assembleDebug` và `assembleParallel`. Gate cuối dùng `aapt` kiểm tra package/label/launcher/version và `apksigner` xác minh chữ ký hai APK. Artifact: APK thường, **`BTC-5-Tang-Paper-<source SHA>.apk`**, JUnit XML/HTML, `android-source-sha.txt` và `android-apks.json` chứa SHA-256 APK/chứng chỉ.

Để cài song song, tải **`BTC-5-Tang-Paper-<source SHA>.apk`**. Tên launcher **BTC 5 Tầng Paper**, biểu tượng màu hổ phách, ID **`com.kenznguyen.btclivealerts.paper`**; mở mặc định tab 5 tầng. Bản thường giữ nguyên ID **`com.kenznguyen.btclivealerts`**, không bị thay thế. Dữ liệu/thiết lập/quyền/thông báo Android của hai app độc lập; **sổ paper trên server vẫn dùng chung nếu cùng API**. Muốn sổ thử riêng cần server/database riêng.

Bản parallel là APK debug để thử nghiệm. Cài cập nhật cần cùng chứng chỉ; debug keystore mới trên runner có thể khiến phải gỡ/cài lại riêng app Paper. Đối chiếu fingerprint trong `android-apks.json`; cấu hình ký release hiện có được giữ nguyên.

Nhánh `feature/android-five-layer-control` được phép kích hoạt workflow debug khi push thay đổi Android/CI và webhook đã kết nối. Có thể chọn nhánh này trong **Start new build**; đối chiếu `android-source-sha.txt` trước khi tải/cài APK. Chưa có kết quả build thì chưa có APK mới được xác minh.

Trong APK, mở **Hệ thống 5 tầng** và nhập HTTPS base URL của common API cùng read token `MARKET_DATA_TOKEN`. Tab này chỉ dùng BTCUSDT PAPER. `CONTROL_TOKEN` riêng là tùy chọn để đánh giá intent, tạm dừng/tiếp tục và hủy lệnh paper. App chỉ lưu base URL, giữ token trong bộ nhớ của màn hình; không nhập API key sàn. Server phải được triển khai riêng theo [runbook 5 tầng](FIVE_LAYER_PAPER_RUNBOOK.md), không chạy thường trực trong Codemagic.

**`android-chart-pro-release`** chỉ chạy thủ công. Trong Codemagic, tạo nhóm biến bảo mật **`android_release`**, cho application sử dụng nhóm này và nhập lại chính các giá trị keystore hiện có:

| Biến | Nội dung |
| --- | --- |
| `ANDROID_KEYSTORE_BASE64` | Base64 của keystore release đang dùng |
| `ANDROID_KEYSTORE_PASSWORD` | Mật khẩu keystore |
| `ANDROID_KEY_ALIAS` | `btc-chart-release` |
| `ANDROID_KEY_PASSWORD` | Mật khẩu key |

Không tạo key mới. Script giải mã vào file tạm quyền 0600, chạy unit tests/assembleRelease, kiểm tra apksigner và so SHA-256 chứng chỉ APK với key được cung cấp, rồi xóa file tạm. Artifact gồm APK, test reports, source SHA và fingerprint công khai; không gồm keystore/password.

Khớp alias không đủ chứng minh cập nhật được APK đã cài. Cần dùng đúng keystore cũ và kiểm tra cài đè trên thiết bị sau build. Không tự đăng Play Store hoặc triển khai release.

## 4. Chuyển webhook/dashboard runtime

Đặt trên Render/server chạy `app.py`:

| Biến | Nội dung |
| --- | --- |
| `CODEMAGIC_API_TOKEN` | Token Codemagic chỉ giữ ở server |
| `CODEMAGIC_APP_ID` | Application ID của repository này |
| `CODEMAGIC_BRANCH` | Nhánh đã có đầy đủ workflow mới; dùng `feature/android-five-layer-control` cho bản APK 5 tầng |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Bot/chat đã dùng trước đây |
| `TELEGRAM_WEBHOOK_SECRET` | Secret của webhook hiện có |

Deploy bridge mới cùng cấu hình Codemagic; không cần đổi URL webhook hoặc tạo webhook Telegram thứ hai. `GITHUB_TOKEN`, `GITHUB_WORKFLOW_FILE`, `GITHUB_REF` và `ACTIONS_GITHUB_TOKEN` không còn được dùng để chạy tác vụ. Không xóa secrets cũ ở tài khoản bên ngoài chỉ vì source đã đổi; việc thu hồi credential là công việc riêng.

Adapter dùng `POST https://api.codemagic.io/builds`, header `x-auth-token`, workflow ID cố định và các biến được allowlist. Lịch sử/artifact dùng hợp đồng `GET /builds` từng được tài liệu chính thức mô tả; khả năng tương thích hiện tại cần kiểm chứng bằng tài khoản thực tế. API trả lỗi nếu response không khớp, không bịa trạng thái build hoặc lặng lẽ quay lại GitHub Actions.

Artifact chỉ tải từ URL Codemagic hợp lệ và các đích lưu trữ redirect được cho phép, có giới hạn kích thước; token Codemagic không được chuyển sang storage host. Dashboard có thể đồng bộ các JSON/CSV cùng một build; nếu history/artifact API chưa tương thích, tải artifact từ Codemagic và dùng chức năng nạp file hiện có.

## 5. Tác vụ thủ công

Trong Codemagic tạo nhóm **`codemagic_legacy`** chứa `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`; thêm `CODEMAGIC_API_TOKEN`, `CODEMAGIC_APP_ID`, `CODEMAGIC_BRANCH` nếu cần khôi phục báo cáo cho `/btstatus` và `/btresult`.

| Workflow | Input | Kết quả |
| --- | --- | --- |
| `telegram-command` | `TELEGRAM_COMMAND`: help/status/position/signal/backtest/btstatus/btresult | Trả lời chat đã cấu hình; artifact backtest khi có |
| `dashboard-backtest` | `BACKTEST_DAYS`, `BACKTEST_INITIAL_CAPITAL`, `ENTRY_MARGIN_PCT`, `DCA_MARGIN_RATIO` | Các file `dashboard_backtest_*` |
| `signal-scan` | `LEGACY_STATE_JSON` chứa state mô phỏng đã xác minh | `state.json`, `state-provenance.json` và tín hiệu mô phỏng |

Tham số backtest: ngày 1–365, vốn 1–100.000.000, entry margin 1–100%, DCA 0–500%. Wrapper chuyển phần trăm sang fraction rõ ràng trước khi gọi engine. Mỗi build dùng `CM_BUILD_ID` làm Run ID để phân biệt báo cáo.

Scanner không có lịch tự động. Không dùng CI cache làm state có thẩm quyền. Khi chạy thủ công, cung cấp snapshot đúng trong `LEGACY_STATE_JSON`, giữ artifact đầu ra, rồi chuyển state mới sang lượt kế tiếp. Snapshot phải có `side`, `qty`, `avg_entry`, `account_balance`, số hữu hạn và vị thế hợp lệ; JSON rỗng không tự khởi tạo state mới. Không chạy chồng lấn. Đây là hand-off thủ công, chưa thay thế một kho state và bộ điều phối nguyên tử dùng chung; nếu cần scanner liên tục, phải triển khai phần đó riêng.

`/status` và `/position` cũng cần snapshot rõ ràng; thiếu/hỏng state báo không khả dụng. Không tự suy ra FLAT từ runner vừa khởi động. `.github/backtest-trigger.txt` không còn kích hoạt backtest khi push; dùng API hoặc Start new build trên Codemagic.

## 6. Nguồn cấu hình

- [YAML và environment](https://github.com/codemagic-ci-cd/codemagic-docs/blob/master/content/yaml-basic-configuration/yaml-getting-started.md): không có key `environment.python`; dùng Python của image và venv.
- [Image Xcode 26.3](https://github.com/codemagic-ci-cd/codemagic-docs/blob/master/content/specs-macos/xcode-26-3.md).
- [Codemagic REST builds](https://github.com/codemagic-ci-cd/codemagic-docs/blob/master/content/rest-api/builds.md).
- [Hợp đồng history cũ](https://github.com/codemagic-ci-cd/codemagic-docs/blob/3102fb2/content/rest-api/builds.md); chưa chứng nhận tương thích live.
## Kiểm thử kho dữ liệu PostgreSQL

Nhánh `feature/data-lake-api` có workflow `data-lake-postgres`: cài dependency
FastAPI/psycopg/pyarrow, khởi động PostgreSQL 17 tạm thời, chạy kiểm thử DB/API/export
thật và dọn server khi kết thúc. `DATA_LAKE_REQUIRE_POSTGRES=1` buộc lỗi nếu thiếu
DB/driver, không coi kiểm thử bị bỏ qua là đạt. Xem
[runbook data lake](../data_lake/README.md) để chạy dịch vụ thường trực ngoài CI.

Nhánh `feature/local-data-lake` cũng chạy hai workflow Python hiện có. Workflow
**`local-data-lake-smoke`** chỉ chạy thủ công trên `linux_x2` để build và thử Compose;
không bật collector hoặc gọi sàn. Runner Linux yêu cầu billing trên Codemagic;
có thể thử trực tiếp trên máy tính theo [hướng dẫn local](../deploy/data-lake/README.md).
