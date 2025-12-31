#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

# Pick compose command
if docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker-compose"
else
  echo "Error: Docker Compose not found. Install with: brew install docker-compose"
  exit 1
fi

echo "Using compose command: $COMPOSE"

# Ensure docker daemon is reachable
if ! docker info >/dev/null 2>&1; then
  echo "Error: Docker daemon not reachable."
  echo "If you use Colima, run: colima start"
  exit 1
fi

# Create .env if missing
if [ ! -f .env ]; then
  echo "Creating .env from .env.example..."
  cp .env.example .env
  echo "Edit .env (set passwords, choose LLM provider) before continuing."
  exit 1
fi

echo "Validating docker-compose.yml..."
$COMPOSE config >/dev/null

echo "Building containers..."
$COMPOSE build

echo "Starting services..."
$COMPOSE up -d

echo "Waiting briefly for services..."
sleep 8

echo "Service status:"
$COMPOSE ps

# If using Ollama, pull the model once
if grep -q "^LLM_PROVIDER=ollama" .env; then
  MODEL="$(grep "^LLM_MODEL=" .env | cut -d= -f2 || true)"
  MODEL="${MODEL:-llama3.2}"
  echo "Pulling Ollama model: $MODEL (only needed once)..."
  $COMPOSE exec -T ollama ollama pull "$MODEL" || true
fi

echo "Quick health checks:"
echo "n8n:        http://localhost:5678"
echo "BrowserUse: http://localhost:8000/health"
echo "Docs:       http://localhost:8000/docs"

curl -fsS http://localhost:8000/health >/dev/null && echo "Browser Use health: OK" || echo "Browser Use health: FAILED"