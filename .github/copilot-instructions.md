# Copilot Instructions for AI Coding Agents

## Architektur & Hauptkomponenten
- **automation/**: Zentrale Steuerung, Workflows, Ingestion, Reports. Enthält CLI-Tools und Konfigs (z.B. `config/router.json`).
- **content_factory/**: Prompt-Pakete, Task-Matrix, Output-Formate, Monetarisierung. Ziel: Content-Erstellung mit 25 spezialisierten Agenten.
- **ai-vault/**: Speicherung von Umgebungsvariablen, LaunchAgents (macOS), Reports, Snapshots.
- **claude_watch/**: Tools zur Überwachung von Claude-Limits (Web, API, Countdown). Enthält eigene Prompts und Templates.
- **external/**: Symlinks/Verweise auf externe Wissensbasen und Output-Pipelines.
- **claude_intake/**: Dropzone für Intake-Files, die automatisiert verarbeitet werden.

## Wichtige Workflows & Befehle
- **Build/Run Content Pipeline:**
  - Dry-Run: `python3 -m automation run --workflow full`
  - Echtlauf: `python3 -m automation run --workflow full --execute`
  - Outputs landen in `content_factory/deliverables/` und Logs in `automation/runs/`
- **Ingestion:**
  - Apple Notes: `python3 -m automation.ingest --source notes --limit 50 --execute`
  - Ordner: `python3 -m automation.ingest --source folder --path claude_intake --execute`
- **Claude-Limit-Monitoring:**
  - Web: `python3 claude_watch/claude_limit_watch.py web --pause-for-login --interval 30`
  - API: `python3 claude_watch/claude_limit_watch.py api --interval 60`
  - Countdown: `python3 claude_watch/claude_limit_watch.py countdown --reset-in 2h32m`

## Konventionen & Besonderheiten
- **Konfigurationsdateien:**
  - Modelle/Provider: `automation/config/router.json`
  - Workflows: `automation/config/mission_control.json`
- **Backups:**
  - Outputs werden automatisch versioniert (Backups in `content_factory/deliverables/backup_*/`).
- **Stil:**
  - Standard: Direkt, klar, keine Emojis. Anpassbar über Prompt-Parameter.
- **Externe Integration:**
  - Output-Export nach `external/ai-empire/04_OUTPUT/content_pipeline/drafts/` für Scheduler.

## Beispiele & Referenzen
- Siehe `content_factory/README.md` für Agenten-Setup und Output-Formate.
- Siehe `automation/README.md` für alle CLI-Workflows und Parameter.
- Siehe `claude_watch/README.md` für Limit-Monitoring und Playwright-Setup.
- Siehe `external/README.md` für externe Verlinkungen und Exportpfade.

## Hinweise für AI Agents
- Halte dich an die bestehenden CLI-Workflows und Output-Strukturen.
- Passe Konfigs und Prompts projektbezogen an, statt generisch zu überschreiben.
- Nutze die Backup- und Logging-Mechanismen für Nachvollziehbarkeit.
- Beachte macOS-spezifische Automatisierungen (LaunchAgents, Notifications).
