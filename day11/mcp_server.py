"""
MCP Server for Day 11
- Slack tools (list_public_channels, read_slack_latest)
- Utility tools (echo, calculate)
- Persistent memory tools backed by SQLite
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, Optional

from slack_tool import list_public_channels, read_slack_latest
from memory_store import store_memory, read_memory, list_memory


class MCPServer:
    def __init__(self) -> None:
        self.initialized: bool = False
        self.tools = [
            {
                "name": "list_public_channels",
                "description": "List public Slack channels the bot can see",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "read_slack_latest",
                "description": "Read latest messages from a Slack channel by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "channel": {
                            "type": "string",
                            "description": "Slack channel ID (e.g. C0123456789)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of messages to fetch",
                            "default": 10,
                        },
                    },
                    "required": ["channel"],
                },
            },
            {
                "name": "echo",
                "description": "Echo back the given text",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to echo"}
                    },
                    "required": ["text"],
                },
            },
            {
                "name": "calculate",
                "description": "Evaluate a simple Python expression (demo only)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Python expression to eval",
                        }
                    },
                    "required": ["expression"],
                },
            },
            {
                "name": "memory_store",
                "description": "Store a key/value pair in persistent memory.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Memory key",
                        },
                        "value": {
                            "type": "string",
                            "description": "Value to store",
                        },
                    },
                    "required": ["key", "value"],
                },
            },
            {
                "name": "memory_read",
                "description": "Read a value from persistent memory.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Memory key",
                        }
                    },
                    "required": ["key"],
                },
            },
            {
                "name": "memory_list",
                "description": "List all memory keys.",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
        ]

    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        self.initialized = True
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "day11-mcp-server", "version": "1.0.0"},
        }

    async def handle_tools_list(self) -> Dict[str, Any]:
        return {"tools": self.tools}

    async def call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if name == "list_public_channels":
            result = await list_public_channels()
        elif name == "read_slack_latest":
            channel = args.get("channel", "")
            limit = int(args.get("limit", 10))
            result = await read_slack_latest(channel, limit)
        elif name == "echo":
            result = {"ok": True, "echo": args.get("text", "")}
        elif name == "calculate":
            expr = args.get("expression", "0")
            try:
                value = eval(expr, {"__builtins__": {}})
                result = {"ok": True, "result": value}
            except Exception as e:
                result = {"ok": False, "error": str(e)}
        elif name == "memory_store":
            key = args.get("key")
            value = args.get("value")
            if not key or value is None:
                result = {"ok": False, "error": "key and value are required"}
            else:
                result = store_memory(key, value)
        elif name == "memory_read":
            key = args.get("key")
            if not key:
                result = {"ok": False, "error": "key is required"}
            else:
                result = read_memory(key)
        elif name == "memory_list":
            result = list_memory()
        else:
            result = {"ok": False, "error": f"Unknown tool: {name}"}

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result),
                }
            ]
        }


async def main() -> None:
    server = MCPServer()
    loop = asyncio.get_event_loop()

    def read_stdin():
        try:
            return sys.stdin.readline()
        except Exception:
            return None

    while True:
        line = await loop.run_in_executor(None, read_stdin)
        if not line:
            await asyncio.sleep(0.05)
            continue

        try:
            request = json.loads(line.strip())
        except json.JSONDecodeError:
            continue

        method = request.get("method")
        req_id = request.get("id")
        params = request.get("params", {})

        response: Optional[Dict[str, Any]] = None

        try:
            if method == "initialize":
                result = await server.handle_initialize(params)
                response = {"jsonrpc": "2.0", "id": req_id, "result": result}
            elif method == "tools/list":
                if not server.initialized:
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32002, "message": "Server not initialized"},
                    }
                else:
                    result = await server.handle_tools_list()
                    response = {"jsonrpc": "2.0", "id": req_id, "result": result}
            elif method == "tools/call":
                if not server.initialized:
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32002, "message": "Server not initialized"},
                    }
                else:
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    result = await server.call_tool(tool_name, arguments)
                    response = {"jsonrpc": "2.0", "id": req_id, "result": result}
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }
        except Exception as e:
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": str(e)},
            }

        if response:
            print(json.dumps(response), flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

