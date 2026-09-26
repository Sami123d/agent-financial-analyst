# Implementation Plan: Asynchronous Background Processing & Polling

Evolve the platform from a blocking synchronous model to an asynchronous background task queue model with dynamic status polling and live log tracking in the frontend.

---

## User Review Required

> [!IMPORTANT]
> This change modifies both the backend API request schema for `/analyze` (now returning a Job Status object instead of a complete report) and the React frontend logic (which will now poll the backend instead of waiting on a single blocking HTTP connection). This is a breaking change for existing synchronous client scripts.

---

## Open Questions

No open questions. The implementation uses FastAPI's native `BackgroundTasks` to avoid installing Redis/Celery locally, keeping the application dependency-free and easy to run on Windows.

---

## Proposed Changes

### Backend API Modernization

Modify the FastAPI endpoints to handle job submission, tracking, and logs.

#### [MODIFY] [api/main.py](file:///C:/Users/Ismail%20Sajid/Downloads/agent-financial-analyst-main/agent-financial-analyst-main/src/agent_financial_analyst/api/main.py)
- Create a global in-memory job store `JOBS_DB: Dict[str, Dict[str, Any]]` to persist task statuses, execution errors, output reports, and live log traces.
- Add dynamic log hooks so the orchestrator can write logs to a specific job ID.
- Define a new `/jobs/{job_id}` GET endpoint that returns:
  ```json
  {
    "job_id": "string",
    "status": "pending | running | completed | failed",
    "logs": ["string"],
    "result": {} or null,
    "error": "string" or null
  }
  ```
- Refactor the `/analyze` POST endpoint to:
  - Generate a unique `job_id`.
  - Initialize the job status as `"pending"`.
  - Queue the analysis using FastAPI `BackgroundTasks`.
  - Return the `job_id` and initial status immediately (HTTP 202).

---

### Orchestrator Custom Logging

#### [MODIFY] [core/orchestrator.py](file:///C:/Users/Ismail%20Sajid/Downloads/agent-financial-analyst-main/agent-financial-analyst-main/src/agent_financial_analyst/core/orchestrator.py)
- Add a thread-safe / task-safe logging mechanism so that messages written via `logger.info` can also append directly to `JOBS_DB[job_id]["logs"]` if running as a background job.

---

### React Frontend Polling & Real-time Trace

#### [MODIFY] [frontend/src/App.tsx](file:///C:/Users/Ismail%20Sajid/Downloads/agent-financial-analyst-main/agent-financial-analyst-main/frontend/src/App.tsx)
- Refactor `handleSearch` to:
  - Send POST request to `/analyze`, get a `job_id`.
  - Begin a recursive polling interval (every 1000ms) to `/jobs/{job_id}`.
  - Pull and display the backend's real-time logs in the "Agent Cluster Logs" sidebar.
  - When status matches `"completed"`, display the report and terminate the polling.
  - If status matches `"failed"`, stop and show the error.

---

## Verification Plan

### Automated Tests
- Write a test inside `tests/test_core.py` testing the async background task execution flow and job endpoint retrieval.

### Manual Verification
- Start the backend: `python -m agent_financial_analyst.cli serve`
- Start the frontend: `cd frontend; npm run dev`
- Run a search for `AAPL` and check if the sidebar logs update incrementally in real time as the agents finish execution.
