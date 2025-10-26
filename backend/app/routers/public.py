from backend.app.schemas.types import Candidate, CandidateScores


from __future__ import annotations
import uuid
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..schemas.types import UploadResumeResponse, TargetProfile, RankRequest, RankResponse, ReRankRequest, Candidate, ScoredCandidate, CandidateScores, WeightMap
from ..cache import store
from ..services.pdf import extract_pdf_text
from ..services import llm, recruitu
from ..services.scoring import score_candidates_with_spec


def weighted_score(scores: CandidateScores, w: WeightMap) -> float:
    total_w = (
        w.education
        + w.companies
        + w.title_seniority
        + w.years_experience
        + w.location
        + w.sector
        + w.skills
    )
    dot = (
        w.education * scores.education
        + w.companies * scores.companies
        + w.title_seniority * scores.title_seniority
        + w.years_experience * scores.years_experience
        + w.location * scores.location
        + w.sector * scores.sector
        + w.skills * scores.skills
    )
    return dot / total_w if total_w > 0 else 0.0


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
    return UploadResumeResponse(targetId=target_id, targetProfile=target, rawText=text)


@router.post("/people/rank", response_model=RankResponse)
async def people_rank(req: RankRequest):
    target: TargetProfile | None = None
    if req.targetId:
        target = store.targets.get(req.targetId)
    if target is None and req.targetProfile is not None:
        target = req.targetProfile
    if target is None:
        raise HTTPException(status_code=400, detail="Provide targetId or targetProfile")

    queries = llm.generate_recruitu_queries(target)
    candidates: List[Candidate] = await recruitu.search(
        queries, count_per_page=req.countPerPage, max_pages=req.maxPages, top_k=req.topK
    )

    # Build similarity spec and apply deterministic scoring
    sim_spec = llm.build_similarity_spec(target)
    scores_list = score_candidates_with_spec(candidates, target, sim_spec)
    results: list[ScoredCandidate] = []
    for cand, scores in zip[tuple[Candidate, CandidateScores]](candidates, scores_list):
        composite = weighted_score(scores, req.weights)
        results.append(ScoredCandidate(candidate=cand, scores=scores, composite=composite))
    results.sort(key=lambda r: r.composite, reverse=True)

    search_id = f"srch_{uuid.uuid4().hex[:12]}"
    store.search_candidates[search_id] = candidates
    store.search_scored[search_id] = results

    return RankResponse(searchId=search_id, results=results)


@router.post("/people/rerank", response_model=RankResponse)
async def people_rerank(req: ReRankRequest):
    results = store.search_scored.get(req.searchId)
    if results is None:
        raise HTTPException(status_code=404, detail="searchId not found")
    recomputed: list[ScoredCandidate] = []
    for item in results:
        comp = weighted_score(item.scores, req.weights)
        recomputed.append(
            ScoredCandidate(candidate=item.candidate, scores=item.scores, composite=comp)
        )
    recomputed.sort(key=lambda r: r.composite, reverse=True)
    return RankResponse(searchId=req.searchId, results=recomputed)
