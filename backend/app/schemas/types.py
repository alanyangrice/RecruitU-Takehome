from __future__ import annotations
from typing import Dict, List, Optional, Generic, TypeVar
from enum import Enum
from pydantic import BaseModel, Field


class FactorName(str, Enum):
    current_experience = "current_experience"
    previous_experience = "previous_experience"
    title = "title"
    school = "school"
    location = "location"


class ParsedResume(BaseModel):
    full_name: Optional[str] = None
    current_company: Optional[str] = None
    previous_companies: List[str] = Field(default_factory=list)
    title: Optional[str] = None
    school: Optional[str] = None
    city: Optional[str] = None


class FactorPlan(BaseModel):
    exact_1_0: List[str] = Field(default_factory=list)
    neighbors_0_75: List[str] = Field(default_factory=list)
    neighbors_0_5: List[str] = Field(default_factory=list)


class SimilarityPlan(BaseModel):
    # Map factor → plan (e.g., factors[FactorName.title].exact_1_0)
    factors: Dict[FactorName, FactorPlan] = Field(default_factory=dict)


class RecruitUCompany(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None

class RecruitUDocument(BaseModel):
    id: str
    full_name: Optional[str] = None
    current_company: Optional[RecruitUCompany] = None
    previous_companies: Optional[str] = None
    previous_titles: Optional[str] = None
    school: Optional[str] = None
    title: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    page_num: int
    num_pages: int
    num_items: int
    num_items_on_page: int
    results: List[T]


class CandidateScore(BaseModel):
    candidate_id: str
    total_score: float
    factors: Dict[FactorName, float] = Field(default_factory=dict)
    document: RecruitUDocument


class UploadResponse(BaseModel):
    query_plan: SimilarityPlan
    parsed: ParsedResume
    results: List[CandidateScore]
