"""
Day 6: Subagents Interaction

Two subagents working together:
- Agent 1 (Planner): Generates a 3-step plan for user's problem
- Agent 2 (Reviewer): Reviews and improves Agent 1's plan
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from openai import OpenAI
import os
import json
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


def agent1_generate_plan(user_text: str) -> dict:
    """
    Agent 1: Planner
    Takes user's problem and generates a clear 3-step plan.
    Uses gpt-5.1 for planning.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-5.1",
            messages=[
                {
                    "role": "system",
                    "content": """You are Agent 1 (Planner).
Your task: Take the user's problem and create a clear, actionable 3-step plan.
Output MUST be valid JSON only in this exact format:
{
  "steps": ["step 1 description", "step 2 description", "step 3 description"],
  "reasoning": "brief explanation of why these steps"
}
Do not include any text outside the JSON."""
                },
                {
                    "role": "user",
                    "content": f"Create a 3-step plan to solve this problem: {user_text}"
                }
            ],
            temperature=0.7,
        )
        
        raw_output = response.choices[0].message.content.strip()
        
        # Try to extract JSON from the response
        try:
            # Remove markdown code blocks if present
            if "```json" in raw_output:
                raw_output = raw_output.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_output:
                raw_output = raw_output.split("```")[1].split("```")[0].strip()
            
            plan_data = json.loads(raw_output)
            return {
                "success": True,
                "raw_output": raw_output,
                "plan": plan_data,
                "model": "gpt-5.1"
            }
        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw output
            return {
                "success": False,
                "raw_output": raw_output,
                "error": "Failed to parse JSON from Agent 1",
                "model": "gpt-5.1"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model": "gpt-5.1"
        }


def agent2_review_plan(agent1_output: str, original_problem: str) -> dict:
    """
    Agent 2: Reviewer
    Reviews and improves Agent 1's plan.
    Uses gpt-5.1 for review tasks.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-5.1",
            messages=[
                {
                    "role": "system",
                    "content": """You are Agent 2 (Reviewer).
You receive a plan from Agent 1.
Your job:
1. Review the plan for clarity, logic, and completeness
2. Improve any weak or missing steps
3. Ensure steps are actionable and in logical order
4. Add any critical steps that might be missing

Output MUST be valid JSON in this exact format:
{
  "improved_steps": ["improved step 1", "improved step 2", "improved step 3"],
  "changes_made": "brief explanation of what you improved",
  "validation": "assessment of plan quality"
}
Do not include any text outside the JSON."""
                },
                {
                    "role": "user",
                    "content": f"""Original problem: {original_problem}

Agent 1's plan:
{agent1_output}

Review and improve this plan. Make sure it's actionable and logical."""
                }
            ],
            temperature=0.5,  # Lower temperature for more focused review
        )
        
        raw_output = response.choices[0].message.content.strip()
        
        # Try to extract JSON from the response
        try:
            # Remove markdown code blocks if present
            if "```json" in raw_output:
                raw_output = raw_output.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_output:
                raw_output = raw_output.split("```")[1].split("```")[0].strip()
            
            review_data = json.loads(raw_output)
            return {
                "success": True,
                "raw_output": raw_output,
                "review": review_data,
                "model": "gpt-5.1"
            }
        except json.JSONDecodeError:
            return {
                "success": False,
                "raw_output": raw_output,
                "error": "Failed to parse JSON from Agent 2",
                "model": "gpt-5.1"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model": "gpt-5.1"
        }


@app.post("/process")
async def process_query(request: Request):
    """
    Main endpoint: Orchestrates interaction between Agent 1 and Agent 2.
    """
    data = await request.json()
    user_input = data.get("user_input", "").strip()
    
    if not user_input:
        return {
            "error": "user_input cannot be empty",
            "agent1": None,
            "agent2": None
        }
    
    # Step 1: Agent 1 generates plan
    agent1_result = agent1_generate_plan(user_input)
    
    # Step 2: Agent 2 reviews and improves (only if Agent 1 succeeded)
    agent2_result = None
    if agent1_result.get("success"):
        # Pass both the raw output and parsed plan to Agent 2
        agent1_output_for_agent2 = agent1_result.get("raw_output", "")
        agent2_result = agent2_review_plan(agent1_output_for_agent2, user_input)
    else:
        agent2_result = {
            "success": False,
            "error": "Cannot review: Agent 1 failed to generate plan",
            "model": "gpt-5.1"
        }
    
    return {
        "original_problem": user_input,
        "agent1": agent1_result,
        "agent2": agent2_result,
        "interaction_success": agent1_result.get("success") and agent2_result.get("success")
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

