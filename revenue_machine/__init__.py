"""
AIEmpire Revenue Machine
Unified automated revenue generation system

This module integrates:
- Revenue Pipeline (News → Content → Publishing → Ads → Money)
- Existing systems (X Lead Machine, CRM, Atomic Reactor)
- OpenClaw 50K agent swarm
- Multi-model routing (Ollama 95% + Gemini 4% + Claude 1%)

Total capability: 100+ pieces of content per day, fully automated
Target revenue: €1,000/day minimum (€30k/month)
Yearly goal: €1,000,000 (Maurice's 100x mission)
"""

from .pipeline import (
    RevenuePipeline,
    NewsScanner,
    ContentFactory,
    MultiPlatformPublisher,
    AdManager,
    SelfOptimizer,
    ContentType,
    Platform,
    RevenueSource,
)

__all__ = [
    "RevenuePipeline",
    "NewsScanner",
    "ContentFactory",
    "MultiPlatformPublisher",
    "AdManager",
    "SelfOptimizer",
    "ContentType",
    "Platform",
    "RevenueSource",
]

__version__ = "1.0.0"
