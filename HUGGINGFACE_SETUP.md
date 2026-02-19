# T-Shirt Factory - Hugging Face Image Generation Setup

## Overview

The factory simulator now uses **Hugging Face API** with the **FLUX.1-dev** model to generate AI-powered product images. This replaces Pollinations.ai to avoid service interruptions.

## Prerequisites

1. **Hugging Face Account** - Sign up at https://huggingface.co
2. **API Token** - Generate at https://huggingface.co/settings/tokens
3. **Model Access** - Request access to `black-forest-labs/FLUX.1-dev` model

## Quick Start

### Step 1: Get Your HF Token

1. Go to https://huggingface.co/settings/tokens
2. Create a new token with `read` permissions
3. Copy the token

### Step 2: Configure Environment

Create a `.env` file in the `factory_ui_simulator` directory:

```bash
cd factory_ui_simulator
cp .env.example .env
```

Edit `.env` and add your token:

```bash
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
```

### Step 3: Build and Run Docker

```bash
cd generated-factories/tshirt-factory-001
docker-compose up --build
```

The container will automatically load environment variables from `.env`.

### Step 4: Test Image Generation

```bash
# Generate an image
curl "http://localhost:5001/proxy-image?prompt=a%20red%20polo%20t-shirt"

# Check cache and configuration
curl http://localhost:5001/cache-info
```

## How It Works

**Request Flow:**
```
/proxy-image endpoint
    ↓
[Check local cache]  → Return (fast ~1ms)
    ↓
[Generate with HF]    → Get PIL.Image from FLUX.1-dev
    ↓
[Convert to PNG]      → Serialize to bytes
    ↓
[Cache locally]       → Store in /tmp/image_cache
    ↓
[Return to client]    → with X-Cache: MISS header
```

**Cache behavior:**
- First request: 5-10 seconds (HF API generation)
- Subsequent requests: <1ms (served from cache)
- Cache persists across container restarts (in `/tmp/image_cache`)

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `HF_TOKEN` | (required) | Hugging Face API token |
| `HF_MODEL` | `black-forest-labs/FLUX.1-dev` | Model to use |
| `HF_PROVIDER` | `together` | Provider: `together`, `replicate`, etc. |

## Error Handling

If image generation fails:
1. Check if `HF_TOKEN` is set: `curl http://localhost:5001/cache-info`
2. Check Docker logs: `docker-compose logs factory-simulator`
3. If token is invalid/expired, generate a new one
4. Fallback placeholder images are generated automatically

## Troubleshooting

### "HF_TOKEN not configured"
- Create `.env` file in `factory_ui_simulator/`
- Add your token: `HF_TOKEN=hf_xxx`
- Rebuild container: `docker-compose up --build`

### "Model access not granted"
- Go to https://huggingface.co/black-forest-labs/FLUX.1-dev
- Click "Request Access"
- Wait for approval (usually instant)

### "Connection timeout"
- Check internet connection
- Verify HF API is reachable: `curl https://api-inference.huggingface.co/status`
- Check Docker container can reach external networks

### Large generated images (5-10MB)
- First generation takes 5-10 seconds
- Cached images are much smaller (500KB-1MB)
- Consider using smaller prompts for faster generation

## Performance Notes

| Metric | Value |
|--------|-------|
| Cold generation | 5-10 sec |
| Cached retrieval | <1ms |
| Image file size | 500KB-1MB |
| Cache storage | ~100MB per 100 images |
| Model | FLUX.1-dev (11B parameters) |

## Disabled Features

These features from Pollinations.ai integration are no longer needed:
- Rate limiting (Hugging Face has its own limits)
- Host proxy service (direct API access)
- Cloudflare bypass workarounds

## API Endpoints

### GET `/proxy-image`
Generate or retrieve a cached image.

**Parameters:**
- `prompt` (required): Image generation prompt
- `width` (optional): Image width in pixels (default: 512)
- `height` (optional): Image height in pixels (default: 512)

**Response Headers:**
- `X-Cache`: `HIT` (cached) or `MISS` (newly generated) or `FALLBACK` (placeholder)
- `X-Generator`: `huggingface` (if successful)

**Example:**
```bash
curl -i "http://localhost:5001/proxy-image?prompt=professional%20product%20photo%20of%20t-shirt"
```

### GET `/cache-info`
Get cache statistics and Hugging Face configuration.

**Response:**
```json
{
  "cache_enabled": true,
  "cached_images": 5,
  "total_size_mb": 2.5,
  "image_generator": {
    "type": "huggingface",
    "model": "black-forest-labs/FLUX.1-dev",
    "provider": "together",
    "token_configured": true
  }
}
```

### POST `/cache-clear`
Clear all cached images.

```bash
curl -X POST http://localhost:5001/cache-clear
```

## Production Deployment

For production:

1. **Store token securely** - Use Docker secrets, environment variables, or vault
2. **Use `docker-compose.override.yml`** - Don't commit real tokens to git
3. **Monitor API usage** - The Hugging Face API has rate limits
4. **Cache strategy** - Cache images locally to reduce API calls
5. **Fallback images** - Placeholder generation ensures UI never breaks

Example `.gitignore` entry:
```
factory_ui_simulator/.env
factory_ui_simulator/.env.local
.env.*.local
```

## Support

- Hugging Face API docs: https://huggingface.co/docs/api-inference
- FLUX.1 model: https://huggingface.co/black-forest-labs/FLUX.1-dev
- Issues: Check Docker container logs with `docker-compose logs factory-simulator`
