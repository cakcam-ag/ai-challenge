"""
Day 7: Dialogue Compression

- Maintains a conversation history.
- Every N messages, compresses that segment into a summary.
- Uses summaries + recent messages instead of full history.
- Returns token usage for:
  - full history context
  - compressed context
"""

import os
import json
from typing import List, Dict, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken

load_dotenv()

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- Global in-memory state (single-user demo) ---------

# Full raw history (for measuring "before compression" token usage)
raw_history: List[Dict[str, str]] = []

# Messages which are not yet summarized (recent segment)
pending_messages: List[Dict[str, str]] = []

# List of summaries (each summary is text)
summaries: List[str] = []

# How many messages (user+assistant) per summary block
SUMMARY_BLOCK_SIZE = 10

SYSTEM_PROMPT = (
    "You are a helpful, concise AI assistant. "
    "Answer clearly, using the conversation history if needed."
)

SUMMARY_MODEL = "gpt-4o-mini"  # Cheaper model for summarization
CHAT_MODEL = "gpt-5.1"  # Main chat model


# --------- Token counting helpers (similar to Day 5) ---------

def get_encoding(model: str):
    try:
        return tiktoken.encoding_for_model(model)
    except Exception:
        return tiktoken.get_encoding("cl100k_base")


def estimate_message_tokens(messages: List[Dict[str, str]], model: str) -> int:
    """
    Rough estimate of tokens used by a list of chat messages.
    """
    encoding = get_encoding(model)
    tokens_per_message = 3
    tokens_per_name = 1

    num_tokens = 0
    for msg in messages:
        num_tokens += tokens_per_message
        for key, value in msg.items():
            num_tokens += len(encoding.encode(str(value)))
            if key == "name":
                num_tokens += tokens_per_name

    num_tokens += 3
    return num_tokens


# --------- Summarization logic ---------

def summarize_messages(messages: List[Dict[str, str]]) -> str:
    """
    Summarize a chunk of conversation messages into a short, dense summary
    that preserves user goals, decisions, and key facts.
    """
    if not messages:
        return ""

    # Turn messages into plain text
    convo_text = ""
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        convo_text += f"{role.upper()}: {content}\n"

    prompt = (
        "You are a conversation summarizer.\n"
        "Your job is to compress the following segment of dialogue into a brief summary, "
        "keeping:\n"
        "- user goals and preferences\n"
        "- important facts\n"
        "- decisions or next steps\n"
        "- key context needed for future conversation\n\n"
        "Be concise but informative.\n\n"
        "CONVERSATION SEGMENT:\n"
        f"{convo_text}"
    )

    resp = client.chat.completions.create(
        model=SUMMARY_MODEL,
        messages=[
            {"role": "system", "content": "You summarize conversations concisely while preserving important context."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    summary = resp.choices[0].message.content.strip()
    return summary


def build_full_context(new_user_message: str) -> List[Dict[str, str]]:
    """
    Context if we used the full raw history + the new user message.
    (For comparison only, we won't send this to the model.)
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(raw_history)
    messages.append({"role": "user", "content": new_user_message})
    return messages


def build_compressed_context(new_user_message: str) -> List[Dict[str, str]]:
    """
    Context actually sent to the model:
    - system prompt
    - combined summaries (if any)
    - pending (unsummarized) messages
    - new user message
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if summaries:
        combined = ""
        for i, s in enumerate(summaries, start=1):
            combined += f"Summary {i}: {s}\n\n"
        messages.append(
            {
                "role": "system",
                "content": "Conversation summary so far:\n" + combined.strip(),
            }
        )

    # include recent unsummarized messages
    messages.extend(pending_messages)
    # current message
    messages.append({"role": "user", "content": new_user_message})

    return messages


@app.post("/chat")
async def chat(request: Request) -> Dict[str, Any]:
    """
    Main chat endpoint:
    - Updates raw history
    - Maintains pending messages
    - Summarizes every SUMMARY_BLOCK_SIZE messages
    - Uses compressed context for model call
    - Returns token comparison
    """
    global raw_history, pending_messages, summaries

    body = await request.json()
    user_message = body.get("message", "").strip()

    if not user_message:
        return {"error": "Message cannot be empty."}

    # 1) Update histories: add user message
    user_msg_obj = {"role": "user", "content": user_message}
    raw_history.append(user_msg_obj)
    pending_messages.append(user_msg_obj)

    # 2) Build both contexts (for comparison)
    full_context_messages = build_full_context(user_message)
    compressed_context_messages = build_compressed_context(user_message)

    # 3) Estimate tokens for both contexts (before calling model)
    full_tokens_est = estimate_message_tokens(full_context_messages, CHAT_MODEL)
    compressed_tokens_est = estimate_message_tokens(compressed_context_messages, CHAT_MODEL)

    # 4) Call model with compressed context ONLY
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=compressed_context_messages,
        temperature=0.7,
    )
    reply_text = response.choices[0].message.content.strip()
    usage = response.usage

    # 5) Update histories with assistant reply
    assistant_msg_obj = {"role": "assistant", "content": reply_text}
    raw_history.append(assistant_msg_obj)
    pending_messages.append(assistant_msg_obj)

    # 6) Check if we should summarize the pending chunk
    summary_created = False
    last_summary_text = None

    if len(pending_messages) >= SUMMARY_BLOCK_SIZE:
        # Summarize this block
        summary_text = summarize_messages(pending_messages)
        summaries.append(summary_text)
        # Clear pending block (they are now "compressed")
        pending_messages = []
        summary_created = True
        last_summary_text = summary_text

    return {
        "reply": reply_text,
        "token_usage": {
            "full_context_tokens_est": full_tokens_est,
            "compressed_context_tokens_est": compressed_tokens_est,
            "api_prompt_tokens": usage.prompt_tokens,
            "api_completion_tokens": usage.completion_tokens,
            "api_total_tokens": usage.total_tokens,
            "savings_percent": round(((full_tokens_est - compressed_tokens_est) / full_tokens_est * 100), 2) if full_tokens_est > 0 else 0,
        },
        "state": {
            "raw_history_length": len(raw_history),
            "pending_messages_length": len(pending_messages),
            "summaries_count": len(summaries),
            "summary_block_size": SUMMARY_BLOCK_SIZE,
            "summary_created": summary_created,
            "last_summary": last_summary_text,
        },
    }


@app.post("/reset")
async def reset():
    """
    Reset the entire conversation (for testing / demos).
    """
    global raw_history, pending_messages, summaries
    raw_history = []
    pending_messages = []
    summaries = []
    return {"status": "reset"}


@app.get("/")
async def serve_index():
    """Serve the HTML frontend."""
    here = os.path.dirname(__file__)
    html_path = os.path.join(here, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"error": "index.html not found"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
        "summaries_count": len(summaries),
    }

