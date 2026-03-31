# AchieveCX AI Consultant

Monorepo: Next.js 14 frontend + FastAPI backend.

```
achievecx/
  frontend/     Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui
  backend/      FastAPI + Python 3.11
```

## Quick start

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Deploy
- Frontend → Vercel (auto-deploy on push)
- Backend → Railway (auto-deploy on push)
- Database → Supabase
