import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.database import SessionLocal
from backend.app.models import ExpenseItem, ReviewResult
from backend.app.utils import retrieve_policy_chunks


def simple_review(item):
    matches = retrieve_policy_chunks(
        f"{item.category or ''} {item.merchant or ''} {item.raw_text or ''}",
        top_k=3
    )

    verdict = "ambiguous"
    reasoning = "Insufficient evidence for a deterministic decision."
    confidence = 0.5
    needs_human_review = True

    if item.category in ["air_travel", "lodging", "ground_transport", "meal"]:
        if matches:
            verdict = "compliant"
            reasoning = f"Retrieved relevant policy evidence for {item.category} expense."
            confidence = 0.7
            needs_human_review = False

    citations = [
        {
            "document_name": m["document_name"],
            "section": m["section"],
            "quote": m["chunk_text"][:300]
        }
        for m in matches
    ]

    return {
        "verdict": verdict,
        "reasoning": reasoning,
        "confidence": confidence,
        "needs_human_review": needs_human_review,
        "citations": citations
    }


def review_expenses():
    db = SessionLocal()

    db.query(ReviewResult).delete()
    db.commit()

    items = db.query(ExpenseItem).all()

    for item in items:
        result = simple_review(item)

        review = ReviewResult(
            expense_item_id=item.id,
            verdict=result["verdict"],
            reasoning=result["reasoning"],
            confidence=result["confidence"],
            citations_json=json.dumps(result["citations"]),
            needs_human_review=result["needs_human_review"]
        )

        db.add(review)
        print(f"Reviewed: {item.file_name} -> {result['verdict']}")

    db.commit()
    db.close()
    print("Expense review completed.")


if __name__ == "__main__":
    review_expenses()
