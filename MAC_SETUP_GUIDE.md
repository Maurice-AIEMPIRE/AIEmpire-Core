# 🍎 Mac Setup Guide - AIEmpire-Core

> Schritt-für-Schritt Anleitung für die Installation auf deinem Mac

---

## 📋 Voraussetzungen prüfen

### System Check
\`\`\`bash
# macOS Version prüfen
sw_vers

# Empfohlen: macOS 13.0 (Ventura) oder neuer
# Dein System: Apple M4, 16GB RAM, macOS 26.2 ✅
\`\`\`

---

## 🛠️ Installation - Schritt für Schritt

### Schritt 1: Homebrew installieren (falls noch nicht vorhanden)

\`\`\`bash
# Prüfen ob Homebrew installiert ist
which brew

# Falls nicht installiert:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Nach der Installation:
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
\`\`\`

### Schritt 2: Basis-Tools installieren

\`\`\`bash
# Node.js (für CRM)
brew install node

# Python 3 (für Swarm & Content Generator)
brew install python3

# Git (sollte schon vorhanden sein)
brew install git

# Versionen prüfen
node --version   # v20+ empfohlen
python3 --version  # 3.10+ empfohlen
git --version
\`\`\`

### Schritt 3: Ollama installieren (AI Models lokal)

\`\`\`bash
# Ollama herunterladen und installieren
curl -fsSL https://ollama.com/install.sh | sh

# Ollama starten
ollama serve &

# Modelle herunterladen (ca. 5-10 Min pro Modell)
ollama pull qwen2.5-coder:7b
ollama pull mistral:7b

# Testen
ollama run mistral "Hallo, bist du bereit?"
\`\`\`

### Schritt 4: Datenbanken installieren

\`\`\`bash
# Redis (für Caching)
brew install redis

# PostgreSQL (für Datenspeicherung)
brew install postgresql@16

# Starten
brew services start redis
brew services start postgresql@16

# Status prüfen
brew services list
\`\`\`

### Schritt 5: Repository klonen

\`\`\`bash
# Ins Dokumente-Verzeichnis wechseln (oder beliebiges anderes)
cd ~/Documents

# Repository klonen
git clone https://github.com/mauricepfeifer-ctrl/AIEmpire-Core.git

# Ins Verzeichnis wechseln
cd AIEmpire-Core

# Struktur anschauen
ls -la
\`\`\`

---

## 🔑 API Keys konfigurieren

### Schritt 6: Environment Variables setzen

\`\`\`bash
# ~/.zshrc editieren
nano ~/.zshrc

# Folgendes ans Ende hinzufügen:

# ==========================================
# AIEmpire-Core API Keys
# ==========================================

# Kimi/Moonshot API (für Content Generator)
export MOONSHOT_API_KEY="sk-your-key-here"

# Twitter/X API (optional, für X Automation)
export X_API_KEY="your-x-api-key"
export X_API_SECRET="your-x-api-secret"
export X_ACCESS_TOKEN="your-access-token"
export X_ACCESS_SECRET="your-access-secret"

# GitHub Token (optional, für GitHub Scanner)
export GITHUB_TOKEN="ghp_your-token-here"

# ==========================================

# Speichern: Ctrl+O, Enter, Ctrl+X

# Neu laden
source ~/.zshrc

# Testen
echo $MOONSHOT_API_KEY
\`\`\`

### Wo bekomme ich API Keys?

| Service | URL | Kosten |
|---------|-----|--------|
| Kimi/Moonshot | https://platform.moonshot.cn | $7.72 Budget vorhanden ✅ |
| Twitter/X | https://developer.twitter.com | Kostenlos (Developer Account) |
| GitHub | https://github.com/settings/tokens | Kostenlos |

---

## 🚀 Komponenten starten

### CRM Server starten

\`\`\`bash
cd ~/Documents/AIEmpire-Core/crm

# Dependencies installieren (nur einmal)
npm install

# Server starten
node server.js

# Output:
# ✓ CRM Server läuft auf http://localhost:3500
# ✓ SQLite Database verbunden
\`\`\`

**In einem neuen Terminal-Tab:** ⌘+T

### Kimi Swarm aktivieren

\`\`\`bash
cd ~/Documents/AIEmpire-Core/kimi-swarm

# Virtual Environment erstellen (nur einmal)
python3 -m venv venv

# Aktivieren
source venv/bin/activate

# Dependencies installieren (nur einmal)
pip install aiohttp

# GitHub Scanner starten
python3 github_scanner_100k.py

# Output:
# Starting GitHub scan with 100,000 agents...
\`\`\`

**In einem neuen Terminal-Tab:** ⌘+T

### X Content Generator

\`\`\`bash
cd ~/Documents/AIEmpire-Core/x-lead-machine

# Post Generator starten
python3 post_generator.py

# Output:
# Generating X posts with Kimi K2.5...
# ✓ 10 posts created
\`\`\`

---

## ✅ Installation verifizieren

### Checklist

\`\`\`bash
# 1. Homebrew
brew --version ✅

# 2. Node.js
node --version ✅

# 3. Python
python3 --version ✅

# 4. Ollama
ollama list ✅

# 5. Redis
redis-cli ping
# Should return: PONG ✅

# 6. PostgreSQL
psql --version ✅

# 7. Repository
ls ~/Documents/AIEmpire-Core ✅

# 8. API Keys
echo $MOONSHOT_API_KEY ✅
\`\`\`

### Services Status prüfen

\`\`\`bash
# Brew Services
brew services list

# Sollte zeigen:
# redis       started
# postgresql@16 started
# ollama      started (optional)

# Ports prüfen
lsof -i :3500   # CRM Server
lsof -i :11434  # Ollama
lsof -i :6379   # Redis
lsof -i :5432   # PostgreSQL
\`\`\`

---

## 🔧 Troubleshooting

### Problem: Homebrew nicht gefunden

\`\`\`bash
# Homebrew Path zur Shell hinzufügen
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
source ~/.zprofile
\`\`\`

### Problem: Python nicht gefunden

\`\`\`bash
# Python3 Link erstellen
sudo ln -s /opt/homebrew/bin/python3 /usr/local/bin/python3

# Oder Homebrew Python nutzen
brew install python3
\`\`\`

### Problem: Port bereits belegt

\`\`\`bash
# Port freigeben (z.B. 3500)
lsof -ti:3500 | xargs kill -9

# Oder anderen Port nutzen
# In crm/server.js: const PORT = 3501
\`\`\`

### Problem: Redis startet nicht

\`\`\`bash
# Redis manuell starten
redis-server /opt/homebrew/etc/redis.conf

# Oder ohne Config
redis-server
\`\`\`

### Problem: PostgreSQL startet nicht

\`\`\`bash
# PostgreSQL manuell starten
pg_ctl -D /opt/homebrew/var/postgresql@16 start

# Status prüfen
pg_ctl -D /opt/homebrew/var/postgresql@16 status
\`\`\`

### Problem: Ollama Models nicht gefunden

\`\`\`bash
# Modelle neu herunterladen
ollama pull qwen2.5-coder:7b
ollama pull mistral:7b

# Modelle auflisten
ollama list
\`\`\`

---

## 📱 Nützliche Mac-Befehle

### Terminal Navigation

\`\`\`bash
# Neuer Terminal Tab
⌘+T

# Zwischen Tabs wechseln
⌘+1, ⌘+2, ⌘+3

# Terminal Fenster teilen
⌘+D (horizontal)
⌘+Shift+D (vertikal)

# Aktuellen Command abbrechen
Ctrl+C

# Prozess im Hintergrund
command &
\`\`\`

### Prozess Management

\`\`\`bash
# Laufende Prozesse anzeigen
ps aux | grep node
ps aux | grep python

# Prozess beenden
kill -9 <PID>

# Alle Node Prozesse beenden
pkill node

# Alle Python Prozesse beenden
pkill python
\`\`\`

---

## 🎯 Nächste Schritte

### Nach der Installation

1. ✅ **Teste CRM:**
   \`\`\`bash
   curl http://localhost:3500/api/leads
   \`\`\`

2. ✅ **Generiere X Posts:**
   \`\`\`bash
   cd x-lead-machine
   cat READY_TO_POST.md  # 7 fertige Posts anschauen
   \`\`\`

3. ✅ **Scanne GitHub:**
   \`\`\`bash
   cd kimi-swarm
   python3 github_scanner_100k.py
   \`\`\`

4. ✅ **Lese Strategien:**
   \`\`\`bash
   cd gold-nuggets
   cat GOLD_OPENCLAW_MASTERPLAN_2026-02-08.md
   \`\`\`

### Dokumentation lesen

- 📖 [COMPLETE_STRUCTURE.md](./COMPLETE_STRUCTURE.md) - Vollständige Struktur
- ⚡ [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - Schnellzugriff
- 🎨 [STRUCTURE_VISUAL.txt](./STRUCTURE_VISUAL.txt) - Visuelle Diagramme
- 📋 [COPILOT_BRIEFING.md](./COPILOT_BRIEFING.md) - System Briefing

---

## 💡 Pro-Tips für Mac

### Alfred Workflow (Optional)

\`\`\`bash
# Alfred installieren (Produktivitäts-Tool)
brew install --cask alfred

# Workflows erstellen für:
# - "aiempire start" → Startet alle Services
# - "aiempire stop" → Stoppt alle Services
# - "aiempire status" → Zeigt Status
\`\`\`

### iTerm2 (Optional)

\`\`\`bash
# Besseres Terminal
brew install --cask iterm2

# Features:
# - Split Panes
# - Better Search
# - Hotkey Window
# - Session Restoration
\`\`\`

### VS Code (Empfohlen)

\`\`\`bash
# Visual Studio Code installieren
brew install --cask visual-studio-code

# Projekt öffnen
cd ~/Documents/AIEmpire-Core
code .

# Extensions installieren:
# - Python
# - JavaScript
# - Docker
# - GitLens
\`\`\`

---

## 🎉 Fertig!

Du hast jetzt:
- ✅ Alle Tools installiert
- ✅ Repository geklont
- ✅ API Keys konfiguriert
- ✅ Services gestartet
- ✅ Alles getestet

**Next:** Start monetizing! 💰

Siehe [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) für tägliche Commands.

---

*Erstellt: 2026-02-08 | Version: 1.0 | Für: Maurice's Mac (M4, 16GB)*
