BTCUSDT Telegram Signal Bot

Bot Telegram dùng để tra cứu trạng thái, vị thế mô phỏng và tín hiệu BTCUSDT thông qua GitHub Actions.

1. Tổng quan hệ thống

Luồng hoạt động:

1. Người dùng gửi lệnh trong Telegram.
2. Render nhận lệnh qua webhook và kiểm tra mã bí mật cùng "TELEGRAM_CHAT_ID".
3. Render gọi GitHub Actions để xử lý lệnh.
4. GitHub Actions chạy "telegram_commands.py".
5. Bot gửi kết quả trở lại Telegram.

Lưu ý: Đây là hệ thống gửi tín hiệu và thông tin giao dịch mô phỏng. Bot không tự đặt, sửa hoặc đóng lệnh Binance Futures.

2. Các lệnh Telegram

Lệnh| Chức năng
"/start"| Hiển thị hướng dẫn
"/help"| Danh sách lệnh
"/status"| Xem trạng thái hệ thống
"/position"| Xem thông tin vị thế mô phỏng
"/signal"| Yêu cầu kiểm tra tín hiệu

Khi nhận lệnh, bot có thể gửi thông báo đang xử lý trước khi GitHub Actions trả kết quả.

3. Cấu trúc repository

Các thành phần chính:

- "app.py": Flask webhook bridge nhận lệnh Telegram và kích hoạt GitHub Actions.
- "bot.py": Logic xử lý tín hiệu và báo cáo giao dịch.
- "telegram_commands.py": Xử lý các lệnh Telegram.
- "requirements-web.txt": Các thư viện phục vụ webhook trên Render.
- "requirements.txt": Các thư viện cho chương trình Python.
- ".github/workflows/telegram-command.yml": Workflow xử lý lệnh Telegram.

Các workflow khác đang hoạt động trong repository, chẳng hạn workflow báo cáo tín hiệu định kỳ, cần được giữ nguyên nếu hệ thống vẫn sử dụng chúng.

4. Cấu hình GitHub

4.1. Tạo GitHub Personal Access Token

Trong GitHub, mở:

"Settings → Developer settings → Personal access tokens → Fine-grained tokens"

Tạo token với các thiết lập phù hợp:

- Resource owner: Tài khoản sở hữu repository.
- Repository access: Chỉ chọn repository "btcusdt-telegram-signals2".
- Repository permissions: Cấp quyền Actions cần thiết để kích hoạt workflow; quyền Contents chỉ cấp theo nhu cầu thực tế.

Lưu token để cấu hình vào Render dưới tên "GITHUB_TOKEN".

Không đưa token vào mã nguồn, README, file YAML hoặc tin nhắn Telegram.

4.2. Cấu hình GitHub Actions Secrets

Mở repository:

"Settings → Secrets and variables → Actions"

Tạo hoặc kiểm tra hai repository secrets:

- "TELEGRAM_BOT_TOKEN": Token bot lấy từ BotFather.
- "TELEGRAM_CHAT_ID": Chat ID được phép sử dụng bot và nhận kết quả.

Các giá trị phải khớp với cấu hình tương ứng trên Render.

5. Triển khai webhook trên Render

Tạo hoặc mở Web Service đã kết nối với repository:

"kenznguyen/btcusdt-telegram-signals2"

5.1. Build Command

pip install -r requirements-web.txt

5.2. Start Command

gunicorn --workers 1 --threads 4 --timeout 30 app:app

5.3. Health Check Path

/health

Sau khi triển khai, truy cập:

https://TEN-MIEN-RENDER/health

Kết quả mong đợi:

{"ok":true}

Thay "TEN-MIEN-RENDER" bằng tên miền Render thực tế của dịch vụ.

5.4. Environment Variables

Trong Render, mở:

"Service → Environment"

Thiết lập các biến sau:

Biến| Giá trị
"TELEGRAM_BOT_TOKEN"| Token từ BotFather
"TELEGRAM_CHAT_ID"| Chat ID được phép điều khiển bot
"TELEGRAM_WEBHOOK_SECRET"| Chuỗi bí mật riêng cho webhook
"GITHUB_TOKEN"| GitHub token có quyền kích hoạt workflow
"GITHUB_REPOSITORY"| "kenznguyen/btcusdt-telegram-signals2"
"GITHUB_REF"| "main"
"GITHUB_WORKFLOW_FILE"| "telegram-command.yml"

Dùng một chuỗi ngẫu nhiên đủ mạnh cho "TELEGRAM_WEBHOOK_SECRET". Theo cách triển khai hiện tại, chuỗi này chỉ nên gồm chữ cái, chữ số, dấu gạch dưới hoặc dấu gạch ngang.

Không chia sẻ các giá trị bí mật trong ảnh chụp màn hình hoặc nhật ký công khai.

6. Đăng ký Telegram webhook

Mã nguồn "app.py" hiện tại nhận webhook tại đường dẫn:

/telegram-webhook

Đăng ký URL đầy đủ có dạng:

https://TEN-MIEN-RENDER/telegram-webhook

Telegram webhook cần được thiết lập với "secret_token" trùng với giá trị "TELEGRAM_WEBHOOK_SECRET" trên Render.

Ví dụ chạy từ terminal riêng, không commit lệnh chứa token vào repository:

export TELEGRAM_BOT_TOKEN='TOKEN_TU_BOTFATHER'
export TELEGRAM_WEBHOOK_SECRET='CHUOI_BI_MAT_WEBHOOK'
export WEBHOOK_URL='https://TEN-MIEN-RENDER/telegram-webhook'

curl -sS -X POST \
  "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -d "url=${WEBHOOK_URL}" \
  -d "secret_token=${TELEGRAM_WEBHOOK_SECRET}" \
  -d 'allowed_updates=["message"]'

Phản hồi thành công từ Telegram API cần có:

{"ok":true,"result":true}

Nếu đã đăng ký webhook cho cùng bot trước đó, thao tác này sẽ thay đổi URL webhook hiện hành. Hãy kiểm tra URL đang dùng trước khi thực hiện.

7. Kiểm tra hệ thống

Sau khi Render triển khai thành công:

1. Mở URL "/health" và xác nhận dịch vụ hoạt động.
2. Gửi "/help" cho bot Telegram.
3. Gửi lần lượt "/status", "/position" và "/signal".
4. Mở repository GitHub.
5. Chọn tab Actions.
6. Kiểm tra workflow xử lý lệnh Telegram có chạy thành công hay không.

Nếu Telegram chỉ trả về thông báo đang xử lý mà không có kết quả:

- Kiểm tra nhật ký Render.
- Kiểm tra workflow trong GitHub Actions.
- Kiểm tra "GITHUB_TOKEN" và quyền Actions.
- Kiểm tra tên workflow, nhánh "main" và repository.
- Kiểm tra hai GitHub Actions secrets "TELEGRAM_BOT_TOKEN" và "TELEGRAM_CHAT_ID".
- Kiểm tra webhook URL và "TELEGRAM_WEBHOOK_SECRET".

8. Bảo mật

- Không commit token hoặc thông tin bí mật vào repository.
- Chỉ cho phép chat ID đã cấu hình sử dụng bot.
- Webhook kiểm tra header "X-Telegram-Bot-Api-Secret-Token".
- Chỉ xử lý các lệnh được cho phép.
- Không sử dụng đầu vào Telegram làm lệnh shell tùy ý.
- Nếu token bị lộ, hãy thu hồi hoặc tạo token mới ngay.
- Không coi tín hiệu mô phỏng là lệnh giao dịch đã được thực hiện trên sàn.

9. Giới hạn hiện tại

- Bot gửi tín hiệu và thông tin mô phỏng, không trực tiếp giao dịch Binance Futures.
- Cơ chế chống xử lý lặp webhook đang lưu trong bộ nhớ tiến trình; khi Render khởi động lại, trạng thái chống lặp có thể bị mất.
- "/status" và "/position" chỉ chính xác khi dữ liệu trạng thái mà workflow đọc được đã được cập nhật và đồng bộ đúng cách.
- Nếu các workflow chạy độc lập và dùng những bản "state.json" khác nhau, dữ liệu vị thế có thể không đồng nhất.
- Dịch vụ Render miễn phí có thể tạm ngừng khi không hoạt động, khiến phản hồi đầu tiên chậm hơn.

10. Mục tiêu phát triển tiếp theo

- Cải thiện lưu trữ trạng thái giao dịch dùng chung giữa các workflow.
- Bổ sung kiểm thử cho webhook và lệnh Telegram.
- Tăng khả năng chống xử lý lặp sau khi dịch vụ khởi động lại.
- Hoàn thiện giám sát lỗi và báo cáo trạng thái.
- Chỉ tích hợp giao dịch tự động sau khi có cơ chế quản trị rủi ro, xác thực và kiểm thử riêng.

---

Repository: "kenznguyen/btcusdt-telegram-signals2"

Mục đích: Telegram command bridge + GitHub Actions + BTCUSDT simulated signals.
