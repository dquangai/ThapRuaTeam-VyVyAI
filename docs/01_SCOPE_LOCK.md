# 01 — Scope Lock

## 1. User problem

People receive suspicious messages involving money, accounts, recruitment, prizes, government impersonation or urgent requests. Information needed to verify the claim is scattered, difficult to evaluate and time-consuming to search.

## 2. Target user

A Vietnamese internet user who:

- Has received a suspicious message or email.
- Does not know which source to trust.
- Needs a quick safety recommendation.
- Wants an explanation rather than a black-box score.

## 3. Primary user story

> As a user, I paste suspicious text so that VYVY can warn me quickly, investigate relevant claims, show supporting evidence and recommend safe next steps.

## 4. MVP input

One field:

```text
investigation_text: string
```

The user may paste:

- A chat transcript.
- An email body.
- An advertisement.
- A recruitment message.
- A payment request.
- A URL included as text.

No files are uploaded. No OCR is performed.

## 5. MVP output

The UI must show:

1. **Fast warning**
   - Risk band.
   - Triggered red flags.
   - Immediate action.

2. **General conclusion**
   - Scam risk score, 0–100.
   - Confidence score, 0–100.
   - One-sentence conclusion.

3. **Why**
   - Expert assessments.
   - Behavioral manipulation indicators.
   - Key evidence.

4. **Evidence**
   - Source.
   - Title.
   - Relevance.
   - Credibility.
   - Link.

5. **Recommended actions**
   - Do not transfer money.
   - Do not share OTP/password.
   - Verify through an official channel.
   - Save evidence.
   - Report through appropriate official mechanisms.

## 6. Functional requirements

- Text length validation.
- Vietnamese-first response.
- Fast Check endpoint.
- Full Investigation endpoint.
- Structured LLM outputs.
- External search adapter.
- Source scoring.
- Four expert assessments.
- Behavioral analysis.
- Judge aggregation.
- Deterministic verification score.
- Explainable report.
- Mock Mode.
- Markdown export or copy.

## 7. Non-functional requirements

- No evidence fabrication.
- Graceful provider failure.
- Configurable timeout.
- Deterministic score from structured components.
- Readable response within one screen plus scroll.
- Testable modules.
- No secret exposure.
- Demo works without database.

## 8. Explicit non-goals

- Determining criminal guilt.
- Replacing police, bank or legal professionals.
- Guaranteeing that a message is safe.
- Tracking users.
- Auto-contacting third parties.
- Full malware scanning.
- Reverse image search.
- Processing screenshots and documents.
- Production-grade scaling.

## 9. Demo acceptance criteria

The demo is accepted when:

- A suspicious sample returns a high-risk warning and clear reasons.
- A benign sample returns low or uncertain risk.
- Evidence cards show only returned search data or labeled fixture data.
- Search failure lowers confidence instead of creating sources.
- The UI remains usable when the backend returns partial results.
