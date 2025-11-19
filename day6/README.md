# Day 6 — Subagents Interaction

## Task
Create two subagents in your code, each using its own model or configuration.
Set up interaction between them.
- Agent 1 solves Task 1 and outputs the result in a format that Agent 2 can easily read and process.
- Agent 2 uses this result to perform a second task (validation, refinement, or transformation).

**Goal:** You have two interacting agents, where the second one checks or improves the work of the first.

## Overview

This implementation demonstrates multi-agent interaction:
- **Agent 1 (Planner)**: Uses `gpt-5.1` to generate a 3-step plan for user's problem
- **Agent 2 (Reviewer)**: Uses `gpt-4o-mini` to review and improve Agent 1's plan

The agents interact sequentially: Agent 1's output becomes Agent 2's input.

## Features

- ✅ Two distinct agents with different models/configurations
- ✅ Agent 1 generates structured JSON plan
- ✅ Agent 2 reviews and improves the plan
- ✅ Clear interaction pipeline (Agent 1 → Agent 2)
- ✅ Error handling for each agent
- ✅ Visual display of both agents' outputs
- ✅ JSON parsing and validation

## Stack

- **Backend:** FastAPI
- **Frontend:** HTML/JavaScript
- **Models:** 
  - Agent 1: `gpt-5.1` (planning)
  - Agent 2: `gpt-4o-mini` (review)

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   Create a `.env` file in the `day6/` directory:
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
2. Enter a problem you want to solve (e.g., "I want to learn Python programming")
3. Click "Run Agents"
4. Watch the interaction:
   - **Agent 1** generates a 3-step plan
   - **Agent 2** reviews and improves the plan
5. Compare the original plan vs. improved plan

## Agent Interaction Flow

```
User Input
    ↓
Agent 1 (Planner) - gpt-5.1
    ↓
JSON Plan (steps + reasoning)
    ↓
Agent 2 (Reviewer) - gpt-4o-mini
    ↓
Improved Plan (improved_steps + changes_made + validation)
```

## Example

**Input:** "I want to learn Python programming"

**Agent 1 Output:**
```json
{
  "steps": [
    "Set up Python environment and install IDE",
    "Complete beginner tutorials and practice basics",
    "Build a small project to apply knowledge"
  ],
  "reasoning": "Start with setup, then learn fundamentals, finally apply"
}
```

**Agent 2 Output:**
```json
{
  "improved_steps": [
    "Install Python 3.x and choose an IDE (VS Code or PyCharm), set up virtual environments",
    "Complete structured course (Python basics, data structures, control flow), practice with coding exercises daily",
    "Build a practical project (e.g., todo app or data analysis script), join Python community for feedback"
  ],
  "changes_made": "Added specific tools, structured learning path, and community engagement",
  "validation": "Plan is actionable and logical, covers all essential steps"
}
```

## API Endpoints

### POST `/process`
Process a user query through both agents.

**Request:**
```json
{
  "user_input": "I want to learn Python programming"
}
```

**Response:**
```json
{
  "original_problem": "I want to learn Python programming",
  "agent1": {
    "success": true,
    "raw_output": "...",
    "plan": {
      "steps": [...],
      "reasoning": "..."
    },
    "model": "gpt-5.1"
  },
  "agent2": {
    "success": true,
    "raw_output": "...",
    "review": {
      "improved_steps": [...],
      "changes_made": "...",
      "validation": "..."
    },
    "model": "gpt-4o-mini"
  },
  "interaction_success": true
}
```

### GET `/`
Serve the HTML frontend.

### GET `/health`
Health check endpoint.

## Key Learnings

1. **Multi-Agent Architecture**: Two agents with distinct roles and models
2. **Agent Interaction**: Sequential pipeline where Agent 2 processes Agent 1's output
3. **Model Selection**: Different models for different tasks (planning vs. review)
4. **Structured Output**: JSON format ensures agents can parse each other's outputs
5. **Error Handling**: Each agent can fail independently, with proper error propagation

