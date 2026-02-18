# RUN.md — Quick Reference Commands

## 1. Setup (einmalig auf deinem Mac)

```bash
cd ~/AIEmpire-Core
source .venv/bin/activate
pip install -r requirements.txt
pip install -r empire-api/requirements.txt
```

## 2. Smoke Test (alles OK?)

```bash
python empire_launch.py --smoke-test
```

Erwartet: compileall PASS, ruff PASS, pytest PASS

## 3. System Status

```bash
python empire_launch.py --status
```

## 4. Safari CSS Fix (nach CSS-Aenderungen)

```bash
python scripts/fix_webkit_backdrop.py
```

## 5. Workflow System

```bash
# Voller 5-Step Loop
python workflow-system/orchestrator.py

# Einzelner Step
python workflow-system/orchestrator.py --step audit

# Neuer Wochen-Zyklus
python workflow-system/orchestrator.py --new-cycle

# Empire Control Center
python workflow-system/empire.py status
python workflow-system/empire.py workflow
python workflow-system/empire.py cowork --daemon --focus revenue
python workflow-system/empire.py full
```

## 6. Antigravity Swarm

```bash
# Fix-Modus
python empire_launch.py --swarm "Fix all import errors"

# Full Pipeline
python empire_launch.py --full-pipeline
```

## 7. Legal War Room aktivieren

```bash
# 1. Dokumente in data/inbox/ legen
# 2. Data Pipeline starten (wenn implementiert)
# 3. Legal Run im Claude Code Chat:
#    "Lese .claude/skills/legal-warroom/SKILL.md und fuehre [LEGAL_RUN] aus"
```

## 8. Skills-System nutzen (in Claude Code)

```
# Nucleus (Orchestrator) laden:
"Lese .claude/skills/nucleus/SKILL.md und route folgende Aufgabe: ..."

# Legal Team laden:
"Lese .claude/skills/legal-warroom/SKILL.md und starte die Legal-Analyse"

# Marketing Team laden:
"Lese .claude/skills/marketing-offers/SKILL.md und erstelle ein Angebot"

# Sales Team laden:
"Lese .claude/skills/sales-leadgen/SKILL.md und generiere eine Lead-Liste"
```

## 9. Ruff Lint Check

```bash
ruff check . --select E,F --quiet
```

## 10. Git Workflow

```bash
git status
git add -A
git commit -m "Stabilize & Standardize: packaging + webkit + 100 agent skills"
git push
```
