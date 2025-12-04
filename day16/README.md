# Day 16 — RAG with Citations & Sources

## Overview

Enhanced RAG pipeline that **enforces citations** in every answer. The model must include source references from the document index.

## Features

- ✅ **Mandatory Citations**: Every RAG answer includes citations in format `[filename#chunk_index]`
- ✅ **Citation Verification**: Post-processing checks if citations are present, retries if missing
- ✅ **Source Tracking**: Each chunk has a unique ID (document filename + chunk index)
- ✅ **Comparison Mode**: Compare answers with/without citations
- ✅ **Citation Highlighting**: UI highlights citations and shows which sources were used

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment:
```bash
cp ../day15/.env .env  # or create .env with OPENAI_API_KEY
```

3. Add documents to `data/docs/` (`.txt` or `.md` files)

4. Start server:
```bash
python3 -m uvicorn backend:app --host 127.0.0.1 --port 8000
```

5. Open http://127.0.0.1:8000

## Usage

1. **Reindex**: Click "Reindex Documents" to build the index
2. **Ask Questions**: Enter a question and click "Compare" to see:
   - Plain LLM (no citations)
   - RAG with citations (unfiltered)
   - RAG with citations (filtered by similarity threshold)

## Citation Format

Citations use the format: `[filename#chunk_index]`

Example:
- `[agents_overview.txt#0]` = first chunk from agents_overview.txt
- `[llm_intro.txt#3]` = fourth chunk from llm_intro.txt

## Testing Checklist

Test with 4-5 questions and verify:
- ✅ Sources included every time in RAG answers
- ✅ Citations are highlighted in the UI
- ✅ Citation badge shows "✓ Citations Found" when present
- ✅ Hallucinations decrease compared to plain LLM
- ✅ Each fact in the answer has a corresponding citation

## API Endpoints

- `POST /reindex` - Rebuild document index
- `POST /ask` - Ask a question (supports modes: `plain`, `rag_unfiltered`, `rag_filtered`, `compare`)
- `GET /health` - Health check

