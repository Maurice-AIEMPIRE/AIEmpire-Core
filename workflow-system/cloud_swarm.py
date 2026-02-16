#!/usr/bin/env python3
"""
CLOUD SWARM - Kostenlose Cloud-Rechenleistung fuer das Empire.
Nutzt Free Tiers von Cloud AI Providern: deren GPU-Power, $0 Kosten.

Architektur:
  CloudSwarm (Orchestrator)
  ├── ProviderPool
  │   ├── Groq         (schnellste Inference, Llama/Mixtral)
  │   ├── Cerebras     (ultra-schnell, Llama)
  │   ├── SambaNova    (schnell, Llama/DeepSeek)
  │   ├── HuggingFace  (viele Modelle, stabil)
  │   ├── Google Gemini(15 RPM free, sehr capable)
  │   ├── OpenRouter   (free Modelle verfuegbar)
  │   └── Ollama       (lokaler Fallback, $0)
  ├── RateLimiter (pro Provider, respektiert Free Tier Limits)
  ├── SmartRouter (waehlt besten verfuegbaren Provider)
  └── ResultCollector (sammelt + merged Ergebnisse)

Strategie:
  - Jeder Provider hat begrenzte Free Tier Limits
  - KOMBINIERT ergeben sie massive Throughput
  - Lokales System bleibt ENTLASTET (nur HTTP Calls)
  - Wenn ein Provider rate-limited → naechster uebernimmt
  - Kosten: $0.00 TOTAL

Usage:
  # Cloud Sprint starten
  python cloud_swarm.py --sprint revenue --tasks 100

  # Maximale Power (alle Provider parallel)
  python cloud_swarm.py --sprint content --tasks 200 --max-power

  # Nur bestimmte Provider nutzen
  python cloud_swarm.py --providers groq,cerebras --tasks 50

  # Status aller Provider
  python cloud_swarm.py --status

  # Provider testen (Health Check)
  python cloud_swarm.py --health

  # Daemon: Automatische Cloud Sprints
  python cloud_swarm.py --daemon --interval 1800
"""

import asyncio
import aiohttp
import json
import os
import sys
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque

# ── Modul-Imports (defensiv) ─────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

try:
    from ollama_engine import OllamaEngine
except ImportError:
    OllamaEngine = None

try:
    from resource_guard import ResourceGuard, sample_resources
except ImportError:
    ResourceGuard = None
    sample_resources = None

try:
    from agent_manager import AgentManager
except ImportError:
    AgentManager = None

# ── Output-Verzeichnisse ────────────────────────────────

OUTPUT_DIR = Path(__file__).parent / "cloud_output"
STATE_DIR = Path(__file__).parent / "state"
CLOUD_STATE_FILE = STATE_DIR / "cloud_swarm_state.json"

LEADS_DIR = OUTPUT_DIR / "leads"
CONTENT_DIR = OUTPUT_DIR / "content"
COMPETITORS_DIR = OUTPUT_DIR / "competitors"
NUGGETS_DIR = OUTPUT_DIR / "gold_nuggets"
REVENUE_OPS_DIR = OUTPUT_DIR / "revenue_operations"

for d in [OUTPUT_DIR, STATE_DIR, LEADS_DIR, CONTENT_DIR,
          COMPETITORS_DIR, NUGGETS_DIR, REVENUE_OPS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════
#  PROVIDER DEFINITIONEN - Alle Free Tier Cloud AI APIs
# ══════════════════════════════════════════════════════════

@dataclass
class ProviderConfig:
    """Konfiguration eines Cloud AI Providers."""
    name: str
    api_url: str
    api_key_env: str             # Environment Variable fuer API Key
    model: str                   # Bestes kostenloses Modell
    rpm_limit: int               # Requests pro Minute (Free Tier)
    tpd_limit: int               # Tokens pro Tag (Free Tier, 0 = unlimited)
    auth_header: str = "Authorization"
    auth_prefix: str = "Bearer"
    api_style: str = "openai"    # openai | gemini | huggingface
    max_tokens: int = 500
    temperature: float = 0.8
    priority: int = 10           # Hoeher = bevorzugt
    enabled: bool = True
    notes: str = ""


# Alle Cloud Provider mit ihren Free Tier Limits
CLOUD_PROVIDERS: Dict[str, ProviderConfig] = {
    "groq": ProviderConfig(
        name="Groq",
        api_url="https://api.groq.com/openai/v1/chat/completions",
        api_key_env="GROQ_API_KEY",
        model="llama-3.3-70b-versatile",
        rpm_limit=30,
        tpd_limit=14400,  # ~14.4K tokens/day free
        priority=10,       # Schnellste Inference
        notes="Schnellste Cloud-Inference. Free: 30 RPM, 14.4K tokens/Tag",
    ),
    "cerebras": ProviderConfig(
        name="Cerebras",
        api_url="https://api.cerebras.ai/v1/chat/completions",
        api_key_env="CEREBRAS_API_KEY",
        model="llama-3.3-70b",
        rpm_limit=30,
        tpd_limit=1000000,  # 1M tokens/Tag
        priority=9,
        notes="Ultra-schnell. Free: 30 RPM, ~1M tokens/Tag",
    ),
    "sambanova": ProviderConfig(
        name="SambaNova",
        api_url="https://api.sambanova.ai/v1/chat/completions",
        api_key_env="SAMBANOVA_API_KEY",
        model="Meta-Llama-3.1-70B-Instruct",
        rpm_limit=10,
        tpd_limit=100000,
        priority=8,
        notes="Free Cloud Tier. Llama + DeepSeek Modelle",
    ),
    "huggingface": ProviderConfig(
        name="HuggingFace",
        api_url="https://api-inference.huggingface.co/models/{model}",
        api_key_env="HF_TOKEN",
        model="mistralai/Mistral-7B-Instruct-v0.3",
        rpm_limit=10,
        tpd_limit=0,  # Rate-limited aber kein hartes Token Limit
        api_style="huggingface",
        priority=6,
        notes="Viele Modelle verfuegbar. Free: rate-limited",
    ),
    "gemini": ProviderConfig(
        name="Google Gemini",
        api_url="https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        api_key_env="GEMINI_API_KEY",
        model="gemini-2.0-flash",
        rpm_limit=15,
        tpd_limit=1000000,  # 1M tokens/Tag free
        api_style="gemini",
        auth_header="x-goog-api-key",
        auth_prefix="",
        priority=9,
        notes="Sehr capable. Free: 15 RPM, 1M tokens/Tag",
    ),
    "openrouter": ProviderConfig(
        name="OpenRouter",
        api_url="https://openrouter.ai/api/v1/chat/completions",
        api_key_env="OPENROUTER_API_KEY",
        model="meta-llama/llama-3.1-8b-instruct:free",
        rpm_limit=10,
        tpd_limit=0,
        priority=5,
        notes="Free Modelle verfuegbar (mit :free Suffix)",
    ),
}


# ══════════════════════════════════════════════════════════
#  RATE LIMITER - Respektiert Free Tier Limits
# ══════════════════════════════════════════════════════════

class RateLimiter:
    """Sliding Window Rate Limiter pro Provider."""

    def __init__(self, rpm_limit: int, tpd_limit: int = 0):
        self.rpm_limit = rpm_limit
        self.tpd_limit = tpd_limit
        self._request_times: deque = deque()
        self._tokens_today: int = 0
        self._day_start: float = time.time()
        self._consecutive_429s: int = 0

    def _cleanup_window(self):
        """Entfernt Eintraege aelter als 60 Sekunden."""
        cutoff = time.time() - 60
        while self._request_times and self._request_times[0] < cutoff:
            self._request_times.popleft()

    def _reset_daily_if_needed(self):
        """Reset Token-Zaehler wenn neuer Tag."""
        if time.time() - self._day_start > 86400:
            self._tokens_today = 0
            self._day_start = time.time()

    def can_request(self) -> bool:
        """Prueft ob ein Request erlaubt ist."""
        self._cleanup_window()
        self._reset_daily_if_needed()

        # RPM Check
        if len(self._request_times) >= self.rpm_limit:
            return False

        # Tages-Token Check
        if self.tpd_limit > 0 and self._tokens_today >= self.tpd_limit:
            return False

        # Backoff nach 429s
        if self._consecutive_429s >= 3:
            return False

        return True

    def record_request(self, tokens: int = 0):
        """Registriert einen erfolgreichen Request."""
        self._request_times.append(time.time())
        self._tokens_today += tokens
        self._consecutive_429s = 0

    def record_rate_limit(self):
        """Registriert einen 429 Rate Limit."""
        self._consecutive_429s += 1

    def reset_backoff(self):
        """Reset nach Erholung."""
        self._consecutive_429s = 0

    def wait_time(self) -> float:
        """Wie lange warten bis naechster Request moeglich."""
        self._cleanup_window()
        if len(self._request_times) < self.rpm_limit:
            return 0.0
        oldest = self._request_times[0]
        return max(0.0, 60.0 - (time.time() - oldest) + 0.5)

    def get_stats(self) -> Dict:
        """Status des Rate Limiters."""
        self._cleanup_window()
        self._reset_daily_if_needed()
        return {
            "requests_last_minute": len(self._request_times),
            "rpm_limit": self.rpm_limit,
            "tokens_today": self._tokens_today,
            "tpd_limit": self.tpd_limit,
            "consecutive_429s": self._consecutive_429s,
            "can_request": self.can_request(),
        }


# ══════════════════════════════════════════════════════════
#  CLOUD PROVIDER - Einzelner Provider mit Rate Limiting
# ══════════════════════════════════════════════════════════

class CloudProvider:
    """Ein einzelner Cloud AI Provider mit Rate Limiting."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.api_key = os.getenv(config.api_key_env, "")
        self.limiter = RateLimiter(config.rpm_limit, config.tpd_limit)
        self.stats = {
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "tokens_used": 0,
            "total_ms": 0,
            "rate_limits_hit": 0,
        }

    @property
    def available(self) -> bool:
        """Provider verfuegbar (API Key gesetzt + kann requesten)."""
        return bool(self.api_key) and self.config.enabled

    @property
    def can_request(self) -> bool:
        """Kann gerade einen Request machen."""
        return self.available and self.limiter.can_request()

    async def execute(self, system_prompt: str, user_prompt: str,
                      session: aiohttp.ClientSession) -> Tuple[bool, str, int, float]:
        """Fuehrt einen LLM-Call aus. Returns: (success, content, tokens, duration_ms)."""
        if not self.can_request:
            return False, "rate_limited", 0, 0

        start = time.monotonic()
        self.stats["requests"] += 1

        try:
            if self.config.api_style == "openai":
                return await self._call_openai_style(system_prompt, user_prompt, session, start)
            elif self.config.api_style == "gemini":
                return await self._call_gemini_style(system_prompt, user_prompt, session, start)
            elif self.config.api_style == "huggingface":
                return await self._call_huggingface_style(system_prompt, user_prompt, session, start)
            else:
                return False, f"unknown api_style: {self.config.api_style}", 0, 0

        except asyncio.TimeoutError:
            self.stats["failures"] += 1
            elapsed = (time.monotonic() - start) * 1000
            return False, "timeout", 0, elapsed
        except aiohttp.ClientError as e:
            self.stats["failures"] += 1
            elapsed = (time.monotonic() - start) * 1000
            return False, f"connection_error: {str(e)[:100]}", 0, elapsed
        except Exception as e:
            self.stats["failures"] += 1
            elapsed = (time.monotonic() - start) * 1000
            return False, f"error: {str(e)[:100]}", 0, elapsed

    async def _call_openai_style(self, system_prompt: str, user_prompt: str,
                                  session: aiohttp.ClientSession,
                                  start: float) -> Tuple[bool, str, int, float]:
        """OpenAI-kompatible API (Groq, Cerebras, SambaNova, OpenRouter)."""
        headers = {
            "Content-Type": "application/json",
            self.config.auth_header: f"{self.config.auth_prefix} {self.api_key}".strip(),
        }

        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        async with session.post(
            self.config.api_url, headers=headers, json=payload,
            timeout=aiohttp.ClientTimeout(total=60),
        ) as resp:
            elapsed = (time.monotonic() - start) * 1000

            if resp.status == 200:
                data = await resp.json()
                content = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 400)
                self.limiter.record_request(tokens)
                self.stats["successes"] += 1
                self.stats["tokens_used"] += tokens
                self.stats["total_ms"] += elapsed
                return True, content, tokens, elapsed

            elif resp.status == 429:
                self.limiter.record_rate_limit()
                self.stats["rate_limits_hit"] += 1
                return False, "rate_limited_429", 0, elapsed

            else:
                text = await resp.text()
                self.stats["failures"] += 1
                return False, f"HTTP {resp.status}: {text[:150]}", 0, elapsed

    async def _call_gemini_style(self, system_prompt: str, user_prompt: str,
                                  session: aiohttp.ClientSession,
                                  start: float) -> Tuple[bool, str, int, float]:
        """Google Gemini API."""
        url = self.config.api_url.format(model=self.config.model)
        url = f"{url}?key={self.api_key}"

        payload = {
            "contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}],
            "generationConfig": {
                "temperature": self.config.temperature,
                "maxOutputTokens": self.config.max_tokens,
            },
        }

        async with session.post(
            url, json=payload, timeout=aiohttp.ClientTimeout(total=60),
        ) as resp:
            elapsed = (time.monotonic() - start) * 1000

            if resp.status == 200:
                data = await resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                else:
                    content = ""
                tokens = data.get("usageMetadata", {}).get("totalTokenCount", 400)
                self.limiter.record_request(tokens)
                self.stats["successes"] += 1
                self.stats["tokens_used"] += tokens
                self.stats["total_ms"] += elapsed
                return True, content, tokens, elapsed

            elif resp.status == 429:
                self.limiter.record_rate_limit()
                self.stats["rate_limits_hit"] += 1
                return False, "rate_limited_429", 0, elapsed

            else:
                text = await resp.text()
                self.stats["failures"] += 1
                return False, f"HTTP {resp.status}: {text[:150]}", 0, elapsed

    async def _call_huggingface_style(self, system_prompt: str, user_prompt: str,
                                       session: aiohttp.ClientSession,
                                       start: float) -> Tuple[bool, str, int, float]:
        """HuggingFace Inference API."""
        url = self.config.api_url.format(model=self.config.model)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "inputs": f"<s>[INST] {system_prompt}\n\n{user_prompt} [/INST]",
            "parameters": {
                "max_new_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "return_full_text": False,
            },
        }

        async with session.post(
            url, headers=headers, json=payload,
            timeout=aiohttp.ClientTimeout(total=90),
        ) as resp:
            elapsed = (time.monotonic() - start) * 1000

            if resp.status == 200:
                data = await resp.json()
                if isinstance(data, list) and data:
                    content = data[0].get("generated_text", "")
                elif isinstance(data, dict):
                    content = data.get("generated_text", str(data))
                else:
                    content = str(data)
                tokens = len(content.split()) * 2  # Grobe Schaetzung
                self.limiter.record_request(tokens)
                self.stats["successes"] += 1
                self.stats["tokens_used"] += tokens
                self.stats["total_ms"] += elapsed
                return True, content, tokens, elapsed

            elif resp.status == 429 or resp.status == 503:
                self.limiter.record_rate_limit()
                self.stats["rate_limits_hit"] += 1
                return False, "rate_limited_429", 0, elapsed

            else:
                text = await resp.text()
                self.stats["failures"] += 1
                return False, f"HTTP {resp.status}: {text[:150]}", 0, elapsed

    async def health_check(self, session: aiohttp.ClientSession) -> bool:
        """Schneller Health Check - einfacher Prompt."""
        if not self.available:
            return False
        success, content, _, _ = await self.execute(
            "Antworte mit genau einem Wort: OK",
            "Status check. Antworte: OK",
            session,
        )
        return success

    def get_status(self) -> Dict:
        """Provider-Status zusammenfassen."""
        avg_ms = self.stats["total_ms"] / max(self.stats["successes"], 1)
        return {
            "name": self.config.name,
            "available": self.available,
            "can_request": self.can_request,
            "api_key_set": bool(self.api_key),
            "model": self.config.model,
            "priority": self.config.priority,
            "stats": {**self.stats, "avg_ms": round(avg_ms, 1)},
            "limiter": self.limiter.get_stats(),
            "notes": self.config.notes,
        }


# ══════════════════════════════════════════════════════════
#  SMART ROUTER - Waehlt besten verfuegbaren Provider
# ══════════════════════════════════════════════════════════

class SmartRouter:
    """Routet Tasks zum besten verfuegbaren Provider."""

    def __init__(self, providers: Dict[str, CloudProvider]):
        self.providers = providers
        self._fallback_order: List[str] = []
        self._update_order()

    def _update_order(self):
        """Sortiert Provider nach Prioritaet."""
        available = [(name, p) for name, p in self.providers.items() if p.available]
        available.sort(key=lambda x: x[1].config.priority, reverse=True)
        self._fallback_order = [name for name, _ in available]

    def get_best_provider(self) -> Optional[str]:
        """Waehlt den besten verfuegbaren Provider."""
        for name in self._fallback_order:
            provider = self.providers[name]
            if provider.can_request:
                return name
        return None

    def get_all_available(self) -> List[str]:
        """Alle Provider die gerade requesten koennen."""
        return [name for name in self._fallback_order
                if self.providers[name].can_request]

    def report_failure(self, provider_name: str):
        """Meldet einen Failure - Provider temporaer deprioritisieren."""
        # Einfach: Verschiebe ans Ende der Liste
        if provider_name in self._fallback_order:
            self._fallback_order.remove(provider_name)
            self._fallback_order.append(provider_name)


# ══════════════════════════════════════════════════════════
#  TASK DEFINITIONEN (gleich wie Open Swarm)
# ══════════════════════════════════════════════════════════

CLOUD_TASK_TYPES = {
    "high_value_lead": {
        "output_dir": LEADS_DIR,
        "priority": "high",
        "revenue_potential": 5000,
        "agent_id": "cloud-lead-finder",
        "system": "Du bist ein B2B Lead Research Agent. Antworte NUR mit validem JSON.",
        "prompt": """Generiere ein REALISTISCHES Premium-Lead-Profil.
Zielgruppe: Unternehmen die 10K-100K+ EUR fuer AI-Automation ausgeben.

OUTPUT als JSON:
{
    "handle": "@firma",
    "company": "Firmenname",
    "industry": "Branche",
    "company_size": "50-500",
    "pain_points": ["Problem 1", "Problem 2", "Problem 3"],
    "ai_opportunity": "Konkrete AI-Loesung",
    "estimated_project_value": "25000 EUR",
    "outreach_hook": "Personalisierter erster Satz",
    "bant_score": 8
}""",
    },
    "viral_content": {
        "output_dir": CONTENT_DIR,
        "priority": "high",
        "revenue_potential": 1000,
        "agent_id": "cloud-content-x",
        "system": "Du bist ein viraler Content Creator. Antworte NUR mit validem JSON.",
        "prompt": """Generiere eine VIRALE X/Twitter Content-Idee.
Autor: Maurice Pfeifer, Elektrotechnikmeister + AI Automation Experte

OUTPUT als JSON:
{
    "format": "thread/single/story",
    "hook": "Attention-grabbing erster Satz (max 280 Zeichen)",
    "main_content": "Hauptinhalt mit konkreten Zahlen",
    "cta": "Call to Action mit Lead-Magnet",
    "hashtags": ["#AI", "#Automation", "#BuildInPublic"],
    "viral_score": 8
}""",
    },
    "competitor_intel": {
        "output_dir": COMPETITORS_DIR,
        "priority": "medium",
        "revenue_potential": 2000,
        "agent_id": "cloud-intel",
        "system": "Du bist ein Competitive Intelligence Agent. Antworte NUR mit validem JSON.",
        "prompt": """Analysiere einen FIKTIVEN AI-Automation Konkurrenten.

OUTPUT als JSON:
{
    "name": "Konkurrenten Name",
    "positioning": "Ihr USP",
    "services": ["Service 1", "Service 2"],
    "weaknesses": ["Schwaeche 1", "Schwaeche 2"],
    "market_gap": "Opportunity fuer Maurice",
    "counter_strategy": "Wie Maurice gewinnt"
}""",
    },
    "gold_nugget": {
        "output_dir": NUGGETS_DIR,
        "priority": "high",
        "revenue_potential": 10000,
        "agent_id": "cloud-nugget",
        "system": "Du bist ein Business Intelligence Agent. Antworte NUR mit validem JSON.",
        "prompt": """Extrahiere ein HIGH-VALUE Gold Nugget - sofort umsetzbare Business-Erkenntnis.
Kontext: AI Automation + BMA Nische, Ziel 100M EUR

OUTPUT als JSON:
{
    "category": "monetization/scaling/automation/arbitrage",
    "title": "Actionable Titel",
    "insight": "Konkrete Erkenntnis mit Zahlen",
    "implementation_steps": ["Schritt 1", "Schritt 2", "Schritt 3"],
    "estimated_revenue": "10000 EUR/Monat",
    "roi_multiplier": "20x"
}""",
    },
    "revenue_optimization": {
        "output_dir": REVENUE_OPS_DIR,
        "priority": "critical",
        "revenue_potential": 15000,
        "agent_id": "cloud-revenue",
        "system": "Du bist ein Revenue Optimization Agent. Antworte NUR mit validem JSON.",
        "prompt": """Identifiziere eine konkrete Revenue-Optimierung.
Channels: Gumroad (27-149 EUR), Fiverr/Upwork, BMA+AI Consulting (2000-10000 EUR)

OUTPUT als JSON:
{
    "optimization_type": "pricing/upsell/automation/new_stream",
    "current_state": "Problem",
    "optimized_state": "Loesung",
    "revenue_impact": "5000 EUR/Monat",
    "time_to_value": "1-2 Wochen",
    "first_action": "Was HEUTE getan werden muss"
}""",
    },
    "strategic_partnership": {
        "output_dir": REVENUE_OPS_DIR,
        "priority": "high",
        "revenue_potential": 20000,
        "agent_id": "cloud-partnership",
        "system": "Du bist ein Partnership Agent. Antworte NUR mit validem JSON.",
        "prompt": """Identifiziere eine strategische Partnership fuer AI+BMA Nische.

OUTPUT als JSON:
{
    "partner_type": "technology/distribution/service",
    "partner_profile": "Ideales Partner-Profil",
    "value_proposition": "Win-Win Proposition",
    "revenue_model": "Wie wird Geld verdient",
    "estimated_annual_value": "50000 EUR",
    "first_outreach_approach": "Wie kontaktieren"
}""",
    },
}

# Sprint-Typen (gleich wie Open Swarm fuer Kompatibilitaet)
CLOUD_SPRINT_TYPES = {
    "revenue": {"name": "Revenue Sprint", "weights": {
        "revenue_optimization": 3.0, "gold_nugget": 2.0, "high_value_lead": 2.0,
        "strategic_partnership": 1.5, "viral_content": 1.0, "competitor_intel": 0.5}},
    "content": {"name": "Content Sprint", "weights": {
        "viral_content": 4.0, "gold_nugget": 1.0, "revenue_optimization": 1.0,
        "high_value_lead": 0.5, "strategic_partnership": 0.3, "competitor_intel": 0.2}},
    "leads": {"name": "Lead Sprint", "weights": {
        "high_value_lead": 4.0, "strategic_partnership": 2.0, "competitor_intel": 1.5,
        "viral_content": 1.0, "revenue_optimization": 0.5, "gold_nugget": 0.5}},
    "intel": {"name": "Intelligence Sprint", "weights": {
        "competitor_intel": 4.0, "gold_nugget": 3.0, "strategic_partnership": 2.0,
        "revenue_optimization": 1.0, "high_value_lead": 0.5, "viral_content": 0.5}},
    "products": {"name": "Product Sprint", "weights": {
        "gold_nugget": 3.0, "revenue_optimization": 3.0, "strategic_partnership": 1.5,
        "viral_content": 1.0, "high_value_lead": 1.0, "competitor_intel": 1.0}},
}


# ══════════════════════════════════════════════════════════
#  CLOUD SWARM ENGINE
# ══════════════════════════════════════════════════════════

class CloudSwarm:
    """Cloud-basierter Agent-Schwarm - nutzt Free Tiers fuer $0."""

    def __init__(self, provider_filter: Optional[List[str]] = None):
        # Provider initialisieren
        self.providers: Dict[str, CloudProvider] = {}
        for name, config in CLOUD_PROVIDERS.items():
            if provider_filter and name not in provider_filter:
                continue
            self.providers[name] = CloudProvider(config)

        # Ollama als lokaler Fallback
        self.ollama = OllamaEngine() if OllamaEngine else None

        # Smart Router
        self.router = SmartRouter(self.providers)

        # Agent Manager fuer Revenue Tracking
        self.manager = AgentManager() if AgentManager else None

        # Session (shared fuer alle Requests)
        self.session: Optional[aiohttp.ClientSession] = None

        # Stats
        self.stats = {
            "total_tasks": 0,
            "completed": 0,
            "failed": 0,
            "tokens_used": 0,
            "cost_usd": 0.0,  # IMMER 0!
            "start_time": None,
            "elapsed_sec": 0,
            "by_type": {t: 0 for t in CLOUD_TASK_TYPES},
            "by_provider": {},
            "sprint_type": "",
            "estimated_revenue": 0.0,
        }
        self.recent_results: List[Dict] = []

    async def _init_session(self):
        """Shared HTTP Session erstellen."""
        if not self.session:
            connector = aiohttp.TCPConnector(limit=20, limit_per_host=10)
            self.session = aiohttp.ClientSession(connector=connector)

    async def _close_session(self):
        """Session schliessen."""
        if self.session:
            await self.session.close()
            self.session = None

    # ── Task Execution ───────────────────────────────────

    def _parse_json(self, content: str) -> Optional[dict]:
        """JSON aus LLM-Antwort extrahieren."""
        content = content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        try:
            return json.loads(content.strip())
        except (json.JSONDecodeError, IndexError):
            return None

    def _save_result(self, task_id: int, task_key: str, provider_name: str,
                     content: str, tokens: int, duration_ms: float):
        """Speichert Ergebnis als JSON-Datei."""
        task_def = CLOUD_TASK_TYPES[task_key]
        output_dir = task_def.get("output_dir", OUTPUT_DIR)
        filename = output_dir / f"cloud_{task_key}_{task_id:06d}.json"

        parsed = self._parse_json(content)
        data = {
            "task_id": task_id,
            "type": task_key,
            "provider": provider_name,
            "priority": task_def.get("priority", "medium"),
            "revenue_potential": task_def.get("revenue_potential", 0),
            "timestamp": datetime.now().isoformat(),
            "tokens": tokens,
            "duration_ms": round(duration_ms, 1),
            "cost": 0.0,
        }
        if parsed:
            data["data"] = parsed
        else:
            data["raw"] = content[:2000]
            data["parse_error"] = "JSON extraction failed"

        with open(filename, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.recent_results.append(data)
        if len(self.recent_results) > 50:
            self.recent_results.pop(0)

    async def execute_task(self, task_id: int, task_key: str) -> Dict:
        """Fuehrt einen Task mit dem besten verfuegbaren Provider aus."""
        task_def = CLOUD_TASK_TYPES[task_key]
        system_prompt = task_def["system"]
        user_prompt = task_def["prompt"]

        # Versuche Cloud Provider (Reihenfolge: bester zuerst)
        tried_providers = []
        for _ in range(len(self.providers) + 1):
            provider_name = self.router.get_best_provider()
            if not provider_name or provider_name in tried_providers:
                break

            tried_providers.append(provider_name)
            provider = self.providers[provider_name]

            success, content, tokens, duration_ms = await provider.execute(
                system_prompt, user_prompt, self.session)

            if success:
                self.stats["completed"] += 1
                self.stats["tokens_used"] += tokens
                self.stats["by_type"][task_key] += 1
                self.stats["by_provider"][provider_name] = \
                    self.stats["by_provider"].get(provider_name, 0) + 1
                self.stats["estimated_revenue"] += task_def.get("revenue_potential", 0) * 0.05

                self._save_result(task_id, task_key, provider_name,
                                  content, tokens, duration_ms)

                # Agent Manager tracking
                if self.manager:
                    agent_id = task_def.get("agent_id", f"cloud-{task_key}")
                    self.manager.record_task(agent_id, success=True)

                return {
                    "task_id": task_id, "type": task_key,
                    "status": "success", "provider": provider_name,
                    "tokens": tokens, "duration_ms": duration_ms,
                }

            # Provider hat gefailed - naechsten versuchen
            if "rate_limited" in content:
                self.router.report_failure(provider_name)
                continue
            # Anderer Fehler - auch naechsten versuchen
            self.router.report_failure(provider_name)
            continue

        # Alle Cloud Provider exhausted → Ollama Fallback
        if self.ollama:
            try:
                resp = await self.ollama.chat(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=500,
                    temperature=0.8,
                )
                if resp.success and resp.content:
                    self.stats["completed"] += 1
                    self.stats["tokens_used"] += resp.tokens
                    self.stats["by_type"][task_key] += 1
                    self.stats["by_provider"]["ollama_fallback"] = \
                        self.stats["by_provider"].get("ollama_fallback", 0) + 1

                    self._save_result(task_id, task_key, "ollama_fallback",
                                      resp.content, resp.tokens, resp.duration_ms)
                    return {
                        "task_id": task_id, "type": task_key,
                        "status": "success", "provider": "ollama_fallback",
                        "tokens": resp.tokens,
                    }
            except Exception:
                pass

        # Komplett gescheitert
        self.stats["failed"] += 1
        return {
            "task_id": task_id, "type": task_key,
            "status": "error", "error": f"all providers exhausted: {tried_providers}",
        }

    # ── Task-Auswahl ─────────────────────────────────────

    def select_task_type(self, sprint_type: str) -> str:
        """Waehlt Task-Typ basierend auf Sprint-Gewichten."""
        sprint = CLOUD_SPRINT_TYPES.get(sprint_type, CLOUD_SPRINT_TYPES["revenue"])
        weights = sprint["weights"]
        keys = list(weights.keys())
        vals = [weights[k] for k in keys]
        total = sum(vals)
        r = random.uniform(0, total)
        cumulative = 0
        for key, weight in zip(keys, vals):
            cumulative += weight
            if r <= cumulative:
                return key
        return keys[0]

    # ── Sprint-Ausfuehrung ───────────────────────────────

    async def run_sprint(self, sprint_type: str = "revenue",
                         total_tasks: int = 100,
                         max_power: bool = False):
        """Cloud Sprint - nutzt alle verfuegbaren Provider."""
        sprint = CLOUD_SPRINT_TYPES.get(sprint_type, CLOUD_SPRINT_TYPES["revenue"])
        self.stats["sprint_type"] = sprint_type
        self.stats["start_time"] = time.time()
        self.stats["total_tasks"] = total_tasks

        await self._init_session()

        # Verfuegbare Provider zaehlen
        available = [n for n, p in self.providers.items() if p.available]
        configured = [n for n, p in self.providers.items() if p.api_key]

        print(f"""
{'='*60}
   CLOUD SWARM - {sprint['name'].upper()}
   Free Cloud Power fuer das Empire
{'='*60}
   Sprint:     {sprint['name']}
   Tasks:      {total_tasks}
   Provider:   {len(available)} aktiv / {len(self.providers)} konfiguriert
   Aktiv:      {', '.join(available) if available else 'KEINE! API Keys setzen.'}
   Max Power:  {'JA' if max_power else 'Nein'}
   Kosten:     $0.00 (Free Tier only!)
{'='*60}
""")

        if not available:
            print("  KEINE PROVIDER VERFUEGBAR!")
            print("  Setze mindestens einen API Key:")
            for name, config in CLOUD_PROVIDERS.items():
                print(f"    export {config.api_key_env}='dein-key'  # {config.name}")
            print()
            await self._close_session()
            return self.stats

        # Concurrency basierend auf Anzahl Provider
        concurrency = min(len(available) * 3, 15) if max_power else min(len(available) * 2, 8)
        semaphore = asyncio.Semaphore(concurrency)

        async def bounded_task(task_id: int, task_key: str):
            async with semaphore:
                return await self.execute_task(task_id, task_key)

        try:
            # Tasks in Batches ausfuehren
            batch_size = concurrency
            task_id = 0

            while task_id < total_tasks:
                batch_count = min(batch_size, total_tasks - task_id)
                tasks = []
                for i in range(batch_count):
                    task_key = self.select_task_type(sprint_type)
                    tasks.append(bounded_task(task_id + i, task_key))

                results = await asyncio.gather(*tasks, return_exceptions=True)
                task_id += batch_count

                # Stats updaten
                self.stats["elapsed_sec"] = time.time() - self.stats["start_time"]
                done = self.stats["completed"] + self.stats["failed"]
                pct = done / max(total_tasks, 1) * 100
                rate = self.stats["completed"] / max(self.stats["elapsed_sec"], 0.1) * 60

                # Provider-Verteilung
                providers_used = set()
                for r in results:
                    if isinstance(r, dict) and r.get("provider"):
                        providers_used.add(r["provider"])

                print(f"  [{pct:5.1f}%] {self.stats['completed']}/{total_tasks} "
                      f"({rate:.1f}/min) "
                      f"via {', '.join(providers_used) if providers_used else '?'}")

                # Kurze Pause zwischen Batches (Rate Limits respektieren)
                await asyncio.sleep(0.5)

        except KeyboardInterrupt:
            print(f"\n  Sprint abgebrochen (Ctrl+C)")
        finally:
            await self._close_session()

        self.stats["elapsed_sec"] = time.time() - self.stats["start_time"]
        self._print_summary()
        self._save_state()

        return self.stats

    # ── Daemon ───────────────────────────────────────────

    async def run_daemon(self, sprint_type: str = "revenue",
                         tasks_per_sprint: int = 50,
                         interval: int = 1800):
        """Daemon: Automatische Cloud Sprints."""
        sprint_count = 0
        print(f"""
{'='*60}
   CLOUD SWARM DAEMON
   Automatische Sprints alle {interval//60} Min
{'='*60}
   Sprint-Typ:      {sprint_type}
   Tasks/Sprint:    {tasks_per_sprint}
   Intervall:       {interval}s ({interval//60} Min)
   Kosten:          $0.00 pro Sprint
{'='*60}
""")

        try:
            while True:
                sprint_count += 1
                print(f"\n  CLOUD SPRINT #{sprint_count}...")
                self.stats = {
                    "total_tasks": 0, "completed": 0, "failed": 0,
                    "tokens_used": 0, "cost_usd": 0.0, "start_time": None,
                    "elapsed_sec": 0, "by_type": {t: 0 for t in CLOUD_TASK_TYPES},
                    "by_provider": {}, "sprint_type": sprint_type,
                    "estimated_revenue": 0.0,
                }
                await self.run_sprint(sprint_type, tasks_per_sprint)
                print(f"\n  Naechster Sprint in {interval//60} Min...")
                await asyncio.sleep(interval)
        except KeyboardInterrupt:
            print(f"\n  Daemon gestoppt nach {sprint_count} Sprints.")

    # ── Health Check ─────────────────────────────────────

    async def health_check(self):
        """Testet alle Provider."""
        await self._init_session()
        print(f"\n{'='*60}")
        print(f"   CLOUD SWARM - HEALTH CHECK")
        print(f"{'='*60}\n")

        for name, provider in self.providers.items():
            if not provider.api_key:
                print(f"  [{name:>12s}]  SKIP  (kein API Key: {provider.config.api_key_env})")
                continue

            print(f"  [{name:>12s}]  testing...", end="", flush=True)
            try:
                ok = await provider.health_check(self.session)
                if ok:
                    print(f"\r  [{name:>12s}]  OK    ({provider.config.model})")
                else:
                    print(f"\r  [{name:>12s}]  FAIL  (Request fehlgeschlagen)")
            except Exception as e:
                print(f"\r  [{name:>12s}]  ERROR ({str(e)[:50]})")

        await self._close_session()
        print(f"\n{'='*60}\n")

    # ── Output ───────────────────────────────────────────

    def _print_summary(self):
        """Sprint-Zusammenfassung."""
        elapsed = self.stats.get("elapsed_sec", 0)
        rate = self.stats["completed"] / max(elapsed, 0.1) * 60

        print(f"""
{'='*60}
   CLOUD SPRINT ABGESCHLOSSEN
{'='*60}
   Completed:      {self.stats['completed']}/{self.stats['total_tasks']}
   Failed:         {self.stats['failed']}
   Tokens:         {self.stats['tokens_used']:,}
   Kosten:         $0.00 (GRATIS!)
   Dauer:          {elapsed:.0f}s ({elapsed/60:.1f} Min)
   Rate:           {rate:.1f} Tasks/Min
   Est. Revenue:   EUR {self.stats['estimated_revenue']:,.0f}
   ---
   Provider-Verteilung:""")
        for prov, count in sorted(self.stats["by_provider"].items(),
                                   key=lambda x: x[1], reverse=True):
            print(f"     {prov:<20s}: {count} Tasks")
        print(f"""
   Task-Verteilung:""")
        for ttype, count in self.stats["by_type"].items():
            if count > 0:
                print(f"     {ttype:<25s}: {count}")
        print(f"""
   Output:         {OUTPUT_DIR}
{'='*60}
""")

    def _save_state(self):
        """State persistent speichern."""
        # Sprint-Datei
        sprint_file = OUTPUT_DIR / f"cloud_sprint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(sprint_file, "w") as f:
            json.dump({
                "sprint_type": self.stats["sprint_type"],
                "completed": self.stats["completed"],
                "failed": self.stats["failed"],
                "tokens_used": self.stats["tokens_used"],
                "cost_usd": 0.0,
                "by_provider": self.stats["by_provider"],
                "by_type": self.stats["by_type"],
                "duration_sec": self.stats["elapsed_sec"],
                "timestamp": datetime.now().isoformat(),
            }, f, indent=2)

        # Gesamt-State
        state = {"total_sprints": 0, "total_tasks": 0, "total_tokens": 0,
                 "sprints": []}
        if CLOUD_STATE_FILE.exists():
            try:
                state = json.loads(CLOUD_STATE_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                pass

        state["total_sprints"] = state.get("total_sprints", 0) + 1
        state["total_tasks"] = state.get("total_tasks", 0) + self.stats["completed"]
        state["total_tokens"] = state.get("total_tokens", 0) + self.stats["tokens_used"]
        state["last_sprint"] = datetime.now().isoformat()

        sprints = state.get("sprints", [])
        sprints.append({
            "type": self.stats["sprint_type"],
            "completed": self.stats["completed"],
            "providers": self.stats["by_provider"],
            "timestamp": datetime.now().isoformat(),
        })
        state["sprints"] = sprints[-30:]

        CLOUD_STATE_FILE.write_text(json.dumps(state, indent=2))

    # ── Status ───────────────────────────────────────────

    @staticmethod
    def show_status():
        """Zeigt Cloud Swarm Status."""
        state = {"total_sprints": 0, "total_tasks": 0, "total_tokens": 0}
        if CLOUD_STATE_FILE.exists():
            try:
                state = json.loads(CLOUD_STATE_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                pass

        # Provider-Status
        providers_status = []
        for name, config in CLOUD_PROVIDERS.items():
            api_key = os.getenv(config.api_key_env, "")
            providers_status.append({
                "name": config.name,
                "key": name,
                "has_key": bool(api_key),
                "env_var": config.api_key_env,
                "model": config.model,
                "rpm": config.rpm_limit,
                "priority": config.priority,
                "notes": config.notes,
            })

        # Output-Dateien zaehlen
        file_counts = {}
        for task_key, task_def in CLOUD_TASK_TYPES.items():
            d = task_def["output_dir"]
            if d.exists():
                count = len(list(d.glob(f"cloud_{task_key}_*.json")))
                if count > 0:
                    file_counts[task_key] = count

        active_count = sum(1 for p in providers_status if p["has_key"])

        print(f"""
{'='*60}
   CLOUD SWARM - STATUS
   Free Cloud Power fuer das Empire
{'='*60}
   Sprints Total:   {state.get('total_sprints', 0)}
   Tasks Total:     {state.get('total_tasks', 0)}
   Tokens Total:    {state.get('total_tokens', 0):,}
   Kosten Total:    $0.00 (IMMER GRATIS!)
   Letzter Sprint:  {state.get('last_sprint', 'nie')}

   PROVIDER ({active_count}/{len(providers_status)} aktiv):""")

        for p in providers_status:
            icon = "ON " if p["has_key"] else "---"
            print(f"   [{icon}] {p['name']:<15s} {p['model']:<35s} {p['rpm']:>3d} RPM")
            if not p["has_key"]:
                print(f"         export {p['env_var']}='...'")

        if not any(p["has_key"] for p in providers_status):
            print(f"""
   KEINE PROVIDER AKTIV!
   Registriere dich kostenlos und setze API Keys:""")
            for p in providers_status:
                print(f"     export {p['env_var']}='dein-key'")

        print(f"""
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
                provs = ", ".join(s.get("providers", {}).keys())
                print(f"     [{s.get('timestamp', '?')[:16]}] "
                      f"{s.get('type', '?')}: {s.get('completed', 0)} Tasks "
                      f"via {provs}")

        print(f"""
   QUICK START:
     1. API Key(s) setzen (mindestens 1):
        export GROQ_API_KEY='...'         # groq.com (schnellste)
        export GEMINI_API_KEY='...'       # aistudio.google.com
        export CEREBRAS_API_KEY='...'     # cerebras.ai
     2. Health Check:  python cloud_swarm.py --health
     3. Test Sprint:   python cloud_swarm.py --test
     4. Voller Sprint: python cloud_swarm.py --sprint revenue --tasks 100
{'='*60}
""")


# ══════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════

async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="CLOUD SWARM - Kostenlose Cloud-Power ($0)")
    parser.add_argument("--sprint", type=str, default="revenue",
                        choices=list(CLOUD_SPRINT_TYPES.keys()),
                        help="Sprint-Typ (default: revenue)")
    parser.add_argument("--tasks", type=int, default=100,
                        help="Anzahl Tasks (default: 100)")
    parser.add_argument("--providers", type=str, default=None,
                        help="Komma-getrennte Provider-Liste (z.B. groq,cerebras)")
    parser.add_argument("--max-power", action="store_true",
                        help="Maximale Concurrency (alle Provider voll)")
    parser.add_argument("--test", action="store_true",
                        help="Test-Modus (10 Tasks)")
    parser.add_argument("--health", action="store_true",
                        help="Health Check aller Provider")
    parser.add_argument("--daemon", action="store_true",
                        help="Daemon-Modus")
    parser.add_argument("--interval", type=int, default=1800,
                        help="Daemon-Intervall in Sekunden (default: 1800)")
    parser.add_argument("--status", action="store_true",
                        help="Status anzeigen")
    args = parser.parse_args()

    if args.status:
        CloudSwarm.show_status()
        return

    provider_filter = args.providers.split(",") if args.providers else None
    swarm = CloudSwarm(provider_filter=provider_filter)

    if args.health:
        await swarm.health_check()
    elif args.test:
        await swarm.run_sprint(args.sprint, total_tasks=10)
    elif args.daemon:
        await swarm.run_daemon(args.sprint, args.tasks, args.interval)
    else:
        await swarm.run_sprint(args.sprint, args.tasks, args.max_power)


if __name__ == "__main__":
    asyncio.run(main())
