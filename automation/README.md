# Automation Core (Empire)

Dieses Modul liefert einen simplen Router + Content-Workflows auf Basis der bestehenden `content_factory/`-Prompts.

## Quickstart

1) API-Keys setzen (Moonshot + OpenAI empfohlen; OpenRouter optional):

```bash
export MOONSHOT_API_KEY="..."     # Kimi (günstig, stark für Research)
export OPENAI_API_KEY="..."       # ChatGPT/Codex
export GEMINI_API_KEY="..."       # Gemini/Veo Video-Rendering

# Optional fuer YouTube Trend-/Performance-Daten
export YOUTUBE_API_KEY="..."
export YOUTUBE_CHANNEL_ID="..."

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

- `--workflow`: `full | threads | tweets | prompts | monetization | youtube_shorts | shorts_revenue`
- `--execute`: fuehrt echte LLM-Calls aus (sonst Dry-Run)
- `--targets`: z.B. `threads=20,tweets=60,premium_prompts=80`
- `--scale`: skaliert alle Targets (z.B. `0.2`)
- `--niche`, `--style`: ueberschreiben Defaults
- `--creative-mode`: Kreativprofil fuer X-Posts (z.B. `comedy_ai_cartoons_dark_humor_comic`)
- `--workflow youtube_shorts`: baut Shorts-Drafts + Feedback-Plan
- `--youtube-channel-id`, `--youtube-region`, `--youtube-language`
- `--youtube-lookback-hours`, `--youtube-drafts`, `--youtube-min-vph`
- `--youtube-queries`: komma-separierte Such-Queries
- `--revenue-target-eur`, `--average-order-value`
- `--profile-click-rate`, `--landing-conversion-rate`
- `--video-provider`: `sora|local`
- `--video-duration-seconds`, `--video-max-renders`
- `--sora-video-enabled`: `true|false`
- `--sora-model`, `--sora-size`
- `--sora-poll-interval-seconds`, `--sora-timeout-seconds`, `--sora-cli-path`

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

## YouTube Shorts Autopilot (neu)

Kostenarm via lokalem Router (`automation/config/router_local.json` als Default fuer `youtube_shorts`):

```bash
# Dry-Run: generiert Trends, Drafts, Publish Queue, Feedback-Plan
python3 -m automation run --workflow youtube_shorts

# Live-Run (lokales Modell + optionale YouTube API Abfragen)
python3 -m automation run --workflow youtube_shorts --execute
```

Outputs:
- `content_factory/deliverables/youtube_shorts/<run_id>/trends.json`
- `content_factory/deliverables/youtube_shorts/<run_id>/drafts.json`
- `content_factory/deliverables/youtube_shorts/<run_id>/video_renders.json`
- `content_factory/deliverables/youtube_shorts/<run_id>/videos/*.mp4`
- `content_factory/deliverables/youtube_shorts/<run_id>/publish_queue.csv`
- `content_factory/deliverables/youtube_shorts/<run_id>/metrics.json`
- `content_factory/deliverables/youtube_shorts/<run_id>/feedback_plan.md`
- `content_factory/deliverables/youtube_shorts/latest.json`

10h Dauerlauf (ohne Nachfragen):

```bash
# 10 Stunden, alle 30 Minuten, standardmaessig Dry-Run
automation/scripts/run_youtube_autopilot.sh 10 30

# Mit echten LLM-Aufrufen
EXECUTE_MODE=1 automation/scripts/run_youtube_autopilot.sh 10 30

# Live-Auto-Publish aktivieren (direkt nach jedem erfolgreichen Run)
AUTO_PUBLISH_YOUTUBE=1 AUTO_PUBLISH_MODE=public EXECUTE_MODE=1 automation/scripts/run_youtube_autopilot.sh 10 30
```

Thermal-/Load-Schutz (empfohlen fuer lange Laeufe):

- Vor jedem Zyklus prueft `automation/scripts/system_safety_guard.sh` automatisch:
  - CPU load/core
  - `pmset` CPU speed limit (Thermal Throttling)
  - freien Memory-Anteil
- Bei Ueberlast wird der Run sauber uebersprungen und Cooldown erzwungen.
- Steuerung via ENV:
  - `SAFETY_GUARD=1`
  - `SAFETY_COOLDOWN_MIN=20`
  - `AUTOPILOT_NICE=10`

## Shorts Revenue Engine (YouTube + TikTok parallel)

```bash
# Dry-Run
python3 -m automation run --workflow shorts_revenue

# Live-Run (lokales Modell, APIs wenn verfuegbar)
python3 -m automation run --workflow shorts_revenue --execute
```

Outputs:
- `content_factory/deliverables/shorts_revenue/<run_id>/trends.json`
- `content_factory/deliverables/shorts_revenue/<run_id>/drafts.json`
- `content_factory/deliverables/shorts_revenue/<run_id>/video_renders.json`
- `content_factory/deliverables/shorts_revenue/<run_id>/videos/*.mp4`
- `content_factory/deliverables/shorts_revenue/<run_id>/youtube_publish_queue.csv`
- `content_factory/deliverables/shorts_revenue/<run_id>/tiktok_publish_queue.csv`
- `content_factory/deliverables/shorts_revenue/<run_id>/youtube_metrics.json`
- `content_factory/deliverables/shorts_revenue/<run_id>/tiktok_metrics.json`
- `content_factory/deliverables/shorts_revenue/<run_id>/money_model.json`
- `content_factory/deliverables/shorts_revenue/<run_id>/execution_brief.md`

YouTube Studio/API-ready:
- Beide Queue-CSVs enthalten `video_file`, `video_status`, `video_operation`, `video_error`.
- Damit kannst du direkt in YouTube Studio final gegenchecken und via API/Upload-Tool automatisiert publizieren.

Optional Cloud-Sync (Google Drive / iCloud):

```bash
# Run-Artefakte in Cloud spiegeln
automation/scripts/sync_shorts_assets.sh youtube_shorts
automation/scripts/sync_shorts_assets.sh shorts_revenue
```

ENV fuer Sync:
- `GOOGLE_DRIVE_SHORTS_DIR`
- `ICLOUD_SHORTS_DIR`
- `SYNC_SHORTS_ASSETS=1` (aktiviert Auto-Sync nach jedem Autopilot-Run)

Dauerlauf:

```bash
# 10 Stunden, alle 30 Minuten
automation/scripts/run_shorts_revenue_autopilot.sh 10 30

# Mit Live-Auto-Publish
AUTO_PUBLISH_YOUTUBE=1 AUTO_PUBLISH_MODE=public EXECUTE_MODE=1 automation/scripts/run_shorts_revenue_autopilot.sh 10 30
```

Daemon-Steuerung (empfohlen in deinem eigenen Terminal):

```bash
# Starten
automation/scripts/start_shorts_revenue_daemon.sh 10 30

# Status
automation/scripts/status_shorts_revenue_daemon.sh

# Stoppen
automation/scripts/stop_shorts_revenue_daemon.sh
```

Hinweis: Der Daemon uebernimmt `SAFETY_GUARD`, `SAFETY_COOLDOWN_MIN` und `AUTOPILOT_NICE`
automatisch in den Hintergrundprozess.

YouTube Auto-Publish:
- `AUTO_PUBLISH_YOUTUBE=1` aktiviert automatische Uploads aus der Queue.
- `AUTO_PUBLISH_MODE=public|unlisted|private`
- `AUTO_PUBLISH_MAX_PER_RUN=<int>` (Default: 1)
- `AUTO_PUBLISH_MAX_PER_DAY=<int>` (Default: 6)
- `AUTO_PUBLISH_MIN_SPACING_MIN=<int>` (Default: 120)
- Script: `automation/scripts/auto_publish_youtube_queue.sh [shorts_revenue|youtube_shorts]`
- Python CLI: `python3 -m automation.youtube_publish --workflow shorts_revenue --mode public --max-posts 1 --max-posts-per-day 6 --min-spacing-min 120`
- KPI Kill-Switch: Wenn letzte 6 public Uploads schwach sind (`avg_vph < 50` oder `avg_like_rate < 0.02`), wird automatisch 12h auf `unlisted` runtergeschaltet.

Auto-Commit (neu, standardmaessig aktiv im Autopilot):
- `AUTO_COMMIT_ENABLED=1` fuehrt nach jedem Zyklus automatisch einen Git-Commit aus.
- `AUTO_COMMIT_PUSH=1` pusht zusaetzlich automatisch (default `0`).
- `AUTO_COMMIT_PUSH_REMOTE=origin` und optional `AUTO_COMMIT_PUSH_BRANCH=<branch>`.
- `AUTO_COMMIT_MESSAGE_PREFIX` fuer Commit-Prefix.
- Wrapper: `automation/scripts/run_auto_commit.sh <workflow> <run_idx> <run_total>`

Erforderliche ENV fuer Upload:
- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`
- optional `YOUTUBE_ACCESS_TOKEN` (falls bereits vorhanden)


## Notes Ingest

Apple Notes (lokal, macOS):

```bash
python3 -m automation.ingest --source notes --limit 50 --execute
```

Ordner-Intake (z.B. `claude_intake/`):

```bash
python3 -m automation.ingest --source folder --path claude_intake --execute
```

ChatGPT Data Export (ZIP oder bereits entpacktes Verzeichnis):

```bash
# Entpackte Exporte im Standardordner (claude_intake/chat_exports)
python3 -m automation.ingest --source chatgpt_export --execute

# Mit konkretem ZIP
python3 -m automation.ingest --source chatgpt_export --export-zip /pfad/export.zip --execute

# Optional: nur neuere Konversationen und Limit
python3 -m automation.ingest --source chatgpt_export --since-date 2026-01-01 --conversation-limit 200 --execute

# X-Feed Textdump Ingest (rohe X-Suchseite als txt/md)
python3 -m automation.ingest --source x_feed_text --path claude_intake/x_feeds --execute
```

Auto-Discovery Reihenfolge fuer `chatgpt_export`:
1. `--export-zip`
2. `CHATGPT_EXPORT_ZIP` (Env)
3. neueste ZIP in `~/Downloads` (`*chatgpt*export*.zip`, `*conversations*.zip`, `*openai*.zip`)
4. neueste ZIP in `claude_intake/chat_exports`
5. `--export-dir` bzw. Standardordner

Neue Optionen:
- `--source chatgpt_export`
- `--source x_feed_text`
- `--export-zip <path>`
- `--export-dir <path>`
- `--conversation-limit <int>`
- `--since-date YYYY-MM-DD`
- `--skip-merge` (optional, falls Nugget-Merge nicht laufen soll)

Outputs:
- `ai-vault/nuggets/nuggets_<run_id>.json`
- `ai-vault/nuggets/nuggets_<run_id>.md`
- `ai-vault/nuggets/nugget_registry.json`
- `ai-vault/nuggets/nugget_backlog_ranked.md`
- `external/imports/chatgpt_exports/<run_id>/normalized_messages.jsonl`
- `external/imports/chatgpt_exports/<run_id>/manifest.json`
- `external/imports/x_feed_text/<run_id>/x_feed_text_normalized.jsonl`

6h Auto-Ingest fuer Chat-Exporte:

```bash
automation/scripts/run_chat_export_ingest.sh
```

LaunchAgent:
- `ai-vault/launchagents/com.ai-empire.chat-export-ingest.plist`

Hinweis: Beim ersten Apple-Notes-Lauf fragt macOS nach Automation-/Notes-Berechtigungen.

## Thread Handoff / Chronik

Kontextlimit-sicherer Wechsel in neue Threads:

```bash
python3 automation/scripts/write_thread_handoff.py
python3 automation/scripts/write_thread_handoff.py --note "Warum ich diese Prioritaet setze"
```

Outputs:
- `00_SYSTEM/thread_handoffs/handoff_<timestamp>.md`
- `00_SYSTEM/project_chronik.md` (wird automatisch fortgeschrieben)


## Status Report (Telegram)

```bash
# Report lokal schreiben
python3 -m automation.report

# Report + Telegram senden
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
python3 -m automation.report --send
```

Income-Stream Telegram (echte Stripe-Einnahmen + Publish + KPI):

```bash
# einmalig/adhoc
automation/scripts/run_income_stream_report.sh send

# nur lokal schreiben (ohne Telegram)
automation/scripts/run_income_stream_report.sh nosend
```

## n8n Integration (optional, empfohlen)

Das System kann Live-Events als JSON an n8n senden (fail-open):
- `shorts_revenue_run`
- `youtube_shorts_run`
- `youtube_publish_result`
- `stripe_revenue_sync`
- `stripe_webhook_received`
- `income_stream_report`
- `x_trend_scout_run`

ENV:
- `N8N_EVENTS_ENABLED=1`
- `N8N_EVENT_WEBHOOK_URL=https://.../webhook/...`
- `N8N_EVENT_TOKEN=...` (optional Bearer)
- `N8N_EVENT_TIMEOUT_SEC=8`

Hinweis:
- Wenn n8n nicht erreichbar ist, laufen alle Kern-Workflows weiter (kein Hard-Fail).

Stripe Sync CLI:

```bash
python3 -m automation.stripe_sync --lookback-hours 24 --max-records 200
# oder:
automation/scripts/run_stripe_sync.sh 24 200
```

Wichtige ENV:
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PROMPT_VAULT_URL` (optional: wird fuer Produkt-CTA in Shorts genutzt)

Stripe Checkout Session (Live-Link erzeugen):

```bash
python3 -m automation.stripe_checkout \
  --price-id price_xxx \
  --success-url "https://deine-domain/success" \
  --cancel-url "https://deine-domain/cancel" \
  --metadata "product=prompt_vault,channel=youtube_shorts"
```

Stripe Webhook Receiver (lokal):

```bash
python3 -m automation.stripe_webhook_server --host 127.0.0.1 --port 8788
# oder:
automation/scripts/run_stripe_webhook_server.sh
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
- `ai-vault/launchagents/com.ai-empire.chat-export-ingest.plist`
- `ai-vault/launchagents/com.ai-empire.income-stream.plist`
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
