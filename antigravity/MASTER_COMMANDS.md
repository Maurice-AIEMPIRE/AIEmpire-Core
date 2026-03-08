# 🚀 Master Commands - Godmode Programmer Control Center

## 🎯 Quick Start

```bash
# 1. Verify System
ollama list
python3 antigravity/godmode_router.py

# 2. Run your first task
python3 antigravity/godmode_router.py fix "Analyze import errors"
```

## 📋 Die 10 Master-Commands

### 1. System Status

```bash
# Check Ollama
ollama list

# Check Claude Code
claude --version

# Check running models
ps aux | grep ollama
```

### 2. Single Agent Task

```bash
# Architect (Structure & Design)
python3 antigravity/godmode_router.py architecture "Design a plugin system for agents"

# Fixer (Bug Fixes)
python3 antigravity/godmode_router.py fix "Fix all import errors in antigravity/"

# Coder (Features)
python3 antigravity/godmode_router.py code "Add logging to empire_launch.py"

# QA (Tests & Review)
python3 antigravity/godmode_router.py qa "Review antigravity/core.py for bugs"
```

### 3. Direct Model Access (Bypass Router)

```bash
# Talk directly to models
ollama run qwen2.5-coder:14b "Explain the architecture of this project"
ollama run qwen2.5-coder:7b "Fix this bug: [paste traceback]"
ollama run deepseek-r1:7b "Review this code: [paste code]"
```

### 4. Merge Gate Check

```bash
# Check if branch is ready to merge
python3 antigravity/merge_gate.py agent/fixer/import-fixes

# Auto-merge if checks pass
python3 antigravity/merge_gate.py agent/fixer/import-fixes --auto
```

### 5. Quality Checks (Manual)

```bash
# Compile check
python3 -m compileall -q .

# Lint check
ruff check .

# Tests
pytest -q --tb=short

# All at once
python3 -m compileall -q . && ruff check . && pytest -q
```

### 6. Git Branch Management

```bash
# List agent branches
git branch | grep agent/

# Switch to agent branch
git checkout agent/fixer/task-123

# Merge agent branch
git checkout main
git merge --no-ff agent/fixer/task-123

# Delete merged branch
git branch -d agent/fixer/task-123
```

### 7. Ollama Model Management

```bash
# Pull new model
ollama pull qwen2.5-coder:32b

# Remove model
ollama rm codellama:7b

# Show model info
ollama show qwen2.5-coder:14b

# Stop all models (free RAM)
ollama stop qwen2.5-coder:14b
```

### 8. Performance Monitoring

```bash
# Watch Ollama performance
watch -n 1 'ps aux | grep ollama | head -5'

# Check RAM usage
top -l 1 | grep PhysMem

# Check model speed (tokens/sec)
time ollama run qwen2.5-coder:7b "Write a hello world function"
```

### 9. Batch Processing (Multiple Tasks)

```bash
# Create task list
cat > tasks.txt << EOF
fix|Fix import errors in antigravity/
code|Add error handling to empire_launch.py
qa|Review all Python files for security issues
architecture|Design a better module structure
EOF

# Process all tasks (coming soon)
# python3 antigravity/batch_processor.py tasks.txt
```

### 10. Emergency Reset

```bash
# Kill all Ollama processes
pkill -9 ollama

# Restart Ollama
brew services restart ollama

# Reset to main branch
git checkout main
git reset --hard origin/main

# Clean all agent branches
git branch | grep agent/ | xargs git branch -D
```

## 🎨 Advanced Workflows

### Workflow 1: Fix All Import Errors

```bash
# 1. Route to Fixer
python3 antigravity/godmode_router.py fix "Analyze and fix all import errors"

# 2. Check the branch
git status

# 3. Run quality gate
python3 antigravity/merge_gate.py agent/fixer/cli-fix

# 4. Merge if approved
git checkout main && git merge --no-ff agent/fixer/cli-fix
```

### Workflow 2: Design + Implement + Test

```bash
# 1. Architect designs
python3 antigravity/godmode_router.py architecture "Design a logging system"

# 2. Coder implements
python3 antigravity/godmode_router.py code "Implement the logging system from architect's design"

# 3. QA reviews
python3 antigravity/godmode_router.py qa "Test the new logging system"

# 4. Merge all branches
for branch in $(git branch | grep agent/); do
  python3 antigravity/merge_gate.py $branch --auto
done
```

### Workflow 3: Parallel Swarm (Manual)

```bash
# Open 4 terminals and run simultaneously:

# Terminal 1 - Architect
python3 antigravity/godmode_router.py architecture "Analyze project structure"

# Terminal 2 - Fixer
python3 antigravity/godmode_router.py fix "Fix all linting errors"

# Terminal 3 - Coder
python3 antigravity/godmode_router.py code "Add docstrings to all functions"

# Terminal 4 - QA
python3 antigravity/godmode_router.py qa "Run security audit"
```

## 🔧 Configuration

### Environment Setup (Permanent)

```bash
# Add to ~/.zshrc
cat >> ~/.zshrc << 'EOF'

# Godmode Programmer Setup
export ANTHROPIC_API_KEY="ollama-local"
export ANTHROPIC_BASE_URL="http://localhost:11434/v1"

# Aliases
alias gm-fix='python3 antigravity/godmode_router.py fix'
alias gm-code='python3 antigravity/godmode_router.py code'
alias gm-arch='python3 antigravity/godmode_router.py architecture'
alias gm-qa='python3 antigravity/godmode_router.py qa'
alias gm-gate='python3 antigravity/merge_gate.py'

# Quick model access
alias qwen14='ollama run qwen2.5-coder:14b'
alias qwen7='ollama run qwen2.5-coder:7b'
alias deepr1='ollama run deepseek-r1:7b'

EOF

# Reload
source ~/.zshrc
```

### Now you can use shortcuts

```bash
gm-fix "Fix import errors"
gm-code "Add feature X"
gm-arch "Design system Y"
gm-qa "Review module Z"
gm-gate agent/fixer/task-123 --auto
```

## 📊 Performance Expectations

| Model | Size | Speed | Best For |
|-------|------|-------|----------|
| qwen2.5-coder:14b | 9 GB | ~2-3 tok/s | Architecture, Complex Design |
| qwen2.5-coder:7b | 4.7 GB | ~5-8 tok/s | Coding, Bug Fixes |
| deepseek-r1:7b | 4.7 GB | ~3-5 tok/s | Testing, Reasoning, QA |

**RAM Requirements:**

- 1 model (7b): ~6-8 GB RAM
- 2 models (7b): ~12-16 GB RAM
- 1 model (14b): ~12-16 GB RAM
- Parallel (4 models): ~32+ GB RAM (not recommended on 16GB Mac)

**Recommendation for 16GB Mac:**

- Run 1 model at a time (sequential)
- Use 7b models for speed
- Use 14b only for complex architecture tasks

## 🐛 Troubleshooting

### Model is too slow

```bash
# Switch to smaller model
# Edit antigravity/godmode_router.py and change:
# "architect": model="qwen2.5-coder:7b"  # instead of :14b
```

### Out of memory

```bash
# Stop all models
ollama stop qwen2.5-coder:14b
ollama stop qwen2.5-coder:7b
ollama stop deepseek-r1:7b

# Run only one at a time
```

### Branch conflicts

```bash
# Reset agent branch
git checkout agent/fixer/task-123
git reset --hard main
git checkout main
git branch -D agent/fixer/task-123
```

### Ollama not responding

```bash
# Restart Ollama
brew services restart ollama

# Check if running
curl http://localhost:11434/api/tags
```

## 🎯 Next Steps

1. **Test the system**: Run a simple task with each agent
2. **Set up aliases**: Add shortcuts to ~/.zshrc
3. **Create task queue**: Build a list of issues to fix
4. **Run first swarm**: Execute 4 tasks in parallel (if you have RAM)
5. **Build dashboard**: Create visualization of progress

## 📚 Related Docs

- `CLAUDE_OFFLINE_SETUP.md` - Full setup guide
- `godmode_router.py` - Router implementation
- `merge_gate.py` - Quality gate implementation
- `STRUCTURE_MAP.md` - Project visualization (coming soon)
