# BTCUSDT Quant System — Hệ thống 5 tầng

**GitHub là nơi lưu trữ mã nguồn, nhánh, lịch sử và bằng chứng; GitHub Actions là cơ chế thực thi CI/workflow chuẩn của dự án.** Codemagic chỉ còn các workflow build/kiểm tra được giữ lại; không phải runner chính của Hệ thống 5 tầng. Ba tác vụ Python Telegram/scanner/backtest cũ đã được gỡ khỏi repository chung.

Phạm vi kiến trúc và các ranh giới loại trừ được ghi tại [Five-Layer Architecture](docs/FIVE_LAYER_ARCHITECTURE.md) và [T0 Active Scope Index](docs/T0_ACTIVE_SCOPE_INDEX.md). Quyết định loại Android Chart/Scanner và Python bot/backtest khỏi phạm vi được ghi tại [Five-Layer Scope Exclusion Decision](docs/evidence/FIVE_LAYER_SCOPE_EXCLUSION_ANDROID_PYTHON_2026-11-10.md).

## Thành phần thuộc Hệ thống 5 tầng

- [Kho dữ liệu chuẩn T0](market_data/README.md): CCXT, SQLite và API chỉ đọc cho nến BTCUSDT perpetual.
- [Hummingbot integration](integrations/README.md): adapter/snapshot sổ lệnh; credentials nằm ở server. Phạm vi và mức độ tích hợp cần căn cứ bằng chứng hiện hành.
- [Kiến trúc 5 tầng](docs/FIVE_LAYER_ARCHITECTURE.md): dữ liệu, trinh sát, chiến lược/AI, paper execution và React control plane. Đây là thiết kế đích; chưa mặc nhiên có nghĩa mọi tầng đã triển khai hoặc được kiểm định.
- [Luồng paper 5 tầng](docs/FIVE_LAYER_PAPER_RUNBOOK.md): luồng nghiên cứu/paper; fixture tests không chứng minh runtime, model hoặc frontend đã vận hành thực tế.

## Hệ thống riêng ngoài phạm vi 5 tầng — KHÔNG THUỘC SCOPE

Android Chart/Scanner vẫn là hệ thống riêng ngoài phạm vi T0–T4. Mã Python cũ `bot.py`, `backtest.py`, `telegram_commands.py`, Telegram bridge, scanner/backtest workflows và dependency chỉ phục vụ chúng đã được loại khỏi repository chung theo manifest retirement. Không xóa Android Paper client, T0–T4 hoặc các script nghiên cứu độc lập không nằm trong manifest.

## CI và workflow

GitHub Actions là runner chuẩn cho kiểm thử và workflow được quản lý trong repository. Chỉ xác nhận PASS khi có workflow run gắn với đúng source SHA và bằng chứng tương ứng. Xem các workflow hiện hành trong [`.github/workflows`](.github/workflows) và tài liệu evidence/handoff.

Codemagic còn giữ các workflow build/kiểm tra khác được liệt kê trong [codemagic.yaml](codemagic.yaml). Các workflow Telegram command, signal scan và dashboard backtest đã được gỡ; xem [manifest](docs/evidence/LEGACY_PYTHON_WORKFLOW_RETIREMENT_MANIFEST_2026-11-10.md). Codemagic không thay thế GitHub Actions làm runner chuẩn của Hệ thống 5 tầng.

Bảng dưới đây là inventory workflow của toàn repository, **không phải** danh sách workflow thuộc Hệ thống 5 tầng. Chỉ workflow có phạm vi T0–T4 đã được xác định mới được tính vào CI/acceptance của Hệ thống 5 tầng; các workflow Android, Telegram, backtest và scanner là legacy/out-of-scope.

| Workflow ID | Công việc | Kích hoạt | Phạm vi 5 tầng |
| --- | --- | --- | --- |
| `canonical-market-data` | Cài CCXT/Flask, chạy kiểm thử Python và kiểm tra CLI | Push đúng nhánh/đường dẫn hoặc thủ công | Cần đối chiếu job/path cụ thể; không tự suy rộng thành acceptance toàn T0–T4 |
| `android-chart-pro-debug` | Unit test Android và APK debug | Push đúng nhánh/đường dẫn hoặc thủ công | OUT OF SCOPE |
| `android-chart-pro-release` | Unit test, APK release và kiểm tra chứng chỉ ký | Chỉ thủ công | OUT OF SCOPE |

## Dữ liệu và trạng thái

- T0 là nguồn dữ liệu chuẩn của Hệ thống 5 tầng; không thay thế bằng state/cache của các hệ thống cũ.
- `dashboard/index.html` được giữ như trình xem báo cáo thủ công: chỉ nạp JSON/CSV đã có, không dispatch workflow hoặc gọi API ngoài.
- `backtest_rsi_percent_b_h1_adx.py` là script nghiên cứu riêng còn được giữ nguyên; không phải thành phần T0–T4. `requirements.txt` vẫn được giữ vì script này dùng các thư viện của nó.
- Hệ thống 5 tầng vẫn paper-only; không bật live execution hoặc gửi lệnh thật.

## Kiểm thử local

```bash
python3 -m unittest market_data.test_store market_data.test_sync market_data.test_api -v
python3 -m unittest discover -s integrations -p 'test_*.py' -v
python3 -m unittest discover -s ci -p 'test_*.py' -v
```

Kiểm thử cấu hình CI cần `requirements-ci.txt`. Build Android cần JDK 17, Gradle 8.9 và Android SDK 35; Codemagic chuẩn bị các công cụ này theo cấu hình đã lưu.


