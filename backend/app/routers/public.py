from backend.app.schemas.types import Candidate, CandidateScores


from __future__ import annotations
import uuid
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..schemas.types import UploadResumeResponse, Candidate, ScoredCandidate, CandidateScores
from ..cache import store
from ..services.pdf import extract_pdf_text
from ..services import recruitu
from ..services import parse_profile as llm
from ..services.scoring import score_candidates_with_spec

def weighted_score(scores: CandidateScores) -> float:
    # Fixed preset weights for MVP (sums to 100 for readability)
    w_current, w_prev, w_title, w_school, w_yoe = 35, 15, 20, 20, 10
    total_w = w_current + w_prev + w_title + w_school + w_yoe
    dot = (
        w_current * scores.current_experience
        + w_prev * scores.previous_experience
        + w_title * scores.title
        + w_school * scores.school
        + w_yoe * scores.years_experience
    )
    return dot / total_w

router = APIRouter(prefix="/api", tags=["public"]) 

@router.post("/resume", response_model=UploadResumeResponse)
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    pdf_bytes = await file.read()
    text = extract_pdf_text(pdf_bytes)
    target = llm.extract_target_profile(text)
    target_id = f"tg_{uuid.uuid4().hex[:12]}"
    store.targets[target_id] = target
    # Run full pipeline
    # 1) Generate queries and similarity spec
    queries = llm.generate_recruitu_queries(target)
    candidates: List[Candidate] = await recruitu.search(queries, count_per_page=20, max_pages=3, top_k=100)
    sim_spec = llm.build_similarity_spec(target)
    scores_list = score_candidates_with_spec(candidates, target, sim_spec)

    # 2) Preset weights for MVP
    results: list[ScoredCandidate] = []
    for cand, scores in zip[tuple[Candidate, CandidateScores]](candidates, scores_list):
        composite = weighted_score(scores)
        results.append(ScoredCandidate(candidate=cand, scores=scores, composite=composite))
    results.sort(key=lambda r: r.composite, reverse=True)

    store.search_scored[f"srch_{uuid.uuid4().hex[:12]}"] = results
    return UploadResumeResponse(targetId=target_id, targetProfile=target, rawText=text, results=results)
