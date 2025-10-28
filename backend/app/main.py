from __future__ import annotations
import uuid
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers.public import router as public_router

app = FastAPI(title="RecruitU Similarity Backend")

# CORS configuration
origins = (
    ["*"]
    if not settings.allowed_origins or settings.allowed_origins == "*"
    else [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
)
allow_credentials = False if "*" in origins else True

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


app.include_router(public_router)
