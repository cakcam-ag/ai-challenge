# Day 8 — MCP Integration

## Task
Install an MCP SDK/client (or run an MCP server if you are using a local setup).
Write minimal code that establishes an MCP connection and retrieves the list of available tools.

**Goal:** Code that connects to MCP and outputs the list of available MCP tools.

## Overview

This implementation demonstrates MCP (Model Context Protocol) integration:
- Connects to an MCP server
- Retrieves list of available tools
- Displays tools with descriptions and schemas
- Provides connection status and tool management

## Features

- ✅ MCP client connection using Python MCP SDK
- ✅ Tool discovery and listing
- ✅ Visual display of available tools
- ✅ Connection status monitoring
- ✅ Error handling for missing dependencies

## Stack

- **Backend:** FastAPI
- **Frontend:** HTML/JavaScript
- **MCP SDK:** Python `mcp` package

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install MCP SDK:**
   ```bash
   pip install mcp
   ```

3. **Optional - Install MCP echo server (for demo):**
   ```bash
   pip install mcp-echo-server
   ```

4. **Set up environment:**
   Create a `.env` file in the `day8/` directory (optional, no API key needed for basic MCP):
   ```
   # No API key required for MCP connection
   ```

5. **Run the backend:**
   ```bash
   ./run_backend.sh
   ```
   Or manually:
   ```bash
   uvicorn backend:app --host 127.0.0.1 --port 8000
   ```

6. **Open in browser:**
   Navigate to `http://127.0.0.1:8000/`

## Usage

1. Open the app in your browser
2. Click "Connect to MCP Server"
3. View the list of available tools
4. Each tool shows:
   - Tool name
   - Description
   - Input schema (if available)

## MCP Server Options

### Option 1: Echo Server (Demo)
```bash
pip install mcp-echo-server
```
The backend will try to use this automatically.

### Option 2: Custom MCP Server
Modify `backend.py` to point to your MCP server:
```python
server_cmd = ["your-mcp-server", "args"]
```

### Option 3: STDIO Server
Use any MCP-compatible server that supports STDIO transport.

## API Endpoints

### GET `/connect`
Connect to MCP server and retrieve tools.

**Response:**
```json
{
  "success": true,
  "tools_count": 2,
  "tools": [
    {
      "name": "echo",
      "description": "Echo tool description",
      "input_schema": {...}
    }
  ],
  "message": "Successfully connected to MCP server. Found 2 tools."
}
```

### GET `/tools`
Get list of available tools (requires connection).

### GET `/status`
Get connection status and current tools.

### GET `/`
Serve the HTML frontend.

### GET `/health`
Health check endpoint.

## Troubleshooting

### "MCP SDK not installed"
```bash
pip install mcp
```

### "MCP server not found"
Install an MCP server (e.g., echo server):
```bash
pip install mcp-echo-server
```

### Connection fails
- Check that MCP server is properly installed
- Verify server command in `backend.py`
- Check server logs for errors

## Key Learnings

1. **MCP Protocol**: Model Context Protocol for tool integration
2. **Tool Discovery**: How to list available tools from MCP server
3. **Connection Management**: Establishing and maintaining MCP connections
4. **Error Handling**: Graceful handling of missing dependencies

## Notes

- MCP is a protocol for connecting AI models to external tools
- The echo server is a simple demo server for testing
- Real MCP servers can provide various tools (file operations, web search, etc.)
- This implementation focuses on tool discovery as required by Day 8

