#!/bin/bash
#═══════════════════════════════════════════════════════════════
# Autopilot Empire - Ollama Model Download Script
# Maurice's AI Business System
#═══════════════════════════════════════════════════════════════
#
# Lädt alle benötigten AI-Modelle für Ollama herunter
# USAGE: bash download-models.sh
#
#═══════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "🤖 AUTOPILOT EMPIRE - Ollama Model Download"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check if Ollama container is running
if ! docker ps | grep -q autopilot-ollama; then
    echo "❌ Error: Ollama container is not running"
    echo "   Please start the stack first: docker-compose up -d"
    exit 1
fi

echo "✅ Ollama container is running"
echo ""

# Models to download
MODELS=(
    "mixtral:8x7b"
    "llama3.3"
    "qwen2.5"
    "deepseek-coder"
    "openhermes"
    "neural-chat"
)

echo "📥 Downloading ${#MODELS[@]} models..."
echo "   ⚠️  This may take 20-30 minutes depending on your connection"
echo ""

# Download each model
for i in "${!MODELS[@]}"; do
    MODEL="${MODELS[$i]}"
    NUM=$((i + 1))
    
    echo "───────────────────────────────────────────────────────────────"
    echo "[$NUM/${#MODELS[@]}] Downloading: $MODEL"
    echo "───────────────────────────────────────────────────────────────"
    
    if docker exec -it autopilot-ollama ollama pull "$MODEL"; then
        echo "✅ $MODEL downloaded successfully"
    else
        echo "❌ Failed to download $MODEL"
        echo "   You can retry later with: docker exec -it autopilot-ollama ollama pull $MODEL"
    fi
    echo ""
done

echo "═══════════════════════════════════════════════════════════════"
echo "✅ MODEL DOWNLOAD COMPLETED!"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Verify models
echo "📋 Verifying installed models..."
docker exec -it autopilot-ollama ollama list

echo ""
echo "🎉 All models are ready!"
echo "   You can now use the Autopilot Empire system."
echo ""
echo "Next steps:"
echo "   1. Open dashboard: http://localhost:8000"
echo "   2. Open monitoring: http://localhost:9090"
echo "   3. Check orchestrator logs: docker-compose logs -f orchestrator"
echo ""
