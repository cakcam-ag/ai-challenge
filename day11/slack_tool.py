"""
Slack tools for MCP integration (read-only)
- list_public_channels: uses channels:read
- read_slack_latest: reads latest messages from a channel (needs appropriate history scopes)
"""

import os
from typing import Dict, Any, List, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
client = WebClient(token=SLACK_TOKEN) if SLACK_TOKEN else None


def _ensure_client() -> Optional[Dict[str, Any]]:
    if not SLACK_TOKEN:
        return {"error": "SLACK_BOT_TOKEN not found in environment"}
    if client is None:
        return {"error": "Slack WebClient could not be initialized"}
    return None


async def list_public_channels() -> Dict[str, Any]:
    """
    List public channels the bot can see.
    Uses 'conversations.list' with type 'public_channel'.
    Requires: channels:read
    """
    err = _ensure_client()
    if err:
        return err

    try:
        result = client.conversations_list(types="public_channel", limit=1000)
        channels: List[Dict[str, Any]] = []
        for ch in result.get("channels", []):
            channels.append(
                {
                    "id": ch.get("id"),
                    "name": ch.get("name"),
                    "is_channel": ch.get("is_channel"),
                    "is_archived": ch.get("is_archived"),
                }
            )
        return {"ok": True, "channels": channels}
    except SlackApiError as e:
        return {"error": str(e), "slack_error": e.response.get("error")}


async def read_slack_latest(channel: str, limit: int = 10) -> Dict[str, Any]:
    """
    Read latest messages from a Slack channel.
    Works if your bot has the right history scope for that channel type.
    Example:
    - public channel: needs channels:history
    - private channel: needs groups:history
    """
    err = _ensure_client()
    if err:
        return err

    try:
        result = client.conversations_history(channel=channel, limit=limit)
        messages: List[Dict[str, Any]] = []
        for msg in result.get("messages", []):
            messages.append(
                {
                    "text": msg.get("text"),
                    "user": msg.get("user"),
                    "ts": msg.get("ts"),
                }
            )
        return {"ok": True, "channel": channel, "messages": messages}
    except SlackApiError as e:
        return {"error": str(e), "slack_error": e.response.get("error")}

