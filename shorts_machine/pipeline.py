#!/usr/bin/env python3
"""
SHORTS MACHINE PIPELINE - End-to-End YouTube Shorts Automation.

Pipeline: Mine → Rank → Script → Assets → Voice → Compose → Publish → Metrics → Optimize

Alles kostenlos mit Ollama + Free Cloud APIs.
Kein manueller Eingriff noetig.

Usage:
  python pipeline.py --mine 100         # 100 Ideen generieren
  python pipeline.py --scripts 30       # 30 Scripts schreiben
  python pipeline.py --produce 10       # 10 Videos bauen
  python pipeline.py --publish          # Upload Queue
  python pipeline.py --metrics          # Metrics pullen
  python pipeline.py --optimize         # Winner-Analyse
  python pipeline.py --pipeline 10      # Full Pipeline
  python pipeline.py --status           # Status
  python pipeline.py --daemon           # Autonomer Modus
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

# Imports
sys.path.insert(0, str(Path(__file__).parent.parent / "workflow-system"))
sys.path.insert(0, str(Path(__file__).parent))

try:
    from ollama_engine import OllamaEngine
except ImportError:
    OllamaEngine = None

try:
    from hook_generator import HookGenerator, HOOK_TEMPLATES
except ImportError:
    HookGenerator = None
    HOOK_TEMPLATES = {}

# ── Verzeichnisse ────────────────────────────────────────

BASE_DIR = Path(__file__).parent.parent
SHORTS_DIR = BASE_DIR / "shorts_machine"
CHANNELS_DIR = BASE_DIR / "channels"
STATE_DIR = SHORTS_DIR / "state"
IDEAS_DIR = STATE_DIR / "ideas"
SCRIPTS_DIR = STATE_DIR / "scripts"
VIDEOS_DIR = STATE_DIR / "videos"
UPLOAD_QUEUE_DIR = STATE_DIR / "upload_queue"
METRICS_DIR = STATE_DIR / "metrics"

for d in [STATE_DIR, IDEAS_DIR, SCRIPTS_DIR, VIDEOS_DIR,
          UPLOAD_QUEUE_DIR, METRICS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ── Nischen-Konfiguration ───────────────────────────────

NISCHEN = {
    "ai_automation": {
        "name": "AI Automation & Agent OS",
        "keywords": ["AI", "automation", "agent", "chatgpt", "workflow", "no-code"],
        "affiliate_products": [
            {"name": "AI Tool Stack", "url": "link-in-bio", "commission": "30%"},
            {"name": "Prompt Pack", "url": "gumroad", "price": "27 EUR"},
        ],
        "target_audience": "Unternehmer, Freelancer, Tech-Interessierte",
        "cta_keywords": ["AUTOMATION", "AI-TOOL", "GRATIS-GUIDE"],
    },
    "money_business": {
        "name": "Geld verdienen / Business (DACH)",
        "keywords": ["Geld verdienen", "Business", "Einkommen", "passiv", "online"],
        "affiliate_products": [
            {"name": "Business Blueprint", "url": "gumroad", "price": "49 EUR"},
            {"name": "Freelancer Guide", "url": "gumroad", "price": "27 EUR"},
        ],
        "target_audience": "DACH, 20-45, Nebeneinkommen suchend",
        "cta_keywords": ["BLUEPRINT", "GRATIS", "ANLEITUNG"],
    },
    "brandschutz_fails": {
        "name": "Sicherheitstechnik / Brandschutz Fails",
        "keywords": ["Brandschutz", "BMA", "Sicherheit", "Feueralarm", "DIN 14675"],
        "affiliate_products": [
            {"name": "BMA Checkliste DIN 14675", "url": "gumroad", "price": "49 EUR"},
            {"name": "Brandschutz SOP Pack", "url": "gumroad", "price": "99 EUR"},
        ],
        "target_audience": "Handwerker, Facility Manager, Sicherheitsbeauftragte",
        "cta_keywords": ["CHECKLISTE", "BMA-GUIDE", "SICHERHEIT"],
    },
}


# ══════════════════════════════════════════════════════════
#  TREND MINER - Ideen generieren und scoren
# ══════════════════════════════════════════════════════════

class TrendMiner:
    """Generiert Short-Ideen, scored und dedupliziert."""

    def __init__(self, nische: str = "ai_automation"):
        self.nische = nische
        self.nische_config = NISCHEN.get(nische, NISCHEN["ai_automation"])
        self.engine = OllamaEngine() if OllamaEngine else None
        self.hook_gen = HookGenerator() if HookGenerator else None

    async def mine_ideas(self, count: int = 100) -> List[Dict]:
        """Generiert Short-Ideen mit LLM + Hook-Templates."""
        ideas = []

        # Phase 1: LLM-basierte Ideengenerierung
        if self.engine:
            llm_ideas = await self._mine_with_llm(count // 2)
            ideas.extend(llm_ideas)

        # Phase 2: Template-basierte Generierung (immer, auch offline)
        template_ideas = self._mine_from_templates(count - len(ideas))
        ideas.extend(template_ideas)

        # Deduplizieren
        seen = set()
        unique = []
        for idea in ideas:
            key = idea.get("topic", "")[:50].lower()
            if key not in seen:
                seen.add(key)
                unique.append(idea)

        # Scoren
        for idea in unique:
            idea["score"] = self._score_idea(idea)

        # Sortieren nach Score
        unique.sort(key=lambda x: x["score"], reverse=True)

        # Speichern
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ideas_file = IDEAS_DIR / f"ideas_{timestamp}.json"
        with open(ideas_file, "w") as f:
            json.dump(unique, f, indent=2, ensure_ascii=False)

        return unique

    async def _mine_with_llm(self, count: int) -> List[Dict]:
        """LLM-basierte Ideengenerierung."""
        ideas = []
        batch_size = 5  # 5 Ideen pro LLM-Call

        for batch in range(0, count, batch_size):
            prompt = f"""Generiere {batch_size} virale YouTube Shorts Ideen.

Nische: {self.nische_config['name']}
Keywords: {', '.join(self.nische_config['keywords'])}
Zielgruppe: {self.nische_config['target_audience']}
Format: 15-30 Sekunden, Faceless, Hook-first

Antworte NUR mit JSON Array:
[
  {{
    "topic": "Konkretes Thema",
    "angle": "Besonderer Blickwinkel/Twist",
    "hook_template": "CONFLICT_REVEAL/SECRET/MISTAKE/STEPS",
    "keywords": ["keyword1", "keyword2"],
    "format": "kinetic_text/slideshow/screen_mockup/narrated_steps",
    "trend_score": 7,
    "novelty_score": 8
  }}
]"""

            try:
                resp = await self.engine.chat(
                    messages=[
                        {"role": "system", "content": "Du bist ein YouTube Shorts Trend-Analyst. Nur JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=800,
                    temperature=0.9,
                )
                if resp.success and resp.content:
                    content = resp.content.strip()
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]
                    try:
                        batch_ideas = json.loads(content.strip())
                        if isinstance(batch_ideas, list):
                            for idea in batch_ideas:
                                idea["source"] = "llm"
                                idea["nische"] = self.nische
                                ideas.append(idea)
                    except json.JSONDecodeError:
                        pass
            except Exception:
                pass

        return ideas

    def _mine_from_templates(self, count: int) -> List[Dict]:
        """Template-basierte Ideengenerierung (offline-faehig)."""
        ideas = []
        topics = self._get_topic_pool()

        for i in range(count):
            topic = random.choice(topics)
            hook = None
            if self.hook_gen:
                hooks = self.hook_gen.generate(count=1)
                hook = hooks[0] if hooks else None

            formats = ["kinetic_text", "slideshow", "screen_mockup", "narrated_steps"]

            idea = {
                "topic": topic["topic"],
                "angle": topic.get("angle", "Standard"),
                "hook_template": hook["hook_template"] if hook else "STEP_BY_STEP",
                "hook_text": hook["hook_text"] if hook else "",
                "keywords": self.nische_config["keywords"][:3],
                "format": random.choice(formats),
                "trend_score": random.randint(5, 9),
                "novelty_score": random.randint(4, 9),
                "source": "template",
                "nische": self.nische,
            }
            ideas.append(idea)

        return ideas

    def _get_topic_pool(self) -> List[Dict]:
        """Vordefinierte Topics pro Nische."""
        pools = {
            "ai_automation": [
                {"topic": "3 AI Tools die 90% der Arbeit erledigen", "angle": "Tool-Stack"},
                {"topic": "Wie ich mein Business mit AI automatisiert habe", "angle": "Story"},
                {"topic": "ChatGPT Fehler die dich Geld kosten", "angle": "Warnung"},
                {"topic": "AI Agent der fuer dich arbeitet", "angle": "Demo"},
                {"topic": "Von 0 auf automatisiert in 7 Tagen", "angle": "Timeline"},
                {"topic": "Warum AI-Automation die Zukunft ist", "angle": "Take"},
                {"topic": "Dieses AI Setup spart 20 Stunden/Woche", "angle": "Zeitersparnis"},
                {"topic": "AI vs. manuell: Der echte Vergleich", "angle": "Vergleich"},
                {"topic": "Mein 100 EUR/Tag AI Workflow", "angle": "Revenue"},
                {"topic": "3 Fehler beim AI Business Start", "angle": "Fehler"},
                {"topic": "AI Automation fuer Anfaenger erklaert", "angle": "Einstieg"},
                {"topic": "So findest du AI Kunden auf LinkedIn", "angle": "Akquise"},
                {"topic": "Ollama: Kostenlose AI auf deinem Laptop", "angle": "Tool"},
                {"topic": "Was AI in 2026 wirklich kann", "angle": "Zukunft"},
                {"topic": "Freelancer vs. AI Agent: Wer gewinnt?", "angle": "Battle"},
            ],
            "money_business": [
                {"topic": "3 Wege Online Geld zu verdienen 2026", "angle": "Uebersicht"},
                {"topic": "Von 0 auf 1000 EUR/Monat - Schritt fuer Schritt", "angle": "Tutorial"},
                {"topic": "Nebeneinkommen mit AI aufbauen", "angle": "AI + Geld"},
                {"topic": "Dieser Side Hustle bringt 500 EUR/Monat", "angle": "Konkret"},
                {"topic": "5 passive Einkommensquellen mit AI", "angle": "Liste"},
                {"topic": "Freelancer Fehler die Geld kosten", "angle": "Warnung"},
                {"topic": "Wie ich ohne Startkapital gestartet bin", "angle": "Story"},
                {"topic": "Digital Products die sich verkaufen", "angle": "Produkt"},
                {"topic": "Gumroad Anleitung: Erstes Produkt in 1 Stunde", "angle": "Tutorial"},
                {"topic": "Fiverr Gig der 100 EUR/Tag bringt", "angle": "Plattform"},
            ],
            "brandschutz_fails": [
                {"topic": "Brandschutz-Fehler die Leben kosten", "angle": "Warnung"},
                {"topic": "BMA richtig planen nach DIN 14675", "angle": "Tutorial"},
                {"topic": "Warum 90% der Brandmelder falsch installiert sind", "angle": "Schock"},
                {"topic": "Brandschutz + AI: Die Zukunft", "angle": "Innovation"},
                {"topic": "Die teuersten Brandschutz-Fehler", "angle": "Kosten"},
                {"topic": "Was der Brandschutzbeauftragte nicht weiss", "angle": "Geheimnis"},
                {"topic": "Checkliste fuer Brandschutz-Abnahme", "angle": "Tool"},
                {"topic": "Real Talk: Brandschutz-Fails aus der Praxis", "angle": "Story"},
            ],
        }
        return pools.get(self.nische, pools["ai_automation"])

    def _score_idea(self, idea: Dict) -> float:
        """Berechnet Gesamt-Score einer Idee."""
        trend = idea.get("trend_score", 5)
        novelty = idea.get("novelty_score", 5)
        competition = idea.get("competition_score", 5)  # Niedrig = gut
        return round((trend * novelty) / max(competition, 1), 2)


# ══════════════════════════════════════════════════════════
#  SCRIPT FACTORY - Scripts + Captions generieren
# ══════════════════════════════════════════════════════════

class ScriptFactory:
    """Erstellt Short-Scripts mit Hook-first Struktur."""

    def __init__(self, nische: str = "ai_automation"):
        self.nische = nische
        self.nische_config = NISCHEN.get(nische, NISCHEN["ai_automation"])
        self.engine = OllamaEngine() if OllamaEngine else None
        self.hook_gen = HookGenerator() if HookGenerator else None

    async def create_script(self, idea: Dict) -> Dict:
        """Erstellt ein Short-Script aus einer Idee."""
        # Hook generieren
        hook_text = idea.get("hook_text", "")
        if not hook_text and self.hook_gen:
            hooks = self.hook_gen.generate(
                template_key=idea.get("hook_template"),
                count=1,
            )
            hook_text = hooks[0]["hook_text"] if hooks else ""

        # CTA generieren
        cta_keyword = random.choice(self.nische_config.get("cta_keywords", ["LINK"]))
        affiliate = random.choice(self.nische_config.get("affiliate_products", [{"name": "Guide"}]))

        # Script mit LLM oder Template
        if self.engine:
            script = await self._create_with_llm(idea, hook_text, cta_keyword)
        else:
            script = self._create_from_template(idea, hook_text, cta_keyword)

        # Metadata
        script_data = {
            "id": f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}",
            "topic": idea.get("topic", ""),
            "nische": self.nische,
            "hook": hook_text,
            "hook_template": idea.get("hook_template", ""),
            "script": script,
            "duration_sec": self._estimate_duration(script),
            "format": idea.get("format", "kinetic_text"),
            "cta_keyword": cta_keyword,
            "pinned_comment": f"Kommentiere '{cta_keyword}' und ich schicke dir den Link!",
            "description": f"{idea.get('topic', '')} | Kommentiere {cta_keyword} fuer mehr!",
            "title_variants": self._generate_title_variants(idea),
            "affiliate": affiliate.get("name", ""),
            "timestamp": datetime.now().isoformat(),
        }

        # Speichern
        script_file = SCRIPTS_DIR / f"{script_data['id']}.json"
        with open(script_file, "w") as f:
            json.dump(script_data, f, indent=2, ensure_ascii=False)

        return script_data

    async def _create_with_llm(self, idea: Dict, hook: str, cta: str) -> str:
        """LLM-basiertes Script."""
        prompt = f"""Schreibe ein YouTube Short Script (15-25 Sekunden).

Topic: {idea.get('topic', '')}
Hook (MUSS der erste Satz sein): {hook}
CTA Keyword: {cta}
Format: Faceless, Kinetic Text

Struktur:
1. Hook (0-2s): {hook}
2. Problem/Setup (2-7s): Warum ist das relevant?
3. Loesung/Twist (7-18s): 2-3 konkrete Punkte
4. CTA (18-22s): "Kommentiere {cta} fuer den Link"

Schreibe NUR das Script (keine Anweisungen), jede Zeile = 1 Slide/Scene.
Kurze Saetze. Max 8 Zeilen."""

        try:
            resp = await self.engine.chat(
                messages=[
                    {"role": "system", "content": "Du schreibst virale YouTube Shorts Scripts. Kurz, direkt, hook-first."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=400,
                temperature=0.8,
            )
            if resp.success and resp.content:
                return resp.content.strip()
        except Exception:
            pass

        return self._create_from_template(idea, hook, cta)

    def _create_from_template(self, idea: Dict, hook: str, cta: str) -> str:
        """Template-basiertes Script (Offline-Fallback)."""
        topic = idea.get("topic", "AI Automation")
        lines = [
            hook or f"Das aendert alles bei {topic}.",
            f"Die meisten machen es falsch.",
            f"Hier sind die 3 Schritte:",
            f"Erstens: Das richtige System waehlen.",
            f"Zweitens: Automatisieren statt manuell.",
            f"Drittens: Messen und optimieren.",
            f"Kommentiere '{cta}' und ich schicke dir die komplette Anleitung!",
        ]
        return "\n".join(lines)

    def _estimate_duration(self, script: str) -> int:
        """Schaetzt Script-Dauer in Sekunden."""
        words = len(script.split())
        # ~2.5 Woerter/Sekunde (Sprechgeschwindigkeit)
        return max(12, min(60, int(words / 2.5)))

    def _generate_title_variants(self, idea: Dict) -> List[str]:
        """Generiert 3 Title-Varianten fuer A/B Testing."""
        topic = idea.get("topic", "")
        return [
            topic,
            f"{topic} (das wusste ich nicht!)",
            f"{topic} #shorts",
        ]

    async def batch_create(self, ideas: List[Dict], count: int = 10) -> List[Dict]:
        """Erstellt mehrere Scripts aus Ideen."""
        scripts = []
        for idea in ideas[:count]:
            script = await self.create_script(idea)
            scripts.append(script)
        return scripts


# ══════════════════════════════════════════════════════════
#  VIDEO COMPOSER - ffmpeg-basierte Video-Produktion
# ══════════════════════════════════════════════════════════

class VideoComposer:
    """Erstellt Faceless Videos aus Scripts.

    Formate:
    - kinetic_text: Text bewegt sich + Sound
    - slideshow: 6-8 Slides mit Text
    - narrated_steps: Bullet Points nacheinander
    """

    def __init__(self):
        self.output_dir = VIDEOS_DIR
        self.ffmpeg_available = self._check_ffmpeg()

    def _check_ffmpeg(self) -> bool:
        """Prueft ob ffmpeg installiert ist."""
        import shutil
        return shutil.which("ffmpeg") is not None

    def compose_video_spec(self, script_data: Dict) -> Dict:
        """Erstellt Video-Spezifikation (ffmpeg Commands vorbereiten)."""
        script_id = script_data["id"]
        script_text = script_data.get("script", "")
        duration = script_data.get("duration_sec", 20)
        video_format = script_data.get("format", "kinetic_text")

        # Scenes aus Script-Zeilen
        lines = [l.strip() for l in script_text.split("\n") if l.strip()]
        scene_duration = max(2, duration // max(len(lines), 1))

        scenes = []
        for i, line in enumerate(lines):
            scenes.append({
                "scene_id": i,
                "text": line,
                "duration_sec": scene_duration,
                "start_sec": i * scene_duration,
                "style": "bold_center" if i == 0 else "standard",
            })

        # Video-Spec
        spec = {
            "id": script_id,
            "format": video_format,
            "resolution": "1080x1920",  # Vertical (9:16)
            "fps": 30,
            "total_duration_sec": duration,
            "scenes": scenes,
            "background": "solid_dark",  # solid_dark, gradient, blur_stock
            "font": "Arial-Bold",
            "font_size": 72,
            "text_color": "#FFFFFF",
            "accent_color": "#FFD700",
            "safe_zone": {"top": 200, "bottom": 300},  # YouTube UI overlay
            "output_file": str(self.output_dir / f"{script_id}.mp4"),
            "thumbnail_file": str(self.output_dir / f"{script_id}_thumb.png"),
            "ffmpeg_available": self.ffmpeg_available,
            "timestamp": datetime.now().isoformat(),
        }

        # Spec speichern
        spec_file = self.output_dir / f"{script_id}_spec.json"
        with open(spec_file, "w") as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)

        return spec

    def generate_ffmpeg_command(self, spec: Dict) -> str:
        """Generiert ffmpeg Command fuer Video-Produktion."""
        scenes = spec.get("scenes", [])
        duration = spec.get("total_duration_sec", 20)
        output = spec.get("output_file", "output.mp4")

        # Drawtext filter fuer jede Scene
        drawtext_filters = []
        for scene in scenes:
            text = scene["text"].replace("'", "\\'").replace(":", "\\:")
            start = scene["start_sec"]
            end = start + scene["duration_sec"]
            style = scene.get("style", "standard")

            fontsize = 72 if style == "bold_center" else 56
            y_pos = "(h-text_h)/2" if style == "bold_center" else "(h-text_h)/2+50"

            drawtext_filters.append(
                f"drawtext=text='{text}'"
                f":fontsize={fontsize}"
                f":fontcolor=white"
                f":x=(w-text_w)/2"
                f":y={y_pos}"
                f":enable='between(t,{start},{end})'"
                f":borderw=3:bordercolor=black"
            )

        filter_chain = ",".join(drawtext_filters)

        cmd = (
            f"ffmpeg -y "
            f"-f lavfi -i color=c=black:s=1080x1920:d={duration}:r=30 "
            f"-vf \"{filter_chain}\" "
            f"-c:v libx264 -preset fast -crf 23 "
            f"-pix_fmt yuv420p "
            f"\"{output}\""
        )

        return cmd


# ══════════════════════════════════════════════════════════
#  YOUTUBE PUBLISHER - Upload + Scheduling
# ══════════════════════════════════════════════════════════

class YouTubePublisher:
    """Managed YouTube Upload Queue + Scheduling."""

    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY", "")
        self.queue_dir = UPLOAD_QUEUE_DIR

    def queue_for_upload(self, script_data: Dict, video_spec: Dict) -> Dict:
        """Fuegt Video zur Upload-Queue hinzu."""
        upload_item = {
            "id": script_data["id"],
            "status": "queued",
            "title": script_data.get("title_variants", ["Untitled"])[0],
            "description": script_data.get("description", ""),
            "pinned_comment": script_data.get("pinned_comment", ""),
            "cta_keyword": script_data.get("cta_keyword", ""),
            "tags": script_data.get("keywords", []) + ["shorts", "viral"],
            "video_file": video_spec.get("output_file", ""),
            "thumbnail_file": video_spec.get("thumbnail_file", ""),
            "scheduled_time": None,  # Optional: Scheduling
            "nische": script_data.get("nische", ""),
            "hook_template": script_data.get("hook_template", ""),
            "queued_at": datetime.now().isoformat(),
        }

        queue_file = self.queue_dir / f"{script_data['id']}_upload.json"
        with open(queue_file, "w") as f:
            json.dump(upload_item, f, indent=2, ensure_ascii=False)

        return upload_item

    def get_queue(self) -> List[Dict]:
        """Gibt aktuelle Upload-Queue zurueck."""
        items = []
        for f in sorted(self.queue_dir.glob("*_upload.json")):
            try:
                items.append(json.loads(f.read_text()))
            except (json.JSONDecodeError, OSError):
                pass
        return items

    def get_queue_stats(self) -> Dict:
        """Queue-Statistiken."""
        queue = self.get_queue()
        return {
            "total": len(queue),
            "queued": sum(1 for q in queue if q.get("status") == "queued"),
            "uploaded": sum(1 for q in queue if q.get("status") == "uploaded"),
            "failed": sum(1 for q in queue if q.get("status") == "failed"),
        }


# ══════════════════════════════════════════════════════════
#  METRICS COLLECTOR - YouTube Analytics
# ══════════════════════════════════════════════════════════

class MetricsCollector:
    """Sammelt YouTube Metrics fuer Optimization."""

    def __init__(self, channel_dir: Optional[Path] = None):
        self.channel_dir = channel_dir
        self.perf_file = None
        if channel_dir:
            self.perf_file = channel_dir / "memory" / "performance.jsonl"

    def log_performance(self, video_id: str, metrics: Dict):
        """Loggt Performance-Daten (append-only)."""
        if not self.perf_file:
            self.perf_file = METRICS_DIR / "performance.jsonl"

        entry = {
            "video_id": video_id,
            "timestamp": datetime.now().isoformat(),
            **metrics,
        }

        with open(self.perf_file, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def get_winners(self, min_views: int = 1000) -> List[Dict]:
        """Findet Top-performing Shorts."""
        if not self.perf_file or not self.perf_file.exists():
            return []

        winners = []
        try:
            with open(self.perf_file, "r") as f:
                for line in f:
                    entry = json.loads(line.strip())
                    if entry.get("views", 0) >= min_views:
                        winners.append(entry)
        except (json.JSONDecodeError, OSError):
            pass

        winners.sort(key=lambda x: x.get("views", 0), reverse=True)
        return winners

    def get_hook_performance(self) -> Dict[str, Dict]:
        """Analysiert welche Hook-Templates am besten performen."""
        if not self.perf_file or not self.perf_file.exists():
            return {}

        hook_stats = {}
        try:
            with open(self.perf_file, "r") as f:
                for line in f:
                    entry = json.loads(line.strip())
                    hook = entry.get("hook_template", "unknown")
                    if hook not in hook_stats:
                        hook_stats[hook] = {"count": 0, "total_views": 0, "total_likes": 0}
                    hook_stats[hook]["count"] += 1
                    hook_stats[hook]["total_views"] += entry.get("views", 0)
                    hook_stats[hook]["total_likes"] += entry.get("likes", 0)
        except (json.JSONDecodeError, OSError):
            pass

        # Durchschnitte berechnen
        for hook, stats in hook_stats.items():
            if stats["count"] > 0:
                stats["avg_views"] = stats["total_views"] / stats["count"]
                stats["avg_likes"] = stats["total_likes"] / stats["count"]

        return hook_stats


# ══════════════════════════════════════════════════════════
#  OPTIMIZER - Self-Learning Feedback Loop
# ══════════════════════════════════════════════════════════

class Optimizer:
    """Analysiert Performance und optimiert die Pipeline."""

    def __init__(self, channel_dir: Optional[Path] = None):
        self.metrics = MetricsCollector(channel_dir)
        self.channel_dir = channel_dir

    def analyze(self) -> Dict:
        """Analysiert Performance und gibt Empfehlungen."""
        hook_perf = self.metrics.get_hook_performance()
        winners = self.metrics.get_winners()

        recommendations = []

        # Hook-Analyse
        if hook_perf:
            best_hook = max(hook_perf.items(),
                           key=lambda x: x[1].get("avg_views", 0))
            worst_hook = min(hook_perf.items(),
                            key=lambda x: x[1].get("avg_views", 0))
            recommendations.append(
                f"Bester Hook: {best_hook[0]} ({best_hook[1].get('avg_views', 0):.0f} avg views)")
            recommendations.append(
                f"Schlechtester Hook: {worst_hook[0]} - weniger nutzen")
        else:
            recommendations.append("Noch keine Performance-Daten - mehr Shorts uploaden!")

        # Winners-Analyse
        if winners:
            recommendations.append(f"{len(winners)} Shorts mit 1000+ Views")
        else:
            recommendations.append("Noch keine Winners - weiter produzieren")

        return {
            "hook_performance": hook_perf,
            "winners_count": len(winners),
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat(),
        }

    def update_channel_skills(self):
        """Aktualisiert Channel Skills basierend auf Performance."""
        if not self.channel_dir:
            return

        analysis = self.analyze()
        winners_file = self.channel_dir / "memory" / "winners.md"

        lines = [
            f"# Winners & Learnings",
            f"Updated: {datetime.now().isoformat()}\n",
            f"## Empfehlungen",
        ]
        for rec in analysis.get("recommendations", []):
            lines.append(f"- {rec}")

        lines.append(f"\n## Hook Performance")
        for hook, stats in analysis.get("hook_performance", {}).items():
            lines.append(f"- **{hook}**: {stats.get('avg_views', 0):.0f} avg views, "
                         f"{stats.get('count', 0)} Shorts")

        winners_file.write_text("\n".join(lines))


# ══════════════════════════════════════════════════════════
#  PIPELINE ORCHESTRATOR - Alles zusammen
# ══════════════════════════════════════════════════════════

class ShortsPipeline:
    """Orchestriert die gesamte Shorts Machine Pipeline."""

    def __init__(self, nische: str = "ai_automation",
                 channel_id: str = "ai_automation"):
        self.nische = nische
        self.channel_id = channel_id
        self.channel_dir = CHANNELS_DIR / channel_id
        self.channel_dir.mkdir(parents=True, exist_ok=True)

        self.miner = TrendMiner(nische)
        self.scripts = ScriptFactory(nische)
        self.composer = VideoComposer()
        self.publisher = YouTubePublisher()
        self.metrics = MetricsCollector(self.channel_dir)
        self.optimizer = Optimizer(self.channel_dir)

    async def run_pipeline(self, count: int = 10):
        """Full Pipeline: Mine → Script → Compose → Queue."""
        print(f"""
{'='*60}
   SHORTS MACHINE - FULL PIPELINE
   {count} Shorts produzieren
{'='*60}
   Nische:     {NISCHEN.get(self.nische, {}).get('name', self.nische)}
   Channel:    {self.channel_id}
   Kosten:     $0.00 (Ollama + Templates)
{'='*60}
""")

        # 1. Mine Ideas
        print(f"  [1/4] Mining {count * 3} Ideen...")
        ideas = await self.miner.mine_ideas(count * 3)
        print(f"        {len(ideas)} Ideen generiert, Top Score: {ideas[0]['score'] if ideas else 0}")

        # 2. Create Scripts
        print(f"  [2/4] Schreibe {count} Scripts...")
        scripts = await self.scripts.batch_create(ideas[:count], count)
        print(f"        {len(scripts)} Scripts erstellt")

        # 3. Compose Videos (Specs)
        print(f"  [3/4] Video-Specs erstellen...")
        video_specs = []
        for script in scripts:
            spec = self.composer.compose_video_spec(script)
            video_specs.append(spec)
        print(f"        {len(video_specs)} Video-Specs erstellt")
        if self.composer.ffmpeg_available:
            print(f"        ffmpeg verfuegbar - Videos koennen gerendert werden")
        else:
            print(f"        ffmpeg NICHT installiert - nur Specs erstellt")

        # 4. Queue for Upload
        print(f"  [4/4] Upload Queue befuellen...")
        for script, spec in zip(scripts, video_specs):
            self.publisher.queue_for_upload(script, spec)
        queue_stats = self.publisher.get_queue_stats()
        print(f"        Queue: {queue_stats['queued']} bereit")

        # Summary
        print(f"""
{'='*60}
   PIPELINE ABGESCHLOSSEN
{'='*60}
   Ideen:      {len(ideas)} generiert
   Scripts:    {len(scripts)} geschrieben
   Videos:     {len(video_specs)} Specs erstellt
   Queue:      {queue_stats['queued']} bereit zum Upload
   Output:     {STATE_DIR}
{'='*60}
""")

        return {
            "ideas": len(ideas),
            "scripts": len(scripts),
            "video_specs": len(video_specs),
            "queued": queue_stats["queued"],
        }

    def show_status(self):
        """Zeigt Pipeline-Status."""
        ideas_count = len(list(IDEAS_DIR.glob("*.json")))
        scripts_count = len(list(SCRIPTS_DIR.glob("*.json")))
        specs_count = len(list(VIDEOS_DIR.glob("*_spec.json")))
        queue_stats = self.publisher.get_queue_stats()

        print(f"""
{'='*60}
   SHORTS MACHINE - STATUS
{'='*60}
   Nische:         {NISCHEN.get(self.nische, {}).get('name', self.nische)}
   Channel:        {self.channel_id}

   Pipeline:
     Ideen-Files:  {ideas_count}
     Scripts:      {scripts_count}
     Video-Specs:  {specs_count}
     Upload Queue: {queue_stats['total']} ({queue_stats['queued']} bereit)

   Hook Templates: {len(HOOK_TEMPLATES)}
   ffmpeg:         {'OK' if self.composer.ffmpeg_available else 'NICHT INSTALLIERT'}

   Nischen verfuegbar:""")
        for key, nische in NISCHEN.items():
            print(f"     {key:<20s}: {nische['name']}")
        print(f"""
   Befehle:
     python pipeline.py --mine 100       # Ideen minen
     python pipeline.py --scripts 30     # Scripts schreiben
     python pipeline.py --produce 10     # Videos bauen
     python pipeline.py --pipeline 10    # Full Pipeline
     python pipeline.py --optimize       # Winner-Analyse
{'='*60}
""")


# ══════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════

async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Shorts Machine - YouTube Shorts Automation")
    parser.add_argument("--nische", type=str, default="ai_automation",
                        choices=list(NISCHEN.keys()),
                        help="Nische (default: ai_automation)")
    parser.add_argument("--channel", type=str, default="ai_automation",
                        help="Channel ID")
    parser.add_argument("--mine", type=int, default=0,
                        help="X Ideen minen")
    parser.add_argument("--scripts", type=int, default=0,
                        help="X Scripts schreiben")
    parser.add_argument("--produce", type=int, default=0,
                        help="X Videos produzieren (Specs)")
    parser.add_argument("--pipeline", type=int, default=0,
                        help="Full Pipeline (X Shorts)")
    parser.add_argument("--optimize", action="store_true",
                        help="Optimizer laufen lassen")
    parser.add_argument("--status", action="store_true",
                        help="Status anzeigen")
    args = parser.parse_args()

    pipeline = ShortsPipeline(nische=args.nische, channel_id=args.channel)

    if args.status:
        pipeline.show_status()
    elif args.pipeline > 0:
        await pipeline.run_pipeline(args.pipeline)
    elif args.mine > 0:
        ideas = await pipeline.miner.mine_ideas(args.mine)
        print(f"  {len(ideas)} Ideen generiert. Top 5:")
        for idea in ideas[:5]:
            print(f"    [{idea['score']:.1f}] {idea['topic']}")
    elif args.scripts > 0:
        ideas = await pipeline.miner.mine_ideas(args.scripts * 2)
        scripts = await pipeline.scripts.batch_create(ideas, args.scripts)
        print(f"  {len(scripts)} Scripts erstellt.")
    elif args.produce > 0:
        # Ideen → Scripts → Specs
        await pipeline.run_pipeline(args.produce)
    elif args.optimize:
        analysis = pipeline.optimizer.analyze()
        print(f"\n  OPTIMIZER ANALYSE:")
        for rec in analysis.get("recommendations", []):
            print(f"    > {rec}")
        print()
    else:
        pipeline.show_status()


if __name__ == "__main__":
    asyncio.run(main())
