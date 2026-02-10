#!/usr/bin/env python3
"""
PRODUCT FACTORY PIPELINE - Von Idee bis Verkauf.

Automatisierte Pipeline:
1. Idea Inbox → Sammeln
2. Scoring → Bewerten
3. Offer Design → Angebot bauen
4. Asset Production → Dateien erstellen
5. Marketing → Content generieren
6. Distribution → Verkaufskanal
7. Feedback → Optimieren

Usage:
  python product_pipeline.py add "AI Ops Checkliste für Handwerker"
  python product_pipeline.py score                    # Alle Ideen bewerten
  python product_pipeline.py rank                     # Top Ideen anzeigen
  python product_pipeline.py design <idea_id>         # Offer erstellen
  python product_pipeline.py build <product_id>       # Assets bauen
  python product_pipeline.py marketing <product_id>   # Content generieren
  python product_pipeline.py status                   # Pipeline Status
"""

import argparse
import json
import os
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

# Paths
FACTORY_DIR = Path(__file__).parent
DATA_DIR = FACTORY_DIR / "data"
IDEAS_DIR = DATA_DIR / "ideas"
RUNS_DIR = FACTORY_DIR / "runs" / "products"
PRODUCTS_DIR = FACTORY_DIR / "products"
CONFIG_DIR = FACTORY_DIR.parent / "config"

IDEAS_DIR.mkdir(parents=True, exist_ok=True)
RUNS_DIR.mkdir(parents=True, exist_ok=True)
PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)

INBOX_FILE = IDEAS_DIR / "inbox.jsonl"
RANKED_FILE = RUNS_DIR / "idea_ranked.json"

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
DEFAULT_MODEL = "qwen2.5-coder:14b"
FAST_MODEL = "llama3.1:8b"


# ── SCORING ─────────────────────────────────────────────────────────

def load_scoring_config() -> dict:
    config_file = CONFIG_DIR / "product_scoring.json"
    if config_file.exists():
        return json.loads(config_file.read_text())
    return {
        "scoring_dimensions": {
            "payment_willingness": {"weight": 0.25},
            "speed_to_market": {"weight": 0.20},
            "reusability": {"weight": 0.20},
            "compliance": {"weight": 0.15},
            "signature_factor": {"weight": 0.20},
        },
        "thresholds": {"minimum_score": 6.0, "auto_approve": 8.0},
    }


def ollama_generate(prompt: str, model: str = None) -> str:
    """Call Ollama for text generation."""
    model = model or FAST_MODEL
    try:
        result = subprocess.run(
            ["curl", "-s", f"{OLLAMA_HOST}/api/generate",
             "-d", json.dumps({"model": model, "prompt": prompt, "stream": False})],
            capture_output=True, text=True, timeout=120
        )
        response = json.loads(result.stdout)
        return response.get("response", "")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return "[Ollama nicht erreichbar]"


# ── PIPELINE STEPS ──────────────────────────────────────────────────

def add_idea(title: str, tags: list = None, source: str = "manual"):
    """Step 1: Add idea to inbox."""
    idea = {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "tags": tags or [],
        "source": source,
        "created": datetime.now().isoformat(),
        "status": "new",
    }

    with open(INBOX_FILE, "a") as f:
        f.write(json.dumps(idea, ensure_ascii=False) + "\n")

    print(f"  [+] Idee hinzugefügt: {idea['id']} - {title}")
    return idea


def load_ideas() -> list:
    """Load all ideas from inbox."""
    ideas = []
    if INBOX_FILE.exists():
        for line in INBOX_FILE.read_text().strip().split("\n"):
            if line.strip():
                try:
                    ideas.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return ideas


def score_ideas():
    """Step 2: Score all unscored ideas using Ollama."""
    ideas = load_ideas()
    config = load_scoring_config()
    dims = config["scoring_dimensions"]
    scored = []

    print(f"\n  Scoring {len(ideas)} Ideen...\n")

    for idea in ideas:
        if idea.get("score"):
            scored.append(idea)
            continue

        prompt = f"""Bewerte diese Produktidee auf einer Skala von 1-10 für jede Dimension.
Antwort NUR als JSON, keine Erklärung.

Idee: "{idea['title']}"

Kontext: Maurice Pfeifer, 37, Elektrotechnikmeister, 16 Jahre BMA-Expertise.
Zielgruppe: Handwerker, Projektleiter, technische Dienstleister, Solo-Unternehmer.

Bewerte:
- payment_willingness: Würde jemand dafür zahlen? (1-10)
- speed_to_market: Wie schnell lieferbar? (1-10)
- reusability: Wie oft verkaufbar? (1-10)
- compliance: Rechtlich sauber? (1-10)
- signature_factor: Wie einzigartig für Maurice? (1-10)

Format: {{"payment_willingness": N, "speed_to_market": N, "reusability": N, "compliance": N, "signature_factor": N}}"""

        response = ollama_generate(prompt)

        try:
            # Extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                scores = json.loads(response[start:end])
            else:
                scores = {d: 5 for d in dims}
        except json.JSONDecodeError:
            scores = {d: 5 for d in dims}

        # Calculate weighted score
        total = 0
        for dim, cfg in dims.items():
            val = scores.get(dim, 5)
            total += val * cfg["weight"]

        idea["scores"] = scores
        idea["score"] = round(total, 2)
        idea["scored_at"] = datetime.now().isoformat()
        scored.append(idea)

        status = "AUTO-APPROVE" if total >= config["thresholds"]["auto_approve"] else (
            "APPROVED" if total >= config["thresholds"]["minimum_score"] else "BELOW THRESHOLD"
        )
        print(f"  [{idea['id']}] {idea['title'][:40]:40s} → {total:.1f}/10 ({status})")

    # Save ranked results
    scored.sort(key=lambda x: x.get("score", 0), reverse=True)
    RANKED_FILE.write_text(json.dumps(scored, indent=2, ensure_ascii=False))

    # Also update inbox
    with open(INBOX_FILE, "w") as f:
        for idea in scored:
            f.write(json.dumps(idea, ensure_ascii=False) + "\n")

    print(f"\n  Gespeichert: {RANKED_FILE}")


def show_ranked():
    """Show ranked ideas."""
    if not RANKED_FILE.exists():
        print("  Noch keine Rankings. Führe 'score' aus.")
        return

    ideas = json.loads(RANKED_FILE.read_text())
    print(f"\n  {'='*70}")
    print(f"  {'ID':8s} {'Score':6s} {'Title':45s} {'Status'}")
    print(f"  {'='*70}")

    for idea in ideas:
        score = idea.get("score", 0)
        status = "★★★" if score >= 8 else ("★★" if score >= 6 else "★")
        print(f"  {idea['id']:8s} {score:5.1f}  {idea['title'][:45]:45s} {status}")

    print(f"  {'='*70}")
    print(f"  {len(ideas)} Ideen total")


def design_offer(idea_id: str):
    """Step 3: Design offer for a specific idea."""
    ideas = load_ideas()
    idea = next((i for i in ideas if i["id"] == idea_id), None)

    if not idea:
        print(f"  Idee {idea_id} nicht gefunden.")
        return

    product_dir = RUNS_DIR / idea_id
    product_dir.mkdir(parents=True, exist_ok=True)

    prompt = f"""Erstelle ein konkretes Produktangebot für:
"{idea['title']}"

Kontext: Maurice Pfeifer, Elektrotechnikmeister, 16 Jahre BMA + AI Expertise.
Zielmarkt: DACH-Region, Handwerk, technische Dienstleister, KMU.

Erstelle ein vollständiges Angebot mit:

1. ZIELGRUPPE (1 Satz: "Ich helfe X, Y zu erreichen, ohne Z")
2. VERSPRECHEN (Was bekommt der Käufer konkret?)
3. MODULE (3-5 Inhaltsblöcke)
4. DELIVERABLES (konkrete Dateien/Templates)
5. PREISANKER:
   - Basic (günstiger Einstieg)
   - Pro (Hauptprodukt)
   - Elite (Premium mit Support)
6. WARUM JETZT? (Urgency)
7. EINZIGARTIGKEIT (Warum nur Maurice?)

Format: Markdown."""

    print(f"  Generiere Offer für: {idea['title']}...")
    response = ollama_generate(prompt, model=DEFAULT_MODEL)

    offer_file = product_dir / "offer.md"
    offer_file.write_text(f"# OFFER: {idea['title']}\n\nGenerated: {datetime.now().isoformat()}\n\n{response}")

    print(f"  → Gespeichert: {offer_file}")


def build_marketing(product_id: str):
    """Step 5: Generate marketing content for a product."""
    product_dir = RUNS_DIR / product_id
    offer_file = product_dir / "offer.md"

    if not offer_file.exists():
        print(f"  Kein Offer für {product_id}. Führe 'design {product_id}' zuerst aus.")
        return

    offer_content = offer_file.read_text()
    marketing_dir = product_dir / "marketing"
    marketing_dir.mkdir(exist_ok=True)

    # Generate posts
    prompt = f"""Basierend auf diesem Produktangebot, erstelle Marketing Content:

{offer_content[:2000]}

Erstelle:
1. 10 kurze Social Media Posts (X/Twitter, max 280 Zeichen)
2. 3 Hook-Varianten (Attention Grabber, 1-2 Sätze)
3. 1 Landing Page Copy (Headline + Subheadline + 3 Bullet Points + CTA)
4. 3 Email-Betreffzeilen

Sprache: Deutsch. Ton: Direkt, kompetent, kein Bullshit.
Keine Emojis übertreiben. Authentisch bleiben.

Format: Markdown mit klaren Abschnitten."""

    print(f"  Generiere Marketing für: {product_id}...")
    response = ollama_generate(prompt, model=DEFAULT_MODEL)

    marketing_file = marketing_dir / "content.md"
    marketing_file.write_text(
        f"# MARKETING: {product_id}\n\nGenerated: {datetime.now().isoformat()}\n\n{response}"
    )

    print(f"  → Gespeichert: {marketing_file}")


def show_status():
    """Show pipeline status."""
    ideas = load_ideas()
    scored = [i for i in ideas if i.get("score")]
    approved = [i for i in scored if i.get("score", 0) >= 6.0]
    products = list(PRODUCTS_DIR.iterdir()) if PRODUCTS_DIR.exists() else []
    runs = list(RUNS_DIR.iterdir()) if RUNS_DIR.exists() else []

    print(f"\n  {'='*50}")
    print("  PRODUCT FACTORY STATUS")
    print(f"  {'='*50}")
    print(f"  Ideen total:     {len(ideas)}")
    print(f"  Bewertet:        {len(scored)}")
    print(f"  Approved (≥6.0): {len(approved)}")
    print(f"  In Produktion:   {len([r for r in runs if r.is_dir()])}")
    print(f"  Fertige Produkte:{len(products)}")
    print(f"  {'='*50}")

    if approved:
        print("\n  TOP IDEEN:")
        for i in sorted(approved, key=lambda x: x.get("score", 0), reverse=True)[:5]:
            print(f"    [{i['id']}] {i.get('score', 0):.1f} - {i['title'][:50]}")


# ── MAIN ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Product Factory Pipeline")
    parser.add_argument("command", choices=["add", "score", "rank", "design", "build",
                                            "marketing", "status"],
                       help="Pipeline command")
    parser.add_argument("args", nargs="*", help="Command arguments")
    parser.add_argument("--tags", nargs="*", default=[], help="Tags for new ideas")
    parser.add_argument("--source", default="manual", help="Idea source")
    parsed = parser.parse_args()

    if parsed.command == "add":
        if not parsed.args:
            print("  Usage: product_pipeline.py add 'Idee Titel'")
            return
        add_idea(" ".join(parsed.args), tags=parsed.tags, source=parsed.source)
    elif parsed.command == "score":
        score_ideas()
    elif parsed.command == "rank":
        show_ranked()
    elif parsed.command == "design":
        if not parsed.args:
            print("  Usage: product_pipeline.py design <idea_id>")
            return
        design_offer(parsed.args[0])
    elif parsed.command == "marketing":
        if not parsed.args:
            print("  Usage: product_pipeline.py marketing <product_id>")
            return
        build_marketing(parsed.args[0])
    elif parsed.command == "status":
        show_status()


if __name__ == "__main__":
    main()
