# Day 1: Simple AI Agent

A simple AI agent that accepts user questions and returns AI responses via an HTTP client.

## Features

- ✅ FastAPI backend with HTTP API
- ✅ Streamlit frontend UI
- ✅ OpenAI GPT-4o-mini integration
- ✅ Clean, modern interface
- ✅ Real-time chat experience

## Architecture

- **Backend**: FastAPI (runs on port 8000)
- **Frontend**: Streamlit (runs on port 8501)
- **Model**: OpenAI GPT-4o-mini

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or with pip3:
```bash
pip3 install -r requirements.txt
```

### 2. Configure API Key

The `.env` file is already configured with your API key. If you need to change it:

```bash
# Edit .env file
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
4. Press Enter or wait for the AI response
5. Continue the conversation!

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
  "reply": "The capital of France is Paris."
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
day1/
├── app.py              # Streamlit frontend UI
├── backend.py          # FastAPI backend with OpenAI integration
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (API key)
├── run_backend.sh      # Script to start backend
├── run_frontend.sh     # Script to start frontend
└── README.md          # This file
```

## Requirements Met

✅ Accepts user input via web interface  
✅ Makes HTTP requests to LLM API (via FastAPI backend)  
✅ Returns and displays AI responses  
✅ Clean, functional interface  

## Notes

- Backend must be running before starting the frontend
- The backend uses FastAPI with automatic API documentation at `http://localhost:8000/docs`
- Streamlit provides a modern, interactive UI without writing HTML/CSS/JS
- All communication happens via HTTP requests between frontend and backend
