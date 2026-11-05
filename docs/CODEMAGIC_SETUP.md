# Codemagic — kiểm thử và build hệ thống 5 tầng

GitHub lưu source/branch/PR/evidence. Codemagic chạy các action theo `codemagic.yaml`. Không có GitHub Actions workflow thực thi trong nhánh này. Mỗi kết quả phải gắn với source SHA, workflow run và artifact thực tế; không suy ra PASS từ YAML.

## 1. Android Paper APK

Workflow duy nhất: **`five-layer-android`**.

- JDK 17, Gradle 8.9 có SHA-256 pin, Android SDK 35 và Build Tools 34.0.0.
- Chạy `ci.test_five_layer_android_boundary` và `ci.test_five_layer_android_apk`.
- Chạy `:app:testDebugUnitTest`.
- Build duy nhất `:app:assembleDebug`.
- Kiểm tra package `com.kenznguyen.btclivealerts.paper`, launcher `MainActivity`, app label, DEX không chứa lớp Chart Pro, manifest không có StrategyMonitorService/foreground service và chữ ký APK.
- Artifact: `BTCUSDT-Quant-System-Paper-<source SHA>.apk`, JUnit XML/HTML, `android-source-sha.txt`, `android-apk.json`.

Không còn workflow `android-chart-pro-debug`, `android-chart-pro-release`, parallel-install APK hoặc release signing group `android_release`. Ứng dụng 5 tầng hiện chỉ build debug-signed APK; chưa cấu hình release distribution.

## 2. Backend, data và React

- `canonical-market-data`: T0/T1, Hummingbot gateway, paper API, risk/ledger contracts và Python CI policy.
- `five-layer-dashboard`: npm frozen install, React tests, build và npm audit.
- `freqai-strategy-smoke`: Freqtrade/FreqAI 2026.9 strategy-load smoke ở dry-run; không train model, không kết nối giao dịch.
- `market-data-timescaledb`: disposable TimescaleDB integration.
- `market-data-kraken-*`: isolated Kraken Spot adapter/store/read API tests; không nhập Spot data vào canonical Futures.

Codemagic là runner tác vụ hữu hạn, không phải host T0 Feeder, API, Hummingbot hoặc model runtime. Các dịch vụ đó cần môi trường triển khai riêng, có persistent storage và supervision.

## 3. Kết nối

1. Mở application `btcusdt-telegram-signals2` trong Codemagic.
2. Chọn YAML từ repository và bật GitHub webhook để nhận push.
3. Chọn đúng workflow ID và branch đã được allowlist trong `codemagic.yaml`.
4. Sau khi hoàn tất, kiểm tra workflow conclusion, source SHA, test logs và artifact gắn với cùng run.
5. Ghi lại bằng chứng vào evidence report và `docs/PROJECT_SESSION_HANDOFF.md`.

Phiên làm việc hiện tại không có quyền xem Codemagic run trực tiếp; nếu không có kết quả từ Codemagic, trạng thái build phải ghi **NOT VERIFIED**.

## 4. Các workflow legacy

Các workflow Telegram command/dashboard backtest/signal scan vẫn còn trong YAML vì là tiện ích legacy độc lập. Chúng không phải thành phần T0–T4, không được phép tự khởi tạo canonical state và không được dùng để chứng minh paper ledger của hệ thống 5 tầng.
