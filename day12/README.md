## Day 12 — Voice Agent

This project connects speech recognition (Whisper) to GPT-5.1 and returns both text replies and optional TTS audio. All interactions are stored in `voice_memory.json`.

### Features
- `/speech_to_text`: Converts base64 WAV audio to text via Whisper.
- `/ask_llm`: Sends recognized text to GPT-5.1.
- `/text_to_speech`: Uses GPT-4o-mini-tts to generate spoken replies.
- `voice_memory.json`: Persists every spoken input + output pair for long-term history.

### Setup
```bash
cd day12
python3 -m venv .venv && source .venv/bin/activate  # optional
pip install -r requirements.txt
```

Create `.env` with:
```
OPENAI_API_KEY=sk-...
```

### Run
```bash
python3 -m uvicorn backend:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` in Chrome, click **Start Recording**, speak your prompt, and then press **Stop Recording**. The page will show:
- Speech-to-text transcription
- LLM response
- Optional audio playback for GPT-4o-mini-tts replies

