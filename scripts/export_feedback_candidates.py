from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.feedback.feedback_store import NEGATIVE_CATEGORIES, list_feedback

OUTPUT_PATH = ROOT / "data" / "evaluation" / "feedback-candidates.json"

CATEGORY_TO_QUESTION_TYPE: dict[str, str] = {
    "incorrect_answer": "answer_quality",
    "missing_citation": "citation_quality",
    "wrong_citation": "citation_quality",
    "hallucination": "faithfulness",
    "refused_incorrectly": "permission_restricted",
    "not_found_incorrectly": "missing_information",
    "permission_issue": "permission_restricted",
    "unclear_answer": "answer_quality",
    "should_have_refused": "permission_restricted",
}


def main() -> None:
    items = list_feedback(rating="thumbs_down", limit=1000)
    candidates = []
    for item in items:
        if item["feedback_category"] not in NEGATIVE_CATEGORIES:
            continue
        candidates.append(
            {
                "original_question": item["question"],
                "bad_answer": item["answer"],
                "user_comment": item.get("user_comment"),
                "feedback_category": item["feedback_category"],
                "suggested_question_type": CATEGORY_TO_QUESTION_TYPE.get(
                    item["feedback_category"], "answer_quality"
                ),
                "needs_human_review": True,
                "source_session_id": item.get("session_id"),
                "feedback_id": item["feedback_id"],
                "created_at": str(item["created_at"]),
            }
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(candidates, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {len(candidates)} candidate(s) to {OUTPUT_PATH}")
    print("NOTE: All candidates have needs_human_review=true. Review before adding to benchmark-questions.json.")


if __name__ == "__main__":
    main()
