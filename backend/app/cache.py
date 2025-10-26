from __future__ import annotations
from typing import Dict, List, Any
from .schemas.types import TargetProfile, Candidate, ScoredCandidate

class InMemoryStore:
    def __init__(self) -> None:
        self.targets: Dict[str, TargetProfile] = {}
        self.search_candidates: Dict[str, List[Candidate]] = {}
        self.search_scored: Dict[str, List[ScoredCandidate]] = {}
        self.meta: Dict[str, Any] = {}

store = InMemoryStore()
