#!/usr/bin/env python3
"""
GEMINI MIRROR - Configuration
Dual-Brain Architecture: Claude (Mac) <-> Gemini (Cloud)

Environment Variables:
  GEMINI_API_KEY        - Google Gemini API key (required)
  MOONSHOT_API_KEY      - Kimi/Moonshot API key (existing)
  ANTHROPIC_API_KEY     - Claude API key (existing)
  EMPIRE_SYNC_SECRET    - Shared secret for sync authentication
"""

import os
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
MIRROR_DIR = Path(__file__).parent
STATE_DIR = MIRROR_DIR / "state"
SYNC_QUEUE_DIR = MIRROR_DIR / "sync_queue"
OUTPUT_DIR = MIRROR_DIR / "output"
MEMORY_DIR = MIRROR_DIR / "memory"

for d in [STATE_DIR, SYNC_QUEUE_DIR, OUTPUT_DIR, MEMORY_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── API Keys ─────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
EMPIRE_SYNC_SECRET = os.getenv("EMPIRE_SYNC_SECRET", "empire-dual-brain-2026")

# ── Gemini API ───────────────────────────────────────────────
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MODEL = "gemini-2.5-pro"  # Latest Gemini model
GEMINI_FLASH_MODEL = "gemini-2.5-flash"  # Fast/cheap model for bulk tasks

# ── Model Routing ────────────────────────────────────────────
# Which brain handles what
MODEL_ROUTING = {
    # Gemini handles: creative expansion, parallel research, bulk analysis
    "creative_expansion": {"provider": "gemini", "model": GEMINI_MODEL},
    "bulk_research": {"provider": "gemini", "model": GEMINI_FLASH_MODEL},
    "vision_questions": {"provider": "gemini", "model": GEMINI_MODEL},
    "code_review": {"provider": "gemini", "model": GEMINI_MODEL},
    "strategy_analysis": {"provider": "gemini", "model": GEMINI_MODEL},

    # Claude handles: critical decisions, architecture, final review
    "architecture": {"provider": "claude", "model": "claude-sonnet-4-20250514"},
    "critical_review": {"provider": "claude", "model": "claude-sonnet-4-20250514"},
    "final_merge": {"provider": "claude", "model": "claude-sonnet-4-20250514"},

    # Kimi handles: bulk tasks, cost-efficient operations
    "bulk_tasks": {"provider": "kimi", "model": "moonshot-v1-32k"},
    "content_gen": {"provider": "kimi", "model": "moonshot-v1-32k"},
}

# ── Sync Configuration ───────────────────────────────────────
SYNC_CONFIG = {
    # How often to sync state between brains (seconds)
    "sync_interval": 300,  # 5 minutes

    # What to sync
    "sync_targets": [
        "workflow-system/state/current_state.json",
        "workflow-system/state/cowork_state.json",
        "workflow-system/state/pattern_library.json",
        "gemini-mirror/state/gemini_state.json",
        "gemini-mirror/state/vision_state.json",
        "gemini-mirror/memory/shared_knowledge.json",
    ],

    # Conflict resolution: which brain wins
    "conflict_resolution": "merge_best",  # merge_best | claude_wins | gemini_wins

    # Max improvements to queue before forced sync
    "max_queue_size": 50,
}

# ── Vision Discovery ─────────────────────────────────────────
VISION_CONFIG = {
    # Questions per day
    "daily_questions": 5,

    # Categories of questions to ask Maurice
    "question_categories": [
        "vision_clarity",      # What exactly does success look like?
        "priority_ranking",    # Which goal matters most right now?
        "resource_allocation", # Where should time/money go?
        "risk_tolerance",      # How aggressive should we be?
        "lifestyle_goals",     # What life do you want to live?
        "business_model",      # How should money flow?
        "tech_preferences",    # Which tools/approaches resonate?
        "relationship_goals",  # Who do you want to work with?
        "timeline_pressure",   # How urgent is each goal?
        "unfair_advantages",   # What unique strengths to leverage?
    ],

    # Store answers persistently
    "answer_retention": "permanent",

    # Build profile from answers
    "profile_update_threshold": 3,  # Update after 3 new answers
}

# ── Cross-Pollination ────────────────────────────────────────
CROSS_POLLINATION_CONFIG = {
    # How to compare outputs from both brains
    "comparison_method": "structured_diff",

    # What to cross-pollinate
    "pollination_targets": [
        "workflow_outputs",
        "strategy_decisions",
        "code_improvements",
        "pattern_discoveries",
        "revenue_ideas",
    ],

    # Quality threshold for accepting improvements
    "quality_threshold": 0.7,

    # Maximum improvements per sync cycle
    "max_improvements_per_cycle": 10,
}
