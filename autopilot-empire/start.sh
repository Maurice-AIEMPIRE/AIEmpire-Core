#!/bin/bash
#═══════════════════════════════════════════════════════════════
# Autopilot Empire - Quick Start Script
# Maurice's AI Business System
#═══════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "🚀 AUTOPILOT EMPIRE - Quick Start"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env from template..."
    cp .env.template .env
    echo "✅ .env created - please edit it if you want to add API keys"
    echo ""
fi

# Start Docker stack
echo "📦 Starting Docker stack..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start (30 seconds)..."
sleep 30

# Check services
echo ""
echo "🔍 Checking service status..."
docker-compose ps

echo ""
echo "🏥 Running health checks..."

# Orchestrator health
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ Orchestrator: healthy"
else
    echo "⚠️  Orchestrator: not ready yet (may need more time)"
fi

# Monitor health
if curl -f http://localhost:9090/health >/dev/null 2>&1; then
    echo "✅ Monitor: healthy"
else
    echo "⚠️  Monitor: not ready yet (may need more time)"
fi

# Ollama health
if curl -f http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "✅ Ollama: healthy"
else
    echo "⚠️  Ollama: not ready yet (may need more time)"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🎉 AUTOPILOT EMPIRE IS STARTING!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📊 Dashboards:"
echo "   Agent Dashboard:  http://localhost:8000"
echo "   Monitoring:       http://localhost:9090"
echo ""
echo "📝 Logs:"
echo "   docker-compose logs -f orchestrator"
echo "   docker-compose logs -f content-service"
echo "   docker-compose logs -f monitor"
echo ""
echo "⚠️  IMPORTANT: First Time Setup"
echo "   If this is your first start, download AI models with:"
echo "   bash download-models.sh"
echo ""
echo "📱 iPhone Remote Access:"
echo "   Run: bash iphone-remote-setup.sh"
echo ""
echo "🛑 To stop the system:"
echo "   docker-compose down"
echo ""
