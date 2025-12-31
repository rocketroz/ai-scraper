# AI Scraper Stack

Browser Use + n8n self-hosted automation stack for FitTwin.

## Quick Start

```bash
# 1. Make setup script executable
chmod +x setup.sh

# 2. Run setup (creates .env, builds containers)
./setup.sh

# 3. Access services
open http://localhost:5678  # n8n
open http://localhost:8000/docs  # Browser Use API
```

## Architecture

```
n8n (localhost:5678)
  └── HTTP Request → Browser Use API (localhost:8000)
                       └── LLM (OpenAI/Claude/Ollama)
                       └── Headless Chromium
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/run-task` | POST | Async task (returns task_id) |
| `/run-task-sync` | POST | Sync task (waits for result) |
| `/task/{id}` | GET | Get task status/result |
| `/tasks` | GET | List all tasks |
| `/scrape-pricing` | POST | Extract pricing from URL |
| `/scrape-products` | POST | Extract product catalog |

## n8n Workflow Pattern

1. Add HTTP Request node
2. Configure:
   - Method: POST
   - URL: http://browser-use:8000/run-task-sync
   - Body (JSON):
   ```json
   {
     "task": "Go to example.com and extract all product names",
     "url": "https://example.com",
     "timeout": 120
   }
   ```
3. Connect to output node (Google Sheets, Slack, etc.)

## LLM Options

Edit `.env` to switch providers:

```bash
# OpenAI (default)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-...

# Anthropic
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-20250514
ANTHROPIC_API_KEY=sk-ant-...

# Ollama (free, local)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
```

For Ollama, pull the model after startup:
```bash
docker compose exec ollama ollama pull llama3.2
```

## Commands

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Rebuild after code changes
docker compose build browser-use
docker compose up -d browser-use

# Shell into container
docker compose exec browser-use bash
```

## FitTwin Use Cases

- **Competitor monitoring**: `/scrape-pricing` on competitor sites
- **Catalog ingestion**: `/scrape-products` for demo data
- **Market research**: Custom tasks for industry news
- **QA automation**: Test virtual try-on across browsers

---
Created: 2025-12-29
