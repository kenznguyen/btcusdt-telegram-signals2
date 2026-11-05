# BTCUSDT Quant System — Android Paper Client

Ứng dụng Android độc lập cho hệ thống 5 tầng. APK chỉ kết nối API chung để đọc trạng thái T0–T4, dữ liệu futures intelligence, quyết định chiến lược, chất lượng dữ liệu, equity, audit log, Hummingbot Order Book và paper ledger.

- Application ID: `com.kenznguyen.btclivealerts.paper`
- Launcher: `BTCUSDT Quant System · 5 Tầng`
- Build: một APK duy nhất; không còn build type parallel.
- Giữ nguyên application ID của bản 5 tầng parallel cũ để cài đè/nâng cấp và giữ dữ liệu ứng dụng hiện có.
- Chế độ: PAPER ONLY. Không có exchange order endpoint, API key sàn hoặc live execution.
- Không còn chart UI, scanner đa symbol, Binance chart engine, chart alerts, in-app backtest hoặc Strategy Monitor service trong ứng dụng này.

## Build và kiểm thử

Codemagic workflow: `five-layer-android`.

Workflow chạy:
1. Static boundary tests: `ci.test_five_layer_android_boundary`.
2. APK verifier contracts: `ci.test_five_layer_android_apk`.
3. Android unit tests: ` :app:testDebugUnitTest `.
4. Build: ` :app:assembleDebug `.
5. Verify application ID, launcher, label, DEX payload, manifest permissions/service, signing certificate và exact source SHA.

Máy local cần JDK 17, Gradle 8.9 và Android SDK 35 / Build Tools 34.0.0:

```bash
gradle :app:testDebugUnitTest :app:assembleDebug --no-daemon
```

Repository chưa có Gradle wrapper. Artifact CI dự kiến:
- `BTCUSDT-Quant-System-Paper-<source SHA>.apk`
- `android-source-sha.txt`
- `android-apk.json`
- JUnit XML/HTML.

Chỉ cài APK sau khi Codemagic build và artifact gate thành công trên đúng source SHA. Build cấu hình không phải bằng chứng APK đã được tạo hoặc chạy trên thiết bị.

## Kết nối API

Mở ứng dụng, nhập HTTPS base URL của common API và read token `MARKET_DATA_TOKEN`. App lưu base URL; token chỉ tồn tại trong bộ nhớ màn hình và cần nhập lại sau khi rời màn hình/khởi động lại.

`CONTROL_TOKEN` là token riêng, tùy chọn, chỉ dùng cho các thao tác paper được API cho phép. Không nhập API key Binance/OKX hoặc credentials Hummingbot vào APK.

Ứng dụng đọc dữ liệu BTCUSDT từ API chung. Hummingbot snapshot được hiển thị tách biệt; timestamp nhận snapshot không phải bằng chứng sequence đã đồng bộ hoặc khả năng khớp lệnh.

## Các giới hạn

- Thiếu/cũ/sai provenance hoặc dữ liệu không hợp lệ phải hiển thị unavailable/WAIT, không thay bằng 0.
- Equity, PnL, trạng thái vị thế và lịch sử được đọc từ server paper ledger; APK không tự tạo sổ trạng thái riêng.
- Không tự gửi lại paper command khi timeout chưa xác định kết quả.
- Codemagic là runner hữu hạn; API, T0 Feeder, Hummingbot và model runtime phải được triển khai riêng.
- Không có release signing identity hoặc phát hành Play Store trong phạm vi hiện tại.
