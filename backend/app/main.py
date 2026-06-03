import json
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .utils import retrieve_policy_chunks
from datetime import datetime



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
