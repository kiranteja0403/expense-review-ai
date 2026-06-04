import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.database import SessionLocal
from backend.app.models import ReviewResult
from backend.app.utils import (
    retrieve_policy_chunks,
    is_policy_question_out_of_scope,
    validate_citation_quote,
)


def run_eval():
    db = SessionLocal()

    reviews = db.query(ReviewResult).all()
    total_reviews = len(reviews)

    verdict_counts = {}
    citation_nonempty = 0
    citation_valid = 0
    citation_total = 0

    for review in reviews:
        verdict_counts[review.verdict] = verdict_counts.get(review.verdict, 0) + 1

        citations = json.loads(review.citations_json) if review.citations_json else []
        if len(citations) > 0:
            citation_nonempty += 1

        for citation in citations:
            citation_total += 1
            quote = citation.get("quote", "")
            if quote:
                citation_valid += 1

    sample_questions = [
        "Are alcoholic drinks reimbursable during travel?",
        "Is economy class expected for airfare?",
        "Can hotel expenses be reimbursed?",
        "Who won the world cup in 2011?"
    ]

    qa_results = []
    refusal_count = 0

    for question in sample_questions:
        out_of_scope = is_policy_question_out_of_scope(question)
        matches = retrieve_policy_chunks(question, top_k=3) if not out_of_scope else []

        if out_of_scope:
            refusal_count += 1

        qa_results.append({
            "question": question,
            "out_of_scope": out_of_scope,
            "retrieved_chunks": len(matches)
        })

    results = {
        "total_reviews": total_reviews,
        "verdict_counts": verdict_counts,
        "citation_nonempty_rate": (
            citation_nonempty / total_reviews if total_reviews > 0 else 0
        ),
        "citation_validity_rate": (
            citation_valid / citation_total if citation_total > 0 else 0
        ),
        "qa_eval": qa_results,
        "refusal_count": refusal_count
    }

    output_path = os.path.join("backend", "eval", "results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    db.close()

    print(json.dumps(results, indent=2))
    print(f"\nSaved eval results to {output_path}")


if __name__ == "__main__":
    run_eval()
