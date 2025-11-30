"""
Day 13 — Document Indexing
FastAPI backend with /reindex and /query endpoints
"""

import os
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


@app.get("/")
def home():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"error": "index.html not found"}


@app.post("/reindex")
def rebuild():
    try:
        ok = build_index()
        return {"success": ok, "message": "Index rebuilt successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/query")
async def run_query(req: Request):
    try:
        body = await req.json()
        q = body.get("query", "").strip()
        k = int(body.get("top_k", 5))

        if not q:
            return {"success": False, "error": "Query cannot be empty"}

        results = query_index(q, k)
        return {"success": True, "results": results}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
    }

