# Day 20 — Daily Productivity Assistant

## Overview

A real-world AI-powered productivity application that solves concrete daily work problems:
- **Meeting Notes Processing**: Automatically summarize meetings, extract action items, identify participants
- **Task Management**: Create, track, and complete tasks with priorities
- **Email Draft Generation**: Generate professional email drafts from context
- **Daily Summaries**: AI-generated daily productivity summaries

## Features

### 1. Meeting Notes Processing
- Paste raw meeting notes
- Get AI-generated summary (3-5 bullet points)
- Automatically extract action items with assignees
- Identify participants
- Auto-create tasks from action items
- Store all meetings in database

### 2. Task Management
- Create tasks with title, description, priority, due date
- View tasks filtered by status (pending/completed)
- Mark tasks as complete
- Tasks automatically created from meeting action items
- Priority-based sorting (high → medium → low)

### 3. Email Draft Generation
- Generate professional email drafts from simple context
- Customizable tone (professional, friendly, formal, casual)
- Subject line and body generation
- Store drafts for later reference
- Context-aware email creation

### 4. Daily Summary
- AI-generated summary of today's activities
- Meeting count, task statistics
- Recent meetings overview
- High-priority tasks highlight
- Concise 3-4 sentence summary

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment:
```bash
cp ../day19/.env .env  # or create .env with OPENAI_API_KEY
```

3. Start server:
```bash
python3 -m uvicorn backend:app --host 127.0.0.1 --port 8000
```

4. Open http://127.0.0.1:8000

## Usage Examples

### Process Meeting Notes
1. Go to "Meetings" tab
2. Enter meeting title and date
3. Paste meeting notes
4. Click "Process Meeting Notes"
5. Get:
   - Summary
   - Action items (auto-created as tasks)
   - Participant list

### Manage Tasks
1. Go to "Tasks" tab
2. Create new tasks with priority
3. View all/pending/completed tasks
4. Mark tasks as complete
5. Tasks from meetings appear automatically

### Generate Email Drafts
1. Go to "Emails" tab
2. Enter recipient (optional)
3. Describe what the email should be about
4. Select tone
5. Get ready-to-send email draft

### Daily Summary
1. Go to "Daily Summary" tab
2. Click "Generate Today's Summary"
3. Get AI-powered overview of your day

## Real-World Use Cases

1. **After a Meeting**:
   - Paste notes → Get summary → Action items become tasks → Generate follow-up emails

2. **Daily Planning**:
   - Check daily summary → See high-priority tasks → Plan your day

3. **Email Writing**:
   - "Follow up on yesterday's meeting" → Get professional draft → Send

4. **Task Tracking**:
   - All action items from meetings → Automatic task creation → Track completion

## API Endpoints

- `POST /meetings/process` - Process meeting notes
- `GET /meetings/list` - List all meetings
- `GET /meetings/{id}` - Get specific meeting
- `POST /tasks/create` - Create task
- `GET /tasks/list` - List tasks (optional ?status=pending)
- `POST /tasks/{id}/complete` - Complete task
- `POST /emails/generate` - Generate email draft
- `GET /emails/list` - List email drafts
- `GET /summary/daily` - Get daily summary
- `GET /stats` - Get statistics
- `GET /health` - Health check

## Database Schema

- **meetings**: title, notes, summary, action_items (JSON), participants, date
- **tasks**: title, description, priority, status, due_date, completed_at
- **email_drafts**: subject, body, recipient, context

## Technology Stack

- **Backend**: FastAPI, SQLite
- **AI**: OpenAI GPT-5.1 for summarization, extraction, generation
- **Frontend**: HTML/CSS/JavaScript
- **Storage**: SQLite database + JSONL logs

## Result

A working, production-ready productivity assistant that solves real daily work problems using AI. Perfect for:
- Remote workers managing multiple meetings
- Project managers tracking tasks
- Anyone who writes many emails
- Teams needing meeting summaries

This is a **real application** you can use every day!
