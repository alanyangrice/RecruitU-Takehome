# RecruitU Takehome

A minimal full-stack MVP to parse a resume, generate a similarity plan, search RecruitU, and score/rank candidates.
Live demo: https://recruitu-takehome-1.onrender.com/

## How it works

1) Upload a resume PDF
2) Backend extracts text and parses fields with OpenAI
3) A similarity plan is built across company, title, school, and location with tiers 1.0 / 0.75 / 0.5 / 0.25
4) RecruitU is queried; each candidate is scored and ranked
5) Frontend displays parsed data, plan, and top results with a Load more button

Runtime flow (end‑to‑end):
- Frontend: user selects a PDF and clicks Start → POST `/api/upload` (multipart).
- Backend:
  - `pdf.extract_pdf_text` gathers text.
  - `parse_profile.parse_resume_text` uses an LLM with a strict JSON schema to return a `ParsedResume`.
  - `parse_profile.build_similarity_plan` generates a `SimilarityPlan` with tiered neighbors per factor.
  - `recruitu.RecruitUClient.search` fetches candidates.
  - `scoring.aggregate_and_score` scores with fixed factor weights and returns a ranked list.
- Frontend renders the parsed fields, the per‑factor tiers, and the scored results.

## Tech Stack

- Backend
  - FastAPI (web framework) + Uvicorn (ASGI server)
  - Pydantic v2 (data models) and python‑multipart (file upload)
  - PyPDF2 (PDF text extraction)
  - OpenAI Python SDK (LLM calls with JSON schema) 
  - httpx (async HTTP client) 
  - python‑dotenv (env loading)
- Frontend
  - React + TypeScript
  - Vite (bundler/dev server) with `/api` dev proxy to `http://localhost:8080`
  - Fetch API for requests; simple component state for status/progress
- Infrastructure (local + hosting friendly)
  - CORS configured in backend via `ALLOWED_ORIGINS`
  - Frontend can read `VITE_API_BASE` at build time for API base URL

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

