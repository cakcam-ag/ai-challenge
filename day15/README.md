# Day 15 — RAG with Reranking & Filtering

Enhanced RAG pipeline with similarity threshold filtering to improve answer quality.

## Features

- **Plain LLM**: Answer without any retrieved context
- **RAG (Unfiltered)**: Retrieve top-k chunks, no filtering
- **RAG (Filtered)**: Retrieve top-k chunks, then filter by similarity threshold
- **Comparison Mode**: See all three answers side-by-side
- **Tunable Threshold**: Adjust similarity cutoff to drop non-relevant chunks

## How It Works

1. **Indexing**: Documents are chunked and embedded using `text-embedding-3-small`
2. **Retrieval**: Question is embedded, cosine similarity computed for all chunks
3. **Reranking**: Chunks sorted by similarity (descending)
4. **Filtering**: Chunks below threshold are dropped (optional)
5. **LLM**: Filtered chunks sent as context to GPT-5.1

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_key_here
```

3. Add documents to `data/docs/`:
   - Place `.txt` or `.md` files in this directory

## Usage

1. Start the server:
```bash
python3 -m uvicorn backend:app --host 127.0.0.1 --port 8000
```

2. Open `http://127.0.0.1:8000/` in your browser

3. Click "Reindex Documents" to build the index

4. Enter a question and adjust:
   - **Top K**: Number of chunks to retrieve (default: 8)
   - **Threshold**: Minimum cosine similarity (default: 0.35)
     - Lower = more chunks pass filter
     - Higher = only very relevant chunks pass

5. Click "Compare" to see all three modes side-by-side

## API Endpoints

- `POST /reindex` - Rebuild index from documents
- `POST /ask` - Ask a question
  - Body: `{"question": "...", "mode": "compare|plain|rag_unfiltered|rag_filtered", "top_k": 8, "threshold": 0.35}`

## Filtering Strategy

- **No Filter**: All top-k chunks used (may include irrelevant ones)
- **With Filter**: Only chunks above threshold used (more focused, but may miss context if threshold too high)

Tune the threshold based on your documents and questions. Start with 0.35 and adjust.

