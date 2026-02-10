#!/usr/bin/env python3
"""
CONTENT MACHINE - Die Geldmaschine.
Generiert 1000x Content fuer X/Twitter und TikTok mit Ollama (kostenlos).

1 Idee → 10+ Content Pieces (Posts, Threads, TikTok Scripts, Replies)
Batch-Modus: 100er Pakete in Minuten statt Stunden.

Architecture:
    ContentMachine
    ├── OllamaEngine     ($0 lokale Generation)
    ├── AgentManager     (Performance Tracking)
    ├── ContentQueue     (Warteschlange + Scheduling)
    ├── XContentFactory  (Posts, Threads, Replies)
    └── TikTokFactory    (Scripts im Hook-Problem-Steps-CTA Format)

Usage:
    python content_machine.py                    # Status
    python content_machine.py --generate 50      # 50 Content-Pieces generieren
    python content_machine.py --batch x          # Batch X-Content
    python content_machine.py --batch tiktok     # Batch TikTok Scripts
    python content_machine.py --multiply "text"  # 1 Idee → 10 Pieces
    python content_machine.py --weekly           # Kompletter Wochen-Plan
"""

import asyncio
import argparse
import json
import os
import sys
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent))

import logging

log = logging.getLogger(__name__)

try:
    from ollama_engine import OllamaEngine, LLMResponse
except Exception as e:
    OllamaEngine = None
    LLMResponse = None
    log.exception("ollama_engine import failed: %s", e)

try:
    from agent_manager import AgentManager
except Exception as e:
    AgentManager = None
    log.exception("agent_manager import failed: %s", e)

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = Path(__file__).parent / "state"
CONTENT_DIR = STATE_DIR / "content"
QUEUE_FILE = CONTENT_DIR / "content_queue.json"
STATS_FILE = CONTENT_DIR / "content_stats.json"

# ── Content Niches ───────────────────────────────────────────
NICHES = {
    "ai_automation": {
        "name": "AI Automation",
        "keywords": ["AI Agent", "Automatisierung", "Claude Code", "Ollama", "GPT", "Kimi"],
        "audience": "Unternehmer, Freelancer, Tech-Enthusiasten",
        "pain_points": ["zu viele manuelle Tasks", "hohe Kosten", "kein Tech-Team", "keine Zeit"],
        "hooks_de": [
            "Ich habe mein ganzes Business automatisiert.",
            "50.000 AI Agents arbeiten fuer mich. Kosten: 15 EUR/Tag.",
            "In 2 Stunden was andere in 2 Wochen schaffen.",
            "Warum zahlst du noch fuer Mitarbeiter?",
            "Das Tool das mir 10.000 EUR/Monat spart.",
            "AI ersetzt keine Jobs. AI ersetzt LANGSAME Leute.",
            "Mein Morgen: Kaffee. Laptop auf. Alles laeuft schon.",
            "90% der AI-Experten sind Faker. Hier ist der Beweis.",
        ],
    },
    "bma_ai": {
        "name": "BMA + AI (Nische)",
        "keywords": ["Brandmeldeanlage", "BMA", "Esser", "Hekatron", "Wartung", "DIN 14675"],
        "audience": "Errichter, Planer, Facility Manager, Brandschutzbeauftragte",
        "pain_points": ["Dokumentation frisst Zeit", "Wartungsprotokolle", "Normen-Updates", "Fachkraeftemangel"],
        "hooks_de": [
            "16 Jahre BMA-Erfahrung in einer AI gepackt.",
            "Brandmeldeanlagen + AI = die Zukunft der Wartung.",
            "Deine BMA-Dokumentation in 5 Minuten statt 5 Stunden.",
            "Esser, Hekatron, Siemens - ich kenne alle. Und jetzt macht es AI.",
            "Wartungsprotokolle die sich selbst schreiben.",
            "DIN 14675 Konformitaet auf Knopfdruck.",
        ],
    },
    "geld_verdienen": {
        "name": "Geld verdienen mit AI",
        "keywords": ["passives Einkommen", "Side Hustle", "Fiverr", "Gumroad", "Online Business"],
        "audience": "Anfaenger, Side Hustler, Wechselwillige",
        "pain_points": ["kein Startkapital", "keine Ahnung wo anfangen", "Angst vor Technik", "braucht schnelle Ergebnisse"],
        "hooks_de": [
            "Von 0 auf 1000 EUR mit einem einzigen Prompt.",
            "Dieses AI-Tool macht dir Geld im Schlaf.",
            "Kopiere diese Strategie. Verdiene damit.",
            "ChatGPT kann dir Geld verdienen. Hier ist wie.",
            "Ich habe 500 EUR verdient ohne eine Zeile Code.",
            "5 AI Side Hustles die JETZT funktionieren.",
            "Dein erster Euro mit AI. Heute noch.",
            "Die 3 besten Gumroad Produkte die AI fuer dich baut.",
        ],
    },
    "build_in_public": {
        "name": "Build in Public",
        "keywords": ["Transparenz", "Journey", "Startup", "Open Source", "Revenue"],
        "audience": "Indie Hacker, Gruender, Developer",
        "pain_points": ["Einsamkeit beim Bauen", "kein Feedback", "Motivation", "Sichtbarkeit"],
        "hooks_de": [
            "Tag {day}: AI Empire aufbauen. Ziel: 100k EUR/Monat.",
            "Was ich heute gebaut habe (und was es bringt):",
            "Mein Revenue-Dashboard. Alles offen. Alles ehrlich.",
            "Die Wahrheit ueber AI-Businesses die keiner erzaehlt.",
            "Fehler Nummer {n} auf dem Weg zu 100k.",
            "Woche {week}: {revenue} EUR Revenue. Hier ist was funktioniert.",
        ],
    },
}

# ── Post Styles ──────────────────────────────────────────────
STYLES = {
    "result": {
        "name": "Ergebnis-Post",
        "structure": "Hook (Zahl/Ergebnis) → Kontrast (ohne X, ohne Y) → Methode → CTA",
        "example": "25% mehr Umsatz in 4 Wochen.\n\nKeine neuen Mitarbeiter.\nKein groesseres Budget.\nNur AI-Agents.\n\nDM 'AI' fuer Details.",
    },
    "controversial": {
        "name": "Kontroverser Post",
        "structure": "Kontroverse These → Begruendung (3 Punkte) → Challenge",
        "example": "90% der AI-Experten haben nie eine Loesung deployed.\n\nSie verkaufen Slides.\nKeine Ergebnisse.\n\nFrag nach Case Studies. Die meisten werden still.",
    },
    "tutorial": {
        "name": "Tutorial/How-To",
        "structure": "Was du erreichst → 3-5 Schritte → Ergebnis → CTA",
        "example": "Vibe Coding in 4 Schritten:\n\n1. Sag der AI was du willst\n2. Sie schreibt den Code\n3. Du testest\n4. Repeat\n\nIch hab so mein CRM in 1h gebaut.",
    },
    "story": {
        "name": "Story/Journey",
        "structure": "Vorher (Problem) → Wendepunkt → Nachher (Ergebnis) → Lektion",
        "example": "16 Jahre Elektromeister.\nDann: AI entdeckt.\n\nJetzt automatisiere ich das\nwofuer andere Wochen brauchen.\n\nDie beste Investition? Zeit zum Lernen.",
    },
    "question": {
        "name": "Engagement-Frage",
        "structure": "Ehrliche Frage → 3 Optionen → CTA (Kommentar)",
        "example": "Ehrliche Frage:\n\nWas ist DEIN groesstes Problem\nbei Automatisierung?\n\n- Zu viele manuelle Tasks?\n- Keine Zeit?\n- Weiss nicht wo anfangen?\n\nKommentar - ich antworte allen.",
    },
    "behind_scenes": {
        "name": "Behind the Scenes",
        "structure": "Was heute passiert → 3-4 Tasks → Ergebnis → Einladung",
        "example": "Mein Setup heute:\n\n- 20 Claude Agents aktiv\n- 50K Kimi-Requests queued\n- CRM fuellt sich automatisch\n\nIch? Kaffee trinken.",
    },
    "thread_hook": {
        "name": "Thread-Start",
        "structure": "Starke Aussage + Thread-Emoji → Versprechen",
        "example": "Wie du 2026 mit AI Geld verdienst\n\n(Ohne Programmierer zu sein)\n\nThread:",
    },
}

# ── TikTok Templates ────────────────────────────────────────
TIKTOK_TEMPLATE = {
    "duration": "45 Sekunden",
    "structure": {
        "hook": {"time": "0-2s", "purpose": "Scroll-Stopper, provokant oder neugierig machend"},
        "problem": {"time": "2-7s", "purpose": "Relatables Problem der Zielgruppe zeigen"},
        "mini_story": {"time": "7-20s", "purpose": "Konkretes Beispiel oder Demo zeigen"},
        "steps": {"time": "20-35s", "purpose": "3 einfache Schritte zum Nachmachen"},
        "cta": {"time": "35-45s", "purpose": "Klarer CTA: Follow, Link in Bio, Kommentar"},
    },
}


class ContentQueue:
    """Warteschlange fuer generierten Content."""

    def __init__(self, queue_file: Path = QUEUE_FILE):
        self.queue_file = queue_file
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        self.items = self._load()

    def _load(self) -> list:
        if self.queue_file.exists():
            try:
                return json.loads(self.queue_file.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return []

    def save(self):
        self.queue_file.write_text(json.dumps(self.items, indent=2, ensure_ascii=False))

    def add(self, item: dict):
        item["id"] = len(self.items) + 1
        item["created_at"] = datetime.now().isoformat()
        item["status"] = "ready"
        self.items.append(item)
        self.save()

    def get_ready(self, platform: str = "", limit: int = 10) -> list:
        ready = [i for i in self.items if i["status"] == "ready"]
        if platform:
            ready = [i for i in ready if i.get("platform") == platform]
        return ready[:limit]

    def mark_posted(self, item_id: int):
        for item in self.items:
            if item["id"] == item_id:
                item["status"] = "posted"
                item["posted_at"] = datetime.now().isoformat()
                break
        self.save()

    def stats(self) -> dict:
        total = len(self.items)
        ready = sum(1 for i in self.items if i["status"] == "ready")
        posted = sum(1 for i in self.items if i["status"] == "posted")
        x_count = sum(1 for i in self.items if i.get("platform") == "x")
        tiktok_count = sum(1 for i in self.items if i.get("platform") == "tiktok")
        return {
            "total": total,
            "ready": ready,
            "posted": posted,
            "x": x_count,
            "tiktok": tiktok_count,
        }


class ContentMachine:
    """Die Geldmaschine - 1000x Content auf Knopfdruck."""

    def __init__(self):
        CONTENT_DIR.mkdir(parents=True, exist_ok=True)
        if OllamaEngine is not None:
            self.ollama = OllamaEngine()
        else:
            self.ollama = None
            log.warning("OllamaEngine not available - ContentMachine limited")
        if AgentManager is not None:
            self.agents = AgentManager()
        else:
            self.agents = None
            log.warning("AgentManager not available")
        self.queue = ContentQueue()
        self._stats = self._load_stats()

    def _load_stats(self) -> dict:
        if STATS_FILE.exists():
            try:
                return json.loads(STATS_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {
            "total_generated": 0,
            "x_posts": 0,
            "x_threads": 0,
            "tiktok_scripts": 0,
            "replies": 0,
            "multiplied": 0,
            "ollama_calls": 0,
            "total_tokens": 0,
            "created": datetime.now().isoformat(),
        }

    def _save_stats(self):
        self._stats["updated"] = datetime.now().isoformat()
        STATS_FILE.write_text(json.dumps(self._stats, indent=2, ensure_ascii=False))

    # ── X/Twitter Content Generation ─────────────────────────

    async def generate_x_post(
        self,
        niche: str = "ai_automation",
        style: str = "result",
        custom_topic: str = "",
    ) -> dict:
        """Generiert einen X/Twitter Post mit Ollama."""
        niche_data = NICHES.get(niche, NICHES["ai_automation"])
        style_data = STYLES.get(style, STYLES["result"])

        hook = random.choice(niche_data["hooks_de"])
        pain = random.choice(niche_data["pain_points"])
        topic = custom_topic or f"{niche_data['name']}: {pain}"

        prompt = f"""Schreibe einen X/Twitter Post.

THEMA: {topic}
ZIELGRUPPE: {niche_data['audience']}
STIL: {style_data['name']} - {style_data['structure']}

BEISPIEL:
{style_data['example']}

REGELN:
1. Max 280 Zeichen (kurz und knackig)
2. Erste Zeile = Hook (Scroll-Stopper)
3. KEINE Hashtags im Text
4. Kein "Hey" oder "Hallo"
5. Maximal 1 Emoji
6. Call-to-Action am Ende
7. Deutsch
8. INSPIRATION fuer Hook: "{hook}"

Schreibe NUR den Post-Text, nichts anderes:"""

        if self.ollama is None:
            return {"error": "OllamaEngine not available", "platform": "x", "type": "post"}

        response = await self.ollama.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.85,
            max_tokens=500,
        )

        self._stats["ollama_calls"] += 1
        self._stats["total_tokens"] += response.tokens

        if response.success:
            content = response.content.strip().strip('"').strip("'")
            post = {
                "platform": "x",
                "type": "post",
                "content": content,
                "niche": niche,
                "style": style,
                "topic": topic,
                "model": response.model,
                "tokens": response.tokens,
                "duration_ms": response.duration_ms,
            }
            self.queue.add(post)
            self._stats["x_posts"] += 1
            self._stats["total_generated"] += 1
            self._save_stats()
            return post
        else:
            return {"error": response.error, "platform": "x", "type": "post"}

    async def generate_x_thread(
        self,
        niche: str = "ai_automation",
        topic: str = "",
        parts: int = 7,
    ) -> dict:
        """Generiert einen X/Twitter Thread."""
        niche_data = NICHES.get(niche, NICHES["ai_automation"])
        topic = topic or f"Wie du mit {niche_data['name']} Geld verdienst"

        prompt = f"""Schreibe einen X/Twitter Thread mit {parts} Posts.

THEMA: {topic}
ZIELGRUPPE: {niche_data['audience']}

FORMAT:
1/{parts}
[Hook Post mit Thread-Emoji am Ende]

2/{parts}
[Erster Punkt]

...

{parts}/{parts}
[CTA: Follow + Like + Retweet]

REGELN:
1. Jeder Post max 280 Zeichen
2. Post 1 = starker Hook
3. Jeder Post steht fuer sich (verstaendlich auch ohne Kontext)
4. Praktischer Mehrwert in jedem Post
5. Letzter Post = CTA
6. Deutsch
7. Max 1 Emoji pro Post

Schreibe den kompletten Thread:"""

        if self.ollama is None:
            return {"error": "OllamaEngine not available", "platform": "x", "type": "thread"}

        response = await self.ollama.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=2000,
        )

        self._stats["ollama_calls"] += 1
        self._stats["total_tokens"] += response.tokens

        if response.success:
            thread = {
                "platform": "x",
                "type": "thread",
                "content": response.content.strip(),
                "niche": niche,
                "topic": topic,
                "parts": parts,
                "model": response.model,
                "tokens": response.tokens,
                "duration_ms": response.duration_ms,
            }
            self.queue.add(thread)
            self._stats["x_threads"] += 1
            self._stats["total_generated"] += 1
            self._save_stats()
            return thread
        else:
            return {"error": response.error, "platform": "x", "type": "thread"}

    async def generate_x_reply(
        self,
        original_tweet: str,
        goal: str = "Mehrwert geben und Expertise zeigen",
    ) -> dict:
        """Generiert eine strategische Reply."""
        prompt = f"""Schreibe eine Reply auf diesen Tweet:

ORIGINAL: {original_tweet}

ZIEL: {goal}

REGELN:
1. Max 280 Zeichen
2. NICHT salesy
3. Echten Tipp oder Mehrwert geben
4. Subtil Expertise zeigen
5. Frage stellen um Gespraech zu starten
6. Deutsch

Schreibe NUR die Reply:"""

        if self.ollama is None:
            return {"error": "OllamaEngine not available"}

        response = await self.ollama.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=300,
        )

        self._stats["ollama_calls"] += 1
        self._stats["total_tokens"] += response.tokens

        if response.success:
            reply = {
                "platform": "x",
                "type": "reply",
                "content": response.content.strip().strip('"'),
                "original": original_tweet[:100],
                "goal": goal,
            }
            self._stats["replies"] += 1
            self._stats["total_generated"] += 1
            self._save_stats()
            return reply
        else:
            return {"error": response.error}

    # ── TikTok Content Generation ────────────────────────────

    async def generate_tiktok_script(
        self,
        niche: str = "geld_verdienen",
        custom_topic: str = "",
    ) -> dict:
        """Generiert ein TikTok-Script im bewaehrten Format."""
        niche_data = NICHES.get(niche, NICHES["geld_verdienen"])
        hook = random.choice(niche_data["hooks_de"])
        pain = random.choice(niche_data["pain_points"])
        topic = custom_topic or f"{niche_data['name']}: {pain}"

        prompt = f"""Schreibe ein TikTok-Video-Script (45 Sekunden).

THEMA: {topic}
ZIELGRUPPE: {niche_data['audience']}

FORMAT (GENAU so):
Hook (0-2s): [Scroll-Stopper, max 10 Woerter, provokant]
Problem (2-7s): [Relatables Problem zeigen, warum ist das wichtig]
Mini-Story (7-20s): [Konkretes Beispiel, Demo, Beweis]
3 Steps (20-35s): Schritt 1 - [Action]. Schritt 2 - [Action]. Schritt 3 - [Action].
CTA (35-45s): [Follow/Link in Bio/Kommentar Aufforderung]
Caption: [Max 150 Zeichen, catchy]
Hashtags: [5-7 relevante Hashtags]

INSPIRATION Hook: "{hook}"

REGELN:
1. Einfache Sprache (Niveau: 15-Jaehriger versteht es)
2. Konkrete Zahlen und Beispiele
3. Jeder Schritt sofort umsetzbar
4. Deutsche Sprache
5. Hook muss SOFORT Neugier wecken

Schreibe das komplette Script:"""

        if self.ollama is None:
            return {"error": "OllamaEngine not available", "platform": "tiktok", "type": "script"}

        response = await self.ollama.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.85,
            max_tokens=800,
        )

        self._stats["ollama_calls"] += 1
        self._stats["total_tokens"] += response.tokens

        if response.success:
            script = {
                "platform": "tiktok",
                "type": "script",
                "content": response.content.strip(),
                "niche": niche,
                "topic": topic,
                "model": response.model,
                "tokens": response.tokens,
                "duration_ms": response.duration_ms,
            }
            self.queue.add(script)
            self._stats["tiktok_scripts"] += 1
            self._stats["total_generated"] += 1
            self._save_stats()
            return script
        else:
            return {"error": response.error, "platform": "tiktok", "type": "script"}

    # ── Content Multiplier ───────────────────────────────────

    async def multiply(self, idea: str, count: int = 10) -> list:
        """1 Idee → N Content Pieces (X Posts + TikTok Scripts + Thread)."""
        print(f"\n  CONTENT MULTIPLIER: '{idea[:50]}...' → {count} Pieces")

        results = []

        # Mix aus verschiedenen Content-Typen
        tasks = []
        for i in range(count):
            niche = random.choice(list(NICHES.keys()))
            if i % 5 == 0:
                # Thread
                tasks.append(("thread", niche, idea))
            elif i % 3 == 0:
                # TikTok
                tasks.append(("tiktok", niche, idea))
            else:
                # X Post
                style = random.choice(list(STYLES.keys()))
                tasks.append(("post", niche, idea, style))

        for idx, task in enumerate(tasks):
            print(f"\r    Generating {idx + 1}/{count}...", end="", flush=True)
            try:
                if task[0] == "thread":
                    result = await self.generate_x_thread(niche=task[1], topic=task[2])
                elif task[0] == "tiktok":
                    result = await self.generate_tiktok_script(niche=task[1], custom_topic=task[2])
                else:
                    result = await self.generate_x_post(
                        niche=task[1], style=task[3], custom_topic=task[2]
                    )
                results.append(result)
            except Exception as e:
                results.append({"error": str(e), "type": task[0]})

        self._stats["multiplied"] += count
        self._save_stats()

        print(f"\n    Done! {len([r for r in results if 'error' not in r])}/{count} erfolgreich")
        return results

    # ── Batch Generation ─────────────────────────────────────

    async def batch_x(self, count: int = 20) -> list:
        """Batch-Generierung von X/Twitter Content."""
        print(f"\n  BATCH X CONTENT: {count} Pieces")
        results = []

        for i in range(count):
            niche = random.choice(list(NICHES.keys()))
            style = random.choice(list(STYLES.keys()))
            print(f"\r    [{i+1}/{count}] {niche}/{style}...", end="", flush=True)

            try:
                if style == "thread_hook" and i % 5 == 0:
                    result = await self.generate_x_thread(niche=niche)
                else:
                    result = await self.generate_x_post(niche=niche, style=style)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})

        ok = len([r for r in results if "error" not in r])
        print(f"\n    Done! {ok}/{count} erfolgreich")
        return results

    async def batch_tiktok(self, count: int = 10) -> list:
        """Batch-Generierung von TikTok Scripts."""
        print(f"\n  BATCH TIKTOK SCRIPTS: {count} Scripts")
        results = []

        for i in range(count):
            niche = random.choice(list(NICHES.keys()))
            print(f"\r    [{i+1}/{count}] {niche}...", end="", flush=True)

            try:
                result = await self.generate_tiktok_script(niche=niche)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})

        ok = len([r for r in results if "error" not in r])
        print(f"\n    Done! {ok}/{count} erfolgreich")
        return results

    # ── Weekly Content Plan ──────────────────────────────────

    async def generate_weekly_plan(self) -> dict:
        """Kompletter Wochen-Content-Plan: 7 Posts + 1 Thread + 5 TikToks."""
        print("\n  WEEKLY CONTENT PLAN")
        print("  7 X-Posts + 1 Thread + 5 TikTok Scripts")

        plan = {
            "week_start": datetime.now().strftime("%Y-%m-%d"),
            "posts": [],
            "thread": None,
            "tiktoks": [],
        }

        # Tagesplan
        day_plan = [
            {"day": "Montag", "style": "result", "niche": "ai_automation"},
            {"day": "Dienstag", "style": "tutorial", "niche": "geld_verdienen"},
            {"day": "Mittwoch", "style": "controversial", "niche": "ai_automation"},
            {"day": "Donnerstag", "style": "behind_scenes", "niche": "build_in_public"},
            {"day": "Freitag", "style": "story", "niche": "bma_ai"},
            {"day": "Samstag", "style": "question", "niche": "ai_automation"},
            {"day": "Sonntag", "style": "result", "niche": "geld_verdienen"},
        ]

        # 7 Daily Posts
        for dp in day_plan:
            print(f"    {dp['day']}: {dp['style']}/{dp['niche']}...")
            post = await self.generate_x_post(niche=dp["niche"], style=dp["style"])
            post["scheduled_day"] = dp["day"]
            plan["posts"].append(post)

        # 1 Sunday Thread
        print("    Sonntag Thread...")
        thread = await self.generate_x_thread(
            niche="ai_automation",
            topic="Wie du 2026 mit AI ein Business aufbaust - Schritt fuer Schritt",
        )
        plan["thread"] = thread

        # 5 TikTok Scripts
        tiktok_niches = ["geld_verdienen", "ai_automation", "bma_ai", "geld_verdienen", "build_in_public"]
        for i, niche in enumerate(tiktok_niches):
            print(f"    TikTok {i+1}: {niche}...")
            script = await self.generate_tiktok_script(niche=niche)
            plan["tiktoks"].append(script)

        # Speichern als Markdown
        md = self._plan_to_markdown(plan)
        week_str = datetime.now().strftime("%Y%m%d")
        md_file = CONTENT_DIR / f"weekly_plan_{week_str}.md"
        md_file.write_text(md, encoding="utf-8")
        print(f"\n    Saved: {md_file}")

        return plan

    def _plan_to_markdown(self, plan: dict) -> str:
        lines = [
            f"# WEEKLY CONTENT PLAN - {plan['week_start']}",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "---",
            "",
            "## X/TWITTER POSTS",
            "",
        ]

        for post in plan["posts"]:
            day = post.get("scheduled_day", "?")
            style = post.get("style", "?")
            content = post.get("content", post.get("error", "Error"))
            lines.extend([
                f"### {day} - {style.upper()}",
                "```",
                content,
                "```",
                "",
            ])

        if plan.get("thread"):
            lines.extend([
                "---",
                "",
                "## SUNDAY THREAD",
                "```",
                plan["thread"].get("content", "Error"),
                "```",
                "",
            ])

        lines.extend(["---", "", "## TIKTOK SCRIPTS", ""])
        for i, tt in enumerate(plan.get("tiktoks", []), 1):
            lines.extend([
                f"### TikTok Script {i} ({tt.get('niche', '?')})",
                "```",
                tt.get("content", tt.get("error", "Error")),
                "```",
                "",
            ])

        lines.extend([
            "---",
            "",
            "## POSTING SCHEDULE",
            "",
            "| Tag | Platform | Type | Status |",
            "|-----|----------|------|--------|",
        ])
        for post in plan["posts"]:
            day = post.get("scheduled_day", "?")
            lines.append(f"| {day} | X | {post.get('style', '?')} | Ready |")
        lines.append("| Sonntag | X | Thread | Ready |")
        for i in range(len(plan.get("tiktoks", []))):
            lines.append(f"| TikTok {i+1} | TikTok | Script | Ready |")

        lines.extend([
            "",
            "---",
            "",
            "## HASHTAGS",
            "```",
            "#AIAutomation #ClaudeCode #BuildInPublic #AI #Automation #KI #GeldVerdienen",
            "```",
        ])

        return "\n".join(lines)

    # ── Export ────────────────────────────────────────────────

    def export_ready_content(self, platform: str = "", limit: int = 20) -> str:
        """Exportiert fertigen Content als Markdown."""
        items = self.queue.get_ready(platform=platform, limit=limit)
        if not items:
            return "Keine fertigen Inhalte in der Queue."

        lines = [
            f"# READY TO POST - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Items: {len(items)}",
            "",
        ]

        for item in items:
            pf = item.get("platform", "?").upper()
            tp = item.get("type", "?")
            lines.extend([
                f"## [{pf}] {tp.upper()} #{item.get('id', '?')}",
                f"Niche: {item.get('niche', '?')} | Style: {item.get('style', '?')}",
                "```",
                item.get("content", ""),
                "```",
                "",
            ])

        return "\n".join(lines)

    # ── Status ───────────────────────────────────────────────

    def show_status(self):
        """Zeigt Content Machine Status."""
        q = self.queue.stats()
        s = self._stats

        print(f"""
{'='*60}
  CONTENT MACHINE - Geldmaschine Status
{'='*60}

  GENERATION STATS:
    Total Generated:  {s['total_generated']}
    X Posts:          {s['x_posts']}
    X Threads:        {s['x_threads']}
    TikTok Scripts:   {s['tiktok_scripts']}
    Replies:          {s['replies']}
    Multiplied:       {s['multiplied']}
    Ollama Calls:     {s['ollama_calls']}
    Total Tokens:     {s['total_tokens']:,}
    Cost:             $0.00 (Ollama = free)

  CONTENT QUEUE:
    Total:            {q['total']}
    Ready to Post:    {q['ready']}
    Already Posted:   {q['posted']}
    X Content:        {q['x']}
    TikTok Content:   {q['tiktok']}

  NICHES:
    {', '.join(NICHES.keys())}

  STYLES:
    {', '.join(STYLES.keys())}

  COMMANDS:
    python content_machine.py --generate 50
    python content_machine.py --batch x
    python content_machine.py --batch tiktok
    python content_machine.py --multiply "deine idee"
    python content_machine.py --weekly
    python content_machine.py --export
{'='*60}""")


async def main():
    parser = argparse.ArgumentParser(description="Content Machine - Geldmaschine")
    parser.add_argument("--generate", type=int, metavar="N", help="N Content-Pieces generieren")
    parser.add_argument("--batch", choices=["x", "tiktok", "both"], help="Batch-Generierung")
    parser.add_argument("--multiply", type=str, metavar="IDEA", help="1 Idee → 10 Pieces")
    parser.add_argument("--weekly", action="store_true", help="Kompletter Wochen-Plan")
    parser.add_argument("--export", action="store_true", help="Fertigen Content exportieren")
    parser.add_argument("--count", type=int, default=10, help="Anzahl (default: 10)")
    args = parser.parse_args()

    machine = ContentMachine()

    if args.generate:
        results = await machine.batch_x(args.generate)
        print(f"\n  {len([r for r in results if 'error' not in r])} Posts generiert!")

    elif args.batch:
        if args.batch in ("x", "both"):
            await machine.batch_x(args.count)
        if args.batch in ("tiktok", "both"):
            await machine.batch_tiktok(args.count)

    elif args.multiply:
        await machine.multiply(args.multiply, args.count)

    elif args.weekly:
        await machine.generate_weekly_plan()

    elif args.export:
        md = machine.export_ready_content()
        print(md)

    else:
        machine.show_status()


if __name__ == "__main__":
    asyncio.run(main())
