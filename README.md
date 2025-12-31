# AI Content Curation & Research Stack

Automated content curation and opportunity research workflows for Laura's Life OS.

**GitHub:** https://github.com/rocketroz/ai-scraper

---

## Overview

This project contains two types of workflows:

1. **n8n Automation Workflows** - Scheduled scrapers that pull content from Reddit/HackerNews and push to Notion
2. **Claude Code Research Agents** - On-demand opportunity research using AI agents
3. **Browser Use API** - Headless browser automation for complex scraping tasks

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Colima (for macOS) or Docker Desktop
- Claude Code CLI (for research agents)

### Start the Stack
```bash
cd ~/Projects/ai-scraper
colima start  # if using Colima on macOS
docker-compose up -d
```

### Access Services
| Service | URL | Credentials |
|---------|-----|-------------|
| n8n | http://localhost:5678 | admin / (see .env) |
| Browser Use API | http://localhost:8000/docs | - |
| Ollama | http://localhost:11434 | - |

---

## n8n Workflows

### 1. Reddit AI Video Daily Digest
| | |
|---|---|
| **Schedule** | Daily at 7am |
| **Sources** | r/StableDiffusion, r/aivideo, r/midjourney |
| **Filters** | Score >= 30, contains technique keywords (prompt, workflow, tutorial, etc.) |
| **Output** | [Notion Database](https://notion.so/41770775e00c4ccdbfb134d1d305e392) |

**Manual Trigger:**
```bash
curl -X POST http://localhost:5678/webhook/reddit-digest
```

### 2. Opportunity Radar Weekly
| | |
|---|---|
| **Schedule** | Mondays at 8am |
| **Sources** | HackerNews (Show HN, startups), Reddit (r/SideProject, r/EntrepreneurRideAlong) |
| **Filters** | Score >= 5, contains domain keywords (video, creator, content, productivity, adhd, parent, ai, saas) |
| **Output** | [Notion Database](https://notion.so/bc3e684029ec4e5d99d41f2d4c52b07c) |

**Manual Trigger:**
```bash
curl -X POST http://localhost:5678/webhook/opportunity-radar
```

### 3. Festival Intelligence Weekly
| | |
|---|---|
| **Schedule** | Wednesdays at 9am |
| **Sources** | r/aivideo, r/runwayml, r/SoraAI, HackerNews (AI film queries) |
| **Filters** | Score >= 10, categorized by Films/Projects, Tools/Platforms, Techniques |
| **Output** | [Notion Database](https://notion.so/6395b6ad7a9a404d8d720d4353effae6) |

**Manual Trigger:**
```bash
curl -X POST http://localhost:5678/webhook/festival-intel
```

### Importing Workflows to n8n

If starting fresh, import the workflow JSON files:

```bash
# Using n8n API
N8N_API_KEY="your-api-key"

for f in n8n-workflows/*.json; do
  curl -X POST "http://localhost:5678/api/v1/workflows" \
    -H "X-N8N-API-KEY: $N8N_API_KEY" \
    -H "Content-Type: application/json" \
    -d @"$f"
done
```

Or import manually via n8n UI: Settings > Import from File

### Activating Workflows

After import, activate each workflow:
```bash
# Get workflow IDs
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "http://localhost:5678/api/v1/workflows" | jq '.data[] | {id, name}'

# Activate a workflow
curl -X PATCH "http://localhost:5678/api/v1/workflows/{workflow_id}" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"active": true}'
```

---

## Browser Use API

Headless browser automation for complex scraping tasks that require JavaScript rendering.

### Architecture
```
n8n (localhost:5678)
  └── HTTP Request → Browser Use API (localhost:8000)
                       └── LLM (OpenAI/Claude/Ollama)
                       └── Headless Chromium
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/run-task` | POST | Async task (returns task_id) |
| `/run-task-sync` | POST | Sync task (waits for result) |
| `/task/{id}` | GET | Get task status/result |
| `/tasks` | GET | List all tasks |
| `/scrape-pricing` | POST | Extract pricing from URL |
| `/scrape-products` | POST | Extract product catalog |

### n8n Integration Pattern

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
3. Connect to output node (Notion, Google Sheets, Slack, etc.)

---

## Claude Code Research Agents

Run comprehensive market/opportunity research using AI agents that search the web for funding data, competitors, and market analysis.

### Quick Command
```
Run 4 research agents in parallel to research opportunities in:
1. Entertainment Tech
2. Video Production
3. Life Optimization
4. Emerging Industries

Save results to a markdown file in output/
```

### Prompt Template

```
Research [DOMAIN] opportunities for a founder with the following background:
- [KEY ROLE 1] (e.g., CEO of [Company] in [industry])
- [KEY ROLE 2] (e.g., Director of [Organization])
- [EDUCATION/EXPERTISE] (e.g., studying [field] at [institution])
- [PERSONAL CONTEXT] (e.g., single parent, has ADHD, etc.)

For each opportunity identified, provide:

1. **The Problem Being Solved** - What specific pain point exists? Include data on market size and current state.

2. **Target Market** - Who would pay for this? How big is the addressable market?

3. **Current Solutions** - Who are the existing players? What have they raised? What are their valuations? Include specific company names, funding amounts, and sources.

4. **What 10x Better Looks Like** - Describe a solution that would be dramatically better than current options.

5. **Founder Edge Analysis** - Specifically explain why THIS founder's unique combination of experiences creates an advantage others don't have.

Requirements:
- Cite specific funding rounds, valuations, and market data with sources
- Include at least 5 concrete opportunities
- Focus on opportunities where the founder's specific background creates genuine competitive advantage
- Prioritize emerging markets with recent funding activity (2024-2025)
```

### Domain-Specific Prompts

<details>
<summary><b>Entertainment Tech</b></summary>

```
Research Entertainment Technology opportunities for a founder who is:
- CEO of FitTwin (virtual try-on startup launching Q1 2026)
- Festival Director for The Innovators Film Festival
- Graduate student in Entertainment Leadership at LMU under Professor Janet Yang
- Screenwriter/director working on AI-native films ("Synthetic Grandma", "Bali Demons")
- Single mother with ADHD

Focus on AI content tools, streaming/distribution, creator economy, rights management, and entertainment infrastructure.
```
</details>

<details>
<summary><b>Video Production</b></summary>

```
Research Video Production Technology opportunities for a founder who is:
- CEO of FitTwin (virtual try-on startup launching Q1 2026)
- Festival Director for The Innovators Film Festival
- Graduate student in Entertainment Leadership at LMU under Professor Janet Yang
- Screenwriter/director working on AI-native films ("Synthetic Grandma", "Bali Demons")
- Single mother with ADHD

Focus on AI video generation, virtual production, post-production automation, mobile video tools, and creator workflow infrastructure.
```
</details>

<details>
<summary><b>Life Optimization</b></summary>

```
Research Life Optimization Product opportunities for a founder who is:
- CEO of FitTwin (virtual try-on startup launching Q1 2026)
- Festival Director for The Innovators Film Festival
- Graduate student in Entertainment Leadership at LMU under Professor Janet Yang
- Screenwriter/director working on AI-native films
- Single mother with ADHD who benefits from structured systems

Focus on ADHD productivity tools, family/parent coordination, executive function support, wellness tech for working parents, and cognitive load management.
```
</details>

<details>
<summary><b>Emerging Industries</b></summary>

```
Research Emerging Industry opportunities for a founder who is:
- CEO of FitTwin (virtual try-on/fashion tech startup launching Q1 2026)
- Festival Director for The Innovators Film Festival
- Graduate student in Entertainment Leadership at LMU under Professor Janet Yang
- Screenwriter/director working on AI-native films
- Single mother with ADHD

Explore climate tech with consumer/creator angles, longevity/health tech, education technology (creative focus), and spatial computing/AR/VR applications. Look for intersections with fashion, entertainment, and creator economy.
```
</details>

---

## Configuration

### Environment Variables (.env)

```bash
# n8n
N8N_USER=admin
N8N_PASSWORD=your-password
N8N_HOST=localhost
N8N_PROTOCOL=http
WEBHOOK_URL=http://localhost:5678/
TIMEZONE=America/Los_Angeles

# Database
POSTGRES_PASSWORD=your-postgres-password

# LLM Provider (for browser-use service)
LLM_PROVIDER=ollama          # or: openai, anthropic
LLM_MODEL=llama3.2:1b        # or: gpt-4o, claude-sonnet-4-20250514

# API Keys (if using cloud LLMs)
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...

# n8n API Key (generate in n8n UI: Settings > API)
N8N_API_KEY=your-api-key

# Notion
NOTION_API_KEY=your-notion-api-key
NOTION_REDDIT_DB=41770775e00c4ccdbfb134d1d305e392
NOTION_FESTIVAL_DB=6395b6ad7a9a404d8d720d4353effae6
NOTION_OPPORTUNITY_DB=bc3e684029ec4e5d99d41f2d4c52b07c
```

### LLM Options

```bash
# OpenAI
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

### Notion Database Setup

Each workflow writes to a Notion database. Required properties:

<details>
<summary><b>Reddit AI Video Database</b></summary>

| Property | Type |
|----------|------|
| Title | title |
| URL | url |
| Score | number |
| Comments | number |
| Subreddit | select |
| Flair | rich_text |
| Date | date |
| Date Scraped | date |
</details>

<details>
<summary><b>Opportunity Radar Database</b></summary>

| Property | Type |
|----------|------|
| Title | title |
| URL | url |
| Score | number |
| Comments | number |
| Source | select (HackerNews, Reddit SideProject, Reddit Entrepreneur) |
| Description | rich_text |
| Date | date |
| Date Scraped | date |
</details>

<details>
<summary><b>Festival Intelligence Database</b></summary>

| Property | Type |
|----------|------|
| Title | title |
| URL | url |
| Score | number |
| Comments | number |
| Source | select (r/aivideo, r/runwayml, r/SoraAI, HackerNews) |
| Category | select (Films/Projects, Tools/Platforms, Techniques) |
| Has Video | checkbox |
| Date | date |
| Date Scraped | date |
</details>

### n8n Notion Credential

Create Notion credential in n8n:
1. Go to Credentials > New
2. Select "Notion API"
3. Enter your Notion API key
4. The credential ID is referenced in workflow JSON files

---

## Docker Services

| Service | Port | Purpose |
|---------|------|---------|
| n8n | 5678 | Workflow automation |
| postgres | 5432 | n8n database |
| ollama | 11434 | Local LLM (optional) |
| browser-use | 8000 | Browser automation |
| redis | 6379 | Caching (optional) |

### Common Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f n8n

# Restart n8n (after .env changes)
docker-compose up -d n8n

# Stop all services
docker-compose down

# Check service status
docker-compose ps

# Rebuild browser-use after code changes
docker-compose build browser-use
docker-compose up -d browser-use

# Shell into container
docker-compose exec browser-use bash
```

---

## File Structure

```
ai-scraper/
├── docker-compose.yml          # Docker stack definition
├── .env                        # Environment variables (not in git)
├── .gitignore
├── README.md                   # This file
├── n8n-workflows/
│   ├── reddit-ai-video.json    # Daily digest workflow
│   ├── opportunity-radar.json  # Weekly opportunity scan
│   └── festival-intelligence.json  # Weekly AI film intel
├── output/
│   └── opportunity-research-*.md   # Research agent outputs
└── browser-use-service/        # Browser automation service
    ├── Dockerfile
    ├── main.py
    └── requirements.txt
```

---

## Troubleshooting

### n8n container can't write files
n8n 2.x has issues with the File node. Use Execute Command with shell redirection instead, or write directly to Notion.

### Notion credential not found
Credentials are stored in n8n's database, not in workflow JSON. After importing, recreate the Notion credential and update workflow nodes.

### Webhook not responding
Ensure workflow is activated:
```bash
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "http://localhost:5678/api/v1/workflows" | jq '.data[] | {name, active}'
```

### Environment variables not loading
Recreate the container after .env changes:
```bash
docker-compose up -d n8n
```

### Ollama model not found
Pull the model after starting the stack:
```bash
docker-compose exec ollama ollama pull llama3.2:1b
```

---

## Use Cases

- **Daily AI Techniques**: Curate top Reddit posts on AI video/image generation
- **Startup Opportunities**: Track HackerNews Show HN and side project discussions
- **Festival Intel**: Monitor AI filmmaking community trends
- **Competitor Research**: Use Browser Use API to scrape competitor sites
- **Market Research**: Run Claude Code agents for deep opportunity analysis

---

## Links

- [n8n Documentation](https://docs.n8n.io/)
- [Notion API](https://developers.notion.com/)
- [Browser Use](https://github.com/browser-use/browser-use)
- [GitHub Repository](https://github.com/rocketroz/ai-scraper)

---

**Created:** 2024-12-29
**Updated:** 2024-12-30
