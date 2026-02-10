"""
Vision Discovery Engine - Daily question system that learns Maurice's exact vision.

Both systems (Claude + Gemini) generate questions to deeply understand:
- The ultimate mission and goals
- Decision-making patterns
- Lifestyle preferences
- Revenue strategies
- What "unfair advantages" means concretely
- Emotional drivers and motivations

Every answer is permanently stored in the Digital Memory.
Questions evolve based on previous answers - they get sharper over time.
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional

from gemini_client import GeminiClient
from digital_memory import DigitalMemory


STATE_DIR = Path(__file__).parent / "state"
QUESTIONS_FILE = STATE_DIR / "vision_questions.json"
ANSWERS_FILE = STATE_DIR / "vision_answers.json"
DISCOVERY_LOG = STATE_DIR / "discovery_log.json"


QUESTION_CATEGORIES = {
    "mission": {
        "de": "Mission & Ziel",
        "focus": "Was ist das ultimative Ziel? Was soll das Empire erreichen?",
    },
    "lifestyle": {
        "de": "Lebensstil & Alltag",
        "focus": "Wie sieht der ideale Tag aus? Was fuer ein Leben wird angestrebt?",
    },
    "revenue": {
        "de": "Einnahmen & Strategie",
        "focus": "Wie soll Geld verdient werden? Welche Kanaele? Welche Betraege?",
    },
    "automation": {
        "de": "Automatisierung",
        "focus": "Was soll als naechstes automatisiert werden? Welche Prozesse nerven?",
    },
    "products": {
        "de": "Produkte & Services",
        "focus": "Welche Produkte? Fuer wen? Zu welchem Preis?",
    },
    "customers": {
        "de": "Kunden & Zielgruppe",
        "focus": "Wer sind die idealen Kunden? Was brauchen sie?",
    },
    "strengths": {
        "de": "Staerken & Vorteile",
        "focus": "Was sind die einzigartigen Vorteile? BMA + AI Kombination?",
    },
    "blockers": {
        "de": "Hindernisse & Probleme",
        "focus": "Was blockiert gerade? Was frustriert? Was kostet Zeit?",
    },
    "decisions": {
        "de": "Entscheidungen",
        "focus": "Welche Entscheidungen stehen an? Was muss priorisiert werden?",
    },
    "experiments": {
        "de": "Experimente & Tests",
        "focus": "Was soll getestet werden? Welche Hypothesen gibt es?",
    },
    "identity": {
        "de": "Identitaet & Werte",
        "focus": "Wer willst du sein? Was sind deine Kernwerte?",
    },
    "fears": {
        "de": "Aengste & Risiken",
        "focus": "Wovor hast du Angst? Was koennte schiefgehen?",
    },
}


class VisionDiscoveryEngine:
    """
    Generates daily questions, stores answers, and builds vision profile.
    Questions get smarter over time based on accumulated knowledge.
    """

    def __init__(self, gemini: GeminiClient, memory: DigitalMemory):
        self.gemini = gemini
        self.memory = memory
        STATE_DIR.mkdir(parents=True, exist_ok=True)

    async def generate_daily_questions(self, session: str = "morning") -> list[dict]:
        """
        Generate today's questions based on:
        1. What we already know (from memory)
        2. What we DON'T know yet (gaps)
        3. What changed recently (new context)
        4. Session type (morning=strategic, evening=reflection)
        """
        # Load existing knowledge
        known = self.memory.get_vision_summary()
        previous_answers = self._load_recent_answers(days=7)
        asked_before = self._load_recent_questions(days=30)

        count = 3 if session == "morning" else 2

        prompt = f"""Du bist der Vision Discovery Agent des AIEmpire Systems.
Dein Meister ist Maurice Pfeifer, 37, Elektrotechnikmeister, 16 Jahre BMA-Expertise.
Ziel: 100 Mio EUR in 1-3 Jahren mit AI-Automatisierung.

Session: {"Morgen (strategisch, zukunftsgerichtet)" if session == "morning" else "Abend (Reflexion, was lief heute, was gelernt)"}

Was wir bereits wissen:
{json.dumps(known, indent=2, ensure_ascii=False)[:3000]}

Letzte 7 Tage Antworten:
{json.dumps(previous_answers, indent=2, ensure_ascii=False)[:2000]}

Bereits gestellte Fragen (nicht wiederholen!):
{json.dumps([q.get("question", "") for q in asked_before], ensure_ascii=False)[:1500]}

Verfuegbare Kategorien: {list(QUESTION_CATEGORIES.keys())}

Generiere genau {count} NEUE Fragen die:
1. TIEFER gehen als bisherige Fragen (nicht oberflaechlich)
2. KONKRETE Antworten provozieren (keine Ja/Nein Fragen)
3. LUECKEN im Wissen schliessen
4. Maurice zum NACHDENKEN bringen
5. Auf Deutsch sind (informell, du-Form)

Jede Frage muss einer Kategorie zugeordnet sein.
Erklaere WARUM du diese Frage stellst (was wir damit lernen).

Antworte als JSON:
[
  {{
    "category": "mission",
    "question": "Die Frage auf Deutsch...",
    "why": "Warum wir das wissen muessen...",
    "depth_level": 1-5,
    "builds_on": "Referenz zu vorheriger Antwort falls relevant"
  }}
]"""

        result = await self.gemini.chat_json(prompt, tier="pro")
        questions = result.get("parsed") or []

        if not isinstance(questions, list):
            questions = []

        # Enrich and store
        for q in questions:
            q["id"] = f"q_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{questions.index(q)}"
            q["session"] = session
            q["generated_at"] = datetime.now(timezone.utc).isoformat()
            q["answered"] = False

        self._save_questions(questions)

        return questions

    async def process_answer(self, question_id: str, answer: str) -> dict:
        """
        Process Maurice's answer:
        1. Store the answer
        2. Extract insights and key facts
        3. Update digital memory
        4. Generate follow-up context
        """
        questions = self._load_all_questions()
        question = next((q for q in questions if q.get("id") == question_id), None)

        if not question:
            return {"error": f"Question {question_id} not found"}

        # Extract insights with Gemini
        prompt = f"""Analysiere Maurice's Antwort auf eine Vision Discovery Frage.

Frage (Kategorie: {question.get('category', 'unknown')}):
"{question.get('question', '')}"

Antwort:
"{answer}"

Bisheriges Wissen ueber Maurice:
{json.dumps(self.memory.get_vision_summary(), indent=2, ensure_ascii=False)[:2000]}

Extrahiere:
1. Konkrete Fakten (was hat er gesagt)
2. Implizite Werte (was sagt das ueber ihn aus)
3. Priorisierungen (was ist ihm wichtiger als anderes)
4. Emotionale Treiber (was motiviert ihn wirklich)
5. Aktionspunkte (was sollte das System jetzt tun)

Antworte als JSON:
{{
  "facts": ["Konkreter Fakt 1", "..."],
  "values": ["Impliziter Wert 1", "..."],
  "priorities": ["Prioritaet 1 > Prioritaet 2"],
  "emotions": ["Emotionaler Treiber 1", "..."],
  "actions": ["Aktion 1", "..."],
  "memory_updates": [
    {{"category": "vision", "key": "...", "value": "...", "confidence": 0.9}}
  ],
  "depth_assessment": "Wie tief war die Antwort? Was fehlt noch?"
}}"""

        result = await self.gemini.chat_json(prompt, tier="pro")
        insights = result.get("parsed") or {}

        # Store answer
        answer_entry = {
            "question_id": question_id,
            "question": question.get("question"),
            "category": question.get("category"),
            "answer": answer,
            "insights": insights,
            "answered_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save_answer(answer_entry)

        # Update memory with extracted insights
        if insights.get("memory_updates"):
            for update in insights["memory_updates"]:
                self.memory.remember(
                    category=update.get("category", "vision"),
                    key=update.get("key", "unknown"),
                    value=update.get("value", ""),
                    confidence=update.get("confidence", 0.7),
                    source="vision_discovery",
                )

        # Mark question as answered
        for q in questions:
            if q.get("id") == question_id:
                q["answered"] = True
                q["answered_at"] = datetime.now(timezone.utc).isoformat()
        self._write_json(QUESTIONS_FILE, questions)

        return {
            "status": "processed",
            "insights_extracted": len(insights.get("facts", [])),
            "memory_updates": len(insights.get("memory_updates", [])),
            "actions_identified": len(insights.get("actions", [])),
            "insights": insights,
        }

    async def get_pending_questions(self) -> list[dict]:
        """Get all unanswered questions."""
        questions = self._load_all_questions()
        return [q for q in questions if not q.get("answered")]

    async def get_vision_profile(self) -> dict:
        """Build a comprehensive vision profile from all accumulated knowledge."""
        answers = self._load_all_answers()
        summary = self.memory.get_vision_summary()

        if not answers:
            return {
                "status": "no_data",
                "message": "Noch keine Antworten. Starte mit den taeglichen Fragen.",
            }

        prompt = f"""Erstelle ein umfassendes Vision-Profil fuer Maurice Pfeifer basierend auf allen gesammelten Daten.

Gesammeltes Wissen:
{json.dumps(summary, indent=2, ensure_ascii=False)[:4000]}

Alle Antworten ({len(answers)} total):
{json.dumps(answers[-20:], indent=2, ensure_ascii=False)[:4000]}

Erstelle ein strukturiertes Profil:
{{
  "core_mission": "Der Kern seiner Mission in einem Satz",
  "values": ["Top 5 Werte"],
  "strengths": ["Top 5 Staerken"],
  "blind_spots": ["Potenzielle blinde Flecken"],
  "decision_style": "Wie trifft er Entscheidungen",
  "motivation_drivers": ["Was treibt ihn an"],
  "fear_drivers": ["Was will er vermeiden"],
  "ideal_day": "Sein idealer Tag",
  "revenue_strategy": "Seine Revenue-Strategie zusammengefasst",
  "unique_edge": "Sein einzigartiger Vorteil",
  "knowledge_gaps": ["Was wir noch nicht wissen"],
  "next_questions": ["Die 3 wichtigsten naechsten Fragen"],
  "confidence_score": 0.0-1.0,
  "total_data_points": 0
}}"""

        result = await self.gemini.chat_json(prompt, tier="pro")
        return result.get("parsed") or {"status": "generation_failed"}

    # -- File Operations --

    def _load_all_questions(self) -> list:
        return self._read_json(QUESTIONS_FILE)

    def _load_all_answers(self) -> list:
        return self._read_json(ANSWERS_FILE)

    def _load_recent_questions(self, days: int = 30) -> list:
        questions = self._load_all_questions()
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        return [q for q in questions if q.get("generated_at", "") >= cutoff]

    def _load_recent_answers(self, days: int = 7) -> list:
        answers = self._load_all_answers()
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        return [a for a in answers if a.get("answered_at", "") >= cutoff]

    def _save_questions(self, new_questions: list):
        all_q = self._load_all_questions()
        all_q.extend(new_questions)
        self._write_json(QUESTIONS_FILE, all_q)

    def _save_answer(self, answer: dict):
        answers = self._load_all_answers()
        answers.append(answer)
        self._write_json(ANSWERS_FILE, answers)

    def _read_json(self, path: Path) -> list:
        if path.exists():
            try:
                return json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                return []
        return []

    def _write_json(self, path: Path, data):
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
