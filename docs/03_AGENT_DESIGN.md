# 03 — Agent Design and Prompt Contracts

## 1. Design principle

Each agent should answer one narrow question and return structured data. Avoid giving an agent the whole product mission and asking it to “investigate everything”.

## 2. Intake Agent

### Purpose

Convert raw text into a clean investigation context.

### Input

- Raw text
- Locale

### Output

```json
{
  "summary": "string",
  "language": "vi",
  "domain": "banking|recruitment|ecommerce|government|investment|other",
  "intent": "payment_request|credential_request|account_threat|offer|other",
  "entities": [
    {
      "text": "string",
      "type": "organization|person|phone|bank_account|domain|url|amount|date|other"
    }
  ],
  "claims": ["string"],
  "is_ready": true,
  "clarification_question": null
}
```

### Prompt rules

- Do not decide the final scam score.
- Preserve uncertainty.
- Extract only entities present in text.
- Do not invent a company name.
- Produce concise claims suitable for search.

## 3. Scam Pattern Classifier

### Purpose

Identify likely scam pattern categories.

### Categories

- Urgent money transfer
- Account lock threat
- OTP/password request
- Government impersonation
- Bank impersonation
- Recruitment fee
- Prize or giveaway
- Investment return promise
- Fake marketplace payment
- Phishing link
- Remote-control app request
- Romance/social engineering
- Unknown

### Output

```json
{
  "patterns": [
    {
      "label": "phishing_link",
      "probability": 0.84,
      "evidence_spans": ["..."]
    }
  ],
  "primary_pattern": "phishing_link",
  "requires_immediate_warning": true
}
```

## 4. Fast Check

### Purpose

Return an immediate, conservative warning.

### Inputs

- Original text
- Rule matches
- Classifier summary

### Rules that should trigger strong caution

- Requests to send money immediately.
- Requests for OTP, password or PIN.
- Threat of account closure or arrest.
- Remote-control application request.
- Unusual domain or shortened link.
- Upfront recruitment or prize fee.
- Guaranteed high return.
- Request to keep the transaction secret.

### Output

```json
{
  "risk_band": "low|medium|high|critical",
  "score": 0,
  "triggered_flags": [],
  "message": "string",
  "immediate_actions": []
}
```

Fast Check is not the final verdict. It is a safety-first early warning.

## 5. Evidence Query Planner

Generate no more than three focused queries:

1. Entity + scam/fraud warning.
2. Domain/phone/account + warning.
3. Claim + official source.

Avoid broad searches. Reuse extracted entities.

## 6. Financial Expert

### Question

Does the message use financial mechanisms commonly associated with fraud?

### Focus

- Transfer destination.
- Upfront fees.
- Guaranteed return.
- Payment urgency.
- Unusual payment rails.
- Mismatch between claim and payment request.

### Output

- Verdict.
- Risk score.
- Reasons.
- Evidence IDs.
- Missing information.
- Confidence.

## 7. Legal Risk Expert

### Question

Does the claim misuse legal or official authority, or conflict with common official procedures?

### Boundaries

- This is not legal advice.
- Do not assert illegality without evidence.
- Highlight procedure inconsistencies.
- Recommend verification through official channels.

## 8. Cyber Expert

### Question

Are there phishing, credential theft, malicious-link or account-takeover signals?

### Focus

- Domain mismatch.
- Suspicious link structure.
- Credential request.
- OTP request.
- Remote access.
- Device installation request.
- Security urgency.

## 9. OSINT Expert

### Question

What do open sources say about the entities, domains, phone numbers and claims?

### Focus

- Official advisories.
- Domain age when available.
- Repeated reports.
- Cross-source corroboration.
- Source reliability.

OSINT Expert may cite only provided evidence IDs.

## 10. Behavioral Analyst

### Red flags

- FOMO.
- Urgency.
- Authority pressure.
- Fear.
- Scarcity.
- Isolation.
- Secrecy.
- Social proof manipulation.
- Reciprocity.
- Gradual commitment.

### Output

```json
{
  "red_flags": [
    {
      "type": "urgency",
      "severity": "high",
      "evidence_span": "Chuyển tiền trong 10 phút...",
      "explanation": "Creates time pressure to reduce verification."
    }
  ],
  "behavioral_risk_score": 82,
  "summary": "string"
}
```

## 11. Judge Agent

### Purpose

Aggregate, challenge and resolve expert outputs.

### Required steps

1. Check whether cited evidence IDs exist.
2. Remove unsupported claims.
3. Identify expert disagreements.
4. Distinguish facts from inferences.
5. Produce a consensus risk.
6. State missing evidence.
7. Propose a calibrated conclusion.

### Judge output

```json
{
  "consensus_score": 0,
  "consensus_label": "safe|uncertain|suspicious|high_risk",
  "supported_findings": [],
  "rejected_findings": [],
  "disagreements": [],
  "missing_evidence": [],
  "reasoning_summary": "string"
}
```

## 12. Safety Advisor

Advice must be practical and non-alarmist.

Priority order:

1. Stop irreversible action.
2. Protect credentials.
3. Verify independently.
4. Preserve evidence.
5. Contact an appropriate trusted organization.
6. Report when necessary.

Never tell a user to confront a suspected scammer.

## 13. Report Generator

The report should contain:

- Conclusion.
- Risk score.
- Confidence.
- Top reasons.
- Expert summary.
- Evidence list.
- Behavioral red flags.
- Recommended actions.
- Limitations.

The report generator must not change numeric scores. It only formats previously calculated results.
