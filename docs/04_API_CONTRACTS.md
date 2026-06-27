# 04 — API and Data Contracts

## 1. Health

### Request

```http
GET /health
```

### Response

```json
{
  "service": "vyvy-backend",
  "status": "ok",
  "version": "0.1.0",
  "mock_mode": false
}
```

## 2. Fast Check

### Request

```http
POST /api/v1/fast-check
Content-Type: application/json
```

```json
{
  "text": "Tài khoản của bạn sẽ bị khóa. Hãy cung cấp OTP...",
  "locale": "vi"
}
```

### Response

```json
{
  "request_id": "uuid",
  "risk_band": "critical",
  "score": 95,
  "triggered_flags": [
    {
      "code": "OTP_REQUEST",
      "label": "Yêu cầu cung cấp OTP",
      "severity": "critical",
      "evidence_span": "cung cấp OTP"
    }
  ],
  "message": "Nội dung có dấu hiệu chiếm đoạt tài khoản.",
  "immediate_actions": [
    "Không cung cấp OTP hoặc mật khẩu.",
    "Không bấm vào đường dẫn trong tin nhắn.",
    "Liên hệ đơn vị qua kênh chính thức."
  ],
  "latency_ms": 120
}
```

## 3. Full Investigation

### Request

```http
POST /api/v1/investigate
Content-Type: application/json
```

```json
{
  "text": "string",
  "locale": "vi",
  "use_web_search": true
}
```

### Response top-level fields

```json
{
  "investigation_id": "uuid",
  "status": "completed|partial|failed",
  "input": {},
  "intake": {},
  "classification": {},
  "evidence_status": {},
  "evidence": [],
  "experts": [],
  "behavioral_analysis": {},
  "judge": {},
  "verification": {},
  "safety_advice": {},
  "report": {},
  "warnings": [],
  "timings_ms": {}
}
```

## 4. Error contract

```json
{
  "error": {
    "code": "INPUT_TOO_LONG",
    "message": "Nội dung vượt quá giới hạn cho phép.",
    "details": {
      "max_characters": 12000
    },
    "request_id": "uuid"
  }
}
```

## 5. Status semantics

- `completed`: all required stages succeeded.
- `partial`: report exists, but one or more providers failed.
- `failed`: no usable report could be produced.

## 6. Evidence status

```json
{
  "provider": "tavily|custom|mock|none",
  "mode": "live|mock|disabled",
  "success": true,
  "queries_attempted": 3,
  "results_returned": 7,
  "errors": []
}
```

## 7. Frontend rendering rule

The frontend must not assume all nested fields exist. It must render:

- Full section when data exists.
- Partial section with warning when data is missing.
- Error card when investigation fails.
- Mock badge when `mode=mock`.
