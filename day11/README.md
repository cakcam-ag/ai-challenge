# Day 11 — External Memory

## Overview
This day adds persistent, long-term memory to the MCP agent. Three new tools are exposed through MCP:

1. `memory_store` – save a key/value pair (backed by SQLite).
2. `memory_read` – read a stored value.
3. `memory_list` – list all stored keys.

These tools persist data between runs via `memory.db`.

## Setup

```bash
cd day11
python3 -m venv .venv && source .venv/bin/activate  # optional
pip install -r requirements.txt
```

Create a `.env` file next to `backend.py` with:

```
OPENAI_API_KEY=<your_key_if_needed>
SLACK_BOT_TOKEN=<optional slack token>
```

## Run

```bash
python3 -m uvicorn backend:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`, click “Connect to MCP,” and use the Memory Manager to store/read/list memories. Data is persisted in `memory.db`.

