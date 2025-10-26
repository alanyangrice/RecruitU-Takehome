from __future__ import annotations
import os
import json
import asyncio
from app.services.parse_profile import parse_resume_text, build_similarity_plan
from app.services.recruitu import RecruitUClient
from app.services.scoring import aggregate_and_score


async def run() -> None:
    sample_path = os.path.join(os.path.dirname(__file__), "sample_resume_investment_banking.txt")
    with open(sample_path, "r", encoding="utf-8") as f:
        text = f.read()

    parsed = parse_resume_text(text)
    plan = build_similarity_plan(parsed)

    client = RecruitUClient()
    results, stats = await aggregate_and_score(client, parsed, plan, return_stats=True)

    print("ParsedResume:")
    print(json.dumps(parsed.model_dump(), indent=2))
    print("\nSet sizes and totals:")
    print(json.dumps(stats, indent=2))

    print("\nTop results (first 10):")
    out = [
        {
            "candidate_id": r.candidate_id,
            "total_score": r.total_score,
            "full_name": r.document.full_name,
            "current_company": getattr(r.document.current_company, "company", None) if r.document.current_company else None,
            "title": r.document.title or (getattr(r.document.current_company, "title", None) if r.document.current_company else None),
        }
        for r in results[:100]
    ]
    print(json.dumps(out, indent=2))

    # Detailed dump for a chosen candidate id
    target_id = os.getenv("CANDIDATE_ID") or (results[0].candidate_id if results else None)
    if target_id:
        target = next((r for r in results if r.candidate_id == target_id), None)
        print("\nDetailed candidate view (from search + scoring):")
        if target:
            print(json.dumps({
                "candidate_id": target.candidate_id,
                "total_score": target.total_score,
                "factors": target.factors,
                "document": target.document.model_dump(),
            }, indent=2))


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()


