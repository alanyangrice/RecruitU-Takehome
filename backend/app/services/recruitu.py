from __future__ import annotations
from typing import List, Dict, Any, Set
import asyncio
import httpx
from ..config import settings
from ..schemas.types import Candidate


async def _search_once(client: httpx.AsyncClient, params: Dict[str, Any]) -> List[Candidate]:
    if not settings.recruitu_base_url:
        return []
    url = settings.recruitu_base_url.rstrip("/") + "/search"
    r = await client.get(url, params=params, timeout=30.0)
    r.raise_for_status()
    data = r.json()
    results = data.get("results", [])
    candidates: list[Candidate] = []
    for item in results:
        cid = item.get("id") or item.get("document", {}).get("id")
        if cid:
            candidates.append(Candidate(id=str(cid), profile=item, summary=None))
    return candidates


async def search(queries: List[Dict[str, Any]], count_per_page: int = 20, max_pages: int = 3, top_k: int = 100) -> List[Candidate]:
    if not settings.recruitu_base_url:
        return []
    tasks = []
    async with httpx.AsyncClient() as client:
        for q in queries:
            for page in range(1, max_pages + 1):
                p = dict(q)
                p["count"] = count_per_page
                p["page"] = page
                tasks.append(_search_once(client, p))
        results_nested = await asyncio.gather(*tasks, return_exceptions=False)
    flat: list[Candidate] = [c for sub in results_nested for c in sub]
    seen: Set[str] = set()
    deduped: list[Candidate] = []
    for c in flat:
        if c.id not in seen:
            seen.add(c.id)
            deduped.append(c)
        if len(deduped) >= top_k:
            break
    return deduped
