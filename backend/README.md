# RecruitU Similarity Backend (FastAPI)

Public endpoints:
- POST `/api/resume` — upload PDF resume, returns `targetId`, `targetProfile`, and `rawText`.
- POST `/api/people/rank` — end-to-end search + scoring. Input `targetId` or inline `targetProfile`, plus `weights`. Returns `searchId` and ranked `results`.
- POST `/api/people/rerank` — recompute composite scores for an existing `searchId` using new `weights` (no additional LLM calls).

## Getting started

1. `python -m venv .venv && source .venv/bin/activate`
2. `pip install -r backend/requirements.txt`
3. Copy `backend/.env.example` to `backend/.env` and fill values.
4. Run: `uvicorn app.main:app --reload --app-dir backend/app --host 0.0.0.0 --port 8000`

Notes:
- If `OPENAI_API_KEY` is not set, the app falls back to deterministic heuristics and zeros for scores.
- Set `RECRUITU_BASE_URL` to the staging base from the assessment. The app will return empty candidates if not configured.
