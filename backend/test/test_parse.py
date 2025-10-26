from __future__ import annotations
import os
import json
from app.services.parse_profile import parse_resume_text, build_similarity_plan


def main() -> None:
    # Load sample resume text
    sample_path = os.path.join(os.path.dirname(__file__), "sample_resume_investment_banking.txt")
    with open(sample_path, "r", encoding="utf-8") as f:
        text = f.read()

    parsed = parse_resume_text(text)
    plan = build_similarity_plan(parsed)

    print("ParsedResume JSON:")
    print(json.dumps(parsed.model_dump(), indent=2))
    print("\nSimilarityPlan JSON:")
    print(json.dumps(plan.model_dump(), indent=2))


if __name__ == "__main__":
    main()


