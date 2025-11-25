# Day 9 — Custom MCP Tool

## Overview
Day 9 implements a custom MCP tool: `web_status_checker` that checks website HTTP status and response time.

## Features
- Custom MCP tool: `web_status_checker`
- Checks URL reachability, HTTP status code, and response time
- Returns meaningful JSON results
- Full MCP protocol implementation
- Web UI for testing

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the backend:
```bash
python3 -m uvicorn backend:app --host 127.0.0.1 --port 8000
```

3. Open browser:
```
http://127.0.0.1:8000/
```

## Usage

1. Click "Connect to MCP" - the tool will auto-connect
2. You'll see the `web_status_checker` tool
3. Enter a URL (e.g., `https://www.google.com`)
4. Click "Run"
5. See the result with status code and response time

## Tool Response Format

```json
{
  "ok": true,
  "url": "https://www.google.com",
  "status": 200,
  "time_ms": 83.41
}
```

