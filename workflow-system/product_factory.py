#!/usr/bin/env python3
"""
PRODUCT FACTORY - Automatisierte Signature-Produkt-Engine.
Verwandelt Ideen in verkaufbare Produkte mit Marketing + Vertrieb.

Pipeline:
    1. Idea Inbox     → Ideen sammeln (data/ideas/inbox.jsonl)
    2. Idea Scoring   → Bewertung nach Revenue-Potenzial
    3. Offer Design   → Zielgruppe, Versprechen, Preisstruktur
    4. Asset Builder   → PDFs, Templates, Checklisten generieren
    5. Marketing Gen  → 30 Posts + 5 Threads + Email Sequence
    6. Sales Ready    → Gumroad/Fiverr Listing vorbereiten
    7. Feedback Loop  → Metriken tracken, Produkt verbessern

Produktlinien:
    A) Blueprint Packs (PDF + Templates) - 27-49 EUR
    B) SOP Packs (Ablauf + Checkliste) - 49-99 EUR
    C) Prompt Packs (Agent Workflows) - 27-79 EUR
    D) Automation Packs (n8n + Setup Guide) - 99-149 EUR
    E) Signature Products (Premium Kurse) - 199-999 EUR

Usage:
    python product_factory.py                        # Status
    python product_factory.py --idea "BMA Checkliste" # Neue Idee
    python product_factory.py --score                 # Ideen bewerten
    python product_factory.py --design <id>           # Offer designen
    python product_factory.py --build <id>            # Assets bauen
    python product_factory.py --market <id>           # Marketing generieren
    python product_factory.py --pipeline              # Volle Pipeline
"""

import asyncio
import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

import logging

log = logging.getLogger(__name__)

try:
    from ollama_engine import OllamaEngine
except Exception as e:
    OllamaEngine = None
    log.exception("ollama_engine import failed: %s", e)

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = Path(__file__).parent / "state"
PRODUCTS_DIR = STATE_DIR / "products"
IDEAS_FILE = PRODUCTS_DIR / "ideas.json"
CATALOG_FILE = PRODUCTS_DIR / "catalog.json"

# ── Produkt-Typen ────────────────────────────────────────────

PRODUCT_TYPES = {
    "blueprint": {
        "name": "Blueprint Pack",
        "description": "PDF + Templates + Beispiel-Dateien",
        "price_range": (27, 49),
        "delivery": "Sofort-Download (PDF + ZIP)",
        "effort_hours": 2,
        "contents": ["Haupt-PDF (15-30 Seiten)", "3-5 Templates", "Checkliste", "Quickstart Guide"],
    },
    "sop": {
        "name": "SOP Pack",
        "description": "Standard Operating Procedures + Checklisten",
        "price_range": (49, 99),
        "delivery": "Sofort-Download (PDF + Notion/Excel)",
        "effort_hours": 4,
        "contents": ["SOP Dokument", "Schritt-fuer-Schritt Checkliste", "Fehlerliste + Loesungen", "Video-Walkthrough (optional)"],
    },
    "prompts": {
        "name": "Prompt Pack",
        "description": "Agent-Workflows + Prompt Library",
        "price_range": (27, 79),
        "delivery": "Sofort-Download (PDF + TXT)",
        "effort_hours": 3,
        "contents": ["50+ Prompts kategorisiert", "Agent-Workflow Configs", "Anwendungsbeispiele", "Updates inklusive"],
    },
    "automation": {
        "name": "Automation Pack",
        "description": "n8n/Make Workflows + Setup Guide",
        "price_range": (99, 149),
        "delivery": "Sofort-Download (JSON + PDF)",
        "effort_hours": 6,
        "contents": ["n8n/Make Workflow-Dateien", "Einrichtungs-Guide", "API Key Setup", "Troubleshooting FAQ"],
    },
    "signature": {
        "name": "Signature Product",
        "description": "Premium Kurs / Masterclass",
        "price_range": (199, 999),
        "delivery": "Online-Zugang + Community",
        "effort_hours": 20,
        "contents": ["Video-Kurs (5-10 Module)", "Workbook", "Templates + Tools", "Community-Zugang", "1x Live Q&A"],
    },
}

# ── Scoring Kriterien ────────────────────────────────────────

SCORING_CRITERIA = {
    "zahlungsbereitschaft": {
        "weight": 3.0,
        "description": "Wie viel wuerde jemand dafuer zahlen? (1-10)",
    },
    "umsetzungsgeschwindigkeit": {
        "weight": 2.5,
        "description": "Wie schnell kann das Produkt fertig sein? (1-10, 10=sofort)",
    },
    "wiederverwendbarkeit": {
        "weight": 2.0,
        "description": "Kann man es mehrfach verkaufen ohne Anpassung? (1-10)",
    },
    "differenzierung": {
        "weight": 2.0,
        "description": "Wie einzigartig ist es? (1-10, 10=nur du kannst das)",
    },
    "marktgroesse": {
        "weight": 1.5,
        "description": "Wie viele potenzielle Kaeufer gibt es? (1-10)",
    },
}

# ── Maurices Signature-Linien ────────────────────────────────

SIGNATURE_LINES = {
    "ai_ops_handwerk": {
        "name": "AI Ops fuer Handwerk & Technik",
        "tagline": "Vom Chaos zur Maschine",
        "audience": "Kleine/mittlere Betriebe, Projektleiter, technische Dienstleister",
        "usp": "16 Jahre Praxis + AI = glaubwuerdig + Praxisfaelle",
    },
    "bma_automation": {
        "name": "BMA + AI Automation",
        "tagline": "Brandmeldeanlagen intelligent automatisieren",
        "audience": "Errichter, Planer, Facility Manager, Brandschutzbeauftragte",
        "usp": "Einzige AI-Loesung fuer BMA - unbesetzter Markt",
    },
    "content_factory": {
        "name": "Agentic Content Factory",
        "tagline": "30 Tage Content in 60 Minuten pro Woche",
        "audience": "Solopreneure, B2B-Berater, Tech-Sales",
        "usp": "Skalierbar, viele Kaeufer, einfacher Einstieg",
    },
}

# ── Starter Produkt-Ideen ────────────────────────────────────

STARTER_IDEAS = [
    {
        "title": "BMA Wartungsprotokoll Generator",
        "description": "AI-gestuetzter Generator fuer normkonforme BMA-Wartungsprotokolle",
        "type": "automation",
        "line": "bma_automation",
        "tags": ["bma", "din14675", "wartung", "nische"],
    },
    {
        "title": "50 AI Business Prompts",
        "description": "Die besten Prompts fuer Unternehmer - Lead Gen, Sales, Content, Analyse",
        "type": "prompts",
        "line": "content_factory",
        "tags": ["prompts", "business", "anfaenger", "schnell"],
    },
    {
        "title": "AI Automation Blueprint - KMU",
        "description": "Schritt-fuer-Schritt Guide: So automatisiert ein KMU mit AI",
        "type": "blueprint",
        "line": "ai_ops_handwerk",
        "tags": ["kmu", "automation", "einsteiger", "breit"],
    },
    {
        "title": "BMA Checklisten-Pack DIN 14675",
        "description": "Alle Checklisten fuer Planung, Errichtung, Inbetriebnahme, Wartung",
        "type": "sop",
        "line": "bma_automation",
        "tags": ["bma", "checklisten", "norm", "nische"],
    },
    {
        "title": "Content Machine Setup Guide",
        "description": "Wie du mit Ollama + Claude Code 1000 Content Pieces pro Woche erstellst",
        "type": "blueprint",
        "line": "content_factory",
        "tags": ["content", "ollama", "automatisierung", "technik"],
    },
    {
        "title": "n8n Lead-Gen Workflow Pack",
        "description": "5 fertige n8n Workflows: X-Monitoring, CRM-Sync, Email-Follow-up",
        "type": "automation",
        "line": "ai_ops_handwerk",
        "tags": ["n8n", "leads", "crm", "automation"],
    },
]


class ProductFactory:
    """Automatisierte Signature-Produkt-Engine."""

    def __init__(self):
        PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
        if OllamaEngine is not None:
            self.ollama = OllamaEngine()
        else:
            self.ollama = None
            log.warning("OllamaEngine not available")
        self.ideas = self._load_ideas()
        self.catalog = self._load_catalog()

    def _load_ideas(self) -> list:
        if IDEAS_FILE.exists():
            try:
                return json.loads(IDEAS_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return []

    def _save_ideas(self):
        IDEAS_FILE.write_text(json.dumps(self.ideas, indent=2, ensure_ascii=False))

    def _load_catalog(self) -> list:
        if CATALOG_FILE.exists():
            try:
                return json.loads(CATALOG_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return []

    def _save_catalog(self):
        CATALOG_FILE.write_text(json.dumps(self.catalog, indent=2, ensure_ascii=False))

    # ── Step 1: Idea Inbox ───────────────────────────────────

    def add_idea(self, title: str, description: str = "", type: str = "blueprint",
                 line: str = "ai_ops_handwerk", tags: list = None,
                 product_type: str = "") -> dict:
        """Neue Produkt-Idee zur Inbox hinzufuegen."""
        idea = {
            "id": len(self.ideas) + 1,
            "title": title,
            "description": description,
            "type": product_type or type,
            "line": line,
            "tags": tags or [],
            "status": "inbox",
            "score": None,
            "score_details": {},
            "created_at": datetime.now().isoformat(),
        }
        self.ideas.append(idea)
        self._save_ideas()
        print(f"    Idee #{idea['id']} hinzugefuegt: {title}")
        return idea

    def seed_starter_ideas(self):
        """Lade die Starter-Ideen in die Inbox."""
        if self.ideas:
            print("    Inbox hat bereits Ideen. Ueberspringe Starter.")
            return

        print("    Lade 6 Starter-Ideen...")
        for idea_data in STARTER_IDEAS:
            self.add_idea(**idea_data)
        print(f"    {len(STARTER_IDEAS)} Starter-Ideen geladen!")

    # ── Step 2: Idea Scoring ─────────────────────────────────

    async def score_idea(self, idea_id: int) -> dict:
        """Bewertet eine Idee nach Revenue-Potenzial."""
        idea = next((i for i in self.ideas if i["id"] == idea_id), None)
        if not idea:
            return {"error": f"Idee #{idea_id} nicht gefunden"}

        product_info = PRODUCT_TYPES.get(idea["type"], PRODUCT_TYPES["blueprint"])
        line_info = SIGNATURE_LINES.get(idea["line"], {})

        prompt = f"""Bewerte diese Produkt-Idee fuer ein AI-Business:

IDEE: {idea['title']}
BESCHREIBUNG: {idea.get('description', '')}
PRODUKT-TYP: {product_info['name']} (Preis: {product_info['price_range'][0]}-{product_info['price_range'][1]} EUR)
PRODUKTLINIE: {line_info.get('name', '?')}
ZIELGRUPPE: {line_info.get('audience', '?')}
USP: {line_info.get('usp', '?')}

KONTEXT: Maurice Pfeifer, 33, Elektrotechnikmeister, 16 Jahre BMA-Expertise.
Verkauft auf Gumroad, Fiverr. Budget: minimal. Muss schnell Umsatz machen.

Bewerte JEDES Kriterium von 1-10 und begruende kurz:

1. Zahlungsbereitschaft (Gewicht 3x): Wuerde jemand dafuer zahlen?
2. Umsetzungsgeschwindigkeit (Gewicht 2.5x): Wie schnell fertig?
3. Wiederverwendbarkeit (Gewicht 2x): Mehrfach verkaufbar ohne Anpassung?
4. Differenzierung (Gewicht 2x): Wie einzigartig?
5. Marktgroesse (Gewicht 1.5x): Wie viele potenzielle Kaeufer?

Antworte als JSON:
{{"zahlungsbereitschaft": {{"score": X, "grund": "..."}},
"umsetzungsgeschwindigkeit": {{"score": X, "grund": "..."}},
"wiederverwendbarkeit": {{"score": X, "grund": "..."}},
"differenzierung": {{"score": X, "grund": "..."}},
"marktgroesse": {{"score": X, "grund": "..."}}}}"""

        if self.ollama is None:
            # Static scoring fallback
            scores = self._static_score(idea)
        else:
            response = await self.ollama.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=800,
            )

            if response.success:
                try:
                    content = response.content.strip()
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    if start >= 0 and end > start:
                        scores = json.loads(content[start:end])
                    else:
                        scores = self._static_score(idea)
                except (json.JSONDecodeError, ValueError):
                    scores = self._static_score(idea)
            else:
                scores = self._static_score(idea)

        # Gewichtete Gesamtpunktzahl berechnen
        total = 0.0
        max_total = 0.0
        for criterion, config in SCORING_CRITERIA.items():
            if criterion in scores:
                s = scores[criterion]
                score_val = s.get("score", 5) if isinstance(s, dict) else s
                total += score_val * config["weight"]
            max_total += 10 * config["weight"]

        final_score = round((total / max_total) * 100, 1) if max_total > 0 else 0

        idea["score"] = final_score
        idea["score_details"] = scores
        idea["status"] = "scored"
        self._save_ideas()

        return {"id": idea_id, "score": final_score, "details": scores}

    def _static_score(self, idea: dict) -> dict:
        """Fallback-Scoring ohne AI."""
        type_scores = {
            "blueprint": {"z": 7, "u": 8, "w": 9, "d": 5, "m": 7},
            "sop": {"z": 8, "u": 6, "w": 8, "d": 7, "m": 6},
            "prompts": {"z": 6, "u": 9, "w": 10, "d": 4, "m": 8},
            "automation": {"z": 8, "u": 5, "w": 7, "d": 7, "m": 6},
            "signature": {"z": 9, "u": 3, "w": 6, "d": 9, "m": 5},
        }
        scores = type_scores.get(idea.get("type", "blueprint"), type_scores["blueprint"])
        # BMA-Nische bekommt Differenzierungs-Bonus
        if "bma" in idea.get("tags", []):
            scores["d"] = min(10, scores["d"] + 3)

        return {
            "zahlungsbereitschaft": {"score": scores["z"], "grund": "Statische Bewertung"},
            "umsetzungsgeschwindigkeit": {"score": scores["u"], "grund": "Statische Bewertung"},
            "wiederverwendbarkeit": {"score": scores["w"], "grund": "Statische Bewertung"},
            "differenzierung": {"score": scores["d"], "grund": "Statische Bewertung"},
            "marktgroesse": {"score": scores["m"], "grund": "Statische Bewertung"},
        }

    async def score_all(self):
        """Bewertet alle unscored Ideen."""
        unscored = [i for i in self.ideas if i.get("status") == "inbox"]
        print(f"\n    Bewerte {len(unscored)} Ideen...")

        for idea in unscored:
            result = await self.score_idea(idea["id"])
            if "error" not in result:
                print(f"    #{idea['id']} {idea['title'][:35]:.<40s} Score: {result['score']}")

        # Ranking anzeigen
        self._show_ranking()

    def _show_ranking(self):
        """Zeigt Ideen sortiert nach Score."""
        scored = [i for i in self.ideas if i.get("score") is not None]
        scored.sort(key=lambda x: x["score"], reverse=True)

        print(f"\n    {'='*55}")
        print(f"    {'Rank':<5} {'Score':<7} {'Type':<12} {'Title'}")
        print(f"    {'='*55}")
        for rank, idea in enumerate(scored, 1):
            marker = " <<<" if rank <= 3 else ""
            print(f"    {rank:<5} {idea['score']:<7.1f} {idea['type']:<12} {idea['title'][:35]}{marker}")
        print(f"    {'='*55}")

    # ── Step 3: Offer Design ─────────────────────────────────

    async def design_offer(self, idea_id: int) -> dict:
        """Designt ein Angebot fuer eine Produkt-Idee."""
        idea = next((i for i in self.ideas if i["id"] == idea_id), None)
        if not idea:
            return {"error": f"Idee #{idea_id} nicht gefunden"}

        product_info = PRODUCT_TYPES.get(idea["type"], PRODUCT_TYPES["blueprint"])
        line_info = SIGNATURE_LINES.get(idea["line"], {})
        price_low, price_high = product_info["price_range"]

        prompt = f"""Designe ein verkaufsfertiges Angebot:

PRODUKT: {idea['title']}
BESCHREIBUNG: {idea.get('description', '')}
TYP: {product_info['name']}
ZIELGRUPPE: {line_info.get('audience', 'Unternehmer')}
PREIS-RANGE: {price_low}-{price_high} EUR

ERSTELLE:
1. Headline (max 10 Woerter, Ergebnis-orientiert)
2. Subheadline (1 Satz, Nutzenversprechen)
3. 5 Bullet Points (Was der Kaeufer bekommt - konkret)
4. 3-Tier Pricing:
   - Basic ({price_low} EUR): [Was enthalten]
   - Pro ({(price_low+price_high)//2} EUR): [Was enthalten]
   - Elite ({price_high} EUR): [Was enthalten]
5. Einwandbehandlung (3 haeufige Einwaende + Antworten)
6. CTA (Call-to-Action Satz)
7. Garantie (z.B. 30 Tage Geld zurueck)

Antworte als JSON:
{{"headline": "...", "subheadline": "...", "bullets": [...], "pricing": {{...}}, "objections": [...], "cta": "...", "guarantee": "..."}}"""

        if self.ollama:
            response = await self.ollama.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500,
            )
            if response.success:
                try:
                    content = response.content.strip()
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    if start >= 0 and end > start:
                        offer = json.loads(content[start:end])
                    else:
                        offer = self._static_offer(idea, product_info)
                except (json.JSONDecodeError, ValueError):
                    offer = self._static_offer(idea, product_info)
            else:
                offer = self._static_offer(idea, product_info)
        else:
            offer = self._static_offer(idea, product_info)

        # In Katalog speichern
        product = {
            "id": len(self.catalog) + 1,
            "idea_id": idea_id,
            "title": idea["title"],
            "type": idea["type"],
            "line": idea.get("line", ""),
            "offer": offer,
            "status": "designed",
            "created_at": datetime.now().isoformat(),
        }
        self.catalog.append(product)
        self._save_catalog()

        idea["status"] = "designed"
        self._save_ideas()

        # Offer als Markdown speichern
        product_dir = PRODUCTS_DIR / f"product_{product['id']}"
        product_dir.mkdir(exist_ok=True)
        md = self._offer_to_markdown(product)
        (product_dir / "offer.md").write_text(md, encoding="utf-8")
        print(f"    Offer gespeichert: {product_dir}/offer.md")

        return product

    def _static_offer(self, idea: dict, product_info: dict) -> dict:
        """Fallback Offer ohne AI."""
        p_low, p_high = product_info["price_range"]
        return {
            "headline": idea["title"],
            "subheadline": f"Der komplette Guide fuer {idea.get('description', idea['title'])}",
            "bullets": product_info["contents"],
            "pricing": {
                "basic": {"price": p_low, "includes": product_info["contents"][:2]},
                "pro": {"price": (p_low + p_high) // 2, "includes": product_info["contents"][:3]},
                "elite": {"price": p_high, "includes": product_info["contents"]},
            },
            "objections": [
                {"objection": "Zu teuer", "answer": f"Spart dir {product_info['effort_hours']*10}+ Stunden Arbeit"},
                {"objection": "Brauche ich das?", "answer": "30 Tage Geld-zurueck-Garantie"},
                {"objection": "Gibt es kostenlos?", "answer": "Nicht in dieser Qualitaet und Praxis-Naehe"},
            ],
            "cta": f"Jetzt {idea['title']} sichern - Sofort-Download",
            "guarantee": "30 Tage Geld-zurueck-Garantie. Kein Risiko.",
        }

    def _offer_to_markdown(self, product: dict) -> str:
        """Konvertiert Offer zu Markdown."""
        offer = product.get("offer", {})
        lines = [
            f"# {offer.get('headline', product['title'])}",
            "",
            f"**{offer.get('subheadline', '')}**",
            "",
            "---",
            "",
            "## Was du bekommst:",
            "",
        ]
        for bullet in offer.get("bullets", []):
            lines.append(f"- {bullet}")

        pricing = offer.get("pricing", {})
        if pricing:
            lines.extend(["", "---", "", "## Pricing", ""])
            for tier, info in pricing.items():
                if isinstance(info, dict):
                    price = info.get("price", "?")
                    includes = info.get("includes", [])
                    lines.append(f"### {tier.upper()} - {price} EUR")
                    for inc in includes:
                        lines.append(f"  - {inc}")
                    lines.append("")

        objections = offer.get("objections", [])
        if objections:
            lines.extend(["---", "", "## FAQ", ""])
            for obj in objections:
                if isinstance(obj, dict):
                    lines.append(f"**{obj.get('objection', '?')}**")
                    lines.append(f"> {obj.get('answer', '')}")
                    lines.append("")

        lines.extend([
            "---",
            "",
            f"## {offer.get('cta', 'Jetzt kaufen')}",
            "",
            f"*{offer.get('guarantee', '30 Tage Geld-zurueck-Garantie')}*",
        ])

        return "\n".join(lines)

    # ── Step 5: Marketing Generation ─────────────────────────

    async def generate_marketing(self, product_id: int, post_count: int = 30) -> dict:
        """Generiert Marketing-Content fuer ein Produkt."""
        product = next((p for p in self.catalog if p["id"] == product_id), None)
        if not product:
            return {"error": f"Produkt #{product_id} nicht gefunden"}

        print(f"\n    Marketing fuer: {product['title']}")

        offer = product.get("offer", {})
        headline = offer.get("headline", product["title"])
        bullets = offer.get("bullets", [])

        marketing = {
            "product_id": product_id,
            "posts": [],
            "threads": [],
            "email_sequence": [],
        }

        # X Posts generieren
        post_angles = [
            "Ergebnis/Transformation zeigen",
            "Problem der Zielgruppe ansprechen",
            "Social Proof / Testimonial",
            "Behind the Scenes - wie es entstanden ist",
            "Kontroverse These zum Thema",
            "Tutorial/Tipp als Teaser",
            "Frage an die Community",
            "FOMO / Limitierung",
            "Story / persoenliche Erfahrung",
            "CTA direkt",
        ]

        for i in range(min(post_count, 30)):
            angle = post_angles[i % len(post_angles)]
            prompt = f"""Schreibe einen X/Twitter Post fuer dieses Produkt:

PRODUKT: {headline}
BULLETS: {', '.join(bullets[:3])}
WINKEL: {angle}

REGELN:
1. Max 280 Zeichen
2. Starker Hook
3. KEINE Hashtags im Text
4. CTA am Ende (Link in Bio / DM)
5. Deutsch
6. Kein Hype ohne Substanz

Schreibe NUR den Post:"""

            if self.ollama:
                response = await self.ollama.chat(
                    [{"role": "user", "content": prompt}],
                    temperature=0.85,
                    max_tokens=400,
                )
                if response.success:
                    marketing["posts"].append({
                        "content": response.content.strip().strip('"'),
                        "angle": angle,
                        "day": (i // 3) + 1,
                    })

            print(f"\r    Posts: {i+1}/{min(post_count, 30)}", end="", flush=True)

        # 3-Email Launch Sequence
        email_prompts = [
            f"Schreibe eine Launch-Ankuendigungs-Email fuer '{headline}'. Betreff + Body. Spannung aufbauen.",
            f"Schreibe eine 'Jetzt verfuegbar' Email fuer '{headline}'. Betreff + Body. Urgency aber nicht fake.",
            f"Schreibe eine 'Letzte Chance' Email fuer '{headline}'. Betreff + Body. Zusammenfassung + CTA.",
        ]

        print()
        for i, ep in enumerate(email_prompts):
            if self.ollama:
                response = await self.ollama.chat(
                    [{"role": "user", "content": ep}],
                    temperature=0.7,
                    max_tokens=800,
                )
                if response.success:
                    marketing["email_sequence"].append({
                        "day": i * 2,
                        "content": response.content.strip(),
                    })
            print(f"    Email {i+1}/3 generiert")

        # Marketing speichern
        product_dir = PRODUCTS_DIR / f"product_{product_id}"
        product_dir.mkdir(exist_ok=True)
        (product_dir / "marketing.json").write_text(
            json.dumps(marketing, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # Posts als Markdown exportieren
        md_lines = [f"# MARKETING - {headline}", "", "---", ""]
        for post in marketing["posts"]:
            md_lines.extend([
                f"## Tag {post.get('day', '?')} - {post.get('angle', '?')}",
                "```",
                post["content"],
                "```",
                "",
            ])

        md_lines.extend(["---", "", "## EMAIL SEQUENCE", ""])
        for email in marketing["email_sequence"]:
            md_lines.extend([
                f"### Email (Tag {email.get('day', '?')})",
                "```",
                email["content"],
                "```",
                "",
            ])

        (product_dir / "marketing.md").write_text("\n".join(md_lines), encoding="utf-8")

        product["status"] = "marketed"
        self._save_catalog()

        total = len(marketing["posts"]) + len(marketing["email_sequence"])
        print(f"    Total: {total} Marketing-Pieces generiert")
        print(f"    Gespeichert: {product_dir}/")
        return marketing

    # ── Full Pipeline ────────────────────────────────────────

    async def run_pipeline(self, idea_title: str = "", idea_description: str = "",
                           product_type: str = "blueprint", line: str = "ai_ops_handwerk") -> dict:
        """Volle Pipeline: Idee → Score → Design → Marketing."""
        print(f"\n{'='*60}")
        print(f"  PRODUCT FACTORY - Full Pipeline")
        print(f"{'='*60}")

        # Step 1: Idee hinzufuegen (oder Starter laden)
        if idea_title:
            idea = self.add_idea(idea_title, idea_description, product_type, line)
        else:
            self.seed_starter_ideas()
            idea = self.ideas[0] if self.ideas else None

        if not idea:
            return {"error": "Keine Idee vorhanden"}

        # Step 2: Score
        print(f"\n  Step 2: Scoring...")
        await self.score_all()

        # Step 3: Top-Idee designen
        scored = sorted(
            [i for i in self.ideas if i.get("score")],
            key=lambda x: x["score"],
            reverse=True,
        )
        if scored:
            top = scored[0]
            print(f"\n  Step 3: Offer Design fuer #{top['id']} ({top['title']})...")
            product = await self.design_offer(top["id"])

            if "error" not in product:
                # Step 4: Marketing
                print(f"\n  Step 4: Marketing Generation...")
                marketing = await self.generate_marketing(product["id"], post_count=10)

                print(f"\n{'='*60}")
                print(f"  PIPELINE COMPLETE!")
                print(f"  Product: {top['title']}")
                print(f"  Score: {top['score']}")
                print(f"  Marketing: {len(marketing.get('posts', []))} Posts")
                print(f"{'='*60}")
                return {"idea": top, "product": product, "marketing": marketing}

        return {"status": "completed", "ideas_scored": len(scored)}

    # ── Status ───────────────────────────────────────────────

    def show_status(self):
        """Zeigt Factory Status."""
        inbox = sum(1 for i in self.ideas if i.get("status") == "inbox")
        scored = sum(1 for i in self.ideas if i.get("status") == "scored")
        designed = sum(1 for i in self.ideas if i.get("status") == "designed")
        products = len(self.catalog)

        print(f"""
{'='*60}
  PRODUCT FACTORY - Status
{'='*60}

  IDEAS:
    Inbox:            {inbox}
    Scored:           {scored}
    Designed:         {designed}
    Total:            {len(self.ideas)}

  CATALOG:
    Products:         {products}

  SIGNATURE LINES:""")
        for key, line in SIGNATURE_LINES.items():
            print(f"    [{key}] {line['name']}")
            print(f"           {line['tagline']}")

        print(f"""
  PRODUCT TYPES:""")
        for key, pt in PRODUCT_TYPES.items():
            print(f"    [{key:<12s}] {pt['name']:<25s} {pt['price_range'][0]}-{pt['price_range'][1]} EUR")

        if self.ideas:
            print(f"\n  TOP IDEAS:")
            scored_ideas = sorted(
                [i for i in self.ideas if i.get("score")],
                key=lambda x: x["score"],
                reverse=True,
            )
            for i, idea in enumerate(scored_ideas[:5], 1):
                print(f"    {i}. [{idea['score']:.0f}] {idea['title']}")

        print(f"""
  COMMANDS:
    python product_factory.py --idea "Titel" --desc "Beschreibung"
    python product_factory.py --score
    python product_factory.py --design 1
    python product_factory.py --market 1
    python product_factory.py --pipeline
{'='*60}""")


async def main():
    parser = argparse.ArgumentParser(description="Product Factory")
    parser.add_argument("--idea", type=str, help="Neue Idee Titel")
    parser.add_argument("--desc", type=str, default="", help="Idee Beschreibung")
    parser.add_argument("--type", type=str, default="blueprint",
                       choices=list(PRODUCT_TYPES.keys()), help="Produkt-Typ")
    parser.add_argument("--line", type=str, default="ai_ops_handwerk",
                       choices=list(SIGNATURE_LINES.keys()), help="Produktlinie")
    parser.add_argument("--score", action="store_true", help="Alle Ideen bewerten")
    parser.add_argument("--design", type=int, metavar="ID", help="Offer fuer Idee designen")
    parser.add_argument("--market", type=int, metavar="ID", help="Marketing generieren")
    parser.add_argument("--pipeline", action="store_true", help="Volle Pipeline")
    parser.add_argument("--seed", action="store_true", help="Starter-Ideen laden")
    args = parser.parse_args()

    factory = ProductFactory()

    if args.idea:
        factory.add_idea(args.idea, args.desc, args.type, args.line)
    elif args.score:
        await factory.score_all()
    elif args.design:
        await factory.design_offer(args.design)
    elif args.market:
        await factory.generate_marketing(args.market)
    elif args.pipeline:
        await factory.run_pipeline()
    elif args.seed:
        factory.seed_starter_ideas()
    else:
        factory.show_status()


if __name__ == "__main__":
    asyncio.run(main())
