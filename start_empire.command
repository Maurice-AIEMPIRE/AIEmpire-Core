#!/bin/bash
# ══════════════════════════════════════════════════
# AI EMPIRE - Ein-Klick Starter
# Pushed Code → Startet Services → Startet App
# Doppelklick auf deinem Mac und fertig.
# ══════════════════════════════════════════════════

cd "$(dirname "$0")"

clear
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║        🔴 AI EMPIRE CONTROL CENTER 🔴       ║"
echo "╠══════════════════════════════════════════════╣"
echo "║  Initialisiere alle Systeme...               ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Step 1: Git Push ──
echo "📤 [1/4] Code wird zu GitHub gepusht..."
git add -A 2>/dev/null
git commit -m "[Empire] Auto-deploy $(date '+%Y-%m-%d %H:%M')" 2>/dev/null
git push origin main 2>/dev/null && echo "   ✅ Gepusht" || echo "   ⚠️  Push fehlgeschlagen (offline?)"
echo ""

# ── Step 2: Dependencies ──
echo "📦 [2/4] Dependencies werden geprüft..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    pip3 install fastapi uvicorn httpx pydantic --quiet 2>/dev/null
    echo "   ✅ Python Packages installiert"
else
    echo "   ✅ Alle Dependencies vorhanden"
fi
echo ""

# ── Step 3: Background Services ──
echo "🔧 [3/4] Services werden gestartet..."
if command -v redis-server &>/dev/null; then
    brew services start redis 2>/dev/null && echo "   ✅ Redis gestartet" || echo "   ⚠️  Redis Problem"
fi
if command -v pg_isready &>/dev/null; then
    brew services start postgresql@16 2>/dev/null && echo "   ✅ PostgreSQL gestartet" || echo "   ⚠️  PostgreSQL Problem"
fi
if command -v ollama &>/dev/null; then
    ollama serve &>/dev/null &
    echo "   ✅ Ollama gestartet"
fi
echo ""

# ── Step 4: Start Empire API ──
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "localhost")
echo "🚀 [4/4] Empire API wird gestartet..."
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║                                              ║"
echo "║  🖥  Mac:     http://localhost:3333           ║"
echo "║  📱 iPhone:  http://${LOCAL_IP}:3333         ║"
echo "║                                              ║"
echo "║  ─────────────────────────────────────────   ║"
echo "║  iPhone Setup:                               ║"
echo "║  1. Öffne den Link oben in Safari            ║"
echo "║  2. Teilen-Button (□↑) drücken               ║"
echo "║  3. 'Zum Home-Bildschirm' wählen             ║"
echo "║  4. Fertig - sieht aus wie eine App!         ║"
echo "║                                              ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "Drücke Ctrl+C zum Beenden"
echo ""

cd empire-api
python3 server.py
