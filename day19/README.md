# Day 19 — Vision QA Agent

## Overview

Automated quality assurance system for generated images using vision-capable models. Implements a generate → analyze → score pipeline with automatic filtering of images that don't meet quality thresholds.

## Features

- ✅ **Vision Analysis**: Uses GPT-4 Vision to analyze generated images
- ✅ **QA Checklist**: Automated evaluation against style profile:
  - Color palette compliance
  - Style template match
  - Mood alignment
  - Visual style elements
  - Required elements (do's)
  - Forbidden elements (don'ts)
- ✅ **Generate → Analyze → Score Pipeline**: Automatic workflow
- ✅ **Quality Threshold**: Discard images below score threshold
- ✅ **Auto-Retry**: Automatically retry generation if QA fails
- ✅ **Comprehensive Logging**: Track all QA results with scores and feedback

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment:
```bash
cp ../day18/.env .env  # or create .env with OPENAI_API_KEY
```

3. Start server:
```bash
python3 -m uvicorn backend:app --host 127.0.0.1 --port 8000
```

4. Open http://127.0.0.1:8000

## Usage

1. **Generate with QA**:
   - Enter base subject
   - Select style profile
   - Set quality threshold (default: 70/100)
   - Set max retries (default: 3)
   - Click "Generate with QA"
   - System will: Generate → Analyze → Score → Retry if needed

2. **Analyze Existing Image**:
   - Paste image URL
   - Enter subject and select profile
   - Click "Analyze Image"
   - Get QA score and detailed feedback

3. **View Statistics**:
   - See total analyzed, pass/fail rates, average scores
   - View stats by style profile

## QA Checklist

Each image is evaluated against:
1. **Color Palette Compliance**: Matches expected colors?
2. **Style Template Match**: Follows chosen style?
3. **Mood Alignment**: Matches expected mood?
4. **Visual Style Elements**: Texture, lighting, composition correct?
5. **Required Elements**: Includes do's from profile?
6. **Forbidden Elements**: Avoids don'ts from profile?

## Scoring

- **Score Range**: 0-100
- **Pass Threshold**: Default 70 (configurable)
- **Auto-Retry**: If score < threshold, automatically retry generation
- **Max Retries**: Configurable (default: 3)

## API Endpoints

- `POST /generate_with_qa` - Generate image with automatic QA
- `POST /analyze_image` - Analyze existing image URL
- `GET /profiles` - Get style profiles
- `GET /logs` - Get QA logs
- `GET /logs/stats` - Get QA statistics
- `GET /health` - Health check

## Testing Checklist

- [ ] Generate image with QA pipeline
- [ ] Verify vision analysis works
- [ ] Check QA score and feedback
- [ ] Test quality threshold filtering
- [ ] Verify auto-retry on failed QA
- [ ] Analyze existing image URL
- [ ] Check checklist results
- [ ] View statistics dashboard
- [ ] Test with different style profiles

## Log Format

Each QA result is logged with:
- Image URL
- Base subject
- Style profile
- QA analysis (score, passed, feedback, checklist results)
- Latency (generation + QA analysis)

This enables tracking quality over time and identifying style compliance issues.

