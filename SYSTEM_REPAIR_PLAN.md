# AIEmpire-Core System Repair Plan
**Status:** CRASH RECOVERY + ANTIGRAVITY FEATURE COMPLETION
**Date:** 2026-02-11
**Target:** 3.8GB RAM System, EUR 100M in 3 Years

---

## Problem Summary
1. **System Crash**: Overloaded (Gemini API + Ollama + Claude processes)
2. **API Issues**: Gemini 400 error (missing GOOGLE_CLOUD_PROJECT)
3. **Missing Features**: Not all Top 10 Antigravity features implemented
4. **Resource Management**: No proper memory protection after crash

---

## Top 10 Antigravity Features (Google Framework)

### ✅ Already Implemented (with fixes needed)
1. **Planning Mode** (antigravity/planning_mode.py)
   - 5-phase workflow: RESEARCH → PLAN → APPROVE → EXECUTE → VERIFY
   - Change classification: [NEW], [MODIFY], [DELETE], [CONFIG]
   - Status: NEEDS HARDENING + error recovery

2. **Cross-Agent Verification** (antigravity/cross_verify.py)
   - "Agents verify each other" principle
   - Fresh context verification
   - Consensus scoring
   - Status: NEEDS TESTING + logging

3. **Knowledge Store** (antigravity/knowledge_store.py)
   - Persistent knowledge items with semantic indexing
   - State snapshots
   - Status: NEEDS PERFORMANCE TUNING

4. **Unified Router** (antigravity/unified_router.py)
   - Gemini → Ollama → Moonshot fallback
   - Provider health checks
   - Task routing by type
   - Status: NEEDS RECOVERY FROM API KEY ISSUES

5. **Sync Engine** (antigravity/sync_engine.py)
   - Bidirectional state synchronization
   - Merge conflict detection
   - Atomic writes
   - Status: NEEDS CRASH RECOVERY MODE

6. **System Guardian** (antigravity/system_guardian.py)
   - RAM/CPU monitoring
   - Auto-kill heavy processes
   - Status: NEEDS PREEMPTIVE THROTTLING

7. **Merge Gate** (antigravity/merge_gate.py)
   - Quality checks before merging
   - Status: WORKING (needs integration)

8. **Godmode Router** (antigravity/godmode_router.py)
   - Distributes to specialized models
   - Status: WORKING (needs testing)

### 🔧 To Be Enhanced/Added
9. **Agent State Persistence**
   - Checkpoint/resume across crashes
   - State recovery mechanism
   - NEW: antigravity/state_recovery.py

10. **Resource-Aware Execution**
   - Per-task resource limits
   - Adaptive model selection based on available RAM
   - NEW: antigravity/resource_aware.py

---

## Step-by-Step Repair Process

### Phase 1: CRITICAL FIXES (Immediate)
- [ ] Fix Gemini API key validation + fallback
- [ ] Enable Ollama fallback for all failed Gemini calls
- [ ] Implement emergency memory cleanup
- [ ] Add crash recovery checkpoint system
- [ ] Restart core services

### Phase 2: FEATURE COMPLETION (Next)
- [ ] Enhance Planning Mode with crash recovery
- [ ] Add State Recovery system
- [ ] Add Resource-Aware Execution
- [ ] Complete Godmode Router testing
- [ ] Integrate all verification gates

### Phase 3: OPTIMIZATION (Then)
- [ ] Profile memory usage per agent
- [ ] Implement token budgets per task
- [ ] Add predictive throttling
- [ ] Configure monitoring alerts
- [ ] Test full end-to-end on 3.8GB machine

### Phase 4: HARDENING (Finally)
- [ ] Automated backup of critical state
- [ ] Multi-level circuit breakers
- [ ] Graceful degradation paths
- [ ] Recovery runbook testing
- [ ] Deploy to production

---

## Resource Constraints
- **System RAM**: 3.8GB (2.2GB available after OS)
- **Ollama Model**: phi:q4 (600MB) max
- **Claude Processes**: Max 2, 450MB each
- **Max Concurrency**: 5 agents
- **Pause Threshold**: >85% RAM

---

## Success Criteria
✓ System starts without crashes
✓ All 4 Godmode agents run concurrently
✓ Gemini API gracefully falls back to Ollama
✓ No memory exhaustion events
✓ Planning → Verify cycle completes in <2 min
✓ State persists across crashes
