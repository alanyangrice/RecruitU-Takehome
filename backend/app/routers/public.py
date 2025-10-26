from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..services.pdf import extract_pdf_text
from ..services.parse_profile import parse_resume_text, build_similarity_plan
from ..services.recruitu import RecruitUClient
from ..services.scoring import aggregate_and_score
from ..schemas.types import UploadResponse


router = APIRouter(prefix="/api", tags=["public"])


@router.post("/upload", response_model=UploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    try:
        resume_text = extract_pdf_text(await file.read())

        # Parse resume text into structured fields, then build a similarity plan
        # that lists close neighbors per factor (company/title/school/location).
        parsed = parse_resume_text(resume_text)
        plan = build_similarity_plan(parsed)

        client = RecruitUClient()
        scored = await aggregate_and_score(client, parsed, plan)
        return UploadResponse(query_plan=plan, parsed=parsed, results=scored)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
