# SPMS traceability

Titles and priorities come from `SPMS_requirements.xlsx`, sheet `requirements`, rows 2–17 (columns A, B, E). Test mappings come from `test_case_analysis`, rows 2–30 (columns B–D); NFR targets come from `nfrs`, rows 2–7 (columns E–F). Module and page homes and NFR verification methods follow [the scaffold design](../superpowers/specs/2026-10-17-spms-codebase-scaffold-design.md).

Both [srs.md](srs.md) and [implementation-plan.md](implementation-plan.md) are local exports (2026-10-17); the Sprint column follows section 3 of the plan. The requirement tree diagram is not exported; the table below follows its leaf nodes. Re-export both documents whenever their sources change.

## Functional and interface requirements

Backend module names mean `backend/app/modules/<name>/`; frontend page names mean `frontend/src/pages/<name>/`. These are fixed homes to create as needed, not existing feature implementations. `Status` tracks implementation, independently of the workbook's approval status.

| ID | Title | Priority | Sprint | Backend module | Frontend page | Test cases | Status |
|---|---|---|---|---|---|---|---|
| SP-1.1 | Ghi nhận xe vào | Must | Sprint 1 | `sessions` | gate | TC-01 | Not started |
| SP-1.2 | Mở barrier tự động | Must | Sprint 1 | `sessions` | gate | TC-02 | Not started |
| SP-1.3 | Đóng phiên đỗ khi xe ra | Must | Sprint 1 | `sessions` | gate | TC-03 | Not started |
| SP-2.1 | Hiển thị chỗ trống | Must | Sprint 1 | `slots` | driver | TC-04 | Not started |
| SP-2.2.1 | Giữ chỗ trước | Should | Sprint 2 | `reservations` | driver | TC-05 | Not started |
| SP-2.2.2 | Tự hủy đặt chỗ quá hạn | Should | Sprint 2 | `reservations` | driver | TC-06 | Not started |
| SP-2.3 | Gợi ý slot gần lối vào | Could | Sprint 3 | `slots` | driver | TC-07 | Not started |
| SP-3.1 | Tính phí gửi xe | Must | Sprint 2 | `billing` | gate, admin | TC-08 | Not started |
| SP-3.2 | Thanh toán QR | Should | Sprint 2 | `billing` | gate, admin | TC-09 | Not started |
| SP-3.3 | Hóa đơn điện tử | Could | Sprint 3 | `billing` | gate, admin | TC-10 | Not started |
| SP-4.1 | Cấu hình bảng giá | Must | Sprint 2 | `billing` | gate, admin | TC-11 | Not started |
| SP-4.2 | Báo cáo doanh thu ngày | Should | Sprint 2 | `reports` | admin | TC-12 | Not started |
| SP-4.3 | Phân quyền theo vai trò | Must | Sprint 1 | `auth` | login; guards all pages | TC-13 | Not started |
| SP-4.4 | Audit log mở barrier thủ công | Must | Sprint 1 | `audit` | admin | TC-14 | Not started |
| IF-01 | Nhận sự kiện từ LPR Camera | Must | Sprint 1 | `sessions` | gate | TC-15 | Not started |
| IF-02 | Nhập tay khi LPR không chắc chắn | Must | Sprint 1 | `sessions` | gate | TC-16 | Not started |

## Nonfunctional requirements

| ID | Target | Verified by | Status |
|---|---|---|---|
| NFR-01 | Gate processing p95 <= 3 seconds | TC-17: timing script, outside `npm run check` | Not started |
| NFR-02 | LPR accuracy >= 95% on 500 labeled images | TC-18: depends on camera vendor | Not Run |
| NFR-03 | Monthly uptime >= 99.5% | Analysis | Not started |
| NFR-04 | 100% personal data encrypted: AES-256 at rest, TLS 1.2+ in transit | Inspection; T-04, Sprint 3: SQLAlchemy column type in `core/` plus HTTPS | Not started |
| NFR-05 | First-time driver completes reservation in <= 1 minute | Demonstration | Not started |
| NFR-06 | >= 1000 slots while meeting NFR-01 | Analysis | Not started |

NFR-04 encryption is deferred until T-04; do not add it to the scaffold. TC-17 and TC-18 are mapped to NFR-01 and NFR-02 respectively by `test_case_analysis` (rows 29–30); the functional table preserves that sheet's FR mappings.

## Change requests

Statuses come from `change_requests`, rows 2–3. Approved CR-02 overrides the workbook's older 15-minute reservation text (including TC-05's expected hold and TC-06's minute-16 steps).

| CR | Status | Effect on build |
|---|---|---|
| CR-02 | Approved | SP-2.2.1 and SP-2.2.2 use a 10-minute hold. TC-06 checks expiry at minute 11 (10/11 boundary, `test_case_analysis!F13`). Build CR-02 with SP-2.2.1 in Sprint 2, per scaffold design. |
| CR-01 | Under Review | Monthly passes: do not build. |
