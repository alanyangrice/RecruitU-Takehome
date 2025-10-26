from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class Education(BaseModel):
    school: Optional[str] = None

class TargetProfile(BaseModel):
    full_name: Optional[str] = None
    headline: Optional[str] = None
    total_years_experience: Optional[float] = None
    locations: List[str] = []
    current_company: Optional[str] = None
    current_title: Optional[str] = None
    total_years_experience: Optional[float] = None
    education: List[Education] = []

class Candidate(BaseModel):
    id: str
    summary: Optional[str] = None
    profile: Dict

class CandidateScores(BaseModel):
    current_experience: float
    previous_experience: float
    title: float
    school: float
    years_experience: float

class ScoredCandidate(BaseModel):
    candidate: Candidate
    scores: CandidateScores
    composite: float

class UploadResumeResponse(BaseModel):
    targetId: str
    targetProfile: TargetProfile
    rawText: Optional[str] = None
    results: List[ScoredCandidate] = []

class SimilaritySpec(BaseModel):
    companies: Dict[str, float] = {}
    titles: Dict[str, float] = {}
    schools: Dict[str, float] = {}
    yoe_target: Optional[float] = None  # total years of experience target
    yoe_score1_max_diff: float = 1.0   # |diff| <= this -> 1.0
    yoe_score0_5_max_diff: float = 3.0 # |diff| <= this -> 0.5
