Expense Review AI

An AI-powered expense report pre-review system that ingests company policy PDFs and employee expense submissions, extracts receipt data, retrieves relevant policy evidence, and produces line-item review results with reasoning, citations, and human override support.

Implemented Features

- Seeded employee, trip, and submission ingestion from provided sample folders
- Receipt registration as expense items
- PDF receipt text extraction using PyMuPDF
- Structured receipt field extraction:
  - merchant
  - amount
  - date
  - category
- Policy PDF ingestion and chunking
- FAISS-based policy retrieval using sentence-transformers embeddings
- Initial review pipeline with:
  - rule-based checks
  - retrieval-backed citations
  - verdicts:
    - compliant
    - likely_violation
    - ambiguous
- Reviewer override API with persisted audit trail
- Submission detail API combining:
  - employee
  - trip
  - expense items
  - review results
  - overrides

Project Structure

```bash
backend/
  app/
    main.py
    database.py
    models.py
    schemas.py
    config.py
    utils.py
  data/
    policies/
    submissions/
    uploads/
    policy_index.faiss
    policy_index_meta.json
  scripts/
    seed_data.py
    process_receipts.py
    extract_receipt_fields.py
    ingest_policies.py
    build_faiss_index.py
    review_expenses.py
  eval/
  requirements.txt
frontend/
README.md
Note: if demo data is reseeded multiple times during development, duplicate submission rows may appear in history. Deleting `expense_review.db` and rerunning setup scripts resets local demo state.
