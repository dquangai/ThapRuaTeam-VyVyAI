# VYVY — Vietnam's AI Investigator Against Digital Scams

VYVY là một MVP điều tra rủi ro lừa đảo số dành cho nội dung văn bản tiếng Việt. Người dùng dán một đoạn chat, email, quảng cáo, lời mời đầu tư hoặc tin nhắn đáng nghi; hệ thống trả về cảnh báo nhanh, bằng chứng tìm kiếm, đánh giá chuyên gia, điểm rủi ro, độ tin cậy và khuyến nghị hành động an toàn.

> MVP hiện chỉ nhận văn bản. Không hỗ trợ OCR, ảnh, PDF, upload file, đăng nhập, cơ sở dữ liệu, browser extension hoặc admin dashboard.

## Mục tiêu sản phẩm

VYVY giúp người dùng tự kiểm tra một nội dung đáng nghi theo luồng:

1. Gửi văn bản cần điều tra.
2. Chạy Fast Check để phát hiện dấu hiệu rủi ro tức thì.
3. Trích xuất nội dung, thực thể, claim và truy vấn tìm kiếm.
4. Tìm kiếm bằng chứng qua adapter.
5. Chạy bốn expert song song: Financial, Legal Risk, Cyber, OSINT.
6. Phân tích kỹ thuật thao túng hành vi.
7. Judge Agent kiểm tra lập luận và bằng chứng.
8. Tính risk score và confidence score bằng logic deterministic.
9. Sinh báo cáo tiếng Việt có kết luận, lý do, bằng chứng, khuyến nghị và giới hạn.

VYVY không kết luận chắc chắn ai là tội phạm. Báo cáo dùng các cụm như “nguy cơ”, “dấu hiệu”, “chưa đủ bằng chứng” và khuyến nghị người dùng xác minh qua kênh chính thức.

## Tính năng chính

- Text-only investigation: một ô nhập văn bản, giới hạn 10–12.000 ký tự.
- Fast Check deterministic: phát hiện OTP/mật khẩu/PIN, chuyển tiền gấp, đe dọa khóa tài khoản/bắt giữ, link đáng nghi, phí trước, lợi nhuận cam kết, yêu cầu giữ bí mật.
- Full Investigation: intake, classifier, evidence search, behavioral analysis, experts, judge, scoring, safety advice và report.
- Mock Mode: demo offline, deterministic, không gọi API ngoài.
- Live Mode: dùng OpenAI cho các node LLM-backed và Tavily cho evidence search khi được cấu hình.
- Optional VirusTotal enrichment: tra cứu reputation domain khi bật cấu hình, không upload file và không scan chủ động.
- Frontend chatbot-style: gửi nội dung như một phiên điều tra, hiển thị fast warning, progress, report, evidence và khuyến nghị.
- Markdown report: có thể copy báo cáo để chia sẻ.

## Công nghệ sử dụng

### Backend

- Python 3.12+
- FastAPI
- Uvicorn
- Pydantic và Pydantic Settings
- OpenAI Python SDK
- httpx
- pytest
- Ruff
- Provider adapter pattern cho LLM, search và enrichment
- JSON Schema contracts trong `contracts/`

### Frontend

- React 19
- TypeScript
- Vite 7
- ESLint
- CSS thuần, responsive, không dùng UI framework ngoài

### External providers

- OpenAI: LLM-backed intake/classifier/experts/judge/report khi Live Mode.
- Tavily: evidence search khi `ENABLE_WEB_SEARCH=true`.
- VirusTotal: optional domain reputation lookup khi `ENABLE_VIRUSTOTAL=true`.

## Cấu trúc repository

```text
.
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes: health, fast-check, investigate
│   │   ├── core/             # typed settings and env loading
│   │   ├── evidence/         # search adapter, normalization, source scoring
│   │   ├── graph/            # full investigation orchestration
│   │   ├── models/           # Pydantic request/response models
│   │   ├── nodes/            # intake, classifier, experts, judge, safety
│   │   ├── prompts/          # structured prompt contracts
│   │   ├── reporting/        # safety advisor and report generator
│   │   ├── scoring/          # deterministic verification/risk/confidence scoring
│   │   └── services/         # OpenAI, Tavily, VirusTotal, provider factory
│   ├── scripts/
│   │   └── live_provider_smoke.py
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── api/              # frontend API client
│   │   ├── components/       # chatbot investigation panel
│   │   ├── data/             # deterministic demo fixtures
│   │   ├── types/            # TypeScript API contracts
│   │   ├── App.tsx
│   │   └── styles.css
│   ├── package.json
│   └── vite.config.ts
├── contracts/                # JSON Schema request/response contracts
├── docs/                     # scope, architecture, scoring, demo notes
├── samples/                  # demo cases and expected report examples
├── specs/active/mvp/         # locked MVP requirements/design/tasks
├── scripts/
│   └── smoke_test.py
├── .env.example
└── README.md
```

## Yêu cầu môi trường

- Windows PowerShell, macOS terminal hoặc Linux shell.
- Python 3.12 hoặc mới hơn.
- Node.js tương thích Vite 7.
- npm.
- Git.

Khuyến nghị trên Windows:

```powershell
py --version
node --version
npm --version
```

## Cấu hình môi trường

Không commit `.env`. Repository đã ignore `.env`, `.env.*`, `backend/.env`, `frontend/.env`.

File mẫu nằm tại:

```text
.env.example
```

Backend đọc env từ:

```text
backend/.env
```

Frontend đọc env từ:

```text
frontend/.env
```

### Mock Mode — chạy demo offline

Mock Mode phù hợp để demo nhanh, chạy test, hoặc làm việc khi chưa có API key.

Tạo file backend env:

```powershell
Copy-Item .env.example backend\.env
```

Trong `backend/.env`, giữ hoặc đặt:

```env
MOCK_MODE=true
ENABLE_WEB_SEARCH=true
ENABLE_VIRUSTOTAL=false
CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Tạo file frontend env:

```powershell
Set-Content -Path frontend\.env -Value "VITE_API_BASE_URL=http://127.0.0.1:8000"
```

Mock Mode không cần `OPENAI_API_KEY`, `TAVILY_API_KEY` hoặc `VIRUSTOTAL_API_KEY`.

### Live Mode — dùng provider thật

Chỉ bật Live Mode khi đã có API key trong `backend/.env`. Không paste key vào README, terminal log, issue hoặc commit.

Trong `backend/.env`, cấu hình:

```env
MOCK_MODE=false
ENABLE_WEB_SEARCH=true
ENABLE_VIRUSTOTAL=false

OPENAI_API_KEY=
OPENAI_MODEL_FAST=gpt-5.4-mini
OPENAI_MODEL_EXPERT=gpt-5.4-mini
OPENAI_MODEL_JUDGE=gpt-5.5
OPENAI_MODEL_REPORT=gpt-5.5

TAVILY_API_KEY=
VIRUSTOTAL_API_KEY=
CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Model routing:

| Role | Env variable | Dùng cho |
| --- | --- | --- |
| FAST | `OPENAI_MODEL_FAST` | Intake, classifier, behavioral, query planning, repair retry |
| EXPERT | `OPENAI_MODEL_EXPERT` | Financial, Legal Risk, Cyber, OSINT experts |
| JUDGE | `OPENAI_MODEL_JUDGE` | Judge, disagreement analysis, consensus |
| REPORT | `OPENAI_MODEL_REPORT` | Safety advisor và report generation |

Không dùng biến deprecated `OPENAI_MODEL`.

## Cài đặt backend

Từ repository root:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Chạy backend:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Kiểm tra health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health | ConvertTo-Json -Depth 8
```

Kết quả mong đợi:

```json
{
  "service": "vyvy-backend",
  "status": "ok",
  "version": "0.1.0"
}
```

Health endpoint không gọi API trả phí và không trả secret.

## Cài đặt frontend

Mở terminal mới từ repository root:

```powershell
cd frontend
npm install
npm run dev
```

Mở trình duyệt:

```text
http://127.0.0.1:5173
```

Nếu frontend báo lỗi CORS, kiểm tra `backend/.env`:

```env
CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Sau đó restart backend.

## Chạy toàn bộ ứng dụng

Terminal 1 — backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2 — frontend:

```powershell
cd frontend
npm run dev
```

Truy cập:

```text
http://127.0.0.1:5173
```

Luồng frontend:

```text
User submits text
-> POST /api/v1/fast-check
-> show fast warning
-> POST /api/v1/investigate
-> show progress
-> render completed or partial report
```

## API endpoints

### Health

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

### Fast Check

```powershell
$body = @{
  text = "Tài khoản của bạn sắp bị khóa. Vui lòng gửi mã OTP trong 10 phút để xác minh."
  locale = "vi"
  use_web_search = $true
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/fast-check `
  -ContentType "application/json" `
  -Body $body
```

### Full Investigation

```powershell
$body = @{
  text = "Tài khoản của bạn sắp bị khóa. Vui lòng gửi mã OTP trong 10 phút để xác minh."
  locale = "vi"
  use_web_search = $true
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/investigate `
  -ContentType "application/json" `
  -Body $body | ConvertTo-Json -Depth 10
```

## Câu hỏi mẫu để demo

Bạn có thể copy từng nội dung dưới đây vào ô chat của VYVY.

### 1. Tuyển dụng online yêu cầu chuyển tiền trước

```text
Em được một người trên Telegram mời làm việc online.
Công việc là like video TikTok và chụp màn hình gửi lại.
Ngày đầu em kiếm được 300.000 đồng.
Sau đó họ bảo muốn nhận nhiệm vụ VIP thì phải chuyển trước 2 triệu để kích hoạt tài khoản.
Họ nói sẽ hoàn lại tiền sau 15 phút.
```

### 2. Đầu tư coin cam kết lợi nhuận

```text
Một người bạn giới thiệu em đầu tư vào dự án coin mới.
Họ cam kết lợi nhuận 3% mỗi ngày.
Nếu giới thiệu thêm người tham gia em sẽ được hoa hồng.
Hiện đã có hơn 5.000 người tham gia.
```

### 3. Quen qua Facebook, gửi quà và yêu cầu đóng thuế

```text
Em quen một người nước ngoài trên Facebook được 2 tuần.
Người đó nói yêu em và muốn gửi quà về Việt Nam.
Sau đó có người tự nhận là nhân viên hải quan gọi điện bảo em đóng 15 triệu tiền thuế để nhận quà.
```

### 4. Fanpage bán iPhone giá rẻ, yêu cầu chuyển khoản trước

```text
Em thấy một fanpage bán iPhone 16 Pro Max giá 12 triệu.
Shop yêu cầu chuyển khoản trước toàn bộ.
Họ nói vì giá khuyến mãi nên không hỗ trợ COD.
```

### 5. Đầu tư hiển thị lãi lớn nhưng yêu cầu nộp phí để rút

```text
Chị gái em được một người trên Zalo giới thiệu đầu tư.
Bỏ vào 50 triệu.
Sau 2 tuần tài khoản hiển thị thành 120 triệu.
Nhưng muốn rút tiền thì phải nộp thêm 15% phí xác minh.
```

## Validation

### Backend tests

```powershell
cd backend
python -m pytest -q
python -m ruff check .
```

### Frontend checks

```powershell
cd frontend
npm run lint
npm run build
```

### Repository smoke test

Từ repository root:

```powershell
python scripts/smoke_test.py
```

Smoke test chạy trực tiếp FastAPI app bằng `TestClient`, kiểm tra:

- `GET /health`
- `POST /api/v1/fast-check`
- `POST /api/v1/investigate`

### Optional live provider smoke test

Script này có thể tiêu tốn quota provider. Chỉ chạy khi bạn chủ động bật:

```env
RUN_LIVE_PROVIDER_TESTS=true
```

Chạy:

```powershell
cd backend
python scripts/live_provider_smoke.py
```

Script chỉ in provider, role, model name, success/failure, latency, result count và safe error type. Không in API key, prompt đầy đủ hoặc raw response.

## Troubleshooting

### CORS: `Disallowed CORS origin`

Nguyên nhân thường gặp: frontend chạy ở `http://127.0.0.1:5173` nhưng backend chỉ allow `http://localhost:5173`.

Sửa trong `backend/.env`:

```env
CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Restart backend sau khi sửa.

### Port bị chiếm hoặc bị Windows chặn

Nếu port `8000` không chạy được, thử port khác:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8002
```

Sau đó cập nhật `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8002
```

Restart frontend.

### Frontend timeout khi gọi `/investigate`

Live Mode có thể mất lâu hơn Mock Mode vì phải gọi provider ngoài. Kiểm tra:

- Backend còn chạy không.
- `VITE_API_BASE_URL` đúng port backend chưa.
- `MOCK_MODE=false` có API key hợp lệ chưa.
- Tavily/OpenAI có quota và model access không.

### Live Mode vẫn ra mock evidence

Kiểm tra `backend/.env`:

```env
MOCK_MODE=false
ENABLE_WEB_SEARCH=true
```

Restart backend và gọi lại `/health`. Khi Live Mode đúng, health phải báo provider mode là `live` cho OpenAI và Tavily nếu đã bật.

## Security notes

- Không commit `.env`.
- Không log API key hoặc authorization header.
- Không lưu nội dung người dùng trong MVP.
- Không render raw stack trace hoặc raw provider response ra UI.
- Không upload file, ảnh hoặc PDF.
- Không chạy code do người dùng cung cấp.
- External search chỉ đi qua evidence adapter.

## Giới hạn MVP

VYVY là công cụ hỗ trợ đánh giá rủi ro, không phải kết luận pháp lý. Kết quả phụ thuộc vào nội dung đầu vào, nguồn bằng chứng khả dụng, provider configuration và quota. Khi hệ thống trả `partial`, nghĩa là một phần provider hoặc stage không khả dụng; risk vẫn được tính từ tín hiệu hiện có và confidence được điều chỉnh giảm.

## License / Hackathon note

Repository này được xây dựng cho MVP hackathon một ngày. Ưu tiên của dự án là demo ổn định, phạm vi rõ ràng, báo cáo giải thích được và an toàn dữ liệu.
