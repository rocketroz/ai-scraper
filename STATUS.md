# Browser Use + n8n Stack

**Last Updated:** 2025-12-29
**Health:** DEPLOYED AND RUNNING

## Current State

Self-hosted AI browser automation stack is live and operational.

## Services Running

| Service | Port | Status |
|---------|------|--------|
| n8n | localhost:5678 | Running |
| Browser Use API | localhost:8000 | Healthy |
| Ollama | localhost:11434 | Running (llama3.2 loaded) |
| PostgreSQL | internal | Healthy |
| Redis | localhost:6379 | Running |

## Architecture

```
n8n (orchestrator) → Browser Use API (agent) → Ollama (llama3.2) → Headless Chromium
```

## Access Points

**n8n Workflow Editor:** http://localhost:5678
- Username: admin
- Password: LifeOS2025!

**Browser Use API:** http://localhost:8000
- Health: http://localhost:8000/health
- Docs: http://localhost:8000/docs

## What's Built
- docker-compose.yml (full 5-service stack)
- FastAPI Browser Use service with async task handling
- Convenience endpoints: /scrape-pricing, /scrape-products
- Local LLM via Ollama (free, private operation)

## Quick Commands

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f browser-use

# Restart services
docker-compose restart

# Stop everything
docker-compose down
```

## Use Cases
- Competitor pricing monitoring
- Product catalog scraping for demo data
- Market research automation
- Any browser-based data extraction

## Documentation
- `browser-use-n8n-stack.md` - Detailed architecture guide
- `README.md` - Quick reference
- `validations/` - Deployment validation reports

---

*Updated: 2025-12-29*
