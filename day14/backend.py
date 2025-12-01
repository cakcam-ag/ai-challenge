"""
Day 14 — RAG Query with Comparison
Implements RAG pipeline and compares with/without RAG
"""

import os
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from document_index import build_index, query_index

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

def openai_headers():
    return {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }


def call_llm(messages: list, model: str = "gpt-5.1") -> str:
    """Call OpenAI LLM with given messages."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7
    }
    
    response = requests.post(url, headers=openai_headers(), json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    
    return data["choices"][0]["message"]["content"]


@app.get("/")
def home():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"error": "index.html not found"}


@app.post("/reindex")
def rebuild():
    """Rebuild the document index."""
    try:
        ok = build_index()
        return {"success": ok, "message": "Index rebuilt successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/query_without_rag")
async def query_without_rag(req: Request):
    """Answer question WITHOUT RAG (just LLM)."""
    try:
        body = await req.json()
        question = body.get("question", "").strip()
        
        if not question:
            return {"success": False, "error": "Question cannot be empty"}
        
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Answer questions based on your training data."},
            {"role": "user", "content": question}
        ]
        
        answer = call_llm(messages)
        
        return {
            "success": True,
            "answer": answer,
            "chunks_used": [],
            "method": "without_rag"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/query_with_rag")
async def query_with_rag(req: Request):
    """Answer question WITH RAG (search chunks + LLM)."""
    try:
        body = await req.json()
        question = body.get("question", "").strip()
        top_k = int(body.get("top_k", 3))
        
        if not question:
            return {"success": False, "error": "Question cannot be empty"}
        
        # Step 1: Search for relevant chunks
        search_results = query_index(question, top_k=top_k)
        
        if not search_results:
            return {"success": False, "error": "No relevant chunks found. Reindex documents first."}
        
        # Step 2: Merge chunks with question
        context_text = "\n\n".join([
            f"[From {r['meta']['file']}]\n{r['chunk']}"
            for r in search_results
        ])
        
        # Step 3: Send to LLM with context
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant. Answer questions using the provided context documents. If the context doesn't contain enough information, say so."
            },
            {
                "role": "user",
                "content": f"""Context documents:
{context_text}

Question: {question}

Answer the question using the context above. If the context doesn't provide enough information, mention that."""
            }
        ]
        
        answer = call_llm(messages)
        
        return {
            "success": True,
            "answer": answer,
            "chunks_used": [
                {
                    "file": r["meta"]["file"],
                    "chunk": r["chunk"][:200] + "..." if len(r["chunk"]) > 200 else r["chunk"],
                    "score": r["score"]
                }
                for r in search_results
            ],
            "method": "with_rag"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/compare")
async def compare_rag(req: Request):
    """Compare answers with and without RAG."""
    try:
        body = await req.json()
        question = body.get("question", "").strip()
        top_k = int(body.get("top_k", 3))
        
        if not question:
            return {"success": False, "error": "Question cannot be empty"}
        
        # Get both answers
        without_rag_resp = await query_without_rag(req)
        with_rag_resp = await query_with_rag(req)
        
        if not without_rag_resp.get("success") or not with_rag_resp.get("success"):
            return {
                "success": False,
                "error": "Failed to get one or both answers",
                "without_rag": without_rag_resp,
                "with_rag": with_rag_resp
            }
        
        # Generate comparison analysis
        comparison_prompt = f"""Compare these two answers to the same question:

Question: {question}

Answer WITHOUT RAG (using only training data):
{without_rag_resp['answer']}

Answer WITH RAG (using retrieved documents):
{with_rag_resp['answer']}

Documents used in RAG:
{chr(10).join([f"- {c['file']} (relevance: {c['score']:.3f})" for c in with_rag_resp['chunks_used']])}

Provide a brief analysis:
1. Where did RAG help? (better factual accuracy, more specific details, etc.)
2. Where didn't RAG help? (no difference, RAG added noise, etc.)
3. Overall assessment: which answer is better and why?

Keep it concise (2-3 sentences per point)."""

        comparison_messages = [
            {"role": "system", "content": "You are an AI evaluation assistant. Analyze and compare answers objectively."},
            {"role": "user", "content": comparison_prompt}
        ]
        
        comparison = call_llm(comparison_messages, model="gpt-4o-mini")
        
        return {
            "success": True,
            "question": question,
            "without_rag": {
                "answer": without_rag_resp["answer"],
                "chunks_used": []
            },
            "with_rag": {
                "answer": with_rag_resp["answer"],
                "chunks_used": with_rag_resp["chunks_used"]
            },
            "comparison": comparison
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "api_key_configured": bool(OPENAI_API_KEY),
    }

