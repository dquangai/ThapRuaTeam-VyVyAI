# 07 — Test Plan

## 1. Test pyramid for a one-day build

Focus on high-value tests:

1. Deterministic unit tests.
2. Contract tests.
3. One integration smoke test.
4. Manual UI demo tests.
5. Provider failure tests.

Do not spend the day building exhaustive coverage.

## 2. Backend unit tests

### Input validation

- Empty text rejected.
- Whitespace-only text rejected.
- Text above maximum length rejected.
- Vietnamese Unicode accepted.
- URL inside text accepted as plain text.

### Fast Check

- OTP request triggers critical flag.
- Urgent transfer triggers high flag.
- Account lock threat triggers flag.
- Benign appointment message does not trigger high risk.
- Score remains 0–100.
- Duplicate flags are deduplicated.

### Source scoring

- Official government/bank source scores above unknown blog.
- Missing date does not crash.
- Invalid URL handled.
- Multiple corroborating sources increase support.
- Low-quality source below threshold can be excluded.

### Experts

- Output validates against schema.
- Evidence IDs must exist.
- Missing evidence produces a limitation.
- Expert cannot create a new URL.

### Judge

- Unsupported findings are rejected.
- Disagreement is preserved.
- Partial expert set is accepted.
- No expert result produces a controlled failure.

### Scoring

- Boundary tests.
- Clamping tests.
- Confidence penalty tests.
- Deterministic repeated output.

## 3. Contract tests

Validate:

- Request JSON matches schema.
- Response JSON matches schema.
- `status=partial` includes warnings.
- Evidence item required fields exist.
- Score types are numeric.
- Enums use allowed values.

## 4. Integration tests

### Live-provider integration

Run only when keys exist:

- One short suspicious input.
- Search returns normalized evidence.
- LLM structured output parses.
- Complete response returned.

### Mock integration

Must always run:

- Fixed input.
- Fixed fixtures.
- Stable final score range.
- Stable evidence IDs.
- No network required.

## 5. Failure injection tests

Simulate:

- Search timeout.
- Search returns zero results.
- LLM invalid JSON.
- One expert timeout.
- All experts timeout.
- Report generation failure.
- Backend `500`.
- Frontend network disconnect.

Expected outcome:

- UI does not crash.
- Status is accurate.
- Confidence is reduced.
- User sees what data is missing.
- No fake evidence is shown.

## 6. Manual demo checklist

Run each case twice.

| Case | Expected |
|---|---|
| OTP phishing | Critical/high risk |
| Recruitment fee | High/suspicious |
| Fake authority payment | High risk |
| Benign school reminder | Low risk |
| Ambiguous marketplace message | Uncertain |

Check:

- Fast warning renders.
- Loading state appears.
- Report renders.
- Evidence opens.
- Copy report works.
- Reset works.
- Console has no red error.
- Mobile width is readable.
- Mock badge appears when enabled.

## 7. Pre-demo smoke commands

```powershell
# Backend
cd backend
python -m pytest -q
python -m ruff check .

# Frontend
cd ..\frontend
npm run lint
npm run build

# Integration
cd ..
python scripts\smoke_test.py
```

Save the output in a text file before the presentation.
