# 🚀 LAUNCH MANUAL – Godmode Programmer

> **System:** Claude Code → Ollama Brain → 4 lokale AI-Agents
> **Stand:** 2026-02-10

---

## Architektur

```
┌─────────────────────────────────────────────────────┐
│                   CLAUDE CODE (Commander)             │
│                   (Terminal Interface)                 │
└──────────────────────┬──────────────────────────────┘
                       │
              ┌────────▼────────┐
              │   OLLAMA API     │
              │ localhost:11434  │
              └────────┬────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
   │ARCHITECT│   │  FIXER  │   │  CODER  │
   │14B model│   │14B model│   │ 7B model│
   └─────────┘   └─────────┘   └─────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
              ┌────────▼────────┐
              │   QA/REVIEWER   │
              │ DeepSeek R1 7B  │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │   MERGE GATE    │
              │ compile+lint+test│
              └─────────────────┘
```

---

## Voraussetzungen

| Komponente | Minimum | Empfohlen |
|---|---|---|
| RAM | 16 GB | 32 GB+ |
| Ollama | v0.15+ | aktuell |
| Claude Code | v2.1+ | aktuell |
| Python | 3.12+ | 3.14+ |
| ruff | installiert | aktuell |
| pytest | installiert | aktuell |

---

## Setup (5 Minuten)

### 1. Ollama starten

```bash
ollama serve
```

### 2. Modelle laden (einmalig)

```bash
ollama pull qwen2.5-coder:14b
ollama pull qwen2.5-coder:7b
ollama pull deepseek-r1:7b
ollama pull codellama:7b
```

### 3. Verifizieren

```bash
python3 empire_launch.py --status
```

### 4. Claude Code → Ollama routen

In deinem Terminal, **vor** dem Start von Claude Code:

```bash
export ANTHROPIC_BASE_URL=http://localhost:11434/v1
export ANTHROPIC_MODEL=qwen2.5-coder:14b
```

Oder in `~/.claude/config.json`:

```json
{
  "apiBaseUrl": "http://localhost:11434/v1",
  "model": "qwen2.5-coder:14b"
}
```

---

## Die 10 Master-Commands

| # | Command | Was es tut |
|---|---------|-----------|
| 1 | `python3 empire_launch.py --status` | System-Check: Ollama, Modelle, Reports |
| 2 | `python3 antigravity/collect_reports.py` | Alle Fehler sammeln |
| 3 | `python3 antigravity/cluster_issues.py` | Issues nach Root-Cause clustern |
| 4 | `python3 antigravity/swarm_run.py --models 4 --mode fix-first` | 4-Agent Swarm starten |
| 5 | `python3 empire_launch.py --smoke-test` | Compile + Lint + Test |
| 6 | `ruff check .` | Lint only |
| 7 | `python3 antigravity/pr_bot.py --open 4` | PRs für Agent-Branches |
| 8 | `python3 antigravity/merge_queue.py` | Merge-fähige Branches prüfen |
| 9 | `python3 antigravity/structure_builder.py` | Dashboard bauen |
| 10 | `python3 empire_launch.py --full-pipeline` | Alles auf einmal |

---

## Swarm Modes

| Mode | Reihenfolge | Use-Case |
|---|---|---|
| `fix-first` | Fixer → QA → Architect → Coder | Bugs zuerst fixen |
| `feature-sprint` | Architect → Coder → QA → Fixer | Neue Features bauen |
| `review-all` | QA only | Alles reviewen |
| `full-parallel` | Alle gleichzeitig (32GB+) | Maximum Power |

---

## Hard Rules

1. **Jeder Agent arbeitet in eigener Branch** (`agent/architect/*`, `agent/fixer/*`, ...)
2. **Kein Direkt-Commit auf main**
3. **Merge nur wenn ALL checks pass:**
   - `python3 -m compileall . -q` ✅
   - `ruff check . --select E,F` ✅
   - `pytest -q` ✅
   - No new regressions ✅

---

## Troubleshooting

| Problem | Lösung |
|---|---|
| Ollama antwortet nicht | `ollama serve` starten |
| Model zu langsam | Wechsle auf 7B: `--mode fix-first` |
| RAM voll | Nur 1 Agent gleichzeitig, kein `full-parallel` |
| Merge blocked | Checks fixen bevor merge |
| Claude Code findet Ollama nicht | `ANTHROPIC_BASE_URL` prüfen |
