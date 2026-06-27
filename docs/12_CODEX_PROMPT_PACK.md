# 12 — Copy/Paste Codex Prompt Pack

Use one prompt at a time. Replace placeholders only where necessary.

---

## Prompt 0 — Repository audit before coding

```text
Read AGENTS.md and every file under specs/active/mvp.

Do not modify code yet.

Audit the repository against the active MVP specification. Return:
1. Current repository tree.
2. Existing components that can be reused.
3. Missing components.
4. Contract conflicts.
5. Highest-risk integration points.
6. Proposed implementation order mapped to task IDs.
7. Exact files expected to change for the first task.

Do not propose OCR, image upload, PDF parsing, authentication, database, admin pages, browser extensions or unrelated refactors. The MVP is text-only.
```

---

## Prompt 1 — Bootstrap repository

```text
Read AGENTS.md and specs/active/mvp/tasks.md.

Execute only task T01: bootstrap the repository.

Create the approved backend/frontend folder structure, health endpoint, minimal Vite page, environment configuration and test commands.

Constraints:
- Text-only MVP.
- No database.
- No authentication.
- No OCR or file upload.
- Do not implement agents yet.
- Do not add dependencies not listed by T01.
- Modify only files allowed by T01.

Validate with the commands listed in T01. At the end report files changed, exact command results, remaining risks and next recommended task.
```

---

## Prompt 2 — Freeze contracts

```text
Read AGENTS.md, requirements.md, design.md and task T02.

Execute only T02.

Implement Pydantic request/response models that match contracts/investigation_request.schema.json and investigation_response.schema.json. Mirror the stable response types in frontend/src/types.

Requirements:
- Optional fields must support partial results.
- Evidence IDs and expert citations must be explicit.
- Risk score and confidence score are separate.
- Enums must be strict.
- Add contract tests.
- Do not implement LLM calls or UI.

Run backend tests and frontend type check/build. Report any schema ambiguity instead of guessing.
```

---

## Prompt 3 — Fast Check

```text
Read AGENTS.md and task T03.

Implement only the deterministic Fast Check module and POST /api/v1/fast-check.

Required signals:
- OTP/password/PIN request
- urgent money transfer
- account lock or arrest threat
- remote-control app request
- suspicious/shortened link
- recruitment/prize upfront fee
- guaranteed investment return
- secrecy request

Requirements:
- Vietnamese evidence spans.
- Deduplicate flags.
- Clamp score 0–100.
- Return clear immediate actions.
- No external API.
- Add unit and API tests.
- Do not modify full investigation flow.

Run all validation commands required by T03.
```

---

## Prompt 4 — Intake and classifier

```text
Read AGENTS.md and task T04.

Implement only Intake Agent and Scam Pattern Classifier with structured outputs.

Requirements:
- Extract only text-present entities.
- Produce no more than five concise claims.
- Produce no more than three focused search queries.
- Preserve uncertainty.
- Retry invalid structured output once.
- Provide a typed fallback.
- Add tests using a fake LLM provider.
- No real search integration.
- No final scoring.
- No frontend changes.

Report prompt contracts and exact test results.
```

---

## Prompt 5 — Evidence adapter

```text
Read AGENTS.md and task T05.

Implement only the evidence search adapter, normalization, source scoring and Mock Mode fixtures.

Requirements:
- Maximum three queries.
- Configurable timeout.
- Maximum eight normalized results.
- Every item has stable evidence_id.
- Never invent title, URL, date or source.
- Live, mock, disabled and failed modes are explicit.
- Search failure returns partial status.
- Add unit tests and one mock integration test.
- Do not implement experts.

Use provider interfaces so the concrete search service can be changed later.
```

---

## Prompt 6 — Parallel expert agents

```text
Read AGENTS.md and task T06.

Implement only Financial, Legal Risk, Cyber and OSINT expert agents.

Requirements:
- One shared typed ExpertAssessment schema.
- Agents run concurrently.
- Every finding references valid evidence IDs or explicitly says it is based on input text.
- Agents cannot add URLs.
- Each agent returns score, verdict, reasons, cited evidence IDs, missing information and confidence.
- One agent failure must not fail the whole group.
- Add tests with fake providers.
- Do not implement Judge, final score or frontend.

Report measured concurrency behavior in the test environment.
```

---

## Prompt 7 — Behavioral analysis

```text
Read AGENTS.md and task T07.

Implement only Behavioral Analyst.

Detect:
- urgency
- fear
- authority pressure
- FOMO
- scarcity
- secrecy
- isolation
- social proof manipulation
- reciprocity
- gradual commitment

Return typed red flags with severity, evidence span and explanation, plus a 0–100 behavioral risk score.

Add tests for suspicious and benign Vietnamese messages. Do not change expert or Judge code.
```

---

## Prompt 8 — Judge and scoring

```text
Read AGENTS.md, docs/05_SCORING_MODEL.md and task T08.

Implement only Judge Agent and deterministic verification/confidence scoring.

Judge must:
- validate evidence references
- reject unsupported findings
- preserve disagreements
- list missing evidence
- produce supported findings

Scoring must be calculated in code, not by the report generator.

Add boundary, failure and partial-result tests. Do not implement UI or new providers.
```

---

## Prompt 9 — Safety and report

```text
Read AGENTS.md and task T09.

Implement only Safety Advisor and Report Generator.

Requirements:
- Practical Vietnamese recommendations.
- No definitive accusation.
- No legal advice.
- Report generator cannot modify numeric scores.
- Include conclusion, why, evidence, expert consensus, behavioral red flags, actions and limitations.
- Support Markdown output.
- Add tests for completed and partial investigations.

Do not add PDF generation.
```

---

## Prompt 10 — LangGraph orchestration

```text
Read AGENTS.md, design.md and task T10.

Wire existing completed nodes into the LangGraph full-investigation flow.

Requirements:
- Preserve typed state.
- Run evidence search and behavioral analysis concurrently where practical.
- Run four experts concurrently.
- Judge waits for available expert results.
- Continue with partial status when one optional stage fails.
- Record stage timings.
- Add an end-to-end mock-mode integration test.
- Do not change node behavior unless required for integration; report any required contract change before making it.
```

---

## Prompt 11 — Full API endpoint

```text
Read AGENTS.md and task T11.

Implement only POST /api/v1/investigate using the completed graph.

Requirements:
- Input validation.
- Request ID.
- Status completed/partial/failed.
- Global exception handling.
- CORS from environment.
- No raw exception leak.
- Response matches contract.
- Add API tests with Mock Mode.
- Do not change frontend.
```

---

## Prompt 12 — Frontend shell

```text
Read AGENTS.md, docs/06_UI_UX_DEMO.md and task T12.

Implement only the static frontend shell using typed mock data.

Required sections:
- header
- text input
- example selector
- Fast Warning
- progress stages
- conclusion
- expert consensus
- evidence
- behavioral red flags
- recommendations
- limitations

Requirements:
- Responsive.
- Accessible labels.
- Empty/loading/partial/error/mock states.
- No real API calls yet.
- No new UI framework unless task T12 explicitly permits it.
- Run lint and build.
```

---

## Prompt 13 — Frontend integration

```text
Read AGENTS.md and task T13.

Integrate the frontend with:
1. POST /api/v1/fast-check
2. POST /api/v1/investigate

Flow:
- validate text
- show fast warning first
- start full investigation
- show progress
- render completed or partial report
- handle timeout/network/backend errors
- support reset and copy Markdown

Do not change backend contracts. If a mismatch exists, stop and report it.
Run frontend build and the repository smoke test.
```

---

## Prompt 14 — Demo fixtures

```text
Read AGENTS.md, samples/demo_cases.md and task T14.

Implement only stable demo fixtures and the example selector.

Requirements:
- Four suspicious/uncertain cases and one benign case.
- Synthetic data only.
- Expected risk band documented.
- Mock evidence clearly labeled.
- Demo result is deterministic.
- No hard-coded fake live sources.
- Add a test proving Mock Mode performs no network call.
```

---

## Prompt 15 — Final quality review

```text
Act as a senior reviewer. Read AGENTS.md and the active MVP spec.

Do not add features.

Review the entire diff for:
- scope violations
- contract mismatch
- evidence hallucination risk
- unsafe wording
- missing timeouts
- missing error states
- secrets
- dead code
- untested deterministic scoring
- frontend crashes on partial data
- deployment blockers

Run all available validation commands.

Fix only P0 and P1 issues. Do not perform broad refactors or visual redesign. Return a table of findings, fixes, test results and residual risks.
```

---

## Prompt 16 — Emergency bug fix

```text
Read AGENTS.md.

Bug:
<PASTE EXACT ERROR>

Reproduction:
<PASTE COMMANDS/STEPS>

Expected:
<EXPECTED BEHAVIOR>

Actual:
<ACTUAL BEHAVIOR>

Investigate before editing. Identify the smallest root-cause fix. Modify only files directly related to the bug. Do not refactor. Add or update one regression test. Run the narrow test first, then required project validations. Report exact results.
```

---

## Prompt 17 — Deployment readiness

```text
Read AGENTS.md.

Do not add product features.

Prepare deployment readiness:
- verify environment variables
- verify production build commands
- verify CORS
- verify health endpoint
- verify no secrets are committed
- verify Mock Mode default is safe
- verify frontend API base URL configuration
- verify error logging
- verify README setup steps

Make only minimal deployment fixes. Run production builds and report exact output.
```
