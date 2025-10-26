from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class Education(BaseModel):
    school: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    grad_year: Optional[int] = None

class CompanyRole(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    seniority: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None

class TargetProfile(BaseModel):
    full_name: Optional[str] = None
    headline: Optional[str] = None
    total_years_experience: Optional[float] = None
    locations: List[str] = []
    current_company: Optional[str] = None
    current_title: Optional[str] = None
    sector: Optional[str] = None
    skills: List[str] = []
    education: List[Education] = []
    companies_of_interest: List[str] = []
    roles_of_interest: List[str] = []
    degrees_of_interest: List[str] = []

class WeightMap(BaseModel):
    education: float = 1.0
    companies: float = 1.0
    title_seniority: float = 1.0
    years_experience: float = 1.0
    location: float = 1.0
    sector: float = 0.8
    skills: float = 0.8

class Candidate(BaseModel):
    id: str
    summary: Optional[str] = None
    profile: Dict

class CandidateScores(BaseModel):
    education: float
    companies: float
    title_seniority: float
    years_experience: float
    location: float
    sector: float
    skills: float

class ScoredCandidate(BaseModel):
    candidate: Candidate
    scores: CandidateScores
    composite: float

class UploadResumeResponse(BaseModel):
    targetId: str
    targetProfile: TargetProfile
    rawText: Optional[str] = None

class RankRequest(BaseModel):
    targetId: Optional[str] = None
    targetProfile: Optional[TargetProfile] = None
    weights: WeightMap = Field(default_factory=WeightMap)
    topK: int = 100
    maxPages: int = 3
    countPerPage: int = 20

class RankResponse(BaseModel):
    searchId: str
    results: List[ScoredCandidate]

class ReRankRequest(BaseModel):
    searchId: str
    weights: WeightMap

# Similarity specification produced by LLM to guide deterministic scoring
class SimilaritySpec(BaseModel):
    companies: Dict[str, float] = {}
    titles: Dict[str, float] = {}
    schools: Dict[str, float] = {}
    locations: Dict[str, float] = {}
    sectors: Dict[str, float] = {}
    skills: Dict[str, float] = {}
    yoe_target: Optional[float] = None  # total years of experience target
    yoe_tolerance_years: float = 3.0
