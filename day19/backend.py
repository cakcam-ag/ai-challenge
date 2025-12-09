import os
import json
import time
import base64
import requests
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
QA_LOG_FILE = "vision_qa_log.jsonl"

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
    """Build a prompt using template: base subject + style description + aspect ratio."""
    style_desc = style_profile.get("style_description", "")
    color_palette = style_profile.get("color_palette", "")
    mood = style_profile.get("mood", "")
    
    prompt_parts = [
        base_subject,
        f"Style: {style_desc}",
        f"Color palette: {color_palette}",
        f"Mood: {mood}",
    ]
    
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
    
    dos = style_profile.get("dos", [])
    if dos:
        prompt_parts.append("Must include: " + ", ".join(dos[:3]))
    
    donts = style_profile.get("donts", [])
    if donts:
        prompt_parts.append("Avoid: " + ", ".join(donts[:3]))
    
    return ". ".join(prompt_parts) + "."


# -------------------------------------------------------
# VISION QA SYSTEM
# -------------------------------------------------------

def download_image_as_base64(image_url: str) -> str:
    """Download image from URL and convert to base64."""
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        image_data = response.content
        base64_image = base64.b64encode(image_data).decode('utf-8')
        return base64_image
    except Exception as e:
        raise Exception(f"Failed to download image: {str(e)}")


def build_qa_checklist(profile: Dict[str, Any], base_subject: str) -> str:
    """Build QA checklist based on style profile and base subject."""
    checklist_items = [
        f"0. SUBJECT PRESENCE (CRITICAL): Is the base subject '{base_subject}' clearly visible and present in the image? This is the MOST IMPORTANT check - if the subject is missing, the image MUST FAIL.",
        f"1. Color Palette Compliance: Does the image use the expected color palette? ({profile.get('color_palette', '')})",
        f"2. Style Template Match: Does it follow the chosen style? ({profile.get('visual_style', {}).get('type', '')})",
        f"3. Mood Alignment: Does the mood match? ({profile.get('mood', '')})",
        f"4. Visual Style Elements: {profile.get('visual_style', {}).get('texture', '')}, {profile.get('visual_style', {}).get('lighting', '')}",
    ]
    
    # Add do's as required elements
    dos = profile.get("dos", [])
    if dos:
        checklist_items.append(f"5. Required Elements: {', '.join(dos[:3])}")
    
    # Add don'ts as forbidden elements
    donts = profile.get("donts", [])
    if donts:
        checklist_items.append(f"6. Forbidden Elements: {', '.join(donts[:3])}")
    
    return "\n".join(checklist_items)


async def analyze_image_vision(image_url: str, profile: Dict[str, Any], base_subject: str) -> Dict[str, Any]:
    """
    Use vision model to analyze generated image against style profile.
    Returns: score (0-100), passed (bool), feedback (str), checklist_results (dict)
    """
    try:
        # Download image and convert to base64
        base64_image = download_image_as_base64(image_url)
        
        # Build QA prompt
        checklist = build_qa_checklist(profile, base_subject)
        
        qa_prompt = f"""You are a quality assurance agent evaluating an AI-generated image.

CRITICAL: The base subject MUST be present in the image. If the subject is missing, the image MUST FAIL regardless of style compliance.

Expected Style Profile: {profile.get('name', '')}
Base Subject: {base_subject}

EVALUATION CHECKLIST:
{checklist}

IMPORTANT RULES:
- If the base subject is NOT clearly visible/present in the image, the overall score MUST be below 50 and passed MUST be false
- Subject presence is more important than style compliance
- A beautiful image that doesn't show the requested subject is a FAILURE

Analyze the provided image and evaluate it against each checklist item.

For each item, provide:
- PASS or FAIL
- Brief explanation (1-2 sentences)

Then provide:
- Overall score (0-100): 
  * If subject is missing: score MUST be 0-40
  * If subject is present but style is poor: 50-69
  * If subject is present and style is good: 70-100
- Final verdict: PASS (score >= 70 AND subject is present) or FAIL (score < 70 OR subject is missing)
- Detailed feedback: What works well? What doesn't match? Is the subject clearly visible?

Format your response as JSON:
{{
  "checklist_results": {{
    "subject_presence": {{"pass": true/false, "explanation": "Is the base subject clearly visible?"}},
    "color_palette": {{"pass": true/false, "explanation": "..."}},
    "style_template": {{"pass": true/false, "explanation": "..."}},
    "mood": {{"pass": true/false, "explanation": "..."}},
    "visual_elements": {{"pass": true/false, "explanation": "..."}},
    "required_elements": {{"pass": true/false, "explanation": "..."}},
    "forbidden_elements": {{"pass": true/false, "explanation": "..."}}
  }},
  "overall_score": 85,
  "passed": true,
  "feedback": "Detailed feedback here..."
}}
"""
        
        openai_client = get_client()
        
        # Use GPT-5.1 Vision to analyze
        response = openai_client.chat.completions.create(
            model="gpt-5.1",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": qa_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.3,
            max_completion_tokens=1000,
        )
        
        analysis_text = response.choices[0].message.content.strip()
        
        # Try to parse JSON from response
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in analysis_text:
                json_start = analysis_text.find("```json") + 7
                json_end = analysis_text.find("```", json_start)
                analysis_text = analysis_text[json_start:json_end].strip()
            elif "```" in analysis_text:
                json_start = analysis_text.find("```") + 3
                json_end = analysis_text.find("```", json_start)
                analysis_text = analysis_text[json_start:json_end].strip()
            
            analysis = json.loads(analysis_text)
        except json.JSONDecodeError:
            # Fallback: extract score and verdict from text
            score = 50  # Default
            passed = False
            
            # Try to find score
            import re
            score_match = re.search(r'score[:\s]+(\d+)', analysis_text, re.IGNORECASE)
            if score_match:
                score = int(score_match.group(1))
            
            # Check if subject is mentioned as missing
            subject_missing = any(phrase in analysis_text.lower() for phrase in [
                "subject is missing",
                "no subject",
                "subject not visible",
                "subject not present",
                "does not show",
                "doesn't show",
                "missing the subject",
            ])
            
            if subject_missing:
                score = min(score, 40)  # Cap at 40 if subject missing
                passed = False
            elif "pass" in analysis_text.lower() and score >= 70:
                passed = True
            elif "fail" in analysis_text.lower() or score < 70:
                passed = False
            
            analysis = {
                "checklist_results": {},
                "overall_score": score,
                "passed": passed,
                "feedback": analysis_text,
            }
        
        return {
            "success": True,
            "score": analysis.get("overall_score", 50),
            "passed": analysis.get("passed", False),
            "feedback": analysis.get("feedback", ""),
            "checklist_results": analysis.get("checklist_results", {}),
            "raw_analysis": analysis_text,
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "score": 0,
            "passed": False,
        }


def log_qa_result(
    image_url: str,
    profile_id: str,
    profile_name: str,
    base_subject: str,
    analysis: Dict[str, Any],
    generation_latency: float,
    qa_latency: float,
    passed: bool,
):
    """Log QA result."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "image_url": image_url,
        "base_subject": base_subject,
        "style_profile": {
            "id": profile_id,
            "name": profile_name,
        },
        "qa_analysis": {
            "score": analysis.get("score", 0),
            "passed": passed,
            "feedback": analysis.get("feedback", ""),
            "checklist_results": analysis.get("checklist_results", {}),
        },
        "latency": {
            "generation_ms": round(generation_latency, 2),
            "qa_analysis_ms": round(qa_latency, 2),
            "total_ms": round(generation_latency + qa_latency, 2),
        },
    }
    
    with open(QA_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    return log_entry


# -------------------------------------------------------
# GENERATE + QA PIPELINE
# -------------------------------------------------------

def estimate_cost(size: str) -> float:
    """Estimate cost for DALL·E 3."""
    costs = {
        "1024x1024": 0.040,
        "1024x1792": 0.080,
        "1792x1024": 0.080,
    }
    return costs.get(size, 0.040)


@app.post("/generate_with_qa")
async def generate_with_qa(request: Request):
    """
    Generate image and automatically QA it.
    
    Body:
    {
        "base_subject": "A coffee cup",
        "profile_id": "minimal_modern",
        "aspect_ratio": "1024x1024",
        "quality_threshold": 70,  # Minimum score to pass
        "max_retries": 3  # How many times to retry if QA fails
    }
    """
    try:
        body = await request.json()
        base_subject = body.get("base_subject", "").strip()
        profile_id = body.get("profile_id", "")
        aspect_ratio = body.get("aspect_ratio", "1024x1024")
        quality_threshold = int(body.get("quality_threshold", 70))
        max_retries = int(body.get("max_retries", 3))
        
        if not base_subject:
            return {"success": False, "error": "base_subject is required"}
        
        if not profile_id:
            return {"success": False, "error": "profile_id is required"}
        
        profile = get_profile(profile_id)
        if not profile:
            return {"success": False, "error": f"Style profile '{profile_id}' not found"}
        
        # Generate → Analyze → Score pipeline
        attempts = []
        
        for attempt_num in range(max_retries):
            attempt_start = time.time()
            
            # Step 1: Generate image
            try:
                prompt = build_prompt(base_subject, profile, aspect_ratio)
                openai_client = get_client()
                
                gen_start = time.time()
                response = openai_client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size=aspect_ratio,
                    quality="standard",
                    n=1,
                )
                gen_latency = (time.time() - gen_start) * 1000
                
                image_url = response.data[0].url
                
            except Exception as e:
                attempts.append({
                    "attempt": attempt_num + 1,
                    "success": False,
                    "error": f"Generation failed: {str(e)}",
                })
                continue
            
            # Step 2: Analyze with vision model
            qa_start = time.time()
            analysis = await analyze_image_vision(image_url, profile, base_subject)
            qa_latency = (time.time() - qa_start) * 1000
            
            if not analysis.get("success"):
                attempts.append({
                    "attempt": attempt_num + 1,
                    "success": False,
                    "error": f"QA analysis failed: {analysis.get('error', 'Unknown')}",
                    "image_url": image_url,
                })
                continue
            
            score = analysis.get("score", 0)
            passed = analysis.get("passed", False) and score >= quality_threshold
            
            # Step 3: Log result
            log_qa_result(
                image_url=image_url,
                profile_id=profile_id,
                profile_name=profile.get("name", ""),
                base_subject=base_subject,
                analysis=analysis,
                generation_latency=gen_latency,
                qa_latency=qa_latency,
                passed=passed,
            )
            
            attempt_result = {
                "attempt": attempt_num + 1,
                "success": True,
                "image_url": image_url,
                "prompt": prompt,
                "score": score,
                "passed": passed,
                "feedback": analysis.get("feedback", ""),
                "checklist_results": analysis.get("checklist_results", {}),
                "latency": {
                    "generation_ms": round(gen_latency, 2),
                    "qa_analysis_ms": round(qa_latency, 2),
                    "total_ms": round(gen_latency + qa_latency, 2),
                },
            }
            
            attempts.append(attempt_result)
            
            # If passed, return immediately
            if passed:
                return {
                    "success": True,
                    "image_url": image_url,
                    "prompt": prompt,
                    "profile": {
                        "id": profile_id,
                        "name": profile.get("name", ""),
                    },
                    "qa_result": {
                        "score": score,
                        "passed": True,
                        "feedback": analysis.get("feedback", ""),
                        "checklist_results": analysis.get("checklist_results", {}),
                    },
                    "attempts": attempts,
                    "total_attempts": attempt_num + 1,
                }
        
        # All attempts failed or didn't pass threshold
        return {
            "success": False,
            "error": f"Failed to generate image that passes QA threshold ({quality_threshold}) after {max_retries} attempts",
            "attempts": attempts,
            "best_score": max([a.get("score", 0) for a in attempts if a.get("success")], default=0),
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/analyze_image")
async def analyze_image_endpoint(request: Request):
    """
    Analyze an existing image URL against a style profile.
    
    Body:
    {
        "image_url": "https://...",
        "profile_id": "minimal_modern",
        "base_subject": "A coffee cup"
    }
    """
    try:
        body = await request.json()
        image_url = body.get("image_url", "").strip()
        profile_id = body.get("profile_id", "")
        base_subject = body.get("base_subject", "Unknown subject")
        
        if not image_url:
            return {"success": False, "error": "image_url is required"}
        
        if not profile_id:
            return {"success": False, "error": "profile_id is required"}
        
        profile = get_profile(profile_id)
        if not profile:
            return {"success": False, "error": f"Style profile '{profile_id}' not found"}
        
        qa_start = time.time()
        analysis = await analyze_image_vision(image_url, profile, base_subject)
        qa_latency = (time.time() - qa_start) * 1000
        
        if not analysis.get("success"):
            return {"success": False, "error": analysis.get("error", "QA analysis failed")}
        
        return {
            "success": True,
            "image_url": image_url,
            "profile": {
                "id": profile_id,
                "name": profile.get("name", ""),
            },
            "qa_result": {
                "score": analysis.get("score", 0),
                "passed": analysis.get("passed", False),
                "feedback": analysis.get("feedback", ""),
                "checklist_results": analysis.get("checklist_results", {}),
            },
            "latency_ms": round(qa_latency, 2),
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
    """Get recent QA logs."""
    if not os.path.exists(QA_LOG_FILE):
        return {"logs": [], "count": 0}
    
    logs = []
    with open(QA_LOG_FILE, "r", encoding="utf-8") as f:
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
    """Get QA statistics."""
    if not os.path.exists(QA_LOG_FILE):
        return {
            "total_analyzed": 0,
            "passed": 0,
            "failed": 0,
            "avg_score": 0.0,
            "by_profile": {},
        }
    
    total = 0
    passed = 0
    failed = 0
    scores = []
    by_profile = {}
    
    with open(QA_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                total += 1
                
                qa = entry.get("qa_analysis", {})
                score = qa.get("score", 0)
                passed_flag = qa.get("passed", False)
                
                scores.append(score)
                if passed_flag:
                    passed += 1
                else:
                    failed += 1
                
                profile_id = entry.get("style_profile", {}).get("id", "unknown")
                if profile_id not in by_profile:
                    by_profile[profile_id] = {"count": 0, "passed": 0, "scores": []}
                
                by_profile[profile_id]["count"] += 1
                if passed_flag:
                    by_profile[profile_id]["passed"] += 1
                by_profile[profile_id]["scores"].append(score)
                
            except json.JSONDecodeError:
                continue
    
    # Calculate averages
    for profile_id in by_profile:
        scores_list = by_profile[profile_id]["scores"]
        if scores_list:
            by_profile[profile_id]["avg_score"] = round(sum(scores_list) / len(scores_list), 2)
        del by_profile[profile_id]["scores"]
    
    return {
        "total_analyzed": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / total * 100, 2) if total > 0 else 0.0,
        "avg_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
        "by_profile": by_profile,
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
    profiles_data = load_style_profiles()
    return {
        "status": "ok",
        "api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
        "profiles_count": len(profiles_data.get("profiles", [])),
        "log_file": QA_LOG_FILE,
    }

