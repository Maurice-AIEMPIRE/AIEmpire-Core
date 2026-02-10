#!/usr/bin/env python3
"""
SALES MACHINE - AI Empire Central Command & Transparency Dashboard
Usage: python sales_machine.py [inventory|machine|blast|status]
"""
import argparse, asyncio, json, os, sys
from datetime import datetime, date
from pathlib import Path
from typing import Tuple

try:
    import aiohttp
except ImportError:
    sys.exit("ERROR: aiohttp required. Install: pip install aiohttp")

# -- Config ---------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "sales"
OLLAMA_URL, OLLAMA_MODEL = "http://localhost:11434", "qwen2.5-coder:7b"
N8N_URL, DAILY_TARGET, W = "http://localhost:5678", 180, 60

SCAN_DIRS = {
    "Gumroad Products": (Path.home() / ".openclaw/workspace/ai-empire/04_OUTPUT/GUMROAD_PRODUCTS", 50),
    "Marketing Assets": (Path.home() / ".openclaw/workspace/ai-empire/04_OUTPUT/MARKETING", 20),
    "Gold Nuggets": (BASE_DIR / "gold-nuggets", 15),
    "N8N Workflows": (BASE_DIR / "n8n-workflows", 75),
    "Scripts": (BASE_DIR / "scripts", 40),
    "X-Lead Machine": (BASE_DIR / "x-lead-machine", 25),
}

PRODUCTS = [
    ("AI Prompt Vault", 27, None, "Gumroad", "draft"),
    ("Docker Automation Guide", 99, None, "Gumroad", "draft"),
    ("Stack-as-a-Service", 99, 999, "Gumroad", "planned"),
    ("BMA + AI Consulting", 2000, None, "Direct", "planned"),
    ("AI Automation Setup", 30, None, "Fiverr", "planned"),
]

TOPICS = [
    "AI agents that run your business 24/7 while you sleep",
    "How a German Elektrotechnikmeister built an AI empire with free local LLMs",
    "The AI Prompt Vault: 500+ battle-tested prompts for EUR 27",
    "Docker automation guide: deploy AI stacks in minutes for EUR 99",
    "Why BMA expertise + AI is a million-euro niche nobody sees",
    "Stack-as-a-Service: your entire AI infrastructure for EUR 99/month",
    "Local LLMs vs Cloud APIs: save 90% on AI costs",
    "From zero to EUR 5400/month with AI automation products",
    "The compound effect: 5-step AI workflow that prints content",
    "How I replaced a 10-person team with AI agents",
]

# -- Helpers ---------------------------------------------------------------
def hline(c="-"): return c * W

def header(t):
    p = W - len(t) - 4; return "=" * (p // 2) + f"  {t}  " + "=" * (p - p // 2)

def scan_dir(path: Path) -> Tuple[int, int]:
    if not path.exists(): return 0, 0
    c, s = 0, 0
    for e in os.scandir(str(path)):
        if e.is_file(): c += 1; s += e.stat().st_size
    return c, s

def fmt_size(b: int) -> str:
    if b < 1024: return f"{b} B"
    return f"{b/1024:.1f} KB" if b < 1048576 else f"{b/1048576:.1f} MB"

def today_s(): return date.today().strftime("%Y%m%d")

def load_j(p: Path):
    if p.exists():
        with open(p) as f: return json.load(f)
    return {}

def save_j(p: Path, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f: json.dump(d, f, indent=2, ensure_ascii=False)

async def ollama_gen(s, prompt: str) -> str:
    try:
        async with s.post(f"{OLLAMA_URL}/api/generate", json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
                          timeout=aiohttp.ClientTimeout(total=120)) as r:
            return (await r.json()).get("response", "").strip() if r.status == 200 else f"[HTTP {r.status}]"
    except Exception as e:
        return f"[Ollama unavailable: {e}]"

async def check_svc(s, url, name) -> Tuple[str, bool]:
    try:
        async with s.get(url, timeout=aiohttp.ClientTimeout(total=5)) as r: return name, r.status < 500
    except Exception: return name, False

def _fallback(plat, topic):
    if plat == "twitter": return f"{topic[:200]}\n\nFull breakdown: [LINK]\n#AI #Automation #AIEmpire"
    if plat == "linkedin":
        return (f"I want to share something that changed how I think about AI.\n\n{topic}\n\n"
                f"After 16 years in fire safety (BMA), I discovered that combining deep domain expertise "
                f"with AI creates opportunities nobody else sees.\n\nDM me if you want to learn how.\n\n#AI #Automation #BMA")
    if plat == "reddit":
        return (f"Hey everyone, wanted to share something I've been working on.\n\n{topic}\n\n"
                f"I've been building AI automation systems using local LLMs (Ollama + qwen2.5) "
                f"and it's been a game-changer.\n\nWhat do you think?")
    return f"[Subject] {topic[:55]}"

# -- Commands --------------------------------------------------------------
def cmd_inventory():
    print("\n" + header("SALES MACHINE - FULL INVENTORY"))
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n" + hline("="))
    tf, ts, tv, rows = 0, 0, 0, []
    for label, (path, vpf) in SCAN_DIRS.items():
        c, sz = scan_dir(path)
        v = c * vpf; tf += c; ts += sz; tv += v
        rows.append((label, c, sz, v, path.exists()))
    print(f"\n{'Category':<22} {'Files':>6} {'Size':>10} {'Est. EUR':>10}")
    print(hline())
    for l, c, sz, v, ex in rows:
        print(f"{l:<22} {c:>6} {fmt_size(sz):>10} {v:>9} EUR{'' if ex else ' [!]'}")
    print(hline())
    print(f"{'TOTAL':<22} {tf:>6} {fmt_size(ts):>10} {tv:>9} EUR")
    print(f"\n{header('PRODUCT CATALOG')}")
    print(f"{'Product':<30} {'Price':>10} {'Platform':<10} {'Status':<10}")
    print(hline())
    for nm, pr, mx, pl, st in PRODUCTS:
        ps = f"{pr}-{mx} EUR" if mx else f"{pr} EUR"
        print(f"{nm:<30} {ps:>10} {pl:<10} {st:<10}")
    mn = sum(p[1]*2 for p in PRODUCTS); mx = sum((p[2] or p[1])*10 for p in PRODUCTS)
    print(f"\n  Monthly (conservative): {mn:,} EUR  |  (optimistic): {mx:,} EUR  |  Daily target: {DAILY_TARGET} EUR")
    pf, bf = DATA_DIR/f"posts_{today_s()}.json", DATA_DIR/f"blast_{today_s()}.json"
    pc = len(load_j(pf)) if pf.exists() else 0
    bc = len(load_j(bf).get("posts", [])) if bf.exists() else 0
    print(f"\n{header('CONTENT PIPELINE TODAY')}")
    print(f"  Machine: {pc}  |  Blast: {bc}  |  Total ready: {pc+bc}")
    if not all(r[4] for r in rows): print("  [!] = Directory not found")
    print()

async def cmd_machine():
    print("\n" + header("SALES MACHINE - RUNNING PIPELINE"))
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    specs = [
        ("linkedin", 3, "Write a professional LinkedIn post about {t}. Long-form (150-200 words), "
         "insightful, personal story angle. CTA at end. 3-5 hashtags at end only."),
        ("twitter", 3, "Write a punchy Twitter/X post about {t}. Max 280 chars. Hook first. "
         "1-2 hashtags. CTA like 'DM me' or 'Link in bio'."),
        ("reddit", 2, "Write a Reddit post about {t}. Value-first, community-style. "
         "Relatable problem, then solution. No hard sell. 100-150 words. End with 'What do you think?'"),
        ("email_subject", 2, "Write one email subject line about {t}. Curiosity-driven, under 60 chars. Just the line."),
    ]
    posts, descs = [], {}
    async with aiohttp.ClientSession() as session:
        print("  [1/4] Checking Ollama...", end=" ", flush=True)
        _, up = await check_svc(session, f"{OLLAMA_URL}/api/tags", "Ollama")
        print("ONLINE" if up else "OFFLINE - fallback mode")
        print("  [2/4] Generating 10 social media posts...")
        ti = 0
        for plat, cnt, tpl in specs:
            for i in range(cnt):
                topic = TOPICS[ti % len(TOPICS)]; ti += 1
                print(f"    -> {plat} #{i+1}: {topic[:50]}...", flush=True)
                content = await ollama_gen(session, tpl.format(t=topic)) if up else _fallback(plat, topic)
                posts.append({"platform": plat, "topic": topic, "content": content,
                              "generated_at": datetime.now().isoformat(), "status": "ready"})
        print("  [3/4] Generating product descriptions...")
        for nm, pr, _, _, _ in PRODUCTS:
            if up:
                descs[nm] = await ollama_gen(session, f"Write a compelling 2-sentence product description for "
                    f"'{nm}' at EUR {pr}. Target: developers and business owners wanting AI automation.")
            else:
                descs[nm] = f"{nm} - Transform your workflow with AI automation. Starting at EUR {pr}."
            print(f"    -> {nm}: done")
    of = DATA_DIR / f"posts_{today_s()}.json"; save_j(of, posts)
    rf = DATA_DIR / f"report_{today_s()}.json"
    save_j(rf, {"date": date.today().isoformat(), "posts_generated": len(posts),
                "platforms": {s[0]: s[1] for s in specs}, "product_descriptions": descs,
                "generated_at": datetime.now().isoformat()})
    print(f"  [4/4] Saved {len(posts)} posts to {of.name}")
    print(f"\n{header('PIPELINE COMPLETE')}")
    print(f"  Posts: {len(posts)}  |  Descriptions: {len(descs)}  |  Files: {of.name}, {rf.name}")
    print(f"  Next: Run 'blast' for 20 more posts\n")

async def cmd_blast():
    print("\n" + header("SALES MACHINE - CONTENT BLAST (20 POSTS)"))
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    seeds = [
        ("twitter", "AI Prompt Vault: 500+ prompts for EUR 27. Stop guessing, start automating. [LINK] #AI #Automation"),
        ("twitter", "I replaced a 10-person team with AI agents on a EUR 500 laptop. Here's how: [LINK] #AIEmpire"),
        ("twitter", "Docker + AI = unstoppable. My EUR 99 guide shows you the exact stack. [LINK] #Docker #AI"),
        ("twitter", "BMA + AI: the niche NOBODY is talking about. EUR 2000/client consulting. DM me."),
        ("twitter", "Local LLMs save me EUR 500/month vs ChatGPT API. Free guide in bio. #Ollama #AI"),
        ("linkedin", "From Elektrotechnikmeister to AI Empire builder - my unconventional path"),
        ("linkedin", "Why I believe local AI models will disrupt the cloud-first narrative"),
        ("linkedin", "The 5-step compound workflow that generates content while I sleep"),
        ("linkedin", "BMA meets AI: How fire safety expertise creates a unique consulting niche"),
        ("linkedin", "Stack-as-a-Service: Why I'm packaging my entire AI infrastructure as a product"),
        ("reddit", "I automated my entire content pipeline with free local LLMs - here's the stack"),
        ("reddit", "Built a consulting business combining 16 years of fire safety with AI automation"),
        ("reddit", "Honest review: running AI agents locally vs cloud - cost breakdown included"),
        ("reddit", "Created a prompt vault with 500+ tested prompts - looking for beta testers"),
        ("reddit", "How I use Docker to deploy AI stacks in under 5 minutes"),
        ("email_subject", "Your AI stack is costing you 10x too much"),
        ("email_subject", "The EUR 27 shortcut to AI mastery"),
        ("email_subject", "I automated everything. Here's the blueprint."),
        ("email_subject", "BMA + AI = EUR 2000/client (and nobody's doing it)"),
        ("email_subject", "Stop paying for cloud AI. Go local. Save 90%."),
    ]
    enhance = {"twitter": "Rewrite this tweet to be more viral, keep under 280 chars. Keep [LINK] and hashtags. Original: {s}",
               "linkedin": "Expand into a compelling LinkedIn post (150-200 words). Add personal story and CTA. Topic: {s}",
               "reddit": "Expand into a genuine Reddit post (100-150 words). Value-first, no hard sell. Topic: {s}",
               "email_subject": "Improve this email subject line, maximize open rate, under 60 chars. Original: {s}"}
    posts = []
    async with aiohttp.ClientSession() as session:
        _, up = await check_svc(session, f"{OLLAMA_URL}/api/tags", "Ollama")
        print(f"  Ollama {'ONLINE - enhancing with AI' if up else 'OFFLINE - using templates'}...\n")
        for idx, (plat, seed) in enumerate(seeds):
            content = await ollama_gen(session, enhance[plat].format(s=seed)) if up else seed
            posts.append({"id": idx+1, "platform": plat, "content": content, "seed": seed,
                          "generated_at": datetime.now().isoformat(), "status": "ready_to_post"})
            print(f"  [{plat.upper():>14} #{idx+1:02d}]\n  {hline('-')}")
            for ln in content.split("\n"): print(f"  {ln}")
            print()
    of = DATA_DIR / f"blast_{today_s()}.json"
    save_j(of, {"date": date.today().isoformat(), "count": len(posts), "posts": posts})
    print(header("BLAST COMPLETE"))
    ct = {}
    for p in posts: ct[p["platform"]] = ct.get(p["platform"], 0) + 1
    print(f"  Total: {len(posts)}  |  " + "  ".join(f"{k}: {v}" for k, v in sorted(ct.items())))
    print(f"  Saved: {of.name}\n  Copy-paste ready. Edit and post!\n")

async def cmd_status():
    print("\n" + header("SALES MACHINE - LIVE STATUS"))
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" + hline("="))
    async with aiohttp.ClientSession() as session:
        checks = await asyncio.gather(
            check_svc(session, f"{OLLAMA_URL}/api/tags", "Ollama"), check_svc(session, N8N_URL, "n8n"))
    print(f"\n  {'Service':<20} {'Status':>10}\n  {hline('-')}")
    for nm, up in checks: print(f"  {nm:<20} {'ONLINE' if up else 'OFFLINE':>10}")
    tr = load_j(BASE_DIR / "data" / "revenue" / "tracking.json")
    tk, tr_today, tr_all = date.today().isoformat(), 0.0, 0.0
    for sale in tr.get("sales", []):
        tr_all += sale.get("amount", 0)
        if sale.get("date", "") == tk: tr_today += sale.get("amount", 0)
    pct = tr_today / DAILY_TARGET * 100 if DAILY_TARGET else 0
    bf = int(min(pct, 100) / 5); bar = "#" * bf + "." * (20 - bf)
    print(f"\n  REVENUE TODAY\n  {hline('-')}")
    print(f"  Target: EUR {DAILY_TARGET}  |  Actual: EUR {tr_today:.2f}  |  [{bar}] {pct:.0f}%  |  All-time: EUR {tr_all:.2f}")
    pf, blf = DATA_DIR/f"posts_{today_s()}.json", DATA_DIR/f"blast_{today_s()}.json"
    pc = len(load_j(pf)) if pf.exists() else 0
    bc = len(load_j(blf).get("posts", [])) if blf.exists() else 0
    print(f"\n  CONTENT PIPELINE\n  {hline('-')}")
    print(f"  Machine: {pc}  |  Blast: {bc}  |  Total: {pc+bc}")
    if pc == 0 and bc == 0: stage = "IDLE - Run 'machine' or 'blast'"
    elif pc > 0 and bc == 0: stage = "GENERATING - Run 'blast' for more"
    else: stage = "LOADED - Posts ready, time to publish!"
    print(f"\n  STAGE: {stage}")
    print(f"\n  NEXT ACTIONS\n  {hline('-')}")
    if pc == 0: print("  1. python sales_machine.py machine")
    if bc == 0: print("  2. python sales_machine.py blast")
    if tr_today == 0: print("  3. Publish Gumroad products (AI Prompt Vault, Docker Guide)")
    print("  4. Post content to X/LinkedIn/Reddit")
    print("  5. Track: python revenue_pipeline.py track --add <amount> <source>\n")

# -- Main -----------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description="Sales Machine - AI Empire Central Command",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="  inventory  Full asset inventory\n  machine    Run sales pipeline\n"
               "  blast      Generate 20 posts\n  status     Live system status")
    p.add_argument("command", choices=["inventory", "machine", "blast", "status"])
    a = p.parse_args()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    {"inventory": lambda: cmd_inventory(), "machine": lambda: asyncio.run(cmd_machine()),
     "blast": lambda: asyncio.run(cmd_blast()), "status": lambda: asyncio.run(cmd_status())}[a.command]()

if __name__ == "__main__":
    main()
