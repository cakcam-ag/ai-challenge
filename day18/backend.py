import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
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

# Files
STYLE_PROFILES_FILE = "style_profiles.json"
GENERATION_LOG_FILE = "style_generation_log.jsonl"

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
# STYLE PROFILES
# -------------------------------------------------------

def load_style_profiles() -> Dict[str, Any]:
    """Load style profiles from JSON file."""
    if not os.path.exists(STYLE_PROFILES_FILE):
        return {"profiles": []}
    with open(STYLE_PROFILES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_profile(profile_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific style profile by ID."""
    profiles_data = load_style_profiles()
    for profile in profiles_data.get("profiles", []):
        if profile.get("id") == profile_id:
            return profile
    return None


# -------------------------------------------------------
# PROMPT TEMPLATE SYSTEM
# -------------------------------------------------------

def build_prompt(
    base_subject: str,
    style_profile: Dict[str, Any],
    aspect_ratio: str = "1024x1024"
) -> str:
    """
    Build a prompt using template: base subject + style description + aspect ratio.
    """
    style_desc = style_profile.get("style_description", "")
    color_palette = style_profile.get("color_palette", "")
    mood = style_profile.get("mood", "")
    
    # Build comprehensive prompt
    prompt_parts = [
        base_subject,
        f"Style: {style_desc}",
        f"Color palette: {color_palette}",
        f"Mood: {mood}",
    ]
    
    # Add visual style details
    visual_style = style_profile.get("visual_style", {})
    if visual_style:
        style_notes = [
            f"Visual type: {visual_style.get('type', '')}",
            f"Texture: {visual_style.get('texture', '')}",
            f"Detail level: {visual_style.get('detail_level', '')}",
            f"Lighting: {visual_style.get('lighting', '')}",
            f"Composition: {visual_style.get('composition', '')}",
        ]
        prompt_parts.extend(style_notes)
    
    # Add do's
    dos = style_profile.get("dos", [])
    if dos:
        prompt_parts.append("Must include: " + ", ".join(dos[:3]))  # Top 3 do's
    
    # Add don'ts
    donts = style_profile.get("donts", [])
    if donts:
        prompt_parts.append("Avoid: " + ", ".join(donts[:3]))  # Top 3 don'ts
    
    return ". ".join(prompt_parts) + "."


# -------------------------------------------------------
# IMAGE GENERATION
# -------------------------------------------------------

def estimate_cost(size: str) -> float:
    """Estimate cost for DALL·E 3."""
    costs = {
        "1024x1024": 0.040,
        "1024x1792": 0.080,
        "1792x1024": 0.080,
    }
    return costs.get(size, 0.040)


def log_generation(
    base_subject: str,
    profile_id: str,
    profile_name: str,
    aspect_ratio: str,
    prompt: str,
    image_url: str,
    latency_ms: float,
    cost: float,
    success: bool,
    error: Optional[str] = None,
):
    """Log image generation with style profile info."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "base_subject": base_subject,
        "style_profile": {
            "id": profile_id,
            "name": profile_name,
        },
        "aspect_ratio": aspect_ratio,
        "prompt": prompt,
        "image_url": image_url,
        "latency_ms": round(latency_ms, 2),
        "cost_estimate_usd": round(cost, 4),
        "success": success,
        "error": error,
    }
    
    with open(GENERATION_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    return log_entry


@app.post("/generate")
async def generate_image(request: Request):
    """
    Generate an image using style profile and prompt template.
    
    Body:
    {
        "base_subject": "A coffee cup",
        "profile_id": "minimal_modern",
        "aspect_ratio": "1024x1024"
    }
    """
    start_time = time.time()
    
    try:
        body = await request.json()
        base_subject = body.get("base_subject", "").strip()
        profile_id = body.get("profile_id", "")
        aspect_ratio = body.get("aspect_ratio", "1024x1024")
        
        if not base_subject:
            return {"success": False, "error": "base_subject is required"}
        
        if not profile_id:
            return {"success": False, "error": "profile_id is required"}
        
        # Get style profile
        profile = get_profile(profile_id)
        if not profile:
            return {"success": False, "error": f"Style profile '{profile_id}' not found"}
        
        # Build prompt using template
        prompt = build_prompt(base_subject, profile, aspect_ratio)
        
        # Generate image
        openai_client = get_client()
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=aspect_ratio,
            quality="standard",
            n=1,
        )
        
        latency_ms = (time.time() - start_time) * 1000
        image_url = response.data[0].url
        cost = estimate_cost(aspect_ratio)
        
        # Log generation
        log_entry = log_generation(
            base_subject=base_subject,
            profile_id=profile_id,
            profile_name=profile.get("name", ""),
            aspect_ratio=aspect_ratio,
            prompt=prompt,
            image_url=image_url,
            latency_ms=latency_ms,
            cost=cost,
            success=True,
        )
        
        return {
            "success": True,
            "image_url": image_url,
            "prompt": prompt,
            "profile": {
                "id": profile_id,
                "name": profile.get("name", ""),
            },
            "log_entry": log_entry,
        }
        
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        error_msg = str(e)
        
        log_generation(
            base_subject=body.get("base_subject", ""),
            profile_id=body.get("profile_id", "unknown"),
            profile_name="unknown",
            aspect_ratio=body.get("aspect_ratio", "1024x1024"),
            prompt="",
            image_url="",
            latency_ms=latency_ms,
            cost=0.0,
            success=False,
            error=error_msg,
        )
        
        return {
            "success": False,
            "error": error_msg,
            "latency_ms": round(latency_ms, 2),
        }


@app.post("/generate_grid")
async def generate_grid(request: Request):
    """
    Generate a grid of images - one per style profile for the same subject.
    
    Body:
    {
        "base_subject": "A coffee cup",
        "aspect_ratio": "1024x1024",
        "profile_ids": ["minimal_modern", "vibrant_playful", "elegant_luxury"]  # optional, defaults to all
    }
    """
    try:
        body = await request.json()
        base_subject = body.get("base_subject", "").strip()
        aspect_ratio = body.get("aspect_ratio", "1024x1024")
        profile_ids = body.get("profile_ids", [])
        
        if not base_subject:
            return {"success": False, "error": "base_subject is required"}
        
        # Get all profiles or specified ones
        profiles_data = load_style_profiles()
        if profile_ids:
            profiles = [p for p in profiles_data.get("profiles", []) if p.get("id") in profile_ids]
        else:
            profiles = profiles_data.get("profiles", [])
        
        if not profiles:
            return {"success": False, "error": "No style profiles found"}
        
        # Generate image for each profile
        results = []
        for profile in profiles:
            profile_id = profile.get("id")
            
            # Call generate endpoint logic
            start_time = time.time()
            try:
                prompt = build_prompt(base_subject, profile, aspect_ratio)
                
                openai_client = get_client()
                response = openai_client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size=aspect_ratio,
                    quality="standard",
                    n=1,
                )
                
                latency_ms = (time.time() - start_time) * 1000
                image_url = response.data[0].url
                cost = estimate_cost(aspect_ratio)
                
                log_generation(
                    base_subject=base_subject,
                    profile_id=profile_id,
                    profile_name=profile.get("name", ""),
                    aspect_ratio=aspect_ratio,
                    prompt=prompt,
                    image_url=image_url,
                    latency_ms=latency_ms,
                    cost=cost,
                    success=True,
                )
                
                results.append({
                    "success": True,
                    "profile_id": profile_id,
                    "profile_name": profile.get("name", ""),
                    "image_url": image_url,
                    "prompt": prompt,
                    "latency_ms": round(latency_ms, 2),
                    "cost": round(cost, 4),
                })
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                results.append({
                    "success": False,
                    "profile_id": profile_id,
                    "profile_name": profile.get("name", ""),
                    "error": str(e),
                    "latency_ms": round(latency_ms, 2),
                })
        
        return {
            "success": True,
            "base_subject": base_subject,
            "aspect_ratio": aspect_ratio,
            "results": results,
            "total_generated": sum(1 for r in results if r.get("success")),
            "total_failed": sum(1 for r in results if not r.get("success")),
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# -------------------------------------------------------
# PROFILE MANAGEMENT
# -------------------------------------------------------

@app.get("/profiles")
async def get_profiles():
    """Get all style profiles."""
    profiles_data = load_style_profiles()
    return profiles_data


@app.get("/profiles/{profile_id}")
async def get_profile_endpoint(profile_id: str):
    """Get a specific style profile."""
    profile = get_profile(profile_id)
    if not profile:
        return {"success": False, "error": f"Profile '{profile_id}' not found"}
    return {"success": True, "profile": profile}


# -------------------------------------------------------
# LOGS
# -------------------------------------------------------

@app.get("/logs")
async def get_logs(limit: int = 50):
    """Get recent generation logs."""
    if not os.path.exists(GENERATION_LOG_FILE):
        return {"logs": [], "count": 0}
    
    logs = []
    with open(GENERATION_LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines[-limit:]:
            try:
                logs.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
    
    logs.reverse()
    return {"logs": logs, "count": len(logs)}


@app.get("/logs/stats")
async def get_log_stats():
    """Get statistics by style profile."""
    if not os.path.exists(GENERATION_LOG_FILE):
        return {"stats": {}}
    
    stats = {}
    with open(GENERATION_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if not entry.get("success"):
                    continue
                
                profile_id = entry.get("style_profile", {}).get("id", "unknown")
                if profile_id not in stats:
                    stats[profile_id] = {
                        "count": 0,
                        "total_cost": 0.0,
                        "avg_latency": 0.0,
                        "latencies": [],
                    }
                
                stats[profile_id]["count"] += 1
                stats[profile_id]["total_cost"] += entry.get("cost_estimate_usd", 0.0)
                stats[profile_id]["latencies"].append(entry.get("latency_ms", 0.0))
            except json.JSONDecodeError:
                continue
    
    # Calculate averages
    for profile_id in stats:
        latencies = stats[profile_id]["latencies"]
        if latencies:
            stats[profile_id]["avg_latency"] = round(sum(latencies) / len(latencies), 2)
        stats[profile_id]["total_cost"] = round(stats[profile_id]["total_cost"], 4)
        del stats[profile_id]["latencies"]
    
    return {"stats": stats}


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
    profiles_data = load_style_profiles()
    return {
        "status": "ok",
        "api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
        "profiles_count": len(profiles_data.get("profiles", [])),
        "log_file": GENERATION_LOG_FILE,
    }

