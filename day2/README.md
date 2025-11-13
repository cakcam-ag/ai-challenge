# Day 2: AI Configuration - Structured JSON Output

Learn how to define a response format for your AI agent and parse structured outputs.

## Features

- ✅ FastAPI backend with JSON-enforced system prompt
- ✅ Structured JSON response format (answer, explanation, confidence)
- ✅ Safe JSON parsing with error handling
- ✅ Streamlit frontend with pretty JSON display
- ✅ All Day 2 requirements met

## What Changed from Day 1

### Backend Changes:
1. **System Prompt**: Enforces JSON output format with specific structure
2. **JSON Parsing**: Safely parses LLM responses and handles invalid JSON
3. **Structured Output**: Always returns valid JSON to frontend

### Frontend Changes:
1. **JSON Display**: Uses `st.json()` to pretty-print structured responses
2. **Type Checking**: Handles both dict (JSON) and string responses

## Architecture

- **Backend**: FastAPI (runs on port 8000)
- **Frontend**: Streamlit (runs on port 8501)
- **Model**: OpenAI GPT-4o-mini
- **Output Format**: Structured JSON

## Response Format

The AI agent now returns responses in this JSON structure:

```json
{
  "answer": "<short answer>",
  "explanation": "<2–3 sentence explanation>",
  "confidence": "<0 to 1 float>"
}
```

**Example:**
```json
{
  "answer": "Paris",
  "explanation": "Paris is the capital of France, known for its culture and cuisine.",
  "confidence": "0.92"
}
```

## Setup

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file in the `day2/` folder:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Run the Application

**Terminal 1 - Start Backend:**
```bash
./run_backend.sh
```
Or manually:
```bash
uvicorn backend:app --reload --port 8000
```

**Terminal 2 - Start Frontend:**
```bash
./run_frontend.sh
```
Or manually:
```bash
streamlit run app.py
```

The frontend will automatically open in your browser at `http://localhost:8501`

## Usage

1. Make sure both backend and frontend are running
2. Open the Streamlit app in your browser
3. Type your question in the chat input
4. Press Enter and see the structured JSON response
5. The response will show:
   - **Answer**: Short, direct answer
   - **Explanation**: 2-3 sentence explanation
   - **Confidence**: Confidence score (0 to 1)

## API Endpoints

### POST `/chat`
Send a message to the AI agent.

**Request:**
```json
{
  "message": "What is the capital of France?"
}
```

**Response:**
```json
{
  "reply": {
    "answer": "Paris",
    "explanation": "Paris is the capital of France, known for its culture and cuisine.",
    "confidence": "0.92"
  }
}
```

### GET `/health`
Check the health status and configuration.

**Response:**
```json
{
  "status": "healthy",
  "api_key_configured": true
}
```

## Project Structure

```
day2/
├── app.py              # Streamlit frontend with JSON display
├── backend.py          # FastAPI backend with JSON enforcement
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (API key)
├── run_backend.sh      # Script to start backend
├── run_frontend.sh     # Script to start frontend
└── README.md          # This file
```

## Requirements Met

✅ System prompt enforces JSON output format  
✅ Provides example of expected output format  
✅ Response can be correctly parsed by application  
✅ Safe JSON parsing with error handling  
✅ Frontend displays structured JSON nicely  

## Key Implementation Details

### System Prompt
The system prompt explicitly instructs the LLM to:
- Always respond in JSON
- Follow the exact structure (answer, explanation, confidence)
- Return error JSON if format cannot be followed

### JSON Parsing
```python
try:
    structured = json.loads(raw)
except json.JSONDecodeError:
    structured = {"error": "Model returned invalid JSON", "raw": raw}
```

This ensures the application always receives valid JSON, even if the LLM fails to follow the format.

### Frontend Display
```python
if isinstance(ai_reply, dict):
    st.json(ai_reply)  # Pretty print JSON
else:
    st.markdown(ai_reply)  # Fallback for strings
```

## Notes

- Backend must be running before starting the frontend
- The system prompt is strict about JSON format
- Invalid JSON responses are caught and returned as error objects
- Confidence scores are returned as strings (can be converted to float if needed)

