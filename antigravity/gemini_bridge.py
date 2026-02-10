"""
Gemini Bridge — Cloud Brain Connection
========================================
Connects the local Mac Brain to Google Gemini Cloud.
Handles: API calls, memory, rate limiting, retry logic.
"""

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from antigravity.config import (
    GEMINI_API_KEY,
    GEMINI_FLASH,
    GEMINI_PRO,
    OFFLINE_MODE,
)

# ─── Data Paths ─────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "_data"
MEMORY_FILE = DATA_DIR / "cloud_memory.json"
SYNC_LOG = DATA_DIR / "sync_log.json"


@dataclass
class CloudMessage:
    """A single message in the cloud conversation."""

    role: str  # "user" or "model"
    content: str
    timestamp: str = ""
    category: str = "general"  # vision, strategy, code, question

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class CloudMemory:
    """Persistent memory for the Cloud Brain."""

    conversations: list[dict[str, Any]] = field(default_factory=list)
    vision_context: str = ""
    last_sync: str = ""
    total_tokens_used: int = 0
    total_requests: int = 0

    def save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        MEMORY_FILE.write_text(json.dumps(self.__dict__, indent=2, ensure_ascii=False))

    @classmethod
    def load(cls) -> "CloudMemory":
        if MEMORY_FILE.exists():
            data = json.loads(MEMORY_FILE.read_text())
            return cls(**data)
        return cls()


class GeminiBridge:
    """
    Bridge between local Mac system and Google Gemini Cloud.

    The Cloud Brain handles:
    - Strategic thinking and planning
    - Vision mining through questions
    - Creative problem solving
    - Knowledge synthesis across domains
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.memory = CloudMemory.load()
        self._client = None
        self._rate_limit_remaining = 1500  # Free tier
        self._last_request_time = 0.0
        self._min_request_interval = 0.5  # 500ms between requests

        if not self.api_key:
            print("⚠️  No GEMINI_API_KEY set. Cloud Brain disabled.")
            print("   Get one free: https://aistudio.google.com/apikey")

    @property
    def is_available(self) -> bool:
        return bool(self.api_key) and not OFFLINE_MODE

    def _get_client(self):
        """Lazy-load the Gemini client."""
        if self._client is None:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.api_key)
                self._client = genai
            except ImportError:
                print("❌ google-generativeai not installed.")
                print("   Run: pip install google-generativeai")
                return None
        return self._client

    def _rate_limit_wait(self):
        """Respect rate limits."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    def think(
        self,
        prompt: str,
        context: str = "",
        model: str = GEMINI_FLASH,
        system_instruction: str = "",
        temperature: float = 0.7,
    ) -> Optional[str]:
        """
        Send a thought to the Cloud Brain and get a response.

        Args:
            prompt: What to think about
            context: Additional context (code, docs, vision)
            model: Which Gemini model to use
            system_instruction: System prompt for this request
            temperature: Creativity level (0.0-2.0)

        Returns:
            Cloud Brain's response, or None if unavailable
        """
        if not self.is_available:
            return None

        genai = self._get_client()
        if genai is None:
            return None

        self._rate_limit_wait()

        # Build the system instruction
        if not system_instruction:
            system_instruction = self._build_system_prompt()

        try:
            gemini_model = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_instruction,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=8192,
                ),
            )

            # Build full prompt with context
            full_prompt = prompt
            if context:
                full_prompt = f"CONTEXT:\n```\n{context}\n```\n\nTASK:\n{prompt}"

            response = gemini_model.generate_content(full_prompt)

            # Track usage
            self.memory.total_requests += 1
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                self.memory.total_tokens_used += (
                    response.usage_metadata.total_token_count or 0
                )

            # Save to memory
            self.memory.conversations.append(
                {
                    "prompt": prompt[:500],
                    "response": response.text[:1000] if response.text else "",
                    "model": model,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Keep memory manageable (last 100 conversations)
            if len(self.memory.conversations) > 100:
                self.memory.conversations = self.memory.conversations[-100:]

            self.memory.save()
            return response.text

        except Exception as e:
            print(f"⚠️  Gemini error: {e}")
            return None

    def think_deep(
        self,
        prompt: str,
        context: str = "",
    ) -> Optional[str]:
        """Use Gemini Pro for complex reasoning tasks."""
        return self.think(
            prompt=prompt,
            context=context,
            model=GEMINI_PRO,
            temperature=0.3,
        )

    def brainstorm(
        self,
        topic: str,
        constraints: str = "",
    ) -> Optional[str]:
        """Creative brainstorming with high temperature."""
        system = """Du bist ein kreativer Stratege und Visionär.
Deine Aufgabe: Generiere unkonventionelle, disruptive Ideen.
Denke in 10x, nicht 10%. Jede Idee muss konkret und umsetzbar sein.
Format: Nummerierte Liste mit Titel + 2-Satz Beschreibung."""

        prompt = f"Brainstorm zum Thema: {topic}"
        if constraints:
            prompt += f"\n\nRahmenbedingungen: {constraints}"

        return self.think(
            prompt=prompt,
            system_instruction=system,
            temperature=1.2,
        )

    def generate_questions(
        self,
        vision_profile: dict[str, Any],
        category: str = "general",
        count: int = 5,
    ) -> Optional[list[str]]:
        """
        Generate daily questions to mine Maurice's vision.

        Categories: general, business, tech, life, priorities
        """
        system = """Du bist ein persönlicher Vision Coach.
Deine Aufgabe: Stelle präzise, tiefgehende Fragen die helfen,
die wahre Vision und Prioritäten des Users zu verstehen.

REGELN:
- Fragen müssen SPEZIFISCH sein, nicht generisch
- Baue auf vorherigen Antworten auf
- Mische: 70% zukunftsgerichtet, 30% reflektierend
- Maximal 2 Sätze pro Frage
- Antworte NUR mit den Fragen, eine pro Zeile, mit Nummer"""

        context = json.dumps(vision_profile, indent=2, ensure_ascii=False)
        prompt = (
            f"Generiere {count} {category}-Fragen für heute.\n"
            f"Basierend auf dem bisherigen Vision Profile."
        )

        response = self.think(
            prompt=prompt,
            context=context,
            system_instruction=system,
            temperature=0.8,
        )

        if response:
            lines = [
                line.strip()
                for line in response.strip().split("\n")
                if line.strip() and any(c.isalpha() for c in line)
            ]
            return lines[:count]
        return None

    def analyze_codebase(self, summary: str) -> Optional[str]:
        """Send codebase summary to Cloud Brain for strategic analysis."""
        system = """Du bist ein Senior Software Architect.
Analysiere die Codebase und gib konkrete Verbesserungsvorschläge.
Fokussiere auf: Architektur, Performance, Wartbarkeit, Skalierbarkeit.
Format: Priorisierte Liste mit Impact-Rating (HIGH/MED/LOW)."""

        return self.think(
            prompt="Analysiere diese Codebase und erstelle einen Verbesserungsplan.",
            context=summary,
            system_instruction=system,
            temperature=0.3,
        )

    def _build_system_prompt(self) -> str:
        """Build the default system prompt with vision context."""
        base = """Du bist das CLOUD BRAIN im Dual Brain System von Maurice.
Du arbeitest zusammen mit einem MAC BRAIN (lokales Ollama-System).

Deine Rolle:
- Strategisches Denken und Planen
- Vision verstehen und verfeinern
- Kreative Lösungen generieren
- Wissen synthetisieren

Du kennst Maurice's Vision und arbeitest aktiv daran,
seine Ziele zu erreichen. Sei direkt, konkret, und liefere
immer actionable Ergebnisse."""

        if self.memory.vision_context:
            base += f"\n\nAKTUELLE VISION:\n{self.memory.vision_context}"

        return base

    def update_vision_context(self, vision_summary: str):
        """Update the Cloud Brain's understanding of the vision."""
        self.memory.vision_context = vision_summary
        self.memory.save()

    def get_stats(self) -> dict[str, Any]:
        """Get Cloud Brain usage statistics."""
        return {
            "total_requests": self.memory.total_requests,
            "total_tokens": self.memory.total_tokens_used,
            "conversations_stored": len(self.memory.conversations),
            "vision_context_length": len(self.memory.vision_context),
            "last_sync": self.memory.last_sync,
            "available": self.is_available,
        }


# ─── Singleton ──────────────────────────────────────────────────────
_bridge: Optional[GeminiBridge] = None


def get_bridge() -> GeminiBridge:
    """Get the default GeminiBridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = GeminiBridge()
    return _bridge


# ─── CLI ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    bridge = GeminiBridge()

    if not bridge.is_available:
        print("❌ Cloud Brain nicht verfügbar.")
        print("   export GEMINI_API_KEY='your-key'")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("🧠 Gemini Bridge — Cloud Brain")
        print()
        stats = bridge.get_stats()
        for key, val in stats.items():
            print(f"  {key}: {val}")
        print()
        print("Usage:")
        print('  python gemini_bridge.py think "Was ist die beste Strategie?"')
        print('  python gemini_bridge.py brainstorm "Revenue in 30 Tagen"')
        print('  python gemini_bridge.py questions')
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "think":
        prompt = " ".join(sys.argv[2:])
        print(f"🧠 Cloud Brain denkt über: {prompt[:80]}...")
        result = bridge.think(prompt)
        if result:
            print(f"\n{result}")
        else:
            print("❌ Keine Antwort erhalten")

    elif cmd == "brainstorm":
        topic = " ".join(sys.argv[2:])
        print(f"💡 Brainstorm: {topic[:80]}...")
        result = bridge.brainstorm(topic)
        if result:
            print(f"\n{result}")

    elif cmd == "questions":
        print("❓ Generiere tägliche Vision-Fragen...")
        questions = bridge.generate_questions({}, count=5)
        if questions:
            print()
            for q in questions:
                print(f"  {q}")

    else:
        print(f"Unknown command: {cmd}")
