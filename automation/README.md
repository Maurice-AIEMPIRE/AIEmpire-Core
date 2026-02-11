# Automation Core (Empire)

Dieses Modul liefert einen simplen Router + Content-Workflows auf Basis der bestehenden `content_factory/`-Prompts.

## Quickstart

1) API-Keys setzen (Moonshot + OpenAI empfohlen; OpenRouter optional):

```bash
export MOONSHOT_API_KEY="..."     # Kimi (günstig, stark für Research)
export OPENAI_API_KEY="..."       # ChatGPT/Codex

# Optional (falls du OpenRouter nutzen willst)
export OPENROUTER_API_KEY="..."
export OPENROUTER_REFERRER="https://example.com"
export OPENROUTER_TITLE="AI Empire"
```

2) Dry-Run (keine Kosten, testet nur die Pipeline):

```bash
python3 -m automation run --workflow full
```

3) Echtlauf (API-Aufrufe aktiv):

```bash
python3 -m automation run --workflow full --execute
```

## Parameter

- `--workflow`: `full | threads | tweets | prompts | monetization`
- `--execute`: fuehrt echte LLM-Calls aus (sonst Dry-Run)
- `--targets`: z.B. `threads=20,tweets=60,premium_prompts=80`
- `--scale`: skaliert alle Targets (z.B. `0.2`)
- `--niche`, `--style`: ueberschreiben Defaults
- `--creative-mode`: Kreativprofil fuer X-Posts (z.B. `comedy_ai_cartoons_dark_humor_comic`)

## Router anpassen

Modelle und Provider liegen in `automation/config/router.json`.
Die Defaults sind so gesetzt, dass OpenRouter als Standard-Router fungiert.

## Outputs

Outputs landen in:
- `content_factory/deliverables/threads_50.md`
- `content_factory/deliverables/tweets_300.md`
- `content_factory/deliverables/premium_prompts_400.md`
- `content_factory/deliverables/monetization_strategy.md`
- `content_factory/deliverables/x_templates/latest.md`
- `content_factory/deliverables/x_templates/latest.json`

Backups werden automatisch unter `content_factory/deliverables/backup_YYYYMMDD_HHMMSS/` abgelegt.

Run-Logs:
- `automation/runs/run_<timestamp>.json`

Dry-Run Outputs:
- `automation/runs/dryrun_<run_id>/`


## Notes Ingest

Apple Notes (lokal, macOS):

```bash
python3 -m automation.ingest --source notes --limit 50 --execute
```

Ordner-Intake (z.B. `claude_intake/`):

```bash
python3 -m automation.ingest --source folder --path claude_intake --execute
```

Outputs:
- `ai-vault/nuggets/nuggets_<run_id>.json`
- `ai-vault/nuggets/nuggets_<run_id>.md`

Hinweis: Beim ersten Apple-Notes-Lauf fragt macOS nach Automation-/Notes-Berechtigungen.


## Status Report (Telegram)

```bash
# Report lokal schreiben
python3 -m automation.report

# Report + Telegram senden
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
python3 -m automation.report --send
```

## TikTok API (neu)

TikTok ist als eigenes CLI-Modul integriert:

```bash
python3 -m automation.tiktok --help
```

Account/App-Setup:
- `automation/TIKTOK_SETUP.md`

Live-Session (generiert direkt PKCE + OAuth-URL + optional API-Checks):

```bash
automation/scripts/run_tiktok_live.sh
```

1) PKCE + OAuth URL erzeugen:

```bash
export TIKTOK_CLIENT_KEY="..."
export TIKTOK_REDIRECT_URI="https://your-app.example/callback"
python3 -m automation.tiktok pkce
# code_challenge + code_verifier in Env setzen
python3 -m automation.tiktok auth-url
```

2) Authorization Code gegen Access/Refresh Token tauschen:

```bash
export TIKTOK_CLIENT_SECRET="..."
python3 -m automation.tiktok exchange-code --code "<CODE_FROM_CALLBACK>"
```

3) Basis-Checks:

```bash
export TIKTOK_ACCESS_TOKEN="..."
python3 -m automation.tiktok user-info
python3 -m automation.tiktok creator-info
python3 -m automation.tiktok video-list --max-count 10
```

4) Access Token refreshen:

```bash
export TIKTOK_REFRESH_TOKEN="..."
python3 -m automation.tiktok refresh-token
```

5) Posting-Flow (Datei):

```bash
# Init + Binary Upload (inbox)
python3 -m automation.tiktok inbox-init-file --file ./video.mp4 --upload

# Init + Binary Upload (direct post)
python3 -m automation.tiktok direct-init-file --file ./video.mp4 --title "Mein Titel" --upload
```

6) Posting-Flow (URL Pull):

```bash
python3 -m automation.tiktok inbox-init-url --video-url "https://example.com/video.mp4"
python3 -m automation.tiktok direct-init-url --title "Mein Titel" --video-url "https://example.com/video.mp4"
```

7) Status fuer `publish_id` abrufen:

```bash
python3 -m automation.tiktok post-status --publish-id "<PUBLISH_ID>"
```

## Free Network (offline, local)

Lokales, kostenloses Setup mit Mic-Button im Browser und Llama via Ollama:

```bash
automation/scripts/run_free_network_live.sh
```

Danach:
- Web UI: `http://127.0.0.1:8765`
- Mic-Input: `Mic Start` im UI
- Backend: `automation/free_network_server.py`

## Jarvis Profile (neu)

Wake-Word gesteuertes Voice-Control fuer Desktop + Handy mit Audio-Doctor und Automation-Routing:

```bash
automation/scripts/run_jarvis_live.sh
```

Dann:
- Desktop: `http://127.0.0.1:8877`
- Handy im selben WLAN: `http://<LAN-IP>:8877`

Audio-Check (DJI-Mic vs Output-Device):

```bash
python3 -m automation.jarvis --profile automation/config/jarvis_profile.json doctor
```

Audio-Profil anwenden (optional, macOS):

```bash
brew install switchaudio-osx
python3 -m automation.jarvis --profile automation/config/jarvis_profile.json audio-apply
```

Details:
- `automation/JARVIS_PROFILE.md`
- Profil: `automation/config/jarvis_profile.json`

## Scheduling (LaunchAgent)

Beispiele liegen in:
- `ai-vault/launchagents/com.ai-empire.notes-ingest.plist`
- `ai-vault/launchagents/com.ai-empire.telegram-report.plist`
- `ai-vault/launchagents/com.ai-empire.daily-content-sprint.plist`

Daily Content Sprint (Host-Fallback ohne Codex-Automations-Host):
- Runtime-Script: `~/Library/Application Support/ai-empire/automation/run_daily_content_sprint.sh`
- Outputs: `~/Library/Application Support/ai-empire/daily_sprints/`

Hinweis: Lege Secrets in `ai-vault/empire.env` (siehe `ai-vault/empire.env.example`).

Laden (macOS, Benutzerkontext):
```bash
launchctl bootstrap gui/$(id -u) ai-vault/launchagents/com.ai-empire.notes-ingest.plist
launchctl bootstrap gui/$(id -u) ai-vault/launchagents/com.ai-empire.telegram-report.plist
```

Stoppen:
```bash
launchctl bootout gui/$(id -u) ai-vault/launchagents/com.ai-empire.notes-ingest.plist
launchctl bootout gui/$(id -u) ai-vault/launchagents/com.ai-empire.telegram-report.plist
```

## Mission Control (neu)

Diese Ebene verbindet drei Dinge:
- parallele Multi-Chat-Runs ueber mehrere KI-Modelle
- Voice-Intake (Audio -> Transkript -> Kommando)
- Revenue-Steuerung mit Monatsziel und 7-Tage-Sprintplan

Konfiguration:
- `automation/config/mission_control.json`
- State-Datei: `ai-vault/mission_control_state.json`

### 1) Status und Umsatz-Steuerung

```bash
# Lagebericht
python3 -m automation.mission_control status

# Umsatz eintragen
python3 -m automation.mission_control revenue-add --amount 1500 --source "Sprint Kunde A" --note "Anzahlung"

# Umsatzliste anzeigen
python3 -m automation.mission_control revenue-list --limit 20
```

### 2) 7-Tage-Sprint aus Ziel ableiten

```bash
# Basierend auf Konfig-Ziel
python3 -m automation.mission_control plan

# Mit eigener Ziel-/Sales-Mathematik
python3 -m automation.mission_control plan \
  --target 10000 \
  --avg-deal 2500 \
  --close-rate 0.2 \
  --meeting-rate 0.3
```

### 3) Viele KI-Chats parallel

```bash
# Dry-run (keine API-Kosten)
python3 -m automation.mission_control multi-chat \
  --prompt "Baue mir 5 Offer-Angles fuer AI Automations." \
  --task-type strategy \
  --agents 9

# Echtlauf ueber Router-Modelle
python3 -m automation.mission_control multi-chat \
  --prompt "Erstelle 10 objection-handler fuer Sales Calls." \
  --task-type strategy \
  --agents 9 \
  --diversify \
  --execute
```

Outputs:
- `automation/runs/parallel_chat_<run_id>.json`
- `automation/runs/parallel_chat_<run_id>.md`

### 4) Sprachsteuerung

Voraussetzungen:
- `OPENAI_API_KEY` gesetzt
- Transcribe-CLI vorhanden (Default: `~/.codex/skills/transcribe/scripts/transcribe_diarize.py`)

```bash
# Nur transkribieren + Intent erkennen
python3 -m automation.mission_control voice --audio path/to/command.m4a

# Intent direkt ausfuehren (standardmaessig dry-run)
python3 -m automation.mission_control voice --audio path/to/command.m4a --dispatch

# Intent ausfuehren mit echten API-Calls
python3 -m automation.mission_control voice --audio path/to/command.m4a --dispatch --execute
```

Voice-Outputs:
- `automation/runs/voice_<run_id>/voice_event.json`
- `automation/runs/voice_<run_id>/*.transcript.txt`

## Stability Layer (neu)

Ziel: OpenClaw dauerhaft stabil halten (Healthchecks, Self-Heal, Snapshots).

### 1) Einmalige Installation

```bash
automation/scripts/install_openclaw_stability.sh
```

Installiert zwei LaunchAgents:
- `com.ai-empire.openclaw-self-heal` (alle 5 Minuten)
- `com.ai-empire.openclaw-snapshot` (stuendlich)

Runtime-Pfad (Launchd-safe):
- `~/Library/Application Support/ai-empire/stability-runtime/`

### 2) Manuelle Checks

```bash
# Health Snapshot erzeugen
automation/scripts/openclaw_healthcheck.sh

# Self-Healing Lauf
automation/scripts/openclaw_self_heal.sh

# Konfig-/State Snapshot
automation/scripts/openclaw_snapshot.sh
```

### 3) Outputs und Logs

- Health Summary: `00_SYSTEM/stability/last_healthcheck.json`
- Self-Heal Report: `00_SYSTEM/stability/last_self_heal.json`
- Health Log: `00_SYSTEM/stability/healthcheck.log`
- Heal Log: `00_SYSTEM/stability/self_heal.log`
- Snapshots: `ai-vault/backups/openclaw/<timestamp>/`

Unter LaunchAgent:
- Health Summary: `~/Library/Application Support/ai-empire/stability-runtime/00_SYSTEM/stability/last_healthcheck.json`
- Self-Heal Report: `~/Library/Application Support/ai-empire/stability-runtime/00_SYSTEM/stability/last_self_heal.json`

### 4) LaunchAgent Betrieb

```bash
# Status
launchctl print gui/$(id -u)/com.ai-empire.openclaw-self-heal
launchctl print gui/$(id -u)/com.ai-empire.openclaw-snapshot

# Stop
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.ai-empire.openclaw-self-heal.plist
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.ai-empire.openclaw-snapshot.plist

# Start
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.ai-empire.openclaw-self-heal.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.ai-empire.openclaw-snapshot.plist
```
