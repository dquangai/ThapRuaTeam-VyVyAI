# Design — VYVY Text Investigation MVP

## API design

- `GET /health`
- `POST /api/v1/fast-check`
- `POST /api/v1/investigate`

## Orchestration design

1. Validate input.
2. Intake.
3. Classification.
4. Evidence Search and Behavioral Analysis in parallel.
5. Four Experts in parallel.
6. Judge.
7. Deterministic Score.
8. Safety Advice.
9. Report.

Fast Check is a separate path called first by the frontend.

## State ownership

- Nodes only write their own state fields.
- Scoring reads approved Judge output and normalized components.
- Report formatting cannot change scores.
- Frontend reads the API contract without inferring missing values.

## Adapter design

Interfaces:

```python
class LLMProvider(Protocol):
    async def structured(self, prompt: str, schema: type[T]) -> T: ...

class SearchProvider(Protocol):
    async def search(self, query: str, limit: int) -> list[RawSearchResult]: ...
```

Implementations:

- Live provider.
- Fake provider for tests.
- Mock fixture provider for demo.

## Error design

Every provider error becomes a typed warning. The graph decides whether to continue. Required core stages failing may return `failed`; optional stages produce `partial`.

## Security design

- Environment variables.
- Input length limits.
- No persistence.
- CORS allowlist.
- Network timeouts.
- No arbitrary code execution.
- No secrets in logs.

## Testing design

- Fake providers for unit tests.
- Mock Mode for integration.
- Live-provider test optional.
- Contract validation required.
