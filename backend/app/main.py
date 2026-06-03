from fastapi import FastAPI
from .database import Base, engine
from . import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Review AI")


@app.get("/")
def root():
    return {"message": "Expense Review AI backend is running"}
