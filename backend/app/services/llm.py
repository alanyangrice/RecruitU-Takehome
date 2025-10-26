from __future__ import annotations
import json
import os
from typing import List, Dict
from openai import OpenAI
from ..config import settings
from ..schemas.types import TargetProfile, Candidate, CandidateScores, SimilaritySpec

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
        # Fallback heuristic when no API key is configured
        # Very naive extraction: create a minimal profile
        return TargetProfile(
            full_name=None,
            headline=None,
            locations=[],
            current_company=None,
            current_title=None,
            sector=None,
            skills=[],
            education=[],
        )
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


def generate_recruitu_queries(target: TargetProfile) -> List[Dict]:
    """Use the LLM to produce 3-6 RecruitU /search filter objects.

    Allowed keys (must match RecruitU /search):
      name, current_company, sector, previous_company, title, role,
      school, undergraduate_year, city

    Fallback: return target profile query
    """
    client = _client_if_configured()
    if client is None:
        return [target.model_dump()]

    system = (
        "Given a target candidate profile, generate RecruitU /search filter objects. "
        "Only use these keys: name, current_company, sector, previous_company, title, role, "
        "school, undergraduate_year, city. Prefer exact strings present in the profile; "
        "infer reasonable variants when helpful. Do not include null or unknown fields. "
        "Return JSON with a 'queries' array."
    )
    payload = target.model_dump()
    resp = client.responses.create(
        model=settings.openai_model_extract,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(payload)},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    parsed = resp.output_parsed or {}
    raw_queries = parsed.get("queries", [])
    cleaned: list[dict] = []
    allowed = {
        "name",
        "current_company",
        "sector",
        "previous_company",
        "title",
        "role",
        "school",
        "undergraduate_year",
        "city",
    }
    for q in raw_queries:
        if isinstance(q, dict):
            filtered = {k: v for k, v in q.items() if k in allowed and v not in (None, "", [])}
            if filtered:
                cleaned.append(filtered)
        if len(cleaned) >= 6:
            break
    if not cleaned:
        # Safety net if model returns nothing usable
        return [{"sector": target.sector or "FINANCE"}]
    return cleaned


def build_similarity_spec(target: TargetProfile) -> SimilaritySpec:
    """Ask LLM to propose similar entities (companies, titles, schools, locations, etc.)
    with ratings 0..1, and a target YOE, to guide deterministic scoring.

    Falls back to a minimal spec when no OpenAI key is configured.
    """
    client = _client_if_configured()
    if client is None:
        comp = {}
        if target.current_company:
            comp[target.current_company] = 1.0
        titles = {}
        if target.current_title:
            titles[target.current_title] = 1.0
        locs = {}
        for l in target.locations:
            locs[l] = 1.0
        schools = {}
        if target.education:
            for e in target.education:
                if e.school:
                    schools[e.school] = 1.0
        return SimilaritySpec(
            companies=comp,
            titles=titles,
            schools=schools,
            locations=locs,
            sectors={target.sector: 1.0} if target.sector else {},
            skills={s: 1.0 for s in target.skills},
            yoe_target=target.total_years_experience,
            yoe_tolerance_years=3.0,
        )

    prompt = (
        "Given a target profile JSON, return a SimilaritySpec JSON with fields: "
        "companies, titles, schools, locations, sectors, skills — each mapping string->score in [0,1]. "
        "Include yoe_target (float, years of experience) and yoe_tolerance_years (float). "
        "Companies example: {'McKinsey':1.0,'Bain':1.0,'BCG':1.0,'EY':0.9,'LEK':0.8}. "
        "Only include a few dozen high-signal entries; omit nulls."
    )
    schema = {
        "type": "object",
        "properties": {
            "companies": {"type": "object", "additionalProperties": {"type": "number"}},
            "titles": {"type": "object", "additionalProperties": {"type": "number"}},
            "schools": {"type": "object", "additionalProperties": {"type": "number"}},
            "locations": {"type": "object", "additionalProperties": {"type": "number"}},
            "sectors": {"type": "object", "additionalProperties": {"type": "number"}},
            "skills": {"type": "object", "additionalProperties": {"type": "number"}},
            "yoe_target": {"type": ["number", "null"]},
            "yoe_tolerance_years": {"type": "number"},
        },
        "required": [],
    }
    resp = client.responses.create(
        model=settings.openai_model_extract,
        input=[{"role": "system", "content": prompt}, {"role": "user", "content": json.dumps(target.model_dump())}],
        response_format={"type": "json_schema", "json_schema": {"name": "SimilaritySpec", "schema": schema}},
        temperature=0.2,
    )
    data = resp.output_parsed or {}
    return SimilaritySpec(**data)
