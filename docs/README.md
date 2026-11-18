# Documentation Index — BTCUSDT Quant System

> Mục tiêu: điều hướng tài liệu hiện có theo vai trò. Đây là **chỉ mục**, không thay thế tài liệu gốc, quyết định đã phê duyệt, session handoff hoặc bằng chứng workflow.

## 1. Bắt đầu tại đây

1. [Project Session Handoff](PROJECT_SESSION_HANDOFF.md) — trạng thái phiên làm việc, branch/SHA, quyết định đang có hiệu lực, giới hạn và bước tiếp theo. **Đọc trước khi tiếp tục công việc.**
2. [Five-Layer Architecture](architecture/FIVE_LAYER_ARCHITECTURE.md) — kiến trúc và ranh giới T0–T4.
3. [T0 Active Scope Index](T0_ACTIVE_SCOPE_INDEX.md) — phạm vi T0 đang hoạt động và tài liệu liên quan.
4. [Five-Layer Paper Runbook](FIVE_LAYER_PAPER_RUNBOOK.md) — luồng kiểm tra/paper; không phải giấy phép live trading.
5. [Complete Roadmap](COMPLETE_ROADMAP.md) — roadmap tổng thể; đối chiếu handoff để biết mục nào còn hiệu lực.
6. [Repository Maintenance](REPOSITORY_MAINTENANCE.md) — quy tắc bảo trì repository.
7. [Repository Structure & Dependency Audit](evidence/REPOSITORY_STRUCTURE_DEPENDENCY_AUDIT_2026-11-18.md) — kết quả audit cấu trúc và truy vết entrypoint gần nhất.

## 2. Architecture và contracts

### Core / Paper execution
- [Core First Architecture Decision](architecture/CORE_FIRST_ARCHITECTURE_DECISION_2026-11-12.md)
- [Core First Readiness Plan](architecture/CORE_FIRST_READINESS_PLAN_2026-11-12.md)
- [Dual Ledger Contract](architecture/DUAL_LEDGER_CONTRACT.md)
- [Dataset Consumer Contract](architecture/DATASET_CONSUMER_CONTRACT.md)
- [Shared Data Foundation](architecture/SHARED_DATA_FOUNDATION.md)

### T0 — canonical data foundation
- [T0 Read-only Candle Contract v1](architecture/T0_READ_ONLY_CANDLE_CONTRACT_V1_2026-11-08.md)
- [T0 Candle API HTTPS Front Door Design](architecture/T0_CANDLE_API_HTTPS_FRONT_DOOR_DESIGN_2026-11-08.md)
- [T0 API Domain Selection Criteria](architecture/T0_API_DOMAIN_SELECTION_CRITERIA_2026-11-08.md)
- [Central Data Lifecycle Policy](architecture/CENTRAL_DATA_LIFECYCLE_POLICY.md)
- [Data Copy / Backup / Replica Lifecycle Contract](architecture/DATA_COPY_BACKUP_REPLICA_LIFECYCLE_CONTRACT.md)
- [Data Deletion Safety Contract](architecture/DATA_DELETION_SAFETY_CONTRACT.md)

### T0 → T1 → T2 data flow
- [T0/T1/T2 Data Consumption Architecture](architecture/T0_T1_T2_DATA_CONSUMPTION_ARCHITECTURE_2026-11-08.md)
- [T0/T1/T2 Synchronization Gap Assessment](architecture/T0_T1_T2_SYNCHRONIZATION_GAP_ASSESSMENT_2026-11-08.md)
- [T2 HTTP Candle Consumer Contract & Test Plan](architecture/T2_HTTP_CANDLE_CONSUMER_CONTRACT_AND_TEST_PLAN_2026-11-08.md)
- [T1 UTC Equity Reconstruction Event Journal](architecture/T1_UTC_EQUITY_RECONSTRUCTION_EVENT_JOURNAL_V1_2026-11-06.md)

### T4 — API gateway / control plane
- [T4 API Gateway Architecture Decision](architecture/T4_API_GATEWAY_ARCHITECTURE_DECISION_2026-11-08.md)

### AI / Dual Strategy — reference contracts, not activation approval
- [AI Strategy Contract](architecture/AI_STRATEGY_CONTRACT.md)
- [AI Strategy API Contract Proposal](architecture/AI_STRATEGY_API_CONTRACT_PROPOSAL.md)
- [AI Strategy Research Evaluation Contract](architecture/AI_STRATEGY_RESEARCH_EVALUATION_CONTRACT.md)
- [AI Calibration Artifact Contract](architecture/AI_CALIBRATION_ARTIFACT_CONTRACT.md)

Các tài liệu AI/dual-strategy là hợp đồng, đề xuất hoặc kế hoạch nghiên cứu. Chúng không tự cho phép triển khai, bật AI paper execution hay live execution. Core First closeout và approval gates vẫn được ưu tiên.

## 3. Decisions — quyết định và phê duyệt

- [Active Decision Supersession](decisions/ACTIVE_DECISION_SUPERSESSION_2026-11-13.md) — tra cứu quyết định nào thay thế quyết định cũ.
- [Personal-use Scope / Decommercialization](decisions/D-2026-11-09-T0-PERSONAL-USE-SCOPE-AND-DECOMMERCIALIZATION.md)
- [Operational-first Empirical Validation](decisions/D-2026-11-09-OPERATIONAL-FIRST-EMPIRICAL-VALIDATION.md)
- [L4 Provenance Personal Scope](decisions/D-2026-11-09-L4-PROVENANCE-PERSONAL-SCOPE.md)
- [L4 Evidence Custody — VPS/GitHub](decisions/D-2026-11-10-L4-EVIDENCE-CUSTODY-VPS-GITHUB-ONLY.md)
- [T0 Signature A2.2 Stage I Owner Approval](decisions/OWNER_APPROVAL_T0_SIGNATURE_A2_2_STAGE_I_2026-11-11.md)

Luôn kiểm tra trạng thái supersession và session handoff trước khi xem một tài liệu quyết định cũ là còn hiệu lực.

## 4. Plans và runbooks

Repository hiện **chưa có** thư mục docs/plans/ hoặc docs/runbooks/ riêng. Tài liệu kế hoạch/hướng dẫn đang nằm tại các vị trí sau; không suy diễn rằng các thư mục đó đã tồn tại.

- [Complete Roadmap](COMPLETE_ROADMAP.md)
- [Five-Layer Paper Runbook](FIVE_LAYER_PAPER_RUNBOOK.md)
- [Core First Readiness Plan](architecture/CORE_FIRST_READINESS_PLAN_2026-11-12.md)
- [T0 Staging Acceptance Checklist](T0_STAGING_ACCEPTANCE_CHECKLIST.md)
- [T0 PostgreSQL Lifecycle Acceptance Matrix](T0_POSTGRESQL_LIFECYCLE_ACCEPTANCE_MATRIX.md)
- [T0 Production Security / Backup / RPO / RTO](T0_PRODUCTION_SECURITY_BACKUP_RPO_RTO.md)
- [Codemagic Setup — legacy/fallback reference](CODEMAGIC_SETUP.md)

## 5. Evidence — bằng chứng và kết quả kiểm chứng

Thư mục [evidence/](evidence/) là kho bằng chứng lịch sử, có nhiều tài liệu theo milestone. Không coi tên file hoặc nội dung kế hoạch là PASS; phải kiểm tra source SHA, workflow run, artifact, verdict và giới hạn trong từng báo cáo.

### Core First / integration
- [Core First Independent Review](evidence/CORE_FIRST_INDEPENDENT_REVIEW_2026-11-18.md)
- [Core First Integration Candidate](evidence/CORE_FIRST_INTEGRATION_CANDIDATE_2026-11-18.md)
- [Core First Paper-only Packaging & Runtime Evidence](evidence/CORE_FIRST_PAPER_ONLY_PACKAGING_AND_RUNTIME_EVIDENCE_2026-11-12.md)
- [Core First Release Readiness & Dual Strategy Plan](evidence/CORE_FIRST_RELEASE_READINESS_AND_DUAL_STRATEGY_PLAN_2026-11-12.md)
- [Core First Partial-fill Crash Investigation](evidence/CORE_FIRST_PARTIAL_FILL_CRASH_INVESTIGATION_2026-11-18.md)

### T0 / T1 / T2
- [T0/T2 Repository Source Parity Review](evidence/T0_T2_REPOSITORY_SOURCE_PARITY_REVIEW_2026-11-10.md)
- [T0/T2 Deployment Parity Evidence Reconciliation](evidence/T0_T2_DEPLOYMENT_PARITY_EVIDENCE_RECONCILIATION_2026-11-10.md)
- [T0 Feeder Runtime Verification](evidence/T0_FEEDER_RUNTIME_VERIFICATION_20261109.md)
- [T1 Producer Call Path Trace](reviews/t1/T1_KLINE_PRODUCER_CALL_PATH_TRACE_2026-11-09.md)

### CI / repository / boundaries
- [CI Ownership & Test Denominator Decision](evidence/CI_OWNERSHIP_AND_TEST_DENOMINATOR_DECISION_2026-11-10.md)
- [Five-Layer Internal Dependency Mapping — Second Pass](evidence/FIVE_LAYER_INTERNAL_DEPENDENCY_MAPPING_SECOND_PASS_2026-11-10.md)
- [Android/Python Scope Exclusion Decision](evidence/FIVE_LAYER_SCOPE_EXCLUSION_ANDROID_PYTHON_2026-11-10.md)
- [Repository Structure & Dependency Audit](evidence/REPOSITORY_STRUCTURE_DEPENDENCY_AUDIT_2026-11-18.md)

### Evidence subcollections
- [P1.8 synthetic/security evidence](evidence/p1-8/)
- [T0 evidence](evidence/t0/)
- [T1 evidence](evidence/t1/)
- [T2 evidence](evidence/t2/)

## 6. Reviews và design

- [T1 contract and source reviews](reviews/t1/)
- [T1 source contract / ingestion adapter design](design/t1/)

Các review trong kho có thể là self-review, independent review request, pre-review hoặc kết quả review đã hoàn tất. Đọc nội dung và verdict; không suy luận mức độc lập chỉ từ thư mục.

## 7. Handoff, history và governance records

- [Current Project Session Handoff](PROJECT_SESSION_HANDOFF.md) — nguồn điều phối tiến độ hiện hành.
- [Historical Handoff Archive](archive/PROJECT_SESSION_HANDOFF_HISTORY_2026-11-10.md) — lịch sử, không thay thế handoff hiện tại.
- [Project Contribution Effort Ledger](PROJECT_CONTRIBUTION_EFFORT_LEDGER.md) — ghi nhận đóng góp/công việc.

## 8. Quy tắc đọc và cập nhật tài liệu

1. Bắt đầu từ PROJECT_SESSION_HANDOFF.md; xác nhận branch, HEAD SHA và trạng thái trước khi làm tiếp.
2. Phân biệt **decision**, **proposal**, **plan**, **review** và **evidence**. Proposal không phải approval; test fixture không chứng minh runtime.
3. Khi ghi nhận PASS, phải gắn đúng source SHA, workflow run và artifact nếu có. Nếu thiếu, ghi NOT VERIFIED hoặc BLOCKED.
4. Không di chuyển/xóa tài liệu lịch sử chỉ để làm gọn thư mục. Thêm liên kết điều hướng trước; bảo toàn provenance.
5. T0 là nền dữ liệu độc lập. Không thay đổi T0, runtime, VPS, credentials hoặc execution boundary qua một thay đổi chỉ mục tài liệu.
6. Hệ thống vẫn paper-only; không bật live execution hoặc gửi lệnh thật.
