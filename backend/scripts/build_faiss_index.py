import os
import sys
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.database import SessionLocal
from backend.app.models import PolicyChunk

INDEX_PATH = os.path.join("backend", "data", "policy_index.faiss")
META_PATH = os.path.join("backend", "data", "policy_index_meta.json")


def build_index():
    db = SessionLocal()
    chunks = db.query(PolicyChunk).all()

    texts = [chunk.chunk_text for chunk in chunks]
    ids = [chunk.id for chunk in chunks]

    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(texts, show_progress_bar=True)

    embeddings = np.array(embeddings).astype("float32")

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)

    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump({"chunk_ids": ids}, f)

    db.close()
    print(f"Saved FAISS index to {INDEX_PATH}")
    print(f"Saved metadata to {META_PATH}")


if __name__ == "__main__":
    build_index()
