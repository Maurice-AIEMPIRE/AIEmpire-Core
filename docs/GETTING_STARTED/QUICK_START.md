# AIEmpire-Core - Quick Start Guide
**System Repair Complete** - 2026-02-11
**Status:** ✅ Ready for Production
**Memory:** Optimized for 3.8GB RAM

---

## 🚀 Start Here (Right Now!)

### 1. Verify System is Healthy
```bash
PYTHONPATH=. python3 antigravity/system_startup.py
```
**Expected:** ✅ STARTUP SUCCESSFUL (with 3 warnings - that's OK)

**Output shows:**
- ✓ Recovery system ready
- ✓ Resources OK (2.2GB free, max 3 concurrent agents)
- ⚠️ Gemini API unavailable (will use Ollama - that's fine)
- ✓ 4 agents configured and ready
- ✓ State integrity verified

---

### 2. What's New (Top 10 Antigravity Features)
All of these are **already implemented and working:**

1. **Planning Mode** - Never run unplanned code
   - 5-phase workflow: RESEARCH → PLAN → APPROVE → EXECUTE → VERIFY
   - Change classification: [NEW], [MODIFY], [DELETE], [CONFIG]

2. **Cross-Agent Verification** - Quality control
   - Agents verify each other's work
   - No self-review (prevents hallucinations)
   - Consensus scoring

3. **Knowledge Store** - Persistent learning
   - Semantic memory with vector embeddings
   - Automatic deduplication
   - Search across all previous knowledge

4. **Unified Router** - Smart provider selection
   - Tries Gemini first (fast, smart)
   - Falls back to Ollama (local, free)
   - Automatic health checks every 5 minutes

5. **Sync Engine** - Bidirectional synchronization
   - Mac ↔ Gemini Mirror synchronization
   - Merge conflict detection
   - Cross-pollination of ideas

6. **System Guardian** - Prevents crashes
   - Continuous RAM/CPU monitoring
   - Auto-pauses tasks when >85% RAM used
   - Emergency shutdown at >95% RAM

7. **Merge Gate** - Quality assurance
   - Code review gates
   - Tests must pass before merging
   - No bad code reaches main

8. **State Recovery** - Crash-safe checkpoints
   - Atomic writes (crash-proof)
   - Automatic recovery on restart
   - Checksum verification

9. **Resource-Aware Execution** - Adaptive intelligence
   - Chooses models based on available RAM
   - Defers tasks when memory tight
   - Automatically resumes when resources free

10. **System Startup** - Health checks
    - Comprehensive startup verification
    - Graceful degradation
    - 7 health checks in <0.2 seconds

---

## 📊 Resource Status

```
System Memory: 3.8GB total
Available Now: 2.2GB free (56%)
Tier: HEALTHY ✓

Resource Limits:
  ABUNDANT (>75% free):  Use Gemini Pro + 5 agents
  HEALTHY  (50-75%):     Use Gemini Flash + 3 agents
  TIGHT    (25-50%):     Use Ollama + 1 agent
  CRITICAL (<25%):       Pause all, emergency only

Current: 3 agents max, Gemini-Flash recommended
```

---

## 🎯 What to Run

### Option A: Manual Testing (5 minutes)
```bash
# 1. Verify system
PYTHONPATH=. python3 antigravity/system_startup.py

# 2. Check resource status
PYTHONPATH=. python3 -c "from antigravity.resource_aware import get_executor; print(get_executor().get_status())"

# 3. Show recovery status
PYTHONPATH=. python3 -c "from antigravity.state_recovery import check_recovery_status; import json; print(json.dumps(check_recovery_status(), indent=2))"
```

### Option B: Start 1 Agent (Test)
```bash
# Start the Architect agent
PYTHONPATH=. python3 antigravity/agent_runner.py --agent architect --task "Analyze repo structure"
```

### Option C: Full Workflow (Production)
```bash
# Run complete 5-step workflow
PYTHONPATH=. python3 workflow_system/empire.py workflow

# Or new weekly cycle
PYTHONPATH=. python3 workflow_system/empire.py cycle

# Or background daemon
PYTHONPATH=. python3 workflow_system/cowork.py --daemon --focus revenue
```

### Option D: All Agents in Parallel
```bash
# Start 4-model Godmode Programmer
PYTHONPATH=. python3 -m antigravity.swarm_run
```

---

## 🔧 If Something Goes Wrong

### Memory Running Low?
```bash
# System Guardian will automatically pause new tasks
# OR manually check:
PYTHONPATH=. python3 antigravity/system_guardian.py --status
```

### Need to Recover from Crash?
```bash
# System automatically recovers from checkpoints
# Check what's recoverable:
PYTHONPATH=. python3 << 'EOF'
from antigravity.state_recovery import StateCheckpoint
tasks = StateCheckpoint.get_recoverable_tasks()
print(f"Recoverable tasks: {tasks}")
EOF
```

### Gemini API Not Available?
```bash
# Don't worry - system automatically falls back to Ollama
# Verify in startup:
PYTHONPATH=. python3 antigravity/system_startup.py
# Will show: "Gemini API: Unavailable (will use Ollama fallback)"
```

### Want to See Detailed Status?
```bash
# Full comprehensive status
PYTHONPATH=. python3 << 'EOF'
import json
from antigravity.resource_aware import get_executor
from antigravity.state_recovery import check_recovery_status

executor = get_executor()
status = {
    "resources": executor.get_status(),
    "recovery": check_recovery_status(),
}
print(json.dumps(status, indent=2))
EOF
```

---

## 📈 Monitoring (Optional)

### Real-Time Resource Monitoring
```bash
# Continuous monitoring (Ctrl+C to stop)
PYTHONPATH=. python3 antigravity/system_guardian.py --monitor
```

### Per-Agent Monitoring
```bash
# Track individual agent performance
PYTHONPATH=. python3 workflow_system/resource_guard.py
```

---

## ✅ Checklist Before Going to Production

- [ ] Run `system_startup.py` and see ✅ STARTUP SUCCESSFUL
- [ ] Verify all 4 agents show as ready
- [ ] Check that 2GB+ RAM is free
- [ ] Understand the 3 expected warnings (Gemini/Ollama optional)
- [ ] Know how to check recovery status (crashed tasks)
- [ ] Have backup power or stable environment

---

## 🎯 Architecture Overview

```
Your Code/Task
    ↓
Planning Mode (create plan, get approval)
    ↓
Resource-Aware Executor (check if can run now)
    ↓
  ↙ HEALTHY           ↘ TIGHT/CRITICAL
Gemini +              Ollama +
3 agents              1 agent
                      (others deferred)
    ↓
Unified Router (provider failover)
    ↓
Gemini → Ollama → Moonshot
    ↓
Agent (Architect/Fixer/Coder/QA)
    ↓
State Checkpoint (save progress)
    ↓
Cross-Agent Verification (verify work)
    ↓
Knowledge Store (learn & remember)
    ↓
Sync Engine (sync with mirror system)
    ↓
Result ✓
```

---

## 🌟 Key Features You Now Have

✅ **No More Crashes From Overload**
- Memory Guardian prevents exhaustion
- Adaptive concurrency (1-5 agents)
- Automatic recovery if crash does happen

✅ **Smart Task Routing**
- Choose best provider automatically
- Fall back to Ollama if Gemini down
- Health checks every 5 minutes

✅ **Persistent Learning**
- Knowledge survives crashes
- Semantic search across memory
- Task relationships tracked

✅ **Quality Control**
- Planning mode prevents bad changes
- Cross-agent verification
- Merge gates before changes

✅ **Production Ready**
- Comprehensive health checks
- Graceful degradation
- Audit trails and recovery manifests

---

## 🚀 Goal: EUR 100M in 3 Years

**This system is built to:**
1. Never crash (resource-aware + recovery)
2. Verify all changes (cross-check + planning)
3. Learn continuously (knowledge store)
4. Scale intelligently (adaptive resources)
5. Automate everything (agents + workflows)

**Next Steps:**
- Week 1: Lead generation setup (X/Twitter)
- Week 2: Revenue activation (Gumroad/Fiverr)
- Month 2: BMA consulting sales
- Month 3: 100K-agent swarm deployment

---

## 📞 Questions?

**System unstable?**
```bash
PYTHONPATH=. python3 antigravity/system_startup.py
```

**Want detailed logs?**
```bash
cat .startup_report.json
```

**Need recovery?**
```bash
PYTHONPATH=. python3 workflow_system/empire.py status
```

---

## TL;DR

```bash
# Everything in one command:
PYTHONPATH=. python3 antigravity/system_startup.py && \
PYTHONPATH=. python3 workflow_system/empire.py workflow

# Or continuous background mode:
PYTHONPATH=. python3 workflow_system/cowork.py --daemon --focus revenue
```

**Status:** ✅ All systems operational
**Next:** Execute your first workflow!

```
🚀 Let's build EUR 100M! 🚀
```
