#!/usr/bin/env python3
"""
GELDMASCHINE - Maximum Revenue Automation
==========================================
Verbindet: Ollama + n8n Cloud + Gumroad + Social Media + Lead Gen
Ziel: EUR 180/Tag = EUR 5,400/Monat = EUR 64,800/Jahr

Usage:
  python geldmaschine.py run          # Full pipeline: generate + queue + report
  python geldmaschine.py status       # Live status aller Systeme
  python geldmaschine.py webhook      # Test n8n Cloud webhook
  python geldmaschine.py posts        # Zeige alle generierten Posts
  python geldmaschine.py report       # Tagesreport mit Revenue
  python geldmaschine.py nonstop      # Continuous mode (alle 60 min)
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime, date
from pathlib import Path

# === CONFIG ===
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "geldmaschine"
POSTS_DIR = DATA_DIR / "posts"
REPORTS_DIR = DATA_DIR / "reports"
REVENUE_FILE = DATA_DIR / "revenue.json"

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5-coder:7b"

N8N_CLOUD_BASE = "https://ai1337empire.app.n8n.cloud"
N8N_WEBHOOK_PATH = os.getenv("N8N_WEBHOOK_PATH", "webhook/content-generate3a43a000-384d-46ca-93ae-b88ef134816d")

DAILY_TARGET = 180  # EUR

PRODUCTS = [
    {"name": "AI Prompt Vault", "price": 27, "platform": "Gumroad", "link_placeholder": "[GUMROAD_LINK_1]"},
    {"name": "Docker Mastery Guide", "price": 99, "platform": "Gumroad", "link_placeholder": "[GUMROAD_LINK_2]"},
    {"name": "AI Stack-as-Service", "price": 99, "platform": "Gumroad", "link_placeholder": "[GUMROAD_LINK_3]",
     "tiers": "STARTER 99 | PRO 299 | ENTERPRISE 999"},
    {"name": "BMA + AI Consulting", "price": 2000, "platform": "Direct", "link_placeholder": "[CALENDAR_LINK]"},
    {"name": "AI Automation Setup", "price": 30, "platform": "Fiverr", "link_placeholder": "[FIVERR_LINK]"},
]

POST_TEMPLATES = {
    "twitter": [
        "I built {product} and it saves 10+ hours/week.\n\nHere's what's inside:\n- {feature1}\n- {feature2}\n- {feature3}\n\nGet it for EUR {price}: {link}",
        "Stop wasting time on {pain_point}.\n\n{product} does it in seconds.\n\nEUR {price} → lifetime access.\n\n{link}",
        "What if AI could {benefit}?\n\nThat's exactly what {product} does.\n\n127 tested prompts. Zero fluff.\n\n{link}",
    ],
    "linkedin": [
        "After 16 years as an Elektrotechnikmeister, I built something I wish existed when I started:\n\n{product}\n\n{description}\n\nEarly access: EUR {price}\n\n{link}",
        "The gap between AI hype and AI results?\n\nPrompts.\n\nI packaged 127 that actually work into {product}.\n\nNo fluff. No theory. Just results.\n\nLink in comments.",
    ],
    "reddit": [
        "[Resource] {product} - {description}\n\nI've been working with AI for {years} years and compiled the prompts that consistently deliver results.\n\nWhat's inside:\n- {feature1}\n- {feature2}\n- {feature3}\n\nFeedback welcome. Link: {link}",
    ],
}

# === INIT ===
for d in [DATA_DIR, POSTS_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def load_revenue():
    if REVENUE_FILE.exists():
        return json.loads(REVENUE_FILE.read_text())
    return {"sales": [], "daily": {}}


def save_revenue(data):
    REVENUE_FILE.write_text(json.dumps(data, indent=2, default=str))


async def check_ollama():
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{OLLAMA_URL}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as r:
                if r.status == 200:
                    data = await r.json()
                    models = [m["name"] for m in data.get("models", [])]
                    return True, models
    except Exception:
        pass
    return False, []


async def check_n8n():
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{N8N_CLOUD_BASE}", timeout=aiohttp.ClientTimeout(total=10)) as r:
                return r.status in (200, 301, 302, 404)
    except Exception:
        pass
    return False


async def generate_via_ollama(prompt, max_tokens=500):
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": "Du bist ein Social Media Marketing Experte. Schreibe kurze, knackige Posts die zum Kauf motivieren. Nutze Emojis sparsam. Schreibe auf Englisch."},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{OLLAMA_URL}/api/chat", json=payload,
                              timeout=aiohttp.ClientTimeout(total=120)) as r:
                if r.status == 200:
                    data = await r.json()
                    return data["message"]["content"]
    except Exception as e:
        return f"[OLLAMA ERROR: {e}]"
    return "[NO RESPONSE]"


async def send_to_n8n(data):
    url = f"{N8N_CLOUD_BASE}/{N8N_WEBHOOK_PATH}"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=data, timeout=aiohttp.ClientTimeout(total=15)) as r:
                return r.status, await r.text()
    except Exception as e:
        return 0, str(e)


async def run_pipeline():
    print("=" * 60)
    print("  GELDMASCHINE - MAXIMUM REVENUE PIPELINE")
    print("=" * 60)
    today = date.today().isoformat()
    results = {"date": today, "posts": [], "webhook_results": [], "errors": []}

    # Phase 1: Check systems
    print("\n  Phase 1: System Check")
    ollama_ok, models = await check_ollama()
    n8n_ok = await check_n8n()
    print(f"    Ollama: {'ONLINE' if ollama_ok else 'OFFLINE'} {models if ollama_ok else ''}")
    print(f"    n8n Cloud: {'REACHABLE' if n8n_ok else 'OFFLINE'}")

    # Phase 2: Generate posts for each product
    print(f"\n  Phase 2: Generating posts for {len(PRODUCTS)} products")
    all_posts = []

    for prod in PRODUCTS:
        for platform in ["twitter", "linkedin"]:
            prompt = (
                f"Write a {platform} post to sell '{prod['name']}' for EUR {prod['price']}.\n"
                f"Product: {prod['name']}\n"
                f"Price: EUR {prod['price']}\n"
                f"Platform: {prod['platform']}\n"
                f"Include a call-to-action. Use placeholder {prod['link_placeholder']} for the link.\n"
                f"Keep it under {'280' if platform == 'twitter' else '600'} characters.\n"
                f"Write ONLY the post text, nothing else."
            )
            if ollama_ok:
                text = await generate_via_ollama(prompt)
            else:
                tmpl = POST_TEMPLATES.get(platform, POST_TEMPLATES["twitter"])[0]
                text = tmpl.format(
                    product=prod["name"], price=prod["price"],
                    link=prod["link_placeholder"],
                    feature1="Tested prompts", feature2="Copy-paste ready",
                    feature3="Lifetime access", pain_point="manual work",
                    benefit="automate everything", description="AI toolkit",
                    years=16,
                )

            post = {
                "product": prod["name"],
                "platform": platform,
                "text": text.strip(),
                "price": prod["price"],
                "link": prod["link_placeholder"],
                "generated": datetime.now().isoformat(),
            }
            all_posts.append(post)
            print(f"    [{prod['name'][:20]:20s}] {platform:10s} -> {len(text)} chars")

    # Phase 3: Save posts
    posts_file = POSTS_DIR / f"posts_{today}.json"
    existing = json.loads(posts_file.read_text()) if posts_file.exists() else []
    existing.extend(all_posts)
    posts_file.write_text(json.dumps(existing, indent=2, default=str))
    print(f"\n  Phase 3: Saved {len(all_posts)} posts ({len(existing)} total today)")
    results["posts"] = all_posts

    # Phase 4: Push to n8n Cloud
    print(f"\n  Phase 4: Pushing to n8n Cloud")
    if n8n_ok:
        for post in all_posts[:3]:  # Send first 3 as test
            status, resp = await send_to_n8n({
                "action": "queue_post",
                "platform": post["platform"],
                "content": post["text"],
                "product": post["product"],
            })
            results["webhook_results"].append({"status": status, "response": resp[:200]})
            state = "OK" if status == 200 else f"CODE {status}"
            print(f"    -> {post['product'][:20]:20s}: {state}")
    else:
        print("    n8n Cloud nicht erreichbar - Posts lokal gespeichert")

    # Phase 5: Daily Report
    print(f"\n  Phase 5: Tagesreport")
    revenue = load_revenue()
    today_rev = sum(s["amount"] for s in revenue.get("sales", []) if s.get("date") == today)
    pct = min(100, int(today_rev / DAILY_TARGET * 100)) if DAILY_TARGET > 0 else 0
    bar = "#" * (pct // 5) + "-" * (20 - pct // 5)
    print(f"    Revenue:   EUR {today_rev:>8.2f} / {DAILY_TARGET} Ziel")
    print(f"    Progress:  [{bar}] {pct}%")
    print(f"    Posts gen:  {len(existing)} heute")
    print(f"    Produkte:  {len(PRODUCTS)} ({sum(1 for p in PRODUCTS if p['platform'] == 'Gumroad')} Gumroad)")

    # Save report
    report = {
        "date": today, "revenue": today_rev, "target": DAILY_TARGET,
        "posts_generated": len(existing), "products": len(PRODUCTS),
        "systems": {"ollama": ollama_ok, "n8n": n8n_ok},
    }
    report_file = REPORTS_DIR / f"report_{today}.json"
    report_file.write_text(json.dumps(report, indent=2))

    print(f"\n  DONE. {len(all_posts)} neue Posts. Report: {report_file.name}")
    return results


async def show_status():
    print("=" * 60)
    print("  GELDMASCHINE - LIVE STATUS")
    print("=" * 60)

    ollama_ok, models = await check_ollama()
    n8n_ok = await check_n8n()
    revenue = load_revenue()
    today = date.today().isoformat()
    today_rev = sum(s["amount"] for s in revenue.get("sales", []) if s.get("date") == today)
    pct = min(100, int(today_rev / DAILY_TARGET * 100)) if DAILY_TARGET > 0 else 0
    bar = "#" * (pct // 5) + "-" * (20 - pct // 5)

    posts_file = POSTS_DIR / f"posts_{today}.json"
    post_count = len(json.loads(posts_file.read_text())) if posts_file.exists() else 0

    print(f"\n  SYSTEME:")
    print(f"    Ollama:     {'ONLINE' if ollama_ok else 'OFFLINE':10s} Modelle: {', '.join(models) if models else 'none'}")
    print(f"    n8n Cloud:  {'ONLINE' if n8n_ok else 'OFFLINE':10s} {N8N_CLOUD_BASE}")

    print(f"\n  REVENUE (Heute {today}):")
    print(f"    EUR {today_rev:>8.2f} / {DAILY_TARGET} Ziel  [{bar}] {pct}%")
    print(f"    Sales: {len([s for s in revenue.get('sales', []) if s.get('date') == today])}")

    print(f"\n  CONTENT:")
    print(f"    Posts heute: {post_count}")
    print(f"    Produkte:   {len(PRODUCTS)}")

    print(f"\n  PRODUKTE:")
    for p in PRODUCTS:
        print(f"    EUR {p['price']:>6} | {p['name']:30s} | {p['platform']}")

    total_pot = sum(p["price"] for p in PRODUCTS)
    print(f"\n  Potential pro Verkauf aller Produkte: EUR {total_pot}")
    print(f"  Ziel: {DAILY_TARGET} EUR/Tag = {DAILY_TARGET * 30} EUR/Monat")

    # Next actions
    print(f"\n  NAECHSTE AKTIONEN:")
    if not ollama_ok:
        print("    [!] Ollama starten: ollama serve")
    if today_rev == 0:
        print("    [!] Erster Verkauf fehlt - Posts absetzen!")
    if post_count == 0:
        print("    [!] Keine Posts heute - python geldmaschine.py run")
    print("    [>] Revenue tracken: python geldmaschine.py report --add 27 'Prompt Vault Sale'")


async def show_posts():
    today = date.today().isoformat()
    posts_file = POSTS_DIR / f"posts_{today}.json"
    if not posts_file.exists():
        print("Keine Posts heute. Starte mit: python geldmaschine.py run")
        return

    posts = json.loads(posts_file.read_text())
    print(f"{'=' * 60}")
    print(f"  {len(posts)} POSTS - READY TO COPY-PASTE")
    print(f"{'=' * 60}")
    for i, p in enumerate(posts, 1):
        print(f"\n{'─' * 60}")
        print(f"  #{i} | {p['platform'].upper()} | {p['product']} | EUR {p['price']}")
        print(f"{'─' * 60}")
        print(p["text"])


async def show_report():
    # Check for --add flag
    if "--add" in sys.argv:
        idx = sys.argv.index("--add")
        if idx + 2 < len(sys.argv):
            amount = float(sys.argv[idx + 1])
            desc = sys.argv[idx + 2]
            revenue = load_revenue()
            revenue["sales"].append({
                "date": date.today().isoformat(),
                "amount": amount,
                "description": desc,
                "time": datetime.now().isoformat(),
            })
            save_revenue(revenue)
            print(f"  +EUR {amount:.2f} | {desc}")

    revenue = load_revenue()
    today = date.today().isoformat()
    today_sales = [s for s in revenue.get("sales", []) if s.get("date") == today]
    today_rev = sum(s["amount"] for s in today_sales)
    total_rev = sum(s["amount"] for s in revenue.get("sales", []))
    pct = min(100, int(today_rev / DAILY_TARGET * 100)) if DAILY_TARGET > 0 else 0
    bar = "#" * (pct // 5) + "-" * (20 - pct // 5)

    print(f"{'=' * 60}")
    print(f"  REVENUE REPORT - {today}")
    print(f"{'=' * 60}")
    print(f"\n  Heute:     EUR {today_rev:>10.2f} / {DAILY_TARGET} [{bar}] {pct}%")
    print(f"  Gesamt:    EUR {total_rev:>10.2f}")
    print(f"  Sales:     {len(today_sales)} heute | {len(revenue.get('sales', []))} gesamt")

    if today_sales:
        print(f"\n  Heutige Sales:")
        for s in today_sales:
            print(f"    EUR {s['amount']:>8.2f} | {s['description']} | {s.get('time', '')[:16]}")

    # 7-day overview
    from collections import defaultdict
    daily = defaultdict(float)
    for s in revenue.get("sales", []):
        daily[s.get("date", "unknown")] += s["amount"]
    if daily:
        print(f"\n  Letzte Tage:")
        for d in sorted(daily.keys())[-7:]:
            dpct = min(100, int(daily[d] / DAILY_TARGET * 100))
            dbar = "#" * (dpct // 5) + "-" * (20 - dpct // 5)
            print(f"    {d}: EUR {daily[d]:>8.2f} [{dbar}] {dpct}%")


async def test_webhook():
    print("  Testing n8n Cloud Webhook...")
    status, resp = await send_to_n8n({
        "action": "test",
        "timestamp": datetime.now().isoformat(),
        "source": "geldmaschine",
    })
    print(f"  Status: {status}")
    print(f"  Response: {resp[:500]}")
    if status == 404:
        print("\n  HINWEIS: Webhook ist im Test-Modus.")
        print("  Gehe zu n8n Cloud und klicke 'Execute Workflow',")
        print("  dann versuche es nochmal.")


async def nonstop():
    print("  NONSTOP MODE - Generiert alle 60 Minuten")
    print("  Druecke Ctrl+C zum Stoppen")
    cycle = 0
    while True:
        cycle += 1
        print(f"\n{'=' * 60}")
        print(f"  ZYKLUS #{cycle} - {datetime.now().strftime('%H:%M:%S')}")
        try:
            await run_pipeline()
        except Exception as e:
            print(f"  ERROR: {e}")
        print(f"\n  Naechster Zyklus in 60 Minuten...")
        await asyncio.sleep(3600)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    if cmd == "run":
        asyncio.run(run_pipeline())
    elif cmd == "status":
        asyncio.run(show_status())
    elif cmd == "webhook":
        asyncio.run(test_webhook())
    elif cmd == "posts":
        asyncio.run(show_posts())
    elif cmd == "report":
        asyncio.run(show_report())
    elif cmd == "nonstop":
        asyncio.run(nonstop())
    else:
        print(f"  Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
