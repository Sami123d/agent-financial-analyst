# --- Backend Stage ---
FROM python:3.11-slim as backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY pyproject.toml .
RUN pip install .

# Copy source code
COPY src /app/src

# Expose API port
EXPOSE 8000

# Start command
CMD ["agent-analyst", "serve", "--host", "0.0.0.0", "--port", "8000"]

# --- Frontend Stage ---
FROM node:20-slim as frontend

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend ./
RUN npm run build

# --- Production Stage (Example with Nginx) ---
# In a real FAANG environment, we'd use a more sophisticated serving layer
# but for this audit, we'll focus on the containerized build.
FROM nginx:alpine as production

COPY --from=frontend /app/frontend/dist /usr/share/nginx/html
# Note: Nginx configuration would go here to proxy to backend
EXPOSE 80
