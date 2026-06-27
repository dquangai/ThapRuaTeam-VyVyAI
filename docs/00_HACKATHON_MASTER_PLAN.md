# 00 — Hackathon Master Plan

## 1. North Star

VYVY must demonstrate one clear moment of value:

> A user pastes suspicious text and receives an immediate warning, a transparent investigation trail, a calibrated risk score and practical safety actions.

The judges should understand the product in less than 30 seconds and see the complete flow in less than 4 minutes.

## 2. Build strategy

Use a vertical-slice approach:

1. Make the smallest end-to-end path work.
2. Add intelligence to each stage.
3. Add external evidence.
4. Add polish only after the core path is stable.
5. Freeze features before the final rehearsal.

Do not build all backend modules first and leave integration to the end.

## 3. Time-boxed schedule

The schedule is expressed as time from kickoff so it works with any event start time.

| Time | Goal | Exit condition |
|---|---|---|
| T-1 day, 90 min | Preflight | Keys tested, repository ready, dependencies cached |
| T+0:00–0:30 | Scope lock and role assignment | Everyone can explain the same MVP |
| T+0:30–1:30 | Repository, contracts, UI shell | Health endpoint and page shell run |
| T+1:30–2:30 | Fast Check vertical slice | Suspicious text produces immediate warning |
| T+2:30–3:45 | Intake + classifier | Structured context is stable |
| T+3:45–5:15 | Evidence adapter + fixtures | Real and mock modes both work |
| T+5:15–6:30 | Four parallel experts | Expert outputs validate against schema |
| T+6:30–7:15 | Behavioral analysis | Red flags and severity appear |
| T+7:15–8:30 | Judge + scoring + safety | Full backend response is complete |
| T+8:30–9:45 | Frontend integration | End-to-end demo works from browser |
| T+9:45–10:45 | Tests and failure paths | Search/LLM failures do not crash demo |
| T+10:45–11:30 | Visual polish + demo fixtures | UI is presentation-ready |
| T+11:30–12:00 | Feature freeze | No new features |
| T+12:00 onward | Rehearsal, backup, pitch | Two clean demo runs and backup video |

## 4. Definition of vertical slice

The first slice should include:

- One text input.
- One Fast Check endpoint.
- One Full Investigation endpoint.
- One simplified expert.
- One basic score.
- One report card.

Once it works, replace the simplified expert with parallel experts and richer scoring. This prevents the team from spending half the day on disconnected modules.

## 5. Team role matrix

### Role A — Product and AI orchestration

- Owns scope.
- Owns prompts and schemas.
- Owns Judge logic.
- Approves user-facing wording.
- Prevents scope creep.

### Role B — Backend and evidence

- Owns FastAPI.
- Owns adapters and external APIs.
- Owns timeouts, retries and mock mode.
- Owns backend tests.

### Role C — Frontend and UX

- Owns input page.
- Owns progress states.
- Owns report visualization.
- Owns error and empty states.

### Role D — QA, integration and pitch

- Maintains demo cases.
- Runs smoke tests.
- Tracks bugs.
- Records fallback video.
- Owns pitch timing.

For a three-person team, merge Role D into Role A. For a two-person team, one person owns backend/AI and one owns frontend/demo.

## 6. Integration rhythm

Every 60–90 minutes:

1. Pull latest `dev`.
2. Run backend tests.
3. Run frontend build.
4. Run one demo case.
5. Tag a known-good commit.
6. Record blockers.

Suggested branch model:

- `main`: known-good demo only.
- `dev`: integration.
- `feat/Txx-short-name`: one task.
- `fix/Txx-short-name`: one bug.

Commit format:

```text
feat(T05): add structured intake agent
fix(T11): handle search timeout without crashing report
test(T08): add judge score boundary tests
```

## 7. Feature freeze rules

After T+11:30:

Allowed:

- Fix crashes.
- Fix wrong data mapping.
- Improve demo text.
- Improve loading state.
- Add missing validation.
- Record backup video.

Not allowed:

- New input types.
- New agents.
- New database.
- New framework.
- Large UI redesign.
- Provider migration.
- Architecture refactor.

## 8. Final success checklist

- Product story is understandable.
- Fast warning appears first.
- Full report cites evidence.
- Safe example does not receive a high-risk result.
- Missing search data is clearly disclosed.
- Mock mode can reproduce a stable demo.
- The same demo works twice in a row.
- Backup assets are stored locally.
