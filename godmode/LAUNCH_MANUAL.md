# GODMODE PROGRAMMER — Launch Manual

> **Dein Setup:** Apple M4, 16GB RAM, Ollama ready, 7 Modelle gepullt.
> **Ziel:** Claude Code als Commander, 4 lokale Modelle als Brain.

---

## Quick Start (3 Befehle)

```bash
# 1. Status checken
python3 godmode/router.py --status

# 2. Issues sammeln
python3 godmode/router.py --collect

# 3. Task an Godmode schicken
python3 godmode/router.py "Fix alle ImportError in brain-system/"
```

---

## Architektur

```
┌─────────────────────────────────────────────┐
│              CLAUDE CODE (Commander)         │
│         Du gibst Befehle im Terminal         │
└──────────────────┬──────────────────────────┘
                   │
          godmode/router.py
                   │
     ┌─────────────┼─────────────────┐
     ▼             ▼                 ▼
┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐
│ARCHITECT│ │  FIXER   │ │  CODER   │ │   QA    │
│qwen2.5  │ │deepseek  │ │qwen2.5   │ │codellama│
│  :7b    │ │ -r1:7b   │ │  :14b    │ │  :7b    │
└─────────┘ └──────────┘ └──────────┘ └─────────┘
     │             │           │           │
     └─────────────┴───────────┴───────────┘
                   │
            agent/* Branches
                   │
              Merge Gate
      (compileall + ruff + pytest)
                   │
                 main
```

---

## Die 4 Rollen

| Rolle | Modell | Temp | Aufgabe |
|-------|--------|------|---------|
| **ARCHITECT** | `qwen2.5-coder:7b` | 0.3 | Struktur, Interfaces, API-Design |
| **FIXER** | `deepseek-r1:7b` | 0.1 | Bugs, Tracebacks, Edge-Cases |
| **CODER** | `qwen2.5-coder:14b` | 0.5 | Feature-Implementierung |
| **QA** | `codellama:7b` | 0.1 | Tests, Lint, Code-Review |

---

## 10 Master-Commands

```bash
# 1. System-Status
python3 godmode/router.py --status

# 2. Alle Issues sammeln (compileall + ruff + parse checks)
python3 godmode/router.py --collect

# 3. Task routen (Auto-Klassifizierung)
python3 godmode/router.py "Implementiere einen Health-Check Endpoint"

# 4. Rolle erzwingen
python3 godmode/router.py --role fixer "TypeError in line 45 von orchestrator.py"
python3 godmode/router.py --role architect "Redesign das Plugin-System"
python3 godmode/router.py --role coder "Baue einen REST API Wrapper für Ollama"
python3 godmode/router.py --role qa "Review den letzten Diff auf main"

# 5. Batch-Tasks aus Datei
python3 godmode/router.py --file tasks.txt

# 6. Merge Gate prüfen
python3 godmode/router.py --check

# 7. Branch mergen (nach QA-Pass)
python3 godmode/router.py --merge agent/fixer/fix-imports-0210

# 8. Smoke Test (manuell)
python3 -m compileall . -q && ruff check . --select E,F && python3 -m pytest -q

# 9. Ollama Modell-Status
ollama list && ollama ps

# 10. Logs ansehen
ls -la godmode/logs/
```

---

## RAM-Management (16GB Limit)

**Regel:** Max 2× 7B-Modelle gleichzeitig in Ollama.

```bash
# Welche Modelle sind gerade geladen?
ollama ps

# Modell entladen (RAM freigeben)
curl -s http://localhost:11434/api/generate -d '{"model":"glm-4.7-flash","keep_alive":0}'

# Nur die 4 Godmode-Modelle behalten
# ARCHITECT: qwen2.5-coder:7b (4.7GB)
# FIXER:    deepseek-r1:7b    (4.7GB)
# CODER:    qwen2.5-coder:14b (9.0GB) ← nur solo laden!
# QA:       codellama:7b       (3.8GB)
```

**Empfehlung für 16GB:**

- Nutze überwiegend FIXER + QA (beide 7B, passen zusammen)
- CODER (14B) nur für große Features, dann allein
- ARCHITECT bei Bedarf statt CODER

---

## Merge Gate — Hard Rules

Kein Code kommt auf `main` ohne diese Checks:

1. `python3 -m compileall . -q` — Keine Syntax-Fehler
2. `ruff check . --select E,F,I` — Keine kritischen Lint-Issues
3. `pytest -q` — Tests bestehen

```bash
# Manuell prüfen
python3 godmode/router.py --check

# Automatisch beim Merge
python3 godmode/router.py --merge agent/fixer/my-fix-branch
```

---

## Workflow: Bug fixen (Beispiel)

```bash
# 1. Issue identifizieren
python3 godmode/router.py --collect

# 2. Fixer beauftragen
python3 godmode/router.py --role fixer "ImportError: No module named 'rich' in empire_brain.py"

# 3. Ergebnis prüfen (QA)
python3 godmode/router.py --role qa "Review den Fix in agent/fixer/importerror-empire_brain"

# 4. Merge wenn QA passt
python3 godmode/router.py --merge agent/fixer/importerror-empire_brain-0210
```

---

## Workflow: Neues Feature (Beispiel)

```bash
# 1. Architektur-Entscheidung
python3 godmode/router.py --role architect "Design REST API für den Agent Swarm Output"

# 2. Implementierung
python3 godmode/router.py --role coder "Implementiere die REST API basierend auf Architect-Output"

# 3. Tests + Review
python3 godmode/router.py --role qa "Schreibe Tests für die neue Swarm API"

# 4. Merge
python3 godmode/router.py --check
python3 godmode/router.py --merge agent/coder/swarm-api-0210
```

---

## Claude Code + Ollama (API-Routing)

Claude Code selbst kann auch auf Ollama geroutet werden (für Token-Kosten = 0):

```bash
# In ~/.claude/settings.json oder Environment:
export ANTHROPIC_BASE_URL="http://localhost:11434/v1"
export ANTHROPIC_API_KEY="ollama"  # Ollama braucht keinen echten Key

# Dann läuft Claude Code gegen lokales Modell
# ACHTUNG: Qualität sinkt vs. echtes Claude — nur für einfache Tasks!
```

> **Empfehlung:** Nutze echtes Claude Code für Orchestrierung, lokale Modelle für Execution.
> Claude = Strategie, Ollama = Umsetzung.

---

## Dateien

```
godmode/
├── config.json     # Modell-Zuordnung, Rollen, Merge-Regeln
├── router.py       # Der Haupt-Router (CLI)
├── ISSUES.json     # Gesammelte Issues (nach --collect)
└── logs/           # Task-Logs pro Tag und Rolle
```
