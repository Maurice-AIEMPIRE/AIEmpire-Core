# Max-Agents Scrum Sprint (24h) - 2026-02-14

## Goal
- 24h Hard Sprint mit 10 parallelen Workern.
- Fokus nur auf Code- und Ops-Blocker in `/Users/maurice/Documents/New project`.
- Produktion/Queues/Assets laufen weiter, Public-Publish bleibt gesperrt bis OAuth sauber verifiziert ist.

## Scope
- In Scope: `automation/`, `00_SYSTEM/`, `content_factory/`, `ai-vault/`.
- Out of Scope: `~/.openclaw/workspace/ai-empire` (nur Referenz).
- Sprint-Artefakt-Owner: Maurice (PO), Command Cell (Scrum Master), Execution Team (Legion/Autopilot/Ops).

## Ceremonies (fixed)
- Sprint Planning: 30 min
- Standups: alle 4h (6 total)
- Sprint Review: letzte 45 min
- Retro: letzte 30 min

## KPI Gate
- Prozess:
  - 100% P0 abgeschlossen
  - >=90% P1 abgeschlossen
- Stabilitaet:
  - <=1 ungeplanter Prozessabbruch je 6h Block
  - keine kritischen Endlosschleifen in Autopilot/Ops-Logs
- Governance:
  - Board aktuell
  - alle Blocker/Entscheidungen mit Zeitstempel dokumentiert

## Backlog
| ID | Priority | Story | Owner | ETA | Status | DoD |
|---|---|---|---|---|---|---|
| P0-01 | P0 | Sprint Board erstellt und als SoT gesetzt | Command Cell | 0.5h | Done | Board enthaelt Goal, Backlog, KPI-Gates, Log, Blocker, Decisions |
| P0-02 | P0 | Security/Identity Hygiene | Command Cell + Maurice | 1h | In Progress | OpenAI-Key rotiert, Auth-Konflikt aufgeloest, keine Klartext-Secrets in Logs/Docs |
| P0-03 | P0 | Worktree Cleanup (stale only) | Ops Lead | 1h | In Progress | Nur stale/verwaiste Worktrees entfernt, aktiver Stand unberuehrt, Liste dokumentiert |
| P0-04 | P0 | YouTube OAuth Unblock vorbereiten | Ops Lead | 2h | In Progress | `youtube_auth.py` Workflow standardisiert, `ai-vault/empire.env` validiert, interner Test bereit |
| P0-05 | P0 | Max-Agents Execution Layer | Automation Unit | 3h | Done | Neue CLI (`run_max_agents_sprint.sh`) mit start/status/pause/resume/finish + Timebox-Rahmen |
| P1-01 | P1 | Ops-Loop Stabilitaet | Reliability | 4h | In Progress | Mindestens ein erfolgreicher Durchlauf aller faelligen Ops-Tasks im Log |
| P1-02 | P1 | Publish Pipeline intern validieren | Publish QA | 4h | In Progress | Deterministischer Queue-Statusfluss, reproduzierbare Publish-Summaries, keine Queue-Korruption |

## Execution Plan (24h)
### Stunde 0-1
- Sprint Planning
- Security-Gates
- Worktree Cleanup (stale only)

### Stunde 1-8
- Build-Block: Legion-Wellen und Code/Ops-Blocker
- Fokus auf P0

### Stunde 8-18
- Ship-Block: Autopilot-Zyklen + interne Publish-Validation + Ops-Stabilisierung

### Stunde 18-23
- KPI-getriebene Repriorisierung, Hardening, Rest-Blocker

### Stunde 23-24
- Review + Retro + naechster Sprint-Backlog

## Command Runbook
```bash
# Start (default policy: internal-only)
automation/scripts/run_max_agents_sprint.sh start --hours 24 --workers 10 --publish internal-only

# Status (Sessions, Keys, Summaries, Logs)
automation/scripts/run_max_agents_sprint.sh status

# Pause / Resume
automation/scripts/run_max_agents_sprint.sh pause
automation/scripts/run_max_agents_sprint.sh resume

# Finish (stops sessions, validates internal publish, writes report, triggers handoff)
automation/scripts/run_max_agents_sprint.sh finish
```

## Tests / Scenarios
- Orchestrierungstest: `multi-chat` mit 10 Agents (`execute=true`) und Ergebnisartefakten.
- Resilience-Test: Safety Guard blockiert -> Degrade Maintenance aktiv -> keine Pipeline-Schaden.
- OAuth/Pipeline-Test: interne Publish-Summary mit `published_count=0` im Internal-Only-Modus.
- Queue-Integritaet: keine doppelten Statusspruenge, Spacing/Daily-Cap stabil.
- Ops-Loop-Test: ingest/income/stripe/handoff laufen nach Intervallen.
- Worktree-Test: stale Cleanup ohne Verlust aktiver Worktrees.

## Execution Log
- 2026-02-14T15:15:00Z - Board initialisiert als Single Source of Truth.
- 2026-02-14T15:16:00Z - Max-Agents Sprint CLI (`run_max_agents_sprint.sh`) implementiert und README erweitert.
- 2026-02-14T15:21:00Z - Starttest mit `--hours 24 --workers 10 --publish internal-only` ausgefuehrt.
- 2026-02-14T15:21:00Z - Start korrekt geblockt wegen laufender Konflikt-Session `ai_empire_ops` (kein doppelter Ops-Loop gestartet).
- 2026-02-14T15:42:47Z - 1h Sprint live gestartet: `start --hours 1 --workers 10 --publish internal-only --force`.
- 2026-02-14T15:42:48Z - Session `max_agents_sprint_legion` (premium: Kimi/DeepSeek/Minimax) aktiv.
- 2026-02-14T15:43:14Z - Zusatz-Session `max_agents_sprint_legion_qwen` (balanced: Qwen-Mix) aktiv.
- 2026-02-14T15:44:44Z - Zusatz-Session `max_agents_sprint_legion_cloud` gestartet (Cloud-Routing fuer Full-Provider-Versuch).

## Blockers
- B-01: YouTube OAuth Credentials unvollstaendig (`auth_ready=false` in letzten Summaries).
- B-02: Security Task benoetigt manuelle Key-Rotation durch Owner.
- B-03: Aktive Session `ai_empire_ops` blockiert Sprint-Start ohne `--force`.
- B-04: `ANTHROPIC_API_KEY`/`ANTHROPIC_AUTH_TOKEN` aktuell nicht gesetzt -> Claude-Provider kann nicht sicher live genutzt werden.

## Decisions
- D-01: Scope auf dieses Repo begrenzt.
- D-02: Worker-Limit fix auf 10.
- D-03: Publish-Policy `internal-only` bis OAuth validiert.
- D-04: Worktree-Policy `stale only`.

## Review
- Noch offen (wird in Sprint-Stunde 23-24 ausgefuellt).

## Retro
- Noch offen (wird in Sprint-Stunde 23-24 ausgefuellt).
