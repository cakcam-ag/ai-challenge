"""
Day 5: Token Counting Backend

Counts tokens for both input (prompt) and output (response).
Demonstrates how model behavior changes with different prompt lengths,
including cases that exceed context limits.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from openai import OpenAI
import os
import tiktoken
from dotenv import load_dotenv

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

# Model context limits (in tokens)
MODEL_LIMITS = {
    "gpt-4o-mini": 128000,
    "gpt-4o": 128000,
    "gpt-3.5-turbo": 16385,
    "gpt-5.1": 128000,
}


def count_tokens(text: str, model: str = "gpt-5.1") -> int:
    """
    Count tokens in a text string using tiktoken.
    """
    try:
        # Get encoding for the model
        # For most OpenAI models, we can use cl100k_base
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback to cl100k_base if model-specific encoding fails
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))


def count_message_tokens(messages: list, model: str = "gpt-5.1") -> int:
    """
    Count tokens in a list of messages (system + user messages).
    Accounts for message formatting overhead.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except Exception:
        encoding = tiktoken.get_encoding("cl100k_base")
    
    tokens_per_message = 3  # Every message follows <|start|>{role/name}\n{content}<|end|>\n
    tokens_per_name = 1  # If there's a name, the role is omitted
    
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(str(value)))
            if key == "name":
                num_tokens += tokens_per_name
    
    num_tokens += 3  # Every reply is primed with <|start|>assistant<|message|>
    return num_tokens


@app.post("/analyze")
async def analyze_tokens(request: Request):
    """
    Analyze a prompt: count tokens, check against context limit, and get AI response.
    Returns detailed token information for both input and output.
    """
    data = await request.json()
    prompt = data.get("prompt", "")
    model = data.get("model", "gpt-5.1")
    test_case = data.get("test_case", "custom")  # short, long, exceeds_limit, custom

    if not prompt:
        return {"error": "Prompt cannot be empty"}

    # Prepare messages
    messages = [
        {
            "role": "system",
            "content": "You are a helpful AI assistant. Provide clear and accurate responses.",
        },
        {"role": "user", "content": prompt},
    ]

    # Count input tokens
    input_token_count = count_message_tokens(messages, model)
    context_limit = MODEL_LIMITS.get(model, 128000)
    
    # Reserve tokens for response (typically 4096 for most models, but can vary)
    # For demonstration, we'll reserve 4000 tokens for the response
    max_input_tokens = context_limit - 4000
    
    result = {
        "prompt": prompt,
        "model": model,
        "test_case": test_case,
        "input_tokens": input_token_count,
        "context_limit": context_limit,
        "max_input_tokens": max_input_tokens,
        "exceeds_limit": input_token_count > max_input_tokens,
        "token_usage_percentage": round((input_token_count / max_input_tokens) * 100, 2),
    }

    # If prompt exceeds limit, return error without calling API
    if result["exceeds_limit"]:
        result["error"] = f"Prompt exceeds context limit! Input tokens: {input_token_count}, Max allowed: {max_input_tokens}"
        result["response"] = None
        result["output_tokens"] = 0
        result["total_tokens"] = input_token_count
        return result

    # Try to get AI response
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=4000,  # Limit response length
        )

        reply_text = response.choices[0].message.content
        
        # Count output tokens
        output_token_count = count_tokens(reply_text, model)
        
        # Also get actual token usage from API (for verification)
        actual_usage = response.usage
        
        result.update({
            "response": reply_text,
            "output_tokens": output_token_count,
            "total_tokens": input_token_count + output_token_count,
            "api_reported_tokens": {
                "prompt_tokens": actual_usage.prompt_tokens,
                "completion_tokens": actual_usage.completion_tokens,
                "total_tokens": actual_usage.total_tokens,
            },
            "success": True,
        })

    except Exception as e:
        error_msg = str(e)
        result.update({
            "error": error_msg,
            "response": None,
            "output_tokens": 0,
            "total_tokens": input_token_count,
            "success": False,
        })

    return result


@app.post("/count_tokens")
async def count_tokens_endpoint(request: Request):
    """
    Endpoint for HTML frontend: counts tokens and gets AI response.
    Returns format: {prompt_tokens, completion_tokens, total_tokens, response}
    """
    data = await request.json()
    prompt = data.get("prompt", "")
    model = data.get("model", "gpt-5.1")

    if not prompt:
        return {"error": "Prompt cannot be empty", "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "response": ""}

    # Prepare messages
    messages = [
        {
            "role": "system",
            "content": "You are a helpful AI assistant. Provide clear and accurate responses.",
        },
        {"role": "user", "content": prompt},
    ]

    # Count input tokens
    input_token_count = count_message_tokens(messages, model)
    context_limit = MODEL_LIMITS.get(model, 128000)
    max_input_tokens = context_limit - 4000

    # Check if exceeds limit
    if input_token_count > max_input_tokens:
        return {
            "error": f"Prompt exceeds context limit! Input tokens: {input_token_count}, Max allowed: {max_input_tokens}",
            "prompt_tokens": input_token_count,
            "completion_tokens": 0,
            "total_tokens": input_token_count,
            "response": "Error: Prompt too long for model context limit."
        }

    # Get AI response
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=4000,
        )

        reply_text = response.choices[0].message.content
        output_token_count = count_tokens(reply_text, model)
        actual_usage = response.usage

        return {
            "prompt_tokens": actual_usage.prompt_tokens,
            "completion_tokens": actual_usage.completion_tokens,
            "total_tokens": actual_usage.total_tokens,
            "response": reply_text,
        }

    except Exception as e:
        return {
            "error": str(e),
            "prompt_tokens": input_token_count,
            "completion_tokens": 0,
            "total_tokens": input_token_count,
            "response": f"Error: {str(e)}"
        }


@app.get("/")
async def serve_html():
    """Serve the HTML frontend"""
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"error": "index.html not found"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
    }

