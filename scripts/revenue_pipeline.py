#!/usr/bin/env python3
"""
REVENUE PIPELINE - AI Empire Unified Revenue Engine
Usage: python revenue_pipeline.py [health|dashboard|launch|track]
  track --add 49.00 "Gumroad - AI Guide"  |  track --views 500 --clicks 30
"""
import argparse, asyncio, json, sys
from datetime import datetime, date
from pathlib import Path
from typing import Optional

try:
    import aiohttp
except ImportError:
    sys.exit("ERROR: aiohttp required. Install: pip install aiohttp")

# ── Config ────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "revenue"
TRACKING_FILE, QUEUE_FILE = DATA_DIR / "tracking.json", DATA_DIR / "post_queue.json"
OLLAMA_URL, OLLAMA_MODEL = "http://localhost:11434", "qwen2.5-coder:7b"
N8N_URL = "http://localhost:5678"
DAILY_TARGET = 180  # EUR/day = 5400/month

PRODUCTS = [
    {"name": "AI Prompt Engineering Pack", "price": 27,   "platform": "Gumroad", "status": "draft"},
    {"name": "BMA + AI Automation Guide",  "price": 49,   "platform": "Gumroad", "status": "draft"},
    {"name": "OpenClaw Starter Kit",       "price": 97,   "platform": "Gumroad", "status": "draft"},
    {"name": "AI Empire Blueprint",        "price": 149,  "platform": "Gumroad", "status": "draft"},
    {"name": "AI Automation Setup",        "price": 30,   "platform": "Fiverr",  "status": "planned"},
    {"name": "BMA + AI Consulting",        "price": 2000, "platform": "Direct",  "status": "planned"},
]
POST_TOPICS = [
    "AI agents running 24/7 while you sleep",
    "How I automated my entire business with Ollama",
    "BMA meets AI: a unique niche nobody sees",
    "From Elektrotechnikmeister to AI Empire builder",
    "Why local LLMs beat cloud APIs for 90% of tasks",
]

def load_json(p: Path, default=None):
    return json.loads(p.read_text()) if p.exists() else (default if default is not None else {})

def save_json(p: Path, data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, default=str))

def progress_bar(pct, width=20):
    n = int(min(pct, 100) / (100 / width))
    return "#" * n + "-" * (width - n)

# ── 1. Health Check ───────────────────────────────────────
async def cmd_health():
    print("\n  SYSTEM HEALTH CHECK\n  " + "=" * 50)
    async with aiohttp.ClientSession() as s:
        for name, url in [("Ollama", f"{OLLAMA_URL}/api/tags"), ("n8n", f"{N8N_URL}/healthz")]:
            try:
                async with s.get(url, timeout=aiohttp.ClientTimeout(total=3)) as r:
                    print(f"  [OK] {name:12s} {url}")
                    if name == "Ollama" and r.status == 200:
                        data = await r.json()
                        models = [m["name"] for m in data.get("models", [])]
                        has = any(OLLAMA_MODEL in m for m in models)
                        print(f"  [{'OK' if has else 'XX'}] Model        {OLLAMA_MODEL} {'loaded' if has else 'NOT FOUND'}")
                        if models:
                            print(f"       Available:   {', '.join(models[:5])}")
            except Exception as e:
                print(f"  [XX] {name:12s} {url}  ({str(e)[:50]})")
    print()

# ── 2. Dashboard ──────────────────────────────────────────
def cmd_dashboard():
    print("\n  REVENUE PIPELINE DASHBOARD\n  " + "=" * 50)
    # Products
    print("\n  PRODUCTS:")
    tags = {"draft": "DRAFT", "live": " LIVE", "planned": " PLAN"}
    for p in PRODUCTS:
        print(f"    [{tags.get(p['status'],'  ?  ')}] {p['name']:35s} EUR {p['price']:>6}  ({p['platform']})")
    print(f"    {'Total potential per sale':41s} EUR {sum(p['price'] for p in PRODUCTS):>6}")
    # Assets
    xl = BASE_DIR / "x-lead-machine"
    n8 = BASE_DIR / "n8n-workflows"
    queue = load_json(QUEUE_FILE, [])
    print(f"\n  MARKETING ASSETS:")
    print(f"    X Lead Machine scripts:  {len(list(xl.glob('*.py'))) if xl.exists() else 0}")
    print(f"    n8n workflows:           {len(list(n8.glob('*.json'))) if n8.exists() else 0}")
    print(f"    Posts in queue:          {len(queue)}")
    # Revenue
    tracking = load_json(TRACKING_FILE, {"days": {}})
    tk = date.today().isoformat()
    td = tracking.get("days", {}).get(tk, {})
    rev, sales = td.get("revenue", 0.0), td.get("sales", 0)
    pct = rev / DAILY_TARGET * 100 if DAILY_TARGET else 0
    print(f"\n  TODAY ({tk}):")
    print(f"    Revenue:  EUR {rev:>8.2f} / {DAILY_TARGET} target")
    print(f"    Progress: [{progress_bar(pct)}] {pct:.0f}%")
    print(f"    Sales:    {sales}")
    tr = sum(d.get("revenue", 0) for d in tracking.get("days", {}).values())
    ts = sum(d.get("sales", 0) for d in tracking.get("days", {}).values())
    print(f"\n  ALL TIME:   EUR {tr:.2f} | {ts} sales")
    # Funnel
    f = td.get("funnel", {})
    v, c, sf = f.get("views", 0), f.get("clicks", 0), f.get("sales", sales)
    print(f"\n  FUNNEL:     {v} views -> {c} clicks ({c/v*100:.1f}% CTR)" if v else "\n  FUNNEL:     No data")
    if c:
        print(f"              {c} clicks -> {sf} sales ({sf/c*100:.1f}% CVR)")
    print()

# ── 3. Launch Sequence ────────────────────────────────────
async def ollama_gen(prompt: str, session: aiohttp.ClientSession) -> str:
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
               "options": {"temperature": 0.8, "num_predict": 200}}
    try:
        async with session.post(f"{OLLAMA_URL}/api/generate", json=payload,
                                timeout=aiohttp.ClientTimeout(total=60)) as r:
            return (await r.json()).get("response", "").strip() if r.status == 200 else f"[HTTP {r.status}]"
    except Exception as e:
        return f"[Error: {e}]"

async def cmd_launch():
    print("\n  LAUNCH SEQUENCE\n  " + "=" * 50)
    # Step 1
    print("\n  Step 1/4: Verify products")
    live = [p for p in PRODUCTS if p["status"] == "live"]
    draft = [p for p in PRODUCTS if p["status"] == "draft"]
    print(f"    Live: {len(live)} | Draft: {len(draft)}")
    if not live:
        print("    WARNING: No live products. Publish on Gumroad first.")
    for p in live:
        print(f"    [LIVE] {p['name']} - EUR {p['price']}")
    # Step 2
    print("\n  Step 2/4: Generate social posts via Ollama")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{OLLAMA_URL}/api/tags", timeout=aiohttp.ClientTimeout(total=3)):
                pass
        except Exception:
            print(f"    Ollama not running. Start: ollama serve && ollama pull {OLLAMA_MODEL}")
            return
        print(f"    Generating {len(POST_TOPICS)} posts with {OLLAMA_MODEL}...")
        posts = []
        for i, topic in enumerate(POST_TOPICS):
            prompt = (f"Write a viral X/Twitter post (max 280 chars) about: {topic}\n"
                      f"Style: Confident AI builder. Hook + insight + CTA. Output ONLY the post.")
            print(f"    [{i+1}/{len(POST_TOPICS)}] {topic[:45]}...", end=" ", flush=True)
            text = await ollama_gen(prompt, session)
            if text and not text.startswith("["):
                posts.append({"topic": topic, "text": text[:280],
                              "generated": datetime.now().isoformat(), "status": "queued"})
                print("OK")
            else:
                print(f"FAIL ({text[:35]})")
    # Step 3
    print(f"\n  Step 3/4: Queue posts")
    if posts:
        q = load_json(QUEUE_FILE, [])
        q.extend(posts)
        save_json(QUEUE_FILE, q)
        print(f"    Added {len(posts)} posts (total queue: {len(q)})")
    else:
        print("    No posts generated.")
    # Step 4
    print(f"\n  Step 4/4: Lead monitoring")
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{N8N_URL}/healthz", timeout=aiohttp.ClientTimeout(total=3)):
                print("    n8n running. Lead workflows available.")
                nd = BASE_DIR / "n8n-workflows"
                if nd.exists():
                    for wf in sorted(nd.glob("*.json")):
                        print(f"    - {wf.stem}")
    except Exception:
        print("    n8n not running. Start: docker run -d -p 5678:5678 n8nio/n8n")
    print("\n  Launch sequence complete.\n")

# ── 4. Revenue Tracking ──────────────────────────────────
def cmd_track(amount: Optional[float] = None, source: Optional[str] = None,
              views: Optional[int] = None, clicks: Optional[int] = None):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tracking = load_json(TRACKING_FILE, {"days": {}, "created": datetime.now().isoformat()})
    tk = date.today().isoformat()
    if tk not in tracking["days"]:
        tracking["days"][tk] = {"revenue": 0.0, "sales": 0, "entries": [],
                                "funnel": {"views": 0, "clicks": 0, "sales": 0}}
    day = tracking["days"][tk]
    changed = False
    if amount is not None and amount > 0:
        day["entries"].append({"amount": amount, "source": source or "unknown",
                               "timestamp": datetime.now().isoformat()})
        day["revenue"] = round(day["revenue"] + amount, 2)
        day["sales"] += 1
        day["funnel"]["sales"] = day["sales"]
        print(f"\n  Added: EUR {amount:.2f} from {source or 'unknown'}")
        changed = True
    if views is not None:
        day["funnel"]["views"] += views; print(f"  Added {views} views"); changed = True
    if clicks is not None:
        day["funnel"]["clicks"] += clicks; print(f"  Added {clicks} clicks"); changed = True
    if changed:
        tracking["updated"] = datetime.now().isoformat()
        save_json(TRACKING_FILE, tracking)
    # Display
    rev, pct = day["revenue"], day["revenue"] / DAILY_TARGET * 100 if DAILY_TARGET else 0
    print(f"\n  REVENUE TRACKING - {tk}\n  " + "=" * 50)
    print(f"  Target:   EUR {DAILY_TARGET}/day (EUR {DAILY_TARGET * 30}/month)")
    print(f"  Today:    EUR {rev:.2f}")
    print(f"  Progress: [{progress_bar(pct)}] {pct:.0f}%")
    print(f"  Sales:    {day['sales']}")
    if day["entries"]:
        print(f"\n  Entries:")
        for e in day["entries"]:
            print(f"    {e['timestamp'][11:16]}  EUR {e['amount']:>8.2f}  {e['source']}")
    all_days = sorted(tracking.get("days", {}).keys(), reverse=True)[:7]
    if len(all_days) > 1:
        print(f"\n  Last 7 days:")
        for dk in all_days:
            dd = tracking["days"][dk]
            dr, ds = dd.get("revenue", 0), dd.get("sales", 0)
            dp = dr / DAILY_TARGET * 100 if DAILY_TARGET else 0
            print(f"    {dk}  EUR {dr:>8.2f}  {ds} sales  [{progress_bar(dp, 10)}] {dp:.0f}%")
    tr = sum(d.get("revenue", 0) for d in tracking.get("days", {}).values())
    print(f"\n  All time:  EUR {tr:.2f} | {sum(d.get('sales', 0) for d in tracking['days'].values())} sales\n")

# ── CLI ───────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="AI Empire - Revenue Pipeline",
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command")
    sub.add_parser("health", help="Check Ollama + n8n")
    sub.add_parser("dashboard", help="Revenue dashboard")
    sub.add_parser("launch", help="Guided launch sequence")
    t = sub.add_parser("track", help="Revenue tracking")
    t.add_argument("--add", nargs=2, metavar=("EUR", "SOURCE"), help="Add revenue")
    t.add_argument("--views", type=int, help="Add views")
    t.add_argument("--clicks", type=int, help="Add clicks")
    args = p.parse_args()
    if not args.command:
        p.print_help(); return
    if args.command == "health":    asyncio.run(cmd_health())
    elif args.command == "dashboard": cmd_dashboard()
    elif args.command == "launch":  asyncio.run(cmd_launch())
    elif args.command == "track":
        amt, src = (float(args.add[0]), args.add[1]) if args.add else (None, None)
        cmd_track(amount=amt, source=src, views=args.views, clicks=args.clicks)

if __name__ == "__main__":
    main()
