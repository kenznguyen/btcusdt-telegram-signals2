# BTCUSDT Quant System — Hệ thống 5 tầng

**GitHub là nơi lưu trữ mã nguồn, nhánh, lịch sử và bằng chứng; GitHub Actions là cơ chế thực thi CI/workflow của dự án.** Không xem Codemagic là runner chính của Hệ thống 5 tầng. Các workflow Codemagic và ứng dụng cũ được giữ lại như tài sản riêng/lịch sử, không phải dependency của hệ thống 5 tầng.

Phạm vi kiến trúc và các ranh giới loại trừ được ghi tại [Five-Layer Architecture](docs/FIVE_LAYER_ARCHITECTURE.md) và [T0 Active Scope Index](docs/T0_ACTIVE_SCOPE_INDEX.md).

## Thành phần thuộc Hệ thống 5 tầng

- [Kho dữ liệu chuẩn T0](market_data/README.md): CCXT, SQLite và API chỉ đọc cho nến BTCUSDT perpetual.
- [Hummingbot integration](integrations/README.md): adapter/snapshot sổ lệnh; credentials nằm ở server. Phạm vi và mức độ tích hợp cần căn cứ bằng chứng hiện hành.
- [Kiến trúc 5 tầng](docs/FIVE_LAYER_ARCHITECTURE.md): dữ liệu, trinh sát, chiến lược/AI, paper execution và React control plane. Đây là thiết kế đích; chưa mặc nhiên có nghĩa mọi tầng đã triển khai hoặc được kiểm định.
- [Luồng paper 5 tầng](docs/FIVE_LAYER_PAPER_RUNBOOK.md): luồng nghiên cứu/paper; fixture tests không chứng minh runtime, model hoặc frontend đã vận hành thực tế.

## Hệ thống riêng ngoài phạm vi 5 tầng

Repository còn lưu Android Chart/Scanner, Python bot/backtest, Telegram và dashboard backtest cũ. Đây là các hệ thống độc lập; không phải T0–T4, consumer, dependency hoặc migration target của Hệ thống 5 tầng. Không suy diễn chúng phải dùng chung dữ liệu, API, chiến lược hoặc runtime.

## CI và workflow

GitHub Actions là runner chuẩn cho kiểm thử và workflow được quản lý trong repository. Chỉ xác nhận PASS khi có workflow run gắn với đúng source SHA và bằng chứng tương ứng. Xem các workflow hiện hành trong [`.github/workflows`](.github/workflows) và tài liệu evidence/handoff.

Codemagic là cấu hình/runner legacy phục vụ một số quy trình cũ, đặc biệt Android và tác vụ backtest. [codemagic.yaml](codemagic.yaml) và [hướng dẫn Codemagic](docs/CODEMAGIC_SETUP.md) được giữ để tham chiếu lịch sử; chúng không định nghĩa CI của Hệ thống 5 tầng.

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


