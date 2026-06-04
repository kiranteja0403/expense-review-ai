import json
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .utils import retrieve_policy_chunks
from datetime import datetime
from .utils import retrieve_policy_chunks




from .database import Base, engine, get_db
from . import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Review AI")


@app.get("/")
def root():
    return {"message": "Expense Review AI backend is running"}


@app.get("/employees")
def get_employees(db: Session = Depends(get_db)):
    employees = db.query(models.Employee).all()
    return [
        {
            "id": e.id,
            "employee_id": e.employee_id,
            "name": e.name,
            "grade": e.grade,
            "title": e.title,
            "department": e.department,
            "manager_id": e.manager_id,
            "home_base": e.home_base,
        }
        for e in employees
    ]


@app.get("/submissions")
def get_submissions(db: Session = Depends(get_db)):
    submissions = db.query(models.Submission).all()
    return [
        {
            "id": s.id,
            "trip_id": s.trip_id,
            "folder_name": s.folder_name,
            "status": s.status,
        }
        for s in submissions
    ]


@app.get("/expense-items")
def get_expense_items(db: Session = Depends(get_db)):
    items = db.query(models.ExpenseItem).all()
    return [
        {
            "id": item.id,
            "submission_id": item.submission_id,
            "file_name": item.file_name,
            "category": item.category,
            "merchant": item.merchant,
            "amount": item.amount,
            "date": item.date,
        }
        for item in items
    ]
@app.get("/expense-items/{item_id}")
def get_expense_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.ExpenseItem).filter(models.ExpenseItem.id == item_id).first()

    if not item:
        return {"error": "Expense item not found"}

    return {
        "id": item.id,
        "submission_id": item.submission_id,
        "file_name": item.file_name,
        "category": item.category,
        "merchant": item.merchant,
        "amount": item.amount,
        "date": item.date,
        "raw_text": item.raw_text,
    }
@app.get("/policy-chunks")
def get_policy_chunks(db: Session = Depends(get_db)):
    chunks = db.query(models.PolicyChunk).all()
    return [
        {
            "id": chunk.id,
            "document_name": chunk.document_name,
            "section": chunk.section,
            "chunk_preview": chunk.chunk_text[:200]
        }
        for chunk in chunks
    ]
@app.get("/expense-items/{item_id}/policy-match")
def get_policy_match(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.ExpenseItem).filter(models.ExpenseItem.id == item_id).first()

    if not item:
        return {"error": "Expense item not found"}

    query_text = f"{item.category or ''} {item.merchant or ''} {item.raw_text or ''}"
    matches = retrieve_policy_chunks(query_text, top_k=3)

    return {
        "expense_item_id": item.id,
        "file_name": item.file_name,
        "category": item.category,
        "merchant": item.merchant,
        "policy_matches": matches
    }
@app.get("/reviews")
def get_reviews(db: Session = Depends(get_db)):
    reviews = db.query(models.ReviewResult).all()
    return [
        {
            "id": r.id,
            "expense_item_id": r.expense_item_id,
            "verdict": r.verdict,
            "reasoning": r.reasoning,
            "confidence": r.confidence,
            "citations": json.loads(r.citations_json) if r.citations_json else [],
            "needs_human_review": r.needs_human_review,
        }
        for r in reviews
    ]
@app.get("/reviews/{expense_item_id}")
def get_review_by_expense_item(expense_item_id: int, db: Session = Depends(get_db)):
    review = db.query(models.ReviewResult).filter(
        models.ReviewResult.expense_item_id == expense_item_id
    ).first()

    if not review:
        return {"error": "Review not found"}

    return {
        "id": review.id,
        "expense_item_id": review.expense_item_id,
        "verdict": review.verdict,
        "reasoning": review.reasoning,
        "confidence": review.confidence,
        "citations": json.loads(review.citations_json) if review.citations_json else [],
        "needs_human_review": review.needs_human_review,
    }
@app.post("/expense-items/{item_id}/override")
def override_review(
    item_id: int,
    final_verdict: str,
    reviewer_comment: str,
    db: Session = Depends(get_db)
):
    item = db.query(models.ExpenseItem).filter(models.ExpenseItem.id == item_id).first()

    if not item:
        return {"error": "Expense item not found"}

    override = models.Override(
        expense_item_id=item.id,
        final_verdict=final_verdict,
        reviewer_comment=reviewer_comment,
        created_at=datetime.utcnow().isoformat()
    )
    db.add(override)
    db.commit()
    db.refresh(override)

    return {
        "message": "Override saved",
        "override_id": override.id,
        "expense_item_id": override.expense_item_id,
        "final_verdict": override.final_verdict,
        "reviewer_comment": override.reviewer_comment,
        "created_at": override.created_at,
    }


@app.get("/expense-items/{item_id}/overrides")
def get_overrides(item_id: int, db: Session = Depends(get_db)):
    overrides = db.query(models.Override).filter(
        models.Override.expense_item_id == item_id
    ).all()

    return [
        {
            "id": o.id,
            "expense_item_id": o.expense_item_id,
            "final_verdict": o.final_verdict,
            "reviewer_comment": o.reviewer_comment,
            "created_at": o.created_at,
        }
        for o in overrides
    ]
@app.get("/submissions/{submission_id}/detail")
def get_submission_detail(submission_id: int, db: Session = Depends(get_db)):
    submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()

    if not submission:
        return {"error": "Submission not found"}

    trip = db.query(models.Trip).filter(models.Trip.id == submission.trip_id).first()
    employee = db.query(models.Employee).filter(models.Employee.id == trip.employee_id).first() if trip else None

    items = db.query(models.ExpenseItem).filter(models.ExpenseItem.submission_id == submission.id).all()

    result_items = []
    for item in items:
        review = db.query(models.ReviewResult).filter(
            models.ReviewResult.expense_item_id == item.id
        ).first()

        overrides = db.query(models.Override).filter(
            models.Override.expense_item_id == item.id
        ).all()

        result_items.append({
            "expense_item_id": item.id,
            "file_name": item.file_name,
            "category": item.category,
            "merchant": item.merchant,
            "amount": item.amount,
            "date": item.date,
            "review": {
                "verdict": review.verdict if review else None,
                "reasoning": review.reasoning if review else None,
                "confidence": review.confidence if review else None,
                "needs_human_review": review.needs_human_review if review else None,
                "citations": json.loads(review.citations_json) if review and review.citations_json else []
            } if review else None,
            "overrides": [
                {
                    "id": o.id,
                    "final_verdict": o.final_verdict,
                    "reviewer_comment": o.reviewer_comment,
                    "created_at": o.created_at,
                }
                for o in overrides
            ]
        })

    return {
        "submission_id": submission.id,
        "folder_name": submission.folder_name,
        "status": submission.status,
        "employee": {
            "employee_id": employee.employee_id if employee else None,
            "name": employee.name if employee else None,
            "grade": employee.grade if employee else None,
            "title": employee.title if employee else None,
            "department": employee.department if employee else None,
            "home_base": employee.home_base if employee else None,
        },
        "trip": {
            "trip_purpose": trip.trip_purpose if trip else None,
            "start_date": trip.start_date if trip else None,
            "end_date": trip.end_date if trip else None,
        },
        "expense_items": result_items
    }
@app.get("/policy-qa")
def policy_qa(question: str, db: Session = Depends(get_db)):
    matches = retrieve_policy_chunks(question, top_k=3)

    if not matches:
        return {
            "question": question,
            "answer": "I don't know based on the provided policy documents.",
            "citations": []
        }

    answer = "Based on the retrieved policy text, the most relevant guidance is shown in the cited policy chunks."
    citations = [
        {
            "document_name": m["document_name"],
            "section": m["section"],
            "quote": m["chunk_text"][:300]
        }
        for m in matches
    ]

    return {
        "question": question,
        "answer": answer,
        "citations": citations
    }
@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "Expense Review AI backend is healthy"
    }


@app.get("/submissions/by-folder/{folder_name}")
def get_submission_by_folder(folder_name: str, db: Session = Depends(get_db)):
    submission = db.query(models.Submission).filter(
        models.Submission.folder_name == folder_name
    ).first()

    if not submission:
        return {"error": "Submission not found"}

    return {
        "submission_id": submission.id,
        "folder_name": submission.folder_name,
        "status": submission.status
    }
