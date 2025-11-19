#!/bin/bash
# Day 5 Token Counting - Backend Run Script
echo "Starting FastAPI backend for Day 5..."
echo "Backend will run on http://127.0.0.1:8000"
cd "$(dirname "$0")"
uvicorn backend:app --host 127.0.0.1 --port 8000

