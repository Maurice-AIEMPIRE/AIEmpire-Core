# Claude Handoff — AI Empire Automation (2026-02-05)

## TL;DR
Apple Notes -> Gold Nuggets Pipeline ist live. Run via:
- `python3 -m automation.ingest --source notes --since-days 30 --limit 200 --execute`
Outputs in `ai-vault/nuggets/`.

## Ziel
Claude soll das System verstehen, bestaetigen, ggf. verbessern und naechste Integrationen (Scheduling + Telegram) bauen.

## Repo
`/Users/maurice/Documents/Dokumente – Mac mini von Maurice/New project`

## Neue/Geaenderte Komponenten

### 1) Automation Router + Workflows
- `automation/` neue Orchestrations-Schicht
- `automation/config/router.json` erweitert: `nugget_extraction: balanced`
- `automation/config/defaults.json` erweitert: `intake_dir: claude_intake`
- `automation/README.md` erweitert (Notes-Ingest + Hinweise)

### 2) Notes -> Nuggets Pipeline
- `automation/ingest.py`: CLI fuer Notes-Ingest (Apple Notes oder Ordner)
- `automation/workflows/notes_ingest.py`: AppleScript Export, HTML->Text, Nugget-Extraktion, Reports
- `automation/prompts/nugget_extractor.md`: Prompt fuer JSON Nuggets
- Outputs:
  - `ai-vault/nuggets/nuggets_<run_id>.json`
  - `ai-vault/nuggets/nuggets_<run_id>.md`
- Run-Logs:
  - `automation/runs/ingest_<run_id>/`

### 3) Content Factory Router
- `automation/cli.py`: main CLI fuer Content Factory (Dry-Run / Execute)
- `automation/core/*`: Router + Provider (OpenAI-Compat)
- `automation/workflows/content_factory.py`: nutzt bestehende `content_factory/prompts/*`

## Commands (Copy/Paste)

### Apple Notes (Live)
```bash
python3 -m automation.ingest --source notes --since-days 30 --limit 200 --execute
```

### Apple Notes (Dry-Run)
```bash
python3 -m automation.ingest --source notes --limit 20
```

### Folder Intake (z.B. claude_intake)
```bash
python3 -m automation.ingest --source folder --path claude_intake --execute
```

### Content Factory (Live)
```bash
python3 -m automation run --workflow full --execute
```

## Wichtige Hinweise
- Beim ersten Notes-Run fragt macOS nach Notes/Automation Permissions.
- API Key via OpenRouter:
  - `OPENROUTER_API_KEY`
  - optional: `OPENROUTER_REFERRER`, `OPENROUTER_TITLE`
- Router ist OpenAI-Compat; OpenRouter Standard, optional OpenAI fallback.

## Output-Orte
- Nuggets JSON/MD: `ai-vault/nuggets/`
- Ingest Run Logs: `automation/runs/ingest_<run_id>/`
- Content Factory Deliverables: `content_factory/deliverables/`

## Offene Next Steps (wenn Claude erweitern soll)
1. LaunchAgent/cron fuer taeglichen Notes-Ingest + Report.
2. Telegram Status Reports (nuggets + costs + runs).
3. Pipeline: Nuggets -> Hook/Thread/Tweet Generator (Content Factory Auto-Trigger).

## Tests
- `python3 -m automation.ingest --source folder --path claude_intake` => "No notes found" (erwartet, nur README/INGESTED)
- `python3 -m automation --help` ok
- `python3 -m automation.ingest --help` ok
