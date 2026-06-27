# Tasks — VYVY One-Day MVP

Each task should be one Codex assignment.

## T01 — Bootstrap

**Estimate:** 45 min  
**Depends on:** none

**Files Allowed**

- Root config files
- `backend/`
- `frontend/`
- `.env.example`

**Acceptance**

- Backend health endpoint works.
- Frontend page works.
- Test/lint/build commands exist.
- No product logic yet.

## T02 — Contracts

**Estimate:** 45 min  
**Depends on:** T01

**Files Allowed**

- `contracts/`
- `backend/app/models/`
- `frontend/src/types/`
- Contract tests

**Acceptance**

- Request/response schemas compile.
- Backend and frontend types align.
- Partial response supported.

## T03 — Fast Check

**Estimate:** 60 min  
**Depends on:** T02

**Files Allowed**

- Fast Check module
- Fast Check route
- Related tests

**Acceptance**

- Required red flags detected.
- No external API.
- Benign message avoids high risk.
- API contract passes.

## T04 — Intake and Classifier

**Estimate:** 75 min  
**Depends on:** T02

**Files Allowed**

- Intake/classifier nodes
- Prompts
- Fake provider tests

**Acceptance**

- Structured output.
- Typed fallback.
- Claims and entities are grounded in input.

## T05 — Evidence Adapter

**Estimate:** 75 min  
**Depends on:** T02, T04

**Files Allowed**

- Search provider
- Source scorer
- Mock fixtures
- Tests

**Acceptance**

- Live/mock/failed modes.
- No invented fields.
- Stable evidence IDs.
- Timeouts.

## T06 — Expert Agents

**Estimate:** 90 min  
**Depends on:** T02, T05

**Files Allowed**

- Expert nodes/prompts
- Expert tests

**Acceptance**

- Four typed agents.
- Concurrent execution.
- Valid evidence references.
- Partial failure supported.

## T07 — Behavioral Analyst

**Estimate:** 45 min  
**Depends on:** T02

**Files Allowed**

- Behavioral node/prompt
- Tests

**Acceptance**

- Red flags include spans.
- Risk score is valid.
- Benign and suspicious tests.

## T08 — Judge and Scoring

**Estimate:** 75 min  
**Depends on:** T06, T07

**Files Allowed**

- Judge
- Scoring
- Tests

**Acceptance**

- Unsupported findings rejected.
- Risk and confidence deterministic.
- Boundary tests pass.

## T09 — Safety and Report

**Estimate:** 60 min  
**Depends on:** T08

**Files Allowed**

- Safety node
- Report node
- Markdown formatter
- Tests

**Acceptance**

- Safe actions.
- No definitive accusation.
- Report preserves scores.
- Partial report supported.

## T10 — Graph Orchestration

**Estimate:** 60 min  
**Depends on:** T04–T09

**Files Allowed**

- Graph builder
- State integration
- Integration tests

**Acceptance**

- Correct execution order.
- Concurrency.
- Timings.
- Mock end-to-end passes.

## T11 — Full API

**Estimate:** 45 min  
**Depends on:** T10

**Files Allowed**

- Investigation route
- Error handling
- API tests

**Acceptance**

- Contract-compliant endpoint.
- Completed/partial/failed statuses.
- No raw exceptions.

## T12 — Frontend Shell

**Estimate:** 90 min  
**Depends on:** T02

**Files Allowed**

- Frontend components/styles/data

**Acceptance**

- All required sections.
- All states with typed mock data.
- Responsive and accessible.
- Build passes.

## T13 — Frontend Integration

**Estimate:** 60 min  
**Depends on:** T03, T11, T12

**Files Allowed**

- Frontend API client
- Page state
- Integration tests

**Acceptance**

- Fast Check shown first.
- Full result rendered.
- Partial/error handled.
- Copy/reset work.

## T14 — Demo Fixtures

**Estimate:** 30 min  
**Depends on:** T05, T12

**Files Allowed**

- `samples/`
- Mock fixtures
- Example selector
- Tests

**Acceptance**

- Five stable cases.
- No network in Mock Mode.
- Expected bands documented.

## T15 — Quality Gate

**Estimate:** 60 min  
**Depends on:** all required tasks

**Files Allowed**

- Only files required for P0/P1 fixes

**Acceptance**

- Tests pass.
- Frontend build passes.
- Smoke test passes.
- No secrets.
- Two successful demo runs.
