"""
Ant Protocol - Autonomous Swarm Intelligence for AI Empire
==========================================================
Agents arbeiten wie Ameisen: autonom, dezentral, kolonie-intelligent.

Architecture:
  QUEEN (Skybot)     - Task-Verteilung, Colony-Monitoring, Pheromone-Steuerung
  WORKER ANTS        - Autonome Task-Discovery, Claim, Execute, Report
  PHEROMONE SYSTEM   - Prioritaets-Signale die Worker anziehen/abstossen
  COLONY STATE       - Shared State via Redis (Task Board, Registry, Trails)
"""

__version__ = "1.0.0"
