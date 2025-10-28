# RecruitU Takehome

A minimal full-stack MVP to parse a resume, generate a similarity plan, search RecruitU, and score/rank candidates.
Live demo: 

## How it works

1) Upload a resume PDF
2) Backend extracts text and parses fields with OpenAI
3) A similarity plan is built across company, title, school, and location with tiers 1.0 / 0.75 / 0.5 / 0.25
4) RecruitU is queried; each candidate is scored and ranked
5) Frontend displays parsed data, plan, and top results with a Load more button

## Tech Stack

## Quick start

- Backend (FastAPI)
  - Python 3.11+
  - Create `backend/.env`:
    ```
    OPENAI_API_KEY=sk-...
    RECRUITU_BASE_URL=https://staging.recruitu.com/api/<token>
    ALLOWED_ORIGINS=*
    ```
  - Install and run:
    ```
    cd backend
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8080
    ```

- Frontend (Vite + React + TS)
  - Install and run:
    ```
    cd frontend
    npm i
    npm run dev
    ```
  - Dev server: http://localhost:5173
  - Proxies `/api` to `http://localhost:8080`

## API

- `GET /api/health` → `{ "status": "ok" }`
- `POST /api/upload` (multipart/form-data)
  - field: `file` (PDF)
  - returns:
    - `parsed`: extracted fields
    - `query_plan`: `SimilarityPlan` (per-factor `FactorPlan` with tiers)
    - `results`: ranked `CandidateScore[]` with `total_score` and factor breakdown

Endpoint response shapes from assignment context are summarized in `assessment_context/endpoint_details.txt`.

