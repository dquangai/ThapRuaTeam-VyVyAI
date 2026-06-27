# VYVY Hackathon Vibe Coding Kit

**Sản phẩm:** VYVY — AI Investigation & Verification Engine  
**Thông điệp:** *Investigate. Debate. Verify. Explain.*  
**Ngày chuẩn bị:** 26/06/2026  
**Ngày thi dự kiến:** 27/06/2026  
**Giới hạn:** Build trong một ngày; MVP hiện tại **chỉ nhận văn bản**.

Bộ tài liệu này được thiết kế để đội thi có thể mở repository, giao từng nhiệm vụ nhỏ cho Codex, kiểm tra kết quả, ghép hệ thống và chuẩn bị demo mà không bị trôi phạm vi.

## 1. Mục tiêu demo cuối ngày

Người dùng dán một đoạn chat, email hoặc nội dung đáng ngờ. VYVY sẽ:

1. Chuẩn hóa và hiểu nội dung.
2. Cảnh báo nhanh các dấu hiệu nguy hiểm trong khoảng vài giây.
3. Tách thực thể và tạo truy vấn điều tra.
4. Thu thập bằng chứng từ nhiều nguồn hoặc từ bộ dữ liệu demo khi API ngoài không khả dụng.
5. Cho bốn chuyên gia AI đánh giá song song:
   - Financial Expert
   - Legal Risk Expert
   - Cyber Expert
   - OSINT Expert
6. Phân tích kỹ thuật thao túng tâm lý.
7. Để Judge Agent tổng hợp, loại bỏ lập luận yếu và tính điểm.
8. Sinh báo cáo dễ hiểu gồm kết luận, lý do, bằng chứng và hành động an toàn.

## 2. Phạm vi bị khóa

### Có trong MVP

- Một ô nhập văn bản.
- Fast Check theo rule và LLM có cấu trúc.
- Full Investigation.
- Tìm kiếm bằng chứng qua adapter.
- Bốn expert chạy song song.
- Behavioral Risk.
- Judge + Verification Score.
- Safety Advice.
- Báo cáo trên web.
- Xuất Markdown hoặc copy báo cáo.
- Mock Mode để demo không phụ thuộc mạng.

### Không làm trong ngày thi

- OCR, xử lý ảnh, screenshot, PDF hoặc file upload.
- Browser extension.
- Đăng nhập, phân quyền, admin dashboard.
- Cơ sở dữ liệu người dùng.
- Hệ thống học liên tục hoặc tự huấn luyện.
- Realtime monitoring.
- Web crawler tổng quát.
- Thanh toán.
- Mobile app.
- Kết luận pháp lý hoặc buộc tội tổ chức/cá nhân.

## 3. Thứ tự đọc

1. `AGENTS.md`
2. `docs/00_HACKATHON_MASTER_PLAN.md`
3. `docs/01_SCOPE_LOCK.md`
4. `specs/active/mvp/requirements.md`
5. `specs/active/mvp/design.md`
6. `specs/active/mvp/tasks.md`
7. `docs/12_CODEX_PROMPT_PACK.md`
8. `docs/07_TEST_PLAN.md`
9. `docs/08_DEMO_PITCH.md`

## 4. Cách dùng với Codex

Codex nên được giao **một nhiệm vụ nhỏ mỗi lần**. Trước mỗi task:

- Yêu cầu đọc `AGENTS.md`.
- Chỉ định task ID trong `specs/active/mvp/tasks.md`.
- Chỉ định files được phép sửa.
- Yêu cầu chạy đúng lệnh kiểm tra.
- Yêu cầu báo cáo `git diff --stat`, test result và rủi ro còn lại.
- Không yêu cầu “xây toàn bộ dự án” bằng một prompt duy nhất.

## 5. Kết quả tối thiểu để được coi là hoàn thành

- `GET /health` trả `200`.
- Fast Check trả kết quả hợp lệ dưới ngưỡng latency đội thi đặt ra.
- Full Investigation trả JSON đúng schema.
- Có ít nhất 4 tình huống demo.
- Không có nguồn bằng chứng giả.
- Khi search lỗi, UI nói rõ “không lấy được dữ liệu ngoài” và giảm confidence.
- Frontend không crash với input rỗng, input dài hoặc API lỗi.
- Có nút chạy demo bằng dữ liệu mẫu.
- Có video dự phòng hoặc ảnh chụp màn hình kết quả.
