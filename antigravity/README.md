# 🤖 Antigravity - Godmode Programmer System

**4 lokale AI-Agenten für parallele Code-Entwicklung**

## 🎯 Was ist das?

Ein vollständig **lokales, offline-fähiges AI-Programmier-System** mit 4 spezialisierten Agenten:

- **Architect** (qwen2.5-coder:14b) - Design, Struktur, Refactoring
- **Fixer** (qwen2.5-coder:7b) - Bugs, Errors, Imports
- **Coder** (qwen2.5-coder:7b) - Features, Implementation
- **QA** (deepseek-r1:7b) - Tests, Review, Security

## ⚡ Quick Start

```bash
# 1. Smoke Test (prüft ob alles funktioniert)
python3 antigravity/smoke_test.py

# 2. Ersten Task ausführen
python3 antigravity/godmode_router.py fix "Analyze import errors"

# 3. Quality Check
python3 antigravity/merge_gate.py agent/fixer/cli-fix
```

## 📚 Dokumentation

| Dokument | Zweck |
|----------|-------|
| **QUICK_START.md** | 5-Minuten Einstieg |
| **LAUNCH_MANUAL.md** | Komplettes Setup & Workflows |
| **MASTER_COMMANDS.md** | Alle Commands im Detail |
| **CLAUDE_OFFLINE_SETUP.md** | Technisches Setup |
| **CLAUDE_OLLAMA_CONFIG.md** | Claude Code Integration (optional) |

## 🚀 Die 4 Master-Commands

```bash
# 1. Architektur & Design
python3 antigravity/godmode_router.py architecture "Design a plugin system"

# 2. Bug Fixes
python3 antigravity/godmode_router.py fix "Fix import errors"

# 3. Feature Implementation
python3 antigravity/godmode_router.py code "Add logging"

# 4. Quality Assurance
python3 antigravity/godmode_router.py qa "Review code for bugs"
```

## 🔧 System-Anforderungen

- **Ollama** v0.15+ (installiert ✓)
- **Python** 3.10+ (installiert ✓)
- **Git** (installiert ✓)
- **RAM**: Minimum 8GB, empfohlen 16GB+
- **Models**:
  - qwen2.5-coder:7b (4.7 GB)
  - qwen2.5-coder:14b (9.0 GB)
  - deepseek-r1:7b (4.7 GB)

## 📊 Performance

| Model | Größe | Speed | RAM | Best For |
|-------|-------|-------|-----|----------|
| qwen2.5-coder:14b | 9 GB | ~2-3 tok/s | ~12 GB | Architecture, Complex Design |
| qwen2.5-coder:7b | 4.7 GB | ~5-8 tok/s | ~6 GB | Coding, Bug Fixes |
| deepseek-r1:7b | 4.7 GB | ~3-5 tok/s | ~6 GB | Testing, Reasoning |

## 🎨 Workflows

### Bug Fix Workflow

```bash
# 1. Fixer findet Bug
python3 antigravity/godmode_router.py fix "Fix import error"

# 2. Quality Check
python3 antigravity/merge_gate.py agent/fixer/cli-fix

# 3. Merge
git checkout main && git merge --no-ff agent/fixer/cli-fix
```

### Feature Workflow

```bash
# 1. Architect designed
python3 antigravity/godmode_router.py architecture "Design logging system"

# 2. Coder implementiert
python3 antigravity/godmode_router.py code "Implement logging from architect's design"

# 3. QA testet
python3 antigravity/godmode_router.py qa "Test new logging system"

# 4. Merge alle
python3 antigravity/merge_gate.py agent/architect/cli-architecture --auto
python3 antigravity/merge_gate.py agent/coder/cli-code --auto
python3 antigravity/merge_gate.py agent/qa/cli-qa --auto
```

## 🔒 Quality Gates

Jeder Agent arbeitet in eigener Branch. Vor dem Merge werden automatisch geprüft:

- ✅ Python Compilation
- ✅ Linting (ruff)
- ✅ Tests (pytest)
- ✅ Merge Conflicts

## 🐛 Troubleshooting

### Ollama läuft nicht

```bash
brew services start ollama
curl http://localhost:11434/api/tags
```

### Model zu langsam

```bash
# Nutze kleineres Model
# Edit godmode_router.py: :14b → :7b
```

### Out of Memory

```bash
# Stoppe Models nach Nutzung
ollama stop qwen2.5-coder:14b
```

## 📁 Dateistruktur

```
antigravity/
├── godmode_router.py          # Router für 4 Agenten
├── merge_gate.py              # Quality Gate System
├── smoke_test.py              # System-Test
├── QUICK_START.md             # 5-Min Quick Start
├── LAUNCH_MANUAL.md           # Komplettes Manual
├── MASTER_COMMANDS.md         # Command Reference
├── CLAUDE_OFFLINE_SETUP.md    # Setup Guide
└── CLAUDE_OLLAMA_CONFIG.md    # Claude Integration
```

## 🎯 Nächste Schritte

1. **Jetzt**: `python3 antigravity/smoke_test.py`
2. **Dann**: Lies `QUICK_START.md`
3. **Danach**: Führe ersten Task aus
4. **Zuletzt**: Baue deine Task-Queue

## 💡 Tipps

### Shortcuts einrichten

```bash
# Füge zu ~/.zshrc hinzu:
alias gm-fix='python3 antigravity/godmode_router.py fix'
alias gm-code='python3 antigravity/godmode_router.py code'
alias gm-arch='python3 antigravity/godmode_router.py architecture'
alias gm-qa='python3 antigravity/godmode_router.py qa'
```

### Direkt mit Models chatten

```bash
ollama run qwen2.5-coder:7b "How do I fix this error?"
ollama run qwen2.5-coder:14b "Design a plugin system"
ollama run deepseek-r1:7b "Review this code"
```

## 🎉 Status

- ✅ Ollama läuft
- ✅ Models installiert
- ✅ Router funktioniert
- ✅ Merge Gate funktioniert
- ✅ QA Agent getestet
- ✅ System ready

**Du kannst loslegen! 🚀**

## 📞 Support

Alle Infos in den Docs:

- Probleme? → `MASTER_COMMANDS.md` → Troubleshooting
- Setup? → `LAUNCH_MANUAL.md`
- Quick Help? → `QUICK_START.md`

---

**Made with 🤖 by Godmode Programmer**
