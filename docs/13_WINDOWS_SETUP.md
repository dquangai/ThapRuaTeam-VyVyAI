# 13 — Windows PowerShell Setup

## 1. Clone and create branches

```powershell
git clone <REPOSITORY_URL>
cd vyvy
git checkout -b dev
git push -u origin dev
```

## 2. Backend

```powershell
cd backend
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item ..\.env.example .env
uvicorn app.main:app --reload --port 8000
```

Open:

```text
http://localhost:8000/health
http://localhost:8000/docs
```

## 3. Frontend

In another PowerShell window:

```powershell
cd frontend
npm install
Copy-Item ..\.env.example .env
npm run dev
```

Open:

```text
http://localhost:5173
```

## 4. Common PowerShell note

Older Windows PowerShell versions may not support `&&`. Run commands on separate lines:

```powershell
git add .
git commit -m "feat(T03): add fast check"
git push
```

## 5. Verify keys without exposing them

```powershell
Get-Content .env | ForEach-Object {
  if ($_ -match "KEY=") {
    ($_ -split "=")[0] + "=***"
  }
}
```

Never paste actual keys into chat, issues, commits or screenshots.

## 6. Useful checks

```powershell
git status
git diff --stat
git diff
python -m pytest -q
npm run build
```
