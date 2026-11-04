# BTCUSDT Quant System — kiến trúc 5 tầng

Repository này lưu source của hệ thống phân tích BTCUSDT và paper trading. Phạm vi hiện tại không bật giao dịch thật: `AI_EXECUTION_ENABLED=false`; không có luồng đặt lệnh Futures thật.

## Kiến trúc

| Tầng | Thành phần | Trách nhiệm |
|---|---|---|
| T0 — Data Foundation | `market_data/`, `app.py` | Nến BTCUSDT Futures, SQLite, đồng bộ CCXT, API đọc dữ liệu và health/readiness của Feeder |
| T1 — Futures Intelligence | `futures_intelligence/` | Import và kiểm tra funding, OI, taker flow, liquidation quan sát được; giữ provenance và coverage |
| T2 — Strategy / AI | `pipeline/`, `freqai_bridge/` | Strategy Core, AI signal research, xác minh dữ liệu/model và tạo decision/intent |
| T3 — Paper execution | `paper_execution/`, `integrations/` | Shared risk controls, paper ledger, mô phỏng trạng thái lệnh; Hummingbot bridge chỉ đọc order book |
| T4 — Control plane | `control_dashboard/`, `android-app/` | React dashboard và Android client dùng API chung |

Năm tầng là các ranh giới trách nhiệm logic; không đồng nghĩa tất cả runtime đã được triển khai hoặc chứng nhận production. Xem [kiến trúc 5 tầng](docs/FIVE_LAYER_ARCHITECTURE.md) và [paper runbook](docs/FIVE_LAYER_PAPER_RUNBOOK.md) để biết trạng thái, giới hạn và các bước cần xác minh.

## T0 Data Foundation

- Canonical market data hiện dùng Binance USDⓈ-M perpetual BTCUSDT và SQLite.
- CCXT sync/API dùng M15 và H1; dữ liệu thiếu được biểu diễn bằng coverage/gaps, không tự forward-fill.
- T0 Feeder health API trong `app.py` chỉ cung cấp `/health`, `/health/live`, `/health/ready`, `/health/data`.
- API nến đọc riêng nằm trong `market_data/api.py`; API paper/control chung nằm trong `pipeline/api.py`.
- Kraken Spot, OKX và Bybit shadow sources phải giữ cách ly theo adapter/acceptance riêng; không trộn vào canonical Binance Futures.

Chi tiết: [market_data/README.md](market_data/README.md).

## Paper-only boundary

- Tín hiệu Core và AI không trực tiếp đặt lệnh.
- Mọi intent phải qua Shared Risk Engine / Kill Switch và paper execution.
- Hummingbot bridge chỉ lấy snapshot order book; không gọi endpoint đặt/hủy lệnh.
- PnL, fill, vị thế và backtest là dữ liệu mô phỏng, không phải xác nhận giao dịch trên sàn.
- Không thêm exchange trading credentials vào CI hoặc Android app.

## CI và kiểm thử

- GitHub lưu source, branch và pull requests.
- GitHub Actions chạy các gate T0/P5 exact-SHA và Android foundation đã được allowlist.
- GitHub Actions là nền tảng CI/workflow duy nhất. Các workflow được allowlist trong `.github/workflows/`; cấu hình runner cũ đã được loại khỏi source.
- Mỗi acceptance phải được đối chiếu với đúng source SHA, workflow/job conclusion và artifact. Không suy diễn PASS từ cấu hình workflow.

Các lệnh kiểm thử chính:

```bash
python3 -m unittest market_data.test_store market_data.test_sync market_data.test_api market_data.test_gateway_runtime -v
python3 -m unittest market_data.test_feeder_health_api market_data.test_feeder_health_runtime_api -v
python3 -m unittest discover -s integrations -p 'test_*.py' -v
python3 -m unittest discover -s ci -p 'test_*.py' -v
python3 -m unittest futures_intelligence.test_import_collector pipeline.test_decision pipeline.test_api paper_execution.test_ledger paper_execution.test_risk_control freqai_bridge.test_exporter -v
```

React dashboard tests/build được mô tả trong [control_dashboard/README.md](control_dashboard/README.md). Android acceptance dùng workflow được allowlist trong `.github/workflows/`.

## Quy tắc thay đổi

1. Không thay đổi tham số chiến lược để làm đẹp kết quả backtest.
2. Không đánh dấu parity/OOS/production-ready nếu thiếu evidence tương ứng.
3. Test sau mỗi thay đổi; acceptance phải ghi đúng source SHA.
4. Không merge PR khi chưa có phê duyệt rõ ràng.
