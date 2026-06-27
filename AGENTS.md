# AGENTS.md — VYVY Repository Instructions

Tài liệu này là quy tắc bắt buộc cho mọi coding agent.

## Mission

Build a reliable one-day hackathon MVP for **VYVY — AI Investigation & Verification Engine**.

The product accepts **text only** and returns an explainable scam-risk investigation report. Preserve the locked MVP scope.

## Required work loop

For every task, follow exactly:

1. READ
2. ANALYZE
3. PLAN
4. IMPLEMENT
5. VALIDATE
6. REPORT

Do not skip validation.

## Before modifying code

Read:

1. This `AGENTS.md`
2. `specs/active/mvp/requirements.md`
3. `specs/active/mvp/design.md`
4. The exact task in `specs/active/mvp/tasks.md`
5. Existing related tests and contracts

Then state:

- What you will change
- What you will not change
- Files you expect to touch
- Validation commands

## Scope rules

The MVP is text-only.

Do not add:

- OCR
- Image processing
- File upload
- PDF parsing
- Browser extension
- Authentication
- Database
- Admin dashboard
- Schedulers
- Continuous learning
- Unrequested dependencies
- Unrelated refactors

A URL may appear inside pasted text, but the UI remains one text input. External search must go through the evidence adapter.

## Code-change rules

- Implement exactly one approved task.
- Modify only files listed in the task's `Files Allowed`.
- Do not rename public contracts without approval.
- Do not change unrelated formatting.
- Do not refactor working code during feature implementation.
- Do not add dependencies unless the task explicitly allows it.
- Keep provider-specific code behind adapters.
- Keep mock data behind `MOCK_MODE`.
- Never silently fall back to fabricated evidence.
- Never claim that a person or organization is definitively criminal.
- Use wording such as “nguy cơ”, “dấu hiệu”, “chưa đủ bằng chứng”.

## Data integrity rules

Every evidence item must have:

- `title`
- `url`
- `source_name`
- `published_at` when available
- `snippet`
- `retrieved_at`
- `credibility_score`
- `relevance_score`

Expert agents may reference only evidence IDs that exist in the evidence collection result.

If search fails:

- Return an explicit error/status field.
- Continue with text-only analysis.
- Lower confidence.
- Do not generate fake URLs, article titles or quotations.

## Structured output rules

All LLM nodes must return data validated by Pydantic models.

On invalid JSON:

1. Retry once with a repair instruction.
2. If still invalid, return a typed fallback result.
3. Log the error without exposing secrets.

## Performance rules

- Run independent experts concurrently.
- Limit external queries and results.
- Use timeouts for every external request.
- Avoid repeated LLM calls for the same data.
- Keep fast check independent from full investigation.
- The frontend must call Fast Check first, then Full Investigation.

## Security rules

- Never commit `.env`.
- Never log API keys.
- Validate input length.
- Escape rendered user content.
- Restrict CORS to configured origins.
- Use HTTP timeouts.
- Do not execute user-provided code.
- Do not follow arbitrary redirect chains without limits.

## Required validation

Backend:

```powershell
python -m pytest -q
python -m ruff check .
```

Frontend:

```powershell
npm run lint
npm run build
```

Integration:

```powershell
python scripts/smoke_test.py
```

If a command is unavailable, report that clearly. Do not claim it passed.

## Completion report format

At the end of each task, report:

1. Task completed
2. Files changed
3. Key implementation decisions
4. Commands run
5. Exact test results
6. Remaining risks
7. Suggested next task ID

Do not start the next task automatically.
