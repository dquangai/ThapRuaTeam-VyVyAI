# 06 — UI/UX for the Demo

## 1. Single-page structure

### Header

- VYVY logo.
- Product name.
- Tagline: Investigate. Debate. Verify. Explain.
- Small “Hackathon MVP — Text Only” badge.

### Input section

- Large textarea.
- Character counter.
- Example case selector.
- Analyze button.
- Clear button.
- Privacy note: “Nội dung được xử lý cho phiên phân tích; không lưu trong MVP.”

### Fast warning section

Appears immediately after `/fast-check`.

- Risk badge.
- Top three red flags.
- One immediate action.
- “Đang tiếp tục điều tra đa nguồn…”

### Investigation progress

Display fixed stages:

1. Understanding content.
2. Finding evidence.
3. Expert debate.
4. Judge verification.
5. Creating report.

The progress indicator may follow request status locally; do not pretend that a stage completed if the backend failed.

### Report section

A. General conclusion  
B. Why this score  
C. Top evidence  
D. Recommended actions

## 2. Visual hierarchy

Highest priority:

- Risk score.
- Conclusion.
- Immediate actions.

Second priority:

- Evidence.
- Expert consensus.
- Behavioral red flags.

Third priority:

- Technical details.
- Timings.
- Raw JSON.

## 3. Color semantics

- Green: low risk.
- Amber: uncertain.
- Orange: suspicious.
- Red: high/critical.
- Gray: unavailable or incomplete.
- Purple/blue: AI analysis and neutral information.

Do not rely on color alone. Always include text labels and icons.

## 4. Required states

- Empty.
- Typing.
- Fast checking.
- Fast warning.
- Full investigating.
- Completed.
- Partial data.
- Error.
- Mock Mode.
- No evidence found.

## 5. Demo-first features

Must have:

- Example dropdown.
- One-click copy report.
- Reset button.
- Mock Mode badge.
- Clear latency display.
- Evidence links.
- Expand/collapse expert details.

Nice to have only after core stability:

- Animated graph.
- PDF export.
- Dark mode.
- Full raw trace.
- Complex charts.

## 6. Accessibility basics

- Button labels must be explicit.
- Text contrast must be readable.
- Textarea needs a label.
- Loading state needs text, not only animation.
- Do not use tiny evidence text.
- Keyboard interaction must work.

## 7. Presentation sequence

1. Start from an empty input.
2. Select a demo case.
3. Read one suspicious sentence aloud.
4. Click Analyze.
5. Point at Fast Warning.
6. Explain parallel investigation while loading.
7. Reveal the report.
8. Open one evidence card.
9. Show expert consensus.
10. End on safe actions.
