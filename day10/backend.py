"""
Day 10 — MCP Tools Composition
- Uses MCP server module directly (same style as Day 8/9)
- Has generic tool runner (/call)
- Adds /pipeline endpoint: search_docs → summarize_text → save_to_file
"""

import os
import json
from typing import Any, Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# MCP server instance (Python object, not over stdio)
mcp_server = None
connected = False
tools_cache: List[Dict[str, Any]] = []


async def connect_mcp() -> Dict[str, Any]:
    """
    Import mcp_server.py, create MCPServer(), initialize it, and cache tools.
    """
    global mcp_server, connected, tools_cache

    try:
        import importlib.util

        server_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")
        spec = importlib.util.spec_from_file_location("mcp_server", server_path)
        mcp_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mcp_module)

        # Create server instance
        mcp_server = mcp_module.MCPServer()

        # Simulate "initialize" call
        await mcp_server.handle_initialize({})

        # Ask for tools
        tools_result = await mcp_server.handle_tools_list()
        tools_cache = []
        for t in tools_result.get("tools", []):
            tools_cache.append(
                {
                    "name": t.get("name", ""),
                    "description": t.get("description", ""),
                    "input_schema": t.get("inputSchema", {}),
                }
            )

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
        return {
            "success": False,
            "error": f"{str(e)}\n{traceback.format_exc()}",
            "tools": [],
        }


async def _call_mcp_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper to call MCP tool and return parsed JSON result (if possible).
    """
    global mcp_server

    if not connected or mcp_server is None:
        return {"success": False, "error": "Not connected to MCP. Call /connect first."}

    try:
        result = await mcp_server.call_tool(tool_name, args)

        # MCP result format: {"content": [{"type": "text", "text": "...json..."}]}
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

        # Fallback
        return {"success": True, "tool": tool_name, "result": result}

    except Exception as e:
        import traceback

        return {
            "success": False,
            "tool": tool_name,
            "error": f"{str(e)}\n{traceback.format_exc()}",
        }


@app.get("/connect")
async def connect_endpoint():
    """Connect to MCP server and load tools."""
    return await connect_mcp()


@app.get("/tools")
async def tools_endpoint():
    """Return cached tools."""
    if not connected:
        return {
            "success": False,
            "error": "Not connected. Call /connect first.",
            "tools": [],
        }
    return {"success": True, "tools": tools_cache, "count": len(tools_cache)}


@app.post("/call")
async def call_tool_endpoint(request: Request):
    """Generic tool caller (used by UI)."""
    body = await request.json()
    tool_name = body.get("tool")
    args = body.get("args", {})

    if not tool_name:
        return {"success": False, "error": "Missing 'tool' in request body."}

    return await _call_mcp_tool(tool_name, args)


@app.post("/pipeline")
async def pipeline_endpoint(request: Request):
    """
    Day 10 pipeline:
    1) search_docs(keyword)
    2) summarize_text(text=combined_text)
    3) save_to_file(filename, content=summary)
    """
    if not connected or mcp_server is None:
        return {"success": False, "error": "Not connected. Call /connect first."}

    body = await request.json()
    keyword: str = (body.get("keyword") or "").strip()
    filename: str = (body.get("filename") or "").strip()

    if not keyword:
        return {"success": False, "error": "keyword is required for the pipeline."}

    # Default filename if not provided
    if not filename:
        safe_kw = "".join(c if c.isalnum() or c in "-_" else "_" for c in keyword.lower())
        filename = f"summary_{safe_kw}.txt"

    # 1) search_docs
    search_res = await _call_mcp_tool(
        "search_docs",
        {"keyword": keyword, "max_files": 10, "max_matches": 200},
    )
    if not search_res.get("success"):
        return {
            "success": False,
            "step": "search_docs",
            "error": search_res.get("error", "Unknown error from search_docs"),
        }

    search_payload = search_res.get("result", {})
    if not search_payload.get("ok"):
        return {
            "success": False,
            "step": "search_docs",
            "error": search_payload.get("error", "search_docs returned ok=False"),
            "search_result": search_payload,
        }

    combined_text = search_payload.get("combined_text", "")
    if not combined_text:
        return {
            "success": False,
            "step": "search_docs",
            "error": "No text found in docs for this keyword.",
            "search_result": search_payload,
        }

    # 2) summarize_text
    summary_res = await _call_mcp_tool("summarize_text", {"text": combined_text})
    if not summary_res.get("success"):
        return {
            "success": False,
            "step": "summarize_text",
            "error": summary_res.get("error", "Unknown error from summarize_text"),
            "search_result": search_payload,
        }

    summary_payload = summary_res.get("result", {})
    if not summary_payload.get("ok"):
        return {
            "success": False,
            "step": "summarize_text",
            "error": summary_payload.get("error", "summarize_text returned ok=False"),
            "search_result": search_payload,
        }

    summary_text = summary_payload.get("summary", "")
    if not summary_text:
        return {
            "success": False,
            "step": "summarize_text",
            "error": "Summarizer returned empty summary.",
            "search_result": search_payload,
        }

    # 3) save_to_file
    save_res = await _call_mcp_tool(
        "save_to_file",
        {"filename": filename, "content": summary_text},
    )
    if not save_res.get("success"):
        return {
            "success": False,
            "step": "save_to_file",
            "error": save_res.get("error", "Unknown error from save_to_file"),
            "search_result": search_payload,
            "summary_result": summary_payload,
        }

    save_payload = save_res.get("result", {})
    if not save_payload.get("ok"):
        return {
            "success": False,
            "step": "save_to_file",
            "error": save_payload.get("error", "save_to_file returned ok=False"),
            "search_result": search_payload,
            "summary_result": summary_payload,
        }

    return {
        "success": True,
        "keyword": keyword,
        "summary_file": save_payload.get("file_path"),
        "steps": {
            "search": search_payload,
            "summary": summary_payload,
            "save": save_payload,
        },
    }


@app.get("/")
async def root():
    """Serve frontend."""
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

