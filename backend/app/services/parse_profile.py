from __future__ import annotations
import json
import os
from typing import List, Dict
from openai import OpenAI
from ..config import settings
from ..schemas.types import TargetProfile, SimilaritySpec

_client: OpenAI | None = None


def _client_if_configured() -> OpenAI | None:
    global _client
    if _client is not None:
        return _client
    if settings.openai_api_key:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def extract_target_profile(text: str) -> TargetProfile:
    client = _client_if_configured()
    if client is None:
        # No API key configured, raise an error
        raise ValueError("OpenAI client not configured")
        
    schema = {
        "type": "object",
        "properties": {
            "full_name": {"type": "string"},
            "headline": {"type": "string"},
            "total_years_experience": {"type": "number"},
            "locations": {"type": "array", "items": {"type": "string"}},
            "current_company": {"type": "string"},
            "current_title": {"type": "string"},
            "sector": {"type": "string"},
            "skills": {"type": "array", "items": {"type": "string"}},
            "education": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "school": {"type": "string"},
                        "degree": {"type": "string"},
                        "field": {"type": "string"},
                        "grad_year": {"type": "integer"},
                    },
                    "required": [],
                },
            },
        },
        "required": [],
    }
    resp = client.responses.create(
        model=settings.openai_model_extract,
        input=[
            {
                "role": "user",
                "content": f"Extract a TargetProfile JSON from the following resume text.\n\n{text}",
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "TargetProfile", "schema": schema},
        },
        temperature=0.2,
    )
    data = resp.output_parsed or {}
    return TargetProfile(**data)


def generate_search_plan(target: TargetProfile) -> tuple[List[Dict], SimilaritySpec]:
    """
    Single entry performing the two LLM calls needed for search and scoring
    for the five-factor model: current_experience, previous_experience, title,
    school, and years_of_experience.
    """
    client = _client_if_configured()
    if client is None:
        raise ValueError("OpenAI client not configured")

    # Call 1: queries (only allowed keys for RecruitU /search we care about)
    q_system = (
        "Given a target candidate profile, generate RecruitU /search filter objects. "
        "Only use these keys: current_company, previous_company, title, school. "
        "Prefer exact strings present in the profile; "
        "infer reasonable variants when helpful. Do not include null or unknown fields. "
        "Return JSON with a 'queries' array."
    )
    payload = target.model_dump()
    q_resp = client.responses.create(
        model=settings.openai_model_extract,
        input=[
            {"role": "system", "content": q_system},
            {"role": "user", "content": json.dumps(payload)},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    q_parsed = q_resp.output_parsed or {}
    raw_queries = q_parsed.get("queries", [])
    allowed = {"current_company", "previous_company", "title", "school"}
    queries: list[dict] = []
    for q in raw_queries:
        if isinstance(q, dict):
            filtered = {k: v for k, v in q.items() if k in allowed and v not in (None, "", [])}
            if filtered:
                queries.append(filtered)
        if len(queries) >= 6:
            break
    if not queries:
        queries = []

    # Call 2: similarity spec with constrained ratings (1.0 and 0.5) for 3+3 companies,
    # 2+2 titles from the fixed ladder, and 3+3 schools; plus YOE thresholds.
    s_prompt = (
        "Given a target profile JSON, return a SimilaritySpec for exactly five factors: "
        "companies (used for current and previous experience), titles, schools, and years of experience. "
        "Companies: include exactly 3 with score 1.0 (not including the same company) and exactly 3 with score 0.5. "
        "Titles: choose from [Analyst, Associate, Vice President, Director, Managing Director]; include exactly 2 with score 1.0 (the same title and the adjacent level), and exactly 2 with score 0.5; omit one to imply 0. "
        "Schools: include exactly 3 with score 1.0 (not including the same school) and exactly 3 with score 0.5. "
        "For years of experience, include: yoe_target (float), yoe_score1_max_diff=1.0, yoe_score0_5_max_diff=3.0. "
        "Return only these fields and omit nulls."
    )
    s_schema = {
        "type": "object",
        "properties": {
            "companies": {"type": "object", "additionalProperties": {"type": "number", "enum": [0.5, 1.0]}},
            "titles": {"type": "object", "additionalProperties": {"type": "number", "enum": [0.5, 1.0]}},
            "schools": {"type": "object", "additionalProperties": {"type": "number", "enum": [0.5, 1.0]}},
            "yoe_target": {"type": ["number", "null"]},
            "yoe_score1_max_diff": {"type": "number"},
            "yoe_score0_5_max_diff": {"type": "number"},
        },
        "required": [],
    }
    s_resp = client.responses.create(
        model=settings.openai_model_extract,
        input=[{"role": "system", "content": s_prompt}, {"role": "user", "content": json.dumps(payload)}],
        response_format={"type": "json_schema", "json_schema": {"name": "SimilaritySpec", "schema": s_schema}},
        temperature=0.2,
    )
    s_data = s_resp.output_parsed or {}
    spec = SimilaritySpec(**s_data)

    return queries, spec


def generate_recruitu_queries(target: TargetProfile) -> List[Dict]:
    """Compatibility wrapper: uses generate_search_plan to fetch queries only."""
    queries, _ = generate_search_plan(target)
    return queries


def build_similarity_spec(target: TargetProfile) -> SimilaritySpec:
    """Compatibility wrapper: uses generate_search_plan to fetch spec only."""
    _, spec = generate_search_plan(target)
    return spec
