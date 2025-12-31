# Browser Use + n8n Self-Hosted Stack

**Created:** 2025-12-29  
**Status:** Implementation Guide

## Architecture Overview

This stack gives you AI-powered browser automation orchestrated through visual workflows, entirely self-hosted and free (minus compute costs).

```
┌─────────────────────────────────────────────────────────┐
│                      n8n (Docker)                       │
│         Visual workflow orchestration layer             │
│    Triggers, scheduling, integrations, webhooks         │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP/Webhook
                      ▼
┌─────────────────────────────────────────────────────────┐
│              Browser Use (Python/FastAPI)               │
│         AI agent controls headless browser              │
│    Adapts to dynamic sites, handles complex tasks       │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   LLM Provider                          │
│   Ollama (free/local) OR Claude/GPT API (paid)          │
└─────────────────────────────────────────────────────────┘
```

## Phase 1: n8n Setup (Day 1)

### Prerequisites
- Docker and Docker Compose installed
- Domain/subdomain pointed to your server (for SSL)
- 2GB+ RAM minimum

### Docker Compose Configuration

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=your-secure-password
      - N8N_HOST=n8n.yourdomain.com
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://n8n.yourdomain.com/
      - GENERIC_TIMEZONE=America/Los_Angeles
    volumes:
      - n8n_data:/home/node/.n8n

  postgres:
    image: postgres:15
    restart: always
    environment:
      - POSTGRES_USER=n8n
      - POSTGRES_PASSWORD=n8n-db-password
      - POSTGRES_DB=n8n
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  n8n_data:
  postgres_data:
```

### Launch Commands

```bash
# Start the stack
docker-compose up -d

# Check logs
docker-compose logs -f n8n

# Access at http://localhost:5678
```

## Phase 2: Browser Use Setup (Day 2-3)

### Option A: Browser Use Cloud (Fastest Start)
Get API key from browser-use.com (new signups get $10 free credits).

In n8n, use HTTP Request node to POST to their API.

### Option B: Self-Hosted Browser Use (Fully Free)

Create a Python service that n8n calls via HTTP.

**Directory structure:**
```
browser-use-service/
├── Dockerfile
├── requirements.txt
├── main.py
└── .env
```

**requirements.txt:**
```
browser-use
fastapi
uvicorn
playwright
```

**main.py:**
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from browser_use import Agent
from langchain_openai import ChatOpenAI
# Or for local: from langchain_community.llms import Ollama

app = FastAPI()

class TaskRequest(BaseModel):
    task: str
    url: str = None

class TaskResponse(BaseModel):
    result: str
    success: bool

@app.post("/run-task", response_model=TaskResponse)
async def run_browser_task(request: TaskRequest):
    try:
        # For Claude/GPT:
        llm = ChatOpenAI(model="gpt-4o")
        
        # For local Ollama (free):
        # llm = Ollama(model="llama3.2")
        
        agent = Agent(
            task=request.task,
            llm=llm,
        )
        
        result = await agent.run()
        
        return TaskResponse(
            result=str(result),
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install playwright dependencies
RUN apt-get update && apt-get install -y \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Add to docker-compose.yml:
```yaml
  browser-use:
    build: ./browser-use-service
    restart: always
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      # Or for Anthropic:
      # - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

## Phase 3: Integration Workflow (Day 4)

### Basic n8n Workflow Pattern

1. **Trigger Node** (Webhook, Schedule, or Manual)
2. **HTTP Request Node** to Browser Use service:
   - Method: POST
   - URL: http://browser-use:8000/run-task
   - Body: `{"task": "Go to [URL] and extract [data]", "url": "..."}`
3. **Process Results** (Code node, Set node)
4. **Output** (Google Sheets, Slack, Email, Database)

### Example: Competitor Price Monitoring

```json
{
  "task": "Navigate to competitor.com/pricing, find all pricing tiers, and return them as JSON with tier_name, price, and features array",
  "url": "https://competitor.com/pricing"
}
```

## Phase 4: Local LLM Option (Fully Free)

For zero API costs, run Ollama alongside:

Add to docker-compose.yml:
```yaml
  ollama:
    image: ollama/ollama:latest
    restart: always
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
```

Then pull a model:
```bash
docker exec -it ollama ollama pull llama3.2
```

Update Browser Use to use Ollama endpoint.

## FitTwin Use Cases

### Immediate Applications
- Monitor competitor virtual try-on features and pricing
- Scrape fashion retailer product catalogs for demo data
- Track industry news and funding announcements
- Automate investor research and outreach tracking

### Future Productization
- Offer automated catalog ingestion to B2B clients
- Build internal QA agent that tests try-on flows across browsers

## Cost Analysis

| Component | Self-Hosted Cost | Cloud Alternative |
|-----------|------------------|-------------------|
| n8n | $0 (Docker) | $24/mo (cloud) |
| Browser Use | $0 (self-hosted) | ~$20/mo |
| LLM (Ollama) | $0 | GPT-4o ~$0.01/task |
| VPS (2GB) | ~$12/mo | N/A |
| **Total** | **~$12/mo** | **~$50+/mo** |

## Resources

- [n8n Docker Docs](https://docs.n8n.io/hosting/installation/docker/)
- [Browser Use GitHub](https://github.com/browser-use/browser-use)
- [Browser Use + n8n Integration](https://docs.browser-use.com/cloud/v1/n8n-browser-use-integration)
- [n8n AI Agent Tutorial](https://docs.n8n.io/advanced-ai/intro-tutorial/)
- [n8n Self-Hosted AI Starter Kit](https://github.com/n8n-io/self-hosted-ai-starter-kit)

---
*Guide created: 2025-12-29*
