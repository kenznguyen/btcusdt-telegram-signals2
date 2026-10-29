# BTCUSDT Chart Pro và hệ thống phân tích futures

**GitHub lưu mã nguồn, nhánh và PR. Codemagic chạy toàn bộ kiểm thử, build APK và các tác vụ thủ công.** Cấu hình thực thi nằm ở [codemagic.yaml](codemagic.yaml); YAML GitHub Actions cũ đã chuyển sang [ci/archive/github-actions](ci/archive/github-actions/README.md) để lưu lịch sử.

## Thành phần

- [Android BTCUSDT Chart Pro](android-app/README.md): biểu đồ M15/H1, chỉ báo, scanner và thông báo; vị thế được mô phỏng.
- [Kho dữ liệu chuẩn](market_data/README.md): CCXT, SQLite và API chỉ đọc cho nến BTCUSDT perpetual.
- [Hummingbot bridge](integrations/README.md): snapshot sổ lệnh; credentials Hummingbot nằm ở server.
- [Kiến trúc 5 tầng](docs/FIVE_LAYER_ARCHITECTURE.md): phân chia dữ liệu, trinh sát, FreqAI, thực thi và giao diện. Đây là thiết kế đích; chưa triển khai toàn bộ.
- `app.py`: webhook Telegram và dashboard backend trên Render; gửi yêu cầu tới Codemagic.
- `bot.py`, `telegram_commands.py`, `backtest.py`: logic tín hiệu, báo cáo và backtest hiện có, dữ liệu OKX. Không đặt lệnh sàn.
- `dashboard/index.html`: xem báo cáo backtest, đồng bộ artifact Codemagic hoặc nạp JSON/CSV thủ công.

## Chạy trên Codemagic

Xem [hướng dẫn cấu hình Codemagic](docs/CODEMAGIC_SETUP.md) để chọn nhánh, cấu hình webhook/nhóm biến bảo mật và tải artifact.

| Workflow ID | Công việc | Kích hoạt |
| --- | --- | --- |
| `canonical-market-data` | Cài CCXT/Flask, chạy kiểm thử Python và kiểm tra CLI | Push đúng nhánh/đường dẫn hoặc thủ công |
| `android-chart-pro-debug` | Unit test Android và APK debug | Push đúng nhánh/đường dẫn hoặc thủ công |
| `android-chart-pro-release` | Unit test, APK release và kiểm tra chứng chỉ ký | Chỉ thủ công |
| `telegram-command` | Xử lý lệnh Telegram và backtest | API Codemagic hoặc thủ công |
| `dashboard-backtest` | Backtest theo tham số từ dashboard | API Codemagic hoặc thủ công |
| `signal-scan` | Một lượt quét mô phỏng với state cung cấp rõ ràng | Chỉ thủ công; không có lịch tự động |

Không cần GitHub Actions quota hoặc GitHub token có quyền Actions. GitHub webhook dùng để Codemagic nhận thay đổi mã nguồn; việc thêm YAML không tự cấu hình tài khoản, secrets hoặc chứng minh build đã chạy.

## Webhook Telegram / Render

Cài `requirements-web.txt`, chạy:

```bash
gunicorn --workers 1 --threads 4 --timeout 30 app:app
```

Health check: `/health`. Đăng ký đúng một webhook Telegram tại `/webhook` hoặc `/telegram-webhook`; giữ header xác thực `X-Telegram-Bot-Api-Secret-Token`.

Các biến cấu hình: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_WEBHOOK_SECRET`, `CODEMAGIC_API_TOKEN`, `CODEMAGIC_APP_ID`, `CODEMAGIC_BRANCH`. Token Codemagic chỉ nằm ở server/nhóm biến bảo mật; không đưa vào trình duyệt hoặc APK.

Các lệnh: `/help`, `/status`, `/position`, `/signal`, `/backtest`, `/btstatus`, `/btresult`. Lệnh được dispatch sang `telegram-command` trên nhánh có cấu hình mới. Cần deploy phiên bản bridge này cùng biến môi trường mới khi chuyển runner.

## Dữ liệu và trạng thái

- Python bot/backtest dùng OKX; APK và kho chuẩn mới dùng Binance Futures. Chưa chứng nhận ngang bằng dữ liệu/chiến lược.
- CI là runner tạm thời, không phải kho trạng thái vị thế. Không dùng cache để tuyên bố state mô phỏng là hiện hành.
- Scanner thủ công cần `LEGACY_STATE_JSON` từ state đã xác minh; tải `state.json` và `state-provenance.json` sau lượt chạy. Chưa có điều phối state dùng chung; không chạy scanner chồng lấn hoặc coi đây là dịch vụ giám sát bền vững.
- `/status` và `/position` yêu cầu state được cung cấp; thiếu/hỏng state báo không khả dụng, không tự tạo vị thế FLAT.
- Lịch sử/artifact Codemagic qua adapter có kiểm tra schema, giới hạn kích thước và lỗi rõ ràng. Hợp đồng lịch sử REST được giữ từ tài liệu chính thức cũ, cần kiểm chứng với tài khoản thực tế; giao diện vẫn hỗ trợ tải artifact và nạp thủ công.
- PnL, vị thế và giá khớp trong backtest là mô phỏng. Phạm vi hiện tại không bật live execution.

## Kiểm thử local

```bash
python3 -m unittest market_data.test_store market_data.test_sync market_data.test_api -v
python3 -m unittest discover -s integrations -p 'test_*.py' -v
python3 -m unittest discover -s ci -p 'test_*.py' -v
```

Kiểm thử cấu hình CI cần `requirements-ci.txt`. Build Android cần JDK 17, Gradle 8.9 và Android SDK 35; Codemagic chuẩn bị các công cụ này theo cấu hình đã lưu.


