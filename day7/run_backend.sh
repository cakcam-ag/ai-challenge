#!/bin/bash
# Day 7 Dialogue Compression - Backend Run Script
echo "Starting FastAPI backend for Day 7..."
echo "Backend will run on http://127.0.0.1:8000"
cd "$(dirname "$0")"
uvicorn backend:app --host 127.0.0.1 --port 8000

