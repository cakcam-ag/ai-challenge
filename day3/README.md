# Day 3: Interaction – Spec Agent with Stopping Condition

An interactive AI agent that gathers requirements through a short conversation and then produces a final technical specification on its own.

## Goal

- You interact with the model.
- It asks a few clarification questions.
- At the right moment, it **stops** and returns a final technical spec in JSON.

## Behavior

### Backend (FastAPI)

- System prompt enforces a **JSON protocol** with two modes:

1. **Collecting requirements**
   ```json
   {
     "status": "collecting",
     "question": "<one clear follow-up question to the user>",
     "notes": "<short summary of what you have understood so far>",
     "confidence": "<0 to 1 float>"
   }
   ```

2. **Final spec**
   ```json
   {
     "status": "final",
     "spec": {
       "title": "<short feature name>",
       "summary": "<2–3 sentence summary of the feature>",
       "inputs": ["<input 1>", "<input 2>", "..."],
       "outputs": ["<output 1>", "<output 2>", "..."],
       "constraints": ["<constraint 1>", "..."],
       "edgeCases": ["<edge case 1>", "..."]
     },
     "confidence": "<0 to 1 float>"
   }
   ```

- The prompt includes a **constraint**:
  - The model should ask at most 2 follow‑up questions.
  - After that, it **must** return a `"status": "final"` spec.

### Frontend (Streamlit)

- Shows a chat interface.
- User describes a feature / answers follow‑up questions.
- Assistant messages are shown as pretty‑printed JSON.
- When `"status": "final"` is returned:
  - The spec is displayed.
  - A banner indicates that the final spec is generated.

## Setup

From the project root:

```bash
cd day3
pip3 install -r requirements.txt
```

Configure your API key (re-using the same `.env` as previous days, or create a new one in `day3/`):

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

## Run

**Terminal 1 – Backend**
```bash
cd day3
./run_backend.sh
```
or
```bash
uvicorn backend:app --reload --port 8000
```

**Terminal 2 – Frontend**
```bash
cd day3
./run_frontend.sh
```
or
```bash
streamlit run app.py
```

The frontend runs at `http://localhost:8501`.

## How to Demo (Day 3)

1. Open the UI.
2. Start by describing a feature, e.g.:
   - "I want a mobile app that tracks daily water intake and reminds users to drink water."
3. The agent should:
   - Ask 1–2 clarification questions (`status = "collecting"`).
   - Then return a final spec (`status = "final"`).
4. Show the final JSON spec with:
   - `title`
   - `summary`
   - `inputs`, `outputs`
   - `constraints`, `edgeCases`

## Requirements Met

- ✅ Interaction: user and model exchange several messages.
- ✅ Prompt describes what final result should look like (technical spec JSON).
- ✅ Agent decides when to stop asking questions and produce the spec.
- ✅ Response can be parsed and used by the application.


