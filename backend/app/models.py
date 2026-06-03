from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    grade = Column(String, nullable=True)
    title = Column(String, nullable=True)
    department = Column(String, nullable=True)
    manager_id = Column(String, nullable=True)
    home_base = Column(String, nullable=True)

    trips = relationship("Trip", back_populates="employee")


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    trip_purpose = Column(String, nullable=True)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)

    employee = relationship("Employee", back_populates="trips")
    submissions = relationship("Submission", back_populates="trip")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    folder_name = Column(String, nullable=True)
    status = Column(String, default="pending")

    trip = relationship("Trip", back_populates="submissions")
    expense_items = relationship("ExpenseItem", back_populates="submission")


class ExpenseItem(Base):
    __tablename__ = "expense_items"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    file_name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    merchant = Column(String, nullable=True)
    amount = Column(Float, nullable=True)
    date = Column(String, nullable=True)
    raw_text = Column(Text, nullable=True)

    submission = relationship("Submission", back_populates="expense_items")
    review_result = relationship("ReviewResult", back_populates="expense_item", uselist=False)
    overrides = relationship("Override", back_populates="expense_item")


class ReviewResult(Base):
    __tablename__ = "review_results"

    id = Column(Integer, primary_key=True, index=True)
    expense_item_id = Column(Integer, ForeignKey("expense_items.id"))
    verdict = Column(String, nullable=True)
    reasoning = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    citations_json = Column(Text, nullable=True)
    needs_human_review = Column(Boolean, default=True)

    expense_item = relationship("ExpenseItem", back_populates="review_result")


class Override(Base):
    __tablename__ = "overrides"

    id = Column(Integer, primary_key=True, index=True)
    expense_item_id = Column(Integer, ForeignKey("expense_items.id"))
    final_verdict = Column(String, nullable=True)
    reviewer_comment = Column(Text, nullable=True)
    created_at = Column(String, nullable=True)

    expense_item = relationship("ExpenseItem", back_populates="overrides")


class PolicyChunk(Base):
    __tablename__ = "policy_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_name = Column(String, nullable=False)
    page = Column(Integer, nullable=True)
    section = Column(String, nullable=True)
    chunk_text = Column(Text, nullable=False)
    embedding_ref = Column(String, nullable=True)
