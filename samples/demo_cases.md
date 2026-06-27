# Demo Cases

All cases are synthetic and deterministic. Mock evidence is labeled with `VYVY Mock Evidence`
and uses `.example` URLs reserved for documentation/demo data.

## Case 1 — OTP phishing

**Case ID:** `bank_otp_phishing`

### Input

“Ngân hàng VYBank Demo thông báo tài khoản của bạn đang bị khóa. Hãy gửi mã OTP vừa nhận để xác minh trong 10 phút, nếu không tài khoản sẽ bị hủy.”

### Expected

- Fast Check risk band: `critical`.
- Full investigation risk band: `high_risk`.
- Flags: OTP, urgency, account threat.
- Mock evidence: `mock_bank_otp_advisory`, `mock_account_lock_script`.
- Advice: do not share OTP; contact the bank through a known official channel.

## Case 2 — Recruitment fee

**Case ID:** `recruitment_fee`

### Input

“Bạn đã trúng tuyển làm việc online với thu nhập 15 triệu mỗi tháng. Để kích hoạt hồ sơ, vui lòng chuyển 850.000 đồng phí bảo đảm trong hôm nay.”

### Expected

- Fast Check risk band: `suspicious`.
- Full investigation risk band: `suspicious`.
- Flags: upfront fee, unrealistic offer, urgency.
- Mock evidence: `mock_recruitment_fee_pattern`.
- Advice: do not pay upfront; verify the recruiter through independent channels.

## Case 3 — Fake authority payment

**Case ID:** `fake_authority_payment`

### Input

“Tổ xác minh hồ sơ Demo yêu cầu bạn nộp tiền vào tài khoản tạm giữ để chứng minh không liên quan vụ việc. Không được nói với người khác vì hồ sơ đang bảo mật.”

### Expected

- Fast Check risk band: `critical`.
- Full investigation risk band: `high_risk`.
- Flags: authority pressure, money transfer, secrecy, fear.
- Mock evidence: `mock_authority_payment_script`, `mock_secrecy_pressure`.
- Advice: do not transfer money; verify through a trusted public contact.

## Case 4 — Ambiguous marketplace message

**Case ID:** `marketplace_login_link`

### Input

“Người mua nói đã thanh toán và gửi một đường dẫn để tôi đăng nhập nhận tiền. Họ thúc giục tôi hoàn thành ngay vì giao dịch sắp hết hạn.”

### Expected

- Fast Check risk band: `suspicious`.
- Full investigation risk band: `uncertain`.
- Flags: link, login request, urgency.
- Mock evidence: `mock_marketplace_login_pattern`.
- Advice: do not log in through the message link; open the marketplace manually.

## Case 5 — Benign reminder

**Case ID:** `benign_school_reminder`

### Input

“Trường Demo nhắc sinh viên hoàn thành khảo sát môn học trước thứ Sáu. Không yêu cầu chuyển tiền, cung cấp mật khẩu hoặc mã OTP. Truy cập cổng thông tin quen thuộc của trường.”

### Expected

- Fast Check risk band: `low`.
- Full investigation risk band: `low`.
- Flags: none expected.
- Mock evidence: `mock_benign_survey_reference`.
- Advice: no urgent action; verify the domain if unsure.
