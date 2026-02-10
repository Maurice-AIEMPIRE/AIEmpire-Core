"""
Gemini Mirror - Dual System Architecture for AIEmpire.

Claude (Mac) + Gemini (Cloud) = Exponential Intelligence.

Components:
- gemini_client: Gemini API interface with cost tracking
- mirror_sync: Bidirectional sync engine
- digital_memory: Persistent knowledge graph
- vision_discovery: Daily question system
- evolution_protocol: Cross-system evolution
- mirror_daemon: Main orchestrator
"""

from .gemini_client import GeminiClient, MirrorGeminiClient
from .digital_memory import DigitalMemory
from .mirror_sync import MirrorSyncEngine
from .vision_discovery import VisionDiscoveryEngine
from .evolution_protocol import EvolutionProtocol

__version__ = "1.0.0"

__all__ = [
    "GeminiClient",
    "MirrorGeminiClient",
    "DigitalMemory",
    "MirrorSyncEngine",
    "VisionDiscoveryEngine",
    "EvolutionProtocol",
]
