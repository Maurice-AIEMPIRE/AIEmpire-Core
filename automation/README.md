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

## Router anpassen

Modelle und Provider liegen in `automation/config/router.json`.
Die Defaults sind so gesetzt, dass OpenRouter als Standard-Router fungiert.

## Outputs

Outputs landen in:
- `content_factory/deliverables/threads_50.md`
- `content_factory/deliverables/tweets_300.md`
- `content_factory/deliverables/premium_prompts_400.md`
- `content_factory/deliverables/monetization_strategy.md`

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


## Scheduling (LaunchAgent)

Beispiele liegen in:
- `ai-vault/launchagents/com.ai-empire.notes-ingest.plist`
- `ai-vault/launchagents/com.ai-empire.telegram-report.plist`

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
