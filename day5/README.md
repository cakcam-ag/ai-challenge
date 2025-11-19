# Day 5 — Token Counting

## Task
Add token counting to your code (for both request and response). Compare three cases:
- A short prompt
- A long prompt
- A prompt that exceeds the model's context limit

**Goal:** Code that counts tokens and clearly demonstrates how the model's behavior changes depending on the prompt length and limits.

## Overview

This implementation demonstrates token counting using `tiktoken` to count tokens in both input prompts and output responses. It shows how different prompt lengths affect token usage and what happens when prompts exceed the model's context limits.

## Features

- ✅ Token counting for input (prompt) using `tiktoken`
- ✅ Token counting for output (response) using `tiktoken`
- ✅ Comparison with API-reported token counts
- ✅ Three test cases: short, long, and exceeding context limit
- ✅ Visual display of token usage and context limits
- ✅ Error handling for prompts that exceed context limits

## Stack

- **Backend:** FastAPI
- **Frontend:** Streamlit
- **Token Counting:** tiktoken
- **Model:** OpenAI (gpt-4o-mini, gpt-4o, gpt-3.5-turbo, gpt-5.1)

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   Create a `.env` file in the `day5/` directory:
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

4. **Run the frontend:**
   ```bash
   ./run_frontend.sh
   ```
   Or manually:
   ```bash
   streamlit run app.py --server.port 8501
   ```

## Usage

1. Open the Streamlit app in your browser (usually `http://localhost:8501`)
2. Select one of the three test cases:
   - **Short Prompt:** Simple question (~50 tokens)
   - **Long Prompt:** Detailed technical request (~2000 tokens)
   - **Exceeds Limit:** Very long prompt that exceeds context window
3. Or enter a custom prompt
4. Click "Analyze Tokens" to see:
   - Input token count
   - Output token count
   - Total token usage
   - Context limit and usage percentage
   - AI response (if within limits)
   - Error message (if exceeds limit)

## Test Cases

### 1. Short Prompt
- **Example:** "What is Python?"
- **Tokens:** ~50 tokens
- **Behavior:** Quick response, minimal token usage

### 2. Long Prompt
- **Example:** Detailed technical specification request
- **Tokens:** ~2000 tokens
- **Behavior:** More context provided, model has more information to work with

### 3. Exceeds Context Limit
- **Example:** Very long repeated text
- **Tokens:** >16,000 tokens (for gpt-3.5-turbo)
- **Behavior:** Error returned, no API call made

## Model Context Limits

| Model | Context Limit |
|-------|--------------|
| gpt-4o-mini | 128,000 tokens |
| gpt-4o | 128,000 tokens |
| gpt-3.5-turbo | 16,385 tokens |
| gpt-5.1 | 128,000 tokens |

## Key Learnings

1. **Token Counting:** Using `tiktoken` to accurately count tokens before sending to API
2. **Context Limits:** Understanding model context windows and reserving tokens for responses
3. **Error Handling:** Detecting when prompts exceed limits before making API calls
4. **Token Efficiency:** Monitoring token usage to optimize costs and stay within limits

## API Endpoints

### POST `/analyze`
Analyze a prompt and count tokens.

**Request:**
```json
{
  "prompt": "Your prompt here",
  "model": "gpt-4o-mini",
  "test_case": "short"
}
```

**Response:**
```json
{
  "prompt": "...",
  "model": "gpt-4o-mini",
  "test_case": "short",
  "input_tokens": 50,
  "output_tokens": 150,
  "total_tokens": 200,
  "context_limit": 128000,
  "max_input_tokens": 124000,
  "token_usage_percentage": 0.04,
  "exceeds_limit": false,
  "response": "AI response here...",
  "api_reported_tokens": {
    "prompt_tokens": 50,
    "completion_tokens": 150,
    "total_tokens": 200
  },
  "success": true
}
```

### GET `/health`
Health check endpoint.

## Notes

- Token counting uses `tiktoken` which is the official OpenAI tokenizer
- The backend reserves 4000 tokens for the response when calculating max input tokens
- Prompts that exceed the limit are rejected before making API calls to save costs
- API-reported token counts are included for verification

