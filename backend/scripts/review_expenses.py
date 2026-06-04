import os
import sys
import json
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.database import SessionLocal
from backend.app.models import ExpenseItem, ReviewResult, Submission, Trip
from backend.app.utils import retrieve_policy_chunks


def parse_date_safe(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return None


def simple_review(item, trip):
    matches = retrieve_policy_chunks(
        f"{item.category or ''} {item.merchant or ''} {item.raw_text or ''}",
        top_k=3
    )

    verdict = "ambiguous"
    reasoning = "Insufficient evidence for a deterministic decision."
    confidence = 0.5
    needs_human_review = True

    text = (item.raw_text or "").lower()
    amount = item.amount or 0.0

    item_date = parse_date_safe(item.date)
    trip_start = parse_date_safe(trip.start_date if trip else None)
    trip_end = parse_date_safe(trip.end_date if trip else None)

    if item_date and trip_start and trip_end:
        if item_date < trip_start or item_date > trip_end:
            verdict = "likely_violation"
            reasoning = "Expense date falls outside the trip date range."
            confidence = 0.9
            needs_human_review = True

    if verdict == "ambiguous":
        if item.category == "meal":
            if "beer" in text or "wine" in text or "cocktail" in text or "vodka" in text:
                verdict = "likely_violation"
                reasoning = "Meal receipt appears to include alcohol, which may violate policy."
                confidence = 0.85
                needs_human_review = True
            elif amount > 75:
                verdict = "likely_violation"
                reasoning = "Meal total appears above a likely per-meal cap."
                confidence = 0.8
                needs_human_review = True
            elif matches:
                verdict = "compliant"
                reasoning = "Retrieved relevant policy evidence for meal expense."
                confidence = 0.7
                needs_human_review = False

        elif item.category == "air_travel":
            if "business" in text or "first" in text:
                verdict = "likely_violation"
                reasoning = "Airfare may be non-economy class and requires review."
                confidence = 0.8
                needs_human_review = True
            elif matches:
                verdict = "compliant"
                reasoning = "Retrieved relevant policy evidence for air travel expense."
                confidence = 0.7
                needs_human_review = False

        elif item.category in ["lodging", "ground_transport"]:
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
        submission = db.query(Submission).filter(Submission.id == item.submission_id).first()
        trip = db.query(Trip).filter(Trip.id == submission.trip_id).first() if submission else None

        result = simple_review(item, trip)

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
