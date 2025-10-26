# RecruitU Similarity Backend

FastAPI backend that implements the end‑to‑end workflow:

- Upload resume (PDF)
- Parse text and extract fields with OpenAI (name, current/previous company, title, school, city)
- Generate a similarity plan of targets (companies/titles/schools/locations) in 1.0/0.75/0.5 tiers
- Query the RecruitU search API and score each candidate
- Return ranked results and the plan to the client

Scoring factors (sum to 100):
- current_experience (50), previous_experience (10), title (15), school (17.5), location (7.5)

Years of experience scoring was intentionally removed per requirements.

## Setup

1) Python 3.11+
2) Create `.env` in `backend/`:

```
OPENAI_API_KEY=sk-...
RECRUITU_BASE_URL=https://staging.recruitu.com/api/<token>
ALLOWED_ORIGINS=*
```

3) Install deps

```
pip install -r requirements.txt
```

4) Run server

```
uvicorn app.main:app --reload --port 8080
```

## API

- `GET /api/health` → `{ "status": "ok" }`
- `POST /api/upload` (multipart/form-data)
  - field: `file` (PDF)
  - returns:
    - `parsed`: fields extracted from the resume
    - `query_plan`: Similarity plan (FactorPlan per factor)
    - `results`: ranked candidates with `total_score` and `factors` map

## Progress reporting

The current endpoint is a single request/response. The frontend shows a simple client‑side progress indicator (uploading → parsing → planning → searching → scoring → done).

If you need streaming server‑side progress, add an SSE endpoint that emits step events while the workflow runs; the frontend can subscribe and reflect real‑time status.

