#!/usr/bin/env python3
"""
KODEX KNOWLEDGE TRANSFER
========================
Script to load all critical knowledge items into the Knowledge Store.
Run this ONCE to initialize Kodex's knowledge base.

Usage:
    python3 KODEX_KNOWLEDGE_TRANSFER.py

This will create persistent knowledge items that Kodex can search/access.
"""

import sys
from pathlib import Path

# Setup path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from antigravity.knowledge_store import KnowledgeStore

def transfer_knowledge():
    """Transfer all critical knowledge to Kodex via Knowledge Store."""

    ks = KnowledgeStore()

    print("📚 KODEX KNOWLEDGE TRANSFER")
    print("=" * 60)

    # ═══════════════════════════════════════════════════════════════════════════════
    # CRITICAL FIXES
    # ═══════════════════════════════════════════════════════════════════════════════

    ks.add(
        ki_type="fix",
        title="Ollama Timeout Root Cause (CRITICAL)",
        content="""
PROBLEM: litellm.APIConnectionError with 40s timeout in Telegram bot

ROOT CAUSE: Ollama service is NOT running. The error occurs because:
1. ollama serve process is not started
2. localhost:11434 is unreachable
3. Fallback models (Kimi, Claude) are not being called

IMMEDIATE FIX (Kodex):
1. Check: ps aux | grep ollama
2. Start: ollama serve &
3. Verify: curl http://localhost:11434/api/tags
4. Test: python3 -c "import requests; print(requests.get('http://localhost:11434/api/tags').json())"

PERMANENT FIX:
- Add auto-start in bombproof_startup.sh
- Implement health check in resource_guard.py
- Multi-model failover (Ollama → Kimi → Gemini)

See: KODEX_HANDOVER_OLLAMA_FIX.md for full details
""",
        tags=["critical", "ollama", "timeout", "telegram", "fix"],
        confidence=1.0,
        references=["KODEX_HANDOVER_OLLAMA_FIX.md", "antigravity/config.py"],
        source="Claude Code - March 7 2026"
    )

    ks.add(
        ki_type="fix",
        title="Config Loading - NEVER use os.getenv directly",
        content="""
PATTERN: All config must go through antigravity/config.py

WRONG:
    import os
    api_key = os.getenv("MOONSHOT_API_KEY")  # ❌ Breaks after crashes

CORRECT:
    from antigravity.config import MOONSHOT_API_KEY  # ✅ Auto-loads from .env
    # or
    from antigravity.config import KIMI_API_KEY  # Alias

WHY: config.py has _load_dotenv() that survives crashes/reboots.
Direct os.getenv loses vars on system reset.

Files to check:
- x_lead_machine/post_generator.py (line 13)
- x_lead_machine/x_automation.py (line 15)
- workflow_system/empire.py (check for os.getenv)
""",
        tags=["critical", "config", "bestpractice"],
        confidence=1.0,
        references=["antigravity/config.py"],
        source="Claude Code"
    )

    # ═══════════════════════════════════════════════════════════════════════════════
    # ARCHITECTURE DECISIONS
    # ═══════════════════════════════════════════════════════════════════════════════

    ks.add(
        ki_type="architecture",
        title="Empire System - 6 Automation Phases",
        content="""
MASTER PLAN: Autonomous Revenue System (Maurice's Goal: EUR 100M in 1-3 years)

PHASE 1 (Week 1): X.com Trend Scanner
- Real-time X trending topic scraping
- Competitor analysis (levelsio, marc_louvion, etc.)
- Auto-generate content ideas from trends
- Store in Knowledge Store for later phases

PHASE 2 (Week 2): Mega-Content Production
- 3 Personas (BMA-Meister, AI Agent King, Money Machine)
- 3 posts/day per persona = 9 posts/day = 63 posts/week
- 6 post styles: result, controversial, tutorial, question, behind-scenes, story
- Kimi 8K model for generation, Gemini for cross-verify

PHASE 3 (Week 3): Autonomous Distribution
- X/Twitter: 3 posts/day per persona (9 total)
- LinkedIn: 1 post/day (BMA-Meister)
- TikTok/YouTube Shorts: Auto-generated from tutorials
- Instagram: 1 post/day (Money Machine)
- Viral reply bot: Auto-reply to trending posts
- DM automation: Lead capturing + welcome sequences

PHASE 4 (Week 4): Self-Improvement Loop
- Daily metrics: engagement rate, lead conversion, content ROI
- Weekly analysis: top 5 posts, emerging trends
- Monthly learning: viral formula extraction, seasonal patterns
- Auto-update hooks/CTAs database based on performance

PHASE 5 (Week 3-4): Revenue Automation
- Gumroad products (27/79/149 EUR)
- Fiverr/Upwork AI services (50-5000 EUR)
- Consulting (BMA + AI, 2000-10000 EUR)
- Community membership (29 EUR/month)
- Affiliate links in posts

PHASE 6 (Week 4+): Full Autonomy
- 24/7 autonomous cycle (scan → produce → distribute → monetize → learn)
- No human intervention needed
- System self-heals via auto-repair
- Resource Guard prevents crashes

TIMELINE:
- Week 2: 1K followers
- Month 1: 1K followers, 100 customers, EUR 5K MRR
- Month 2: 50K followers, 500 customers, EUR 50K MRR
- Month 3: 100K followers, 1K customers, EUR 200K MRR

See: EMPIRE_AUTOMATION_MASTER_PLAN.md for complete details
""",
        tags=["architecture", "empire", "automation", "revenue", "roadmap"],
        confidence=1.0,
        references=["EMPIRE_AUTOMATION_MASTER_PLAN.md"],
        source="Claude Code - March 7 2026"
    )

    # ═══════════════════════════════════════════════════════════════════════════════
    # OPERATIONAL KNOWLEDGE
    # ═══════════════════════════════════════════════════════════════════════════════

    ks.add(
        ki_type="decision",
        title="Model Routing Strategy - Fallback Chain",
        content="""
PRINCIPLE: Every AI call goes through unified_router (NEVER direct API calls)

FALLBACK CHAIN:
1. Ollama (local) - 95% usage
   - Free, fast, local
   - Models: mistral, neural-chat, dolphin
   - Timeout: 40s (increase to 120s if running slow)

2. Kimi (Moonshot) - 4% usage
   - When Ollama times out
   - MOONSHOT_API_KEY required
   - 8K context model

3. Claude (Anthropic) - 1% usage
   - When Kimi fails
   - ANTHROPIC_API_KEY required
   - Critical tasks only

OPTIMIZATION: Run all 3 models in parallel, return fastest valid result

IMPLEMENTATION:
    from antigravity.unified_router import UnifiedRouter
    router = UnifiedRouter()

    # Auto-routes through fallback chain
    result = await router.complete("Your prompt here")

    # Force specific model
    result = await router.complete("Prompt", model="kimi")

See: antigravity/unified_router.py for implementation
""",
        tags=["architecture", "routing", "models", "fallback"],
        confidence=1.0,
        references=["antigravity/unified_router.py", "antigravity/config.py"],
        source="Claude Code"
    )

    ks.add(
        ki_type="pattern",
        title="Viral Content Patterns (from existing code)",
        content="""
6 PROVEN POST STYLES (from x_lead_machine/post_generator.py):

1. RESULT style
   Hook + Concrete Result (with numbers) + How + CTA
   Example: "Von 0 auf 100 Leads in 24 Stunden. Ohne Cold Calls. Ohne Ads. Ohne Team. Nur AI + Strategie. Like wenn du wissen willst wie."

2. CONTROVERSIAL style
   Polarizing opinion that starts discussion (fact-based)

3. TUTORIAL style
   Step-by-step (numbered), immediately actionable

4. QUESTION style
   Genuine engagement question (not fake)

5. BEHIND-SCENES style
   Transparent, authentic look at what you're building

6. STORY style
   Short story: Problem → Solution → Learning

POST RULES:
- Max 280 characters (or THREAD if longer)
- First line = Hook (stops scroll)
- No hashtags in text
- No "Hey" or "Hallo"
- Max 1-2 emojis
- Call-to-action at end
- Language: Deutsch (DE) or English (EN)

TRENDING TOPICS (February 2026):
- Claude Code + AI Agents
- Vibe Coding - AI schreibt Code
- MCP Model Context Protocol
- 50K AI Agents gleichzeitig
- Von 0 auf €100k mit AI
- Ollama - kostenlose lokale LLMs
- AI Automation Agency starten
- ChatGPT vs Claude vs Gemini
- Build in Public
- No-Code AI Automation

BUYER KEYWORDS (to monitor for leads):
"looking for AI", "need automation", "anyone built", "how do I automate",
"struggling with", "hate manual work", "need help with", "recommend any AI",
"best tool for", "who can help", "hiring for AI", "budget for automation"

TARGET ACCOUNTS (to monitor):
levelsio, marc_louvion, gregisenberg, taborenz, swyx, alexalbert__

See: x_lead_machine/post_generator.py, x_lead_machine/x_automation.py
""",
        tags=["content", "viral", "patterns", "x-twitter"],
        confidence=0.9,
        references=["x_lead_machine/post_generator.py"],
        source="Claude Code"
    )

    # ═══════════════════════════════════════════════════════════════════════════════
    # OPERATIONAL PROCEDURES
    # ═══════════════════════════════════════════════════════════════════════════════

    ks.add(
        ki_type="decision",
        title="Startup & Recovery Procedures",
        content="""
BOMBPROOF STARTUP SEQUENCE (5 phases, automated):

Phase 1: Auto-Repair
- Fix .env variables
- Recover from crashes
- Clean corrupted files
- Start Ollama if needed

Phase 2: Health Check
- Resource Guard startup_check
- Detect previous crashes → Safe Mode
- Database integrity check

Phase 3: Core Services
- Ollama (95% cost)
- Redis (caching)
- PostgreSQL (persistence)

Phase 4: App Services
- CRM (Port 3500)
- Atomic Reactor (Port 8888)
- OpenClaw agents (Port 18789)

Phase 5: Verification
- Health check all services
- Smoke tests
- Warm up models

MANUAL START:
    ./scripts/bombproof_startup.sh

AUTO-START ON BOOT:
    # macOS:
    cp scripts/com.aiempire.bombproof.plist ~/Library/LaunchAgents/
    launchctl load ~/Library/LaunchAgents/com.aiempire.bombproof.plist

    # Linux (systemd):
    sudo cp scripts/aiempire.service /etc/systemd/system/
    sudo systemctl enable aiempire
    sudo systemctl start aiempire

RESOURCE MONITORING:
    python3 workflow_system/resource_guard.py

THRESHOLDS:
- CPU > 95% or RAM > 92% → EMERGENCY (stop Ollama)
- CPU > 85% or RAM > 85% → CRITICAL (concurrency: 50)
- CPU > 70% or RAM > 75% → WARN (concurrency: 200)
- Trend rising + >60% → PREDICTIVE WARN

See: scripts/bombproof_startup.sh, workflow_system/resource_guard.py
""",
        tags=["operational", "startup", "recovery", "health"],
        confidence=1.0,
        references=["scripts/bombproof_startup.sh", "workflow_system/resource_guard.py"],
        source="Claude Code"
    )

    ks.add(
        ki_type="learning",
        title="System Quick Commands Reference",
        content="""
EMPIRE ENGINE (Main entry point):
    python3 empire_engine.py              # Status dashboard
    python3 empire_engine.py scan         # Scan X trends
    python3 empire_engine.py produce      # Generate content
    python3 empire_engine.py distribute   # Post to platforms
    python3 empire_engine.py leads        # Process CRM leads
    python3 empire_engine.py revenue      # Revenue report
    python3 empire_engine.py auto         # Full autonomous cycle
    python3 empire_engine.py repair       # Self-heal system
    python3 empire_engine.py setup        # Dev setup

KNOWLEDGE STORE ACCESS:
    from antigravity.knowledge_store import KnowledgeStore
    ks = KnowledgeStore()
    results = ks.search("ollama timeout")
    results = ks.search_by_tag("critical")
    recent = ks.recent(limit=10)

EMPIRE BRIDGE (Integration layer):
    from antigravity.empire_bridge import get_bridge
    bridge = get_bridge()
    result = await bridge.execute("Prompt here")
    result = await bridge.execute_verified("Critical task")
    bridge.learn("fix", "Title", "Content")
    status = bridge.system_status()

DEBUG OLLAMA:
    ps aux | grep ollama                          # Check running
    ollama list                                   # List models
    ollama serve &                                # Start service
    curl http://localhost:11434/api/tags          # Test API
    tail -f /tmp/ollama.log                       # View logs

RESOURCE MONITORING:
    python3 workflow_system/resource_guard.py              # Status
    python3 workflow_system/resource_guard.py --can-launch 14b  # Check before launch

AUTO-REPAIR:
    python3 scripts/auto_repair.py                # Self-heal

GIT OPERATIONS:
    git branch -a                                 # Show branches
    git status                                    # Current status
    git log --oneline -10                         # Recent commits
    git push -u origin claude/setup-lobehub-skills-3xEMa  # Push to feature branch
""",
        tags=["operational", "commands", "quickref"],
        confidence=1.0,
        references=["empire_engine.py", "antigravity/empire_bridge.py"],
        source="Claude Code"
    )

    # ═══════════════════════════════════════════════════════════════════════════════
    # SUMMARIZE
    # ═══════════════════════════════════════════════════════════════════════════════

    print("\n✅ KNOWLEDGE ITEMS LOADED:")
    print()

    recent = ks.recent(limit=10)
    for i, item in enumerate(recent, 1):
        print(f"{i}. [{item.ki_type.upper()}] {item.title}")
        print(f"   Tags: {', '.join(item.tags)}")
        print(f"   Confidence: {item.confidence * 100:.0f}%")
        print()

    print("=" * 60)
    print("📚 Knowledge Transfer Complete!")
    print()
    print("KODEX CAN NOW ACCESS KNOWLEDGE VIA:")
    print("  from antigravity.knowledge_store import KnowledgeStore")
    print("  ks = KnowledgeStore()")
    print("  results = ks.search('ollama')")
    print("  results = ks.search_by_tag('critical')")
    print()
    print("STORED IN: .antigravity/knowledge_store.jsonl")
    print()

if __name__ == "__main__":
    transfer_knowledge()
