# Telegram commands -> GitHub Actions (BTCUSDT signal bot)

## Luồng hoạt động

1. Bạn gửi `/status`, `/position`, `/signal` hoặc `/help` trong Telegram.
2. Dịch vụ webhook kiểm tra secret header và chỉ chấp nhận đúng `TELEGRAM_CHAT_ID` đã cấu hình.
3. Dịch vụ gọi GitHub Actions `telegram-command.yml` bằng GitHub API.
4. Workflow chạy `telegram_commands.py` và gửi kết quả về Telegram.

Lệnh được whitelist; không gửi token, chat ID hoặc văn bản tùy ý vào workflow input. Bot chỉ phát tín hiệu mô phỏng, không đặt lệnh Futures.

## A. Đưa file vào repository

Sao chép các file sau vào root repository `kenznguyen/btcusdt-telegram-signals`:

- `bot.py` (bản bot tối ưu hiện tại)
- `telegram_commands.py`
- `requirements.txt`
- `.github/workflows/telegram-command.yml`

Không xóa workflow báo cáo định kỳ đang có (`signals.yml`). Nếu `bot.py` trên GitHub đã có sửa đổi mới hơn file gói này, hãy giữ bản mới nhất và chỉ tích hợp các phần cần thiết.

## B. Tạo GitHub token để dispatch workflow

Tạo Fine-grained personal access token trong GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens:

- Resource owner: tài khoản sở hữu repository.
- Repository access: chỉ chọn `btc...` repository này.
- Repository permissions: **Actions: Read and write**, **Contents: Read-only**.
- Không đặt token vào file Python, YAML, README, commit hoặc tin nhắn Telegram.

Lưu token này để nhập vào biến môi trường `GITHUB_TOKEN` của dịch vụ Render. Không dùng `GITHUB_TOKEN` mặc định của workflow làm token bridge, vì token đó không nằm sẵn trong dịch vụ webhook.

## C. Triển khai webhook bridge trên Render

1. Push các file trên lên GitHub.
2. Tạo Web Service trên Render, kết nối repository này. Có thể dùng `render.yaml` hoặc nhập thủ công:
   - Build command: `pip install -r requirements-web.txt`
   - Start command: `gunicorn --workers 1 --threads 4 --timeout 30 app:app`
   - Health check path: `/health`
3. Thêm Environment Variables (Render → service → Environment):
   - `TELEGRAM_BOT_TOKEN`: token từ BotFather.
   - `TELEGRAM_CHAT_ID`: chat ID cá nhân được phép điều khiển bot; phải khớp GitHub Actions secret.
   - `TELEGRAM_WEBHOOK_SECRET`: chuỗi ngẫu nhiên dài, chỉ dùng cho webhook; chỉ gồm chữ, số, `_` và `-`.
   - `GITHUB_TOKEN`: fine-grained token ở bước B.
   - `GITHUB_REPOSITORY`: `kenznguyen/btcusdt-telegram-signals`
   - `GITHUB_REF`: `main`
   - `GITHUB_WORKFLOW_FILE`: `telegram-command.yml`
4. Deploy và xác nhận `https://TEN-MIEN-RENDER/health` trả về `{"ok":true}`.

Lưu ý: gói Render miễn phí có thể sleep khi không hoạt động, nên lệnh đầu tiên sau thời gian nhàn rỗi có thể trễ. Dịch vụ luôn bật sẽ phù hợp hơn nếu cần phản hồi nhanh ổn định.

## D. Cấu hình GitHub Actions secrets

Trong GitHub repository → Settings → Secrets and variables → Actions → New repository secret, tạo/kiểm tra:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Hai giá trị phải trùng với cấu hình Render. Không đặt `GITHUB_TOKEN` của Render làm secret Telegram.

## E. Đăng ký Telegram webhook (chạy một lần)

Sau khi có URL Render và đã đặt các biến môi trường cục bộ trong terminal, chạy lệnh sau. Thay `WEBHOOK_URL` bằng URL dịch vụ Render của bạn; đừng gửi token cho người khác hoặc commit lệnh có token vào repository.

```bash
export TELEGRAM_BOT_TOKEN='TOKEN_TỪ_BOTFATHER'
export TELEGRAM_WEBHOOK_SECRET='CHUỖI_BÍ_MẬT_WEBHOOK'
export WEBHOOK_URL='https://TEN-MIEN-RENDER/telegram-webhook'

curl -sS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -d "url=${WEBHOOK_URL}" \
  -d "secret_token=${TELEGRAM_WEBHOOK_SECRET}" \
  -d 'allowed_updates=["message"]'
```

Phản hồi Telegram API cần có `"ok":true`. Nếu trước đây đã dùng webhook khác cho cùng bot, `setWebhook` sẽ thay webhook đó.

## F. Thử nghiệm

Gửi lần lượt:

- `/help`
- `/status`
- `/position`
- `/signal`

Bot sẽ gửi tin nhắn xác nhận rằng GitHub Actions đang xử lý, sau đó workflow gửi kết quả. Kiểm tra GitHub → Actions → `Telegram Command Response` nếu chưa nhận được kết quả.

## Bảo mật và giới hạn

- Chỉ đúng chat ID được phép gọi workflow.
- Webhook xác thực header `X-Telegram-Bot-Api-Secret-Token`.
- Chỉ bốn lệnh được cho phép; không cho phép Telegram truyền shell command hay tên workflow tùy ý.
- Không in token vào log.
- Deduplication hiện ở bộ nhớ tiến trình; sau khi dịch vụ restart, Telegram retry cũ có thể không được nhận diện. Workflow trả kết quả về chat ID đã cấu hình, không nhận chat ID từ người gửi.
- Lệnh `/status` đọc `state.json` có sẵn trong checkout của workflow. Nếu state của workflow báo cáo định kỳ không được lưu bền vững/khôi phục vào repository hoặc artifact, lệnh có thể không thấy vị thế mới nhất; cần dùng chung cơ chế lưu state bền vững để đồng bộ chính xác giữa các workflow.
