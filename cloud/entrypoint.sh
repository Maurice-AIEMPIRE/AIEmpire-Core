#!/bin/bash
# AI Empire Cloud Entrypoint
# ===========================
# Starts all services in the container

echo "=== AI EMPIRE CLOUD — Starting ==="

# 1. Start Redis
echo "Starting Redis..."
redis-server --daemonize yes --maxmemory 256mb --maxmemory-policy allkeys-lru

# 2. Start Ollama (background)
echo "Starting Ollama..."
ollama serve &
sleep 3

# 3. Pull model if not present
if ! ollama list | grep -q "qwen2.5-coder:7b"; then
    echo "Pulling qwen2.5-coder:7b (einmalig)..."
    ollama pull qwen2.5-coder:7b
fi

# 4. Start Empire API
echo "Starting Empire API on port 8080..."
cd /app
python3 cloud/cloud_api.py
