"""FastAPI implementation for the institutional Research Analyst."""

from __future__ import annotations

import contextvars
import os
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger

from ..core.orchestrator import ResearchOrchestrator
from ..schema.models import ResearchReport
from ..utils.logging import setup_logging

# Initialize Logging
setup_logging(level="INFO")

# Context var for tracking current job logging session
job_id_var = contextvars.ContextVar("job_id", default=None)

# Custom rate-limiting resolver partition per API Key
def get_limit_key(request: Request) -> str:
    key = request.headers.get("X-API-Key")
    return f"key:{key}" if key else f"ip:{get_remote_address(request)}"

# Initialize Rate Limiter
limiter = Limiter(key_func=get_limit_key)
app = FastAPI(
    title="Agent Financial Analyst API",
    description="FAANG-level institutional equity research as a service.",
    version="1.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Header scheme configuration
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
ALLOWED_API_KEYS = set(os.environ.get("ALLOWED_API_KEYS", "analyst_pro_dev_key_2026").split(","))

def verify_api_key(api_key: Optional[str] = Depends(api_key_header)):
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Authentication credentials missing in X-API-Key header"
        )
    if api_key not in ALLOWED_API_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key"
        )
    return api_key

# CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Orchestrator
orchestrator = ResearchOrchestrator()

# In-memory job repository
JOBS_DB: Dict[str, Dict[str, Any]] = {}


# Custom loguru sink to route agent console outputs into JOBS_DB in real time
def jobs_log_sink(message):
    record = message.record
    job_id = job_id_var.get()
    if job_id and job_id in JOBS_DB:
        # Append formatted message
        JOBS_DB[job_id]["logs"].append(record["message"])

# Wire sink to loguru
logger.add(jobs_log_sink, level="INFO")


class ResearchRequest(BaseModel):
    ticker: str


class JobStatus(BaseModel):
    job_id: str
    status: str
    ticker: str
    logs: List[str]
    result: Optional[ResearchReport] = None
    error: Optional[str] = None


@app.get("/")
def read_root():
    return {"status": "online", "description": "Agent Financial Analyst API"}


async def run_analysis_job(job_id: str, ticker: str):
    """Async task executor run by background worker thread."""
    job_id_var.set(job_id)
    JOBS_DB[job_id]["status"] = "running"
    JOBS_DB[job_id]["logs"].append(f"Job running in worker thread with ID: {job_id}")
    
    try:
        report = await orchestrator.analyze(ticker)
        JOBS_DB[job_id]["status"] = "completed"
        JOBS_DB[job_id]["result"] = report
        JOBS_DB[job_id]["logs"].append("Job completed successfully.")
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        JOBS_DB[job_id]["status"] = "failed"
        JOBS_DB[job_id]["error"] = str(e)
        JOBS_DB[job_id]["logs"].append(f"Job failed: {e}")


@app.post("/analyze", response_model=JobStatus, status_code=202)
@limiter.limit("5/minute")
async def analyze_stock(
    payload: ResearchRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    Kicks off a full multi-agent institutional research report for the 
    specified stock ticker asynchronously.
    """
    job_id = str(uuid.uuid4())
    ticker_upper = payload.ticker.upper()
    
    # Initialize job state
    JOBS_DB[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "ticker": ticker_upper,
        "logs": [f"Enqueued research job for {ticker_upper}"],
        "result": None,
        "error": None
    }
    
    # Run in background
    background_tasks.add_task(run_analysis_job, job_id, ticker_upper)
    
    return JOBS_DB[job_id]


@app.get("/jobs/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str, api_key: str = Depends(verify_api_key)):
    """Retrieve current logs and execution progress for a queued job."""
    if job_id not in JOBS_DB:
        raise HTTPException(status_code=404, detail="Job not found")
    return JOBS_DB[job_id]


@app.get("/health")
def health_check():
    return {"status": "healthy"}

