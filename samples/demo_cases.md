# Demo Cases

All cases are synthetic.

## Case 1 — OTP phishing

### Input

“Bộ phận hỗ trợ ngân hàng thông báo tài khoản của bạn đang bị khóa. Hãy gửi mã OTP vừa nhận để xác minh trong 10 phút, nếu không tài khoản sẽ bị hủy.”

### Expected

- Fast Check: critical.
- Full risk: high/critical.
- Flags: OTP, authority, urgency, account threat.
- Advice: do not share OTP; contact bank through official channel.

## Case 2 — Recruitment fee

### Input

“Bạn đã trúng tuyển làm việc online với thu nhập 15 triệu mỗi tháng. Để kích hoạt hồ sơ, vui lòng chuyển 850.000 đồng phí bảo đảm trong hôm nay.”

### Expected

- Fast Check: high.
- Full risk: suspicious/high.
- Flags: upfront fee, unrealistic offer, urgency.

## Case 3 — Fake authority payment

### Input

“Cơ quan điều tra yêu cầu bạn nộp tiền vào tài khoản tạm giữ để chứng minh không liên quan vụ án. Không được nói với người khác vì hồ sơ đang bảo mật.”

### Expected

- Fast Check: critical.
- Full risk: high/critical.
- Flags: authority pressure, money transfer, secrecy, fear.

## Case 4 — Ambiguous marketplace message

### Input

“Người mua nói đã thanh toán và gửi một đường dẫn để tôi đăng nhập nhận tiền. Họ thúc giục tôi hoàn thành ngay vì giao dịch sắp hết hạn.”

### Expected

- Fast Check: high.
- Full risk: suspicious/high depending on evidence.
- Flags: link, login request, urgency.

## Case 5 — Benign reminder

### Input

“Nhà trường nhắc sinh viên hoàn thành khảo sát môn học trước thứ Sáu. Không yêu cầu chuyển tiền, cung cấp mật khẩu hoặc mã OTP. Truy cập cổng thông tin quen thuộc của trường.”

### Expected

- Fast Check: low.
- Full risk: low/uncertain.
- Advice: verify domain if unsure.
