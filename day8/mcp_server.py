"""
MCP Server with Slack tools
Implements MCP protocol: initialize, tools/list, tools/call
"""

import asyncio
import json
import sys
from typing import Dict, Any

from slack_tool import list_public_channels, read_slack_latest


class MCPServer:
    def __init__(self) -> None:
        self.initialized: bool = False
        self.tools = [
            {
                "name": "list_public_channels",
                "description": "List public Slack channels the bot can see",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
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
                        "text": {
                            "type": "string",
                            "description": "Text to echo",
                        }
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
        ]

    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        self.initialized = True
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "day8-mcp-server", "version": "1.0.0"},
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
                # ⚠ demo only, not safe for untrusted input
                value = eval(expr, {"__builtins__": {}})
                result = {"ok": True, "result": value}
            except Exception as e:
                result = {"ok": False, "error": str(e)}
        else:
            result = {"ok": False, "error": f"Unknown tool: {name}"}

        # Wrap result in MCP text content
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

        response: Dict[str, Any] | None = None

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
