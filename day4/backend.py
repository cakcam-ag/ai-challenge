"""
Day 4: Temperature Comparison Backend

Allows testing the same prompt with different temperature values (0, 0.7, 1.2)
to compare accuracy, creativity, and diversity of responses.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os
from concurrent.futures import ThreadPoolExecutor
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


@app.post("/compare")
async def compare_temperatures(request: Request):
    """
    Run the same prompt with three different temperature values.
    Returns all three responses for comparison.
    """
    data = await request.json()
    prompt = data.get("prompt", "")

    if not prompt:
        return {"error": "Prompt cannot be empty"}

    temperatures = [0.0, 0.7, 1.5]
    results = {}

    try:
        # Run all 3 requests in parallel for faster response
        def get_response(temp):
            response = client.chat.completions.create(
                model="gpt-5.1",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant. Provide clear and accurate responses.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=temp,
            )
            return {
                "temperature": temp,
                "response": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
            }

        # Run all requests in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(get_response, temp) for temp in temperatures]
            responses = [future.result() for future in futures]

        for resp in responses:
            # Handle both 0.0 and 0 as keys
            temp_key = f"temp_{resp['temperature']}"
            results[temp_key] = resp

        return {"results": results, "prompt": prompt}

    except Exception as e:
        return {"error": str(e)}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
    }

