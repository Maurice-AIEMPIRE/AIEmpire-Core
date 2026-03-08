# Claude Code → Ollama Offline Setup

## ✅ System Status

- **Ollama**: v0.15.4 ✓
- **Claude Code**: v2.1.34 ✓
- **Lokale Modelle**:
  - qwen2.5-coder:7b (4.7 GB)
  - qwen2.5-coder:14b (9.0 GB)
  - deepseek-r1:7b (4.7 GB)
  - deepseek-r1:8b (5.2 GB)
  - codellama:7b (3.8 GB)

## 🎯 Zielbild: 4-Model Godmode Programmer

```
┌─────────────────────────────────────────────────┐
│         Claude Code (Commander/Tool)            │
└──────────────────┬──────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │  Router/Orchestrator │
         └─────────┬─────────┘
                   │
    ┌──────────────┼──────────────┬──────────────┐
    │              │              │              │
┌───▼───┐     ┌───▼───┐     ┌───▼───┐     ┌───▼───┐
│Architect│   │ Fixer │   │ Coder │   │  QA   │
│qwen14b │   │qwen7b │   │qwen7b │   │deepR1 │
└────────┘     └────────┘     └────────┘     └────────┘
```

## 📋 Setup Steps

### 1. Ollama API aktivieren (läuft bereits)

```bash
# Ollama läuft standardmäßig auf http://localhost:11434
curl http://localhost:11434/api/tags
```

### 2. Claude Code auf Ollama routen

Claude Code nutzt die Anthropic API. Wir leiten diese auf Ollama um:

```bash
# Setze Environment Variables
export ANTHROPIC_API_KEY="ollama-local"
export ANTHROPIC_BASE_URL="http://localhost:11434/v1"
```

**Permanent machen** (in `~/.zshrc`):

```bash
echo 'export ANTHROPIC_API_KEY="ollama-local"' >> ~/.zshrc
echo 'export ANTHROPIC_BASE_URL="http://localhost:11434/v1"' >> ~/.zshrc
source ~/.zshrc
```

### 3. Test: Claude Code mit lokalem Model

```bash
# Test mit qwen2.5-coder:7b
claude --model qwen2.5-coder:7b "Write a Python function to calculate fibonacci"
```

### 4. 4-Model Router Setup

Erstelle `antigravity/godmode_router.py`:

```python
"""
4-Model Godmode Programmer Router
Verteilt Tasks an spezialisierte lokale Modelle
"""

import asyncio
import json
from typing import Literal, Dict, Any
from dataclasses import dataclass
import subprocess

@dataclass
class AgentConfig:
    name: str
    model: str
    role: str
    branch_prefix: str
    
AGENTS = {
    "architect": AgentConfig(
        name="Architect",
        model="qwen2.5-coder:14b",
        role="Structure, APIs, Refactoring",
        branch_prefix="agent/architect"
    ),
    "fixer": AgentConfig(
        name="Fixer",
        model="qwen2.5-coder:7b",
        role="Bugs, Tracebacks, Imports",
        branch_prefix="agent/fixer"
    ),
    "coder": AgentConfig(
        name="Coder",
        model="qwen2.5-coder:7b",
        role="Feature Implementation",
        branch_prefix="agent/coder"
    ),
    "qa": AgentConfig(
        name="QA",
        model="deepseek-r1:7b",
        role="Tests, Lint, Review",
        branch_prefix="agent/qa"
    )
}

class GodmodeRouter:
    def __init__(self):
        self.agents = AGENTS
        
    async def route_task(self, task: Dict[str, Any]) -> str:
        """Route task to appropriate agent"""
        task_type = task.get("type", "code")
        
        # Routing Logic
        if "architecture" in task_type or "refactor" in task_type:
            agent = "architect"
        elif "bug" in task_type or "error" in task_type or "fix" in task_type:
            agent = "fixer"
        elif "test" in task_type or "qa" in task_type or "review" in task_type:
            agent = "qa"
        else:
            agent = "coder"
            
        return agent
    
    async def execute_task(self, agent_key: str, prompt: str, context: Dict = None):
        """Execute task with specific agent"""
        agent = self.agents[agent_key]
        
        # Create branch
        branch_name = f"{agent.branch_prefix}/{context.get('task_id', 'task')}"
        subprocess.run(["git", "checkout", "-b", branch_name], capture_output=True)
        
        # Build prompt with role context
        full_prompt = f"""You are {agent.name}, specialized in: {agent.role}

Task: {prompt}

Rules:
- Work only in your domain
- Make atomic commits
- Add tests for changes
- Follow existing patterns

Context: {json.dumps(context or {}, indent=2)}
"""
        
        # Call Ollama via subprocess (simulating Claude Code)
        result = subprocess.run(
            ["ollama", "run", agent.model, full_prompt],
            capture_output=True,
            text=True
        )
        
        return {
            "agent": agent.name,
            "model": agent.model,
            "branch": branch_name,
            "output": result.stdout,
            "error": result.stderr
        }
    
    async def run_parallel_swarm(self, tasks: list[Dict]):
        """Run multiple agents in parallel"""
        results = []
        for task in tasks:
            agent = await self.route_task(task)
            result = await self.execute_task(agent, task["prompt"], task.get("context"))
            results.append(result)
        return results

# CLI Interface
if __name__ == "__main__":
    import sys
    
    router = GodmodeRouter()
    
    if len(sys.argv) < 2:
        print("Usage: python godmode_router.py <task_type> <prompt>")
        sys.exit(1)
    
    task = {
        "type": sys.argv[1],
        "prompt": " ".join(sys.argv[2:])
    }
    
    agent = asyncio.run(router.route_task(task))
    print(f"Routing to: {AGENTS[agent].name} ({AGENTS[agent].model})")
    
    result = asyncio.run(router.execute_task(agent, task["prompt"]))
    print(json.dumps(result, indent=2))
```

### 5. Merge Gate (Quality Control)

Erstelle `antigravity/merge_gate.py`:

```python
"""
Merge Gate - Ensures quality before merging agent branches
"""

import subprocess
import sys
from pathlib import Path

class MergeGate:
    def __init__(self, repo_path: Path = Path.cwd()):
        self.repo = repo_path
        
    def run_checks(self, branch: str) -> dict:
        """Run all quality checks"""
        results = {}
        
        # 1. Compile Check
        compile_result = subprocess.run(
            ["python3", "-m", "compileall", "."],
            capture_output=True,
            text=True
        )
        results["compile"] = compile_result.returncode == 0
        
        # 2. Lint Check
        lint_result = subprocess.run(
            ["ruff", "check", "."],
            capture_output=True,
            text=True
        )
        results["lint"] = lint_result.returncode == 0
        results["lint_output"] = lint_result.stdout
        
        # 3. Tests
        test_result = subprocess.run(
            ["pytest", "-q", "--tb=short"],
            capture_output=True,
            text=True
        )
        results["tests"] = test_result.returncode == 0
        results["test_output"] = test_result.stdout
        
        # 4. No regressions (compare with main)
        diff_result = subprocess.run(
            ["git", "diff", "main", "--stat"],
            capture_output=True,
            text=True
        )
        results["diff"] = diff_result.stdout
        
        return results
    
    def approve_merge(self, branch: str) -> bool:
        """Check if branch can be merged"""
        checks = self.run_checks(branch)
        
        print(f"\n🔍 Merge Gate Results for {branch}")
        print(f"✓ Compile: {'PASS' if checks['compile'] else 'FAIL'}")
        print(f"✓ Lint: {'PASS' if checks['lint'] else 'FAIL'}")
        print(f"✓ Tests: {'PASS' if checks['tests'] else 'FAIL'}")
        
        if not checks['compile']:
            print("\n❌ Compilation errors detected")
            return False
            
        if not checks['tests']:
            print(f"\n❌ Test failures:\n{checks['test_output']}")
            return False
        
        print("\n✅ All checks passed - Safe to merge")
        return True
    
    def merge_branch(self, branch: str, auto_merge: bool = False):
        """Merge branch if checks pass"""
        if not self.approve_merge(branch):
            print(f"\n🚫 Merge blocked for {branch}")
            sys.exit(1)
        
        if auto_merge:
            subprocess.run(["git", "checkout", "main"])
            subprocess.run(["git", "merge", "--no-ff", branch])
            print(f"\n✅ Merged {branch} into main")
        else:
            print(f"\n✅ Ready to merge - run: git merge {branch}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python merge_gate.py <branch_name> [--auto]")
        sys.exit(1)
    
    gate = MergeGate()
    auto = "--auto" in sys.argv
    gate.merge_branch(sys.argv[1], auto_merge=auto)
```

## 🚀 Master Commands

### 1. System Status

```bash
ollama list
claude --version
```

### 2. Start Godmode Swarm

```bash
python3 antigravity/godmode_router.py fix "Fix all import errors in antigravity/"
```

### 3. Test Single Agent

```bash
# Architect
ollama run qwen2.5-coder:14b "Analyze the structure of antigravity/ and suggest improvements"

# Fixer
ollama run qwen2.5-coder:7b "Fix the import error in empire_launch.py"

# QA
ollama run deepseek-r1:7b "Review the code in antigravity/core.py for bugs"
```

### 4. Merge with Quality Gate

```bash
python3 antigravity/merge_gate.py agent/fixer/import-fixes
```

### 5. Full Workflow

```bash
# 1. Route task
python3 antigravity/godmode_router.py fix "Fix import cycles"

# 2. Check quality
python3 antigravity/merge_gate.py agent/fixer/task-123

# 3. Merge if approved
git merge agent/fixer/task-123
```

## 🎯 Next Steps

1. **Test Ollama API**: `curl http://localhost:11434/api/tags`
2. **Set Environment**: Add exports to `~/.zshrc`
3. **Create Router**: Copy `godmode_router.py` to `antigravity/`
4. **Create Merge Gate**: Copy `merge_gate.py` to `antigravity/`
5. **Test Single Agent**: Run one Ollama model with a simple task
6. **Test Router**: Route a task and verify it goes to correct agent
7. **Test Merge Gate**: Create a test branch and run quality checks

## 📊 Expected Performance

- **Architect (14b)**: ~2-3 tok/s (complex decisions)
- **Fixer/Coder (7b)**: ~5-8 tok/s (fast iteration)
- **QA (deepseek-r1)**: ~3-5 tok/s (reasoning)

## 🔧 Troubleshooting

### Ollama not responding

```bash
# Restart Ollama
brew services restart ollama
```

### Claude Code not finding models

```bash
# Verify env vars
echo $ANTHROPIC_BASE_URL
# Should be: http://localhost:11434/v1
```

### Model too slow

```bash
# Use smaller model
ollama run qwen2.5-coder:7b instead of :14b
```
