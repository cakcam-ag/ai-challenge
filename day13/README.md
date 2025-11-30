# Day 13 — Document Indexing

A document indexing system using FAISS and OpenAI embeddings.

## Features

- **Document Processing**: Loads `.txt` and `.md` files from `data/docs/`
- **Text Chunking**: Splits documents into overlapping chunks (400 tokens, 50 overlap)
- **Embeddings**: Uses OpenAI `text-embedding-3-large` model
- **FAISS Index**: Stores vectors in FAISS for fast similarity search
- **Semantic Search**: Query documents using semantic similarity

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
   - Example: `data/docs/article1.txt`, `data/docs/readme.md`

## Usage

1. Start the server:
```bash
python3 -m uvicorn backend:app --host 127.0.0.1 --port 8000
```

2. Open `http://127.0.0.1:8000/` in your browser

3. Click "Reindex Documents" to build the FAISS index

4. Enter a query and click "Search" to find relevant document chunks

## API Endpoints

- `POST /reindex` - Rebuild the FAISS index from documents in `data/docs/`
- `POST /query` - Search the index
  - Body: `{"query": "your question", "top_k": 5}`
  - Returns: Array of matching chunks with scores

## Storage

- `storage/faiss.index` - FAISS vector index
- `storage/chunks.json` - Chunk metadata and text

