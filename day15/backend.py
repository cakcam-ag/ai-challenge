import os
import json
import math
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

_client = None

def get_client():
    """Lazy initialization of AsyncOpenAI client to avoid import-time errors."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        _client = AsyncOpenAI(api_key=api_key)
    return _client

INDEX_FILE = "rag_index.json"
DOCS_DIR = os.path.join("data", "docs")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# in-memory cache
RAG_INDEX: Dict[str, Any] = {"chunks": []}


# -------------------------------------------------------
# INDEX LOAD / SAVE
# -------------------------------------------------------

def load_index() -> Dict[str, Any]:
    global RAG_INDEX
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # ensure embedding values are floats
        for ch in data.get("chunks", []):
            ch["embedding"] = [float(x) for x in ch.get("embedding", [])]
        RAG_INDEX = data
    else:
        RAG_INDEX = {"chunks": []}
    return RAG_INDEX


def save_index(index: Dict[str, Any]) -> None:
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)


# -------------------------------------------------------
# EMBEDDINGS / SIMILARITY
# -------------------------------------------------------

async def embed_text(text: str) -> List[float]:
    """Get a unit-norm embedding for text."""
    client = get_client()
    try:
        resp = await client.embeddings.create(
            model="text-embedding-3-small",
            input=[text],
        )
        vec = resp.data[0].embedding
        # L2-normalize so cosine = dot
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]
    except Exception as e:
        raise Exception(f"Embedding error: {str(e)}")


def cosine_sim(a: List[float], b: List[float]) -> float:
    return float(sum(x * y for x, y in zip(a, b)))


# -------------------------------------------------------
# LLM HELPERS
# -------------------------------------------------------

async def ask_llm_no_rag(question: str) -> str:
    """Plain answer, no retrieved context."""
    client = get_client()
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": question}
            ],
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"LLM error: {str(e)}")


async def ask_llm_with_rag(question: str, chunks: List[Dict[str, Any]]) -> str:
    """Answer using retrieved chunks as context."""
    context_texts = [f"[{c['doc']} #{c['chunk_index']}] {c['text']}" for c in chunks]
    context_block = "\n\n".join(context_texts)

    prompt = (
        "You are a helpful assistant using RAG.\n"
        "You are given CONTEXT extracted from local documents.\n"
        "Use it when relevant. If you don't see an answer in the context, say so.\n\n"
        f"CONTEXT:\n{context_block}\n\n"
        f"QUESTION: {question}"
    )

    client = get_client()
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"LLM error: {str(e)}")


# -------------------------------------------------------
# INDEXING
# -------------------------------------------------------

def chunk_text(text: str, max_chars: int = 800) -> List[str]:
    """Simple character-based chunking with paragraph boundaries when possible."""
    chunks: List[str] = []
    buf = ""

    for line in text.splitlines():
        if len(buf) + len(line) + 1 > max_chars:
            if buf.strip():
                chunks.append(buf.strip())
            buf = line + "\n"
        else:
            buf += line + "\n"

    if buf.strip():
        chunks.append(buf.strip())

    return chunks


@app.post("/reindex")
async def reindex_endpoint():
    """
    Walks data/docs directory, reads .txt/.md files,
    chunks them, embeds each chunk, and stores in rag_index.json
    """
    os.makedirs(DOCS_DIR, exist_ok=True)

    chunks: List[Dict[str, Any]] = []
    doc_count = 0
    chunk_id = 0

    for root, _, files in os.walk(DOCS_DIR):
        for fname in files:
            if not fname.lower().endswith((".txt", ".md")):
                continue
            doc_count += 1
            path = os.path.join(root, fname)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

            for i, ch_text in enumerate(chunk_text(text)):
                embedding = await embed_text(ch_text)
                rel = os.path.relpath(path, DOCS_DIR)
                chunks.append(
                    {
                        "id": f"chunk-{chunk_id}",
                        "doc": rel,
                        "chunk_index": i,
                        "text": ch_text,
                        "embedding": embedding,
                    }
                )
                chunk_id += 1

    index = {"chunks": chunks, "doc_count": doc_count}
    save_index(index)
    load_index()  # refresh cache

    return {
        "success": True,
        "doc_count": doc_count,
        "chunk_count": len(chunks),
        "message": f"Indexed {doc_count} docs into {len(chunks)} chunks.",
    }


# -------------------------------------------------------
# RETRIEVAL + RERANK / FILTER
# -------------------------------------------------------

async def retrieve_chunks(
    question: str,
    top_k: int = 8,
    similarity_threshold: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Retrieve chunks for a question.
    - Always sort by similarity descending.
    - If similarity_threshold is not None, drop chunks below it.
    """
    index = RAG_INDEX if RAG_INDEX["chunks"] else load_index()
    if not index["chunks"]:
        return {"chunks": [], "all_scores": []}

    q_emb = await embed_text(question)

    scored: List[Dict[str, Any]] = []
    for ch in index["chunks"]:
        score = cosine_sim(q_emb, ch["embedding"])
        scored.append({"chunk": ch, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:top_k]

    if similarity_threshold is not None:
        top = [s for s in top if s["score"] >= similarity_threshold]

    used_chunks = [
        {
            "doc": s["chunk"]["doc"],
            "chunk_index": s["chunk"]["chunk_index"],
            "text": s["chunk"]["text"],
            "score": s["score"],
        }
        for s in top
    ]

    all_scores = [float(s["score"]) for s in scored]

    return {"chunks": used_chunks, "all_scores": all_scores}


# -------------------------------------------------------
# QUESTION ENDPOINT
# -------------------------------------------------------

@app.post("/ask")
async def ask_endpoint(req: Request):
    """
    Body:
    {
      "question": "...",
      "mode": "compare" | "plain" | "rag_unfiltered" | "rag_filtered",
      "top_k": 8,
      "threshold": 0.35
    }
    """
    body = await req.json()
    question = (body.get("question") or "").strip()
    if not question:
        return {"success": False, "error": "question is required"}

    mode = body.get("mode", "compare")
    top_k = int(body.get("top_k", 8))
    threshold = body.get("threshold", 0.35)
    try:
        threshold = float(threshold)
    except Exception:
        threshold = 0.35

    result: Dict[str, Any] = {
        "success": True,
        "question": question,
        "top_k": top_k,
        "threshold": threshold,
    }

    # always compute retrieval once (for compare modes)
    retrieval_unfiltered = await retrieve_chunks(question, top_k=top_k, similarity_threshold=None)
    retrieval_filtered = await retrieve_chunks(question, top_k=top_k, similarity_threshold=threshold)

    if mode == "plain":
        ans_plain = await ask_llm_no_rag(question)
        result.update(
            {
                "mode": "plain",
                "answer_plain": ans_plain,
            }
        )
    elif mode == "rag_unfiltered":
        ans_rag = await ask_llm_with_rag(question, retrieval_unfiltered["chunks"])
        result.update(
            {
                "mode": "rag_unfiltered",
                "answer_rag_unfiltered": ans_rag,
                "chunks_unfiltered": retrieval_unfiltered["chunks"],
            }
        )
    elif mode == "rag_filtered":
        ans_rag = await ask_llm_with_rag(question, retrieval_filtered["chunks"])
        result.update(
            {
                "mode": "rag_filtered",
                "answer_rag_filtered": ans_rag,
                "chunks_filtered": retrieval_filtered["chunks"],
            }
        )
    else:  # "compare" → show all three
        ans_plain = await ask_llm_no_rag(question)
        ans_unfiltered = await ask_llm_with_rag(question, retrieval_unfiltered["chunks"])
        ans_filtered = await ask_llm_with_rag(question, retrieval_filtered["chunks"])

        result.update(
            {
                "mode": "compare",
                "answer_plain": ans_plain,
                "answer_rag_unfiltered": ans_unfiltered,
                "answer_rag_filtered": ans_filtered,
                "chunks_unfiltered": retrieval_unfiltered["chunks"],
                "chunks_filtered": retrieval_filtered["chunks"],
            }
        )

    return result


# -------------------------------------------------------
# BASIC PAGES / HEALTH
# -------------------------------------------------------

@app.get("/")
async def root():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"error": "index.html not found"}


@app.get("/health")
async def health():
    index = RAG_INDEX if RAG_INDEX["chunks"] else load_index()
    return {
        "status": "ok",
        "chunks": len(index.get("chunks", [])),
        "docs_dir": os.path.abspath(DOCS_DIR),
    }

