# Day 18 — Prompt & Style Systems

## Overview

Brand-consistent image generation system using style profiles and prompt templates. Generate the same subject across multiple brand styles for comparison and consistency.

## Features

- ✅ **Style Profiles**: 3 pre-defined brand styles (Minimal Modern, Vibrant Playful, Elegant Luxury)
- ✅ **Prompt Templates**: Base subject + style description + aspect ratio
- ✅ **Style Grid Generation**: Generate same subject in all styles simultaneously
- ✅ **Profile Details**: Color palette, mood, visual style, do's and don'ts
- ✅ **Consistency Tracking**: Log which profile and template used for each image
- ✅ **Statistics**: Track usage per style profile

## Style Profiles

### 1. Minimal Modern
- **Colors**: Neutral tones, whites, grays, soft beiges
- **Mood**: Clean, professional, sophisticated
- **Style**: Flat design, smooth texture, moderate detail
- **Use Case**: Corporate, professional, clean aesthetic

### 2. Vibrant Playful
- **Colors**: Bright saturated colors, vibrant blues, oranges, yellows
- **Mood**: Energetic, fun, youthful, optimistic
- **Style**: 3D rendered, vibrant gradients, high detail
- **Use Case**: Youth brands, entertainment, dynamic products

### 3. Elegant Luxury
- **Colors**: Rich deep tones, golds, purples, navy, emerald
- **Mood**: Sophisticated, luxurious, premium, refined
- **Style**: Photorealistic, luxurious materials, very high detail
- **Use Case**: Premium brands, luxury products, high-end services

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment:
```bash
cp ../day17/.env .env  # or create .env with OPENAI_API_KEY
```

3. Start server:
```bash
python3 -m uvicorn backend:app --host 127.0.0.1 --port 8000
```

4. Open http://127.0.0.1:8000

## Usage

1. **Load Profiles**: Click "Load Profiles" to see all style definitions

2. **Generate Grid**:
   - Enter a base subject (e.g., "A coffee cup")
   - Select aspect ratio
   - Click "Generate Grid" to create images in all 3 styles
   - Compare consistency within each style and distinctiveness between styles

3. **Generate Single**:
   - Enter subject and select a specific profile
   - Generate one image at a time

4. **View Statistics**: See usage stats per style profile

## Prompt Template System

The system builds prompts using:
```
[Base Subject]. Style: [Style Description]. Color palette: [Colors]. Mood: [Mood]. 
Visual type: [Type]. Texture: [Texture]. Detail level: [Level]. Lighting: [Lighting]. 
Composition: [Composition]. Must include: [Top 3 Do's]. Avoid: [Top 3 Don'ts].
```

## API Endpoints

- `GET /profiles` - Get all style profiles
- `GET /profiles/{id}` - Get specific profile
- `POST /generate` - Generate single image with style profile
- `POST /generate_grid` - Generate grid (all profiles for same subject)
- `GET /logs` - Get generation logs
- `GET /logs/stats` - Get statistics by profile
- `GET /health` - Health check

## Testing Checklist

- [ ] Load and view all style profiles
- [ ] Generate grid with same subject across all styles
- [ ] Compare consistency within each style (generate 2-3 images per style)
- [ ] Compare distinctiveness between styles (same subject, different styles)
- [ ] Verify prompt templates include all profile details
- [ ] Check logs show correct profile and template info
- [ ] View statistics per style profile
- [ ] Test single image generation

## Log Format

Each generation is logged with:
- Base subject
- Style profile (id, name)
- Aspect ratio
- Generated prompt
- Image URL
- Latency and cost
- Success/failure status

This enables reuse and iteration across campaigns.

