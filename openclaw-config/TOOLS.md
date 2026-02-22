# TOOLS.md - Local Notes & Tool Configuration

## Vibe Code (Tip #5)
Use `scripts/vibe_code.sh` to code through natural language:
```bash
./scripts/vibe_code.sh "Build a FastAPI endpoint for user metrics"
./scripts/vibe_code.sh "Fix import errors in empire_engine.py"
```
Routes to: Codex CLI → Claude Code → Ollama (whichever is available).

## Multi-Muscle Router (Tip #1)
Different models for different tasks. Use the router directly:
```bash
python3 antigravity/unified_router.py muscle coding "Implement retry logic"
python3 antigravity/unified_router.py muscle research "Analyze AI agent trends"
python3 antigravity/unified_router.py muscle creative "Write viral hook about AI"
```

## File Watcher (Tip #2)
Auto-processes files dropped into `watch/` folder:
```bash
python3 scripts/file_watcher.py
# Drop a video → auto-transcribe, translate, generate thumbnails
# Drop a document → auto-summarize, extract action items
# Drop an image → auto-describe, suggest social media caption
```

## Mission Control (Tip #6)
Custom tooling dashboard at http://localhost:3001:
```bash
cd mission-control && npm run dev
```

## Communication Channels (Tip #3)
- **Telegram**: Quick messages, status checks, file sharing
- **Discord**: Deep work, multi-channel workflows with subagents

## SSH / Servers
- Local Ollama: http://localhost:11434
- LiteLLM Proxy: http://localhost:4000
- CRM: http://localhost:3500
- Atomic Reactor: http://localhost:8888
- Mission Control: http://localhost:3001

## Security Rules (Tips #9, #10)
- NO email access (prompt injection vector)
- NO direct X/Twitter API posting (bot detection risk)
- Content is DRAFTED only, human posts manually
- All API keys in .env, never hardcoded
