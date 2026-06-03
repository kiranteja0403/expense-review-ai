import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.database import SessionLocal
from backend.app.models import PolicyChunk
from backend.app.utils import extract_text_from_pdf

POLICIES_DIR = os.path.join("backend", "data", "policies")


def chunk_text(text, chunk_size=1000, overlap=200):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


def ingest_policies():
    db = SessionLocal()

    db.query(PolicyChunk).delete()
    db.commit()

    print(f"Looking inside policies dir: {POLICIES_DIR}")

    for filename in os.listdir(POLICIES_DIR):
        if not filename.lower().endswith(".pdf"):
            continue

        file_path = os.path.join(POLICIES_DIR, filename)
        print(f"\nProcessing policy: {filename}")

        text = extract_text_from_pdf(file_path)
        print(f"Extracted text length: {len(text)}")

        if not text:
            print(f"No text found in {filename}")
            continue

        chunks = chunk_text(text)
        print(f"Generated {len(chunks)} chunks")

        for i, chunk in enumerate(chunks):
            policy_chunk = PolicyChunk(
                document_name=filename,
                page=None,
                section=f"chunk_{i+1}",
                chunk_text=chunk,
                embedding_ref=None,
            )
            db.add(policy_chunk)

        db.commit()
        print(f"Ingested {filename} with {len(chunks)} chunks")

    db.close()
    print("\nPolicy ingestion completed.")


if __name__ == "__main__":
    ingest_policies()
