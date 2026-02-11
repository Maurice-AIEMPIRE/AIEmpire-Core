# AI Empire — Cloud Container (100% Open Source)
# ================================================
# Runs on: Google Cloud Run, GCE, any Docker host
# Base: Python 3.12 slim (Debian)

FROM python:3.12-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git redis-server && \
    rm -rf /var/lib/apt/lists/*

# Install Ollama (free, open source LLM runtime)
RUN curl -fsSL https://ollama.com/install.sh | sh

# Working directory
WORKDIR /app

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create data dirs
RUN mkdir -p empire_data/scans empire_data/content empire_data/leads \
    empire_data/revenue empire_data/agent_results empire_data/feed_scans \
    antigravity/_knowledge antigravity/_state antigravity/_reports

# Expose ports
EXPOSE 8080 11434 6379

# Health check
HEALTHCHECK --interval=30s --timeout=10s \
    CMD python3 -c "import httpx; r=httpx.get('http://localhost:8080/health'); assert r.status_code==200"

# Start script
COPY cloud/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
