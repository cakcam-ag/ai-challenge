# Day 7 — Dialogue Compression

## Task
Implement a dialogue history compression mechanism (for example, every 10 messages create a summary and store it instead of the full original history). Check how the agent continues the conversation using the summarized history instead of the full context. Compare answer quality and token usage before and after compression.

**Goal:** The agent works with compressed history and can still perform the same tasks while using fewer tokens.

## Overview

This implementation demonstrates dialogue compression:
- Maintains full conversation history for comparison
- Every 10 messages, compresses that segment into a summary
- Uses summaries + recent messages instead of full history
- Shows token usage comparison (full vs compressed)
- Agent continues conversation using compressed context

## Features

- ✅ Dialogue history compression every 10 messages
- ✅ Token usage comparison (full history vs compressed)
- ✅ Visual display of compression savings
- ✅ Summary creation notifications
- ✅ Chat interface with conversation history
- ✅ Reset functionality for testing

## Stack

- **Backend:** FastAPI
- **Frontend:** HTML/JavaScript
- **Models:** 
  - Chat: `gpt-5.1`
  - Summarization: `gpt-4o-mini` (cost-effective for summaries)

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   Create a `.env` file in the `day7/` directory:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

3. **Run the backend:**
   ```bash
   ./run_backend.sh
   ```
   Or manually:
   ```bash
   uvicorn backend:app --host 127.0.0.1 --port 8000
   ```

4. **Open in browser:**
   Navigate to `http://127.0.0.1:8000/`

## Usage

1. Open the app in your browser
2. Start chatting with the agent
3. Watch the token metrics:
   - **Full history tokens**: What it would cost without compression
   - **Compressed tokens**: What it actually uses
   - **Token savings**: Percentage saved
4. After 10 messages, a summary is created automatically
5. Continue chatting - the agent uses compressed history but maintains context

## How It Works

### Compression Flow

```
Messages 1-10 → Summarized → Stored as Summary 1
Messages 11-20 → Summarized → Stored as Summary 2
...
Recent messages (not yet summarized) → Sent directly
```

### Context Building

**Full Context (for comparison only):**
- System prompt
- All raw messages (user + assistant)
- New user message

**Compressed Context (actually used):**
- System prompt
- All summaries (concatenated)
- Recent unsummarized messages
- New user message

### Token Savings

As the conversation grows:
- **Full history**: Linear growth (every message adds tokens)
- **Compressed**: Bounded growth (summaries are fixed size, only recent messages grow)

Example: After 50 messages:
- Full: ~5000 tokens
- Compressed: ~1500 tokens (3 summaries + 10 recent messages)
- **Savings: ~70%**

## API Endpoints

### POST `/chat`
Send a message and get a response with compression stats.

**Request:**
```json
{
  "message": "What is Python?"
}
```

**Response:**
```json
{
  "reply": "Python is a programming language...",
  "token_usage": {
    "full_context_tokens_est": 5000,
    "compressed_context_tokens_est": 1500,
    "api_prompt_tokens": 1523,
    "api_completion_tokens": 45,
    "api_total_tokens": 1568,
    "savings_percent": 70.0
  },
  "state": {
    "raw_history_length": 50,
    "pending_messages_length": 8,
    "summaries_count": 4,
    "summary_block_size": 10,
    "summary_created": false,
    "last_summary": null
  }
}
```

### POST `/reset`
Reset the conversation history.

### GET `/`
Serve the HTML frontend.

### GET `/health`
Health check endpoint.

## Key Learnings

1. **Compression Strategy**: Summarize in blocks to maintain context while reducing tokens
2. **Token Efficiency**: Significant savings (50-80%) in long conversations
3. **Context Preservation**: Summaries preserve key information for continuity
4. **Quality Trade-off**: Compressed context may lose some nuance but maintains core meaning
5. **Scalability**: Enables longer conversations without hitting context limits

## Testing

To see compression in action:
1. Send 10+ messages
2. Watch for summary creation notification
3. Compare token usage before and after compression
4. Continue conversation - agent should maintain context
5. Check that token savings increase as conversation grows

