# SkyBot — AI Agent via Telegram

Open-Source AI Agent der 24/7 in der Cloud (oder auf deinem Mac) laeuft und ueber Telegram gesteuert wird.

## Architektur

```
┌──────────────────────────────────────────────────────┐
│                    TELEGRAM                           │
│               (Dein Handy/iPad)                       │
└──────────────────┬───────────────────────────────────┘
                   │ Messages
                   ▼
┌──────────────────────────────────────────────────────┐
│              SKYBOT (bot.py)                          │
│         Telegram Bot Interface                        │
│    Security / Routing / Progress Display              │
└──────────────────┬───────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────┐
│             AGENT (agent.py)                          │
│     Claude API ←→ Tool Use Loop                       │
│     Fallback: Ollama (lokal) / Kimi (Cloud)           │
└────┬────────┬────────┬────────┬────────┬─────────────┘
     │        │        │        │        │
     ▼        ▼        ▼        ▼        ▼
┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
│  Web   ││ Code   ││ File   ││ GitHub ││  Web   │
│ Search ││  Exec  ││  Ops   ││ Search ││Builder │
└────────┘└────────┘└────────┘└────────┘└────────┘
```

## Quick Start

```bash
# 1. Setup (installiert alles + fragt nach Tokens)
bash skybot/setup.sh

# 2. Starten
python3 -m skybot.bot
```

## Voraussetzungen

| Was | Warum | Pflicht? |
|-----|-------|----------|
| Python 3.11+ | Runtime | Ja |
| TELEGRAM_BOT_TOKEN | Bot-Zugang | Ja |
| ANTHROPIC_API_KEY | Claude + Tool Use | Nein (aber empfohlen) |
| MOONSHOT_API_KEY | Kimi Fallback | Nein |
| Ollama | Lokales AI Modell | Nein |

**Ohne ANTHROPIC_API_KEY:** Nur Chat-Modus (Ollama oder Kimi)
**Mit ANTHROPIC_API_KEY:** Voller Agent mit 5 Tools

## .env Konfiguration

```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
ANTHROPIC_API_KEY=sk-ant-...
MOONSHOT_API_KEY=sk-...            # Optional: Kimi Fallback
GITHUB_TOKEN=ghp_...               # Optional: Hoehere GitHub Rate Limits
SKYBOT_MODEL=claude-sonnet-4-5-20250929  # Optional: Modell aendern
SKYBOT_MAX_TOKENS=4096             # Optional
SKYBOT_MAX_TOOL_ROUNDS=15          # Optional
```

## Telegram Befehle

| Befehl | Funktion |
|--------|----------|
| `/start` | Willkommen + Info |
| `/help` | Alle Befehle |
| `/stats` | Agent-Statistiken |
| `/reset` | Konversation loeschen |
| `/model` | Aktives Modell anzeigen |
| `/tools` | Verfuegbare Tools |
| Einfach tippen | Agent arbeitet! |

## Beispiel-Prompts

```
Suche nach den trending Python repos auf GitHub

Baue mir eine Landing Page fuer BMA Beratung mit Kontaktformular

Schreib ein Python Script das alle CSV Dateien in einem Ordner zusammenfuehrt

Was sind die neuesten Nachrichten ueber AI Agents?

Erstelle ein Snake Game in Python und fuehre es aus

Recherchiere die Top 5 Fiverr Gigs fuer AI Automation
```

## Tools

### 1. Web Search (`web_search`)
- DuckDuckGo Suche (kein API Key noetig)
- URLs direkt abrufen und Text extrahieren

### 2. Code Execution (`code_exec`)
- Python und Bash Code in Sandbox ausfuehren
- Timeout: 30 Sekunden
- Gefaehrliche Befehle blockiert

### 3. File Operations (`file_ops`)
- Lesen, Schreiben, Loeschen, Verzeichnisse
- Nur innerhalb `skybot_workspace/`

### 4. GitHub Search (`github_search`)
- Repos, Code, User, Trending
- Optional mit GITHUB_TOKEN fuer hoehere Limits

### 5. Web Builder (`web_builder`)
- Generiert komplette Websites (HTML/CSS/JS)
- Gespeichert in `skybot_workspace/websites/`

## Deployment

### Option A: Mac (LaunchAgent)
```bash
# Auto-Start bei Boot
cat > ~/Library/LaunchAgents/com.aiempire.skybot.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.aiempire.skybot</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/python3</string>
    <string>-m</string>
    <string>skybot.bot</string>
  </array>
  <key>WorkingDirectory</key><string>$(pwd)</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
</dict></plist>
EOF
launchctl load ~/Library/LaunchAgents/com.aiempire.skybot.plist
```

### Option B: VPS/Cloud (systemd)
```bash
sudo cat > /etc/systemd/system/skybot.service << EOF
[Unit]
Description=SkyBot AI Agent
After=network.target

[Service]
User=$USER
WorkingDirectory=/home/$USER/AIEmpire-Core
ExecStart=/usr/bin/python3 -m skybot.bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable --now skybot
```

### Option C: Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r skybot/requirements.txt
CMD ["python3", "-m", "skybot.bot"]
```

## Zukunft / Erweiterungen

- [ ] noVNC Live Desktop Streaming (sehe was der Agent tut)
- [ ] Claude Computer Use API (echte Desktop-Kontrolle)
- [ ] Scheduled Tasks (taegliche Reports, Auto-Scans)
- [ ] WhatsApp Integration
- [ ] Multi-User Support
- [ ] Persistent Memory (ChromaDB)
- [ ] Voice Messages (Whisper STT)
