# 🧠🧠 DUAL BRAIN ARCHITECTURE — Mac ↔ Gemini Cloud

> **"Zwei digitale Gehirne, die sich gegenseitig verstärken und für deine Vision arbeiten."**

## Vision

Dein lokales Mac-System und Google Gemini Cloud werden **zwei synchronisierte Gehirne**,
die sich gegenseitig verbessern. Jedes Gehirn hat Stärken:

| Eigenschaft | 🖥 Mac Brain (Ollama) | ☁️ Cloud Brain (Gemini) |
|---|---|---|
| **Stärke** | Code-Execution, Git, lokale Files | Reasoning, Kreativität, Wissen |
| **Speed** | Sofort, kein Internet nötig | Schnell, massiv parallel |
| **Kosten** | Gratis, unbegrenzt | Free Tier: 1500 req/Tag |
| **Kontext** | Voller Zugriff auf dein Repo | Bekommt Snapshots + Summaries |
| **Rolle** | EXECUTOR — führt aus | STRATEGIST — denkt, plant, fragt |

## Architektur

```
┌─────────────────────────────────────────────────────────┐
│                    👑 MAURICE (Vision Owner)              │
│                                                          │
│  ╔════════════╗     Daily Questions      ╔════════════╗  │
│  ║ VISION     ║◄═══════════════════════►║ VISION     ║  │
│  ║ JOURNAL    ║     Answers + Goals      ║ JOURNAL    ║  │
│  ╚════════════╝                          ╚════════════╝  │
│        │                                       │         │
│  ┌─────▼──────────┐                ┌──────────▼──────┐  │
│  │  🖥 MAC BRAIN   │◄══ SYNC ══════►│ ☁️ CLOUD BRAIN  │  │
│  │  (Ollama Local) │   Protocol     │ (Gemini API)    │  │
│  │                 │                │                 │  │
│  │ • Code Executor │                │ • Strategy AI   │  │
│  │ • Git Manager   │                │ • Creative AI   │  │
│  │ • File System   │                │ • Research AI   │  │
│  │ • System Guard  │                │ • Vision Miner  │  │
│  │ • Build/Test    │                │ • Question Gen  │  │
│  └────────┬────────┘                └────────┬────────┘  │
│           │                                   │          │
│     ┌─────▼───────────────────────────────────▼─────┐    │
│     │            🔄 SYNC ENGINE                      │    │
│     │  • Knowledge Packets (Mac → Cloud)             │    │
│     │  • Strategy Patches (Cloud → Mac)              │    │
│     │  • Vision Updates (bidirektional)               │    │
│     │  • Daily Digest + Question Queue               │    │
│     └────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

## Kernmodule

### 1. `gemini_bridge.py` — Cloud Brain Verbindung

- Gemini API Client mit Retry + Rate Limiting
- Sendet Knowledge Packets an Cloud Brain
- Empfängt Strategy Patches zurück
- Conversation Memory in JSON

### 2. `vision_engine.py` — Dein digitales Gedächtnis

- Sammelt deine Antworten auf tägliche Fragen
- Baut ein **Vision Profile** auf (was du willst, was du hasst, deine Ziele)
- Erkennt Muster in deinen Entscheidungen
- Generiert personalisierte Empfehlungen

### 3. `sync_engine.py` — Bidirektionaler Sync

- **Knowledge Packets**: Codebase-Snapshots, Git-Diffs, Metrics → Cloud
- **Strategy Patches**: Cloud-Analysen, Verbesserungen → Mac
- **Vision Updates**: Frage-Antwort-Paare, Goal-Changes → beide
- Conflict Resolution bei divergenten Entwicklungen

### 4. `daily_briefing.py` — Tägliches Coaching

- Morgens: 5-10 Fragen um deine aktuelle Vision zu verstehen
- Abends: Summary was beide Brains heute gelernt/gebaut haben
- Wöchentlich: Deep-Dive Vision Review + Strategie-Anpassung

## Datenfluss

```
MORGENS:
  Cloud Brain → generiert Fragen basierend auf Vision Profile
  Maurice → beantwortet Fragen
  Vision Engine → updated Vision Profile
  Sync Engine → sendet Updates an beide Brains

TAGSÜBER:
  Mac Brain → führt Code/Tasks aus, sammelt Learnings
  Cloud Brain → analysiert, findet Patterns, plant Verbesserungen
  Sync Engine → synchronisiert alle 30 min

ABENDS:
  Cloud Brain → generiert Daily Summary + Tomorrow Plan
  Maurice → reviewed + adjusted Priorities
  Sync Engine → konsolidiert alles für morgen
```

## Dateien

```
antigravity/
├── gemini_bridge.py      # Gemini API Client + Memory
├── vision_engine.py      # Vision Mining + Profile
├── sync_engine.py        # Bidirektionaler Sync
├── daily_briefing.py     # Tägliches Coaching System
├── config.py             # Zentrale Konfiguration (✅ EXISTS)
├── unified_router.py     # Multi-Provider Router (✅ EXISTS)
└── _data/
    ├── vision_profile.json    # Dein Vision Profile
    ├── question_history.json  # Alle Fragen + Antworten
    ├── sync_log.json          # Sync History
    └── daily_briefings/       # Tägliche Briefings
```

## Quick Start

```bash
# 1. Gemini API Key setzen
export GEMINI_API_KEY="your-key-from-aistudio.google.com"

# 2. Dual Brain starten
python3 antigravity/daily_briefing.py --morning

# 3. Sync starten (läuft im Hintergrund)
python3 antigravity/sync_engine.py --daemon
```
