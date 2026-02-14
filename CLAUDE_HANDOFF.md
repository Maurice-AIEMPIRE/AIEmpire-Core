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

---

## Update 2026-02-14 (AIEmpire-Core Import)
- Vollstruktur aus `/Users/maurice/Downloads/AIEmpire-Core-main.zip` importiert nach:
  - `/Users/maurice/Documents/Dokumente – Mac mini von Maurice/New project/external/imports/AIEmpire-Core-main`
- Import bereinigt:
  - Mac Metadata-Dateien `._*` entfernt (Resource-Fork-Artefakte)
- Import-Umfang:
  - ca. 374 Dateien, 53 Verzeichnisse, ~5.2 MB
- Relevante Kernpfade fuer YouTube/Autopilot:
  - `/Users/maurice/Documents/Dokumente – Mac mini von Maurice/New project/external/imports/AIEmpire-Core-main/revenue_machine/pipeline.py`
  - `/Users/maurice/Documents/Dokumente – Mac mini von Maurice/New project/external/imports/AIEmpire-Core-main/antigravity/unified_router.py`
  - `/Users/maurice/Documents/Dokumente – Mac mini von Maurice/New project/external/imports/AIEmpire-Core-main/.github/workflows`
- Prioritaet bleibt:
  - YouTube Shorts fokussiert, vollautomatische Feedback-Schleife, minimale Zusatzkosten.

---

# 2026-02-14 — YouTube Shorts Autopilot Focus (User Priority)

## Ziel
Vollautomatischer, faceless YouTube Shorts Kanal. Maximale Viralitaet, Reichweite, und Einnahmen. System soll:
- Trends/News scouten
- Skripte generieren
- Videos produzieren und publishen
- Performance messen
- Bei Underperformance automatisch anpassen

## Non-negotiables
- Keine zusaetzlichen Kosten. Bestehende Infrastruktur maximal ausnutzen.
- Vollautomatischer Betrieb; User prueft nur Ergebnisse.
- Keine rassistischen Themen/Angles.

## System Annahmen (aus User Kontext)
- Claude Desktop laeuft staendig.
- Atlas (ChatGPT Browser) soll als "Auge" fuer Trend-Scouting genutzt werden (falls API/Logs vorhanden).
- Bestehende Stack: Ollama (lokal), n8n, Antigravity, GitHub Actions, Atomic Reactor, Knowledge Store, Unified Router.

## Content Machine: High-Level Loop
1. Trend/News Scouting (Atlas/YouTube Trends/Comments).
2. Emotionale Hooks + Script (Hook/Story/CTA).
3. Video Render (Voice, B-Roll, Captions).
4. Upload (YouTube API).
5. Feedback Loop (Retention/CTR/Comments).
6. Autoadaption der Hooks/Topics bei Underperformance.

## KPI/Feedback Heuristiken (initial)
- Retention < 60–70% => Hook zu schwach => Hook-Template aggressiver.
- Views stagnieren => Thema gesaettigt => neues Topic/Angle.
- Engagement-Rate niedrig => CTA/Question anpassen.

## Monetarisierungsziel
Langfristiges Ziel: >= 500 EUR/Tag via YouTube + Ads + ggf. Affiliate/Produkt-Links (spaeter).

## Offene To-Dos (Implementierung)
- Modul: `youtube_sentinel.py` (Atlas-Daten -> Knowledge Store / Strategy).
- Module: Trend Analyzer, Script Generator, Video Creator, Uploader, Performance Tracker.
- Pipeline/Workflow: regelmaessiger Scout + Produce + Upload + Analyze (z.B. GitHub Actions / n8n).

## Update 2026-02-14 (YouTube Shorts Workflow in Automation-Core)
- Neuer Workflow implementiert:
  - `automation/workflows/youtube_shorts.py`
- CLI integriert:
  - `python3 -m automation run --workflow youtube_shorts`
  - neue Flags: `--youtube-channel-id`, `--youtube-region`, `--youtube-language`, `--youtube-lookback-hours`, `--youtube-drafts`, `--youtube-min-vph`, `--youtube-queries`
- Low-cost Standard:
  - `youtube_shorts` nutzt ohne expliziten Override den lokalen Router `automation/config/router_local.json`
- Neue Deliverables:
  - `content_factory/deliverables/youtube_shorts/<run_id>/trends.json`
  - `content_factory/deliverables/youtube_shorts/<run_id>/drafts.json`
  - `content_factory/deliverables/youtube_shorts/<run_id>/publish_queue.csv`
  - `content_factory/deliverables/youtube_shorts/<run_id>/metrics.json`
  - `content_factory/deliverables/youtube_shorts/<run_id>/feedback_plan.md`
  - `content_factory/deliverables/youtube_shorts/latest.json`
- Dauerlauf-Script:
  - `automation/scripts/run_youtube_autopilot.sh`
  - Beispiel: `automation/scripts/run_youtube_autopilot.sh 10 30`

## Update 2026-02-14 (Shorts Revenue Engine)
- Neuer Cross-Platform Workflow:
  - `automation/workflows/shorts_revenue.py`
- Ziel:
  - YouTube + TikTok parallel orchestrieren
  - Content -> Publish Queues -> Metriken -> 24h Revenue-Modell
- Neue CLI:
  - `python3 -m automation run --workflow shorts_revenue`
- Neue Dauerlauf-Automation:
  - `automation/scripts/run_shorts_revenue_autopilot.sh`
  - `automation/scripts/start_shorts_revenue_daemon.sh`
  - `automation/scripts/status_shorts_revenue_daemon.sh`
  - `automation/scripts/stop_shorts_revenue_daemon.sh`
- Neue Outputs:
  - `content_factory/deliverables/shorts_revenue/<run_id>/youtube_publish_queue.csv`
  - `content_factory/deliverables/shorts_revenue/<run_id>/tiktok_publish_queue.csv`
  - `content_factory/deliverables/shorts_revenue/<run_id>/money_model.json`
  - `content_factory/deliverables/shorts_revenue/<run_id>/execution_brief.md`
