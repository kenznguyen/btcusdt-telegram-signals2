# Codemagic — các workflow còn được giữ lại

GitHub lưu source/nhánh/PR và GitHub Actions là runner CI chuẩn của repository. Codemagic chỉ còn các workflow được giữ lại trong `codemagic.yaml`; không coi đây là runner chính của Hệ thống 5 tầng. Ba workflow Python Telegram/scanner/backtest cũ đã được gỡ. Việc đổi source không tự thay cài đặt trên các nhánh chưa merge hoặc runtime bên ngoài.

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
- Chạy toàn bộ kiểm thử kho nến/sync/API, gateway Hummingbot và chính sách CI; kiểm tra CLI/syntax.
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

## 4. Các workflow legacy đã gỡ

Các workflow ID `telegram-command`, `dashboard-backtest` và `signal-scan` không còn được định nghĩa trong `codemagic.yaml`. Các bản GitHub Actions lưu trữ tương ứng cũng đã được loại bỏ khỏi `ci/archive/github-actions`; các file cùng tên không tồn tại dưới `.github/workflows` trên branch này.

Không dùng Telegram webhook, `ci/run-legacy.py`, `bot.py`, `backtest.py` hoặc `telegram_commands.py` trong repository chung. Không thu hồi/xóa secrets, artifacts, cache, lịch sử build hoặc cấu hình tài khoản bên ngoài trong thay đổi source này. Các workflow Codemagic khác và GitHub Actions T0–T4 được giữ nguyên.

