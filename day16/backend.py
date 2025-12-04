import os
import json
import math
import requests
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

_client = None

def get_client():
    """Lazy initialization for OpenAI client."""
    global _client
    if _client is None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY missing")
        _client = AsyncOpenAI(api_key=key)
    return _client


INDEX_FILE = "rag_index.json"
DOCS_DIR = os.path.join("data", "docs")

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

RAG_INDEX: Dict[str, Any] = {"chunks": []}


# -------------------------------------------------------
# LOAD / SAVE INDEX
# -------------------------------------------------------

def load_index():
    global RAG_INDEX
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # fix embedding types
        for c in data.get("chunks", []):
            c["embedding"] = [float(x) for x in c.get("embedding", [])]

        RAG_INDEX = data
    return RAG_INDEX


def save_index(idx: Dict[str, Any]):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(idx, f, indent=2)


# -------------------------------------------------------
# EMBEDDINGS
# -------------------------------------------------------

async def embed_text(text: str) -> List[float]:
    client = get_client()
    resp = await client.embeddings.create(
        model="text-embedding-3-small",
        input=[text],
    )
    vec = resp.data[0].embedding
    norm = math.sqrt(sum(v*v for v in vec)) or 1.0
    return [v/norm for v in vec]


def cosine_sim(a, b):
    return float(sum(x*y for x, y in zip(a, b)))


# -------------------------------------------------------
# CORE LLM CALL
# -------------------------------------------------------

async def call_llm(prompt: str, model="gpt-4o") -> str:
    """Call LLM using chat completions API."""
    client = get_client()
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        # Fallback: try with requests if SDK fails
        api_key = os.getenv("OPENAI_API_KEY")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        resp = requests.post("https://api.openai.com/v1/chat/completions", 
                           headers=headers, json=payload, timeout=90)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


# -------------------------------------------------------
# LLM HELPERS FOR DAY 16
# -------------------------------------------------------

async def ask_llm_with_citations(question: str, chunks: List[Dict[str, Any]]) -> str:
    """
    Day 16: Answer MUST include citations.
    Citations should reference chunk IDs like [doc#chunk].
    """

    context_texts = []
    for c in chunks:
        cid = f"{c['doc']}#{c['chunk_index']}"
        context_texts.append(f"[{cid}] {c['text']}")

    context_block = "\n\n".join(context_texts)

    prompt = f"""You are a RAG assistant that MUST ALWAYS cite sources.

RULES:
- Use citations in the format: [filename#chunk_index] (e.g., [agents_overview.txt#0])
- Every important fact or claim must include a citation
- At the end of your answer, include a CITATIONS section listing all sources used

CONTEXT (with chunk IDs):
{context_block}

QUESTION: {question}

Provide a detailed answer with inline citations like [filename#chunk_index] throughout your response.
End with a CITATIONS section listing all sources used.
"""

    answer = await call_llm(prompt, model="gpt-4o")

    # Post-check: verify citations are present
    has_citations = False
    citation_patterns = [
        "CITATIONS:",
        "Citations:",
        "Sources:",
        "SOURCES:",
    ]
    
    for pattern in citation_patterns:
        if pattern in answer:
            has_citations = True
            break
    
    # Also check for inline citations like [file#number]
    import re
    inline_citations = re.findall(r'\[[\w\.]+#\d+\]', answer)
    if inline_citations:
        has_citations = True

    if not has_citations:
        # Retry with stronger instructions
        retry_prompt = f"""You must include citations in your answer.

Available chunk IDs to cite:
{', '.join([f"{c['doc']}#{c['chunk_index']}" for c in chunks])}

QUESTION: {question}

CONTEXT:
{context_block}

Rewrite your answer and:
1. Include inline citations like [filename#chunk_index] for each fact
2. End with a CITATIONS section listing all sources used
"""
        answer = await call_llm(retry_prompt, model="gpt-4o")

    return answer


async def ask_llm_no_rag(question: str) -> str:
    """Plain LLM without RAG."""
    prompt = f"You are a helpful assistant. Answer the following question:\n\n{question}"
    return await call_llm(prompt, model="gpt-4o-mini")


# -------------------------------------------------------
# INDEXING
# -------------------------------------------------------

def chunk_text(text: str, max_chars=800):
    chunks = []
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
    os.makedirs(DOCS_DIR, exist_ok=True)

    chunks = []
    cid = 0
    doc_count = 0

    for root, _, files in os.walk(DOCS_DIR):
        for fname in files:
            if not fname.lower().endswith((".txt", ".md")):
                continue
            doc_count += 1
            path = os.path.join(root, fname)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

            for i, ch_text in enumerate(chunk_text(text)):
                emb = await embed_text(ch_text)
                rel = os.path.relpath(path, DOCS_DIR)
                chunks.append({
                    "id": f"chunk-{cid}",
                    "doc": rel,
                    "chunk_index": i,
                    "text": ch_text,
                    "embedding": emb,
                })
                cid += 1

    index = {"chunks": chunks, "doc_count": doc_count}
    save_index(index)
    load_index()

    return {"success": True, "chunk_count": len(chunks), "doc_count": doc_count}


# -------------------------------------------------------
# RETRIEVAL
# -------------------------------------------------------

async def retrieve(question, top_k=8, threshold=None):
    index = RAG_INDEX if RAG_INDEX["chunks"] else load_index()

    if not index.get("chunks"):
        return {"chunks": []}

    qemb = await embed_text(question)
    scored = []

    for ch in index["chunks"]:
        score = cosine_sim(qemb, ch["embedding"])
        scored.append({"chunk": ch, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:top_k]

    if threshold is not None:
        top = [s for s in top if s["score"] >= threshold]

    return {
        "chunks": [
            {
                "doc": s["chunk"]["doc"],
                "chunk_index": s["chunk"]["chunk_index"],
                "text": s["chunk"]["text"],
                "score": s["score"],
            }
            for s in top
        ]
    }


# -------------------------------------------------------
# ASK ENDPOINT (WITH DAY 16)
# -------------------------------------------------------

@app.post("/ask")
async def ask(req: Request):
    body = await req.json()
    q = (body.get("question") or "").strip()
    if not q:
        return {"success": False, "error": "question is required"}

    mode = body.get("mode", "compare")
    top_k = int(body.get("top_k", 8))
    th = float(body.get("threshold", 0.35))

    unfiltered = await retrieve(q, top_k=top_k)
    filtered = await retrieve(q, top_k=top_k, threshold=th)

    if mode == "plain":
        return {
            "success": True,
            "answer_plain": await ask_llm_no_rag(q)
        }

    elif mode == "rag_unfiltered":
        answer = await ask_llm_with_citations(q, unfiltered["chunks"])
        return {
            "success": True,
            "chunks": unfiltered["chunks"],
            "answer": answer
        }

    elif mode == "rag_filtered":
        answer = await ask_llm_with_citations(q, filtered["chunks"])
        return {
            "success": True,
            "chunks": filtered["chunks"],
            "answer": answer
        }

    else:  # compare
        plain = await ask_llm_no_rag(q)
        rag_unfiltered = await ask_llm_with_citations(q, unfiltered["chunks"])
        rag_filtered = await ask_llm_with_citations(q, filtered["chunks"])
        
        return {
            "success": True,
            "answer_plain": plain,
            "answer_rag_unfiltered": rag_unfiltered,
            "answer_rag_filtered": rag_filtered,
            "chunks_unfiltered": unfiltered["chunks"],
            "chunks_filtered": filtered["chunks"]
        }


# -------------------------------------------------------
# BASIC
# -------------------------------------------------------

@app.get("/")
async def root():
    path = os.path.join(os.path.dirname(__file__), "index.html")
    return FileResponse(path) if os.path.exists(path) else {"error": "index.html missing"}


@app.get("/health")
async def health():
    idx = RAG_INDEX if RAG_INDEX["chunks"] else load_index()
    return {"status": "ok", "chunks": len(idx.get("chunks", [])), "docs_dir": os.path.abspath(DOCS_DIR)}

