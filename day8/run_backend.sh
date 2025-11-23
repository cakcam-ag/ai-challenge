#!/bin/bash
# Day 8 MCP Integration - Backend Run Script
echo "Starting FastAPI backend for Day 8..."
echo "Backend will run on http://127.0.0.1:8000"
echo ""
echo "Note: Make sure MCP is installed: pip install mcp"
echo "Optional: Install echo server: pip install mcp-echo-server"
cd "$(dirname "$0")"
uvicorn backend:app --host 127.0.0.1 --port 8000

