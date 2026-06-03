from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
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
