#!/usr/bin/env python3
"""
OPEN SWARM - Komplett kostenloser Agent-Schwarm mit Ollama.
Ersetzt Kimi Moonshot API ($$$) durch lokale LLMs ($0).

Architektur:
  Kimi Swarm:  500 concurrent, Moonshot API, $0.0005/task
  Open Swarm:  1-4 concurrent, Ollama lokal, $0.00/task = GRATIS

Sprint-System:
  - Fokussierte Task-Bursts (30-120 Min)
  - Resource-aware Concurrency
  - Self-orchestrating (kein Claude API noetig)
  - Gleiche Output-Struktur wie Kimi Swarm

Usage:
  # Sprint starten (default: 50 Tasks, revenue-fokus)
  python open_swarm.py --sprint revenue --tasks 50

  # Content-Sprint (100 Posts generieren)
  python open_swarm.py --sprint content --tasks 100

  # Lead-Sprint
  python open_swarm.py --sprint leads --tasks 30

  # Daemon: Automatische Sprints alle 60 Min
  python open_swarm.py --daemon --interval 3600

  # Test-Modus (5 Tasks, schneller Check)
  python open_swarm.py --test

  # Status
  python open_swarm.py --status
"""

import asyncio
import json
import os
import sys
import time
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field

# ── Modul-Imports (defensiv) ─────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

try:
    from ollama_engine import OllamaEngine, LLMResponse
except ImportError:
    OllamaEngine = None
    LLMResponse = None

try:
    from resource_guard import ResourceGuard, sample_resources
except ImportError:
    ResourceGuard = None
    sample_resources = None

try:
    from agent_manager import AgentManager
except ImportError:
    AgentManager = None

# ── Konfiguration ────────────────────────────────────────

# Ollama-basiert: Concurrency haengt von RAM ab
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
OLLAMA_SMALL_MODEL = os.getenv("OLLAMA_SMALL_MODEL", "qwen2.5-coder:3b")

# Output-Verzeichnisse (kompatibel mit Kimi Swarm)
OUTPUT_DIR = Path(__file__).parent / "swarm_output"
STATE_DIR = Path(__file__).parent / "state"
SPRINT_STATE_FILE = STATE_DIR / "open_swarm_state.json"

LEADS_DIR = OUTPUT_DIR / "leads"
CONTENT_DIR = OUTPUT_DIR / "content"
COMPETITORS_DIR = OUTPUT_DIR / "competitors"
NUGGETS_DIR = OUTPUT_DIR / "gold_nuggets"
REVENUE_OPS_DIR = OUTPUT_DIR / "revenue_operations"
INSIGHTS_DIR = OUTPUT_DIR / "insights"

for d in [OUTPUT_DIR, STATE_DIR, LEADS_DIR, CONTENT_DIR, COMPETITORS_DIR,
          NUGGETS_DIR, REVENUE_OPS_DIR, INSIGHTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ── Sprint-Definitionen ─────────────────────────────────

SPRINT_TYPES = {
    "revenue": {
        "name": "Revenue Sprint",
        "beschreibung": "Fokus auf Umsatz-generierende Tasks",
        "task_weights": {
            "revenue_optimization": 3.0,
            "gold_nugget": 2.0,
            "high_value_lead": 2.0,
            "strategic_partnership": 1.5,
            "viral_content": 1.0,
            "competitor_intel": 0.5,
        },
    },
    "content": {
        "name": "Content Sprint",
        "beschreibung": "Masse an X + TikTok Content produzieren",
        "task_weights": {
            "viral_content": 4.0,
            "revenue_optimization": 1.0,
            "gold_nugget": 1.0,
            "high_value_lead": 0.5,
            "strategic_partnership": 0.3,
            "competitor_intel": 0.2,
        },
    },
    "leads": {
        "name": "Lead Sprint",
        "beschreibung": "Hochwertige B2B Leads recherchieren",
        "task_weights": {
            "high_value_lead": 4.0,
            "strategic_partnership": 2.0,
            "competitor_intel": 1.5,
            "viral_content": 1.0,
            "revenue_optimization": 0.5,
            "gold_nugget": 0.5,
        },
    },
    "intel": {
        "name": "Intelligence Sprint",
        "beschreibung": "Markt- und Wettbewerbs-Analyse",
        "task_weights": {
            "competitor_intel": 4.0,
            "gold_nugget": 3.0,
            "strategic_partnership": 2.0,
            "revenue_optimization": 1.0,
            "high_value_lead": 0.5,
            "viral_content": 0.5,
        },
    },
    "products": {
        "name": "Product Sprint",
        "beschreibung": "Produkt-Ideen und Optimierungen",
        "task_weights": {
            "gold_nugget": 3.0,
            "revenue_optimization": 3.0,
            "strategic_partnership": 1.5,
            "viral_content": 1.0,
            "high_value_lead": 1.0,
            "competitor_intel": 1.0,
        },
    },
}


# ── Task-Definitionen (gleich wie Kimi, aber fuer Ollama optimiert) ──

TASK_TYPES = {
    "high_value_lead": {
        "output_dir": LEADS_DIR,
        "priority": "high",
        "revenue_potential": 5000,
        "agent_id": "swarm-lead-finder",
        "squad": "sales",
        "system": "Du bist ein B2B Lead Research Agent. Antworte NUR mit validem JSON.",
        "prompt": """Generiere ein REALISTISCHES Premium-Lead-Profil.

Zielgruppe: Unternehmen die 10K-100K+ EUR fuer AI-Automation ausgeben.
Branchen: SaaS, E-Commerce, Manufacturing, Finance, Healthcare

OUTPUT als JSON:
{
    "handle": "@beispiel_firma",
    "company": "Firmenname",
    "industry": "Branche",
    "company_size": "50-500 employees",
    "annual_revenue": "5M-50M EUR",
    "pain_points": ["Problem 1", "Problem 2", "Problem 3"],
    "ai_opportunity": "Konkrete AI-Loesung",
    "estimated_project_value": "25000 EUR",
    "decision_maker": "CTO/CEO title",
    "outreach_hook": "Personalisierter erster Satz",
    "bant_score": 8
}""",
    },
    "viral_content": {
        "output_dir": CONTENT_DIR,
        "priority": "high",
        "revenue_potential": 1000,
        "agent_id": "swarm-content-x",
        "squad": "content",
        "system": "Du bist ein viraler Content Creator fuer X/Twitter. Antworte NUR mit validem JSON.",
        "prompt": """Generiere eine VIRALE X/Twitter Content-Idee mit Lead-Gen Hook.

Autor: Maurice Pfeifer, Elektrotechnikmeister + AI Automation Experte
Fokus: AI-Automation Success Stories, Behind-the-Scenes, BMA+AI Nische

OUTPUT als JSON:
{
    "format": "thread/single/meme/story",
    "hook": "Attention-grabbing erster Satz (max 280 Zeichen)",
    "main_content": "Hauptinhalt mit konkreten Zahlen und Story",
    "cta": "Call to Action mit Lead-Magnet",
    "lead_magnet": "Kostenloser Download Titel",
    "hashtags": ["#AI", "#Automation", "#BuildInPublic"],
    "viral_score": 8,
    "best_posting_time": "09:00 CET"
}""",
    },
    "competitor_intel": {
        "output_dir": COMPETITORS_DIR,
        "priority": "medium",
        "revenue_potential": 2000,
        "agent_id": "swarm-intel",
        "squad": "intelligence",
        "system": "Du bist ein Competitive Intelligence Agent. Antworte NUR mit validem JSON.",
        "prompt": """Analysiere einen FIKTIVEN AI-Automation Konkurrenten.
Finde strategische Schwachstellen die Maurice ausnutzen kann.

OUTPUT als JSON:
{
    "name": "Konkurrenten Name",
    "positioning": "Ihr USP",
    "services": ["Service 1", "Service 2", "Service 3"],
    "pricing": "Preismodell Details",
    "strengths": ["Staerke 1", "Staerke 2"],
    "weaknesses": ["Kritische Schwaeche 1", "Schwaeche 2"],
    "market_gap": "Opportunity fuer Maurice",
    "counter_strategy": "Wie Maurice gewinnt",
    "vulnerability_score": 7
}""",
    },
    "gold_nugget": {
        "output_dir": NUGGETS_DIR,
        "priority": "high",
        "revenue_potential": 10000,
        "agent_id": "swarm-nugget",
        "squad": "intelligence",
        "system": "Du bist ein Business Intelligence Agent. Antworte NUR mit validem JSON.",
        "prompt": """Extrahiere ein HIGH-VALUE Gold Nugget - sofort umsetzbare Business-Erkenntnis.

Kontext: AI Automation Business, BMA+AI Nische, Ziel 100M EUR
Kategorien: Monetarisierung, Skalierung, Automation, Arbitrage

OUTPUT als JSON:
{
    "category": "monetization/scaling/automation/arbitrage",
    "title": "Actionable Titel",
    "insight": "Konkrete Business-Erkenntnis mit Zahlen",
    "implementation_steps": ["Schritt 1", "Schritt 2", "Schritt 3"],
    "estimated_revenue": "10000 EUR/Monat",
    "implementation_time": "1-4 Wochen",
    "required_investment": "0-500 EUR",
    "roi_multiplier": "20x",
    "competitive_moat": "Wie defensible ist das?"
}""",
    },
    "revenue_optimization": {
        "output_dir": REVENUE_OPS_DIR,
        "priority": "critical",
        "revenue_potential": 15000,
        "agent_id": "swarm-revenue",
        "squad": "sales",
        "system": "Du bist ein Revenue Optimization Agent. Antworte NUR mit validem JSON.",
        "prompt": """Identifiziere eine konkrete Revenue-Optimierung fuer ein AI Automation Business.

Aktuelle Channels: Gumroad (27-149 EUR), Fiverr/Upwork, BMA+AI Consulting (2000-10000 EUR)
Alle Channels bei 0 EUR - muessen aktiviert werden!

OUTPUT als JSON:
{
    "optimization_type": "pricing/upsell/automation/cost_reduction/new_stream",
    "current_state": "Problem/Ineffizienz",
    "optimized_state": "Konkrete Loesung",
    "revenue_impact": "5000 EUR/Monat additional",
    "implementation_complexity": "low/medium/high",
    "time_to_value": "1-2 Wochen",
    "required_resources": ["Resource 1", "Resource 2"],
    "first_action": "Was HEUTE getan werden muss",
    "priority_score": 9
}""",
    },
    "strategic_partnership": {
        "output_dir": REVENUE_OPS_DIR,
        "priority": "high",
        "revenue_potential": 20000,
        "agent_id": "swarm-partnership",
        "squad": "sales",
        "system": "Du bist ein Strategic Partnership Agent. Antworte NUR mit validem JSON.",
        "prompt": """Identifiziere eine strategische Partnership fuer AI-Automation + BMA Nische.

Kontext: Maurice hat 16 Jahre BMA-Expertise + AI Automation Skills
Ziel: Win-Win Partnerschaften mit hohem Revenue-Potenzial

OUTPUT als JSON:
{
    "partner_type": "technology/distribution/complementary_service",
    "partner_profile": "Ideales Partner-Profil",
    "value_proposition": "Win-Win Proposition",
    "revenue_model": "Wie wird Geld verdient",
    "estimated_annual_value": "50000 EUR",
    "first_outreach_approach": "Wie kontaktieren",
    "partnership_effort": "Setup-Aufwand",
    "strategic_value": "Langfristige Bedeutung"
}""",
    },
}


# ── Concurrency-Berechnung basierend auf RAM ─────────────

def _detect_max_concurrent() -> int:
    """Erkennt verfuegbaren RAM und setzt Concurrency."""
    try:
        with open("/proc/meminfo", "r") as f:
            lines = f.readlines()
        info = {}
        for line in lines[:10]:
            parts = line.split()
            if len(parts) >= 2:
                info[parts[0].rstrip(":")] = int(parts[1])
        available_mb = info.get("MemAvailable", info.get("MemFree", 0)) / 1024

        # Ollama braucht ~3-5GB pro Modell
        # 1 concurrent Request = ~1GB extra RAM
        if available_mb < 4000:
            return 1  # Nur 1 Request gleichzeitig
        elif available_mb < 8000:
            return 2
        elif available_mb < 16000:
            return 3
        else:
            return 4  # Max 4 - Ollama limitiert
    except (FileNotFoundError, KeyError, ValueError):
        return 1  # Konservativ


def _detect_best_model() -> str:
    """Waehlt Modell basierend auf RAM."""
    try:
        with open("/proc/meminfo", "r") as f:
            line = f.readline()
        total_mb = int(line.split()[1]) / 1024
        if total_mb < 4000:
            return "phi:q4"           # ~2GB RAM
        elif total_mb < 8000:
            return "qwen2.5-coder:3b" # ~3GB RAM
        elif total_mb < 16000:
            return OLLAMA_MODEL       # ~5GB RAM (qwen2.5-coder:7b)
        else:
            return "deepseek-r1:8b"   # ~6GB RAM
    except (FileNotFoundError, ValueError):
        return OLLAMA_MODEL


# ── Self-Orchestrator (ersetzt Claude API) ───────────────

class SelfOrchestrator:
    """Analysiert Sprint-Performance mit Ollama statt Claude API.
    Komplett kostenlos, laeuft lokal."""

    def __init__(self, engine: 'OllamaEngine'):
        self.engine = engine
        self.insights = []

    async def analyze_sprint(self, stats: Dict, recent_results: List[Dict]) -> Dict:
        """Analysiert Sprint-Progress und gibt Empfehlungen."""
        if not self.engine:
            return self._rule_based_analysis(stats)

        # Kompakter Prompt fuer lokales Modell
        prompt = f"""Analysiere diesen AI-Agent-Sprint:
Completed: {stats.get('completed', 0)}/{stats.get('total_tasks', 0)}
Errors: {stats.get('failed', 0)}
Task-Verteilung: {json.dumps(stats.get('by_type', {}), indent=0)}
Laufzeit: {stats.get('elapsed_sec', 0):.0f}s

Letzte 3 Ergebnisse (Kurzform):
{json.dumps([r.get('type', '?') for r in recent_results[-3:]])}

Bewerte 1-10 und gib 2 konkrete Empfehlungen.
Antworte NUR mit JSON:
{{"rating": 7, "empfehlungen": ["Empfehlung 1", "Empfehlung 2"], "fokus_shift": "none/mehr_leads/mehr_content/mehr_nuggets"}}"""

        try:
            resp = await self.engine.chat(
                messages=[
                    {"role": "system", "content": "Du bist ein Sprint-Analyst. Kurz und praezise. Nur JSON."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=300,
                temperature=0.5,
            )
            if resp.success and resp.content:
                content = resp.content.strip()
                # JSON extrahieren
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                try:
                    analysis = json.loads(content.strip())
                    self.insights.append(analysis)
                    return analysis
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass

        return self._rule_based_analysis(stats)

    def _rule_based_analysis(self, stats: Dict) -> Dict:
        """Fallback: Regelbasierte Analyse ohne LLM."""
        completed = stats.get("completed", 0)
        failed = stats.get("failed", 0)
        total = completed + failed
        success_rate = (completed / max(total, 1)) * 100

        if success_rate >= 90:
            rating = 8
            empfehlungen = ["Weiter so - hohe Erfolgsrate", "Mehr high-value Tasks einplanen"]
        elif success_rate >= 70:
            rating = 6
            empfehlungen = ["Fehlerrate reduzieren", "Einfachere Prompts testen"]
        else:
            rating = 4
            empfehlungen = ["Ollama-Modell pruefen", "Concurrency reduzieren"]

        return {
            "rating": rating,
            "empfehlungen": empfehlungen,
            "fokus_shift": "none",
            "source": "rule_based",
        }


# ── Open Swarm Engine ────────────────────────────────────

class OpenSwarm:
    """Komplett kostenloser Agent-Schwarm mit Ollama.

    Ersetzt KimiSwarm500K:
    - Kimi: 500 concurrent, $0.0005/task, API Key noetig
    - Open: 1-4 concurrent, $0.00/task, laeuft offline
    """

    def __init__(self, model: Optional[str] = None):
        self.max_concurrent = _detect_max_concurrent()
        self.model = model or _detect_best_model()
        self.engine = OllamaEngine(model=self.model) if OllamaEngine else None
        self.guard = ResourceGuard() if ResourceGuard else None
        self.manager = AgentManager() if AgentManager else None
        self.orchestrator = SelfOrchestrator(self.engine) if self.engine else None
        self.semaphore = asyncio.Semaphore(self.max_concurrent)

        self.stats = {
            "total_tasks": 0,
            "completed": 0,
            "failed": 0,
            "tokens_used": 0,
            "cost_usd": 0.0,  # Immer 0!
            "start_time": None,
            "elapsed_sec": 0,
            "by_type": {t: 0 for t in TASK_TYPES},
            "sprint_type": "",
            "sprint_name": "",
            "orchestrations": 0,
            "estimated_revenue": 0.0,
        }
        self.recent_results = []

    # ── Task Execution ───────────────────────────────────

    def _parse_json_response(self, content: str) -> Optional[dict]:
        """Extrahiert JSON aus LLM-Antwort."""
        content = content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        try:
            return json.loads(content.strip())
        except (json.JSONDecodeError, IndexError):
            return None

    def _save_result(self, task_id: int, task_key: str, task_def: Dict, content: str):
        """Speichert Ergebnis als JSON-Datei."""
        output_dir = task_def.get("output_dir", OUTPUT_DIR)
        filename = output_dir / f"{task_key}_{task_id:06d}.json"

        parsed = self._parse_json_response(content)
        if parsed:
            data = {
                "task_id": task_id,
                "type": task_key,
                "priority": task_def.get("priority", "medium"),
                "revenue_potential": task_def.get("revenue_potential", 0),
                "timestamp": datetime.now().isoformat(),
                "model": self.model,
                "cost": 0.0,
                "provider": "ollama_local",
                "data": parsed,
            }
        else:
            data = {
                "task_id": task_id,
                "type": task_key,
                "timestamp": datetime.now().isoformat(),
                "model": self.model,
                "raw": content[:2000],
                "parse_error": "JSON extraction failed",
            }

        with open(filename, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.recent_results.append(data)
        if len(self.recent_results) > 50:
            self.recent_results.pop(0)

    async def execute_task(self, task_id: int, task_key: str, retries: int = 2) -> Dict:
        """Fuehrt einen einzelnen Task mit Ollama aus."""
        task_def = TASK_TYPES[task_key]

        # Resource Guard Check
        if self.guard:
            async with self.guard.check() as state:
                if state.paused:
                    return {"task_id": task_id, "type": task_key,
                            "status": "paused", "error": "System ueberlastet"}

        async with self.semaphore:
            for attempt in range(retries):
                try:
                    if not self.engine:
                        return {"task_id": task_id, "type": task_key,
                                "status": "error", "error": "OllamaEngine nicht verfuegbar"}

                    resp = await self.engine.chat(
                        messages=[
                            {"role": "system", "content": task_def["system"]},
                            {"role": "user", "content": task_def["prompt"]},
                        ],
                        max_tokens=500,
                        temperature=0.8,
                    )

                    if resp.success and resp.content:
                        self.stats["completed"] += 1
                        self.stats["tokens_used"] += resp.tokens
                        self.stats["by_type"][task_key] += 1
                        self.stats["estimated_revenue"] += task_def.get("revenue_potential", 0) * 0.05

                        self._save_result(task_id, task_key, task_def, resp.content)

                        # Agent Manager tracking
                        if self.manager:
                            agent_id = task_def.get("agent_id", f"swarm-{task_key}")
                            self.manager.record_task(agent_id, success=True)

                        return {
                            "task_id": task_id,
                            "type": task_key,
                            "status": "success",
                            "tokens": resp.tokens,
                            "duration_ms": resp.duration_ms,
                        }
                    else:
                        if attempt < retries - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        self.stats["failed"] += 1
                        if self.manager:
                            agent_id = task_def.get("agent_id", f"swarm-{task_key}")
                            self.manager.record_task(agent_id, success=False)
                        return {
                            "task_id": task_id, "type": task_key,
                            "status": "error", "error": resp.error,
                        }

                except asyncio.TimeoutError:
                    if attempt == retries - 1:
                        self.stats["failed"] += 1
                        return {"task_id": task_id, "type": task_key,
                                "status": "error", "error": "timeout"}
                    await asyncio.sleep(2)
                except Exception as e:
                    if attempt == retries - 1:
                        self.stats["failed"] += 1
                        return {"task_id": task_id, "type": task_key,
                                "status": "error", "error": str(e)[:200]}
                    await asyncio.sleep(2)

        self.stats["failed"] += 1
        return {"task_id": task_id, "type": task_key,
                "status": "error", "error": "max retries"}

    # ── Task-Auswahl (gewichteter Random) ────────────────

    def select_task_type(self, sprint_type: str) -> str:
        """Waehlt Task-Typ basierend auf Sprint-Gewichten."""
        sprint = SPRINT_TYPES.get(sprint_type, SPRINT_TYPES["revenue"])
        weights = sprint["task_weights"]

        task_keys = list(weights.keys())
        task_weights = [weights[k] for k in task_keys]
        total = sum(task_weights)

        r = random.uniform(0, total)
        cumulative = 0
        for key, weight in zip(task_keys, task_weights):
            cumulative += weight
            if r <= cumulative:
                return key

        return task_keys[0]

    # ── Sprint-Ausfuehrung ───────────────────────────────

    async def run_sprint(self, sprint_type: str = "revenue", total_tasks: int = 50):
        """Fuehrt einen fokussierten Sprint durch."""
        sprint = SPRINT_TYPES.get(sprint_type, SPRINT_TYPES["revenue"])
        self.stats["sprint_type"] = sprint_type
        self.stats["sprint_name"] = sprint["name"]
        self.stats["start_time"] = time.time()
        self.stats["total_tasks"] = total_tasks

        # Ollama Health Check
        if self.engine:
            healthy = await self.engine.health_check()
            if not healthy:
                print(f"\n  FEHLER: Ollama nicht erreichbar ({self.engine.host})")
                print(f"  Starte mit: ollama serve")
                return self.stats

        print(f"""
{'='*60}
   OPEN SWARM - {sprint['name'].upper()}
   Komplett kostenlos mit Ollama ($0)
{'='*60}
   Sprint:      {sprint['name']}
   Beschreibung: {sprint['beschreibung']}
   Tasks:       {total_tasks}
   Modell:      {self.model}
   Concurrent:  {self.max_concurrent}
   Kosten:      $0.00 (GRATIS!)
{'='*60}
""")

        # Batch-Ausfuehrung
        task_id = 0
        batch_size = self.max_concurrent
        orchestration_interval = max(10, total_tasks // 5)  # 5 Checkpoints

        try:
            while task_id < total_tasks:
                # Resource Check
                if self.guard:
                    state = self.guard.evaluate()
                    if state.paused:
                        print(f"  GUARD: Pausiert - warte auf Recovery...")
                        await asyncio.sleep(10)
                        continue

                # Batch erstellen
                batch_count = min(batch_size, total_tasks - task_id)
                tasks = []
                for i in range(batch_count):
                    task_key = self.select_task_type(sprint_type)
                    tasks.append(self.execute_task(task_id + i, task_key))

                # Batch ausfuehren
                results = await asyncio.gather(*tasks, return_exceptions=True)
                task_id += batch_count

                # Fortschritt
                self.stats["elapsed_sec"] = time.time() - self.stats["start_time"]
                pct = (self.stats["completed"] + self.stats["failed"]) / max(total_tasks, 1) * 100
                rate = self.stats["completed"] / max(self.stats["elapsed_sec"], 0.1)

                # Erfolgreiche Tasks zaehlen
                success_count = sum(1 for r in results
                                    if isinstance(r, dict) and r.get("status") == "success")
                fail_count = batch_count - success_count

                print(f"  [{pct:5.1f}%] {self.stats['completed']}/{total_tasks} "
                      f"({rate:.1f} tasks/min) "
                      f"Batch: {success_count} ok, {fail_count} fail")

                # Self-Orchestration Checkpoint
                if task_id > 0 and task_id % orchestration_interval == 0 and self.orchestrator:
                    analysis = await self.orchestrator.analyze_sprint(
                        self.stats, self.recent_results)
                    self.stats["orchestrations"] += 1
                    rating = analysis.get("rating", "?")
                    empfehlungen = analysis.get("empfehlungen", [])
                    print(f"\n  --- CHECKPOINT #{self.stats['orchestrations']} ---")
                    print(f"  Rating: {rating}/10")
                    for e in empfehlungen[:2]:
                        print(f"  > {e}")
                    print()

        except KeyboardInterrupt:
            print(f"\n  Sprint abgebrochen (Ctrl+C)")

        # Finale Stats
        self.stats["elapsed_sec"] = time.time() - self.stats["start_time"]
        self._print_summary()
        self._save_state()

        return self.stats

    # ── Daemon-Modus ─────────────────────────────────────

    async def run_daemon(self, sprint_type: str = "revenue",
                         tasks_per_sprint: int = 30,
                         interval: int = 3600):
        """Daemon: Automatische Sprints in regelmaessigen Intervallen."""
        sprint_count = 0
        print(f"""
{'='*60}
   OPEN SWARM DAEMON
   Automatische Sprints alle {interval}s
{'='*60}
   Sprint-Typ:      {sprint_type}
   Tasks/Sprint:    {tasks_per_sprint}
   Intervall:       {interval}s ({interval//60} Min)
   Modell:          {self.model}
   Kosten:          $0.00 pro Sprint (GRATIS!)
{'='*60}
""")

        try:
            while True:
                sprint_count += 1
                print(f"\n{'='*40}")
                print(f"  SPRINT #{sprint_count} startet...")
                print(f"{'='*40}")

                # Stats zuruecksetzen fuer neuen Sprint
                self.stats = {
                    "total_tasks": 0, "completed": 0, "failed": 0,
                    "tokens_used": 0, "cost_usd": 0.0, "start_time": None,
                    "elapsed_sec": 0, "by_type": {t: 0 for t in TASK_TYPES},
                    "sprint_type": sprint_type, "sprint_name": "",
                    "orchestrations": 0, "estimated_revenue": 0.0,
                }

                await self.run_sprint(sprint_type, tasks_per_sprint)

                print(f"\n  Naechster Sprint in {interval}s ({interval//60} Min)...")
                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            print(f"\n  Daemon gestoppt nach {sprint_count} Sprints.")

    # ── Output ───────────────────────────────────────────

    def _print_summary(self):
        """Sprint-Zusammenfassung ausgeben."""
        elapsed = self.stats.get("elapsed_sec", 0)
        rate = self.stats["completed"] / max(elapsed, 0.1) * 60  # pro Minute

        print(f"""
{'='*60}
   SPRINT ABGESCHLOSSEN
{'='*60}
   Typ:            {self.stats['sprint_name']}
   Completed:      {self.stats['completed']}/{self.stats['total_tasks']}
   Failed:         {self.stats['failed']}
   Tokens:         {self.stats['tokens_used']:,}
   Kosten:         $0.00 (GRATIS!)
   Dauer:          {elapsed:.0f}s ({elapsed/60:.1f} Min)
   Rate:           {rate:.1f} Tasks/Min
   Modell:         {self.model}
   Concurrent:     {self.max_concurrent}
   Orchestrations: {self.stats['orchestrations']}
   Est. Revenue:   EUR {self.stats['estimated_revenue']:,.0f}
   ---
   Task-Verteilung:""")
        for task_key, count in self.stats["by_type"].items():
            if count > 0:
                print(f"     {task_key:<25s}: {count}")
        print(f"""
   Output:         {OUTPUT_DIR}
{'='*60}
""")

    def _save_state(self):
        """Sprint-State persistent speichern."""
        # Aktuellen Sprint speichern
        sprint_file = OUTPUT_DIR / f"sprint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(sprint_file, "w") as f:
            json.dump({
                "sprint_type": self.stats["sprint_type"],
                "completed": self.stats["completed"],
                "failed": self.stats["failed"],
                "tokens_used": self.stats["tokens_used"],
                "cost_usd": 0.0,
                "estimated_revenue": self.stats["estimated_revenue"],
                "by_type": self.stats["by_type"],
                "duration_sec": self.stats["elapsed_sec"],
                "model": self.model,
                "concurrent": self.max_concurrent,
                "timestamp": datetime.now().isoformat(),
            }, f, indent=2)

        # Gesamt-State updaten
        state = {"total_sprints": 0, "total_tasks": 0, "total_tokens": 0,
                 "total_revenue": 0.0, "sprints": []}
        if SPRINT_STATE_FILE.exists():
            try:
                state = json.loads(SPRINT_STATE_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                pass

        state["total_sprints"] = state.get("total_sprints", 0) + 1
        state["total_tasks"] = state.get("total_tasks", 0) + self.stats["completed"]
        state["total_tokens"] = state.get("total_tokens", 0) + self.stats["tokens_used"]
        state["total_revenue"] = state.get("total_revenue", 0) + self.stats["estimated_revenue"]
        state["last_sprint"] = datetime.now().isoformat()
        state["model"] = self.model

        # Letzte 20 Sprints merken
        sprints = state.get("sprints", [])
        sprints.append({
            "type": self.stats["sprint_type"],
            "completed": self.stats["completed"],
            "timestamp": datetime.now().isoformat(),
        })
        state["sprints"] = sprints[-20:]

        SPRINT_STATE_FILE.write_text(json.dumps(state, indent=2))

    # ── Status ───────────────────────────────────────────

    @staticmethod
    def show_status():
        """Zeigt Gesamt-Status aller Sprints."""
        state = {"total_sprints": 0, "total_tasks": 0, "total_tokens": 0,
                 "total_revenue": 0.0}
        if SPRINT_STATE_FILE.exists():
            try:
                state = json.loads(SPRINT_STATE_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                pass

        # Output-Dateien zaehlen
        file_counts = {}
        for task_key, task_def in TASK_TYPES.items():
            d = task_def["output_dir"]
            if d.exists():
                count = len(list(d.glob(f"{task_key}_*.json")))
                if count > 0:
                    file_counts[task_key] = count

        # Resource Status
        resources = ""
        if sample_resources:
            r = sample_resources()
            resources = f"  CPU: {r['cpu_percent']}% | RAM: {r['ram_percent']}%"

        print(f"""
{'='*60}
   OPEN SWARM - STATUS
{'='*60}
   Sprints Total:   {state.get('total_sprints', 0)}
   Tasks Total:     {state.get('total_tasks', 0)}
   Tokens Total:    {state.get('total_tokens', 0):,}
   Kosten Total:    $0.00 (IMMER GRATIS!)
   Est. Revenue:    EUR {state.get('total_revenue', 0):,.0f}
   Letzter Sprint:  {state.get('last_sprint', 'nie')}
   Modell:          {state.get('model', 'unbekannt')}
{resources}
   ---
   Generierte Dateien:""")
        for key, count in file_counts.items():
            print(f"     {key:<25s}: {count} Files")
        if not file_counts:
            print(f"     (noch keine)")

        # Letzte Sprints
        sprints = state.get("sprints", [])
        if sprints:
            print(f"\n   Letzte Sprints:")
            for s in sprints[-5:]:
                print(f"     [{s.get('timestamp', '?')[:16]}] "
                      f"{s.get('type', '?')}: {s.get('completed', 0)} Tasks")

        print(f"\n   Sprint-Typen:")
        for key, sprint in SPRINT_TYPES.items():
            print(f"     {key:<12s}: {sprint['name']} - {sprint['beschreibung']}")

        print(f"{'='*60}\n")


# ── CLI ──────────────────────────────────────────────────

async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="OPEN SWARM - Kostenloser Agent-Schwarm mit Ollama ($0)")
    parser.add_argument("--sprint", type=str, default="revenue",
                        choices=list(SPRINT_TYPES.keys()),
                        help="Sprint-Typ (default: revenue)")
    parser.add_argument("--tasks", type=int, default=50,
                        help="Anzahl Tasks pro Sprint (default: 50)")
    parser.add_argument("--model", type=str, default=None,
                        help="Ollama Modell (auto-detect wenn leer)")
    parser.add_argument("--test", action="store_true",
                        help="Test-Modus (5 Tasks)")
    parser.add_argument("--daemon", action="store_true",
                        help="Daemon-Modus (automatische Sprints)")
    parser.add_argument("--interval", type=int, default=3600,
                        help="Daemon-Intervall in Sekunden (default: 3600)")
    parser.add_argument("--status", action="store_true",
                        help="Status anzeigen")
    args = parser.parse_args()

    if args.status:
        OpenSwarm.show_status()
        return

    swarm = OpenSwarm(model=args.model)

    if args.test:
        await swarm.run_sprint(args.sprint, total_tasks=5)
    elif args.daemon:
        await swarm.run_daemon(args.sprint, args.tasks, args.interval)
    else:
        await swarm.run_sprint(args.sprint, total_tasks=args.tasks)


if __name__ == "__main__":
    asyncio.run(main())
