# Day 10 — MCP Tools Composition

## Overview
Day 10 introduces a mini MCP pipeline where multiple tools are composed together:

1. `search_docs` – scans text files under `docs/` for a keyword.
2. `summarize_text` – produces a short summary of the combined matches.
3. `save_to_file` – writes the summary to `output/<filename>`.

The FastAPI backend exposes:
- `GET /connect` – load tools.
- `POST /call` – run any tool manually.
- `POST /pipeline` – executes the search → summarize → save sequence.

## Setup

```bash
cd day10
python3 -m venv .venv && source .venv/bin/activate  # optional
pip install -r requirements.txt
```

Create the working folders (already provided here):

```bash
mkdir -p docs output
```

Add a few `.txt` files under `docs/` so `search_docs` has something to scan.

## Running

```bash
python3 -m uvicorn backend:app --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000/`:
- Click “Connect to MCP”.
- Try the pipeline by providing a keyword (e.g., “python”) and optional filename.
- You can also call any tool manually in the Raw Tools Browser section.

The generated summaries are stored under the `output/` directory.***

