# BTCUSDT Quant System — hệ thống 5 tầng

Repository này chứa hệ thống phân tích futures BTCUSDT độc lập, ưu tiên độ tin cậy dữ liệu và kiểm soát rủi ro. Android là Paper Client duy nhất của repository; React là giao diện điều khiển web.

**GitHub lưu source, branch, PR và evidence. Codemagic chạy các action kiểm thử/build theo `codemagic.yaml`.** Không coi cấu hình workflow là bằng chứng job hoặc artifact đã thành công.

## Kiến trúc

| Tầng | Thành phần | Trách nhiệm |
|---|---|---|
| T0 | [market_data](market_data/README.md) | Canonical market data, write gateway, Feeder, scheduler, recovery, lease/fencing, health/readiness |
| T1 | [futures_intelligence](futures_intelligence/README.md) | Funding, OI, trades/taker flow, liquidations, provenance và coverage |
| T2 | [freqai_bridge](freqai_bridge/README.md), [pipeline](pipeline/CONTRACTS.md) | Freqtrade/FreqAI research, Core + AI signals, provenance/freshness, decision contracts |
| T3 | [paper_execution](paper_execution/README.md), [integrations](integrations/README.md) | Shared Risk Engine, Kill Switch, Hummingbot snapshots, paper ledger và audit |
| T4 | [control_dashboard](control_dashboard/README.md), [pipeline API](pipeline/CONTRACTS.md) | React control dashboard và API chung |

Android Paper Client: [android-app](android-app/README.md). Ứng dụng chỉ kết nối API chung; không chứa chart/scanner/monitor của sản phẩm khác.

## Chế độ an toàn

- Paper-only; không thực hiện lệnh thật.
- Không bật live execution; `ai_execution_enabled=false`.
- Mọi tín hiệu phải qua shared risk controls và paper admission.
- Dữ liệu thiếu, cũ, không đồng bộ hoặc thiếu provenance không được thay bằng giá trị giả.
- Không tuyên bố lợi nhuận hoặc readiness nếu chưa có bằng chứng đúng source SHA.

## Codemagic workflows

| Workflow | Công việc |
|---|---|
| `five-layer-android` | Android boundary tests, unit tests, build và APK payload verification |
| `canonical-market-data` | T0/T1, API, gateway và paper backend tests |
| `five-layer-dashboard` | React tests, build và dependency audit |
| `freqai-strategy-smoke` | Load Freqtrade/FreqAI strategy ở dry-run; không train hoặc trade |
| `market-data-timescaledb` | Disposable TimescaleDB integration |
| `market-data-kraken-*` | Kiểm thử adapter Spot cô lập, không đưa vào canonical Futures |

Các workflow legacy Telegram/backtest trong repository không thuộc runtime T0–T4 và không được dùng làm nguồn trạng thái của hệ thống 5 tầng. Chúng chưa bị xóa trong đợt tách Android này.

## Tài liệu vận hành

- [Kiến trúc 5 tầng](docs/FIVE_LAYER_ARCHITECTURE.md)
- [Paper runbook](docs/FIVE_LAYER_PAPER_RUNBOOK.md)
- [Codemagic setup](docs/CODEMAGIC_SETUP.md)
- [Project handoff](docs/PROJECT_SESSION_HANDOFF.md)

Mỗi thay đổi phải ghi phạm vi, test/evidence, exact source SHA, workflow run/artifact nếu có, trạng thái PASS/BLOCKED/NOT VERIFIED và bước tiếp theo. Không merge PR khi chưa có phê duyệt rõ ràng.
