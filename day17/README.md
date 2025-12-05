# Day 17 — Image Generation Fundamentals

## Overview

Image generation pipeline with DALL·E 3 and DALL·E 2, featuring comprehensive parameter logging and cost estimation.

## Features

- ✅ **Multiple Models**: DALL·E 3 and DALL·E 2 support
- ✅ **Parameter Control**: prompt, size, quality (DALL·E 3), steps (logged), seed (logged)
- ✅ **Comprehensive Logging**: Every request logs:
  - Model name
  - Input parameters (prompt, size, quality, steps, seed)
  - Response latency (ms)
  - Cost estimate (USD)
  - Success/failure status
- ✅ **Statistics Dashboard**: View total requests, success rate, total cost, average latency
- ✅ **Log Viewer**: Browse recent generation requests with all details

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment:
```bash
cp ../day16/.env .env  # or create .env with OPENAI_API_KEY
```

3. Start server:
```bash
python3 -m uvicorn backend:app --host 127.0.0.1 --port 8000
```

4. Open http://127.0.0.1:8000

## Usage

1. **Generate Image**:
   - Enter a prompt
   - Select model (DALL·E 3 or DALL·E 2)
   - Choose size (options vary by model)
   - Set quality (DALL·E 3 only: standard or HD)
   - Optionally set steps and seed (logged but not used by DALL·E)
   - Click "Generate Image"

2. **View Statistics**:
   - Click "Refresh Stats" to see:
     - Total requests
     - Successful vs failed
     - Total cost estimate
     - Average latency

3. **View Logs**:
   - Click "Refresh Logs" to see last 20 requests
   - Each log shows all parameters, latency, cost, and result

## Parameters

### DALL·E 3
- **Sizes**: `1024x1024`, `1024x1792`, `1792x1024`
- **Quality**: `standard` ($0.040/image) or `hd` ($0.080/image for larger sizes)

### DALL·E 2
- **Sizes**: `256x256`, `512x512`, `1024x1024`
- **Quality**: Not applicable (always standard)
- **Cost**: $0.016-$0.020 per image depending on size

### Logged Parameters
- **Steps**: Logged but not used (DALL·E doesn't support steps)
- **Seed**: Logged but not used (DALL·E doesn't support seeds)

## Log Format

Logs are stored in `image_generation_log.jsonl` (JSON Lines format):

```json
{
  "timestamp": "2024-12-04T10:30:00",
  "model": "dall-e-3",
  "prompt": "A futuristic city",
  "parameters": {
    "size": "1024x1024",
    "quality": "standard",
    "steps": null,
    "seed": null
  },
  "latency_ms": 3456.78,
  "cost_estimate_usd": 0.040,
  "success": true,
  "image_url": "https://..."
}
```

## API Endpoints

- `POST /generate` - Generate an image with logging
- `GET /logs` - Get recent logs (limit query param)
- `GET /logs/stats` - Get statistics
- `GET /health` - Health check

## Testing Checklist

- [ ] Generate image with DALL·E 3
- [ ] Generate image with DALL·E 2
- [ ] Test different sizes
- [ ] Test HD quality (DALL·E 3)
- [ ] Verify all parameters are logged
- [ ] Check latency is recorded
- [ ] Verify cost estimates are accurate
- [ ] Test error handling (invalid prompt, etc.)
- [ ] View statistics dashboard
- [ ] Review log entries

