# 11 — Team Operating System

## 1. Communication rule

Use short status messages:

```text
TASK: T05
STATUS: working / blocked / ready for review
FILES: ...
BLOCKER: ...
ETA: ...
```

Avoid long unstructured chat during the build.

## 2. Task ownership

Each task has one owner. Other members may review, but should not edit the same files simultaneously.

Suggested ownership:

| Area | Owner |
|---|---|
| Product/spec/prompts | AI lead |
| Backend/API | Backend lead |
| Search/evidence | Backend or AI lead |
| Frontend | Frontend lead |
| QA/demo | QA/pitch lead |

## 3. Definition of Ready

A task is ready when:

- Acceptance criteria are written.
- Files allowed are listed.
- Dependencies are complete.
- Input/output contract is known.
- Validation command is known.

## 4. Definition of Done

A task is done when:

- Acceptance criteria pass.
- Tests run.
- No unrelated files changed.
- No secret committed.
- Commit created.
- Another teammate can run it.
- Integration owner has accepted it.

## 5. Bug priority

### P0

- Demo cannot start.
- API returns no report.
- App crashes.
- Secret exposed.
- Evidence is fabricated.

### P1

- One major section missing.
- Incorrect score mapping.
- Search failure crashes UI.
- Demo case result is clearly wrong.

### P2

- Layout issue.
- Minor wording issue.
- Noncritical animation issue.
- Extra polish.

Fix P0, then P1. Ignore P2 near freeze.

## 6. Review protocol

Reviewer checks:

1. Does it meet the task?
2. Did it stay in scope?
3. Are contracts preserved?
4. Are tests honest?
5. Are sources grounded?
6. Is failure handled?
7. Is the diff small enough to understand?

## 7. Codex parallelism

Safe parallel tasks:

- Backend models/contracts.
- Frontend static layout.
- Demo fixtures.
- Documentation.
- Unit tests for stable modules.

Unsafe parallel tasks:

- Two agents editing graph state.
- Two agents editing the same API response model.
- UI integration before contract freeze.
- Judge and scoring changing the same schema independently.
