# 🚀 Mission Control - Quick Reference

## Schnellstart

### 1. Command Line
```bash
python3 mission_control_scanner.py
```

### 2. GitHub Control
```
@bot mission-control
```

### 3. Python Integration
```python
from mission_control_scanner import TaskScanner, MissionControl

scanner = TaskScanner()
data = scanner.scan_all()
mc = MissionControl(data)
print(mc.generate_dashboard())
```

## Output-Komponenten

### Dashboard Sections
1. **📊 OVERVIEW** - Total Tasks + Kategorien
2. **🚨 TOP 10 BLOCKERS** - Kritische Blockaden
3. **💎 TOP 10 LEVERS** - High-Impact Tasks
4. **⏰ TIME-CRITICAL** - Deadlines
5. **💰 COST RISKS** - Token/Compute/Docker
6. **📋 TASK TABLE** - 5 Tasks pro Kategorie
7. **⚡ NEXT 90 MIN** - Action List (max 7)

### JSON Export
```json
{
  "scan_time": "ISO-8601",
  "summary": { "total_open": 25, ... },
  "blockers": [...],
  "levers": [...],
  "time_critical": [...],
  "cost_risks": [...],
  "all_tasks": [...]
}
```

## Kategorien

- **BUILD** - Entwicklung, Features, Produkte
- **FIX** - Bugs, Errors, Probleme
- **AUTOMATE** - Workflows, Pipelines
- **CONTENT** - Posts, Copy, Leads
- **STRATEGY** - Planung, Analyse, Research

## Priorität

```
Score = (IMPACT × 5) + (URGENCY × 3) + (EFFORT × -2)
```

**Reihenfolge:** IMPACT > URGENCY > EFFORT

## Gescannte Systeme

✅ OpenClaw (jobs.json)
✅ Git/GitHub (commits, issues)
✅ Docker (compose files)
✅ n8n (workflows)
✅ Atomic Reactor (tasks, reports)
✅ Brain System (orchestrator DB)
✅ CRM (leads, deals)
✅ Logs (errors, warnings)

## Beispiele

### Alle High-Impact Tasks
```python
scanner = TaskScanner()
data = scanner.scan_all()
high_impact = [t for t in data['tasks'] if t['impact'] >= 8]
```

### Tasks nach Kategorie
```python
build_tasks = [t for t in data['tasks'] if t['category'] == 'BUILD']
```

### Export für Knowledge Graph
```python
mc = MissionControl(data)
json_file = mc.export_json()
# Speichere in ChromaDB oder Brain System
```

## Integration Points

### Brain System
```python
# In prefrontal_brain.py
from mission_control_scanner import TaskScanner
data = TaskScanner().scan_all()
top_tasks = data['tasks'][:5]  # Top 5 für Sprint
```

### n8n Workflow
```javascript
const { exec } = require('child_process');
exec('python3 mission_control_scanner.py', (err, stdout) => {
  const data = JSON.parse(stdout);
  return data.stats.total_open;
});
```

### GitHub Actions
```yaml
- name: Mission Control Scan
  run: |
    python3 mission_control_scanner.py > scan_output.txt
    cat scan_output.txt
```

## Häufige Use Cases

### 1. Daily Standup
```bash
python3 mission_control_scanner.py | head -50
# Zeigt Overview + Blockers + Levers
```

### 2. Sprint Planning
```python
data = TaskScanner().scan_all()
top_10 = data['tasks'][:10]
# Plan Sprint mit Top 10 Tasks
```

### 3. Cost Monitoring
```python
data = TaskScanner().scan_all()
costs = data['stats']['cost_risks']
high_risk = [c for c in costs if c['risk'] == 'High']
```

### 4. Blocker Resolution
```python
data = TaskScanner().scan_all()
blockers = data['stats']['blockers']
# Resolve jeden Blocker bevor du Tasks startest
```

## Kommandos

### GitHub Control
```
@bot status              # System Status
@bot mission-control     # Full Mission Control Scan
@bot generate-content    # Content Generation
@bot revenue-report      # Revenue Overview
@bot help               # Alle Commands
```

### Python API
```python
# Scan
scanner.scan_all()

# Dashboard
mc.generate_dashboard()

# Action List
mc.generate_next_90_min()

# Export
mc.export_json(filepath='custom.json')
```

## Best Practices

1. **Regelmäßige Scans** - Alle 4 Stunden oder vor wichtigen Entscheidungen
2. **Blocker First** - Blocker haben absolute Priorität
3. **Next 90 Min** - Fokus auf Action List, von oben nach unten
4. **Cost Monitoring** - Prüfe Cost Risks täglich
5. **JSON Archive** - Speichere Exports für Trend-Analyse

## Troubleshooting

**Problem:** Keine Tasks gefunden
**Lösung:** Prüfe Pfade und Berechtigungen

**Problem:** Falsche Kategorien
**Lösung:** Passe `_infer_category()` an

**Problem:** Langsame Performance
**Lösung:** Limitiere Log-Scans, nutze .gitignore

## Links

- **Full Docs:** [MISSION_CONTROL.md](./MISSION_CONTROL.md)
- **Examples:** [mission_control_examples.py](./mission_control_examples.py)
- **Scanner:** [mission_control_scanner.py](./mission_control_scanner.py)
- **GitHub Control:** [github_control_interface.py](./github_control_interface.py)

---

**Maurice's AI Empire** - Automating everything 🚀
