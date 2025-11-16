"""
Day 3: FastAPI Backend for Interactive Spec Gathering

The model has a short conversation to collect requirements and then,
by itself, stops asking questions and returns a final technical spec.

No JSON formatting is required in the response body – just natural text.
We only use simple markers so the frontend can detect when the spec is final.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env (re-use Day 1/2 key)
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
    """
    Handle chat requests.

    Protocol:
    - User sends a free-form message describing a feature / product idea.
    - The model either:
        * asks a follow-up question (normal conversational text), or
        * returns a final technical spec.

    Convention:
    - During requirement gathering, start your message with: QUESTION:
    - When you return the final spec, start with: FINAL_SPEC:
      and stop asking further questions.
    """
    data = await request.json()
    user_input = data.get("message", "")
    history = data.get("history", [])

    if not user_input:
        # Frontend may send an empty ping; treat as init
        user_input = "INIT_CONVERSATION"

    try:
        # Build conversation history for the model
        messages = [
            {
                "role": "system",
                "content": """
You are a senior engineer helping to write a short technical specification.

You must follow this EXACT sequence of questions:

1) Ask about **project name and purpose**
2) Ask about **target users / audience**
3) Ask about **key features and functionality**
4) Ask about **technical requirements** (stack, APIs, data sources, etc.)
5) Ask about **success criteria / metrics**

Rules for questions:
- Always prefix questions with: `QUESTION: `
- Ask ONE question at a time.
- Keep questions short and precise.

Conversation start:
- When the user sends `INIT_CONVERSATION`, you must reply with the FIRST question:
  `QUESTION: What is the project name and what is its main purpose?`

Conversation handling:
- You will see the full previous conversation in the messages.
- Use it to understand which questions have ALREADY been asked and answered.
- Do NOT repeat questions that have already been clearly answered.

After you have asked all five questions and the user has answered them (or given enough information):
- STOP asking questions.
- Return a final technical specification.
- Start the message with: `FINAL_SPEC: `
- Write the spec in clear markdown with sections:
  - Title
  - Summary
  - Requirements
  - Inputs
  - Outputs
  - Constraints
  - Edge cases

Do NOT include JSON. Just natural language text.
""",
            }
        ]

        # Add prior turns from history so the model can continue the sequence
        for turn in history:
            role = turn.get("role")
            content = turn.get("content", "")
            if role in ("user", "assistant") and isinstance(content, str):
                messages.append({"role": role, "content": content})

        # Add the latest user input
        messages.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model="gpt-5.1",
            messages=messages,
        )

        reply_text = response.choices[0].message.content
        return {"reply": reply_text}

    except Exception as e:
        return {"reply": f"Error from backend: {str(e)}"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
    }



