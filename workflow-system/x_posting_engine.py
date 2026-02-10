#!/usr/bin/env python3
"""
X POSTING ENGINE - Automatisierte X/Twitter Content Pipeline.
Generiert, queued und bereitet Posts zum Posten vor.

Features:
- Queue-basiertes Posting-System mit Scheduling
- Mass-Generation mit Ollama ($0)
- Viral Reply Engine fuer Engagement
- DM-Sequence Generator fuer Lead Nurturing
- Trending Topic Integration
- Performance Tracking

Usage:
    python x_posting_engine.py                     # Status
    python x_posting_engine.py --generate 30       # 30 Posts generieren
    python x_posting_engine.py --replies 10        # 10 Replies vorbereiten
    python x_posting_engine.py --weekly            # Wochenplan
    python x_posting_engine.py --export            # Ready-to-Post exportieren
    python x_posting_engine.py --dm "lead info"    # DM-Sequence
"""

import asyncio
import argparse
import json
import os
import sys
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

import logging

log = logging.getLogger(__name__)

try:
    from ollama_engine import OllamaEngine, LLMResponse
except Exception as e:
    OllamaEngine = None
    LLMResponse = None
    log.exception("ollama_engine import failed: %s", e)

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = Path(__file__).parent / "state"
X_DIR = STATE_DIR / "x_content"
POSTS_FILE = X_DIR / "all_posts.json"
SCHEDULE_FILE = X_DIR / "schedule.json"

# ── Maurice's Brand Voice ─────────────────────────────────────

BRAND_VOICE = """Du schreibst als Maurice Pfeifer - Elektrotechnikmeister mit 16 Jahren BMA-Erfahrung,
jetzt AI-Automation-Experte. Tonfall: Direkt, keine Floskel, Ergebnis-orientiert.
Kein Bullshit, keine leeren Versprechen. Konkrete Zahlen, echte Beispiele.
Du sprichst Deutsch, klar und verstaendlich. Wie ein Kumpel der sich auskennt."""

# ── Trending Topics (Live-Update via Content Machine) ────────

CURRENT_TRENDS = [
    {"topic": "Claude Code und AI Agents", "buzz": 5, "hashtags": ["#ClaudeCode", "#AIAgents"]},
    {"topic": "Vibe Coding - AI schreibt den Code", "buzz": 4, "hashtags": ["#VibeCoding", "#AI"]},
    {"topic": "MCP Model Context Protocol", "buzz": 4, "hashtags": ["#MCP", "#Anthropic"]},
    {"topic": "50.000 AI Agents gleichzeitig", "buzz": 5, "hashtags": ["#AISwarm", "#Automation"]},
    {"topic": "Ollama - kostenlose lokale AI", "buzz": 3, "hashtags": ["#Ollama", "#LocalAI"]},
    {"topic": "Build in Public Journey", "buzz": 4, "hashtags": ["#BuildInPublic", "#IndieHacker"]},
    {"topic": "AI Automation Agency starten", "buzz": 4, "hashtags": ["#AIAgency", "#Business"]},
    {"topic": "BMA + AI - unbesetzte Nische", "buzz": 3, "hashtags": ["#BMA", "#PropTech"]},
    {"topic": "Geld verdienen mit AI 2026", "buzz": 5, "hashtags": ["#AI", "#GeldVerdienen"]},
    {"topic": "ChatGPT vs Claude vs Gemini", "buzz": 4, "hashtags": ["#ChatGPT", "#Claude"]},
]

# ── Post Types with Structures ───────────────────────────────

POST_TYPES = {
    "single": {
        "max_chars": 280,
        "structure": "Hook → Content → CTA",
    },
    "thread": {
        "max_per_post": 280,
        "parts": 7,
        "structure": "Hook-Post → 5 Value Posts → CTA Post",
    },
    "reply": {
        "max_chars": 280,
        "structure": "Mehrwert → Expertise-Hint → Frage",
    },
    "dm": {
        "max_chars": 1000,
        "structure": "Bezug → Wert → Soft CTA",
    },
}

# ── Engagement Hooks (Proven Patterns) ───────────────────────

HOOKS = {
    "numbers": [
        "{N}% mehr {result} in {time}.",
        "Von 0 auf {N} {unit} in {time}.",
        "{N} {unit} gespart. Jeden Monat.",
        "In {time}: {N} {result}. Ohne {obstacle}.",
    ],
    "contrast": [
        "Andere machen {old}. Ich mache {new}.",
        "Ohne {without1}. Ohne {without2}. Nur {method}.",
        "{old_way} = Vergangenheit. {new_way} = Zukunft.",
    ],
    "authority": [
        "{years} Jahre {field}. Dann: {pivot}.",
        "Nachdem ich {achievement}: Mein Fazit.",
        "Was {n} Projekte mich gelehrt haben:",
    ],
    "controversy": [
        "Unpopular Opinion: {statement}",
        "{percent}% der {group} machen {mistake}.",
        "Hot Take: {claim}",
    ],
    "curiosity": [
        "Dieser eine Trick hat alles veraendert.",
        "Keiner redet darueber. Aber:",
        "Was ich in {time} gelernt habe:",
    ],
}

# ── Scheduling Templates ─────────────────────────────────────

WEEKLY_SCHEDULE = {
    "Montag": {"type": "result", "time": "09:00", "trend_idx": 0},
    "Dienstag": {"type": "tutorial", "time": "12:00", "trend_idx": 1},
    "Mittwoch": {"type": "controversial", "time": "18:00", "trend_idx": 2},
    "Donnerstag": {"type": "behind_scenes", "time": "09:00", "trend_idx": 5},
    "Freitag": {"type": "story", "time": "12:00", "trend_idx": 7},
    "Samstag": {"type": "question", "time": "10:00", "trend_idx": 8},
    "Sonntag": {"type": "thread", "time": "11:00", "trend_idx": 3},
}


class XPostingEngine:
    """X/Twitter Content Pipeline - Generate, Queue, Schedule, Post."""

    def __init__(self):
        X_DIR.mkdir(parents=True, exist_ok=True)
        if OllamaEngine is not None:
            self.ollama = OllamaEngine()
        else:
            self.ollama = None
            log.warning("OllamaEngine not available - XPostingEngine limited")
        self.posts = self._load_posts()
        self.schedule = self._load_schedule()

    def _load_posts(self) -> list:
        if POSTS_FILE.exists():
            try:
                return json.loads(POSTS_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return []

    def _save_posts(self):
        POSTS_FILE.write_text(json.dumps(self.posts, indent=2, ensure_ascii=False))

    def _load_schedule(self) -> list:
        if SCHEDULE_FILE.exists():
            try:
                return json.loads(SCHEDULE_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return []

    def _save_schedule(self):
        SCHEDULE_FILE.write_text(json.dumps(self.schedule, indent=2, ensure_ascii=False))

    # ── Post Generation ──────────────────────────────────────

    async def generate_post(
        self,
        topic: str = "",
        style: str = "result",
        trend: Optional[dict] = None,
    ) -> dict:
        """Generiert einen X Post."""
        if not topic and trend:
            topic = trend["topic"]
        elif not topic:
            trend = random.choice(CURRENT_TRENDS)
            topic = trend["topic"]

        styles_map = {
            "result": "Zeige ein konkretes Ergebnis mit Zahlen. Hook + Kontrast + CTA.",
            "tutorial": "Schritt-fuer-Schritt Anleitung. 3-5 nummerierte Schritte.",
            "controversial": "Kontroverse These die Diskussion startet. Faktenbasiert.",
            "behind_scenes": "Zeig was du baust. Transparent, authentisch.",
            "story": "Kurze Story: Problem → Wendepunkt → Lektion.",
            "question": "Engagement-Frage. Echt interessiert. Mit Optionen.",
        }

        style_desc = styles_map.get(style, styles_map["result"])

        prompt = f"""{BRAND_VOICE}

Schreibe einen X/Twitter Post.

THEMA: {topic}
STIL: {style_desc}

REGELN:
1. MAXIMAL 280 Zeichen - STRENG!
2. Erste Zeile = Hook (Scroll-Stopper)
3. KEINE Hashtags im Text
4. Kein "Hey", "Hallo", "Hi"
5. Max 1 Emoji
6. Call-to-Action am Ende
7. Deutsch
8. Kurze Saetze. Zeilenumbrueche nutzen.

Schreibe NUR den Post-Text:"""

        if self.ollama is None:
            return {"error": "OllamaEngine not available"}

        response = await self.ollama.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.85,
            max_tokens=400,
        )

        if response.success:
            content = response.content.strip().strip('"').strip("'")
            post = {
                "id": len(self.posts) + 1,
                "type": "single",
                "style": style,
                "topic": topic,
                "content": content,
                "hashtags": trend.get("hashtags", ["#AI", "#Automation"]) if trend else ["#AI"],
                "model": response.model,
                "tokens": response.tokens,
                "created_at": datetime.now().isoformat(),
                "status": "ready",
                "engagement": {"likes": 0, "replies": 0, "retweets": 0, "impressions": 0},
            }
            self.posts.append(post)
            self._save_posts()
            return post
        else:
            return {"error": response.error}

    async def generate_thread(self, topic: str = "", parts: int = 7) -> dict:
        """Generiert einen X Thread."""
        if not topic:
            trend = random.choice(CURRENT_TRENDS)
            topic = trend["topic"]

        prompt = f"""{BRAND_VOICE}

Schreibe einen X/Twitter Thread mit {parts} Posts zum Thema: {topic}

FORMAT:
1/{parts}
[Hook mit Thread-Hinweis am Ende]

2/{parts}
[Erster Punkt - konkreter Mehrwert]

...

{parts}/{parts}
[CTA: Follow + Like + Retweet]

REGELN:
1. JEDER Post max 280 Zeichen
2. Post 1 muss Neugier wecken
3. Jeder Post steht fuer sich
4. Praktischer Mehrwert
5. Letzter Post = starker CTA
6. Deutsch
7. Max 1 Emoji pro Post

Schreibe den Thread:"""

        if self.ollama is None:
            return {"error": "OllamaEngine not available"}

        response = await self.ollama.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=2500,
        )

        if response.success:
            thread = {
                "id": len(self.posts) + 1,
                "type": "thread",
                "topic": topic,
                "content": response.content.strip(),
                "parts": parts,
                "model": response.model,
                "tokens": response.tokens,
                "created_at": datetime.now().isoformat(),
                "status": "ready",
            }
            self.posts.append(thread)
            self._save_posts()
            return thread
        else:
            return {"error": response.error}

    async def generate_reply(
        self,
        original_tweet: str,
        context: str = "AI Automation Expertise zeigen",
    ) -> dict:
        """Generiert eine strategische Reply."""
        prompt = f"""{BRAND_VOICE}

Schreibe eine Reply auf diesen Tweet:

ORIGINAL: {original_tweet}

ZIEL: {context}

REGELN:
1. Max 280 Zeichen
2. NICHT salesy oder aufdringlich
3. Echten Tipp oder Mehrwert geben
4. Subtil auf Expertise hinweisen
5. Offene Frage am Ende
6. Deutsch

Schreibe NUR die Reply:"""

        if self.ollama is None:
            return {"error": "OllamaEngine not available"}

        response = await self.ollama.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=300,
        )

        if response.success:
            reply = {
                "id": len(self.posts) + 1,
                "type": "reply",
                "original_tweet": original_tweet[:200],
                "content": response.content.strip().strip('"'),
                "context": context,
                "created_at": datetime.now().isoformat(),
                "status": "ready",
            }
            self.posts.append(reply)
            self._save_posts()
            return reply
        else:
            return {"error": response.error}

    async def generate_dm_sequence(self, lead_name: str, lead_interest: str, lead_tweet: str = "") -> dict:
        """Generiert 3-DM Nurture Sequence fuer einen Lead."""
        prompt = f"""{BRAND_VOICE}

Erstelle eine 3-DM Sequence fuer diesen Lead:

NAME: {lead_name}
INTERESSE: {lead_interest}
ORIGINAL TWEET: {lead_tweet}

ZIEL: Termin fuer 15-Min Discovery Call

DM 1 (Tag 0): Erster Kontakt - warm, Bezug auf Tweet, echtes Interesse
DM 2 (Tag 2): Mehr Wert geben - konkreten Tipp oder Resource teilen
DM 3 (Tag 4): Letzter Versuch - CTA zum Call, kein Druck

FORMAT (als JSON Array):
[
  {{"day": 0, "subject": "Erster Kontakt", "message": "..."}},
  {{"day": 2, "subject": "Value Add", "message": "..."}},
  {{"day": 4, "subject": "Soft Close", "message": "..."}}
]

REGELN:
1. Kein Copy-Paste Gefuehl
2. Persoenlich und authentisch
3. Maximal 500 Zeichen pro DM
4. Jede DM gibt Mehrwert
5. Deutsch

Schreibe die Sequence als JSON:"""

        if self.ollama is None:
            return {"error": "OllamaEngine not available"}

        response = await self.ollama.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000,
        )

        if response.success:
            try:
                # Try to parse JSON from response
                content = response.content.strip()
                # Find JSON array in response
                start = content.find("[")
                end = content.rfind("]") + 1
                if start >= 0 and end > start:
                    sequence = json.loads(content[start:end])
                else:
                    sequence = [{"day": 0, "message": content}]
            except (json.JSONDecodeError, ValueError):
                sequence = [{"day": 0, "message": response.content}]

            dm = {
                "id": len(self.posts) + 1,
                "type": "dm_sequence",
                "lead_name": lead_name,
                "lead_interest": lead_interest,
                "sequence": sequence,
                "created_at": datetime.now().isoformat(),
                "status": "ready",
            }
            self.posts.append(dm)
            self._save_posts()
            return dm
        else:
            return {"error": response.error}

    # ── Batch Operations ─────────────────────────────────────

    async def batch_generate(self, count: int = 20) -> list:
        """Batch-Generierung von X Posts."""
        print(f"\n  X POSTING ENGINE: Generiere {count} Posts")
        results = []
        start = time.time()

        styles = ["result", "tutorial", "controversial", "behind_scenes", "story", "question"]

        for i in range(count):
            trend = random.choice(CURRENT_TRENDS)
            style = styles[i % len(styles)]
            print(f"\r    [{i+1}/{count}] {style} / {trend['topic'][:30]}...", end="", flush=True)

            try:
                if i > 0 and i % 7 == 0:
                    # Every 7th: Thread
                    result = await self.generate_thread(topic=trend["topic"])
                else:
                    result = await self.generate_post(topic=trend["topic"], style=style, trend=trend)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})

        elapsed = time.time() - start
        ok = len([r for r in results if "error" not in r])
        print(f"\n    Fertig! {ok}/{count} in {elapsed:.1f}s")
        return results

    async def batch_replies(self, tweets: List[str] = None, count: int = 10) -> list:
        """Batch-Generierung von Replies."""
        if not tweets:
            # Demo tweets based on current trends
            tweets = [
                "Just started my AI automation journey. Any tips?",
                "Looking for someone who can help automate my lead gen process",
                "Is Claude Code worth learning in 2026?",
                "Struggling to find the right AI tool for my business",
                "Anyone using Ollama for production workloads?",
                "How do I start an AI automation agency?",
                "My team spends 20 hours/week on manual data entry",
                "Need help with BMA documentation automation",
                "What's the best way to monetize AI skills?",
                "Building my first AI agent - where to start?",
            ]

        print(f"\n  REPLY ENGINE: Generiere {min(count, len(tweets))} Replies")
        results = []

        for i, tweet in enumerate(tweets[:count]):
            print(f"\r    [{i+1}/{min(count, len(tweets))}] Reply...", end="", flush=True)
            try:
                reply = await self.generate_reply(tweet)
                results.append(reply)
            except Exception as e:
                results.append({"error": str(e)})

        ok = len([r for r in results if "error" not in r])
        print(f"\n    Fertig! {ok}/{min(count, len(tweets))} Replies")
        return results

    # ── Weekly Plan ──────────────────────────────────────────

    async def create_weekly_plan(self) -> dict:
        """Erstellt kompletten Wochen-Content-Plan."""
        print("\n  WEEKLY CONTENT PLAN")
        print("  " + "=" * 40)

        plan = {
            "week_of": datetime.now().strftime("%Y-%m-%d"),
            "days": {},
        }

        for day, config in WEEKLY_SCHEDULE.items():
            trend = CURRENT_TRENDS[config["trend_idx"] % len(CURRENT_TRENDS)]
            print(f"    {day}: {config['type']} / {trend['topic'][:30]}...")

            if config["type"] == "thread":
                post = await self.generate_thread(topic=trend["topic"])
            else:
                post = await self.generate_post(
                    topic=trend["topic"],
                    style=config["type"],
                    trend=trend,
                )

            plan["days"][day] = {
                "post": post,
                "time": config["time"],
                "type": config["type"],
                "trend": trend["topic"],
            }

        # Save as Markdown
        md = self._plan_to_markdown(plan)
        week_str = datetime.now().strftime("%Y%m%d")
        md_file = X_DIR / f"weekly_plan_{week_str}.md"
        md_file.write_text(md, encoding="utf-8")
        print(f"\n    Saved: {md_file}")

        # Also save to schedule
        self.schedule.append(plan)
        self._save_schedule()

        return plan

    def _plan_to_markdown(self, plan: dict) -> str:
        lines = [
            f"# X/TWITTER WEEKLY PLAN - {plan['week_of']}",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "---",
            "",
        ]

        for day, data in plan["days"].items():
            post = data["post"]
            content = post.get("content", post.get("error", "Error"))
            hashtags = " ".join(post.get("hashtags", []))

            lines.extend([
                f"## {day} ({data['time']}) - {data['type'].upper()}",
                f"Trend: {data['trend']}",
                "",
                "```",
                content,
                "```",
                "",
                f"Hashtags: {hashtags}",
                "",
                "---",
                "",
            ])

        lines.extend([
            "## ENGAGEMENT CHECKLIST",
            "",
            "Nach jedem Post:",
            "- [ ] 30 Min aktiv bleiben - Kommentare beantworten",
            "- [ ] 5 Posts in der AI-Nische kommentieren",
            "- [ ] 3 DMs an interessante Kommentatoren",
            "",
            "## TRACKING",
            "",
            "| Tag | Post | Impressions | Likes | Replies | DMs |",
            "|-----|------|-------------|-------|---------|-----|",
        ])
        for day in plan["days"]:
            lines.append(f"| {day} | | | | | |")

        return "\n".join(lines)

    # ── Export ────────────────────────────────────────────────

    def export_ready(self, post_type: str = "", limit: int = 30) -> str:
        """Exportiert ready-to-post Content."""
        posts = [p for p in self.posts if p.get("status") == "ready"]
        if post_type:
            posts = [p for p in posts if p.get("type") == post_type]
        posts = posts[-limit:]

        if not posts:
            return "Keine fertigen Posts in der Queue."

        lines = [
            f"# READY TO POST - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Posts: {len(posts)}",
            "",
        ]

        for p in posts:
            tp = p.get("type", "?").upper()
            style = p.get("style", "")
            hashtags = " ".join(p.get("hashtags", []))
            lines.extend([
                f"## [{tp}] #{p.get('id', '?')} {f'- {style}' if style else ''}",
                f"Topic: {p.get('topic', p.get('original_tweet', '?')[:50])}",
                "",
                "```",
                p.get("content", ""),
                "```",
                "",
            ])
            if hashtags:
                lines.append(f"Hashtags: {hashtags}")
            lines.extend(["", "---", ""])

        return "\n".join(lines)

    # ── Status ───────────────────────────────────────────────

    def show_status(self):
        """Zeigt Engine Status."""
        by_type = {}
        by_status = {"ready": 0, "posted": 0, "draft": 0}
        for p in self.posts:
            t = p.get("type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1
            s = p.get("status", "draft")
            by_status[s] = by_status.get(s, 0) + 1

        print(f"""
{'='*60}
  X POSTING ENGINE - Status
{'='*60}

  CONTENT LIBRARY:
    Total Posts:      {len(self.posts)}
    Ready to Post:    {by_status['ready']}
    Already Posted:   {by_status['posted']}

  BY TYPE:""")
        for t, c in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            print(f"    {t:<15s}: {c}")

        print(f"""
  WEEKLY SCHEDULES: {len(self.schedule)}

  CURRENT TRENDS:""")
        for t in CURRENT_TRENDS[:5]:
            buzz = "X" * t["buzz"]
            print(f"    [{buzz:<5s}] {t['topic']}")

        print(f"""
  COMMANDS:
    python x_posting_engine.py --generate 30
    python x_posting_engine.py --replies 10
    python x_posting_engine.py --weekly
    python x_posting_engine.py --export
    python x_posting_engine.py --dm "lead info"
{'='*60}""")


async def main():
    parser = argparse.ArgumentParser(description="X Posting Engine")
    parser.add_argument("--generate", type=int, metavar="N", help="N Posts generieren")
    parser.add_argument("--replies", type=int, metavar="N", help="N Replies generieren")
    parser.add_argument("--weekly", action="store_true", help="Wochenplan erstellen")
    parser.add_argument("--export", action="store_true", help="Ready Content exportieren")
    parser.add_argument("--dm", type=str, metavar="INFO", help="DM-Sequence generieren")
    parser.add_argument("--type", type=str, default="", help="Filter: single/thread/reply")
    args = parser.parse_args()

    engine = XPostingEngine()

    if args.generate:
        await engine.batch_generate(count=args.generate)
    elif args.replies:
        await engine.batch_replies(count=args.replies)
    elif args.weekly:
        await engine.create_weekly_plan()
    elif args.export:
        md = engine.export_ready(post_type=args.type)
        print(md)
    elif args.dm:
        result = await engine.generate_dm_sequence(
            lead_name="Lead",
            lead_interest=args.dm,
        )
        if "error" not in result:
            print(json.dumps(result["sequence"], indent=2, ensure_ascii=False))
        else:
            print(f"Error: {result['error']}")
    else:
        engine.show_status()


if __name__ == "__main__":
    asyncio.run(main())
