"""
MCP Server for Day 10
- Slack tools (list_public_channels, read_slack_latest)
- Utility tools (echo, calculate)
- New doc tools: search_docs, summarize_text, save_to_file
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, Optional

from dotenv import load_dotenv
import requests
from slack_tool import list_public_channels, read_slack_latest

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


class MCPServer:
    def __init__(self) -> None:
        self.initialized: bool = False
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_SUMMARY_MODEL", "gpt-4o-mini")

        self.tools = [
            # --- Slack tools ---
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
            # --- Simple tools ---
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
            # --- Day 10: Doc tools ---
            {
                "name": "search_docs",
                "description": "Search text files in ./docs for a keyword and return matches + combined text.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "Keyword to search inside docs/",
                        },
                        "max_files": {
                            "type": "integer",
                            "description": "Max number of files to scan",
                            "default": 10,
                        },
                        "max_matches": {
                            "type": "integer",
                            "description": "Max total matches to return",
                            "default": 200,
                        },
                    },
                    "required": ["keyword"],
                },
            },
            {
                "name": "summarize_text",
                "description": "Summarize a larger piece of text into a short paragraph.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to summarize",
                        }
                    },
                    "required": ["text"],
                },
            },
            {
                "name": "save_to_file",
                "description": "Save given content to ./output/<filename>.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Filename to save under output/",
                        },
                        "content": {
                            "type": "string",
                            "description": "Text content to write to file",
                        },
                    },
                    "required": ["filename", "content"],
                },
            },
        ]

    # -------------------------------------------------------------------------
    # MCP protocol handlers
    # -------------------------------------------------------------------------

    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        self.initialized = True
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "day10-mcp-server", "version": "1.0.0"},
        }

    async def handle_tools_list(self) -> Dict[str, Any]:
        return {"tools": self.tools}

    # -------------------------------------------------------------------------
    # Tool implementations
    # -------------------------------------------------------------------------

    async def _tool_search_docs(self, args: Dict[str, Any]) -> Dict[str, Any]:
        keyword = (args.get("keyword") or "").strip()
        max_files = int(args.get("max_files", 10))
        max_matches = int(args.get("max_matches", 200))

        if not keyword:
            return {"ok": False, "error": "keyword is required"}

        docs_dir = os.path.join(os.path.dirname(__file__), "docs")
        if not os.path.isdir(docs_dir):
            return {
                "ok": False,
                "error": f"docs directory not found: {docs_dir}. Create it and add some .txt files.",
            }

        keyword_lower = keyword.lower()
        matches = []
        combined_chunks = []
        files_scanned = 0
        total_matches = 0

        for root, _, files in os.walk(docs_dir):
            for fname in files:
                if not fname.lower().endswith((".txt", ".md")):
                    continue
                filepath = os.path.join(root, fname)
                files_scanned += 1

                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        for line_no, line in enumerate(f, start=1):
                            if keyword_lower in line.lower():
                                match = {
                                    "file": os.path.relpath(filepath, docs_dir),
                                    "line": line_no,
                                    "text": line.strip(),
                                }
                                matches.append(match)
                                combined_chunks.append(line.strip())
                                total_matches += 1
                                if total_matches >= max_matches:
                                    break
                except Exception:
                    continue

                if files_scanned >= max_files or total_matches >= max_matches:
                    break
            if files_scanned >= max_files or total_matches >= max_matches:
                break

        combined_text = "\n".join(combined_chunks)

        return {
            "ok": True,
            "keyword": keyword,
            "files_scanned": files_scanned,
            "total_matches": total_matches,
            "matches": matches,
            "combined_text": combined_text,
        }

    async def _tool_summarize_text(self, args: Dict[str, Any]) -> Dict[str, Any]:
        text = (args.get("text") or "").strip()
        if not text:
            return {"ok": False, "error": "text is required"}

        if not self.openai_api_key:
            return {"ok": False, "error": "OPENAI_API_KEY not configured for summarizer."}

        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.openai_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that writes concise, well-structured summaries.",
                    },
                    {
                        "role": "user",
                        "content": f"Summarize the following text into 3-5 concise sentences:\n\n{text}",
                    },
                ],
                "temperature": 0.2,
            }
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )
            data = response.json()
            if response.status_code != 200:
                error_msg = data.get("error", {}).get("message", response.text)
                return {"ok": False, "error": f"OpenAI API error: {error_msg}"}

            summary = data["choices"][0]["message"]["content"].strip()
            return {"ok": True, "summary": summary}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def _tool_save_to_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        filename = (args.get("filename") or "").strip()
        content = args.get("content") or ""

        if not filename:
            return {"ok": False, "error": "filename is required"}

        base_dir = os.path.dirname(__file__)
        out_dir = os.path.join(base_dir, "output")
        os.makedirs(out_dir, exist_ok=True)

        safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in filename)
        file_path = os.path.join(out_dir, safe_name)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            return {"ok": False, "error": str(e)}

        return {"ok": True, "file_path": file_path}

    # -------------------------------------------------------------------------
    # Tool dispatcher
    # -------------------------------------------------------------------------

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
        elif name == "search_docs":
            result = await self._tool_search_docs(args)
        elif name == "summarize_text":
            result = await self._tool_summarize_text(args)
        elif name == "save_to_file":
            result = await self._tool_save_to_file(args)
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

