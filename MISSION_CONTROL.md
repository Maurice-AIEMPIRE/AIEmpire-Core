# 🚀 Mission Control - AI Empire Task Management

## Overview

Mission Control ist ein umfassendes Task-Management-System, das **ALLE** aktiven und offenen Tasks über alle Systeme hinweg erfasst und priorisiert. Es liefert eine **EINSEITIGE** Mission-Control-Übersicht mit klaren Handlungsempfehlungen.

## Features

### 📊 System-Scan
Mission Control scannt automatisch folgende Systeme:

1. **OpenClaw** - Jobs und Konfigurationen (`/openclaw-config/`)
2. **Git/GitHub** - Issues, PRs, und Commits
3. **Docker** - Compose Stacks in `/systems/`, `/atomic-reactor/`, `/openclaw-config/`
4. **n8n** - Workflow-Konfigurationen (`/n8n-workflows/`)
5. **Agent Queues** - Async Task Queues (Redis wenn verfügbar)
6. **Brain System** - Sessions und Events (`/brain-system/`)
7. **Atomic Reactor** - Tasks und Reports (`/atomic-reactor/`)
8. **CRM** - Leads und Deals (`/crm/crm.db`)
9. **Logs** - System-Logs für Errors und Warnings

### 📈 Dashboard-Komponenten

Die Mission Control Übersicht enthält:

1. **TOTAL offene Tasks** - Gesamtzahl aller aktiven Tasks
2. **Top 10 Blocker** - Kritische Blockaden mit klarer Ursache
3. **Top 10 Hebel** - Tasks mit höchstem Impact
4. **Zeitkritische Tasks** - Tasks mit nahenden Deadlines
5. **Kostenrisiken** - Token/Compute/Docker-Kosten

### 📋 Task-Kategorisierung

Alle Tasks werden in **5 Kategorien** geclustert:

- **BUILD** - Neue Features, Produkte, Systeme entwickeln
- **FIX** - Bugs beheben, Probleme lösen
- **AUTOMATE** - Workflows automatisieren, Pipelines erstellen
- **CONTENT** - Content erstellen, Posts schreiben, Leads generieren
- **STRATEGY** - Planung, Analyse, Research, Revenue-Optimierung

Pro Kategorie werden **maximal 5 Tasks** angezeigt (Rest wird zusammengefasst).

### 🎯 Priorisierung

Tasks werden nach folgender Formel priorisiert:

```
Priority Score = (IMPACT × 5) + (URGENCY × 3) + (EFFORT × -2)
```

**Prioritätsordnung:** IMPACT > URGENCY > EFFORT

- **IMPACT (1-10):** Wie groß ist die Auswirkung?
- **URGENCY (1-10):** Wie dringend ist es?
- **EFFORT (1-10):** Wie aufwändig ist es? (niedrig ist besser)

### ⚡ Next 90 Minutes

Das System generiert eine **Action List** mit maximal **7 Punkten**, die in den nächsten 90 Minuten erledigt werden sollten - basierend auf der höchsten Priorität.

### 📄 JSON Export

Alle Details werden in komprimiertes JSON für das Knowledge Graph exportiert mit:
- Vollständige Task-Liste
- Statistiken
- Blocker-Details
- Lever-Details
- Cost Risks
- Time-Critical Items

## Usage

### Command Line

```bash
# Mission Control Scan ausführen
python3 mission_control_scanner.py

# Output:
# - Dashboard auf Console
# - Next 90 Minutes Action List
# - JSON Export: mission_control_YYYYMMDD_HHMMSS.json
```

### GitHub Control Interface

Mission Control ist in das GitHub Control System integriert:

```
@bot mission-control
```

Dieser Command führt einen vollständigen Scan durch und liefert das Dashboard direkt im GitHub Issue/Comment zurück.

### Programmatic Usage

```python
from mission_control_scanner import TaskScanner, MissionControl

# Scan durchführen
scanner = TaskScanner()
scan_data = scanner.scan_all()

# Mission Control Dashboard generieren
mc = MissionControl(scan_data)

# Dashboard ausgeben
print(mc.generate_dashboard())

# Next 90 min Action List
print(mc.generate_next_90_min())

# JSON exportieren
json_file = mc.export_json()
```

## Output Format

### 1. Dashboard (Console/GitHub)

```
================================================================================
🚀 MISSION CONTROL - AI EMPIRE
================================================================================

📊 OVERVIEW
TOTAL OPEN TASKS: 25
By Category:
  BUILD       :   5 tasks
  FIX         :   0 tasks
  AUTOMATE    :  20 tasks
  ...

🚨 TOP 10 BLOCKERS
1. [Source] Task Name
   Reason: Why it's blocked

💎 TOP 10 HIGH-IMPACT LEVERS
1. [Source] Task Name
   Impact: Description

⏰ TIME-CRITICAL TASKS
• Task Name (Deadline: 2026-02-10)

💰 COST RISKS
• [Token] Task Name - Risk: High (50,000 tokens)

📋 TASK OVERVIEW (Max 5 per category)
BUILD:
ID                   Title                    Impact   Urgency
------------------------------------------------------------------------
reactor-T-004        Product Ideas            9/10     6/10
...
```

### 2. Next 90 Minutes Action List

```
⚡ NEXT 90 MINUTES - ACTION LIST
================================================================================
1. [BUILD] Task Title
   Source: AtomicReactor | Impact: 9/10 | Urgency: 6/10
   Estimated Effort: 5/10

2. [AUTOMATE] Workflow Task
   ...

💡 Focus on IMPACT > URGENCY > EFFORT
```

### 3. JSON Export

```json
{
  "scan_time": "2026-02-08T13:56:55.218498",
  "summary": {
    "total_open": 25,
    "by_category": {
      "BUILD": 5,
      "AUTOMATE": 20
    },
    "blockers_count": 0,
    "levers_count": 4,
    "cost_risks_count": 4
  },
  "blockers": [...],
  "levers": [...],
  "time_critical": [...],
  "cost_risks": [...],
  "all_tasks": [...]
}
```

## Integration Points

### 1. Brain System Integration

Mission Control kann vom Prefrontal (CEO) Brain verwendet werden zur Entscheidungsfindung:

```python
# In brain-system/brains/prefrontal_brain.py
from mission_control_scanner import TaskScanner

scanner = TaskScanner()
data = scanner.scan_all()
# Use data for prioritization decisions
```

### 2. Atomic Reactor Integration

Tasks aus dem Atomic Reactor werden automatisch erfasst. Um neue Tasks hinzuzufügen:

```yaml
# atomic-reactor/tasks/T-XXX-task-name.yaml
id: T-XXX
title: Task Name
type: analysis|content|development
priority: high|medium|low
status: pending|running|completed
effort: 1-10
```

### 3. n8n Workflow Integration

Mission Control kann als n8n-Node verwendet werden:

```javascript
// In n8n workflow
const { exec } = require('child_process');

exec('python3 /path/to/mission_control_scanner.py', (error, stdout) => {
  // Process output
  return JSON.parse(stdout);
});
```

### 4. GitHub Actions Integration

Automatischer Scan via GitHub Actions:

```yaml
# .github/workflows/mission-control.yml
name: Mission Control Scan
on:
  schedule:
    - cron: '0 */4 * * *'  # Every 4 hours
  workflow_dispatch:

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Mission Control
        run: python3 mission_control_scanner.py
```

## Configuration

### Task Detection Customization

Passe die Kategorie-Erkennung an in `mission_control_scanner.py`:

```python
def _infer_category(self, text: str) -> str:
    # Add custom keywords for each category
    if "my_custom_keyword" in text.lower():
        return "CUSTOM_CATEGORY"
    # ...
```

### Priority Weight Tuning

Passe die Priorisierungs-Gewichte an:

```python
PRIORITY_WEIGHTS = {
    "IMPACT": 5,    # Higher = more weight on impact
    "URGENCY": 3,   # Higher = more weight on urgency  
    "EFFORT": -2    # Negative = prefer lower effort
}
```

## Best Practices

### 1. Regular Scans
- Führe Mission Control mindestens **alle 4 Stunden** aus
- Bei kritischen Phasen: jede Stunde
- Vor wichtigen Entscheidungen: manuell

### 2. Action List Usage
- Die "Next 90 Minutes" Liste ist dein **sofortiger Fokus**
- Arbeite die Liste **von oben nach unten** ab
- Nach 90 Minuten: neuen Scan durchführen

### 3. Blocker Management
- **Blocker haben absolute Priorität**
- Identifiziere Root Cause sofort
- Löse Blocker bevor du andere Tasks startest

### 4. Cost Risk Monitoring
- Überprüfe Cost Risks täglich
- Tasks mit >50k Tokens erfordern Genehmigung
- Docker Services regelmäßig optimieren

### 5. Knowledge Graph Integration
- Exportiere JSON nach jedem Scan
- Speichere in `/brain-system/knowledge/` oder ChromaDB
- Verwende für Trend-Analyse und Pattern Recognition

## Troubleshooting

### Keine Tasks gefunden

**Problem:** Scanner findet 0 Tasks

**Lösung:**
1. Prüfe ob Pfade korrekt sind
2. Prüfe Berechtigungen für Dateien/Verzeichnisse
3. Stelle sicher dass Tasks im richtigen Format vorliegen

### Falsche Kategorisierung

**Problem:** Tasks landen in falscher Kategorie

**Lösung:**
1. Passe Keywords in `_infer_category()` an
2. Setze explizite `category` in Task-Definitionen
3. Verwende klarere Task-Titel

### Performance Issues

**Problem:** Scan dauert zu lange

**Lösung:**
1. Limitiere Anzahl der gescannten Log-Files
2. Verwende `.gitignore` für große Verzeichnisse
3. Scanne nur veränderte Dateien (Git diff)

## Future Enhancements

- [ ] **Real-time Updates** - WebSocket-basiertes Live-Dashboard
- [ ] **Dependency Tracking** - Task-Dependencies und Blocker-Chains
- [ ] **Predictive Analytics** - ML-basierte Task-Duration-Schätzung
- [ ] **Team Collaboration** - Multi-User Task Assignment
- [ ] **Mobile App** - React Native Dashboard
- [ ] **Voice Commands** - Alexa/Siri Integration
- [ ] **Gantt Charts** - Visuelle Timeline-Darstellung

## Related Systems

- **Brain System** - `/brain-system/` - Orchestrator für alle Brains
- **Atomic Reactor** - `/atomic-reactor/` - Task Execution Engine
- **GitHub Control** - `github_control_interface.py` - Issue-basierte Steuerung
- **n8n Workflows** - `/n8n-workflows/` - Workflow Automation
- **CRM System** - `/crm/` - Lead & Deal Management

## Author

**Maurice Pfeifer** - Elektrotechnikmeister mit 16 Jahren BMA-Expertise
- Building the AI Empire
- Automating everything
- GitHub: @mauricepfeifer-ctrl

## License

Proprietary - Maurice's AI Empire
