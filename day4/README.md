# Day 4: Temperature Comparison

Compare AI responses at different temperature settings to understand how temperature affects accuracy, creativity, and diversity.

## Features

- ✅ Run the same prompt with 3 different temperature values (0, 0.7, 1.2)
- ✅ Side-by-side comparison of responses
- ✅ Visual analysis of differences
- ✅ Example prompts for different use cases
- ✅ All Day 4 requirements met

## What is Temperature?

Temperature controls the randomness and creativity of AI responses:

- **0.0**: Most deterministic, accurate, consistent (best for factual tasks)
- **0.7**: Balanced, default setting (good for general tasks)
- **1.2**: More creative, diverse, less predictable (best for creative tasks)

## Architecture

- **Backend**: FastAPI (runs on port 8000)
- **Frontend**: Streamlit (runs on port 8501)
- **Model**: OpenAI GPT-4o-mini
- **Temperatures**: 0.0, 0.7, 1.2

## Setup

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file in the `day4/` folder:

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
3. Enter a prompt (or use example prompts)
4. Click "Compare Temperatures"
5. View side-by-side comparison of all 3 temperature responses
6. Analyze the differences in accuracy, creativity, and diversity

## API Endpoints

### POST `/compare`
Run the same prompt with three different temperature values.

**Request:**
```json
{
  "prompt": "Explain quantum computing in simple terms"
}
```

**Response:**
```json
{
  "prompt": "Explain quantum computing in simple terms",
  "results": {
    "temp_0.0": {
      "temperature": 0.0,
      "response": "...",
      "tokens_used": 150
    },
    "temp_0.7": {
      "temperature": 0.7,
      "response": "...",
      "tokens_used": 152
    },
    "temp_1.2": {
      "temperature": 1.2,
      "response": "...",
      "tokens_used": 148
    }
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
day4/
├── app.py              # Streamlit frontend with temperature comparison
├── backend.py          # FastAPI backend with temperature parameter
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (API key)
├── run_backend.sh      # Script to start backend
├── run_frontend.sh     # Script to start frontend
└── README.md          # This file
```

## Requirements Met

✅ Run same prompt with temperature values: 0, 0.7, 1.2  
✅ Compare outputs in terms of accuracy, creativity, diversity  
✅ Describe which temperature works best for which types of tasks  
✅ Provide examples showing how answers change with different temperature  

## Temperature Analysis

### Temperature 0.0 (Deterministic)
**Best for:**
- Factual Q&A
- Code generation
- Data extraction
- Technical documentation
- Mathematical problems

**Characteristics:**
- Most accurate and consistent
- Minimal variation between runs
- Focused and precise
- Less creative

### Temperature 0.7 (Balanced)
**Best for:**
- General conversation
- Balanced tasks
- Most common use cases
- Default setting

**Characteristics:**
- Good balance of accuracy and creativity
- Natural language flow
- Moderate variation
- Reliable for most tasks

### Temperature 1.2 (Creative)
**Best for:**
- Creative writing
- Brainstorming
- Ideation
- Storytelling
- Marketing copy

**Characteristics:**
- More diverse responses
- Higher creativity
- Less predictable
- May sacrifice some accuracy

## Example Comparisons

### Factual Question
**Prompt:** "What is the capital of France?"

- **Temp 0.0**: "The capital of France is Paris."
- **Temp 0.7**: "The capital of France is Paris, a city known for its rich history and culture."
- **Temp 1.2**: "Ah, Paris! The City of Light, the capital of France, where art, history, and romance converge..."

### Creative Task
**Prompt:** "Write a short story about a robot."

- **Temp 0.0**: Structured, factual, minimal creativity
- **Temp 0.7**: Balanced narrative with some creativity
- **Temp 1.2**: Highly creative, varied storytelling, unique perspectives

## Notes

- Backend must be running before starting the frontend
- All three temperature responses are generated in parallel
- Token usage may vary slightly between temperatures
- Higher temperatures may produce longer or more varied responses

