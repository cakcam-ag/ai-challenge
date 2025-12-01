"""
Day 14 — Document Indexing (reused from Day 13)
Core indexing logic: chunk → embed → store in FAISS
"""

import os
import json
import faiss
import numpy as np
from typing import List, Dict
import requests
import tiktoken
from dotenv import load_dotenv

load_dotenv()

# ------------------------------
# Configuration
# ------------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "data/docs")
STORAGE_DIR = os.path.join(os.path.dirname(__file__), "storage")
INDEX_PATH = os.path.join(STORAGE_DIR, "faiss.index")
CHUNKS_PATH = os.path.join(STORAGE_DIR, "chunks.json")

EMBED_MODEL = "text-embedding-3-large"
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

def openai_headers():
    """Get headers for OpenAI API requests."""
    return {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

tokenizer = tiktoken.get_encoding("cl100k_base")


# ------------------------------
# Utility: chunk text
# ------------------------------
def chunk_text(text: str, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP) -> List[str]:
    tokens = tokenizer.encode(text)
    chunks = []

    start = 0
    while start < len(tokens):
        end = start + chunk_size
        chunk = tokenizer.decode(tokens[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


# ------------------------------
# Utility: embed text
# ------------------------------
def embed(texts: List[str]) -> List[List[float]]:
    """Generate embeddings using OpenAI API via HTTP."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    url = "https://api.openai.com/v1/embeddings"
    payload = {
        "model": EMBED_MODEL,
        "input": texts
    }
    
    response = requests.post(url, headers=openai_headers(), json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    
    return [item["embedding"] for item in data["data"]]


# ------------------------------
# Load documents
# ------------------------------
def load_documents() -> Dict[str, str]:
    docs = {}
    if not os.path.exists(DATA_DIR):
        return docs
    
    for root, _, files in os.walk(DATA_DIR):
        for f in files:
            if f.lower().endswith((".txt", ".md")):
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                        docs[f] = fp.read()
                except Exception as e:
                    print(f"Error reading {path}: {e}")
    return docs


# ------------------------------
# Build index from scratch
# ------------------------------
def build_index():
    os.makedirs(STORAGE_DIR, exist_ok=True)

    docs = load_documents()
    if not docs:
        raise Exception(f"No documents found in {DATA_DIR}. Add .txt or .md files there.")

    print(f"Loaded {len(docs)} documents")

    chunks = []
    metadata = []

    # Chunk every document
    for filename, text in docs.items():
        file_chunks = chunk_text(text)
        for chunk in file_chunks:
            chunks.append(chunk)
            metadata.append({"file": filename})

    print(f"Generated {len(chunks)} total chunks")

    if not chunks:
        raise Exception("No chunks generated from documents.")

    # Embed
    vectors = embed(chunks)
    vectors_np = np.array(vectors).astype("float32")

    dim = vectors_np.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors_np)

    faiss.write_index(index, INDEX_PATH)
    print("FAISS index saved.")

    with open(CHUNKS_PATH, "w", encoding="utf-8") as fp:
        json.dump(
            [{"text": t, "meta": m} for t, m in zip(chunks, metadata)],
            fp,
            ensure_ascii=False,
            indent=2
        )

    print("Chunk metadata saved.")
    return True


# ------------------------------
# Query Search
# ------------------------------
def query_index(query: str, top_k=5):
    if not os.path.exists(INDEX_PATH):
        raise Exception("Index not built. Call /reindex first.")

    index = faiss.read_index(INDEX_PATH)

    with open(CHUNKS_PATH, "r", encoding="utf-8") as fp:
        chunks = json.load(fp)

    query_vec = embed([query])[0]
    q_np = np.array([query_vec]).astype("float32")

    distances, ids = index.search(q_np, top_k)

    results = []
    for idx, dist in zip(ids[0], distances[0]):
        if idx == -1:
            continue
        results.append({
            "score": float(dist),
            "chunk": chunks[idx]["text"],
            "meta": chunks[idx]["meta"]
        })

    return results

