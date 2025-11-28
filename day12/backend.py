"""
Day 12 — Voice Agent
Speech ➜ Text (Whisper) ➜ GPT-5.1 ➜ Text ➜ Speech (GPT-4o-mini-tts)
Also persisting interactions into voice_memory.json
"""

import os
import json
import base64
import uuid
from typing import Dict, Any

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "voice_memory.json")


def record_memory(entry: Dict[str, Any]) -> None:
    try:
        memory = []
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                memory = json.load(f)
        memory.append(entry)
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2)
    except Exception as e:
        print("Memory write error:", e)


def openai_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }


@app.post("/speech_to_text")
async def speech_to_text(payload: Dict[str, Any]):
    """Receive base64 wav audio and convert to text using Whisper."""
    if not OPENAI_API_KEY:
        return {"success": False, "error": "OPENAI_API_KEY not configured"}

    audio_b64 = payload.get("audio")
    if not audio_b64:
        return {"success": False, "error": "Missing audio data"}

    temp_path = os.path.join(os.path.dirname(__file__), f"temp_{uuid.uuid4().hex}.wav")
    try:
        audio_bytes = base64.b64decode(audio_b64)
        with open(temp_path, "wb") as f:
            f.write(audio_bytes)

        url = "https://api.openai.com/v1/audio/transcriptions"
        files = {
            "file": ("audio.wav", open(temp_path, "rb"), "audio/wav"),
        }
        data = {"model": "whisper-1"}
        resp = requests.post(url, headers=openai_headers(), data=data, files=files, timeout=120)
        transcript = resp.json()
        text = transcript.get("text")
        if not resp.ok or not text:
            return {"success": False, "error": transcript}

        record_memory({"type": "user-speech", "text": text})
        return {"success": True, "text": text}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass


@app.post("/ask_llm")
async def ask_llm(payload: Dict[str, Any]):
    if not OPENAI_API_KEY:
        return {"success": False, "error": "OPENAI_API_KEY not configured"}

    user_text = payload.get("text", "").strip()
    if not user_text:
        return {"success": False, "error": "Missing text"}

    url = "https://api.openai.com/v1/chat/completions"
    body = {
        "model": "gpt-5.1",
        "messages": [
            {"role": "system", "content": "You are a helpful voice assistant."},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.6,
    }

    try:
        resp = requests.post(
            url,
            headers={**openai_headers(), "Content-Type": "application/json"},
            json=body,
            timeout=120,
        )
        data = resp.json()
        if not resp.ok:
            return {"success": False, "error": data}

        answer = data["choices"][0]["message"]["content"]
        record_memory({"type": "assistant-reply", "text": answer})
        return {"success": True, "answer": answer}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/text_to_speech")
async def text_to_speech(payload: Dict[str, Any]):
    if not OPENAI_API_KEY:
        return {"success": False, "error": "OPENAI_API_KEY not configured"}

    text = payload.get("text", "").strip()
    if not text:
        return {"success": False, "error": "Missing text"}

    url = "https://api.openai.com/v1/audio/speech"
    body = {
        "model": "gpt-4o-mini-tts",
        "voice": "alloy",
        "input": text,
    }

    try:
        resp = requests.post(
            url,
            headers={**openai_headers(), "Content-Type": "application/json"},
            json=body,
            timeout=120,
        )
        if not resp.ok:
            return {"success": False, "error": resp.text}

        audio_b64 = base64.b64encode(resp.content).decode()
        record_memory({"type": "tts", "text": text})
        return {"success": True, "audio": audio_b64}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/")
async def serve_ui():
    path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "index.html not found"}

