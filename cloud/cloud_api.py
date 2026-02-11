#!/usr/bin/env python3
"""
Cloud API — Empire REST API for Google Cloud
==============================================
Single FastAPI server that exposes ALL Empire features via REST.
Runs on Cloud Run, GCE, or any container platform.

Endpoints:
  GET  /health          → System health
  GET  /status          → Full system status
  POST /ask             → Ask AI (smart routing)
  POST /agents/run      → Run specific agent
  POST /agents/auto     → Full autonomous cycle
  GET  /feeds/scan      → Scan feeds
  GET  /feeds/github    → GitHub trending
  GET  /feeds/hn        → Hacker News
  POST /knowledge/add   → Add knowledge item
  GET  /knowledge/search → Search knowledge

Port: 8080 (Cloud Run standard)
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Setup paths
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Load env
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    import uvicorn
except ImportError:
    print("FastAPI not installed. Run: pip install fastapi uvicorn")
    sys.exit(1)


app = FastAPI(
    title="AI Empire Cloud API",
    version="2.0.0",
    description="Maurice Pfeifer's AI Empire — Cloud API"
)


# ─── Health & Status ──────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/status")
async def status():
    """Full system status."""
    from empire_boot import check_ollama, check_api_keys
    return {
        "ollama": check_ollama(),
        "api_keys": check_api_keys(),
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
    }


# ─── AI Queries ───────────────────────────────────────────────

@app.post("/ask")
async def ask(prompt: str, prefer: str = "auto", system: str = ""):
    """Ask AI with smart provider routing."""
    from antigravity.provider_chain import get_chain
    chain = get_chain()
    result = await chain.query(prompt=prompt, system=system, prefer=prefer)
    return result


# ─── Agents ───────────────────────────────────────────────────

@app.post("/agents/run")
async def run_agent(agent: str, task: str, prefer: str = "ollama"):
    """Run a specific agent."""
    from antigravity.agent_orchestrator import Orchestrator
    orch = Orchestrator(prefer_provider=prefer)
    result = await orch.run(agent, task)
    return result


@app.post("/agents/auto")
async def auto_cycle(prefer: str = "ollama"):
    """Run full autonomous cycle."""
    from antigravity.agent_orchestrator import Orchestrator
    orch = Orchestrator(prefer_provider=prefer)
    result = await orch.auto_cycle()
    return result


# ─── Feed Scanner ─────────────────────────────────────────────

@app.get("/feeds/scan")
async def scan_feeds():
    """Full feed scan (HN + GitHub + OSS)."""
    from antigravity.feed_scanner import FeedScanner
    scanner = FeedScanner()
    result = await scanner.full_scan()
    return result


@app.get("/feeds/github")
async def github_trending():
    """GitHub trending repos."""
    from antigravity.feed_scanner import FeedScanner
    scanner = FeedScanner()
    return await scanner.scan_github_trending()


@app.get("/feeds/hn")
async def hackernews():
    """Hacker News top stories."""
    from antigravity.feed_scanner import FeedScanner
    scanner = FeedScanner()
    return await scanner.scan_hackernews()


# ─── Knowledge Store ─────────────────────────────────────────

@app.post("/knowledge/add")
async def add_knowledge(ki_type: str, title: str, content: str, tags: str = ""):
    """Add knowledge item."""
    from antigravity.knowledge_store import KnowledgeStore
    ks = KnowledgeStore()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    ks.add(ki_type, title, content=content, tags=tag_list)
    return {"status": "added", "title": title}


@app.get("/knowledge/search")
async def search_knowledge(q: str):
    """Search knowledge store."""
    from antigravity.knowledge_store import KnowledgeStore
    ks = KnowledgeStore()
    results = ks.search(q)
    return {"query": q, "results": len(results), "items": [vars(r) for r in results[:10]]}


# ─── Main ─────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    print(f"\n  AI Empire Cloud API starting on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
