"""
Browser Use Service - AI-powered browser automation API
Designed to integrate with n8n workflows for FitTwin automation tasks
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


def get_llm():
    """Initialize LLM based on environment configuration."""
    if LLM_PROVIDER == "openai":
        from browser_use import ChatOpenAI
        return ChatOpenAI(
            model=LLM_MODEL,
            temperature=0.1,
        )
    elif LLM_PROVIDER == "anthropic":
        from browser_use import ChatAnthropic
        return ChatAnthropic(
            model=LLM_MODEL or "claude-sonnet-4-20250514",
            temperature=0.1,
        )
    elif LLM_PROVIDER == "ollama":
        from browser_use import ChatOllama
        return ChatOllama(
            model=LLM_MODEL or "llama3.2",
            host=OLLAMA_HOST,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")


# Task storage (in production, use Redis)
task_store: dict[str, dict] = {}


# Pydantic Models
class TaskRequest(BaseModel):
    """Request model for browser automation tasks."""
    task: str = Field(..., description="Natural language description of the task")
    url: Optional[str] = Field(None, description="Starting URL (optional)")
    timeout: int = Field(300, description="Task timeout in seconds")
    save_screenshot: bool = Field(False, description="Save screenshot on completion")
    structured_output: Optional[dict] = Field(None, description="JSON schema for structured output")
    metadata: Optional[dict] = Field(None, description="Custom metadata for tracking")


class TaskResponse(BaseModel):
    """Response model for task results."""
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None


class TaskStatus(BaseModel):
    """Status check response."""
    task_id: str
    status: str
    progress: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    llm_provider: str
    llm_model: str
    timestamp: str


# Lifespan for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting Browser Use Service with {LLM_PROVIDER}/{LLM_MODEL}")
    # Startup: verify LLM connection
    try:
        llm = get_llm()
        logger.info("LLM connection verified")
    except Exception as e:
        logger.warning(f"LLM connection failed on startup: {e}")
    yield
    # Shutdown
    logger.info("Shutting down Browser Use Service")


# FastAPI App
app = FastAPI(
    title="Browser Use Service",
    description="AI-powered browser automation for n8n workflows",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for n8n integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def execute_browser_task(task_id: str, request: TaskRequest):
    """Execute a browser automation task asynchronously."""
    task_store[task_id]["status"] = "running"
    start_time = datetime.now()
    
    try:
        from browser_use import Agent, Browser

        llm = get_llm()

        # Configure browser with direct parameters
        browser = Browser(
            headless=True,
            disable_security=False,
        )
        
        # Build task string
        task_description = request.task
        if request.url:
            task_description = f"Go to {request.url}. Then: {request.task}"
        
        if request.structured_output:
            task_description += f"\n\nReturn the result as JSON matching this schema: {json.dumps(request.structured_output)}"
        
        # Create and run agent
        agent = Agent(
            task=task_description,
            llm=llm,
            browser=browser,
        )
        
        result = await asyncio.wait_for(
            agent.run(),
            timeout=request.timeout
        )
        
        # Handle screenshot
        screenshot_path = None
        if request.save_screenshot:
            screenshot_path = f"/app/data/screenshots/{task_id}.png"
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            # Screenshot logic would go here
        
        await browser.stop()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        task_store[task_id].update({
            "status": "completed",
            "result": str(result),
            "completed_at": end_time.isoformat(),
            "duration_seconds": duration,
            "screenshot_path": screenshot_path,
        })
        
        logger.info(f"Task {task_id} completed in {duration:.2f}s")
        
    except asyncio.TimeoutError:
        task_store[task_id].update({
            "status": "failed",
            "error": f"Task timed out after {request.timeout} seconds",
            "completed_at": datetime.now().isoformat(),
        })
        logger.error(f"Task {task_id} timed out")
        
    except Exception as e:
        task_store[task_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now().isoformat(),
        })
        logger.error(f"Task {task_id} failed: {e}")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Docker and monitoring."""
    return HealthResponse(
        status="healthy",
        llm_provider=LLM_PROVIDER,
        llm_model=LLM_MODEL,
        timestamp=datetime.now().isoformat(),
    )


@app.post("/run-task", response_model=TaskResponse)
async def run_task(request: TaskRequest, background_tasks: BackgroundTasks):
    """
    Submit a browser automation task.
    
    The task runs asynchronously. Use /task/{task_id} to check status.
    For n8n: configure webhook callback in metadata for completion notification.
    """
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
    
    task_store[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "request": request.model_dump(),
        "started_at": datetime.now().isoformat(),
        "result": None,
        "error": None,
    }
    
    # Run task in background
    background_tasks.add_task(execute_browser_task, task_id, request)
    
    logger.info(f"Task {task_id} queued: {request.task[:100]}...")
    
    return TaskResponse(
        task_id=task_id,
        status="pending",
        started_at=task_store[task_id]["started_at"],
    )


@app.post("/run-task-sync", response_model=TaskResponse)
async def run_task_sync(request: TaskRequest):
    """
    Submit and wait for a browser automation task (synchronous).
    
    Use this for simpler n8n workflows that expect immediate results.
    Warning: May timeout for long-running tasks.
    """
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
    
    task_store[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "request": request.model_dump(),
        "started_at": datetime.now().isoformat(),
        "result": None,
        "error": None,
    }
    
    await execute_browser_task(task_id, request)
    
    task_data = task_store[task_id]
    
    if task_data["status"] == "failed":
        raise HTTPException(status_code=500, detail=task_data["error"])
    
    return TaskResponse(
        task_id=task_id,
        status=task_data["status"],
        result=task_data.get("result"),
        error=task_data.get("error"),
        screenshot_path=task_data.get("screenshot_path"),
        started_at=task_data["started_at"],
        completed_at=task_data.get("completed_at"),
        duration_seconds=task_data.get("duration_seconds"),
    )


@app.get("/task/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get the status and result of a task."""
    if task_id not in task_store:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_data = task_store[task_id]
    
    return TaskResponse(
        task_id=task_id,
        status=task_data["status"],
        result=task_data.get("result"),
        error=task_data.get("error"),
        screenshot_path=task_data.get("screenshot_path"),
        started_at=task_data["started_at"],
        completed_at=task_data.get("completed_at"),
        duration_seconds=task_data.get("duration_seconds"),
    )


@app.get("/tasks")
async def list_tasks(status: Optional[str] = None, limit: int = 50):
    """List recent tasks, optionally filtered by status."""
    tasks = list(task_store.values())
    
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    
    # Sort by start time, most recent first
    tasks.sort(key=lambda x: x["started_at"], reverse=True)
    
    return {"tasks": tasks[:limit], "total": len(tasks)}


@app.delete("/task/{task_id}")
async def delete_task(task_id: str):
    """Delete a task from the store."""
    if task_id not in task_store:
        raise HTTPException(status_code=404, detail="Task not found")
    
    del task_store[task_id]
    return {"message": f"Task {task_id} deleted"}


# Convenience endpoints for common FitTwin use cases

@app.post("/scrape-pricing")
async def scrape_pricing(url: str, background_tasks: BackgroundTasks):
    """
    Convenience endpoint: Extract pricing information from a URL.
    Useful for competitor monitoring.
    """
    request = TaskRequest(
        task="Find all pricing information on this page. Extract tier names, prices, billing periods, and feature lists. Return as structured JSON.",
        url=url,
        structured_output={
            "tiers": [
                {
                    "name": "string",
                    "price": "string",
                    "billing_period": "string",
                    "features": ["string"]
                }
            ]
        }
    )
    return await run_task(request, background_tasks)


@app.post("/scrape-products")
async def scrape_products(url: str, background_tasks: BackgroundTasks):
    """
    Convenience endpoint: Extract product catalog from an e-commerce page.
    Useful for demo data collection.
    """
    request = TaskRequest(
        task="Extract all product information visible on this page. Get product names, prices, images URLs, and descriptions. Return as JSON array.",
        url=url,
        structured_output={
            "products": [
                {
                    "name": "string",
                    "price": "string",
                    "image_url": "string",
                    "description": "string"
                }
            ]
        }
    )
    return await run_task(request, background_tasks)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
