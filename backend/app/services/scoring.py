from __future__ import annotations
from typing import Iterable, List, Tuple, Dict, Optional
from ..schemas.types import (
    CandidateScore,
    ParsedResume,
    RecruitUDocument as RecruitUSearchDocument,
    SimilarityPlan,
    FactorName,
    FactorPlan,
)

# ---------- small utilities ----------

def _normalize(s: Optional[str]) -> str:
    return (s or "").strip().lower()


def _contains_any(hay: Optional[str], needles: Iterable[str]) -> bool:
    hay_n = _normalize(hay)
    return any((n := _normalize(x)) and n in hay_n for x in needles)


def _safe_attr(obj, attr: str, default=None):
    return getattr(obj, attr, default) if obj is not None else default


def _level_score(field: str, top: Iterable[str], mid: Iterable[str], low: Iterable[str], very_low: Iterable[str]) -> float:
    if _contains_any(field, top):
        return 1.0
    if _contains_any(field, mid):
        return 0.75
    if _contains_any(field, low):
        return 0.5
    if _contains_any(field, very_low):
        return 0.25
    return 0.0


# ---------- core scoring ----------

def score_document(doc: RecruitUSearchDocument, plan: SimilarityPlan) -> Dict[FactorName, float]:
    """Score a document based on the similarity plan and return a dictionary of factors and their scores."""
    factors: Dict[FactorName, float] = {}

    # current_experience: company match from current_company.company
    company_field = _safe_attr(_safe_attr(doc, "current_company"), "company", "") or ""
    fp_company: FactorPlan = plan.factors.get(FactorName.current_experience, FactorPlan())
    score_company = _level_score(company_field, fp_company.exact_1_0, fp_company.neighbors_0_75, fp_company.neighbors_0_5, fp_company.neighbors_0_25)
    factors[FactorName.current_experience] = score_company

    # previous_experience: string field previous_companies
    score_prev = _level_score(doc.previous_companies or "", fp_company.exact_1_0, fp_company.neighbors_0_75, fp_company.neighbors_0_5, fp_company.neighbors_0_25)
    factors[FactorName.previous_experience] = score_prev

    # title: prefer doc.title; fallback to current_company.title
    title_field = (doc.title or _safe_attr(_safe_attr(doc, "current_company"), "title", "")) or ""
    fp_title: FactorPlan = plan.factors.get(FactorName.title, FactorPlan())
    score_title = _level_score(title_field, fp_title.exact_1_0, fp_title.neighbors_0_75, fp_title.neighbors_0_5, fp_title.neighbors_0_25)
    factors[FactorName.title] = score_title

    # school
    fp_school: FactorPlan = plan.factors.get(FactorName.school, FactorPlan())
    score_school = _level_score(doc.school or "", fp_school.exact_1_0, fp_school.neighbors_0_75, fp_school.neighbors_0_5, fp_school.neighbors_0_25)
    factors[FactorName.school] = score_school

    # years_of_experience removed from scoring

    # location (city)
    fp_loc: FactorPlan = plan.factors.get(FactorName.location, FactorPlan())
    loc_score = _level_score(doc.city or "", fp_loc.exact_1_0, fp_loc.neighbors_0_75, fp_loc.neighbors_0_5, fp_loc.neighbors_0_25)
    factors[FactorName.location] = loc_score
    return factors


# Weighted scoring out of 100
FACTOR_WEIGHTS: Dict[FactorName, float] = {
    FactorName.current_experience: 40.0,
    FactorName.previous_experience: 10.0,
    FactorName.title: 15.0,
    FactorName.school: 17.5,
    FactorName.location: 7.5,
}


def aggregate_score(breakdown: Dict[FactorName, float]) -> float:
    if not breakdown:
        return 0.0
    total = sum(FACTOR_WEIGHTS[f] * breakdown.get(f, 0.0) for f in FACTOR_WEIGHTS)
    return round(total, 2)
    

# ---------- aggregation workflow ----------

async def aggregate_and_score(
    client,
    parsed: ParsedResume,
    plan: SimilarityPlan,
    return_stats: bool = False,
    search_count: int = 1000,
):
    """
    Ordered aggregation workflow:
      1) current_company → add if new
      2) previous_company (each) → add if new
      3) title → add if new
      4) school → add if new
      5) location → add if new

    Then: return ranked results (no people enrichment).
    """
    total_map: Dict[str, CandidateScore] = {}
    counters: Dict[str, int] = {
        "current_added": 0,
        "previous_added": 0,
        "title_added": 0,
        "school_added": 0,
        "location_added": 0,
    }

    async def _search_and_add(query_key: str, query_value: str, counter_key: str):
        if not query_value:
            return
        res = await client.search({query_key: query_value, "count": search_count})
        for r in res.results:
            if r.id in total_map:
                continue
            factors = score_document(r, plan)
            total_map[r.id] = CandidateScore(
                candidate_id=r.id,
                total_score=aggregate_score(factors),
                factors=factors,
                document=r,
            )
            counters[counter_key] += 1

    # 1) current company
    await _search_and_add("current_company", parsed.current_company or "", "current_added")

    # 2) previous companies
    for pc in (parsed.previous_companies or []):
        if pc:
            await _search_and_add("previous_company", pc, "previous_added")

    # 3) title
    await _search_and_add("title", parsed.title or "", "title_added")

    # 4) school
    await _search_and_add("school", parsed.school or "", "school_added")

    # 5) location (city)
    if getattr(parsed, "city", None):
        await _search_and_add("city", parsed.city, "location_added")

    # Rank results
    scored = list(total_map.values())
    scored.sort(key=lambda c: c.total_score, reverse=True)

    if return_stats:
        stats = {
            "current_company_added": counters["current_added"],
            "previous_company_added": counters["previous_added"],
            "title_added": counters["title_added"],
            "school_added": counters["school_added"],
            "location_added": counters["location_added"],
            "total_candidates": len(total_map),
        }
        return scored, stats

    return scored
