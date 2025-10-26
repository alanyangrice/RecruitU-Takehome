# RecruitU Frontend (Vite + React + TS)

Minimal one-page UI to upload a resume, show progress, and display results.

## Dev

1) Start the backend (in another terminal):
```
uvicorn app.main:app --reload --port 8080
```

2) Start the frontend:
```
cd frontend
npm i
npm run dev
```

- Dev server: http://localhost:5173
- Proxies /api to http://localhost:8080 (see vite.config.ts)

## Build
```
npm run build
npm run preview
```

## Notes
- Progress is client-side (uploading → parsing → planning → searching → scoring → done).
- If you want server-driven progress, add an SSE endpoint on the backend that emits step updates and subscribe from the UI.
