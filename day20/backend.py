import os
import json
import time
import base64
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, UploadFile, File
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
DB_PATH = "productivity_assistant.db"
MEETINGS_LOG = "meetings.jsonl"
TASKS_LOG = "tasks.jsonl"

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
# DATABASE INITIALIZATION
# -------------------------------------------------------

def init_db():
    """Initialize SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    
    # Meetings table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            notes TEXT,
            summary TEXT,
            action_items TEXT,
            participants TEXT,
            date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tasks table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            priority TEXT,
            status TEXT DEFAULT 'pending',
            due_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT
        )
    """)
    
    # Email drafts table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS email_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            body TEXT,
            recipient TEXT,
            context TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

init_db()


# -------------------------------------------------------
# MEETING NOTES PROCESSING
# -------------------------------------------------------

@app.post("/meetings/process")
async def process_meeting_notes(request: Request):
    """
    Process meeting notes:
    1. Summarize the meeting
    2. Extract action items
    3. Identify participants
    4. Store in database
    
    Body: {
        "title": "Team Standup",
        "notes": "We discussed...",
        "date": "2024-01-15" (optional)
    }
    """
    try:
        body = await request.json()
        title = body.get("title", "").strip()
        notes = body.get("notes", "").strip()
        date = body.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        if not notes:
            return {"success": False, "error": "notes are required"}
        
        if not title:
            title = f"Meeting - {date}"
        
        openai_client = get_client()
        
        # Generate summary
        summary_prompt = f"""Summarize the following meeting notes in 3-5 bullet points:

{notes}

Provide a concise summary focusing on key decisions and topics discussed."""
        
        summary_resp = openai_client.chat.completions.create(
            model="gpt-5.1",
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.7,
            max_completion_tokens=500,
        )
        summary = summary_resp.choices[0].message.content.strip()
        
        # Extract action items
        action_items_prompt = f"""Extract action items from the following meeting notes. Format as a JSON array of objects with "person" and "task" fields:

{notes}

Example format:
[
  {{"person": "John", "task": "Review PR #123"}},
  {{"person": "Sarah", "task": "Update documentation"}}
]

If no action items, return empty array []. Return ONLY valid JSON."""
        
        action_items_resp = openai_client.chat.completions.create(
            model="gpt-5.1",
            messages=[{"role": "user", "content": action_items_prompt}],
            temperature=0.3,
            max_completion_tokens=500,
        )
        action_items_text = action_items_resp.choices[0].message.content.strip()
        
        # Parse action items JSON
        try:
            if "```json" in action_items_text:
                json_start = action_items_text.find("```json") + 7
                json_end = action_items_text.find("```", json_start)
                action_items_text = action_items_text[json_start:json_end].strip()
            elif "```" in action_items_text:
                json_start = action_items_text.find("```") + 3
                json_end = action_items_text.find("```", json_start)
                action_items_text = action_items_text[json_start:json_end].strip()
            
            action_items = json.loads(action_items_text)
        except:
            action_items = []
        
        # Extract participants
        participants_prompt = f"""List the participants mentioned in these meeting notes. Return as a comma-separated list of names:

{notes}

If no names mentioned, return "Unknown"."""
        
        participants_resp = openai_client.chat.completions.create(
            model="gpt-5.1",
            messages=[{"role": "user", "content": participants_prompt}],
            temperature=0.3,
            max_completion_tokens=200,
        )
        participants = participants_resp.choices[0].message.content.strip()
        
        # Store in database
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO meetings (title, notes, summary, action_items, participants, date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            title,
            notes,
            summary,
            json.dumps(action_items),
            participants,
            date
        ))
        meeting_id = cur.lastrowid
        conn.commit()
        conn.close()
        
        # Log to file
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "meeting_id": meeting_id,
            "title": title,
            "date": date,
        }
        with open(MEETINGS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        # Create tasks from action items
        task_ids = []
        if action_items:
            for item in action_items:
                person = item.get("person", "Unknown")
                task_desc = item.get("task", "")
                if task_desc:
                    task_id = create_task(
                        title=f"Action: {task_desc}",
                        description=f"From meeting: {title}\nAssigned to: {person}",
                        priority="medium"
                    )
                    task_ids.append(task_id)
        
        return {
            "success": True,
            "meeting_id": meeting_id,
            "summary": summary,
            "action_items": action_items,
            "participants": participants,
            "tasks_created": len(task_ids),
            "task_ids": task_ids,
        }
        
    except Exception as e:
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


@app.get("/meetings/list")
async def list_meetings():
    """List all meetings."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute("""
            SELECT id, title, date, summary, created_at
            FROM meetings
            ORDER BY created_at DESC
            LIMIT 50
        """)
        
        meetings = []
        for row in cur.fetchall():
            meetings.append({
                "id": row[0],
                "title": row[1],
                "date": row[2],
                "summary": row[3],
                "created_at": row[4],
            })
        
        conn.close()
        return {"success": True, "meetings": meetings}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/meetings/{meeting_id}")
async def get_meeting(meeting_id: int):
    """Get a specific meeting."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute("""
            SELECT id, title, notes, summary, action_items, participants, date, created_at
            FROM meetings
            WHERE id = ?
        """, (meeting_id,))
        
        row = cur.fetchone()
        conn.close()
        
        if not row:
            return {"success": False, "error": "Meeting not found"}
        
        return {
            "success": True,
            "meeting": {
                "id": row[0],
                "title": row[1],
                "notes": row[2],
                "summary": row[3],
                "action_items": json.loads(row[4]) if row[4] else [],
                "participants": row[5],
                "date": row[6],
                "created_at": row[7],
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# -------------------------------------------------------
# TASK MANAGEMENT
# -------------------------------------------------------

def create_task(title: str, description: str = "", priority: str = "medium", due_date: str = None) -> int:
    """Helper to create a task."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tasks (title, description, priority, due_date)
        VALUES (?, ?, ?, ?)
    """, (title, description, priority, due_date))
    task_id = cur.lastrowid
    conn.commit()
    conn.close()
    return task_id


@app.post("/tasks/create")
async def create_task_endpoint(request: Request):
    """Create a new task."""
    try:
        body = await request.json()
        title = body.get("title", "").strip()
        description = body.get("description", "").strip()
        priority = body.get("priority", "medium")
        due_date = body.get("due_date")
        
        if not title:
            return {"success": False, "error": "title is required"}
        
        task_id = create_task(title, description, priority, due_date)
        
        # Log
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "title": title,
            "action": "created",
        }
        with open(TASKS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        return {"success": True, "task_id": task_id}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/tasks/list")
async def list_tasks(status: str = None):
    """List all tasks, optionally filtered by status."""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        if status:
            cur = conn.execute("""
                SELECT id, title, description, priority, status, due_date, created_at, completed_at
                FROM tasks
                WHERE status = ?
                ORDER BY 
                    CASE priority
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                    END,
                    created_at DESC
            """, (status,))
        else:
            cur = conn.execute("""
                SELECT id, title, description, priority, status, due_date, created_at, completed_at
                FROM tasks
                ORDER BY 
                    CASE priority
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                    END,
                    created_at DESC
            """)
        
        tasks = []
        for row in cur.fetchall():
            tasks.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "priority": row[3],
                "status": row[4],
                "due_date": row[5],
                "created_at": row[6],
                "completed_at": row[7],
            })
        
        conn.close()
        return {"success": True, "tasks": tasks}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/tasks/{task_id}/complete")
async def complete_task(task_id: int):
    """Mark a task as completed."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            UPDATE tasks
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (task_id,))
        conn.commit()
        conn.close()
        
        return {"success": True, "task_id": task_id}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# -------------------------------------------------------
# EMAIL DRAFT GENERATION
# -------------------------------------------------------

@app.post("/emails/generate")
async def generate_email(request: Request):
    """
    Generate an email draft based on context.
    
    Body: {
        "recipient": "john@example.com",
        "context": "Follow up on yesterday's meeting about the project timeline",
        "tone": "professional" (optional)
    }
    """
    try:
        body = await request.json()
        recipient = body.get("recipient", "").strip()
        context = body.get("context", "").strip()
        tone = body.get("tone", "professional")
        
        if not context:
            return {"success": False, "error": "context is required"}
        
        openai_client = get_client()
        
        prompt = f"""Generate a professional email based on the following context:

Recipient: {recipient if recipient else "colleague"}
Context: {context}
Tone: {tone}

Generate:
1. A clear, concise subject line
2. A well-structured email body (2-3 paragraphs)

Format as JSON:
{{
  "subject": "...",
  "body": "..."
}}"""
        
        response = openai_client.chat.completions.create(
            model="gpt-5.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_completion_tokens=800,
        )
        
        email_text = response.choices[0].message.content.strip()
        
        # Parse JSON
        try:
            if "```json" in email_text:
                json_start = email_text.find("```json") + 7
                json_end = email_text.find("```", json_start)
                email_text = email_text[json_start:json_end].strip()
            elif "```" in email_text:
                json_start = email_text.find("```") + 3
                json_end = email_text.find("```", json_start)
                email_text = email_text[json_start:json_end].strip()
            
            email_data = json.loads(email_text)
        except:
            # Fallback: extract subject and body manually
            lines = email_text.split("\n")
            subject = ""
            body = ""
            in_body = False
            for line in lines:
                if "subject" in line.lower() and ":" in line:
                    subject = line.split(":", 1)[1].strip().strip('"')
                elif "body" in line.lower() and ":" in line:
                    in_body = True
                    body = line.split(":", 1)[1].strip().strip('"')
                elif in_body:
                    body += "\n" + line
            
            email_data = {"subject": subject or "Email", "body": body or email_text}
        
        # Store draft
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO email_drafts (subject, body, recipient, context)
            VALUES (?, ?, ?, ?)
        """, (
            email_data.get("subject", ""),
            email_data.get("body", ""),
            recipient,
            context
        ))
        draft_id = cur.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "draft_id": draft_id,
            "subject": email_data.get("subject", ""),
            "body": email_data.get("body", ""),
            "recipient": recipient,
        }
        
    except Exception as e:
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


@app.get("/emails/list")
async def list_email_drafts():
    """List all email drafts."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute("""
            SELECT id, subject, recipient, created_at
            FROM email_drafts
            ORDER BY created_at DESC
            LIMIT 50
        """)
        
        drafts = []
        for row in cur.fetchall():
            drafts.append({
                "id": row[0],
                "subject": row[1],
                "recipient": row[2],
                "created_at": row[3],
            })
        
        conn.close()
        return {"success": True, "drafts": drafts}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# -------------------------------------------------------
# DAILY SUMMARY
# -------------------------------------------------------

@app.get("/summary/daily")
async def get_daily_summary():
    """Generate a daily summary of meetings, tasks, and emails."""
    try:
        # Get today's data
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Meetings
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute("""
            SELECT COUNT(*) FROM meetings WHERE date = ?
        """, (today,))
        meetings_count = cur.fetchone()[0]
        
        # Tasks
        cur = conn.execute("""
            SELECT COUNT(*) FROM tasks WHERE status = 'pending'
        """)
        pending_tasks = cur.fetchone()[0]
        
        cur = conn.execute("""
            SELECT COUNT(*) FROM tasks WHERE DATE(completed_at) = DATE('now')
        """)
        completed_today = cur.fetchone()[0]
        
        # Recent meetings
        cur = conn.execute("""
            SELECT title, summary FROM meetings
            WHERE date = ?
            ORDER BY created_at DESC
            LIMIT 5
        """, (today,))
        recent_meetings = [{"title": r[0], "summary": r[1]} for r in cur.fetchall()]
        
        # High priority tasks
        cur = conn.execute("""
            SELECT title, description FROM tasks
            WHERE status = 'pending' AND priority = 'high'
            ORDER BY created_at DESC
            LIMIT 5
        """)
        high_priority = [{"title": r[0], "description": r[1]} for r in cur.fetchall()]
        
        conn.close()
        
        # Generate AI summary
        openai_client = get_client()
        
        summary_prompt = f"""Generate a brief daily productivity summary for today ({today}):

Meetings today: {meetings_count}
Pending tasks: {pending_tasks}
Completed today: {completed_today}

Recent meetings:
{json.dumps(recent_meetings, indent=2)}

High priority tasks:
{json.dumps(high_priority, indent=2)}

Provide a concise 3-4 sentence summary highlighting key activities and priorities."""
        
        response = openai_client.chat.completions.create(
            model="gpt-5.1",
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.7,
            max_completion_tokens=300,
        )
        
        ai_summary = response.choices[0].message.content.strip()
        
        return {
            "success": True,
            "date": today,
            "meetings_count": meetings_count,
            "pending_tasks": pending_tasks,
            "completed_today": completed_today,
            "recent_meetings": recent_meetings,
            "high_priority_tasks": high_priority,
            "ai_summary": ai_summary,
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# -------------------------------------------------------
# STATISTICS
# -------------------------------------------------------

@app.get("/stats")
async def get_stats():
    """Get overall statistics."""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Counts
        cur = conn.execute("SELECT COUNT(*) FROM meetings")
        meetings_count = cur.fetchone()[0]
        
        cur = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
        pending_tasks = cur.fetchone()[0]
        
        cur = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'completed'")
        completed_tasks = cur.fetchone()[0]
        
        cur = conn.execute("SELECT COUNT(*) FROM email_drafts")
        email_drafts = cur.fetchone()[0]
        
        conn.close()
        
        return {
            "success": True,
            "meetings": meetings_count,
            "pending_tasks": pending_tasks,
            "completed_tasks": completed_tasks,
            "email_drafts": email_drafts,
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


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
        "database": DB_PATH,
    }
