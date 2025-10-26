from __future__ import annotations
from typing import List
from ..schemas.types import Candidate, CandidateScores, TargetProfile, SimilaritySpec


def _string_or_none(value):
    if isinstance(value, str):
        return value
    return None


def _extract_candidate_fields(c: Candidate) -> dict:
    p = c.profile or {}
    doc = p.get("document") or p
    current = doc.get("current_company") or {}
    undergrad = doc.get("undergrad") or {}
    return {
        "current_company": _string_or_none(current.get("company")),
        "current_title": _string_or_none(current.get("title")),
        "previous_companies": _string_or_none(doc.get("previous_companies")),
        "previous_titles": _string_or_none(doc.get("previous_titles")),
        "city": _string_or_none(doc.get("city")),
        "school": _string_or_none(undergrad.get("school")),
        "current_starts_at": (current.get("starts_at") or {}).get("year"),
    }


def _score_from_mapping(value: str | None, mapping: dict[str, float]) -> float:
    if not value or not mapping:
        return 0.0
    v = value.lower()
    best = 0.0
    for key, score in mapping.items():
        if not isinstance(key, str):
            continue
        if key.lower() in v:
            best = max(best, float(score))
    return best


def _score_any_from_mapping(values: list[str], mapping: dict[str, float]) -> float:
    best = 0.0
    for v in values:
        best = max(best, _score_from_mapping(v, mapping))
    return best


def _score_years(candidate_value: float | None, target_value: float | None, tol_years: float) -> float:
    if candidate_value is None or target_value is None:
        return 0.0
    diff = abs(float(candidate_value) - float(target_value))
    if tol_years <= 0:
        return 0.0
    return max(0.0, 1.0 - min(1.0, diff / tol_years))


def score_candidates_with_spec(cands: List[Candidate], target: TargetProfile, spec: SimilaritySpec) -> List[CandidateScores]:
    results: list[CandidateScores] = []
    for c in cands:
        f = _extract_candidate_fields(c)
        prev_companies = []
        if f["previous_companies"]:
            prev_companies = [s.strip() for s in f["previous_companies"].split(",") if s.strip()]
        current_experience = _score_from_mapping(f["current_company"], spec.companies)
        previous_experience = _score_any_from_mapping(prev_companies, spec.companies)

        prev_titles = []
        if f["previous_titles"]:
            prev_titles = [s.strip() for s in f["previous_titles"].split(",") if s.strip()]
        title_score = _score_from_mapping(f["current_title"], spec.titles)

        school_score = _score_from_mapping(f["school"], spec.schools)

        y_current = None
        if f["current_starts_at"]:
            try:
                from datetime import datetime
                y_current = datetime.utcnow().year - int(f["current_starts_at"])  # rough
            except Exception:
                y_current = None
        # Years experience scoring uses two-step ramp based on target.yoe_target
        y_total = getattr(target, "total_years_experience", None)
        yoe_total_score = 0.0
        if y_total is not None and spec.yoe_target is not None:
            diff = abs(float(y_total) - float(spec.yoe_target))
            if diff <= spec.yoe_score1_max_diff:
                yoe_total_score = 1.0
            elif diff <= spec.yoe_score0_5_max_diff:
                yoe_total_score = 0.5
            else:
                yoe_total_score = 0.0

        results.append(
            CandidateScores(
                current_experience=current_experience,
                previous_experience=previous_experience,
                title=title_score,
                school=school_score,
                years_experience=max(yoe_total_score, 0.0),
            )
        )
    return results
