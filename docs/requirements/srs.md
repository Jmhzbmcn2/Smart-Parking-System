Exported from https://claude.ai/code/artifact/aa272cea-9945-440d-9b30-452de8ead248 on 2026-10-17. Re-export when the doc changes. The requirement-tree diagram is not exported; see the tree in traceability.md. CR-02 (Approved) overrides the 15-minute hold below: the hold is 10 minutes and TC-06 checks minute 11.

# SRS – Smart Parking Management System

Oct 16, 2026 · @Linh

## 1. Giới thiệu

### 1.1 Mục đích

Tài liệu đặc tả yêu cầu phần mềm (SRS) cho **Smart Parking Management System (SPMS)**, phiên bản 1.0. Đối tượng đọc: giảng viên, nhóm phát triển, nhóm kiểm thử và chủ bãi xe. Cấu trúc theo ISO/IEC/IEEE 29148:2018.

### 1.2 Phạm vi

SPMS quản lý một bãi xe ô tô nhiều tầng: nhận diện biển số khi xe ra/vào, theo dõi chỗ trống theo thời gian thực, đặt chỗ trước, tính phí và thanh toán online.

- **Trong phạm vi:** web app cho tài xế, màn hình cho nhân viên, trang quản trị, tích hợp camera, cảm biến và cổng thanh toán.
- **Ngoài phạm vi:** xe máy, trạm sạc xe điện, phần cứng camera/barrier (mua sẵn từ nhà cung cấp).

### 1.3 Định nghĩa và viết tắt

| Thuật ngữ | Ý nghĩa |
| --- | --- |
| LPR | License Plate Recognition – nhận diện biển số từ camera |
| Slot | Một chỗ đỗ xe, có mã dạng `T1-A-05` (Tầng 1, Khu A, chỗ 05) |
| Phiên đỗ | Khoảng thời gian từ lúc xe vào đến lúc xe ra |
| MoSCoW | Mức ưu tiên Must / Should / Could / Won't |
| FR / NFR | Functional / Non-functional Requirement |

### 1.4 Tài liệu tham chiếu

- ISO/IEC/IEEE 29148:2018 – Requirements engineering.
- Mẫu case study LMS-2026, môn CSE703095.

## 2. Mô tả tổng quan

### 2.1 Bối cảnh sản phẩm

Hiện bãi xe ghi vé giấy và đếm chỗ trống thủ công. Giờ cao điểm, tài xế phải chạy vòng tìm chỗ, cổng ra ùn tắc do thu tiền mặt. SPMS tự động hóa ra/vào và thanh toán, giảm thời gian chờ ở cổng.

### 2.2 Stakeholders

| ID | Vai trò | Influence | Interest | Quan tâm chính |
| --- | --- | --- | --- | --- |
| STK-01 | Chủ bãi xe | High | High | Doanh thu, báo cáo |
| STK-02 | Quản lý IT | High | Medium | Bảo mật, độ ổn định |
| STK-03 | Tài xế | Low | High | Tìm chỗ nhanh, trả tiền tiện |
| STK-04 | Nhân viên trực cổng | Medium | High | Xử lý sự cố nhanh |
| STK-05 | Cơ quan quản lý đô thị | Medium | Low | Tuân thủ quy định |

### 2.3 Actors

| ID | Actor | Loại | Mô tả |
| --- | --- | --- | --- |
| ACT-01 | Driver | Primary | Đặt chỗ, gửi xe, thanh toán |
| ACT-02 | Parking Attendant | Primary | Giám sát cổng, xử lý ngoại lệ |
| ACT-03 | Administrator | Primary | Cấu hình giá, slot, tài khoản |
| ACT-04 | LPR Camera | Secondary | Gửi biển số đọc được |
| ACT-05 | Slot Sensor | Secondary | Báo slot có xe / trống |
| ACT-06 | Payment Gateway | Secondary | Xử lý thanh toán online |

### 2.4 Ràng buộc

- Chạy trên trình duyệt (Chrome, Edge, Safari bản mới nhất), không cần cài app.
- Tiền tệ VND; giờ theo múi UTC+7.
- Dữ liệu cá nhân xử lý theo Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân.

### 2.5 Giả định

- Bãi xe có 2 tầng, mỗi tầng 2 khu, tổng 200 slot.
- Camera và cảm biến có API gửi sự kiện qua mạng nội bộ.
- Biển số theo định dạng Việt Nam, ví dụ `30A-123.45`.

## 3. Yêu cầu chức năng

Yêu cầu chức năng tổ chức thành cây 3 cấp: gốc `SP`, 4 nhóm chức năng, rồi đến yêu cầu nguyên tử. ID dạng chấm cho biết vị trí trong cây: `SP-2.2.1` là con của `SP-2.2`. Chỉ nút lá mới có tiêu chí chấp nhận và được kiểm thử.

&#91;embedded content: cây yêu cầu chức năng · 4 nhóm, 14 nút lá\]

SP-2 sâu nhất vì "Đặt chỗ trước" tách thành 2 yêu cầu con có thể kiểm thử riêng.

### 3.1 Chi tiết nút lá

| ID | Parent | Yêu cầu | Priority | Tiêu chí chấp nhận | Source |
| --- | --- | --- | --- | --- | --- |
| SP-1.1 | SP-1 | Hệ thống phải ghi nhận biển số và giờ vào khi camera LPR đọc được biển số ở cổng vào. | Must | Phiên đỗ mới được tạo với đúng biển số và giờ vào. | STK-01 |
| SP-1.2 | SP-1 | Hệ thống phải mở barrier khi phiên đỗ được tạo hoặc đã thanh toán. | Must | Barrier mở trong 3 giây sau sự kiện hợp lệ. | STK-04 |
| SP-1.3 | SP-1 | Hệ thống phải đóng phiên đỗ và ghi giờ ra khi xe qua cổng ra. | Must | Phiên đỗ có trạng thái Closed và giờ ra. | STK-01 |
| SP-2.1 | SP-2 | Hệ thống phải hiển thị số slot trống theo từng tầng và khu. | Must | Số hiển thị khớp trạng thái cảm biến trong vòng 5 giây. | STK-03 |
| SP-2.2.1 | SP-2.2 | Hệ thống phải cho tài xế giữ một slot trống trong tối đa 15 phút. | Should | Slot được giữ chuyển sang trạng thái Reserved. | STK-03 |
| SP-2.2.2 | SP-2.2 | Hệ thống phải tự hủy đặt chỗ khi quá 15 phút mà xe chưa vào. | Should | Slot trở lại Available ở phút thứ 16. | STK-01 |
| SP-2.3 | SP-2 | Hệ thống phải gợi ý slot trống gần lối vào nhất khi xe vào. | Could | Slot gợi ý có khoảng cách nhỏ nhất trong các slot trống. | STK-03 |
| SP-3.1 | SP-3 | Hệ thống phải tính phí theo bảng giá hiện hành khi phiên đỗ kết thúc. | Must | Với giá mẫu 20.000 VND cho 2 giờ đầu và 10.000 VND mỗi giờ sau (làm tròn lên), phiên 3 giờ 10 phút tính 40.000 VND. | STK-01 |
| SP-3.2 | SP-3 | Hệ thống phải cho thanh toán online bằng mã QR. | Should | Giao dịch thành công đổi phiên sang Paid. | STK-03 |
| SP-3.3 | SP-3 | Hệ thống phải gửi hóa đơn điện tử qua email khi tài xế yêu cầu. | Could | Email hóa đơn đến trong 5 phút sau thanh toán. | STK-05 |
| SP-4.1 | SP-4 | Hệ thống phải cho Administrator cấu hình bảng giá. | Must | Giá mới áp dụng cho phiên bắt đầu sau thời điểm lưu. | STK-01 |
| SP-4.2 | SP-4 | Hệ thống phải xuất báo cáo doanh thu theo ngày. | Should | Tổng báo cáo bằng tổng các phiên Paid trong ngày. | STK-01 |
| SP-4.3 | SP-4 | Hệ thống phải chặn tài khoản Driver truy cập chức năng quản trị. | Must | Tài khoản Driver mở trang quản trị nhận lỗi 403. | STK-02 |
| SP-4.4 | SP-4 | Hệ thống phải ghi audit log cho mọi thao tác mở barrier thủ công. | Must | Mỗi lần mở thủ công có 1 dòng log gồm người làm, giờ, lý do. | STK-02 |

### 3.2 Yêu cầu giao diện

SPMS không tự chạy model nhận diện biển số. Camera ANPR mua sẵn tự nhận diện và gửi kết quả sang; khi demo, một script mock đóng vai camera.

| ID | Yêu cầu | Priority | Tiêu chí chấp nhận | Test case |
| --- | --- | --- | --- | --- |
| IF-01 | Hệ thống phải nhận sự kiện biển số qua `POST /api/lpr-events` với JSON gồm `plate`, `confidence`, `gate_id`, `timestamp`. | Must | Request hợp lệ trả HTTP 201 và tạo sự kiện cổng tương ứng. | TC-15 |
| IF-02 | Hệ thống phải cho Attendant nhập tay biển số khi `confidence < 0.8` hoặc quá 5 giây không có sự kiện. | Must | Màn hình cổng hiện ô nhập tay; mỗi lần nhập tay có audit log. | TC-16 |

## 4. Yêu cầu phi chức năng

Mọi NFR đều có metric và target đo được, để kiểm chứng được.

| ID | Category | Yêu cầu | Metric | Target | Priority | Verification |
| --- | --- | --- | --- | --- | --- | --- |
| NFR-01 | Performance | Nhận diện biển số đủ nhanh để xe không phải dừng lâu ở cổng. | Thời gian từ lúc xe dừng đến lúc barrier mở, p95 | ≤ 3 giây | Must | Test |
| NFR-02 | Accuracy | LPR đọc đúng biển số trong điều kiện ánh sáng bình thường. | Tỉ lệ đọc đúng trên bộ mẫu 500 ảnh | ≥ 95% | Must | Test |
| NFR-03 | Availability | Hệ thống hoạt động liên tục vì bãi mở 24/7. | Uptime theo tháng | ≥ 99,5% | Must | Analysis |
| NFR-04 | Security | Dữ liệu biển số và tài khoản được mã hóa. | Phạm vi mã hóa | 100% dữ liệu cá nhân (AES-256 khi lưu, TLS 1.2+ khi truyền) | Must | Inspection |
| NFR-05 | Usability | Tài xế mới đặt chỗ được mà không cần hướng dẫn. | Thời gian hoàn thành đặt chỗ, người dùng lần đầu | ≤ 1 phút | Should | Demonstration |
| NFR-06 | Scalability | Hệ thống mở rộng được khi bãi thêm tầng. | Số slot quản lý được mà vẫn đạt NFR-01 | ≥ 1.000 slot | Could | Analysis |

## 5. Use cases

### UC-01 Xe vào bãi

- **Actor chính:** Driver. **Actor phụ:** LPR Camera.
- **Tiền điều kiện:** Bãi còn ít nhất 1 slot trống.
- **Luồng chính:**
  1. Xe dừng trước cổng vào.
  2. Camera đọc biển số và gửi cho hệ thống.
  3. Hệ thống tạo phiên đỗ và gợi ý slot.
  4. Barrier mở, xe vào.
- **Luồng thay thế:** 2a. Camera không đọc được biển số: Attendant nhập tay, hệ thống ghi audit log.
- **Hậu điều kiện:** Phiên đỗ ở trạng thái Active.
- **Truy vết:** SP-1.1, SP-1.2, SP-2.3, SP-4.4.

### UC-02 Đặt chỗ trước

- **Actor chính:** Driver.
- **Tiền điều kiện:** Driver đã đăng nhập.
- **Luồng chính:**
  1. Driver xem số slot trống theo tầng.
  2. Driver chọn một slot và xác nhận.
  3. Hệ thống giữ slot trong 15 phút.
- **Luồng thay thế:** 3a. Quá 15 phút xe chưa vào: hệ thống hủy đặt chỗ, slot trở lại Available.
- **Hậu điều kiện:** Slot ở trạng thái Reserved.
- **Truy vết:** SP-2.1, SP-2.2.1, SP-2.2.2.

### UC-03 Xe ra và thanh toán

- **Actor chính:** Driver. **Actor phụ:** LPR Camera, Payment Gateway.
- **Tiền điều kiện:** Xe có phiên đỗ Active.
- **Luồng chính:**
  1. Camera cổng ra đọc biển số.
  2. Hệ thống tính phí và hiển thị mã QR.
  3. Driver quét QR và thanh toán.
  4. Hệ thống đóng phiên, barrier mở.
- **Luồng thay thế:** 3a. Thanh toán thất bại: barrier giữ đóng, Attendant thu tiền mặt và mở thủ công (có audit log).
- **Hậu điều kiện:** Phiên đỗ ở trạng thái Closed và Paid.
- **Truy vết:** SP-1.3, SP-3.1, SP-3.2, SP-4.4.

## 6. Rủi ro và truy vết

### 6.1 Hazards

| ID | Hazard | Nguyên nhân | Severity (1–5) | Likelihood (1–5) | Giảm thiểu | Liên quan |
| --- | --- | --- | --- | --- | --- | --- |
| HZ-01 | Barrier hạ xuống khi xe đang đi qua | Cảm biến vật cản lỗi | 5 | 2 | Cảm biến an toàn phần cứng chặn hạ barrier, độc lập với phần mềm | SP-1.2 |
| HZ-02 | Tính phí nhầm xe | LPR đọc sai biển số | 3 | 3 | Hiển thị ảnh xe lúc vào để Driver xác nhận trước khi trả tiền | SP-3.1, NFR-02 |
| HZ-03 | Không ra được khi mất kết nối thanh toán | Payment Gateway ngừng hoạt động | 3 | 2 | Attendant thu tiền mặt, mở barrier thủ công có log | SP-3.2, SP-4.4 |
| HZ-04 | Lộ dữ liệu biển số và lịch sử đỗ xe | Truy cập trái phép vào DB | 4 | 2 | Mã hóa dữ liệu, phân quyền theo vai trò | NFR-04, SP-4.3 |

### 6.2 Ma trận truy vết

Mỗi nút lá có ít nhất một test case.

| Yêu cầu | Use case | Test case | Loại test |
| --- | --- | --- | --- |
| SP-1.1 | UC-01 | TC-01 Xe vào tạo phiên đỗ đúng biển số | Positive |
| SP-1.2 | UC-01 | TC-02 Barrier mở trong 3 giây | Positive |
| SP-1.3 | UC-03 | TC-03 Xe ra đóng phiên đỗ | Positive |
| SP-2.1 | UC-02 | TC-04 Số slot trống khớp cảm biến | Positive |
| SP-2.2.1 | UC-02 | TC-05 Đặt chỗ chuyển slot sang Reserved | Positive |
| SP-2.2.2 | UC-02 | TC-06 Đặt chỗ tự hủy ở phút 16 | Boundary |
| SP-2.3 | UC-01 | TC-07 Gợi ý slot gần lối vào nhất | Positive |
| SP-3.1 | UC-03 | TC-08 Phiên 3 giờ 10 phút tính 40.000 VND | Boundary |
| SP-3.2 | UC-03 | TC-09 Thanh toán QR thất bại giữ barrier đóng | Negative |
| SP-3.3 | UC-03 | TC-10 Email hóa đơn đến trong 5 phút | Positive |
| SP-4.1 | – | TC-11 Giá mới chỉ áp dụng cho phiên mới | Positive |
| SP-4.2 | – | TC-12 Tổng báo cáo bằng tổng phiên Paid | Positive |
| SP-4.3 | – | TC-13 Driver vào trang quản trị nhận 403 | Negative |
| SP-4.4 | UC-01, UC-03 | TC-14 Mở barrier thủ công sinh 1 dòng log | Positive |
