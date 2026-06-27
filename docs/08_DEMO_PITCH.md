# 08 — Demo and Pitch Script

## 1. Core story

### Opening

“Mỗi ngày, người dùng nhận được những tin nhắn yêu cầu chuyển tiền, cung cấp OTP hoặc bấm vào đường dẫn lạ. Vấn đề không phải là thiếu thông tin. Vấn đề là thông tin nằm rải rác, khó đánh giá và người dùng thường phải quyết định trong trạng thái bị thúc ép.”

### Problem

“Các công cụ hiện tại thường chỉ kiểm tra một phần: một đường dẫn, một số điện thoại hoặc một từ khóa. Người dùng vẫn phải tự ghép các mảnh bằng chứng và tự quyết định.”

### Solution

“VYVY hoạt động như một nhóm điều tra AI: hiểu nội dung, cảnh báo sớm, tìm bằng chứng, để nhiều chuyên gia tranh luận, sau đó dùng một trọng tài để đưa ra kết luận có thể giải thích.”

## 2. Four-minute demo

### 0:00–0:30 — Context

- Show suspicious message.
- Highlight urgency, money or credential request.

### 0:30–1:00 — Fast Check

- Paste text.
- Click Analyze.
- Show immediate warning.
- Explain that VYVY prioritizes user safety before the deeper investigation finishes.

### 1:00–2:00 — Investigation

- Show progress.
- Explain:
  - Intake extracts entities and claims.
  - Search finds external evidence.
  - Four experts analyze different dimensions.
  - Behavioral Analyst detects manipulation.
  - Judge rejects unsupported arguments.

### 2:00–3:15 — Report

- Show risk and confidence separately.
- Show why the score is high.
- Open top evidence.
- Show one disagreement or limitation.
- Show safety recommendations.

### 3:15–4:00 — Differentiation

- Explain that VYVY does not merely label.
- It shows evidence, expert consensus, confidence and next steps.
- Mention text-only scope as a deliberate hackathon MVP.
- State future expansion only after the working demo.

## 3. Key judging points

### Innovation

Multi-agent investigation and debate, not a single chatbot response.

### Technical quality

- Structured outputs.
- Parallel agents.
- Evidence-grounded claims.
- Deterministic scoring.
- Failure-aware confidence.

### User value

- Immediate warning.
- Understandable reasons.
- Actionable next steps.
- Vietnamese-first experience.

### Feasibility

- Text-only MVP.
- Provider adapters.
- Mock Mode.
- Clear path to image/link/document support later.

## 4. Questions and answers

### “How do you prevent hallucinated evidence?”

“Experts cannot create evidence. They can only cite evidence IDs returned by the search adapter. The Judge rejects references that do not exist.”

### “Why use multiple agents?”

“Different scams combine financial, cyber, official-procedure and social-engineering signals. Narrow expert roles reduce blind spots and make disagreements visible.”

### “Is 96% a probability?”

“In our implementation it is a calibrated risk score, not a legal probability. We show a separate confidence score to represent evidence quality and completeness.”

### “What happens without internet?”

“Mock Mode uses a fixed, labeled demo fixture. In normal mode, if search fails, the system continues text analysis, discloses the missing data and lowers confidence.”

### “Does VYVY declare someone a criminal?”

“No. VYVY identifies risk signals and recommends verification. It does not determine guilt or provide a legal judgment.”

## 5. Backup demo package

Prepare:

- 60–90 second screen recording.
- Screenshots of Fast Warning and full report.
- One exported Markdown report.
- Local backend and frontend.
- Mock Mode fixture.
- A slide with the architecture.
- A slide with the scoring formula.
