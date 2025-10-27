from __future__ import annotations
from typing import Any
from openai import OpenAI
from ..config import settings
from ..schemas.types import ParsedResume, SimilarityPlan, FactorPlan, FactorName


SYSTEM_EXTRACT = (
    "You are an expert resume parser for finance roles. "
    "Extract ONLY these fields as concise values: full_name, current_company, previous_companies (array), "
    "title (map to one of: Analyst, Associate, Vice President, Director, Managing Director if possible), "
    "school (primary undergrad), city (current city if present). "
    "Respond as strict JSON for the ParsedResume pydantic model."
)


SYSTEM_PLAN = (
    "You generate similarity targets for company, title, school, and location. "
    "Rules (OUTPUT EXACT COUNTS): Company: exactly 3 at 1.0, 3 at 0.75, 3 at 0.5, 3 at 0.25; no duplicates; exclude the exact company from 0.75/0.5/0.25. "
    "Title (Analyst, Associate, Vice President, Director, Managing Director): exactly 1 at 1.0 (same title), 1 at 0.75, 1 at 0.5, 1 at 0.25. "
    "School: exactly 3 at 1.0 (peer schools with similar ranking/prestige; include the original school in 1.0), 3 at 0.75, 3 at 0.5, 3 at 0.25. "
    "Location: response must be the name of the city. provide multiple city names for each list: 3 at 1.0 for location_exact_1_0 (major cities in neighboring states), 3 at 0.75 for location_neighbors_0_75 (major cities in the same regional area like northeast, southeast, west coast, etc.), 3 at 0.5 for location_neighbors_0_5 (major cities across the country), 3 at 0.25 for location_neighbors_0_25 (farther domestic cities). "
    "Return strict JSON with top-level arrays named: current_company_* , title_* , school_* , location_* ."
)


def _client() -> OpenAI:
    """Create a configured OpenAI client from environment settings."""
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")
    return OpenAI(api_key=settings.openai_api_key)

def _json_schema_for_parsed_resume() -> dict[str, Any]:
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "full_name": {"type": ["string", "null"]},
            "current_company": {"type": ["string", "null"]},
            "previous_companies": {
                "type": "array",
                "items": {"type": "string"},
                "default": [],
            },
            "title": {"type": ["string", "null"]},
            "school": {"type": ["string", "null"]},
            "city": {"type": ["string", "null"]},
        },
        "required": [
            "full_name",
            "current_company",
            "previous_companies",
            "title",
            "school",
        ],
    }


def _json_schema_for_similarity_plan() -> dict[str, Any]:
    arr_str = {"type": "array", "items": {"type": "string"}}
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "current_company_exact_and_neighbors_1_0": {**arr_str, "maxItems": 3},
            "current_company_neighbors_0_75": {**arr_str, "maxItems": 3},
            "current_company_neighbors_0_5": {**arr_str, "maxItems": 3},
            "current_company_neighbors_0_25": {**arr_str, "maxItems": 3},
            "title_exact_and_neighbors_1_0": {**arr_str, "maxItems": 1},
            "title_neighbors_0_75": {**arr_str, "maxItems": 1},
            "title_neighbors_0_5": {**arr_str, "maxItems": 1},
            "title_neighbors_0_25": {**arr_str, "maxItems": 1},
            "school_exact_and_neighbors_1_0": {**arr_str, "maxItems": 3},
            "school_neighbors_0_75": {**arr_str, "maxItems": 3},
            "school_neighbors_0_5": {**arr_str, "maxItems": 3},
            "school_neighbors_0_25": {**arr_str, "maxItems": 3},
            "location_exact_1_0": {**arr_str, "maxItems": 3},
            "location_neighbors_0_75": {**arr_str, "maxItems": 3},
            "location_neighbors_0_5": {**arr_str, "maxItems": 3},
            "location_neighbors_0_25": {**arr_str, "maxItems": 3},
        },
        "required": [
            "current_company_exact_and_neighbors_1_0",
            "current_company_neighbors_0_75",
            "current_company_neighbors_0_5",
            "current_company_neighbors_0_25",
            "title_exact_and_neighbors_1_0",
            "title_neighbors_0_75",
            "title_neighbors_0_5",
            "title_neighbors_0_25",
            "school_exact_and_neighbors_1_0",
            "school_neighbors_0_75",
            "school_neighbors_0_5",
            "school_neighbors_0_25",
            "location_exact_1_0",
            "location_neighbors_0_75",
            "location_neighbors_0_5",
            "location_neighbors_0_25",
        ],
    }


def _chat_json_with_schema(model: str, system: str, user: str, schema_name: str, schema: dict[str, Any]) -> dict[str, Any]:
    """
    Chat with the LLM using a strict JSON schema.

    Returns a dictionary parsed from the LLM's response.
    """
    client = _client()
    # First attempt: strict JSON schema
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.1,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": schema_name, "schema": schema, "strict": True},
            },
        )
        raw = completion.choices[0].message.content or "{}"
        return __import__("json").loads(raw)
    except Exception:
        # Fallback: json_object with a strong instruction still yields valid JSON
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system + " Always return strict JSON only."},
                {"role": "user", "content": user},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        raw = completion.choices[0].message.content or "{}"
        return __import__("json").loads(raw)


def parse_resume_text(text: str) -> ParsedResume:
    """
    Extract structured fields from raw resume text using an LLM with a strict JSON schema.

    Returns a `ParsedResume` with the minimal fields needed for planning & scoring.
    """
    data = _chat_json_with_schema(
        model=settings.openai_model_extract,
        system=SYSTEM_EXTRACT,
        user=text,
        schema_name="ParsedResume",
        schema=_json_schema_for_parsed_resume(),
    )
    parsed = ParsedResume.model_validate(data)
    return parsed


def build_similarity_plan(parsed: ParsedResume) -> SimilarityPlan:
    """
    Ask the LLM to propose search/score targets per factor and coerce into `SimilarityPlan`.

    The output is normalized and truncated for each tier (1.0 / 0.75 / 0.5 / 0.25).
    """
    user_payload = __import__("json").dumps(parsed.model_dump())
    data = _chat_json_with_schema(
        model=settings.openai_model_score,
        system=SYSTEM_PLAN,
        user=user_payload,
        schema_name="SimilarityPlan",
        schema=_json_schema_for_similarity_plan(),
    )
    # Build SimilarityPlan.factors from flat arrays
    def dedupe_limit(values: list[str], limit: int) -> list[str]:
        """Stable de‑dupe preserving order and enforce a maximum length."""
        return list(dict.fromkeys(values))[:limit]

    # Dedupe and truncate
    company_1 = dedupe_limit(data.get("current_company_exact_and_neighbors_1_0", []), 3)
    company_075 = dedupe_limit(data.get("current_company_neighbors_0_75", []), 3)
    company_05 = dedupe_limit(data.get("current_company_neighbors_0_5", []), 3)
    company_025 = dedupe_limit([v for v in data.get("current_company_neighbors_0_25", []) if v not in company_1], 3)

    title_1 = dedupe_limit(data.get("title_exact_and_neighbors_1_0", []), 1)
    title_075 = dedupe_limit(data.get("title_neighbors_0_75", []), 1)
    title_05 = dedupe_limit([v for v in data.get("title_neighbors_0_5", []) if v not in title_1], 1)
    title_025 = dedupe_limit([v for v in data.get("title_neighbors_0_25", []) if v not in title_1], 1)

    school_1 = dedupe_limit(data.get("school_exact_and_neighbors_1_0", []), 3)
    school_075 = dedupe_limit(data.get("school_neighbors_0_75", []), 3)
    school_05 = dedupe_limit([v for v in data.get("school_neighbors_0_5", []) if v not in school_1], 3)
    school_025 = dedupe_limit([v for v in data.get("school_neighbors_0_25", []) if v not in school_1], 3)

    loc_1 = dedupe_limit(data.get("location_exact_1_0", []), 3)
    loc_075 = dedupe_limit(data.get("location_neighbors_0_75", []), 3)
    loc_05 = dedupe_limit(data.get("location_neighbors_0_5", []), 3)
    loc_025 = dedupe_limit([v for v in data.get("location_neighbors_0_25", []) if v not in loc_1], 3)

    factors = {
        FactorName.current_experience: FactorPlan(exact_1_0=company_1, neighbors_0_75=company_075, neighbors_0_5=company_05, neighbors_0_25=company_025),
        FactorName.title: FactorPlan(exact_1_0=title_1, neighbors_0_75=title_075, neighbors_0_5=title_05, neighbors_0_25=title_025),
        FactorName.school: FactorPlan(exact_1_0=school_1, neighbors_0_75=school_075, neighbors_0_5=school_05, neighbors_0_25=school_025),
        FactorName.location: FactorPlan(exact_1_0=loc_1, neighbors_0_75=loc_075, neighbors_0_5=loc_05, neighbors_0_25=loc_025),
    }
    return SimilarityPlan(factors=factors)
