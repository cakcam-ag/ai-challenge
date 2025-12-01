# Day 14 — RAG Query Comparison

Compare LLM answers with and without RAG (Retrieval-Augmented Generation).

## Features

- **Without RAG**: Direct LLM answer using only training data
- **With RAG**: LLM answer enhanced with retrieved document chunks
- **Comparison**: Side-by-side comparison with AI-generated analysis
- **Document Search**: Uses FAISS index from Day 13 to find relevant chunks

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
   - These will be indexed and used for RAG

## Usage

1. Start the server:
```bash
python3 -m uvicorn backend:app --host 127.0.0.1 --port 8000
```

2. Open `http://127.0.0.1:8000/` in your browser

3. Click "Reindex Documents" to build the FAISS index

4. Enter a question and click "Compare Answers" to see:
   - Answer without RAG
   - Answer with RAG (using retrieved chunks)
   - AI-generated comparison analysis

## API Endpoints

- `POST /reindex` - Rebuild the FAISS index from documents
- `POST /query_without_rag` - Get answer without RAG
  - Body: `{"question": "your question"}`
- `POST /query_with_rag` - Get answer with RAG
  - Body: `{"question": "your question", "top_k": 3}`
- `POST /compare` - Compare both methods
  - Body: `{"question": "your question", "top_k": 3}`
  - Returns: Both answers + AI-generated comparison

## How RAG Works

1. **Question** → User asks a question
2. **Search** → Find relevant document chunks using semantic search (FAISS)
3. **Merge** → Combine chunks with the question as context
4. **LLM** → Send merged context + question to LLM
5. **Answer** → LLM generates answer using the retrieved context

## Comparison

The `/compare` endpoint automatically:
- Gets answer without RAG
- Gets answer with RAG
- Uses an LLM to analyze differences and provide insights

