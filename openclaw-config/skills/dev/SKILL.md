# SKILL: Dev / AI Engineering
*Lade diesen Skill wenn: Code, Python, OpenClaw, Skill, Script, Bug, API, Automation, Build, Fix*

---

## Tech-Stack (Priorität)

### Sprachen:
- **Python 3** — Hauptsprache (asyncio, aiohttp für I/O)
- **JavaScript/Node.js** — CRM (Express.js)
- **YAML** — Atomic Reactor Task Definitions
- **Markdown** — Skills, Docs, Memory

### Infrastruktur:
- Redis — Cache + Message Queue
- PostgreSQL — Persistente Daten
- ChromaDB — Vektorsuche
- Docker Compose — Service Orchestration
- FastAPI (Port 8888) — Atomic Reactor

### AI-Stack:
- Ollama (lokal, 95%) — Standard für alles
- Kimi K2.5 (API, 4%) — Komplex, Long-Context
- Claude Opus 4.6 (API, 1%) — Kritisch, Strategisch
- OpenClaw (Port 18789) — Agent-Orchestration

---

## Coding-Standards (STRIKT)

### API Calls:
```python
# RICHTIG — immer durch Router
from antigravity.empire_bridge import get_bridge
bridge = get_bridge()
result = await bridge.execute("deine anfrage")

# FALSCH — niemals direkte API calls
import anthropic
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

### Config:
```python
# RICHTIG
from antigravity.config import config
api_key = config.anthropic_api_key

# FALSCH — niemals direkt
import os
api_key = os.getenv("ANTHROPIC_API_KEY")
```

### File Writes:
```python
# RICHTIG — atomic write via sync_engine
from antigravity.sync_engine import atomic_write
atomic_write("output.json", data)

# FALSCH — direkte open() für kritische Daten
with open("output.json", "w") as f:
    json.dump(data, f)
```

### Async Pattern:
```python
async def main():
    async with aiohttp.ClientSession() as session:
        result = await fetch_data(session, url)
    return result
```

---

## Systemarchitektur-Überblick

```
empire_engine.py          ← Einstiegspunkt (NIEMALS direkt API calls)
    ↓
antigravity/empire_bridge.py  ← Alle AI-Calls hier durch
    ↓
antigravity/unified_router.py ← Ollama → Kimi → Claude Routing
    ↓
antigravity/cross_verify.py  ← Kritische Outputs gegenseitig prüfen
```

### Ports (FEST, nicht ändern):
- 18789 — OpenClaw Agent
- 8888 — Atomic Reactor (FastAPI)
- 3500 — CRM (Express.js)
- 6379 — Redis
- 5432 — PostgreSQL
- 11434 — Ollama

---

## Skill erstellen (OpenClaw)

Neuen Skill anlegen:
```bash
mkdir openclaw-config/skills/neuer-skill
touch openclaw-config/skills/neuer-skill/SKILL.md
```

SKILL.md Struktur:
```markdown
# SKILL: Name
*Trigger: wann wird dieser Skill geladen?*

## Was der Skill tut
## Regeln / Vorgaben
## Tools & Verbindungen
```

Dann sagen: "install the [name] skill" oder manuell in SKILLS_INDEX.md eintragen.

---

## Debugging-Workflow

1. **Fehler aufgetreten?** → `python3 scripts/auto_repair.py`
2. **Port-Konflikt?** → `lsof -i :PORT` dann `kill PID`
3. **Ollama offline?** → `ollama serve` (braucht separates Terminal)
4. **Redis weg?** → `redis-server --daemonize yes`
5. **Crash nach Reboot?** → `./scripts/bombproof_startup.sh`

### Knowledge Store für Fixes:
```python
from antigravity.knowledge_store import KnowledgeStore
ks = KnowledgeStore()
ks.add("fix", "kurzbeschreibung",
       content="was hat funktioniert",
       tags=["bugfix", "component-name"])
```

---

## Code-Review-Checkliste

Vor jedem Commit:
- [ ] Keine hardcoded API Keys
- [ ] Config über `antigravity/config.py`
- [ ] Alle AI-Calls über empire_bridge
- [ ] Atomare Writes für State-Dateien
- [ ] Cost Tracking auf jedem API Call
- [ ] Keine synchronen I/O-Blöcker in async Kontext
- [ ] Error Handling für externe Services

---

## Atomic Reactor Tasks (YAML)

```yaml
# atomic_reactor/tasks/beispiel.yaml
name: content-generate
description: Generiert Content für X
steps:
  - action: ai_call
    prompt: "Generiere 3 Tweets über AI Automation"
    model: ollama
  - action: write_file
    path: x_lead_machine/queue.md
```
