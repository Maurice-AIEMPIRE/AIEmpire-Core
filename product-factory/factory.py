#!/usr/bin/env python3
"""
PRODUCT FACTORY - Automated Signature Product Pipeline
7-Step automated pipeline from idea to revenue.

Pipeline:
  Step 1: Idea Inbox        → Collect and store ideas
  Step 2: Idea Scoring      → Score by revenue potential, speed, differentiation
  Step 3: Product Design    → Build offer skeleton (audience, promise, tiers)
  Step 4: Asset Production  → Generate PDFs, templates, quickstart guides
  Step 5: Marketing Engine  → 30 posts, 5 threads, 3 hooks, landing copy
  Step 6: Sales/Distribution → Gumroad/LemonSqueezy setup + auto-delivery
  Step 7: Feedback Loop     → Track metrics, improve product + messaging

Product Tiers:
  A) Core Assets      → SOPs, Checklisten, Templates, Prompts, Mini-Tools
  B) Blueprint Packs  → Bundled products (29-149 EUR)
  C) Signature Products → Premium (999-5000 EUR): Sprints, Kurse, Membership

Usage:
  python factory.py status                    # Pipeline status
  python factory.py idea "Beschreibung"       # Add idea to inbox
  python factory.py score                     # Score all unscored ideas
  python factory.py design <idea_id>          # Design product from idea
  python factory.py produce <product_id>      # Generate product assets
  python factory.py market <product_id>       # Generate marketing content
  python factory.py pipeline                  # Run full pipeline
  python factory.py list                      # List all products
"""

import asyncio
import aiohttp
import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "gemini-mirror"))

from mirror_core import call_gemini, call_gemini_flash

# ── Paths ────────────────────────────────────────────────────

FACTORY_ROOT = Path(__file__).parent
PROJECT_ROOT = FACTORY_ROOT.parent
IDEAS_DIR = FACTORY_ROOT / "data" / "ideas"
RUNS_DIR = FACTORY_ROOT / "runs" / "products"
PRODUCTS_DIR = FACTORY_ROOT / "products"
MARKETING_DIR = FACTORY_ROOT / "marketing"
SALES_DIR = FACTORY_ROOT / "sales"
TEMPLATES_DIR = FACTORY_ROOT / "templates"
METRICS_FILE = FACTORY_ROOT / "runs" / "metrics.json"

for d in [IDEAS_DIR, RUNS_DIR, PRODUCTS_DIR, MARKETING_DIR, SALES_DIR, TEMPLATES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── State ────────────────────────────────────────────────────

INBOX_FILE = IDEAS_DIR / "inbox.jsonl"
RANKED_FILE = RUNS_DIR / "idea_ranked.json"
PIPELINE_STATE_FILE = FACTORY_ROOT / "runs" / "pipeline_state.json"


def load_pipeline_state() -> Dict:
    if PIPELINE_STATE_FILE.exists():
        return json.loads(PIPELINE_STATE_FILE.read_text())
    return {
        "created": datetime.now().isoformat(),
        "total_ideas": 0,
        "total_products": 0,
        "total_launched": 0,
        "total_revenue": 0.0,
        "active_products": [],
        "pipeline_runs": 0,
    }


def save_pipeline_state(state: Dict) -> None:
    state["updated"] = datetime.now().isoformat()
    PIPELINE_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


# ── Signature Product Lines ──────────────────────────────────

PRODUCT_LINES = {
    "ai_ops_handwerk": {
        "name": "AI Ops fuer Handwerk & Technik",
        "signature": "AI Ops Command Center - vom Chaos zur Maschine",
        "audience": "Kleine/mittlere Betriebe, Projektleiter, technische Dienstleister",
        "usp": "Maurice ist glaubwuerdig + Praxisfaelle ohne Ende",
        "price_tiers": {"basic": 29, "pro": 99, "elite": 299},
    },
    "legal_warroom": {
        "name": "Legal Warroom System",
        "signature": "Legal Warroom - Beweise, Timeline, Schriftsatz-Engine",
        "audience": "Unternehmer/Angestellte in Konflikten + Anwaelte",
        "usp": "Extrem hoher wahrgenommener Wert, einzigartig",
        "price_tiers": {"basic": 49, "pro": 149, "elite": 499},
    },
    "content_factory": {
        "name": "Agentic Content Factory",
        "signature": "30 Tage Content in 60 Minuten / Woche",
        "audience": "Solopreneure, B2B-Berater, Tech-Sales",
        "usp": "Skalierbar, viele Kaeufer, einfacher Einstieg",
        "price_tiers": {"basic": 27, "pro": 79, "elite": 199},
    },
}

# ── Step 1: Idea Inbox ──────────────────────────────────────

def add_idea(description: str, source: str = "user", tags: List[str] = None) -> Dict:
    """Add an idea to the inbox."""
    idea = {
        "id": f"idea_{int(time.time())}",
        "description": description,
        "source": source,
        "tags": tags or [],
        "created": datetime.now().isoformat(),
        "status": "inbox",
        "score": None,
    }

    # Append to JSONL
    with open(INBOX_FILE, "a") as f:
        f.write(json.dumps(idea, ensure_ascii=False) + "\n")

    # Update state
    state = load_pipeline_state()
    state["total_ideas"] += 1
    save_pipeline_state(state)

    print(f"  Idea added: {idea['id']}")
    print(f"  '{description[:60]}...'")

    return idea


def load_ideas() -> List[Dict]:
    """Load all ideas from inbox."""
    if not INBOX_FILE.exists():
        return []
    ideas = []
    for line in INBOX_FILE.read_text().strip().split("\n"):
        if line.strip():
            try:
                ideas.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return ideas


# ── Step 2: Idea Scoring ─────────────────────────────────────

SCORING_CRITERIA = {
    "willingness_to_pay": {"weight": 0.25, "de": "Zahlungsbereitschaft der Zielgruppe"},
    "speed_to_market": {"weight": 0.20, "de": "Schnelligkeit zur Umsetzung"},
    "reusability": {"weight": 0.15, "de": "Wiederverwendbarkeit der Assets"},
    "risk_compliance": {"weight": 0.15, "de": "Risiko/Compliance (niedrig = besser)"},
    "differentiation": {"weight": 0.15, "de": "Differenzierung (Signature-Faktor)"},
    "scalability": {"weight": 0.10, "de": "Skalierbarkeit ohne Mehraufwand"},
}


async def score_ideas() -> List[Dict]:
    """Score all unscored ideas using Gemini."""
    ideas = load_ideas()
    unscored = [i for i in ideas if i.get("score") is None]

    if not unscored:
        print("  Keine unscored Ideas vorhanden.")
        return ideas

    print(f"  Scoring {len(unscored)} Ideas...")

    prompt = f"""Bewerte diese Produktideen fuer Maurice Pfeifer's AI Empire.

MAURICE'S PROFIL:
- Elektrotechnikmeister, 37, 16 Jahre BMA-Expertise
- Ziel: 100 Mio EUR in 1-3 Jahren
- Unique: BMA + AI Kombination

BEWERTUNGSKRITERIEN (je 1-10):
{json.dumps({k: v['de'] for k, v in SCORING_CRITERIA.items()}, indent=2, ensure_ascii=False)}

IDEAS ZUM BEWERTEN:
{json.dumps([{"id": i["id"], "description": i["description"]} for i in unscored], indent=2, ensure_ascii=False)}

Bewerte JEDE Idee und berechne einen Gesamtscore (gewichtet).

Antworte als JSON Array:
[
  {{
    "id": "idea_xxx",
    "scores": {{
      "willingness_to_pay": 8,
      "speed_to_market": 9,
      "reusability": 7,
      "risk_compliance": 8,
      "differentiation": 9,
      "scalability": 6
    }},
    "total_score": 8.1,
    "recommended_product_line": "ai_ops_handwerk|legal_warroom|content_factory",
    "reasoning": "..."
  }}
]"""

    response = await call_gemini(prompt, system_instruction=(
        "Du bist der Produkt-Scoring-Agent. Bewerte Ideen objektiv nach "
        "Revenue-Potenzial und Umsetzbarkeit. Antworte NUR als valides JSON Array."
    ))

    try:
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        scored = json.loads(response.strip())
    except (json.JSONDecodeError, IndexError):
        print("  Scoring fehlgeschlagen - Gemini-Antwort nicht parsebar.")
        return ideas

    # Apply scores
    score_map = {s["id"]: s for s in scored if isinstance(s, dict)}
    for idea in ideas:
        if idea["id"] in score_map:
            idea["score"] = score_map[idea["id"]]
            idea["status"] = "scored"

    # Save updated ideas
    with open(INBOX_FILE, "w") as f:
        for idea in ideas:
            f.write(json.dumps(idea, ensure_ascii=False) + "\n")

    # Save ranked version
    ranked = sorted(ideas, key=lambda x: (x.get("score", {}).get("total_score", 0)
                                           if isinstance(x.get("score"), dict) else 0),
                    reverse=True)
    RANKED_FILE.write_text(json.dumps(ranked, indent=2, ensure_ascii=False))

    print(f"  {len(scored)} Ideas bewertet. Ranking gespeichert.")
    return ranked


# ── Step 3: Product Design ───────────────────────────────────

async def design_product(idea_id: str) -> Dict:
    """Design a product from a scored idea."""
    ideas = load_ideas()
    idea = next((i for i in ideas if i["id"] == idea_id), None)

    if not idea:
        print(f"  Idea {idea_id} nicht gefunden.")
        return {}

    score_info = idea.get("score", {})
    product_line = score_info.get("recommended_product_line", "ai_ops_handwerk") \
        if isinstance(score_info, dict) else "ai_ops_handwerk"
    line_config = PRODUCT_LINES.get(product_line, PRODUCT_LINES["ai_ops_handwerk"])

    prompt = f"""Designe ein verkaufbares Produkt aus dieser Idee.

IDEE: {idea['description']}
SCORING: {json.dumps(score_info, ensure_ascii=False)[:500]}
PRODUKTLINIE: {line_config['name']}
SIGNATURE: {line_config['signature']}
ZIELGRUPPE: {line_config['audience']}

Erstelle ein komplettes Offer Skeleton:

Antworte als JSON:
{{
  "product_id": "prod_xxx",
  "title": "Produkttitel (deutsch, catchy)",
  "subtitle": "Einzeiler der den Nutzen erklaert",
  "product_line": "{product_line}",
  "target_audience": {{
    "primary": "Hauptzielgruppe",
    "pain_points": ["..."],
    "desired_outcome": "..."
  }},
  "promise": "Das Versprechen in einem Satz",
  "modules": [
    {{"title": "Modul 1", "description": "...", "deliverables": ["..."]}},
  ],
  "pricing": {{
    "basic": {{"price": {line_config['price_tiers']['basic']}, "includes": ["..."]}},
    "pro": {{"price": {line_config['price_tiers']['pro']}, "includes": ["..."]}},
    "elite": {{"price": {line_config['price_tiers']['elite']}, "includes": ["..."]}}
  }},
  "deliverables": ["PDF Guide", "Templates", "Checklisten", "Quickstart"],
  "production_time_hours": 8,
  "unique_angle": "Was macht dieses Produkt einzigartig?"
}}"""

    print(f"  Designing product from: {idea['description'][:50]}...")
    response = await call_gemini(prompt, system_instruction=(
        "Du bist der Produkt-Designer fuer Maurice's AI Empire. "
        "Erstelle Produkte die SOFORT verkaufbar sind, echten Wert liefern, "
        "und kein Scam oder Fake-Engagement sind. QUALITAET vor Quantitaet. "
        "Antworte NUR als valides JSON."
    ))

    try:
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        product = json.loads(response.strip())
    except (json.JSONDecodeError, IndexError):
        product = {"error": "Design fehlgeschlagen", "raw": response[:500]}

    # Set product ID
    product_id = product.get("product_id", f"prod_{int(time.time())}")
    product["product_id"] = product_id
    product["source_idea"] = idea_id
    product["designed_at"] = datetime.now().isoformat()
    product["status"] = "designed"

    # Save product
    product_dir = RUNS_DIR / product_id
    product_dir.mkdir(parents=True, exist_ok=True)
    (product_dir / "offer.json").write_text(json.dumps(product, indent=2, ensure_ascii=False))

    # Also save as markdown
    offer_md = format_offer_markdown(product)
    (product_dir / "offer.md").write_text(offer_md)

    print(f"  Product designed: {product_id}")
    print(f"  Title: {product.get('title', 'N/A')}")
    print(f"  Saved to: {product_dir}")

    return product


def format_offer_markdown(product: Dict) -> str:
    """Format a product offer as readable markdown."""
    lines = [
        f"# {product.get('title', 'Untitled')}",
        f"*{product.get('subtitle', '')}*",
        "",
        f"## Zielgruppe",
        f"{json.dumps(product.get('target_audience', {}), indent=2, ensure_ascii=False)}",
        "",
        f"## Versprechen",
        f"{product.get('promise', '')}",
        "",
        f"## Module",
    ]

    for mod in product.get("modules", []):
        if isinstance(mod, dict):
            lines.append(f"### {mod.get('title', 'N/A')}")
            lines.append(f"{mod.get('description', '')}")
            for d in mod.get("deliverables", []):
                lines.append(f"- {d}")
            lines.append("")

    lines.append("## Preisstruktur")
    pricing = product.get("pricing", {})
    for tier, info in pricing.items():
        if isinstance(info, dict):
            lines.append(f"### {tier.upper()} - {info.get('price', '?')} EUR")
            for item in info.get("includes", []):
                lines.append(f"- {item}")
            lines.append("")

    lines.append(f"## Unique Angle")
    lines.append(f"{product.get('unique_angle', '')}")
    lines.append("")
    lines.append(f"---")
    lines.append(f"*Product ID: {product.get('product_id', 'N/A')}*")
    lines.append(f"*Designed: {product.get('designed_at', 'N/A')}*")

    return "\n".join(lines)


# ── Step 4: Asset Production ─────────────────────────────────

async def produce_assets(product_id: str) -> Dict:
    """Generate all product assets (content, templates, guides)."""
    offer_file = RUNS_DIR / product_id / "offer.json"
    if not offer_file.exists():
        print(f"  Product {product_id} nicht gefunden.")
        return {}

    product = json.loads(offer_file.read_text())
    bundle_dir = PRODUCTS_DIR / product_id / "bundle"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    print(f"  Producing assets for: {product.get('title', product_id)}")

    # Generate each deliverable
    deliverables = product.get("deliverables", ["Guide", "Templates", "Checkliste"])

    for i, deliverable in enumerate(deliverables, 1):
        print(f"  [{i}/{len(deliverables)}] Generating: {deliverable}")
        content = await generate_asset(product, deliverable)

        # Save as markdown (can be converted to PDF later)
        safe_name = deliverable.lower().replace(" ", "_").replace("/", "_")
        asset_file = bundle_dir / f"{safe_name}.md"
        asset_file.write_text(content)

    # Generate quickstart guide
    print(f"  Generating quickstart guide...")
    quickstart = await generate_quickstart(product)
    (bundle_dir / "quickstart.md").write_text(quickstart)

    # Update product status
    product["status"] = "produced"
    product["produced_at"] = datetime.now().isoformat()
    product["asset_count"] = len(deliverables) + 1
    (RUNS_DIR / product_id / "offer.json").write_text(
        json.dumps(product, indent=2, ensure_ascii=False))

    print(f"  Assets produced: {len(deliverables) + 1} files in {bundle_dir}")
    return product


async def generate_asset(product: Dict, deliverable: str) -> str:
    """Generate a single product asset using Gemini."""
    prompt = f"""Erstelle den folgenden Inhalt fuer das Produkt:

PRODUKT: {product.get('title', 'N/A')}
ZIELGRUPPE: {json.dumps(product.get('target_audience', {}), ensure_ascii=False)[:300]}
VERSPRECHEN: {product.get('promise', 'N/A')}

ZU ERSTELLEN: {deliverable}

Erstelle professionellen, sofort nutzbaren Content im Markdown-Format.
- Klar strukturiert mit Ueberschriften
- Praktische Beispiele und Vorlagen
- Actionable Steps (kein Blabla)
- Deutsch, professioneller Ton
- Mindestens 500 Woerter

WICHTIG: Der Content muss ECHTEN WERT liefern. Kein Filler, kein Scam.
Jemand der das kauft muss danach BESSER dastehen als vorher."""

    return await call_gemini(prompt, system_instruction=(
        "Du bist ein professioneller Content-Ersteller fuer digitale Produkte. "
        "Erstelle hochwertigen, praxisnahen Content der echten Mehrwert liefert. "
        "Format: Markdown. Sprache: Deutsch. Ton: Professionell aber zugaenglich."
    ), max_tokens=4096)


async def generate_quickstart(product: Dict) -> str:
    """Generate a quickstart guide for the product."""
    prompt = f"""Erstelle einen Quickstart Guide fuer:

PRODUKT: {product.get('title', 'N/A')}
MODULE: {json.dumps(product.get('modules', []), ensure_ascii=False)[:500]}

Der Quickstart Guide muss:
1. In 10 Minuten lesbar sein
2. Sofort umsetzbare erste Schritte enthalten
3. Die wichtigsten Ergebnisse in den ersten 24h ermoeglichen
4. Klar zeigen wo man anfaengt und was der naechste Schritt ist

Format: Markdown. Sprache: Deutsch."""

    return await call_gemini_flash(prompt, system_instruction=(
        "Erstelle einen klaren, kurzen Quickstart Guide. "
        "Fokus auf sofortige Umsetzbarkeit. Keine Theorie, nur Praxis."
    ))


# ── Step 5: Marketing Content Engine ─────────────────────────

async def generate_marketing(product_id: str) -> Dict:
    """Generate complete marketing content for a product."""
    offer_file = RUNS_DIR / product_id / "offer.json"
    if not offer_file.exists():
        print(f"  Product {product_id} nicht gefunden.")
        return {}

    product = json.loads(offer_file.read_text())
    mkt_dir = MARKETING_DIR / product_id
    mkt_dir.mkdir(parents=True, exist_ok=True)

    print(f"  Generating marketing for: {product.get('title', product_id)}")

    # Generate all marketing assets in parallel
    tasks = {
        "posts": generate_social_posts(product),
        "threads": generate_threads(product),
        "hooks": generate_hooks(product),
        "landing": generate_landing_copy(product),
        "emails": generate_email_sequence(product),
    }

    results = {}
    for name, coro in tasks.items():
        print(f"  Generating: {name}...")
        results[name] = await coro

    # Save all marketing assets
    for name, content in results.items():
        if isinstance(content, str):
            (mkt_dir / f"{name}.md").write_text(content)
        elif isinstance(content, (list, dict)):
            (mkt_dir / f"{name}.json").write_text(
                json.dumps(content, indent=2, ensure_ascii=False))

    # Update product
    product["marketing_generated"] = True
    product["marketing_at"] = datetime.now().isoformat()
    (RUNS_DIR / product_id / "offer.json").write_text(
        json.dumps(product, indent=2, ensure_ascii=False))

    print(f"  Marketing generated: {len(results)} asset types in {mkt_dir}")
    return results


async def generate_social_posts(product: Dict) -> str:
    """Generate 30 social media posts."""
    prompt = f"""Erstelle 30 Social Media Posts fuer dieses Produkt:

PRODUKT: {product.get('title', 'N/A')}
VERSPRECHEN: {product.get('promise', 'N/A')}
ZIELGRUPPE: {json.dumps(product.get('target_audience', {}), ensure_ascii=False)[:300]}
PREIS: {json.dumps(product.get('pricing', {}), ensure_ascii=False)[:200]}

Erstelle 30 Posts die:
- Mix aus Storytelling, Tipps, Behind-the-Scenes, Social Proof, CTA
- Fuer X/Twitter optimiert (max 280 Zeichen pro Post)
- KEIN Fake-Engagement, keine Scam-Taktiken
- Authentisch, ehrlich, wertliefend
- 10 Posts pro Woche fuer 3 Wochen

Format: Nummeriert, 1 Post pro Zeile. Deutsch."""

    return await call_gemini(prompt, system_instruction=(
        "Du bist ein Social Media Stratege. Erstelle authentische, "
        "wertliefernde Posts. Kein Scam, kein Fake. Echte Tipps + echte CTAs."
    ), max_tokens=4096)


async def generate_threads(product: Dict) -> str:
    """Generate 5 Twitter/X threads."""
    prompt = f"""Erstelle 5 X/Twitter Threads fuer:

PRODUKT: {product.get('title', 'N/A')}
VERSPRECHEN: {product.get('promise', 'N/A')}
ZIELGRUPPE: {product.get('target_audience', {}).get('primary', 'N/A')}

Jeder Thread:
- 5-8 Tweets
- Hook → Value → CTA
- Echter Mehrwert in jedem Tweet
- Deutsche Sprache

Format: Thread 1, Thread 2, etc. mit nummerierten Tweets."""

    return await call_gemini(prompt, system_instruction=(
        "Erstelle virale Threads die echten Wert liefern. "
        "Jeder Thread muss standalone funktionieren und zum Produkt fuehren."
    ), max_tokens=4096)


async def generate_hooks(product: Dict) -> str:
    """Generate 3 attention hooks."""
    prompt = f"""Erstelle 3 Attention Hooks fuer:

PRODUKT: {product.get('title', 'N/A')}
VERSPRECHEN: {product.get('promise', 'N/A')}
PAIN POINTS: {json.dumps(product.get('target_audience', {}).get('pain_points', []), ensure_ascii=False)}

Jeder Hook muss:
- In 2 Sekunden Aufmerksamkeit fangen
- Neugier wecken
- Zum Weiterlesen zwingen
- Authentisch sein (kein Clickbait-Scam)

Format: 3 Hooks mit Erklaerung warum sie funktionieren."""

    return await call_gemini_flash(prompt, system_instruction=(
        "Erstelle Hooks die Aufmerksamkeit fangen. Ehrlich und authentisch."
    ))


async def generate_landing_copy(product: Dict) -> str:
    """Generate landing page copy."""
    prompt = f"""Erstelle Landing Page Copy fuer:

PRODUKT: {product.get('title', 'N/A')}
SUBTITLE: {product.get('subtitle', 'N/A')}
VERSPRECHEN: {product.get('promise', 'N/A')}
ZIELGRUPPE: {json.dumps(product.get('target_audience', {}), ensure_ascii=False)[:300]}
PREISSTRUKTUR: {json.dumps(product.get('pricing', {}), ensure_ascii=False)[:300]}
MODULE: {json.dumps(product.get('modules', []), ensure_ascii=False)[:500]}

Erstelle:
1. Headline + Subheadline
2. Problem-Agitation-Solution
3. Feature-Benefit Liste
4. Social Proof Platzhalter
5. Pricing Table (3 Tiers)
6. FAQ (5 Fragen)
7. Final CTA

Format: Markdown. Sprache: Deutsch. Ton: Ueberzeugend aber ehrlich."""

    return await call_gemini(prompt, system_instruction=(
        "Du bist ein Conversion Copywriter. Erstelle Landing Page Copy "
        "die verkauft ohne zu luegen. Ehrliche Versprechen, echte Vorteile."
    ), max_tokens=4096)


async def generate_email_sequence(product: Dict) -> str:
    """Generate a 5-email sales sequence."""
    prompt = f"""Erstelle eine 5-Email Sales Sequence fuer:

PRODUKT: {product.get('title', 'N/A')}
VERSPRECHEN: {product.get('promise', 'N/A')}
PREIS: {json.dumps(product.get('pricing', {}), ensure_ascii=False)[:200]}

Email Sequence:
1. Welcome + Quick Win
2. Problem vertiefend + Story
3. Loesung vorstellen + Beweis
4. FAQ + Einwaende behandeln
5. Final CTA + Dringlichkeit (ehrlich)

Jede Email: Subject Line + Body (300-500 Woerter). Deutsch."""

    return await call_gemini(prompt, system_instruction=(
        "Erstelle eine Email-Sequenz die konvertiert. "
        "Ehrlich, wertliefend, respektvoll. Kein Spam-Ton."
    ), max_tokens=4096)


# ── Step 6: Sales/Distribution ───────────────────────────────

async def setup_sales(product_id: str) -> Dict:
    """Generate sales setup instructions and delivery config."""
    offer_file = RUNS_DIR / product_id / "offer.json"
    if not offer_file.exists():
        return {}

    product = json.loads(offer_file.read_text())
    sales_dir = SALES_DIR / product_id
    sales_dir.mkdir(parents=True, exist_ok=True)

    delivery = {
        "product_id": product_id,
        "title": product.get("title", ""),
        "platforms": {
            "gumroad": {
                "setup": f"https://app.gumroad.com/products/new",
                "pricing": product.get("pricing", {}),
                "delivery": "Digital download (ZIP bundle)",
            },
            "lemonsqueezy": {
                "setup": f"https://app.lemonsqueezy.com/products/new",
                "pricing": product.get("pricing", {}),
                "delivery": "Digital download + license key",
            },
        },
        "bundle_contents": list((PRODUCTS_DIR / product_id / "bundle").glob("*"))
                           if (PRODUCTS_DIR / product_id / "bundle").exists() else [],
        "auto_delivery": True,
        "created": datetime.now().isoformat(),
    }

    # Convert Path objects to strings
    delivery["bundle_contents"] = [str(f.name) for f in delivery["bundle_contents"]
                                    if isinstance(f, Path)]

    (sales_dir / "delivery.json").write_text(
        json.dumps(delivery, indent=2, ensure_ascii=False))

    # Generate Gumroad listing
    listing = await generate_listing(product)
    (sales_dir / "gumroad_listing.md").write_text(listing)

    print(f"  Sales setup created: {sales_dir}")
    return delivery


async def generate_listing(product: Dict) -> str:
    """Generate marketplace listing copy."""
    prompt = f"""Erstelle eine Gumroad/LemonSqueezy Produkt-Listing fuer:

PRODUKT: {product.get('title', 'N/A')}
SUBTITLE: {product.get('subtitle', 'N/A')}
VERSPRECHEN: {product.get('promise', 'N/A')}
PREISE: {json.dumps(product.get('pricing', {}), ensure_ascii=False)[:300]}

Erstelle:
- Produkt-Titel (catchy)
- Kurzbeschreibung (2 Saetze)
- Ausfuehrliche Beschreibung (mit Bullet Points)
- Was enthalten ist (Deliverables)
- Fuer wen ist das (und fuer wen NICHT)
- Pricing Tiers erklaert

Format: Markdown. Sprache: Deutsch. Bereit zum Copy-Paste in Gumroad."""

    return await call_gemini_flash(prompt, system_instruction=(
        "Erstelle eine Marketplace-Listing die klar kommuniziert was der "
        "Kaeufer bekommt und warum es den Preis wert ist."
    ))


# ── Step 7: Feedback Loop ────────────────────────────────────

def record_metrics(product_id: str, metrics: Dict) -> None:
    """Record product metrics for the feedback loop."""
    all_metrics = {}
    if METRICS_FILE.exists():
        all_metrics = json.loads(METRICS_FILE.read_text())

    if product_id not in all_metrics:
        all_metrics[product_id] = {"entries": [], "created": datetime.now().isoformat()}

    all_metrics[product_id]["entries"].append({
        **metrics,
        "recorded_at": datetime.now().isoformat(),
    })

    METRICS_FILE.write_text(json.dumps(all_metrics, indent=2, ensure_ascii=False))


# ── Full Pipeline ────────────────────────────────────────────

async def run_full_pipeline(idea_description: str = None) -> Dict:
    """Run the full 7-step pipeline."""
    print("\n  PRODUCT FACTORY - Full Pipeline")
    print("  " + "=" * 50)

    results = {}

    # Step 1: Add idea (if provided)
    if idea_description:
        print("\n  [Step 1/7] Adding idea to inbox...")
        idea = add_idea(idea_description)
        results["idea"] = idea

    # Step 2: Score ideas
    print("\n  [Step 2/7] Scoring ideas...")
    ranked = await score_ideas()
    results["ranked"] = [r.get("id") for r in ranked[:5]]

    if not ranked:
        print("  No ideas to process.")
        return results

    # Use top-ranked idea
    top_idea = ranked[0]
    idea_id = top_idea["id"]
    print(f"  Top idea: {top_idea.get('description', 'N/A')[:50]}")

    # Step 3: Design product
    print(f"\n  [Step 3/7] Designing product from {idea_id}...")
    product = await design_product(idea_id)
    product_id = product.get("product_id")
    results["product"] = product_id

    if not product_id:
        print("  Design failed.")
        return results

    # Step 4: Produce assets
    print(f"\n  [Step 4/7] Producing assets for {product_id}...")
    await produce_assets(product_id)

    # Step 5: Generate marketing
    print(f"\n  [Step 5/7] Generating marketing for {product_id}...")
    marketing = await generate_marketing(product_id)
    results["marketing"] = list(marketing.keys()) if marketing else []

    # Step 6: Setup sales
    print(f"\n  [Step 6/7] Setting up sales for {product_id}...")
    sales = await setup_sales(product_id)
    results["sales"] = bool(sales)

    # Step 7: Initialize metrics
    print(f"\n  [Step 7/7] Initializing metrics tracking...")
    record_metrics(product_id, {
        "event": "pipeline_complete",
        "steps_completed": 7,
    })

    # Update pipeline state
    state = load_pipeline_state()
    state["total_products"] += 1
    state["pipeline_runs"] += 1
    state["active_products"].append(product_id)
    save_pipeline_state(state)

    print(f"\n  PIPELINE COMPLETE")
    print(f"  Product: {product.get('title', product_id)}")
    print(f"  ID: {product_id}")
    print(f"  Files: {PRODUCTS_DIR / product_id}")
    print(f"  Marketing: {MARKETING_DIR / product_id}")
    print(f"  Sales: {SALES_DIR / product_id}")

    return results


# ── Status Display ───────────────────────────────────────────

def show_status() -> None:
    """Show factory pipeline status."""
    state = load_pipeline_state()

    print("\n  PRODUCT FACTORY STATUS")
    print("  " + "=" * 50)
    print(f"  Total Ideas:    {state.get('total_ideas', 0)}")
    print(f"  Total Products: {state.get('total_products', 0)}")
    print(f"  Launched:       {state.get('total_launched', 0)}")
    print(f"  Revenue:        {state.get('total_revenue', 0):.2f} EUR")
    print(f"  Pipeline Runs:  {state.get('pipeline_runs', 0)}")

    # Active products
    active = state.get("active_products", [])
    if active:
        print(f"\n  ACTIVE PRODUCTS ({len(active)}):")
        for pid in active:
            offer_file = RUNS_DIR / pid / "offer.json"
            if offer_file.exists():
                p = json.loads(offer_file.read_text())
                status = p.get("status", "?")
                title = p.get("title", pid)
                print(f"    [{status:10s}] {title[:50]}")
            else:
                print(f"    [unknown   ] {pid}")

    # Ideas inbox
    ideas = load_ideas()
    if ideas:
        unscored = [i for i in ideas if i.get("score") is None]
        scored = [i for i in ideas if i.get("score") is not None]
        print(f"\n  IDEAS: {len(ideas)} total ({len(unscored)} unscored, {len(scored)} scored)")

    # Product lines
    print(f"\n  PRODUCT LINES:")
    for key, line in PRODUCT_LINES.items():
        print(f"    {line['name']}")
        print(f"      {line['signature']}")
        print(f"      Preise: {line['price_tiers']}")

    # Directories
    print(f"\n  DIRECTORIES:")
    for name, path in [("Ideas", IDEAS_DIR), ("Products", PRODUCTS_DIR),
                        ("Marketing", MARKETING_DIR), ("Sales", SALES_DIR)]:
        if path.exists():
            files = list(path.rglob("*"))
            file_count = len([f for f in files if f.is_file()])
            print(f"    {name:12s}: {file_count} files")

    print()


def list_products() -> None:
    """List all products in the pipeline."""
    print("\n  ALL PRODUCTS")
    print("  " + "=" * 50)

    if not RUNS_DIR.exists():
        print("  Keine Produkte vorhanden.\n")
        return

    for product_dir in sorted(RUNS_DIR.iterdir()):
        if product_dir.is_dir():
            offer_file = product_dir / "offer.json"
            if offer_file.exists():
                p = json.loads(offer_file.read_text())
                print(f"\n  {p.get('product_id', product_dir.name)}")
                print(f"    Title:    {p.get('title', 'N/A')}")
                print(f"    Status:   {p.get('status', 'N/A')}")
                print(f"    Line:     {p.get('product_line', 'N/A')}")
                print(f"    Designed: {p.get('designed_at', 'N/A')[:10]}")

                pricing = p.get("pricing", {})
                if pricing:
                    prices = [f"{t}: {info.get('price', '?')} EUR"
                              for t, info in pricing.items() if isinstance(info, dict)]
                    print(f"    Pricing:  {', '.join(prices)}")

    print()


# ── Main ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Product Factory - Automated Signature Product Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="Show pipeline status")
    sub.add_parser("list", help="List all products")

    idea_p = sub.add_parser("idea", help="Add idea to inbox")
    idea_p.add_argument("description", type=str, help="Idea description")

    sub.add_parser("score", help="Score all unscored ideas")

    design_p = sub.add_parser("design", help="Design product from idea")
    design_p.add_argument("idea_id", type=str, help="Idea ID")

    produce_p = sub.add_parser("produce", help="Generate product assets")
    produce_p.add_argument("product_id", type=str, help="Product ID")

    market_p = sub.add_parser("market", help="Generate marketing content")
    market_p.add_argument("product_id", type=str, help="Product ID")

    pipeline_p = sub.add_parser("pipeline", help="Run full pipeline")
    pipeline_p.add_argument("--idea", type=str, help="Start with this idea")

    args = parser.parse_args()

    if args.command == "status" or not args.command:
        show_status()
    elif args.command == "list":
        list_products()
    elif args.command == "idea":
        add_idea(args.description)
    elif args.command == "score":
        asyncio.run(score_ideas())
    elif args.command == "design":
        asyncio.run(design_product(args.idea_id))
    elif args.command == "produce":
        asyncio.run(produce_assets(args.product_id))
    elif args.command == "market":
        asyncio.run(generate_marketing(args.product_id))
    elif args.command == "pipeline":
        asyncio.run(run_full_pipeline(args.idea))


if __name__ == "__main__":
    main()
