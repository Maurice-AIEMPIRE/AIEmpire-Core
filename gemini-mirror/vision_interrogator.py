"""
Vision Interrogator - Digitales Gedaechtnis und Visions-Erkennung

Beide Systeme (Main + Mirror) stellen Maurice taeglich intelligente Fragen,
um seine Vision, Wuensche, Prioritaeten und Persoenlichkeit zu verstehen.

Die Antworten werden zu einem persistenten "digitalen Gedaechtnis",
das beiden Systemen als Kontext dient.

Fragetypen:
- Vision:      Langfristige Ziele, Traeume, Ambitionen
- Strategy:    Wie soll das Ziel erreicht werden
- Priorities:  Was ist jetzt am wichtigsten
- Preferences: Arbeitsstil, Tools, Entscheidungsmuster
- Blockers:    Was hindert, was frustriert
- Values:      Was ist wichtig, Prinzipien
- Lifestyle:   Wie soll das Leben aussehen

Tiefen:
- Surface: Schnelle Ja/Nein Fragen (30 Sekunden)
- Medium:  1-2 Saetze (2 Minuten)
- Deep:    Reflektion (5+ Minuten)
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

MIRROR_DIR = Path(__file__).parent
sys.path.insert(0, str(MIRROR_DIR))

from config import (
    VISION_STATE_FILE,
    QUESTION_LOG_FILE,
    VISION_MEMORY_FILE,
    PERSONALITY_FILE,
    VISION_CONFIG,
    MODEL_ROUTING,
)
from gemini_client import GeminiClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [VISION] %(levelname)s %(message)s",
)
logger = logging.getLogger("vision-interrogator")


# === Maurice Profil (wachsend mit jeder Antwort) ===

DEFAULT_PROFILE = {
    "name": "Maurice Pfeifer",
    "age": 37,
    "expertise": "Elektrotechnikmeister, 16 Jahre BMA (Brandmeldeanlagen)",
    "primary_goal": "100 Mio EUR in 1-3 Jahren, alles automatisiert mit AI",
    "known_preferences": [],
    "known_values": [],
    "known_blockers": [],
    "vision_clarity_score": 1,  # 1-10, waechst mit Antworten
    "total_answers": 0,
    "personality_traits": [],
    "decision_patterns": [],
    "updated": datetime.now().isoformat(),
}


QUESTION_GENERATOR_PROMPT = """Du bist der Vision-Interrogator im AIEmpire System.
Dein Ziel: Maurice Pfeifer (37, Elektrotechnikmeister, Ziel: 100M EUR mit AI)
WIRKLICH verstehen. Nicht oberflaechlich - TIEF.

Du bist sein digitales Gedaechtnis und sein strategischer Berater.
Jede Frage muss einen ZWECK haben: Entweder neue Information gewinnen,
eine Annahme verifizieren, oder eine Entscheidung vorbereiten.

AKTUELLES PROFIL:
{profile}

BEREITS BEANTWORTETE FRAGEN (letzte 20):
{recent_qa}

HEUTIGER FOKUS: {focus_category}
TIEFE: {depth}

REGELN:
1. Stelle GENAU {count} Fragen
2. Jede Frage in der Kategorie: {focus_category}
3. Tiefe: {depth}
4. Frage NICHT was schon beantwortet wurde
5. Fragen muessen ACTIONABLE sein (die Antwort muss einen Unterschied machen)
6. Auf Deutsch
7. Mische verschiedene Fragetypen (offen, geschlossen, hypothetisch, priorisierend)

Antworte NUR als JSON:
{{
  "questions": [
    {{
      "id": "Q-001",
      "question": "Die Frage auf Deutsch",
      "category": "{focus_category}",
      "depth": "{depth}",
      "purpose": "Warum diese Frage wichtig ist",
      "expected_insight": "Was wir aus der Antwort lernen",
      "follow_up_trigger": "Bei welcher Antwort nachfragen"
    }}
  ],
  "reasoning": "Warum diese Fragen jetzt wichtig sind",
  "profile_gaps": ["Was wir noch nicht wissen"]
}}"""


ANSWER_PROCESSOR_PROMPT = """Du bist der Antwort-Prozessor im AIEmpire Vision System.
Maurice hat Fragen beantwortet. Extrahiere ALLE Informationen.

AKTUELLES PROFIL:
{profile}

FRAGE UND ANTWORT:
{qa_pair}

Analysiere die Antwort und extrahiere:
1. Neue Fakten ueber Maurice
2. Preferences/Praeferenzen
3. Werte und Prinzipien
4. Entscheidungsmuster
5. Emotionale Hinweise
6. Strategische Implikationen

Antworte NUR als JSON:
{{
  "extracted_facts": ["Fakt 1", "Fakt 2"],
  "preferences_detected": ["Praeferenz 1"],
  "values_detected": ["Wert 1"],
  "decision_patterns": ["Muster 1"],
  "emotional_signals": ["Signal 1"],
  "strategic_implications": ["Implikation 1"],
  "profile_updates": {{
    "known_preferences": ["Neue Praeferenzen zum Hinzufuegen"],
    "known_values": ["Neue Werte"],
    "known_blockers": ["Neue Blocker"],
    "personality_traits": ["Neue Traits"]
  }},
  "confidence": 1-10,
  "follow_up_recommended": true/false,
  "follow_up_question": "Optional: Nachfrage"
}}"""


class VisionInterrogator:
    """
    Stellt intelligente Fragen und baut ein digitales Gedaechtnis auf.
    """

    def __init__(self):
        self.client = GeminiClient()
        self.profile = self._load_profile()
        self.state = self._load_state()
        self.questions_log = self._load_questions_log()

    # === State Management ===

    def _load_profile(self) -> Dict:
        if PERSONALITY_FILE.exists():
            try:
                return json.loads(PERSONALITY_FILE.read_text())
            except json.JSONDecodeError:
                pass
        PERSONALITY_FILE.parent.mkdir(parents=True, exist_ok=True)
        PERSONALITY_FILE.write_text(json.dumps(DEFAULT_PROFILE, indent=2, ensure_ascii=False))
        return DEFAULT_PROFILE.copy()

    def _save_profile(self):
        self.profile["updated"] = datetime.now().isoformat()
        PERSONALITY_FILE.write_text(json.dumps(self.profile, indent=2, ensure_ascii=False))

    def _load_state(self) -> Dict:
        if VISION_STATE_FILE.exists():
            try:
                return json.loads(VISION_STATE_FILE.read_text())
            except json.JSONDecodeError:
                pass
        default = {
            "created": datetime.now().isoformat(),
            "total_questions_asked": 0,
            "total_answers_received": 0,
            "answers": [],
            "pending_questions": [],
            "daily_stats": {},
        }
        self._save_state(default)
        return default

    def _save_state(self, state: Dict = None):
        if state is None:
            state = self.state
        state["updated"] = datetime.now().isoformat()
        VISION_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))

    def _load_questions_log(self) -> List:
        if QUESTION_LOG_FILE.exists():
            try:
                return json.loads(QUESTION_LOG_FILE.read_text())
            except json.JSONDecodeError:
                pass
        return []

    def _save_questions_log(self):
        QUESTION_LOG_FILE.write_text(
            json.dumps(self.questions_log[-500:], indent=2, ensure_ascii=False)
        )

    # === Fragen generieren ===

    async def generate_daily_questions(
        self,
        focus: Optional[str] = None,
        count: int = None,
        depth: str = "medium",
    ) -> List[Dict]:
        """Generiert taegliche Fragen basierend auf aktuellem Wissensstand."""
        if count is None:
            count = VISION_CONFIG["questions_per_day"]

        # Fokus automatisch waehlen basierend auf Profil-Luecken
        if focus is None:
            focus = self._choose_focus()

        logger.info(f"Generiere {count} Fragen (Fokus: {focus}, Tiefe: {depth})")

        # Letzte Q&As fuer Kontext
        recent_qa = self.state.get("answers", [])[-20:]
        recent_qa_text = json.dumps(recent_qa, ensure_ascii=False)[:2000]

        prompt = QUESTION_GENERATOR_PROMPT.format(
            profile=json.dumps(self.profile, ensure_ascii=False)[:1500],
            recent_qa=recent_qa_text,
            focus_category=focus,
            depth=depth,
            count=count,
        )

        routing = MODEL_ROUTING.get("vision_questions", {"model": "pro", "temp": 0.9})

        result = await self.client.chat_json(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Generiere {count} {depth}-Fragen in der Kategorie {focus}."},
            ],
            model=routing["model"],
            temperature=routing["temp"],
        )

        questions = result.get("parsed", {}).get("questions", [])
        if not questions:
            logger.warning("Keine Fragen generiert, verwende Fallback")
            questions = self._fallback_questions(focus, count)

        # Fragen speichern
        for q in questions:
            q["generated_at"] = datetime.now().isoformat()
            q["answered"] = False
            q["source"] = "gemini_mirror"

        self.state["pending_questions"].extend(questions)
        self.state["total_questions_asked"] = (
            self.state.get("total_questions_asked", 0) + len(questions)
        )
        self._save_state()

        # Log
        self.questions_log.append({
            "timestamp": datetime.now().isoformat(),
            "focus": focus,
            "depth": depth,
            "count": len(questions),
            "questions": [q["question"] for q in questions],
        })
        self._save_questions_log()

        logger.info(f"✓ {len(questions)} Fragen generiert")
        return questions

    def _choose_focus(self) -> str:
        """Waehlt automatisch den besten Fokus basierend auf Profil-Luecken."""
        categories = VISION_CONFIG["categories"]

        # Zaehle Antworten pro Kategorie
        category_counts = {c: 0 for c in categories}
        for answer in self.state.get("answers", []):
            cat = answer.get("category", "vision")
            if cat in category_counts:
                category_counts[cat] += 1

        # Waehle die Kategorie mit den wenigsten Antworten
        return min(category_counts, key=category_counts.get)

    def _fallback_questions(self, focus: str, count: int) -> List[Dict]:
        """Fallback-Fragen falls Gemini nicht liefert."""
        fallbacks = {
            "vision": [
                "Wo siehst du dich in genau 12 Monaten - was hat sich KONKRET veraendert?",
                "Welche eine Sache wuerde dein Leben am meisten veraendern wenn sie morgen Realitaet waere?",
                "Was ist der EINE Satz der deine Vision beschreibt?",
            ],
            "strategy": [
                "Welcher Revenue-Kanal hat das beste Aufwand-zu-Ertrag-Verhaeltnis?",
                "Was ist der schnellste Weg zum ersten 10.000 EUR Monat?",
                "Welche Aufgaben sollten NIEMALS automatisiert werden?",
            ],
            "priorities": [
                "Wenn du heute nur EINE Sache erledigen koenntest - welche?",
                "Was ist gerade dein groesster Zeitfresser?",
                "Welche 3 Tasks wuerden 80% des Impacts bringen?",
            ],
            "preferences": [
                "Arbeitest du lieber morgens oder abends an wichtigen Sachen?",
                "Bevorzugst du schnelle Iteration oder gruendliche Planung?",
                "Wie triffst du Entscheidungen - Bauchgefuehl oder Daten?",
            ],
            "blockers": [
                "Was frustriert dich gerade am meisten am System?",
                "Welcher Blocker haelt dich seit ueber einer Woche auf?",
                "Was wuerdest du sofort aendern wenn du unbegrenztes Budget haettest?",
            ],
            "values": [
                "Was ist dir wichtiger: Schnelligkeit oder Qualitaet?",
                "Wuerdest du Kontrolle aufgeben fuer 10x mehr Geschwindigkeit?",
                "Welche Grenze wuerdest du nie ueberschreiten fuer Geld?",
            ],
            "lifestyle": [
                "Wie sieht dein perfekter Arbeitstag aus?",
                "Wieviel willst du noch selbst arbeiten wenn alles automatisiert ist?",
                "Was machst du mit dem Geld wenn das Ziel erreicht ist?",
            ],
        }
        questions = fallbacks.get(focus, fallbacks["vision"])[:count]
        return [
            {
                "id": f"FB-{i+1}",
                "question": q,
                "category": focus,
                "depth": "medium",
                "purpose": "Fallback-Frage",
                "expected_insight": "Grundlegende Vision-Information",
            }
            for i, q in enumerate(questions)
        ]

    # === Antworten verarbeiten ===

    async def process_answer(
        self,
        question_id: str,
        answer: str,
    ) -> Dict:
        """Verarbeitet eine Antwort und aktualisiert das Profil."""
        logger.info(f"Verarbeite Antwort fuer {question_id}")

        # Frage finden
        question = None
        for q in self.state.get("pending_questions", []):
            if q.get("id") == question_id:
                question = q
                break

        if not question:
            logger.warning(f"Frage {question_id} nicht gefunden")
            question = {"id": question_id, "question": "Unbekannte Frage", "category": "vision"}

        qa_pair = {
            "question": question.get("question", ""),
            "answer": answer,
            "category": question.get("category", "vision"),
            "timestamp": datetime.now().isoformat(),
        }

        # Gemini analysiert die Antwort
        processor_prompt = ANSWER_PROCESSOR_PROMPT.format(
            profile=json.dumps(self.profile, ensure_ascii=False)[:1500],
            qa_pair=json.dumps(qa_pair, ensure_ascii=False),
        )

        result = await self.client.chat_json(
            messages=[
                {"role": "system", "content": processor_prompt},
                {"role": "user", "content": f"Analysiere diese Antwort: {answer}"},
            ],
            model="flash",
            temperature=0.3,
        )

        analysis = result.get("parsed", {})

        # Profil aktualisieren
        updates = analysis.get("profile_updates", {})
        for key in ["known_preferences", "known_values", "known_blockers", "personality_traits"]:
            new_items = updates.get(key, [])
            existing = self.profile.get(key, [])
            for item in new_items:
                if item not in existing:
                    existing.append(item)
            self.profile[key] = existing

        # Vision Clarity Score aktualisieren
        total_answers = self.profile.get("total_answers", 0) + 1
        self.profile["total_answers"] = total_answers
        self.profile["vision_clarity_score"] = min(10, 1 + (total_answers * 0.1))
        self._save_profile()

        # Antwort in State speichern
        qa_record = {
            **qa_pair,
            "analysis": analysis,
            "question_id": question_id,
        }
        self.state["answers"].append(qa_record)
        self.state["total_answers_received"] = (
            self.state.get("total_answers_received", 0) + 1
        )

        # Frage als beantwortet markieren
        for q in self.state.get("pending_questions", []):
            if q.get("id") == question_id:
                q["answered"] = True
                break

        self._save_state()

        # Vision Memory aktualisieren
        self._update_vision_memory(qa_record, analysis)

        logger.info(f"✓ Antwort verarbeitet (Confidence: {analysis.get('confidence', '?')})")
        return {
            "status": "processed",
            "analysis": analysis,
            "profile_updated": bool(updates),
            "follow_up": analysis.get("follow_up_question") if analysis.get("follow_up_recommended") else None,
        }

    async def batch_process_answers(self, answers: List[Dict]) -> List[Dict]:
        """Verarbeitet mehrere Antworten auf einmal."""
        results = []
        for a in answers:
            result = await self.process_answer(a["question_id"], a["answer"])
            results.append(result)
        return results

    # === Vision Memory ===

    def _update_vision_memory(self, qa_record: Dict, analysis: Dict):
        """Aktualisiert das persistente Vision-Gedaechtnis."""
        memory = {}
        if VISION_MEMORY_FILE.exists():
            try:
                memory = json.loads(VISION_MEMORY_FILE.read_text())
            except json.JSONDecodeError:
                pass

        if "entries" not in memory:
            memory["entries"] = []
        if "summary" not in memory:
            memory["summary"] = {}

        memory["entries"].append({
            "timestamp": datetime.now().isoformat(),
            "question": qa_record.get("question", ""),
            "answer": qa_record.get("answer", ""),
            "category": qa_record.get("category", ""),
            "extracted_facts": analysis.get("extracted_facts", []),
            "strategic_implications": analysis.get("strategic_implications", []),
        })

        # Nur letzte 500 behalten
        memory["entries"] = memory["entries"][-500:]
        memory["last_updated"] = datetime.now().isoformat()
        memory["total_entries"] = len(memory["entries"])

        VISION_MEMORY_FILE.write_text(json.dumps(memory, indent=2, ensure_ascii=False))

    # === Zusammenfassung ===

    async def generate_vision_summary(self) -> Dict:
        """Generiert eine Zusammenfassung der gesammelten Vision."""
        all_answers = self.state.get("answers", [])
        if not all_answers:
            return {"error": "Keine Antworten vorhanden"}

        answers_text = json.dumps(all_answers[-50:], ensure_ascii=False)[:4000]

        result = await self.client.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": """Erstelle eine umfassende Vision-Zusammenfassung basierend auf allen Antworten.
Antworte als JSON:
{
  "vision_statement": "1-2 Saetze die Maurices Vision beschreiben",
  "core_goals": ["Top 5 Ziele"],
  "key_values": ["Top 5 Werte"],
  "decision_style": "Beschreibung wie er Entscheidungen trifft",
  "biggest_blockers": ["Top 3 Blocker"],
  "personality_summary": "Kurze Persoenlichkeitsbeschreibung",
  "strategic_direction": "Wohin geht die Reise",
  "confidence": 1-10,
  "missing_information": ["Was wir noch wissen muessen"]
}""",
                },
                {
                    "role": "user",
                    "content": f"Profil: {json.dumps(self.profile, ensure_ascii=False)[:1000]}\n\nAntworten: {answers_text}",
                },
            ],
            model="pro",
            temperature=0.5,
        )

        summary = result.get("parsed", {})

        # Summary in Memory speichern
        if VISION_MEMORY_FILE.exists():
            memory = json.loads(VISION_MEMORY_FILE.read_text())
        else:
            memory = {}
        memory["summary"] = summary
        memory["summary_generated"] = datetime.now().isoformat()
        VISION_MEMORY_FILE.write_text(json.dumps(memory, indent=2, ensure_ascii=False))

        return summary

    # === Status ===

    def get_status(self) -> Dict:
        """Gibt den Vision-Status zurueck."""
        pending = [q for q in self.state.get("pending_questions", []) if not q.get("answered")]
        return {
            "total_questions_asked": self.state.get("total_questions_asked", 0),
            "total_answers_received": self.state.get("total_answers_received", 0),
            "pending_questions": len(pending),
            "vision_clarity": self.profile.get("vision_clarity_score", 1),
            "known_preferences": len(self.profile.get("known_preferences", [])),
            "known_values": len(self.profile.get("known_values", [])),
            "known_blockers": len(self.profile.get("known_blockers", [])),
            "personality_traits": len(self.profile.get("personality_traits", [])),
        }

    def get_pending_questions(self) -> List[Dict]:
        """Gibt unbeantwortete Fragen zurueck."""
        return [
            q for q in self.state.get("pending_questions", [])
            if not q.get("answered")
        ]

    def show_status(self):
        """Zeigt Vision-Status an."""
        status = self.get_status()
        print("\n╔══════════════════════════════════════════╗")
        print("║    VISION INTERROGATOR - STATUS          ║")
        print("╚══════════════════════════════════════════╝")
        print(f"  Fragen gestellt:    {status['total_questions_asked']}")
        print(f"  Antworten erhalten: {status['total_answers_received']}")
        print(f"  Offen:              {status['pending_questions']}")
        print(f"  Vision-Klarheit:    {status['vision_clarity']}/10")
        print(f"  Praeferenzen:       {status['known_preferences']}")
        print(f"  Werte:              {status['known_values']}")
        print(f"  Blocker:            {status['known_blockers']}")
        print(f"  Persoenlichkeit:    {status['personality_traits']} Traits")

        pending = self.get_pending_questions()
        if pending:
            print("\n  Offene Fragen:")
            for q in pending[:5]:
                print(f"    [{q.get('id', '?')}] {q.get('question', '')[:80]}")
        print()


# === CLI ===

async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Vision Interrogator")
    parser.add_argument("--generate", action="store_true", help="Neue Fragen generieren")
    parser.add_argument("--focus", type=str, help="Fokus-Kategorie")
    parser.add_argument("--depth", choices=["surface", "medium", "deep"], default="medium")
    parser.add_argument("--count", type=int, default=5, help="Anzahl Fragen")
    parser.add_argument("--answer", nargs=2, metavar=("QUESTION_ID", "ANSWER"), help="Frage beantworten")
    parser.add_argument("--summary", action="store_true", help="Vision-Zusammenfassung")
    parser.add_argument("--status", action="store_true", help="Status anzeigen")
    parser.add_argument("--pending", action="store_true", help="Offene Fragen anzeigen")
    args = parser.parse_args()

    vi = VisionInterrogator()

    if args.status:
        vi.show_status()
    elif args.pending:
        questions = vi.get_pending_questions()
        for q in questions:
            print(f"\n[{q.get('id', '?')}] ({q.get('category', '?')}, {q.get('depth', '?')})")
            print(f"  {q.get('question', '')}")
    elif args.generate:
        questions = await vi.generate_daily_questions(
            focus=args.focus,
            count=args.count,
            depth=args.depth,
        )
        print(f"\n{len(questions)} Fragen generiert:")
        for q in questions:
            print(f"\n  [{q['id']}] {q['question']}")
            print(f"    Zweck: {q.get('purpose', '')[:80]}")
    elif args.answer:
        question_id, answer_text = args.answer
        result = await vi.process_answer(question_id, answer_text)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.summary:
        summary = await vi.generate_vision_summary()
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        vi.show_status()


if __name__ == "__main__":
    asyncio.run(main())
