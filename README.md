# BTCUSDT Chart Pro + Telegram Signal Bot

## Android Chart Pro

Ứng dụng Android nằm trong [`android-app/`](android-app/README.md), dùng dữ liệu công khai Binance USDⓈ-M Futures để hiển thị biểu đồ, quét nhiều mã và phát cảnh báo. Ứng dụng chỉ mô phỏng và thông báo; không đặt lệnh giao dịch.

- Biểu đồ và cảnh báo biểu đồ được tách theo mã giao dịch/khung thời gian.
- Scanner tự kết nối lại và tải bù nến khi mạng trở lại.
- Chiến lược vị thế và backtest hiện vẫn dành cho BTCUSDT; các thẻ này được ghi rõ trong giao diện.
- Xem [`android-app/README.md`](android-app/README.md) để build, chạy kiểm thử và hiểu giới hạn mô phỏng.

## Telegram Signal Bot

Bot Telegram theo dõi tín hiệu BTCUSDT Futures dựa trên nến M15 và bộ lọc xu hướng H1. Hệ thống sử dụng **một webhook Telegram chạy trên Render để nhận lệnh**, còn việc quét tín hiệu định kỳ được tách riêng sang **GitHub Actions workflow**.

> **Lưu ý rủi ro:** Đây là bot phát thông báo và mô phỏng vị thế. Bot không đặt, sửa hoặc đóng lệnh trên Binance Futures. Tín hiệu không phải lời khuyên đầu tư và cần được tự xác minh.

## 1. Kiến trúc hiện tại

```text
Người dùng Telegram
        |
        v
Một Telegram webhook
Render: app.py (/webhook)
        |
        | workflow_dispatch
        v
GitHub Actions: telegram-command.yml
        |
        v
telegram_commands.py
        |
        v
Kết quả trả về Telegram


GitHub Actions thủ công (lịch tự động đang tắt)
        |
        v
signal-scan.yml
        |
        v
bot.py -> lấy nến đã đóng từ OKX
        |
        v
Tín hiệu / thông báo -> Telegram
```

- **Render webhook:** chỉ nhận và xác thực lệnh Telegram, sau đó yêu cầu GitHub Actions xử lý.
- **Telegram Command workflow:** chạy khi Render dispatch workflow hoặc khi có thay đổi ở `.github/backtest-trigger.txt` trên nhánh `main`.
- **Signal Scanner workflow:** hiện chỉ chạy thủ công từ tab Actions; lịch tự động đã tắt.
- Hai workflow dùng chung Telegram Bot API để gửi tin nhắn; workflow quét tín hiệu **không cần một webhook Telegram thứ hai**.
- Không bật lại workflow polling dùng `getUpdates`/ `deleteWebhook` trong khi đang dùng webhook Render, vì polling có thể xóa webhook.

## 2. Các lệnh Telegram

| Lệnh | Chức năng |
|---|---|
| `/start` | Bắt đầu và xem hướng dẫn |
| `/help` | Danh sách lệnh |
| `/status` | Yêu cầu báo cáo trạng thái |
| `/position` | Yêu cầu thông tin vị thế mô phỏng |
| `/signal` | Kiểm tra tín hiệu hiện tại |
| `/backtest` | Chạy backtest |
| `/btstatus` | Kiểm tra trạng thái backtest |
| `/btresult` | Xem kết quả backtest |

Các lệnh được Render chuyển thành `workflow_dispatch`; GitHub Actions cần được bật trong repository. Lệnh backtest có thể mất thời gian vì cần tải và xử lý dữ liệu lịch sử.

## 3. Logic quét tín hiệu

- Mã thị trường: BTCUSDT; dữ liệu nến được lấy từ hợp đồng hoán đổi BTC-USDT trên OKX.
- Khung thời gian: M15 để tìm điểm vào và quản lý vị thế mô phỏng; H1 để lọc xu hướng.
- Chỉ xử lý nến đã đóng theo cờ xác nhận của nguồn dữ liệu.
- Các điều kiện và tham số được cấu hình bằng biến môi trường trong `bot.py`; ví dụ gồm RSI, ADX H1, ROE DCA, ADX DCA, TP và các ngưỡng SL.
- Khi không có nến M15 mới, scanner bỏ qua lượt chạy để tránh gửi lặp thông báo.
- Khi xử lý nến mới, bot có thể gửi thông báo ENTRY, DCA, TAKE PROFIT, SOFT SL, EMERGENCY SL và báo cáo trạng thái.
- Giá khớp, ROE, phí/trượt giá và vị thế trong tin nhắn là mô phỏng; kết quả thực tế trên sàn có thể khác.

Các tham số mặc định trong mã không thay thế cho việc kiểm thử chiến lược trên dữ liệu lịch sử. Hãy kiểm tra trực tiếp mã nguồn trước khi thay đổi thông số.

## 4. Các file chính

| Đường dẫn | Vai trò |
|---|---|
| `app.py` | Flask webhook bridge trên Render; xác thực webhook và dispatch workflow |
| `bot.py` | Quét nến, tính chỉ báo và gửi tín hiệu/vị thế mô phỏng |
| `telegram_commands.py` | Xử lý lệnh Telegram và các tác vụ backtest |
| `requirements-web.txt` | Thư viện cho dịch vụ webhook Render |
| `requirements.txt` | Thư viện Python của dự án |
| `.github/workflows/telegram-command.yml` | Workflow xử lý lệnh/backtest |
| `.github/workflows/signal-scan.yml` | Workflow quét tín hiệu theo lịch |
| `.github/backtest-trigger.txt` | File kích hoạt backtest khi được cập nhật trên nhánh `main` |

## 5. Cấu hình GitHub

### 5.1. Repository secrets

Vào **Repository → Settings → Secrets and variables → Actions**, tạo hoặc xác nhận:

- `TELEGRAM_BOT_TOKEN`: token bot từ BotFather.
- `TELEGRAM_CHAT_ID`: chat ID được phép sử dụng/nhận thông báo.

Không ghi các giá trị bí mật vào README, mã nguồn, commit hoặc ảnh chụp màn hình công khai.

### 5.2. Quyền kích hoạt workflow

Render cần biến `GITHUB_TOKEN` là GitHub Personal Access Token có quyền kích hoạt workflow trong repository. Với fine-grained token, chỉ cấp quyền cần thiết cho đúng repository; kiểm tra quyền **Actions: Read and write** và quyền bổ sung nếu cấu hình repository yêu cầu.

Các giá trị Render liên quan:
- `GITHUB_REPOSITORY=kenznguyen/btcusdt-telegram-signals2`
- `GITHUB_REF=main`
- `GITHUB_WORKFLOW_FILE=telegram-command.yml`

Workflow sử dụng GitHub Actions `GITHUB_TOKEN` riêng bên trong job; token đó không tự động thay thế token PAT mà Render dùng để dispatch workflow.

## 6. Triển khai webhook trên Render

Tạo hoặc mở Web Service kết nối với repository `kenznguyen/btcusdt-telegram-signals2`.

**Build Command**
```bash
pip install -r requirements-web.txt
```

**Start Command**
```bash
gunicorn --workers 1 --threads 4 --timeout 30 app:app
```

**Health Check Path**
```text
/health
```

Các biến môi trường cần có trên Render:

| Biến | Giá trị |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token bot Telegram |
| `TELEGRAM_CHAT_ID` | Chat ID được phép điều khiển/nhận tin |
| `TELEGRAM_WEBHOOK_SECRET` | Chuỗi bí mật riêng cho webhook |
| `GITHUB_TOKEN` | GitHub PAT có quyền dispatch workflow |
| `GITHUB_REPOSITORY` | `kenznguyen/btcusdt-telegram-signals2` |
| `GITHUB_REF` | `main` |
| `GITHUB_WORKFLOW_FILE` | `telegram-command.yml` |

Tạo `TELEGRAM_WEBHOOK_SECRET` ngẫu nhiên, không chia sẻ công khai; để tương thích với cách truyền header, chỉ dùng chữ cái, chữ số, dấu gạch dưới và dấu gạch ngang.

Sau khi deploy, mở `https://TEN-MIEN-RENDER/health`. Kết quả dự kiến là JSON cho biết dịch vụ hoạt động, ví dụ `{"ok":true}`.

## 7. Đăng ký một webhook Telegram

Chỉ đăng ký **một URL webhook cho bot Telegram này**. Mã hiện tại hỗ trợ `/webhook` và `/telegram-webhook`; chọn một URL và dùng nhất quán. Ví dụ:

```text
https://TEN-MIEN-RENDER/webhook
```

Đặt `secret_token` của Telegram trùng với `TELEGRAM_WEBHOOK_SECRET` trên Render. Có thể chạy lệnh sau trong terminal riêng; thay các giá trị bằng thông tin thật, không commit token:

```bash
export TELEGRAM_BOT_TOKEN='TOKEN_TU_BOTFATHER'
export TELEGRAM_WEBHOOK_SECRET='CHUOI_BI_MAT_WEBHOOK'
export WEBHOOK_URL='https://TEN-MIEN-RENDER/webhook'

curl -sS -X POST \
  "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -d "url=${WEBHOOK_URL}" \
  -d "secret_token=${TELEGRAM_WEBHOOK_SECRET}" \
  -d 'allowed_updates=["message"]'
```

Để kiểm tra cấu hình webhook, gọi `getWebhookInfo` bằng Telegram Bot API và xác nhận URL đúng, không rỗng, đồng thời kiểm tra `pending_update_count` và `last_error_message` nếu có. Không đăng công khai URL API chứa bot token.

Không chạy polling bằng `getUpdates` cùng lúc với webhook. Không cần webhook riêng cho workflow quét tín hiệu vì scanner gửi tin nhắn đi bằng Telegram Bot API.

## 8. Chạy và kiểm tra GitHub Actions

### Kiểm tra scanner

1. Mở [Actions](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions).
2. Chọn **BTCUSDT Signal Scanner**.
3. Chọn **Run workflow** để thử thủ công trên nhánh `main`.
4. Mở log và kiểm tra bước cài thư viện cùng bước chạy `python bot.py`.
5. Xác nhận tin nhắn Telegram nếu có sự kiện mới; không có nến mới thì bot có thể kết thúc mà không gửi tin.

Scanner hiện chỉ chạy thủ công qua workflow_dispatch. Không có lịch cron tự động trong workflow hiện tại.

### Kiểm tra lệnh

1. Gửi `/help` hoặc `/status` cho bot Telegram.
2. Mở Actions và chọn **Telegram Command**.
3. Kiểm tra lượt chạy tương ứng và log của `telegram_commands.py`.
4. Nếu lệnh không chạy, kiểm tra log Render, biến `GITHUB_TOKEN`, tên workflow, nhánh và quyền Actions.

## 9. Trạng thái và giới hạn cần biết

- GitHub Actions chạy trên máy ảo tạm thời. Scanner sử dụng GitHub Actions Cache cho `state.json`; cache là cơ chế khôi phục trạng thái tiện dụng, **không phải cơ sở dữ liệu bền vững hoặc giao dịch nguyên tử**. Nếu cần độ tin cậy cao, hãy chuyển trạng thái sang kho lưu trữ bền vững dùng chung.
- Workflow scanner và workflow lệnh là hai tiến trình riêng. Báo cáo `/status` hoặc `/position` có thể không phản ánh cùng trạng thái nếu các workflow không đọc/ghi cùng một nguồn trạng thái.
- Chống xử lý lặp webhook trong tiến trình Render có thể mất khi tiến trình khởi động lại.
- Lịch GitHub Actions có thể trễ; scanner không phù hợp làm hệ thống thực thi lệnh hoặc dừng lỗ khẩn cấp.
- Giá và sự kiện mô phỏng không đại diện cho lệnh đã khớp trên sàn.
- Hãy kiểm tra log và lịch sử Actions để xác nhận hệ thống chạy thực tế; việc cấu hình workflow không tự chứng minh rằng Telegram đã nhận tin thành công.

## 10. Bảo mật

- Không commit token, PAT hoặc secret.
- Chỉ chấp nhận chat ID đã cấu hình và các lệnh được cho phép.
- Webhook xác thực header `X-Telegram-Bot-Api-Secret-Token`.
- Khi token bị lộ, thu hồi hoặc thay mới ngay, rồi cập nhật biến môi trường.
- Không dùng dữ liệu Telegram làm lệnh shell tùy ý.
- Không thêm API key giao dịch Binance vào hệ thống nếu chưa có yêu cầu, kiểm thử và cơ chế quản trị rủi ro riêng.

---

**Repository:** [kenznguyen/btcusdt-telegram-signals2](https://github.com/kenznguyen/btcusdt-telegram-signals2)

**Mục tiêu:** Một webhook Telegram trên Render để nhận lệnh + GitHub Actions workflow riêng cho lệnh/backtest và workflow riêng cho quét tín hiệu định kỳ.


## 11. Dashboard hiệu suất backtest

Dashboard tĩnh ở `dashboard/index.html` dùng giao diện Dark Trading Terminal, chạy ngay trên trình duyệt và không cần cài thêm thư viện Python hay đưa secrets vào frontend.

### Cách sử dụng

1. Mở [GitHub Actions](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions), chọn lần chạy backtest mong muốn và tải artifact chứa các file backtest.
2. Mở `dashboard/index.html` trong trình duyệt (hoặc bật GitHub Pages với thư mục gốc `/dashboard` theo cách triển khai phù hợp).
3. Nhấn **Nạp dữ liệu backtest** và chọn các file cùng một lần chạy:
   - `backtest_last_result.json`: KPI, kết quả và danh sách trade nếu JSON có trường `trades`.
   - `backtest_trades.csv`: lịch sử trade chi tiết.
   - `backtest_equity_m15.csv`: equity và drawdown theo nến.
   - `backtest_status.json`: trạng thái backtest gần nhất trong artifact, nếu có.
4. Kiểm tra Run ID và thời gian tạo để tránh trộn file từ nhiều lần backtest khác nhau.

Dashboard không tự tải dữ liệu từ Actions và không khẳng định bot live đang chạy. Trạng thái chỉ hiển thị khi có status file được nạp. Nếu chưa có dữ liệu, KPI để trống thay vì dùng số minh họa. Intrabar drawdown là ước tính theo OHLC, không phải dữ liệu tick-level. Dashboard chỉ đọc và trình bày dữ liệu; không sửa logic Entry, DCA, TP hoặc SL.

