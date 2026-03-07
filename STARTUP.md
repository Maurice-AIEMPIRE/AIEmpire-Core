# 🚀 AIEmpire Startup - Schritt für Schritt

## ⚡ QUICKSTART (5 Minuten)

### SCHRITT 1: CLI Bot starten
```bash
cd /home/user/AIEmpire-Core
python3 aibot.py
```

Das öffnet den **interaktiven Chat-Modus**. Jetzt kannst du:
```
> read empire_engine.py          # Datei lesen
> grep "def main"                # Code durchsuchen
> git status                      # Git Status
> bash "ps aux | head -5"         # Commands ausführen
> analyze "Was ist AIEmpire?"     # Ollama Analyse
> help                            # Alle Commands anzeigen
> quit                            # Beenden
```

---

## 🎯 VOLLSTÄNDIGE STARTUP SEQUENZ

### Phase 1: Voraussetzungen checken (2 min)

```bash
# 1. Python Version
python3 --version
# ✅ Muss 3.9+ sein

# 2. Ollama installiert?
which ollama
# Falls nicht: brew install ollama

# 3. Ollama läuft?
curl http://localhost:11434/api/tags
# Falls nicht: ollama serve &
```

---

### Phase 2: Bots starten

#### Option A: NUR CLI Bot (Empfohlen zum Starten!)
```bash
# Terminal 1: CLI Bot
python3 aibot.py
```

#### Option B: Telegram Bot AUCH starten
```bash
# Terminal 2: Telegram Bot
python3 telegram_bot/bot.py
# ⚠️ Funktioniert nur wenn Internet vorhanden
```

#### Option C: Web-Interface (FastAPI - optional)
```bash
# Terminal 3: Web-Interface starten
pip3 install fastapi uvicorn httpx
python3 local_bot_system.py
# Dann öffne: http://localhost:8000
```

---

## 📋 COMMANDS - VOLLSTÄNDIGE ÜBERSICHT

### 📖 FILE OPERATIONS

```bash
# Datei lesen
aibot.py read CLAUDE.md

# Datei bearbeiten
aibot.py edit file.py "old_code" "new_code"
```

### ⚙️ CODE EXECUTION

```bash
# Python Code ausführen
aibot.py bash "python3 empire_engine.py"

# Beliebige Commands
aibot.py exec "ps aux | grep ollama"

# Command mit Timeout (max 60 Sekunden)
aibot.py bash "sleep 10 && echo 'Done!'"
```

### 🔍 CODE SUCHE

```bash
# Pattern suchen
aibot.py grep "def main"

# Nach Funktionen suchen
aibot.py grep "class.*Bot"

# Mit glob pattern
aibot.py grep "TELEGRAM" "**/*.py"
```

### 🐙 GIT OPERATIONEN

```bash
# Status
aibot.py git status

# Commits anzeigen
aibot.py git log --oneline -5

# Änderungen adden
aibot.py git add -A

# Commit
aibot.py git commit -m "Message"

# Push
aibot.py git push origin claude/setup-lobehub-skills-3xEMa
```

### 🧠 OLLAMA ANALYSE (Kostenlos!)

```bash
# Ollama analysieren
aibot.py analyze "Erkläre kurz AIEmpire-Core"

# Code Review
aibot.py analyze "Review diesen Code: def main(): pass"

# Brainstorming
aibot.py analyze "10 Ideen für Revenue Channels"
```

---

## 🎮 INTERAKTIVER MODUS

Einfach starten:
```bash
python3 aibot.py
```

Dann kannst du direkt tippen:
```
> read CLAUDE.md
> grep empire_engine
> git status
> bash "ls -la"
> quit
```

---

## 📱 TELEGRAM BOT (Optional)

### Setup:
```bash
python3 telegram_bot/bot.py
```

### Features:
- 📝 Textnachrichten verarbeiten
- 📄 PDFs analysieren
- 📦 ZIP-Dateien entpacken
- 🖼️ Bilder speichern
- 🐦 X-Posts erstellen
- 💰 Revenue Reports

### Befehle im Telegram:
```
/start        - Bot starten + Menü
/status       - System Status
/revenue      - Revenue Report
/help         - Alle Befehle
/post [text]  - X-Post erstellen
```

---

## 🌐 WEB-INTERFACE (localhost:8000)

### Installation:
```bash
pip3 install fastapi uvicorn httpx
python3 local_bot_system.py
```

### Browser öffnen:
```
http://localhost:8000
```

### Features:
- 💬 Web-Chat Interface
- 📊 Health-Check
- 🔗 REST API: `POST /api/bot`

---

## ❌ TROUBLESHOOTING

### Problem: "Ollama not found"
```bash
# Installieren:
brew install ollama

# Ollama starten:
ollama serve
```

### Problem: "Port already in use"
```bash
# Für Port 8000 (FastAPI):
lsof -i :8000
kill -9 <PID>

# Für Ollama Port 11434:
lsof -i :11434
kill -9 <PID>
```

### Problem: "Telegram network error"
- Nur im Sandbox (kein Internet)
- In Produktion funktioniert es mit echtem Token

### Problem: "Command timeout"
- Erhöhe Timeout in aibot.py (default: 60s)
- Für lange Commands lieber direkt bash nutzen

---

## 🏗️ ARCHITECTURE

```
┌─────────────────────────────────────┐
│       AIEMPIRE STARTUP              │
├─────────────────────────────────────┤
│                                     │
│  CLI Bot (aibot.py)         [START] │
│  ├─ read/edit/exec/grep     📦     │
│  ├─ git commands             🐙    │
│  └─ ollama analyze           🧠    │
│                                     │
│  Telegram Bot (telegram_bot/)       │
│  ├─ File uploads             📁    │
│  ├─ Empire Engine commands   ⚙️    │
│  └─ X-Post generation       🐦    │
│                                     │
│  Web-Interface (local_bot_system)   │
│  ├─ FastAPI server          🌐    │
│  ├─ Web chat                💬    │
│  └─ REST API                🔗    │
│                                     │
│  Ollama Backend                     │
│  └─ qwen2.5:1.5b (kostenlos) 🤖   │
│                                     │
└─────────────────────────────────────┘
```

---

## 📊 RECOMMENDED WORKFLOW

### Täglich:
1. **CLI Bot starten** → `python3 aibot.py`
2. **Status checken** → `git status`
3. **Code bearbeiten** → `edit file.py ...`
4. **Commits machen** → `git add -A` → `git commit -m "..."`
5. **Pushen** → `git push`

### Bei Fragen/Analyse:
```bash
aibot.py analyze "Wie debugge ich X?"
```

### Empire Engine durchgehend laufen lassen:
```bash
# Terminal separieren:
python3 empire_engine.py auto  # Läuft im Hintergrund
```

---

## 💡 TIPPS

1. **CLI Bot ist schnell** - Nutze ihn für tägliche Arbeit
2. **Ollama ist kostenlos** - Nutze `analyze` commands
3. **Git Integration** - Commits direkt vom Bot
4. **Interaktiver Modus** - Tippe einfach `python3 aibot.py`
5. **Telegram für Mobile** - Bot auch auf dem Handy

---

## ✅ SUCCESS CHECKLIST

- [ ] Python 3.9+ installiert
- [ ] Ollama installiert & läuft
- [ ] aibot.py läuft (interaktiv)
- [ ] git status funktioniert
- [ ] Erste Datei gelesen (read CLAUDE.md)
- [ ] Ollama analyse funktioniert
- [ ] Telegram Bot optional gestartet
- [ ] Web-Interface optional aktiviert

---

**READY? Starten mit:**
```bash
python3 aibot.py
```

**Dann direkt eingeben:**
```
> read CLAUDE.md
> analyze "Was soll ich jetzt tun?"
> git status
```

🚀 **LOS GEHT'S!**
