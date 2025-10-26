# RecruitU Similarity Backend (MVP)

FastAPI backend implementing the workflow:

- Upload resume (PDF)
- Parse text and extract fields with OpenAI
- Generate similarity plan (companies, titles, schools, experience bands)
- Search RecruitU API
- Score results using five factors only

## Setup

1. Python 3.11+
2. Create `.env` in this directory:

```
OPENAI_API_KEY=sk-...
RECRUITU_BASE_URL=https://staging.recruitu.com/api/<token>
ALLOWED_ORIGINS=*
```

3. Install deps

```
pip install -r requirements.txt
```

4. Run server

```
uvicorn app.main:app --reload --port 8080
```

## API

- `GET /api/health`
- `POST /api/upload` (multipart form)
  - field `file`: PDF resume
  - response: parsed fields, similarity plan, ranked candidates with factor breakdowns

## Notes

- Only five scoring factors: `current_experience`, `previous_experience`, `title`, `school`, `years_of_experience`.
- Experience bands: 1.0 close band around N years; 0.5 for next band; else 0.

