import os
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Log file for tracking requests
LOG_FILE = "image_generation_log.jsonl"

# Initialize OpenAI client
client = None

def get_client():
    """Lazy initialization of OpenAI client."""
    global client
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        client = OpenAI(api_key=api_key)
    return client


# -------------------------------------------------------
# COST ESTIMATION (per image)
# -------------------------------------------------------

COST_PER_IMAGE = {
    "dall-e-3": {
        "1024x1024": 0.040,  # $0.040 per image
        "1024x1792": 0.080,  # $0.080 per image (landscape)
        "1792x1024": 0.080,  # $0.080 per image (portrait)
    },
    "dall-e-2": {
        "1024x1024": 0.020,
        "512x512": 0.018,
        "256x256": 0.016,
    }
}


def estimate_cost(model: str, size: str, quality: str = "standard") -> float:
    """Estimate cost in USD for image generation."""
    if model.startswith("dall-e-3"):
        size_key = size
        return COST_PER_IMAGE.get("dall-e-3", {}).get(size_key, 0.040)
    elif model.startswith("dall-e-2"):
        size_key = size
        return COST_PER_IMAGE.get("dall-e-2", {}).get(size_key, 0.020)
    else:
        # Unknown model - return 0 or estimate
        return 0.0


# -------------------------------------------------------
# LOGGING
# -------------------------------------------------------

def log_request(
    model: str,
    prompt: str,
    size: str,
    quality: str,
    steps: Optional[int],
    seed: Optional[int],
    latency_ms: float,
    cost_estimate: float,
    success: bool,
    error: Optional[str] = None,
    image_url: Optional[str] = None,
):
    """Log image generation request to JSONL file."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "prompt": prompt,
        "parameters": {
            "size": size,
            "quality": quality,
            "steps": steps,
            "seed": seed,
        },
        "latency_ms": round(latency_ms, 2),
        "cost_estimate_usd": round(cost_estimate, 4),
        "success": success,
        "error": error,
        "image_url": image_url,
    }
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    return log_entry


# -------------------------------------------------------
# IMAGE GENERATION
# -------------------------------------------------------

@app.post("/generate")
async def generate_image(request: Request):
    """
    Generate an image with logging.
    
    Body:
    {
        "prompt": "A futuristic city at sunset",
        "model": "dall-e-3",  # or "dall-e-2"
        "size": "1024x1024",   # dall-e-3: "1024x1024", "1024x1792", "1792x1024"
                              # dall-e-2: "256x256", "512x512", "1024x1024"
        "quality": "standard", # dall-e-3 only: "standard" or "hd"
        "steps": null,         # Not used for DALL·E, but logged
        "seed": null           # Not used for DALL·E, but logged
    }
    """
    start_time = time.time()
    
    try:
        body = await request.json()
        prompt = body.get("prompt", "").strip()
        model = body.get("model", "dall-e-3")
        size = body.get("size", "1024x1024")
        quality = body.get("quality", "standard")
        steps = body.get("steps")  # Not used for DALL·E but logged
        seed = body.get("seed")    # Not used for DALL·E but logged
        
        if not prompt:
            return {"success": False, "error": "prompt is required"}
        
        # Validate model
        if model not in ["dall-e-3", "dall-e-2"]:
            return {"success": False, "error": f"Unsupported model: {model}. Use 'dall-e-3' or 'dall-e-2'"}
        
        # Validate size for model
        if model == "dall-e-3":
            valid_sizes = ["1024x1024", "1024x1792", "1792x1024"]
            if size not in valid_sizes:
                return {"success": False, "error": f"Invalid size for dall-e-3: {size}. Valid: {valid_sizes}"}
            valid_quality = ["standard", "hd"]
            if quality not in valid_quality:
                return {"success": False, "error": f"Invalid quality: {quality}. Valid: {valid_quality}"}
        elif model == "dall-e-2":
            valid_sizes = ["256x256", "512x512", "1024x1024"]
            if size not in valid_sizes:
                return {"success": False, "error": f"Invalid size for dall-e-2: {size}. Valid: {valid_sizes}"}
            quality = "standard"  # dall-e-2 doesn't support quality parameter
        
        # Generate image
        openai_client = get_client()
        
        if model == "dall-e-3":
            response = openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
            )
        else:  # dall-e-2
            response = openai_client.images.generate(
                model="dall-e-2",
                prompt=prompt,
                size=size,
                n=1,
            )
        
        latency_ms = (time.time() - start_time) * 1000
        image_url = response.data[0].url
        cost_estimate = estimate_cost(model, size, quality)
        
        # Log successful request
        log_entry = log_request(
            model=model,
            prompt=prompt,
            size=size,
            quality=quality,
            steps=steps,
            seed=seed,
            latency_ms=latency_ms,
            cost_estimate=cost_estimate,
            success=True,
            image_url=image_url,
        )
        
        return {
            "success": True,
            "image_url": image_url,
            "log_entry": log_entry,
        }
        
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        error_msg = str(e)
        
        # Log failed request
        log_request(
            model=body.get("model", "unknown"),
            prompt=body.get("prompt", ""),
            size=body.get("size", "unknown"),
            quality=body.get("quality", "standard"),
            steps=body.get("steps"),
            seed=body.get("seed"),
            latency_ms=latency_ms,
            cost_estimate=0.0,
            success=False,
            error=error_msg,
        )
        
        return {
            "success": False,
            "error": error_msg,
            "latency_ms": round(latency_ms, 2),
        }


# -------------------------------------------------------
# LOG VIEWING
# -------------------------------------------------------

@app.get("/logs")
async def get_logs(limit: int = 50):
    """Get recent image generation logs."""
    if not os.path.exists(LOG_FILE):
        return {"logs": [], "count": 0}
    
    logs = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines[-limit:]:  # Get last N entries
            try:
                logs.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
    
    logs.reverse()  # Most recent first
    return {"logs": logs, "count": len(logs)}


@app.get("/logs/stats")
async def get_log_stats():
    """Get statistics from logs."""
    if not os.path.exists(LOG_FILE):
        return {
            "total_requests": 0,
            "successful": 0,
            "failed": 0,
            "total_cost_estimate": 0.0,
            "avg_latency_ms": 0.0,
        }
    
    total = 0
    successful = 0
    failed = 0
    total_cost = 0.0
    total_latency = 0.0
    
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                total += 1
                if entry.get("success"):
                    successful += 1
                    total_cost += entry.get("cost_estimate_usd", 0.0)
                else:
                    failed += 1
                total_latency += entry.get("latency_ms", 0.0)
            except json.JSONDecodeError:
                continue
    
    return {
        "total_requests": total,
        "successful": successful,
        "failed": failed,
        "total_cost_estimate_usd": round(total_cost, 4),
        "avg_latency_ms": round(total_latency / total if total > 0 else 0.0, 2),
    }


# -------------------------------------------------------
# BASIC ROUTES
# -------------------------------------------------------

@app.get("/")
async def root():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"error": "index.html not found"}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
        "log_file": LOG_FILE,
        "log_exists": os.path.exists(LOG_FILE),
    }

