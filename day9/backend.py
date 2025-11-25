"""
Day 9 — Custom MCP Tool
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
from openai import OpenAI

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

# OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None


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


@app.post("/chat")
async def chat_endpoint(request: Request):
    """AI agent that can call MCP tools automatically"""
    global mcp_server, connected, openai_client
    
    if not openai_client:
        return {"success": False, "error": "OpenAI API key not configured"}
    
    if not connected or mcp_server is None:
        return {"success": False, "error": "Not connected to MCP. Call /connect first."}
    
    body = await request.json()
    user_message = body.get("message", "")
    
    if not user_message:
        return {"success": False, "error": "Missing 'message' in request body."}
    
    # Convert MCP tools to OpenAI function format
    functions = []
    for tool in tools_cache:
        schema = tool.get("input_schema", {})
        functions.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": schema
            }
        })
    
    # Call OpenAI with function calling
    try:
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant with access to tools. When the user asks about weather or website status, use the appropriate tool. Always call tools when relevant."
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=functions if functions else None,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        # Check if the model wants to call a tool
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            # Call the MCP tool
            tool_result = await mcp_server.call_tool(tool_name, tool_args)
            
            # Extract result from MCP format
            tool_result_data = {}
            if isinstance(tool_result, dict) and "content" in tool_result:
                for item in tool_result["content"]:
                    if isinstance(item, dict) and item.get("type") == "text":
                        try:
                            tool_result_data = json.loads(item.get("text", "{}"))
                        except:
                            tool_result_data = {"result": item.get("text", "")}
            
            # Add tool result to conversation and get final response
            messages.append(message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result_data)
            })
            
            # Get final response from AI
            final_response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=functions if functions else None,
            )
            
            final_message = final_response.choices[0].message.content
            
            return {
                "success": True,
                "reply": final_message,
                "tool_used": tool_name,
                "tool_result": tool_result_data
            }
        else:
            # No tool call needed, just return the response
            return {
                "success": True,
                "reply": message.content,
                "tool_used": None
            }
            
    except Exception as e:
        import traceback
        return {"success": False, "error": f"{str(e)}\n{traceback.format_exc()}"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "connected": connected,
        "tools_count": len(tools_cache),
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
    }

