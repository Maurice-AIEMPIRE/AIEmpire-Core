# ⚡ QUICK START - Godmode Programmer in 5 Minuten

## ✅ Was du bereits hast

- ✓ Ollama v0.15.4
- ✓ Claude Code v2.1.34
- ✓ qwen2.5-coder:7b (4.7 GB)
- ✓ qwen2.5-coder:14b (9.0 GB)
- ✓ deepseek-r1:7b (4.7 GB)
- ✓ Godmode Router installiert
- ✓ Merge Gate installiert

## 🚀 Sofort loslegen (3 Befehle)

```bash
# 1. Test: Ist Ollama bereit?
ollama list

# 2. Test: Erster Task mit Fixer Agent
python3 antigravity/godmode_router.py fix "Check for import errors"

# 3. Test: Merge Gate
python3 antigravity/merge_gate.py main
```

## 🎯 Die 4 Agenten

| Agent | Model | Rolle | Wann nutzen? |
|-------|-------|-------|--------------|
| **Architect** | qwen2.5-coder:14b | Design, Struktur, APIs | "Design a...", "Refactor...", "Architecture..." |
| **Fixer** | qwen2.5-coder:7b | Bugs, Errors, Imports | "Fix...", "Debug...", "Error..." |
| **Coder** | qwen2.5-coder:7b | Features, Implementation | "Add...", "Implement...", "Create..." |
| **QA** | deepseek-r1:7b | Tests, Review, Lint | "Test...", "Review...", "Check..." |

## 💡 Beispiele (Copy & Paste)

### Beispiel 1: Import-Fehler fixen

```bash
python3 antigravity/godmode_router.py fix "Analyze all import errors in antigravity/ and suggest fixes"
```

### Beispiel 2: Neue Feature implementieren

```bash
python3 antigravity/godmode_router.py code "Add a progress bar to empire_launch.py"
```

### Beispiel 3: Code Review

```bash
python3 antigravity/godmode_router.py qa "Review antigravity/godmode_router.py for bugs and improvements"
```

### Beispiel 4: Architektur-Analyse

```bash
python3 antigravity/godmode_router.py architecture "Analyze the project structure and suggest improvements"
```

## 🔄 Workflow: Von Task bis Merge

```bash
# 1. Task starten
python3 antigravity/godmode_router.py fix "Fix import errors"

# 2. Warten bis fertig (Model arbeitet)
# Output zeigt: "✅ Task completed on branch: agent/fixer/cli-fix"

# 3. Quality Check
python3 antigravity/merge_gate.py agent/fixer/cli-fix

# 4. Wenn approved: Mergen
git checkout main
git merge --no-ff agent/fixer/cli-fix
```

## ⚡ Shortcuts einrichten (Optional)

```bash
# Füge zu ~/.zshrc hinzu:
cat >> ~/.zshrc << 'EOF'

# Godmode Shortcuts
alias gm-fix='python3 antigravity/godmode_router.py fix'
alias gm-code='python3 antigravity/godmode_router.py code'
alias gm-arch='python3 antigravity/godmode_router.py architecture'
alias gm-qa='python3 antigravity/godmode_router.py qa'

EOF

source ~/.zshrc

# Jetzt kannst du nutzen:
gm-fix "Fix import errors"
gm-code "Add logging"
gm-arch "Design plugin system"
gm-qa "Review code"
```

## 🎨 Direkt mit Models chatten (ohne Router)

```bash
# Schneller Bugfix
ollama run qwen2.5-coder:7b "How do I fix this error: ModuleNotFoundError"

# Architektur-Frage
ollama run qwen2.5-coder:14b "What's the best way to structure a multi-agent system?"

# Code Review
ollama run deepseek-r1:7b "Review this code: [paste code]"
```

## 📊 Performance-Tipps

### Wenn zu langsam

```bash
# Nutze kleineres Model für Fixer & Coder
# Edit antigravity/godmode_router.py:
# "fixer": model="qwen2.5-coder:7b"  # Schon so ✓
```

### Wenn RAM knapp (< 16GB)

```bash
# Stoppe Models nach Nutzung
ollama stop qwen2.5-coder:14b
ollama stop qwen2.5-coder:7b
```

### Wenn Model hängt

```bash
# Restart Ollama
brew services restart ollama
```

## 🐛 Häufige Fehler

### "Error: connection refused"

```bash
# Ollama läuft nicht
brew services start ollama

# Warte 5 Sekunden, dann:
ollama list
```

### "Branch already exists"

```bash
# Lösche alte Agent-Branches
git branch -D agent/fixer/cli-fix
```

### "Model not found"

```bash
# Pull das Model
ollama pull qwen2.5-coder:7b
```

## 🎯 Dein erster echter Task

```bash
# 1. Analysiere dein Projekt
python3 antigravity/godmode_router.py architecture "Analyze the AIEmpire-Core structure and list all main components"

# 2. Finde Bugs
python3 antigravity/godmode_router.py qa "Scan for common Python bugs and anti-patterns"

# 3. Fixe Import-Probleme
python3 antigravity/godmode_router.py fix "Fix all import errors and circular dependencies"

# 4. Merge wenn OK
python3 antigravity/merge_gate.py agent/fixer/cli-fix --auto
```

## 📚 Nächste Schritte

1. ✅ **Jetzt**: Führe einen Test-Task aus (siehe oben)
2. 📋 **Dann**: Erstelle eine Task-Liste (alle 209 Issues)
3. 🤖 **Danach**: Lasse die 4 Agenten parallel arbeiten
4. 📊 **Zuletzt**: Baue ein Dashboard für Fortschritt

## 🔗 Weitere Dokumente

- `MASTER_COMMANDS.md` - Alle Commands im Detail
- `CLAUDE_OFFLINE_SETUP.md` - Komplettes Setup
- `godmode_router.py` - Router-Code
- `merge_gate.py` - Quality-Gate-Code

---

## ⚡ TL;DR - Die 3 wichtigsten Befehle

```bash
# 1. Task ausführen
python3 antigravity/godmode_router.py <type> "<task>"

# 2. Quality Check
python3 antigravity/merge_gate.py <branch>

# 3. Direkt mit Model chatten
ollama run qwen2.5-coder:7b "<frage>"
```

**Das war's! Du bist ready. 🚀**
