#!/bin/bash
# Day 5 Token Counting - Frontend Run Script
echo "Starting Streamlit frontend for Day 5..."
echo "It will open in your browser automatically"
cd "$(dirname "$0")"
python3 -m streamlit run app.py --server.port 8501

