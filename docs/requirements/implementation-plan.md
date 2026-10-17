Exported from https://claude.ai/code/artifact/8c780454-ef4a-492d-a3f5-7cb73ff9e8b8 on 2026-10-17. Re-export when the doc changes. Architecture and schedule diagrams are not exported. CR-02 (Approved) overrides the 15-minute hold below: the hold is 10 minutes.

# Kế hoạch triển khai SPMS

Oct 17, 2026 · @Linh

## 1. Mục tiêu và giả định

Xây SPMS bản demo trong 6 tuần (19/10 đến 29/11/2026), chia 3 sprint, mỗi sprint 2 tuần. Demo cuối kỳ ngày 30/11 chạy được cả 3 use case UC-01, UC-02, UC-03. Đầu vào là SRS v1.0 và file `SPMS_requirements.xlsx`.

- **Phạm vi:** 16 yêu cầu (14 nút lá SP-x.x cùng IF-01, IF-02) và NFR-01 đến NFR-05. NFR-06 chỉ đánh giá bằng phân tích.
- **Ngoài phạm vi:** camera, barrier, cảm biến thật. Tất cả được thay bằng mock. Cổng thanh toán dùng môi trường sandbox hoặc mock.
- **Giả định:** nhóm 4 người, mỗi người khoảng 8 giờ/tuần, tức khoảng 64 giờ/sprint cho cả nhóm.

## 2. Kiến trúc và công nghệ

Một backend REST, một web app dùng chung cho 3 vai trò, còn các thiết bị ngoài đều là script mock gọi vào API. Khi có thiết bị thật, chỉ cần thay script mock, backend giữ nguyên.

&#91;embedded content: kiến trúc · 3 mock, 1 backend, 1 web app\]

| Thành phần | Công nghệ | Ghi chú |
| --- | --- | --- |
| Frontend | React + Vite + shadcn/ui | Dùng lại layout của prototype `spms_ui.html` |
| Backend | Python FastAPI | REST API, tự sinh Swagger để test IF-01 |
| Database | SQLite (demo), có thể chuyển PostgreSQL | Bảng `slots`, `sessions`, `reservations`, `prices`, `audit_log`, `users` |
| Realtime | WebSocket của FastAPI | Đẩy trạng thái slot cho SP-2.1 (≤ 5 giây) |
| Mock LPR / Sensor | Script Python gọi `POST /api/lpr-events`, `POST /api/sensor-events` | Đóng vai ACT-04, ACT-05 |
| Mock Payment | Endpoint giả trả success/fail | Đóng vai ACT-06; thử được TC-09 |
| Quản lý | GitHub (repo, Issues, Projects) | Mỗi issue gắn ID yêu cầu, ví dụ `[SP-3.1]` |

## 3. Backlog

Mỗi nút lá trong cây yêu cầu là một task. Sprint 1 làm các yêu cầu Must của luồng ra/vào, Sprint 2 làm thanh toán và đặt chỗ, Sprint 3 làm phần Could, NFR và kiểm thử. Mỗi sprint tối đa 64 giờ; task phụ thuộc luôn nằm cùng hoặc sau sprint của task nó cần.

| ID | Task | Priority | Ước lượng (giờ) | Phụ thuộc | Sprint |
| --- | --- | --- | --- | --- | --- |
| T-00 | Dựng repo, CI, khung FastAPI + React | – | 8 | – | 1 |
| T-01 | Thiết kế DB và seed 200 slot | – | 6 | T-00 | 1 |
| IF-01 | API `POST /api/lpr-events` + script mock LPR | Must | 6 | T-01 | 1 |
| SP-1.1 | Tạo phiên đỗ khi xe vào | Must | 6 | IF-01 | 1 |
| SP-1.2 | Mở barrier (mock) | Must | 4 | SP-1.1 | 1 |
| SP-1.3 | Đóng phiên khi xe ra | Must | 4 | SP-1.1 | 1 |
| SP-2.1 | Màn hình chỗ trống + WebSocket + mock sensor | Must | 10 | T-01 | 1 |
| SP-4.3 | Đăng nhập và phân quyền 3 vai trò | Must | 10 | T-00 | 1 |
| SP-4.4 | Audit log | Must | 4 | SP-1.2 | 1 |
| IF-02 | Nhập tay biển số khi confidence thấp | Must | 6 | IF-01, SP-4.4 | 1 |
| SP-4.1 | Cấu hình bảng giá | Must | 6 | SP-4.3 | 2 |
| SP-3.1 | Tính phí | Must | 6 | SP-1.3, SP-4.1 | 2 |
| SP-3.2 | Thanh toán QR (mock payment) | Should | 10 | SP-3.1 | 2 |
| SP-4.2 | Báo cáo doanh thu ngày | Should | 8 | SP-3.1 | 2 |
| SP-2.2.1 | Giữ chỗ 15 phút | Should | 8 | SP-2.1 | 2 |
| SP-2.2.2 | Job tự hủy đặt chỗ quá hạn | Should | 4 | SP-2.2.1 | 2 |
| T-02 | Test hiệu năng TC-17 (NFR-01) | Must | 6 | SP-1.2 | 2 |
| T-03 | Tích hợp và demo nội bộ cuối sprint | – | 8 | – | 2 |
| SP-2.3 | Gợi ý slot gần lối vào | Could | 4 | SP-2.1 | 3 |
| SP-3.3 | Hóa đơn email | Could | 6 | SP-3.2 | 3 |
| T-04 | Mã hóa dữ liệu, bật HTTPS (NFR-04) | Must | 8 | T-01 | 3 |
| T-05 | Test khả dụng với 3 tài xế (NFR-05) | Should | 4 | SP-2.2.1 | 3 |
| T-06 | Chạy toàn bộ TC-01 đến TC-18, cập nhật Excel | – | 12 | tất cả | 3 |
| T-07 | Dự phòng sửa lỗi | – | 16 | – | 3 |
| T-08 | Chuẩn bị demo và báo cáo | – | 10 | T-06 | 3 |

Tổng theo sprint: Sprint 1 là 64 giờ, Sprint 2 là 56 giờ, Sprint 3 là 60 giờ.

## 4. Lộ trình

&#91;embedded content: lộ trình · 3 sprint, 3 mốc\]

Mỗi sprint mở đầu bằng buổi lập kế hoạch (duyệt CR nếu có) và kết thúc bằng review. Demo nội bộ cuối Sprint 2 phải chạy được trọn UC-01 và UC-03; nếu chưa được, Sprint 3 cắt SP-2.3 và SP-3.3 trước.

## 5. Phân công vai trò

Mỗi người giữ một vai trò chính và một nhóm task. Điền tên thành viên vào cột cuối.

| Vai trò | Phụ trách | Task chính | Thành viên |
| --- | --- | --- | --- |
| PM / Requirements Engineer | Backlog, change request, cập nhật SRS và Excel | T-03, T-08, CR |  |
| Backend Developer | API, DB, job tự hủy, mock thiết bị | T-01, IF-01, SP-1.x, SP-3.1, SP-2.2.2 |  |
| Frontend Developer | 3 màn hình Tài xế / Cổng / Quản trị | SP-2.1, SP-2.2.1, IF-02, SP-4.1, SP-4.2 |  |
| QA / DevOps | CI, bảo mật, test case, NFR | T-00, SP-4.3, T-02, T-04, T-05, T-06 |  |

## 6. Definition of Done, kiểm thử và quản lý thay đổi

Một task chỉ được đóng khi đạt đủ các điều kiện sau:

- [ ] Code đã merge vào `main` qua pull request có 1 người review.
- [ ] Test case truy vết của task đã chạy và đạt đúng tiêu chí chấp nhận trong SRS.
- [ ] Cột `status`, `actual_result`, `executed_by`, `executed_date` của sheet `test_cases` đã được điền.
- [ ] Issue GitHub đã gắn đúng ID yêu cầu.

**Kiểm thử:** unit test cho logic có nhánh (tính phí, hết hạn đặt chỗ, phân quyền); test tích hợp cho IF-01, IF-02 bằng script mock. Cuối mỗi sprint chạy lại toàn bộ test case của các sprint trước.

**Quản lý thay đổi:** SRS v1.0 là baseline. Mọi thay đổi ghi vào sheet `change_requests`, PM đánh giá ảnh hưởng và cả nhóm duyệt ở buổi họp đầu sprint. CR-02 (giữ chỗ 10 phút) đã duyệt, làm cùng SP-2.2.1 ở Sprint 2. CR-01 (vé tháng) chưa duyệt, không nằm trong kế hoạch.

## 7. Rủi ro dự án

| Rủi ro | Ảnh hưởng | Cách xử lý |
| --- | --- | --- |
| Sprint 1 đầy 64/64 giờ, dễ trễ | Chậm cả Sprint 2 vì SP-3.1 cần SP-1.3 | Làm T-00, T-01, IF-01, SP-1.x trước; SP-4.3 trễ thì đẩy sang đầu Sprint 2 |
| WebSocket khó hơn dự kiến | SP-2.1 không đạt 5 giây | Dự phòng: polling mỗi 3 giây vẫn đạt tiêu chí |
| Sandbox thanh toán không đăng ký được | Không demo được SP-3.2 với QR thật | Dùng mock payment, vẫn chạy được TC-09 |
| Không có bộ 500 ảnh biển số | Không chạy được TC-18 (NFR-02) | Ghi TC-18 là Not Run, lý do "phụ thuộc nhà cung cấp camera" |
| Thành viên bận thi giữa kỳ | Mất 25% năng lực một sprint | T-07 có 16 giờ dự phòng; cắt SP-3.3, SP-2.3 (Could) trước |
