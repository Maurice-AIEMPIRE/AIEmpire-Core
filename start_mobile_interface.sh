#!/bin/bash
# Mobile Empire Interface Launcher
# Startet die Web-App für Handy-Zugang

echo "🚀 Starte Mobile Empire Interface..."
echo "📱 Du kannst von deinem Handy aus zugreifen:"
echo "   http://localhost:8000"
echo "   oder http://[deine-ip]:8000"
echo ""
echo "Stelle sicher, dass diese Umgebungsvariablen gesetzt sind:"
echo "  GEMINI_API_KEY=dein_gemini_key"
echo "  CLAUDE_API_KEY=dein_claude_key"
echo "  GROK_API_KEY=dein_grok_key"
echo ""

cd "$(dirname "$0")"

# Erstelle virtuelle Umgebung falls nicht vorhanden
if [ ! -d ".venv" ]; then
    echo "🐍 Erstelle virtuelle Umgebung..."
    python3 -m venv .venv
fi

# Aktiviere virtuelle Umgebung
source .venv/bin/activate

# Installiere Dependencies
echo "📦 Installiere Dependencies..."
pip install -r requirements.txt

# Starte die App
echo "🌐 Starte Web-App..."
python mobile_empire_interface.py