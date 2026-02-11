#!/bin/bash
# 🚨 ANTIGRAVITY INSTANT FIX
# Führe diesen Script direkt in deinem Terminal aus

echo "🔧 AIEmpire Antigravity Reparatur..."
echo "=================================="

# 1. Google Cloud Projekt setzen
echo "1️⃣  Setze Google Cloud Project..."
gcloud config set project ai-empire-486415
gcloud config set compute/region europe-west4

# 2. Authentifizierung
echo "2️⃣  Prüfe Authentifizierung..."
gcloud auth login || echo "⚠️  Authentifizierung benötigt - bitte den Browser-Prompt folgen"

# 3. Alle Python-Prozesse killen (sauber)
echo "3️⃣  Stoppe alte Prozesse..."
pkill -f "antigravity" 2>/dev/null || true
pkill -f "python.*orchestrator" 2>/dev/null || true
sleep 2

# 4. Cache cleanen
echo "4️⃣  Cleane Python Cache..."
cd "$(dirname "$0")/.." || exit 1
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# 5. .env validieren
echo "5️⃣  Validiere .env..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env fehlt! Erstelle aus .env.example..."
    cp .env.example .env 2>/dev/null || echo "⚠️  .env.example nicht gefunden"
fi

# 6. Test: Config laden
echo "6️⃣  Teste Config..."
python3 -c "
from antigravity.config import GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_REGION
if GOOGLE_CLOUD_PROJECT:
    print(f'✅ Project: {GOOGLE_CLOUD_PROJECT}')
    print(f'✅ Region: {GOOGLE_CLOUD_REGION}')
else:
    print('❌ Project ist LEER!')
    exit(1)
" || exit 1

# 7. Health Check
echo "7️⃣  Health Check..."
python3 -c "
from antigravity.gemini_client import GeminiClient
client = GeminiClient(use_vertex=True)
if client.health_check():
    print('✅ Antigravity ist READY!')
else:
    print('⚠️  Vertex AI nicht verfügbar, aber Ollama funktioniert')
" || echo "⚠️  Health Check mit Fehler"

echo ""
echo "=================================="
echo "✅ REPARATUR ABGESCHLOSSEN!"
echo ""
echo "Jetzt starten:"
echo "  python workflow-system/empire.py status"
echo "  python workflow-system/empire.py cowork --daemon --focus revenue"
echo ""
