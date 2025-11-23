"""
Day 8 — MCP Integration + Slack (read-only)
- Direct integration with MCP server module
- Lists tools and calls them directly
- Serves a simple web UI
"""

import os
import json
from typing import Any, Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# MCP server instance
mcp_server = None
connected = False
tools_cache: List[Dict[str, Any]] = []


async def connect_mcp() -> Dict[str, Any]:
    """Load MCP server module and get tools"""
    global mcp_server, connected, tools_cache
    
    try:
        import importlib.util
        server_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")
        spec = importlib.util.spec_from_file_location("mcp_server", server_path)
        mcp_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mcp_module)
        
        # Create server instance
        mcp_server = mcp_module.MCPServer()
        
        # Initialize (simulate initialize call)
        await mcp_server.handle_initialize({})
        
        # Get tools list
        tools_result = await mcp_server.handle_tools_list()
        
        tools_cache = []
        for t in tools_result.get("tools", []):
            tools_cache.append({
                "name": t.get("name", ""),
                "description": t.get("description", ""),
                "input_schema": t.get("inputSchema", {})
            })
        
        connected = True
        
        return {
            "success": True,
            "message": f"Connected to MCP server. Found {len(tools_cache)} tools.",
            "tools": tools_cache,
            "count": len(tools_cache),
        }
        
    except Exception as e:
        import traceback
        connected = False
        mcp_server = None
        tools_cache = []
        return {"success": False, "error": f"{str(e)}\n{traceback.format_exc()}", "tools": []}


@app.get("/connect")
async def connect_endpoint():
    return await connect_mcp()


@app.get("/tools")
async def tools_endpoint():
    if not connected:
        return {"success": False, "error": "Not connected. Call /connect first.", "tools": []}
    return {"success": True, "tools": tools_cache, "count": len(tools_cache)}


@app.post("/call")
async def call_tool_endpoint(request: Request):
    global mcp_server, connected

    if not connected or mcp_server is None:
        return {"success": False, "error": "Not connected to MCP. Call /connect first."}

    body = await request.json()
    tool_name = body.get("tool")
    args = body.get("args", {})

    if not tool_name:
        return {"success": False, "error": "Missing 'tool' in request body."}

    try:
        result = await mcp_server.call_tool(tool_name, args)

        # Extract content from MCP response format
        if isinstance(result, dict) and "content" in result:
            text_piece = ""
            for item in result["content"]:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_piece = item.get("text", "")

            if text_piece:
                try:
                    parsed = json.loads(text_piece)
                    return {"success": True, "tool": tool_name, "result": parsed}
                except json.JSONDecodeError:
                    return {"success": True, "tool": tool_name, "result": text_piece}

        return {"success": True, "tool": tool_name, "result": result}

    except Exception as e:
        import traceback
        return {"success": False, "error": f"{str(e)}\n{traceback.format_exc()}", "tool": tool_name}


@app.get("/")
async def root():
    """Serve frontend"""
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"error": "index.html not found"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "connected": connected,
        "tools_count": len(tools_cache),
        "slack_token_configured": bool(os.getenv("SLACK_BOT_TOKEN")),
    }
