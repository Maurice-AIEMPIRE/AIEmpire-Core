#!/usr/bin/env python3
"""
SHORTS MACHINE - Faceless YouTube Shorts Money Machine
Vollautomatische Pipeline: Trend → Script → Video → Upload → Optimize

Architecture:
  TrendMiner → IdeaRanker → ScriptFactory → AssetFactory →
  VoiceFactory → VideoComposer → YouTubePublisher → MetricsCollector → Optimizer

Revenue-Strategie:
  Shorts = Distribution (Traffic)
  Geld = Funnel (Affiliate + Digital Products + Leads + AdSense)

Usage:
  python -m shorts_machine                    # Status
  python -m shorts_machine --mine 100         # 100 Ideen minen
  python -m shorts_machine --scripts 30       # 30 Scripts generieren
  python -m shorts_machine --produce 10       # 10 Videos produzieren
  python -m shorts_machine --publish          # Upload-Queue abarbeiten
  python -m shorts_machine --metrics          # Metrics pullen
  python -m shorts_machine --optimize         # Hook/Format Optimizer
  python -m shorts_machine --pipeline 10      # Full Pipeline (10 Shorts)
  python -m shorts_machine --daemon           # Autonomer Daemon
"""

__version__ = "1.0.0"
__all__ = [
    "TrendMiner",
    "IdeaRanker",
    "ScriptFactory",
    "HookGenerator",
    "VideoComposer",
    "YouTubePublisher",
    "MetricsCollector",
    "Optimizer",
]
