"""
Day 2: FastAPI Backend with Structured JSON Output
Handles HTTP requests to OpenAI API with enforced JSON response format
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os
import json
from dotenv import load_dotenv

# Load environment variables
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


@app.post("/chat")
async def chat(request: Request):
    """Handle chat requests and return structured JSON response"""
    data = await request.json()
    user_input = data.get("message", "")

    if not user_input:
        return {"reply": {"error": "Message cannot be empty"}}

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are an AI that ALWAYS responds in JSON.

Your output MUST follow exactly this structure:

{
  "answer": "<short answer>",
  "explanation": "<2–3 sentence explanation>",
  "confidence": "<0 to 1 float>"
}

Example:
{
  "answer": "Blue whales",
  "explanation": "They are the largest animals ever known. They can reach 30 meters in length.",
  "confidence": "0.91"
}

If you cannot follow the format, return a JSON error object:
{
  "error": "Could not generate output"
}"""
                },
                {"role": "user", "content": user_input}
            ]
        )

        raw = response.choices[0].message.content

        # Try to parse JSON safely
        try:
            structured = json.loads(raw)
        except json.JSONDecodeError:
            structured = {"error": "Model returned invalid JSON", "raw": raw}

        return {"reply": structured}

    except Exception as e:
        return {"reply": {"error": str(e)}}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "api_key_configured": bool(os.getenv("OPENAI_API_KEY"))
    }

