# MASTER.md - AI Empire Mastermind

Letzter Scan: 2026-02-05

## 0. Kurzueberblick
- Zweck: Zentraler Wissens- und Befehls-Hub fuer dieses Repo.
- Status: Automatische Kontext-Zusammenfassung erzeugt.
- Hinweis: Einige Inhalte (z.B. SWARM_SUMMARY) sind agent-generierte Zusammenfassungen und sollten vor Entscheidungen verifiziert werden.

## 1. North Star (Arbeitsannahme)
- Aufbau und Betrieb eines agentenbasierten Content- und Operations-Systems.
- Einheitlicher Mastermind-Kanal statt verstreuter Kontexte.

## 2. Command Protocol (so arbeite ich fuer dich)
- Dieser Chat ist der einzige Steuerkanal.
- Wenn du einen Befehl gibst, brauche ich nur: Ziel, Prioritaet, Deadline (optional), Randbedingungen.
- Ich handle standardmaessig proaktiv und dokumentiere Ergebnisse hier und in `MASTER.md`.

Beispiel:
Befehl: "Erstelle 50 Threads zum Thema X"
Ziel: "Konvertierende Threads"
Deadline: "heute 18:00"
Randbedingungen: "Deutsch, kein Emoji, 220-260 Zeichen je Tweet"

## 3. Brain Map (System-Architektur wie ein Gehirn)

### 3.1 Prefrontal Cortex (Strategie & Planung)
- `content_factory/`: 25-Agenten-System fuer Content-Produktion.
- `content_factory/RUNBOOK.md`: Ablaufsteuerung der Agenten.
- `content_factory/TASK_MATRIX.md`: Rollen, Outputs, Wortlimits.

### 3.2 Hippocampus (Langzeitgedaechtnis)
- `SWARM_SUMMARY.md`: Aggregierte Agenten-Auswertung (unverifiziert).
- `ai-vault/snapshots/`: Session-Snapshots.
- `ai-vault/nuggets/`: Extrahierte Gold Nuggets aus Notizen.
- `content_factory/deliverables/`: Fertige Content-Outputs.

### 3.2.1 Sensory Intake (neues Wissen)
- `claude_intake/`: Ablage fuer Claude-Exports und neues Wissen.

### 3.3 Motor Cortex (Ausfuehrung & Tools)
- `agent-dashboard/`: macOS Menu-Bar App (Swift) zum Monitoring/Steuern.
- `agent-dashboard/build.sh`: Build-Skript fuer `AgentMonitor.app`.
- `claude_watch/`: Monitoring fuer Claude Usage Limits (Playwright/API/Countdown).
- `automation/`: Router + Orchestrator fuer Content-Workflows (LLM-Calls + Dry-Run).

### 3.4 Autonomes Nervensystem (Automationen)
- `ai-vault/launchagents/`:
  - `com.ai-empire.autopipeline.plist`
  - `com.ai-empire.agentmonitor.plist`
  - `com.ai-empire.telegram-router.plist`
  - `com.ai-empire.snapshot.plist`
- `ai-vault/launchagents/com.ai-empire.notes-ingest.plist`: taeglicher Notes-Ingest.
- `ai-vault/launchagents/com.ai-empire.telegram-report.plist`: taeglicher Telegram Status Report.
- Status der LaunchAgents ist hier nicht geprueft.

### 3.5 Immunsystem (Risiko- & Systemchecks)
- `system_audit/kimi_army_audit.py`: Scan-Skript.
- `system_audit/KIMI_ARMY_AUDIT_SUMMARY.md`: Audit-Zusammenfassung.

## 4. Agenten-Setup (Content Factory)
- Orchestrator (1): Gesamtziel zerlegen, QA, Review.
- Ideation (10): Hooks, Themen, Angles.
- Writer (8): Drafts fuer Tweets/Threads/Prompts.
- Refiner (4): Kuertzen, schaerfen, Struktur.
- Strategy (2): Monetarisierung (Zielgruppe, Offer, Pricing, Funnel, CTAs).

Workflows:
- `content_factory/workflows/workflow_threads.md`
- `content_factory/workflows/workflow_tweets.md`
- `content_factory/workflows/workflow_premium_prompts.md`
- `content_factory/workflows/workflow_monetization.md`

## 5. Outputs & Exporte
- Haupt-Deliverables:
  - `content_factory/deliverables/threads_50.md`
  - `content_factory/deliverables/tweets_300.md`
  - `content_factory/deliverables/premium_prompts_400.md`
  - `content_factory/deliverables/monetization_strategy.md`
  - `content_factory/deliverables/offer_copy.md`
  - `content_factory/deliverables/pricing_arguments.md`
  - `content_factory/deliverables/dm_scripts.md`
- Exporte (CSV/JSON): `content_factory/deliverables/exports/`
- Backups: `content_factory/deliverables/backup_*/`

## 6. Empire Principles (Napoleon Hill, angewandt)
- Definiteness of Purpose: klares Hauptziel je Zyklus.
- Mastermind Alliance: klare Rollen, gemeinsame Mission.
- Faith + Autosuggestion: taegliche Ziel- und Identitaetsverstaerkung.
- Specialized Knowledge: Wissensluecken gezielt schliessen.
- Imagination: neue Offers/Angles systematisch testen.
- Organized Planning: Runbooks + klare Workflows.
- Decision: schnelle, klare Entschluesse mit Reviewfenster.
- Persistence: definierte Durchhalte-Regeln je Sprint.
- Power of Mastermind: Entscheidungen werden gebuendelt gefaellt.
- Transmutation: Energie in Output und Umsatz lenken.
- Subconscious Mind + Brain: wiederholte Muster fuer Fokus.
- Sixth Sense: Rueckmeldungen aus Daten + Bauchgefuehl abgleichen.

## 7. Energie-Rituale ("Universale Energie" in Praxis)
- Morgens: 5 Minuten Fokus (Ziel + 3 Outcomes des Tages).
- Vor Execution: 60 Sekunden Atemfokus + klares Intent.
- Abends: 3 Learnings + 1 Optimierung fuer morgen.

## 8. Offene Entscheidungen
- Welche NISCHE und welcher STIL sollen in `content_factory/prompts/` gelten?
- Welchen Automations-Rhythmus willst du fuer das Mastermind-Update?

## 9. Budget & Revenue
- `BUDGET_LOG.md`: 50 USD Budget-Tracking.
- `REVENUE_PLAN.md`: Ziel 100 EUR/Tag (Minimum).
- Status 2026-02-05: Remaining budget 50 USD.

## 10. Claude Insights
- Source: `claude_intake/CLAUDE_HANDOFF.md` | Insights: Apple Notes -> Gold Nuggets pipeline live; neue Automation-Router + Content Factory Workflows dokumentiert; Commands + Output-Orte bestaetigt. | Actions: LaunchAgent/cron fuer taeglichen Notes-Ingest + Report aufsetzen; Telegram-Statusreports integrieren; Nuggets -> Hook/Thread/Tweet Auto-Trigger bauen.

## 11. Changelog
- 2026-02-05: Initialer Mastermind-Scan erstellt.
