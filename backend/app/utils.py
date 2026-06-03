import re
import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()


def extract_merchant(raw_text: str, category: str = None) -> str:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return None

    if category == "air_travel":
        for line in lines[:10]:
            if "united" in line.lower():
                return "United Airlines"

    if category == "lodging":
        for line in lines[:10]:
            if "marriott" in line.lower():
                return line

    if category == "ground_transport":
        for line in lines[:10]:
            if "uber" in line.lower():
                return "Uber"

    if category == "meal":
        for line in lines[:10]:
            lower = line.lower()
            if any(word in lower for word in ["mercantile", "snooze", "sushiden", "avanti"]):
                return line

    return lines[0]


def extract_amount(raw_text: str) -> float:
    patterns = [
        r"Total Charged\s*\$?([0-9,]+\.[0-9]{2})",
        r"Total charged\s*\$?([0-9,]+\.[0-9]{2})",
        r"TOTAL\s*\$?([0-9,]+\.[0-9]{2})",
        r"Total\s*\$?([0-9,]+\.[0-9]{2})",
        r"Amount\s*\$?([0-9,]+\.[0-9]{2})",
    ]

    for pattern in patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", ""))

    amounts = re.findall(r"\$([0-9,]+\.[0-9]{2})", raw_text)
    if amounts:
        return float(amounts[-1].replace(",", ""))

    return None


def extract_date(raw_text: str) -> str:
    patterns = [
        r"Charge Date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})",
        r"Issued:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})",
        r"Posted Date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})",
        r"Check-In:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})",
        r"Date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})",
        r"([0-9]{4}-[0-9]{2}-[0-9]{2})",
    ]

    for pattern in patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            return match.group(1)

    return None
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.app.database import SessionLocal
from backend.app.models import PolicyChunk

INDEX_PATH = "backend/data/policy_index.faiss"
META_PATH = "backend/data/policy_index_meta.json"

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def retrieve_policy_chunks(query_text: str, top_k: int = 3):
    if not query_text:
        return []

    index = faiss.read_index(INDEX_PATH)

    with open(META_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    chunk_ids = meta["chunk_ids"]

    query_embedding = embedding_model.encode([query_text])
    query_embedding = np.array(query_embedding).astype("float32")

    distances, indices = index.search(query_embedding, top_k)

    db = SessionLocal()
    results = []

    for idx in indices[0]:
        if idx < len(chunk_ids):
            chunk_id = chunk_ids[idx]
            chunk = db.query(PolicyChunk).filter(PolicyChunk.id == chunk_id).first()
            if chunk:
                results.append({
                    "id": chunk.id,
                    "document_name": chunk.document_name,
                    "section": chunk.section,
                    "chunk_text": chunk.chunk_text
                })

    db.close()
    return results
