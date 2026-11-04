# GitHub Actions — CI và acceptance

GitHub lưu source, branch và pull request; GitHub Actions là runner CI/workflow duy nhất của repository. Codemagic đã được retire. Không cấu hình webhook, credential hoặc runner Codemagic cho repository này.

## Workflow đang hoạt động

| Workflow | Mục đích |
| --- | --- |
| `t0-validation.yml` | T0 market-data, Feeder, health, recovery, operational contract và data integrity |
| `t0-manual-validation.yml` | Các gate T0 được gọi thủ công: runtime config, component, Kraken Spot và TimescaleDB |
| `t0-health-api-boundary.yml` | PR regression cho T0 health API và app surface |
| `p5-4-1-post-merge-validation.yml` | Orchestrate exact-SHA T0, G1 và G2 acceptance |
| `p5-3-10-5-g1-green-validation.yml` | Gateway runtime GREEN contracts |
| `p5-3-11-g2-integration-green.yml` | G2 routing, Feeder lifecycle, pipeline và FreqAI consumer regression |
| `p5-3-10-4-g1-red-execution.yml`, `p5-3-11-5-g2-red-validation.yml`, `p5-3-11-g2-integration-red.yml` | Các workflow RED/reproduction theo trigger được định nghĩa trong từng file |
| `p5-4-10-backup-restore-fixture.yml` | Fixture-only backup/restore acceptance |
| `android-t0-foundation.yml`, `android-t0-foundation-github-actions.yml` | Android foundation checks |
| `t0-9-art-jni-runtime.yml` | ART/JNI runtime instrumentation thủ công |
| `android-release-pair.yml` | Release pair thủ công, yêu cầu source SHA và signing secrets được phê duyệt |
| `cross-layer-integration.yml` | Integrations, futures intelligence, paper system và FreqAI bridge tests |
| `control-dashboard.yml` | Node tests, React build và npm audit |
| `freqai-strategy-smoke.yml` | Kiểm tra load FreqAI strategy thủ công; không train hoặc trade |

Trigger, branch/path filters, permissions và thời hạn artifact được định nghĩa trong từng workflow. Không suy diễn PASS từ việc file YAML tồn tại.

## Quy trình nghiệm thu

1. Xác định branch và source SHA cần kiểm tra.
2. Chạy workflow được áp dụng cho phạm vi thay đổi; các acceptance gate phải checkout đúng PR head SHA hoặc commit được chọn.
3. Kiểm tra trạng thái workflow và từng job/step trên GitHub Actions.
4. Đối chiếu source SHA trong log/manifest/artifact với SHA dự kiến.
5. Chỉ ghi PASS khi workflow/job kết thúc thành công và bằng chứng exact-SHA khớp.

Không merge PR khi chưa có phê duyệt rõ ràng. Không chạy lại workflow trên SHA khác rồi dùng kết quả thay cho source cần nghiệm thu.

## Ranh giới an toàn

Các workflow kiểm thử dùng môi trường cô lập, không yêu cầu exchange trading credentials và đặt `AI_EXECUTION_ENABLED=false` ở các acceptance paper/T0 liên quan. Không có workflow nào được phép gửi lệnh Futures thật. Artifact kiểm thử không phải bằng chứng production, live exchange connectivity, profitability hoặc triển khai server.

## Dashboard React

Từ `control_dashboard/`, quy trình local tương ứng:

```bash
npm ci --ignore-scripts
npm test
npm run build
npm audit --audit-level=high
```

GitHub Actions workflow sử dụng Node 24 và npm 11.9.0, lưu source SHA và upload build artifact khi thành công.
