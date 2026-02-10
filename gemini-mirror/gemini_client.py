"""
Gemini Client - Hybrid API Client fuer Google Gemini
Spiegelt das KimiClient Pattern: Local Ollama → Gemini Flash → Gemini Pro

Fallback-Kette:
1. Ollama (lokal, kostenlos)
2. Gemini Flash (schnell, guenstig)
3. Gemini Pro (stark, teurer)
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

from config import (
    GEMINI_API_KEY,
    GEMINI_BASE_URL,
    GEMINI_MODELS,
    RESOURCE_LIMITS,
)

logger = logging.getLogger("gemini-client")


class CostTracker:
    """Verfolgt API-Kosten pro Tag und stoppt bei Limit."""

    def __init__(self, daily_limit: float = 10.0):
        self.daily_limit = daily_limit
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.today_cost = 0.0
        self.total_calls = 0
        self.total_tokens_in = 0
        self.total_tokens_out = 0

    def _reset_if_new_day(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self.today:
            self.today = today
            self.today_cost = 0.0

    def add_cost(self, tokens_in: int, tokens_out: int, model: str):
        self._reset_if_new_day()
        if "flash" in model:
            cost = (tokens_in / 1000) * RESOURCE_LIMITS["cost_per_1k_input_flash"]
            cost += (tokens_out / 1000) * RESOURCE_LIMITS["cost_per_1k_output_flash"]
        else:
            cost = (tokens_in / 1000) * RESOURCE_LIMITS["cost_per_1k_input_pro"]
            cost += (tokens_out / 1000) * RESOURCE_LIMITS["cost_per_1k_output_pro"]
        self.today_cost += cost
        self.total_calls += 1
        self.total_tokens_in += tokens_in
        self.total_tokens_out += tokens_out
        return cost

    def can_spend(self) -> bool:
        self._reset_if_new_day()
        return self.today_cost < self.daily_limit

    def get_stats(self) -> Dict:
        return {
            "today_cost_usd": round(self.today_cost, 4),
            "daily_limit_usd": self.daily_limit,
            "budget_remaining": round(self.daily_limit - self.today_cost, 4),
            "total_calls": self.total_calls,
            "total_tokens_in": self.total_tokens_in,
            "total_tokens_out": self.total_tokens_out,
        }


class GeminiClient:
    """
    Hybrid Client fuer Google Gemini API.
    Fallback: Ollama (lokal) → Gemini Flash → Gemini Pro
    Kompatibel mit dem KimiClient Interface.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        ollama_url: str = "http://localhost:11434",
        offline_mode: bool = False,
    ):
        self.api_key = api_key or GEMINI_API_KEY
        self.ollama_url = ollama_url
        self.local_model = "gemma2:9b"
        self.fallback_local = "qwen2.5-coder:7b"
        self.offline_mode = offline_mode or (not self.api_key)
        self.cost_tracker = CostTracker(
            daily_limit=RESOURCE_LIMITS["emergency_stop_daily_cost"]
        )
        self.semaphore = asyncio.Semaphore(
            RESOURCE_LIMITS["max_concurrent_gemini_calls"]
        )
        if self.offline_mode:
            logger.info("OFFLINE-MODUS: Kein API-Key, verwende Bootstrap-Daten")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "flash",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        use_local: bool = True,
        force_provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Unified Chat-Interface.

        Args:
            messages: OpenAI-Format [{"role": "user", "content": "..."}]
            model: "flash", "pro", oder "thinking"
            temperature: 0.0-2.0
            max_tokens: Max Output-Tokens
            use_local: Zuerst Ollama versuchen
            force_provider: "ollama", "gemini" oder None (auto)

        Returns:
            {
                "content": str,
                "source": "local_ollama" | "gemini_flash" | "gemini_pro",
                "model": str,
                "tokens_in": int,
                "tokens_out": int,
                "cost_usd": float,
                "latency_ms": int,
            }
        """
        start_time = time.time()

        # Offline-Modus: Bootstrap-Daten zurueckgeben
        if self.offline_mode and force_provider != "ollama":
            return self._offline_response(messages, model, start_time)

        # Forced Provider
        if force_provider == "ollama":
            return await self._try_ollama(messages, temperature, start_time)
        if force_provider == "gemini":
            return await self._call_gemini(
                messages, model, temperature, max_tokens, start_time
            )

        # Auto-Routing: Ollama zuerst wenn aktiviert
        if use_local:
            try:
                result = await self._try_ollama(messages, temperature, start_time)
                if result.get("content"):
                    return result
            except Exception as e:
                logger.debug(f"Ollama nicht verfuegbar: {e}")

        # Gemini API
        return await self._call_gemini(
            messages, model, temperature, max_tokens, start_time
        )

    async def _try_ollama(
        self,
        messages: List[Dict],
        temperature: float,
        start_time: float,
    ) -> Dict[str, Any]:
        """Versucht lokales Ollama Model."""
        payload = {
            "model": self.local_model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status == 404:
                        # Fallback Model versuchen
                        payload["model"] = self.fallback_local
                        async with session.post(
                            f"{self.ollama_url}/api/chat",
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=120),
                        ) as resp2:
                            resp2.raise_for_status()
                            data = await resp2.json()
                    else:
                        resp.raise_for_status()
                        data = await resp.json()

            content = data.get("message", {}).get("content", "")
            latency = int((time.time() - start_time) * 1000)
            return {
                "content": content,
                "source": "local_ollama",
                "model": payload["model"],
                "tokens_in": 0,
                "tokens_out": 0,
                "cost_usd": 0.0,
                "latency_ms": latency,
            }
        except Exception as e:
            raise ConnectionError(f"Ollama Fehler: {e}")

    async def _call_gemini(
        self,
        messages: List[Dict],
        model: str,
        temperature: float,
        max_tokens: int,
        start_time: float,
    ) -> Dict[str, Any]:
        """Ruft Google Gemini API auf."""
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY nicht gesetzt! "
                "export GEMINI_API_KEY='dein-key'"
            )

        if not self.cost_tracker.can_spend():
            raise RuntimeError(
                f"Tages-Budget erreicht: "
                f"${self.cost_tracker.today_cost:.2f} / "
                f"${self.cost_tracker.daily_limit:.2f}"
            )

        model_id = GEMINI_MODELS.get(model, model)
        url = f"{GEMINI_BASE_URL}/models/{model_id}:generateContent?key={self.api_key}"

        # OpenAI-Format → Gemini-Format konvertieren
        gemini_contents = self._convert_messages(messages)

        payload = {
            "contents": gemini_contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": 0.95,
            },
        }

        # System-Instruction extrahieren
        system_msg = next(
            (m["content"] for m in messages if m.get("role") == "system"), None
        )
        if system_msg:
            payload["systemInstruction"] = {
                "parts": [{"text": system_msg}]
            }

        async with self.semaphore:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=180),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise RuntimeError(
                            f"Gemini API Fehler {resp.status}: {error_text[:500]}"
                        )
                    data = await resp.json()

        # Response parsen
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"Keine Gemini-Antwort: {json.dumps(data)[:500]}")

        content = ""
        for part in candidates[0].get("content", {}).get("parts", []):
            content += part.get("text", "")

        # Token-Usage extrahieren
        usage = data.get("usageMetadata", {})
        tokens_in = usage.get("promptTokenCount", 0)
        tokens_out = usage.get("candidatesTokenCount", 0)
        cost = self.cost_tracker.add_cost(tokens_in, tokens_out, model_id)
        latency = int((time.time() - start_time) * 1000)

        source = f"gemini_{model}" if model in GEMINI_MODELS else f"gemini_{model_id}"

        return {
            "content": content,
            "source": source,
            "model": model_id,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": round(cost, 6),
            "latency_ms": latency,
        }

    def _offline_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
        start_time: float,
    ) -> Dict[str, Any]:
        """Generiert Bootstrap-Antworten im Offline-Modus."""
        # System-Prompt analysieren um Kontext zu verstehen
        system_msg = ""
        user_msg = ""
        for m in messages:
            if m.get("role") == "system":
                system_msg = m["content"]
            elif m.get("role") == "user":
                user_msg = m["content"]

        # Intelligente Offline-Antwort basierend auf Step-Typ
        content = self._generate_offline_content(system_msg, user_msg)
        latency = int((time.time() - start_time) * 1000)

        return {
            "content": content,
            "source": "offline_bootstrap",
            "model": f"offline_{model}",
            "tokens_in": 0,
            "tokens_out": 0,
            "cost_usd": 0.0,
            "latency_ms": latency,
        }

    def _generate_offline_content(self, system: str, user: str) -> str:
        """Generiert kontextabhaengige Offline-Daten."""
        s = system.lower()

        if "audit" in s:
            return json.dumps({
                "timestamp": datetime.now().isoformat(),
                "overall_score": 3,
                "areas": {
                    "revenue": {"score": 1, "status": "Kein Umsatz - Aktivierung noetig", "blockers": ["Kein Gumroad Produkt live", "Keine Fiverr Gigs"], "opportunities": ["BMA+AI Consulting", "Gumroad Templates"]},
                    "content": {"score": 2, "status": "Content Pipeline existiert, aber inaktiv", "blockers": ["Keine regelmaessigen Posts"], "opportunities": ["X/Twitter BMA Content", "LinkedIn Fachbeitraege"]},
                    "automation": {"score": 5, "status": "Grundstruktur steht (Orchestrator, Cowork, n8n)", "blockers": ["API Keys fehlen teilweise"], "opportunities": ["Gemini Mirror aktivieren", "Kimi Swarm produktiv nutzen"]},
                    "system_health": {"score": 4, "status": "Mirror initialisiert, Main laeuft", "blockers": ["GEMINI_API_KEY fehlt"], "opportunities": ["Dual-Brain Amplification starten"]},
                    "swarm": {"score": 3, "status": "Swarm-Code existiert, nicht produktiv", "blockers": ["Kein aktiver Swarm-Job"], "opportunities": ["Content-Generierung per Swarm"]},
                    "mirror": {"score": 2, "status": "Initialisiert, Offline-Modus", "blockers": ["GEMINI_API_KEY fehlt"], "opportunities": ["Volle Dual-Brain Power nach Key-Setup"]}
                },
                "top_3_priorities": [
                    {"title": "GEMINI_API_KEY setzen und Mirror aktivieren", "impact": "high", "effort": "5 Minuten"},
                    {"title": "Erstes Gumroad Produkt erstellen (BMA Checkliste)", "impact": "high", "effort": "2-4 Stunden"},
                    {"title": "Fiverr Profil + 3 Gigs erstellen", "impact": "high", "effort": "3-5 Stunden"}
                ],
                "energy_score": 4,
                "recommended_focus": "revenue",
                "_offline": True,
            })

        elif "architect" in s:
            return json.dumps({
                "timestamp": datetime.now().isoformat(),
                "solutions": [
                    {
                        "priority": "Revenue-Aktivierung",
                        "approaches": [
                            {"name": "Gumroad Quick Launch", "description": "BMA-Checkliste als PDF, Preis 27 EUR", "pros": ["Schnell", "Passiv"], "cons": ["Braucht Marketing"], "setup_hours": 3, "implementation_steps": ["Template erstellen", "Gumroad Upload", "X/Twitter Promotion"], "resources_needed": ["Gumroad Account", "Canva/Design"], "expected_roi": "27-270 EUR/Monat nach Marketing"},
                            {"name": "Fiverr AI-Services", "description": "3 Gigs: AI Setup, BMA Docs, Automation", "pros": ["Marketplace Traffic", "Recurring"], "cons": ["Zeitaufwand pro Order"], "setup_hours": 4, "implementation_steps": ["Profil erstellen", "3 Gigs aufsetzen", "Portfolio Samples"], "resources_needed": ["Fiverr Account", "Portfolio"], "expected_roi": "500-3000 EUR/Monat"},
                        ],
                        "recommended": "Gumroad Quick Launch",
                        "why": "Schnellster Weg zu passivem Einkommen, parallel zu Fiverr aufbaubar"
                    }
                ],
                "cross_system_synergies": ["Mirror generiert Content-Ideen fuer Gumroad", "Main Swarm erstellt Social Media Posts"],
                "quick_wins": [{"action": "GEMINI_API_KEY setzen", "impact": "Volles Dual-Brain System", "effort_minutes": 5}],
                "_offline": True,
            })

        elif "analyst" in s:
            return json.dumps({
                "timestamp": datetime.now().isoformat(),
                "reviews": [
                    {"solution": "Gumroad Quick Launch", "feasibility_score": 9, "risk_assessment": {"technical_risks": ["Kein Design-Skill"], "business_risks": ["Kein Marketing-Budget"], "mitigation": ["Canva Templates nutzen", "Organic X/Twitter Marketing"]}, "scalability": "Hoch - weitere Produkte leicht hinzufuegbar", "cost_analysis": "Near-Zero Cost, nur Zeit", "timeline_realistic": True, "recommended_changes": ["Erst 1 Produkt, dann iterieren"], "go_no_go": "GO"}
                ],
                "overall_recommendation": "Revenue-First Strategie starten, parallel Mirror aktivieren",
                "critical_path": ["API Key setzen", "Gumroad Produkt erstellen", "First Sale erreichen"],
                "dual_brain_advantage": "Mirror generiert Produkt-Ideen und Content, Main exekutiert",
                "_offline": True,
            })

        elif "refinery" in s:
            return json.dumps({
                "timestamp": datetime.now().isoformat(),
                "iteration": 1,
                "refined_plan": {
                    "actions": [
                        {"title": "GEMINI_API_KEY setzen", "description": "Kostenloser Key von aistudio.google.com", "priority": 1, "estimated_minutes": 5, "assignee": "manual", "dependencies": [], "deliverable": "Funktionierendes Dual-Brain System"},
                        {"title": "BMA Safety Checklist PDF", "description": "27 EUR Gumroad Produkt", "priority": 2, "estimated_minutes": 180, "assignee": "both", "dependencies": [], "deliverable": "Verkaufsfertiges Digitales Produkt"},
                        {"title": "Fiverr AI Consultant Profil", "description": "3 Gigs aufsetzen", "priority": 3, "estimated_minutes": 240, "assignee": "manual", "dependencies": [], "deliverable": "Live Fiverr Profil mit 3 Gigs"},
                    ],
                    "execution_order": ["GEMINI_API_KEY setzen", "BMA Safety Checklist PDF", "Fiverr AI Consultant Profil"],
                    "parallel_tracks": [["API Key + Mirror"], ["Gumroad + Fiverr"]]
                },
                "quality_score": 7,
                "improvements_made": ["Priorisierung nach Impact/Effort"],
                "remaining_issues": ["Marketing-Strategie noch offen"],
                "converged": True,
                "_offline": True,
            })

        elif "compounder" in s:
            return json.dumps({
                "timestamp": datetime.now().isoformat(),
                "cycle_summary": "Bootstrap-Zyklus: System initialisiert, Offline-Audit durchgefuehrt, Revenue-Strategie entworfen",
                "patterns_discovered": [
                    {"name": "Revenue-First", "description": "Immer zuerst Umsatz generieren, dann optimieren", "category": "revenue", "reusable": True, "confidence": 8},
                    {"name": "Dual-Brain-Bootstrap", "description": "System kann offline starten und sich selbst bootstrappen", "category": "system", "reusable": True, "confidence": 9}
                ],
                "cross_system_insights": [
                    {"insight": "Mirror braucht API-Key fuer volle Power", "applies_to": "mirror", "action_required": "GEMINI_API_KEY setzen"},
                    {"insight": "Main und Mirror zusammen koennen Content 10x schneller produzieren", "applies_to": "both", "action_required": "Beide Systeme aktivieren"}
                ],
                "next_cycle_priorities": [
                    {"title": "API-Key setzen und vollen Zyklus fahren", "why": "Dual-Brain Amplification braucht echte AI", "estimated_impact": "10x Insight-Qualitaet"},
                    {"title": "Erstes Revenue-Produkt erstellen", "why": "Revenue = 0 ist der groesste Blocker", "estimated_impact": "Erste Einnahmen"}
                ],
                "knowledge_compressed": "System steht, Revenue fehlt, API-Key ist der Gate-Opener fuer volle Power",
                "dual_brain_effectiveness": 3,
                "recommended_model_adjustments": {"main": "Kimi Swarm fuer Content-Generierung einsetzen", "mirror": "Gemini Pro fuer strategische Analysen nutzen"},
                "_offline": True,
            })

        elif "executor" in s:
            return json.dumps({
                "action_title": "Bootstrap-Analyse: System-Readiness Check",
                "deliverable_type": "analysis",
                "deliverable": "SYSTEM-STATUS:\n- Mirror: Initialisiert, Offline-Modus\n- Orchestrator: 5-Step Loop bereit\n- Cowork: Observe-Plan-Act-Reflect bereit\n- Sync: Bidirektional konfiguriert\n- Vision: 5 Starter-Fragen generiert\n- Dual-Brain: Amplification Engine bereit\n\nNAECHSTER SCHRITT: GEMINI_API_KEY setzen (https://aistudio.google.com/apikey)\nDANN: python gemini-mirror/gemini_empire.py full",
                "files_to_create": [],
                "files_to_modify": [],
                "next_manual_step": "GEMINI_API_KEY setzen: export GEMINI_API_KEY='AIza...'",
                "execution_notes": "Offline-Bootstrap abgeschlossen. System wartet auf API-Key.",
                "quality_score": 6,
                "ready_for_main": True,
                "_offline": True,
            })

        elif "reflektor" in s or ("reflekt" in s and "cowork" in s):
            return json.dumps({
                "cycle_score": 5,
                "what_worked": "Bootstrap-Initialisierung erfolgreich, alle Subsysteme bereit",
                "what_didnt": "Ohne API-Key nur Offline-Daten moeglich",
                "pattern_discovered": {"name": "Bootstrap-First", "description": "System kann sich selbst initialisieren und ist sofort nach Key-Setup voll einsatzbereit", "reusable": True, "share_with_main": True},
                "improvement_for_next_cycle": "API-Key setzen und echten Zyklus fahren",
                "recommended_focus_shift": "revenue",
                "confidence": 7,
                "message_to_main": "Mirror ist bereit - brauche nur den Gemini API Key fuer volle Power!",
                "_offline": True,
            })

        elif "review" in s or "verstaerk" in s:
            return json.dumps({
                "review_score": 5,
                "strengths": ["Solide Architektur", "Gutes Automatisierungs-Framework"],
                "weaknesses": ["Kein Revenue", "APIs nicht verbunden"],
                "blind_spots": ["Marketing-Strategie fehlt komplett"],
                "improvements": [{"area": "Revenue", "current": "0 EUR", "suggested": "BMA Consulting + Gumroad starten", "impact": "high", "effort": "1 Woche"}],
                "missed_opportunities": ["BMA-Expertise ist einzigartig - nicht genutzt"],
                "competitive_edge": "Mirror wuerde tiefere strategische Analysen liefern",
                "synthesis": "Main exekutiert, Mirror denkt strategisch - zusammen unschlagbar",
                "next_action": "GEMINI_API_KEY setzen fuer echte Dual-Brain Power",
                "_offline": True,
            })

        elif "plan" in s or "cowork" in s:
            return json.dumps({
                "priority_action": {
                    "title": "Gemini API Key einrichten und Mirror vollstaendig aktivieren",
                    "why": "Ohne Key laeuft das System nur im Bootstrap-Modus",
                    "how": ["aistudio.google.com oeffnen", "API Key generieren", "export GEMINI_API_KEY='...'", "python gemini_empire.py full"],
                    "expected_impact": "Volles Dual-Brain System mit echter AI",
                    "effort_minutes": 5,
                    "category": "automation",
                    "dependencies": [],
                    "success_criteria": "Voller Workflow-Zyklus laeuft mit echten Gemini-Antworten",
                    "dual_brain_relevance": "Kernvoraussetzung fuer beide Systeme"
                },
                "secondary_actions": [
                    {"title": "Erstes Gumroad Produkt erstellen", "why": "Revenue = 0", "effort_minutes": 180},
                    {"title": "Vision-Fragen beantworten", "why": "System muss Maurice verstehen", "effort_minutes": 15}
                ],
                "situation_assessment": "System ist initialisiert und bereit, braucht nur noch den API-Key-Startschuss",
                "risk_alert": None,
                "_offline": True,
            })

        elif "reflekt" in s or "reflect" in s:
            return json.dumps({
                "cycle_score": 5,
                "what_worked": "Bootstrap-Initialisierung erfolgreich, alle Subsysteme bereit",
                "what_didnt": "Ohne API-Key nur Offline-Daten moeglich",
                "pattern_discovered": {"name": "Bootstrap-First", "description": "System kann sich selbst initialisieren und ist sofort nach Key-Setup voll einsatzbereit", "reusable": True, "share_with_main": True},
                "improvement_for_next_cycle": "API-Key setzen und echten Zyklus fahren",
                "recommended_focus_shift": "revenue",
                "confidence": 7,
                "message_to_main": "Mirror ist bereit - brauche nur den Gemini API Key fuer volle Power!",
                "_offline": True,
            })

        else:
            return json.dumps({
                "status": "offline_bootstrap",
                "message": "System im Offline-Modus. Setze GEMINI_API_KEY fuer echte AI-Antworten.",
                "timestamp": datetime.now().isoformat(),
                "_offline": True,
            })

    def _convert_messages(
        self, messages: List[Dict[str, str]]
    ) -> List[Dict]:
        """Konvertiert OpenAI-Format zu Gemini-Format."""
        gemini_contents = []
        for msg in messages:
            if msg.get("role") == "system":
                continue  # System wird separat behandelt
            role = "model" if msg["role"] == "assistant" else "user"
            gemini_contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}],
            })
        return gemini_contents

    async def chat_json(
        self,
        messages: List[Dict[str, str]],
        model: str = "flash",
        temperature: float = 0.5,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """
        Chat mit erzwungenem JSON-Output.
        Parsed die Antwort automatisch.
        """
        result = await self.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            use_local=False,
            force_provider="gemini",
        )

        parsed = self._parse_json(result["content"])
        result["parsed"] = parsed
        result["parse_success"] = "parse_error" not in parsed
        return result

    @staticmethod
    def _parse_json(raw: str) -> Dict:
        """Robust JSON-Parser (wie im Hauptsystem)."""
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return {"parse_error": True, "raw": raw[:2000]}

    def get_cost_stats(self) -> Dict:
        """Gibt aktuelle Kosten-Statistiken zurueck."""
        return self.cost_tracker.get_stats()


# === Convenience-Funktionen ===

_default_client: Optional[GeminiClient] = None


def get_client() -> GeminiClient:
    """Singleton-Instanz des GeminiClient."""
    global _default_client
    if _default_client is None:
        _default_client = GeminiClient()
    return _default_client


async def quick_gemini(
    prompt: str,
    system: str = "",
    model: str = "flash",
    temperature: float = 0.7,
) -> str:
    """Schneller Gemini-Aufruf fuer einfache Prompts."""
    client = get_client()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    result = await client.chat(messages, model=model, temperature=temperature)
    return result["content"]


async def quick_gemini_json(
    prompt: str,
    system: str = "Antworte NUR mit validem JSON.",
    model: str = "flash",
) -> Dict:
    """Schneller Gemini-Aufruf mit JSON-Output."""
    client = get_client()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    result = await client.chat_json(messages, model=model)
    return result.get("parsed", {})
