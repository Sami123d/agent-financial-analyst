# Production Readiness Gap Analysis: `agent-financial-analyst`

A comprehensive review of what is required to transition this multi-agent prototype into a highly scalable, secure, and production-grade institutional platform.

---

## 🚦 Current Status Overview
* **Agent Architecture**: **90% Ready** (Robust model tiering, critique loop, dynamic asset routing, and parallel execution).
* **CLI & API Hooks**: **85% Ready** (API endpoints are wired; CLI crash bugs are fully resolved).
* **Data Integration**: **75% Ready** (Live yfinance and live SEC EDGAR ticker mappings are operational).
* **Production Infrastructure**: **30% Ready** (Needs database persistence, background worker queues, security, and hosting configs).

---

## 🛠️ The Production Gap: 6 Critical Pillars

### 1. Asynchronous Task Queue & Job Management
> [!IMPORTANT]
> Currently, the `/analyze` API endpoint executes the agent pipeline synchronously in the request-response thread. A single analysis takes **15–30 seconds**, which will timeout on standard API gateways (Nginx/Cloudflare limits are typically 30s) and block the server event loop under concurrent load.
* **Requirements**:
  - Integrate a task queue like **Celery** or **Redis Queue (RQ)**.
  - Implement a job polling model:
    1. User requests `/analyze` and gets a `job_id` instantly (HTTP 202).
    2. Workers execute the analysis in the background.
    3. Frontend polls `/jobs/{job_id}` or connects via **WebSockets** to stream live progress logs.

### 2. Authentication & Rate-Limiting Security
* **Current state**: Anyone can call the FastAPI endpoints. There is a simple rate-limiter, but no user boundary.
* **Requirements**:
  - Implement **JWT (JSON Web Token)** authentication (e.g. FastAPI Security with OAuth2).
  - Add API key management so enterprise users can call the service programmatically.
  - Tie rate-limiting to user IDs or client API keys, not just IP addresses.

### 3. Database Persistence
* **Current state**: Generated reports are written to local Markdown files. If the container restarts, all reports are lost.
* **Requirements**:
  - Add a relational database (e.g., **PostgreSQL**) to store user records, job states, metadata, and finalized research reports.
  - Store agent trace arrays and reasoning monologues (`agent_traces`) in a document-based store (or a JSONB column in Postgres) to run future analysis on agent errors.

### 4. Enterprise-Grade SEC Filing Extraction (RAG)
* **Current state**: The regex parser splits sections by finding "Item 1A" and "Item 1B" and slices the first 5,000 characters. If the filing HTML structure changes or has nested tables, the extraction might cut off early.
* **Requirements**:
  - Implement **Semantic Retrieval (RAG)**: chunk the SEC documents, embed them (e.g., using OpenAI `text-embedding-3-small`), store them in a vector database (**Qdrant / Chroma**), and query the database for specific risks.
  - Use a specialized SEC HTML parser (like `sec-parser`) to extract exact items cleanly regardless of structural deviations.

### 5. Telemetry & APM Connection
* **Current state**: OpenTelemetry hooks are set up in the code, but they are not exporting to any monitoring dashboard.
* **Requirements**:
  - Add an OpenTelemetry exporter to ship metrics and spans to a central system (e.g., **Datadog, Honeycomb, or Grafana Tempo**).
  - Configure alerts for LLM rate limit triggers (HTTP 429) or elevated latency.

### 6. DevOps & Infrastructure Configs
* **Current state**: Has a basic `Dockerfile` but no multi-container orchestration.
* **Requirements**:
  - Create a `docker-compose.yml` that orchestrates:
    - **FastAPI Backend App**
    - **React Frontend (Vite) App**
    - **Redis** (as message broker)
    - **Celery Worker**
    - **PostgreSQL Database**
  - Add Helm Charts or Kubernetes manifests for cloud deployment (AWS EKS, GCP GKE).
