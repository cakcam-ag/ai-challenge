#!/bin/bash

# Day 1 AI Agent - Backend Server
echo "Starting FastAPI backend..."
echo "Backend will run on http://127.0.0.1:8000"
echo ""
uvicorn backend:app --reload --port 8000

