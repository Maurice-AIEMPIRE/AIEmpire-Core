# OpenClaw Optimization Guide — 11 Power Tips
# Adapted for AI Empire by Maurice Pfeifer
# Source: @alexfinn optimization thread

---

## Tip 1: Opus for Brain, Different Models for Every Muscle

**Status: IMPLEMENTED**

Instead of routing everything through one model, we now use **Multi-Muscle Routing**:

| Muscle | Model | Provider | Cost | Best For |
|--------|-------|----------|------|----------|
| Brain | Gemini 2.0 Pro | Cloud | Paid | Planning, architecture, decisions |
| Coding | Qwen 2.5 Coder 14B | Ollama (local) | Free | Implementation, features, fixes |
| Research | Kimi K2.5 | Moonshot | Free | Analysis, trends (256K context) |
| Creative | Gemini 2.0 Flash | Cloud | Cheap | Content, writing, marketing |
| Reasoning | DeepSeek R1 7B | Ollama (local) | Free | Code review, QA, verification |
| Fast | Qwen 2.5 Coder 7B | Ollama (local) | Free | Quick iterations, simple tasks |
| Vibe Code | Code Llama 7B | Ollama (local) | Free | Rapid prototyping |

**Files changed:**
- `openclaw-config/models.json` — Task routing map + muscle tags on each model
- `openclaw-config/litellm_config.yaml` — Muscle-specific fallback chains
- `antigravity/unified_router.py` — Multi-muscle detection + `execute_muscle()` API
- `antigravity/config.py` — Model constants

**Usage:**
```bash
python3 antigravity/unified_router.py muscle research "Analyze AI agent market"
python3 antigravity/unified_router.py muscle creative "Write viral hook"
python3 antigravity/unified_router.py muscle coding "Implement retry logic"
```

---

## Tip 2: Host on Local Device, Not VPS

**Status: IMPLEMENTED (file watcher + local Ollama stack)**

Advantage: Airdrop files from phone → agent auto-processes them.

**File watcher workflow:**
```bash
python3 scripts/file_watcher.py          # Watch ~/AIEmpire-Core/watch/
python3 scripts/file_watcher.py ~/Desktop # Watch custom folder
```

Drop a file → auto-process:
- **Video** → transcribe (whisper), translate 10 languages, extract chapters
- **Document** → summarize, extract action items
- **Image** → describe, suggest social captions
- **Code** → review, find bugs, suggest improvements
- **Audio** → transcribe, create show notes

Output goes to `watch/processed/`.

**Local stack (docker-compose):**
- Ollama (LLMs, free)
- LiteLLM Proxy (unified API gateway)
- ChromaDB (vector DB)
- Redis (cache/queue)

---

## Tip 3: Telegram for Quick, Discord for Deep Work

**Status: CONFIGURED in OpenClaw AGENTS.md**

- **Telegram**: Fast messaging, file sharing, status checks. Set up via BotFather.
- **Discord**: Multi-channel workflows where subagents work in different channels.

The BOOTSTRAP.md guides initial Telegram/Discord setup on first run.

---

## Tip 4: Reverse Prompt as Much as You Can

**Status: IMPLEMENTED (3x daily cron job + heartbeat)**

Instead of telling your agent what to do, ASK it:

> "Based on what you know about me and my goals, what is the next best task?"

**Cron job runs 3x daily (07:00, 13:00, 20:00)** asking:
1. What is the single highest-impact task right now?
2. What is blocked or stalled?
3. What quick win could we knock out in <15 minutes?
4. Is there anything I should know that I probably don't?

**Files:**
- `openclaw-config/jobs.json` — "Reverse Prompt" cron job
- `openclaw-config/HEARTBEAT.md` — Reverse prompt on idle

**Also added: Daily optimization check (07:30)** that reviews:
- Git status, uncommitted changes
- Recent memory files
- System inventory
- Automation opportunities

---

## Tip 5: Use OpenClaw to Vibe Code

**Status: IMPLEMENTED**

Instead of using Claude Code directly, tell your OpenClaw what to build:

```bash
./scripts/vibe_code.sh "Build a FastAPI endpoint for user metrics"
./scripts/vibe_code.sh "Fix import errors in empire_engine.py"
./scripts/vibe_code.sh  # Interactive mode
```

Routes to: Codex CLI → Claude Code → Ollama (whichever is available).

---

## Tip 6: Build Your Own Mission Control

**Status: IMPLEMENTED (NextJS scaffold)**

Custom tooling dashboard at http://localhost:3001:

```bash
cd mission-control && npm install && npm run dev
```

**3 built-in tools:**
1. **Revenue Pipeline** — Track all revenue channels, next actions
2. **System Inventory** — Monitor all 14+ systems, health status
3. **Content Pipeline** — View cron schedule, draft management

**Dashboard features:**
- Real-time system health monitoring
- Multi-muscle router status
- Cron job overview
- Quick actions (trigger reverse prompt, check router, vibe code)

---

## Tip 7: Run Everything Through OpenClaw

**Status: IMPLEMENTED (daily optimization cron)**

Every task on your computer — run it through your agent first.

The **daily optimization check** (07:30 cron) automatically:
1. Checks git status
2. Reviews recent memory files
3. Checks system inventory
4. Identifies 3 automation opportunities
5. Suggests 1 workflow improvement

---

## Tip 8: Start Cheap, Scale Up

**Recommendation: Follow this progression**

1. **Start**: Any laptop with 8GB+ RAM → Ollama with 7B models (free)
2. **Scale**: Mac Mini M2 (16GB) → Ollama with 14B models (free)
3. **Max**: Mac Studio M2 Ultra (64GB+) → Multiple 70B models in parallel

Current setup optimized for 16GB RAM:
- Qwen 2.5 Coder 14B (primary coding muscle)
- Qwen 2.5 Coder 7B (fast tasks)
- DeepSeek R1 7B (reasoning)
- Code Llama 7B (vibe code)

---

## Tip 9: Don't Give Email Access

**Status: IMPLEMENTED (hard block)**

Email is a prompt injection vector. An attacker can send a crafted email
that manipulates the agent's behavior.

**Changes:**
- Removed email from heartbeat checks
- Added hard security rule in AGENTS.md: "NEVER access, read, or send emails"
- Removed email from `heartbeat-state.json` template

---

## Tip 10: Don't Give It Its Own X Account

**Status: IMPLEMENTED (draft-only mode)**

X is actively cracking down on bots and API usage.

**Changes:**
- All X/Twitter content is now DRAFT ONLY
- No direct API posting
- Agent generates content → saves to files → Maurice reviews and posts manually
- Updated AGENTS.md with hard security rule
- Mission Control content page shows this workflow clearly

---

## Tip 11: Have Fun and Experiment

This is the greatest technology of our lifetimes. The setup is designed
to make experimentation easy:

- Vibe code anything with `scripts/vibe_code.sh`
- Drop files for auto-processing with `scripts/file_watcher.py`
- Reverse prompts keep the agent proactive
- Mission Control gives you a visual dashboard
- Multi-muscle routing optimizes cost automatically

Don't worry about making money immediately. Build, tinker, learn.
The revenue systems are ready when you are.

---

## Quick Reference

```bash
# Dashboard
python3 empire_engine.py

# Vibe Code
./scripts/vibe_code.sh "Build something cool"

# File Watcher
python3 scripts/file_watcher.py

# Multi-Muscle Router
python3 antigravity/unified_router.py status
python3 antigravity/unified_router.py muscle research "Analyze trends"

# Mission Control
cd mission-control && npm run dev

# System Repair
python3 scripts/auto_repair.py

# Bombproof Startup
./scripts/bombproof_startup.sh
```
