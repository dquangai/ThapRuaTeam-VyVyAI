# 05 — Verification and Confidence Scoring

## 1. Separate risk from confidence

Two numbers are required:

- **Risk Score:** How dangerous the content appears.
- **Confidence Score:** How strong and complete the supporting basis is.

A high risk score with low confidence means “strong warning signs, but insufficient external confirmation”.

## 2. Risk formula

All components are normalized to 0–100:

```text
risk_score =
    0.35 × evidence_risk
  + 0.25 × source_risk
  + 0.20 × consensus_risk
  + 0.10 × context_risk
  + 0.10 × behavioral_risk
```

Clamp to 0–100 and round to one decimal.

## 3. Component definitions

### Evidence Risk — 35%

Measures how directly the collected evidence supports scam indicators.

Examples:

- Official warning names the same domain/entity.
- Multiple sources report the same mechanism.
- Domain or phone appears in a warning database.
- Message claims conflict with verified facts.

### Source Risk — 25%

Measures the risk inferred from source properties:

- Suspicious or newly registered domain.
- No official ownership.
- Source identity mismatch.
- Low-reputation hosting or redirects.
- Claims found only on low-quality sources.

### Consensus Risk — 20%

Weighted average of expert risk scores.

Suggested expert weights:

- Cyber: 30%
- Financial: 25%
- OSINT: 25%
- Legal Risk: 20%

Weights can be adjusted by domain.

### Context Risk — 10%

Text-level context:

- Money request.
- Credential request.
- Urgency.
- Impersonation.
- Internal contradictions.
- Unrealistic benefit.

### Behavioral Risk — 10%

Manipulation severity:

- Fear.
- Authority pressure.
- FOMO.
- Secrecy.
- Isolation.
- Scarcity.

## 4. Risk labels

| Score | Label | Meaning |
|---|---|---|
| 0–24 | Low | Few direct warning signs |
| 25–49 | Uncertain | Some warning signs; verify |
| 50–74 | Suspicious | Multiple meaningful indicators |
| 75–89 | High Risk | Strong indicators; avoid action |
| 90–100 | Critical | Immediate safety warning |

## 5. Confidence formula

```text
confidence =
    0.30 × evidence_coverage
  + 0.25 × source_quality
  + 0.25 × expert_agreement
  + 0.20 × data_completeness
```

Apply penalties:

- Search unavailable: -20.
- More than one expert failed: -15.
- No official or high-quality source: -10.
- Input too vague: -10.
- Mock Mode: label as demo confidence, not real confidence.

## 6. Deterministic implementation

The LLM may propose component scores, but the final score must be calculated in code.

Required tests:

- All zeros returns zero.
- All hundreds returns 100.
- Score is clamped.
- Missing components use documented fallback.
- Search failure reduces confidence.
- One expert failure does not crash scoring.
- Rounding is stable.

## 7. Wording rules

Do not say:

- “Đây chắc chắn là lừa đảo.”
- “Tổ chức này là tội phạm.”

Prefer:

- “Nội dung có nguy cơ lừa đảo rất cao.”
- “Có nhiều dấu hiệu phù hợp với mô hình lừa đảo.”
- “Chưa đủ dữ liệu để xác nhận danh tính.”
- “Hãy xác minh qua kênh chính thức trước khi hành động.”
