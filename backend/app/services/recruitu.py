from __future__ import annotations
from typing import Any, Dict
import httpx
from ..config import settings
from ..schemas.types import PaginatedResponse, RecruitUDocument


class RecruitUClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.recruitu_base_url or "").rstrip("/")
        if not self.base_url:
            raise RuntimeError("RECRUITU_BASE_URL not configured")

    async def search(self, params: Dict[str, Any]) -> PaginatedResponse[RecruitUDocument]:
        """Query the RecruitU search API and return a paginated response of documents."""
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(f"{self.base_url}/search", params=params)
            resp.raise_for_status()
            data = resp.json()
            # Unwrap nested { id, document: {...} } into flat RecruitUDocument objects
            results = data.get("results", [])
            unwrapped: list[dict] = []
            for item in results:
                doc = (item or {}).get("document") or {}
                if isinstance(doc, dict):
                    if "id" not in doc and "id" in item:
                        doc["id"] = item.get("id")
                    unwrapped.append(doc)
            data["results"] = unwrapped
            return PaginatedResponse[RecruitUDocument].model_validate(data)
