#!/usr/bin/env python3
"""
EMPIRE ENGINE — The Unified Revenue Machine
=============================================
One program to rule them all. Combines the best of:
  - Workflow System (5-Step Compound Loop)
  - Brain System (7 specialized AI brains)
  - X Lead Machine (content + virality)
  - Kimi Swarm (500K agents for scale)
  - Atomic Reactor (task execution)
  - CRM (lead management)
  - Antigravity (code quality + self-repair)
  - Knowledge Store (persistent learning)
  - Planning Mode (strategic execution)

Revenue Channels (automated):
  1. Gumroad digital products (BMA Checklisten, AI Kits)
  2. Fiverr/Upwork AI services
  3. BMA + AI consulting (UNIQUE NICHE)
  4. X/Twitter → Lead Machine → CRM → Close
  5. Faceless YouTube/TikTok content
  6. Premium Community (Discord/Telegram)

Architecture:
  ┌─────────────────────────────────────────────┐
  │              EMPIRE ENGINE                     │
  │                                                │
  │  ┌─────────┐  ┌──────────┐  ┌──────────────┐ │
  │  │ SCANNER │→│ PRODUCER │→│ DISTRIBUTOR  │ │
  │  │ (News)  │  │ (Content)│  │ (Multi-Plat) │ │
  │  └─────────┘  └──────────┘  └──────────────┘ │
  │       │             │              │           │
  │       ▼             ▼              ▼           │
  │  ┌─────────┐  ┌──────────┐  ┌──────────────┐ │
  │  │KNOWLEDGE│  │   CRM    │  │  MONETIZER   │ │
  │  │ STORE   │  │ (Leads)  │  │  (Revenue)   │ │
  │  └─────────┘  └──────────┘  └──────────────┘ │
  │                                                │
  │  Models: Ollama (95%) → Kimi (4%) → Claude (1%)│
  └─────────────────────────────────────────────┘

Usage:
  python3 empire_engine.py                    # Status dashboard
  python3 empire_engine.py scan               # Scan news + trends
  python3 empire_engine.py produce            # Generate content
  python3 empire_engine.py distribute         # Post to all platforms
  python3 empire_engine.py leads              # Process leads
  python3 empire_engine.py revenue            # Revenue report
  python3 empire_engine.py auto               # Full autonomous cycle
  python3 empire_engine.py godmode [task]     # 4-Role AI Router (Fixer/Coder/QA)
  python3 empire_engine.py mirror             # Mirror System (Mac <-> Gemini)
  python3 empire_engine.py repair             # Auto-Repair (self-healing)
  python3 empire_engine.py setup              # First-time setup wizard

Author: Maurice Pfeifer — Elektrotechnikmeister + AI Architect
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# ─── Setup paths ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# ─── Safe imports (graceful degradation) ──────────────────────────────────────
def safe_import(module_name):
    """Import module, return None if not available."""
    try:
        return __import__(module_name, fromlist=[""])
    except ImportError:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

CONFIG = {
    "version": "2.0.0",
    "name": "Empire Engine",
    "owner": "Maurice Pfeifer",
    "niche": "BMA (Brandmeldeanlagen) + AI Automation",

    # Revenue targets
    "target_monthly": 100_000,  # EUR
    "target_yearly": 1_000_000,

    # Content production
    "content": {
        "personas": [
            {"name": "BMA-Meister", "focus": "fire safety + tech", "platforms": ["x", "linkedin", "youtube"]},
            {"name": "AI Agent King", "focus": "AI agents + automation", "platforms": ["x", "tiktok", "youtube"]},
            {"name": "Money Machine", "focus": "passive income + AI biz", "platforms": ["x", "tiktok", "instagram"]},
        ],
        "daily_posts_per_persona": 3,
        "video_formats": ["youtube_short", "tiktok", "instagram_reel"],
        "languages": ["de", "en"],
    },

    # Revenue channels
    "channels": {
        "gumroad": {
            "products": [
                {"name": "BMA-Checklisten-Pack", "price": 27, "url": ""},
                {"name": "AI Agent Starter Kit", "price": 49, "url": ""},
                {"name": "BMA + AI Masterclass", "price": 149, "url": ""},
                {"name": "Agent Empire Blueprint", "price": 97, "url": ""},
                {"name": "Premium Prompt Library", "price": 37, "url": ""},
            ],
        },
        "fiverr": {
            "gigs": [
                {"name": "AI Agent Setup & Automation", "price_range": "50-500"},
                {"name": "BMA Digitalization Consulting", "price_range": "200-5000"},
                {"name": "Custom AI Agent Development", "price_range": "100-2000"},
            ],
        },
        "consulting": {
            "services": [
                {"name": "BMA + AI Integration", "price_range": "2000-10000", "unique": True},
                {"name": "AI Agent Architecture", "price_range": "1000-5000"},
                {"name": "Automation Audit", "price_range": "500-2000"},
            ],
        },
        "community": {
            "platform": "discord",
            "price_monthly": 29,
            "name": "Agent Builders Club",
        },
    },

    # AI Model routing
    "models": {
        "scanner": "qwen2.5-coder:7b",      # Fast, for news scanning
        "producer": "qwen2.5-coder:14b",     # Quality, for content
        "reasoning": "deepseek-r1:7b",       # Deep thinking
        "cloud_bulk": "kimi-k2.5",           # Kimi for bulk tasks
        "cloud_critical": "claude-opus-4.6",  # Claude for critical
    },

    # News sources to scan
    "news_sources": {
        "ai": [
            "https://news.ycombinator.com",
            "https://www.producthunt.com",
            "https://arxiv.org/list/cs.AI/recent",
        ],
        "bma": [
            "https://www.brandschutz-zentrale.de",
            "https://www.bhe.de",
        ],
        "business": [
            "https://www.indiehackers.com",
            "https://twitter.com/search?q=AI+agents",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# CORE ENGINE MODULES
# ═══════════════════════════════════════════════════════════════════════════════

class Scanner:
    """
    NEWS SCANNER — First-Mover Intelligence
    Scans sources, extracts trends, identifies opportunities.
    Uses Ollama locally for cost-free analysis.
    """

    def __init__(self):
        self.results_dir = PROJECT_ROOT / "empire_data" / "scans"
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def scan_trends(self) -> dict:
        """Scan all configured news sources for trends."""
        print("  Scanning news sources...")

        # Check for Ollama
        try:
            import httpx
            r = httpx.get("http://localhost:11434/api/version", timeout=3)
            ollama_ok = r.status_code == 200
        except Exception:
            ollama_ok = False

        scan_result = {
            "timestamp": datetime.now().isoformat(),
            "ollama_available": ollama_ok,
            "sources_scanned": 0,
            "trends": [],
            "opportunities": [],
        }

        if not ollama_ok:
            print("    Ollama nicht verfuegbar — Scan-Modus eingeschraenkt")
            scan_result["note"] = "Ollama offline — starte mit: ollama serve"
            return scan_result

        # Scan each category
        for category, sources in CONFIG["news_sources"].items():
            for url in sources:
                scan_result["sources_scanned"] += 1
                # Note: actual web scraping would go here
                # For now, mark as scannable
                scan_result["trends"].append({
                    "category": category,
                    "source": url,
                    "status": "ready_to_scan",
                })

        # Save scan result
        scan_file = self.results_dir / f"scan_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        scan_file.write_text(json.dumps(scan_result, indent=2, ensure_ascii=False))

        return scan_result


class Producer:
    """
    CONTENT PRODUCER — High-End Multi-Format Content
    Generates posts, videos, articles for all personas.
    Uses Ollama for drafts, Kimi for bulk, Claude for premium.
    """

    def __init__(self):
        self.output_dir = PROJECT_ROOT / "empire_data" / "content"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_daily_content(self) -> dict:
        """Generate a full day of content for all personas."""
        result = {
            "timestamp": datetime.now().isoformat(),
            "content_pieces": [],
            "total_pieces": 0,
        }

        for persona in CONFIG["content"]["personas"]:
            for i in range(CONFIG["content"]["daily_posts_per_persona"]):
                piece = {
                    "persona": persona["name"],
                    "focus": persona["focus"],
                    "platforms": persona["platforms"],
                    "piece_number": i + 1,
                    "formats": CONFIG["content"]["video_formats"],
                    "status": "ready_to_generate",
                    "languages": CONFIG["content"]["languages"],
                }
                result["content_pieces"].append(piece)
                result["total_pieces"] += 1

        print(f"  Content Plan: {result['total_pieces']} Stuecke fuer {len(CONFIG['content']['personas'])} Personas")
        return result


class Distributor:
    """
    MULTI-PLATFORM DISTRIBUTOR — Post Everywhere
    Handles X/Twitter, YouTube, TikTok, Instagram, LinkedIn.
    Schedules, posts, tracks engagement.
    """

    def __init__(self):
        self.queue_dir = PROJECT_ROOT / "empire_data" / "distribution"
        self.queue_dir.mkdir(parents=True, exist_ok=True)

    def get_platform_status(self) -> dict:
        """Check which platforms are connected."""
        platforms = {
            "x_twitter": {"connected": False, "method": "x_lead_machine/x_automation.py"},
            "youtube": {"connected": False, "method": "YouTube API"},
            "tiktok": {"connected": False, "method": "TikTok API"},
            "instagram": {"connected": False, "method": "Instagram Graph API"},
            "linkedin": {"connected": False, "method": "LinkedIn API"},
            "gumroad": {"connected": False, "method": "Gumroad API"},
            "fiverr": {"connected": False, "method": "Manual (Browser)"},
        }

        # Check X Lead Machine
        if (PROJECT_ROOT / "x_lead_machine" / "x_automation.py").exists():
            platforms["x_twitter"]["connected"] = True

        return platforms


class Monetizer:
    """
    REVENUE ENGINE — Track and Optimize Revenue
    Monitors all channels, calculates metrics, suggests optimizations.
    """

    def __init__(self):
        self.data_dir = PROJECT_ROOT / "empire_data" / "revenue"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def get_revenue_status(self) -> dict:
        """Get current revenue across all channels."""
        channels = {}

        for channel_name, channel_config in CONFIG["channels"].items():
            channels[channel_name] = {
                "configured": True,
                "active": False,  # Will be True once products/gigs are live
                "revenue_this_month": 0,
                "products": channel_config.get("products", channel_config.get("gigs", channel_config.get("services", []))),
            }

        total = sum(c["revenue_this_month"] for c in channels.values())

        return {
            "timestamp": datetime.now().isoformat(),
            "total_monthly_revenue": total,
            "target_monthly": CONFIG["target_monthly"],
            "gap": CONFIG["target_monthly"] - total,
            "channels": channels,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def show_dashboard():
    """Show the Empire Engine status dashboard."""
    print()
    print("=" * 62)
    print("         EMPIRE ENGINE — Revenue Dashboard")
    print(f"         {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 62)
    print()

    # System Status
    print("  SYSTEM STATUS")
    print("  " + "-" * 56)

    # Check core services
    checks = {
        "Ollama (AI Lokal)": _check_ollama(),
        ".env Config": (PROJECT_ROOT / ".env").exists(),
        "Git Repo": (PROJECT_ROOT / ".git").exists(),
        "Workflow System": (PROJECT_ROOT / "workflow_system" / "orchestrator.py").exists(),
        "X Lead Machine": (PROJECT_ROOT / "x_lead_machine").exists(),
        "CRM System": (PROJECT_ROOT / "crm").exists(),
        "Brain System": (PROJECT_ROOT / "brain_system").exists(),
        "Kimi Swarm": (PROJECT_ROOT / "kimi_swarm").exists(),
        "Knowledge Store": (PROJECT_ROOT / "antigravity" / "knowledge_store.py").exists(),
        "Planning Mode": (PROJECT_ROOT / "antigravity" / "planning_mode.py").exists(),
        "Auto-Repair": (PROJECT_ROOT / "scripts" / "auto_repair.py").exists(),
        "BMA Academy": (PROJECT_ROOT / "BMA_ACADEMY").exists() or (PROJECT_ROOT / "products").exists(),
        "Mirror System": (PROJECT_ROOT / "mirror-system" / "sync" / "sync_manager.py").exists(),
        "Godmode Router": (PROJECT_ROOT / "godmode" / "router.py").exists(),
        "Config Module": (PROJECT_ROOT / "config" / "env_config.py").exists(),
        "Warroom": (PROJECT_ROOT / "warroom" / "00_command" / "status.md").exists(),
    }

    up = sum(1 for v in checks.values() if v)
    for name, ok in checks.items():
        status = "OK" if ok else "---"
        print(f"    [{status:>3}] {name}")

    print(f"\n    Systems: {up}/{len(checks)} aktiv")

    # Revenue Status
    print()
    print("  REVENUE STATUS")
    print("  " + "-" * 56)
    monetizer = Monetizer()
    rev = monetizer.get_revenue_status()
    print(f"    Umsatz diesen Monat: EUR {rev['total_monthly_revenue']:,.0f}")
    print(f"    Ziel:                EUR {rev['target_monthly']:,.0f}")
    print(f"    Gap:                 EUR {rev['gap']:,.0f}")

    print()
    print("    Kanaele:")
    for name, channel in rev["channels"].items():
        status = "AKTIV" if channel["active"] else "BEREIT"
        n_products = len(channel.get("products", []))
        print(f"      {name:15} [{status:>6}] {n_products} Produkte/Services")

    # Quick Wins
    print()
    print("  SOFORT-MASSNAHMEN (Quick Wins)")
    print("  " + "-" * 56)
    quick_wins = [
        "1. BMA-Checklisten auf Gumroad hochladen (EUR 27 x N)",
        "2. 3 Fiverr Gigs erstellen (AI Setup, BMA, Agent Dev)",
        "3. X/Twitter taeglich posten (3 Personas, 9 Posts/Tag)",
        "4. Discord 'Agent Builders Club' starten (EUR 29/Monat)",
        "5. 5 BMA-Firmen direkt kontaktieren (EUR 2000-10000/Projekt)",
    ]
    for win in quick_wins:
        print(f"    {win}")

    # Commands
    print()
    print("  BEFEHLE")
    print("  " + "-" * 56)
    commands = {
        "scan": "News + Trends scannen (First Mover)",
        "produce": "Content fuer alle Personas generieren",
        "distribute": "Content auf alle Plattformen posten",
        "leads": "Leads verarbeiten + CRM updaten",
        "revenue": "Revenue Report anzeigen",
        "auto": "Voller autonomer Zyklus",
        "godmode": "Godmode 4-Role Router starten",
        "mirror": "Mirror System (Mac<->Gemini) starten",
        "setup": "Ersteinrichtung (Accounts + APIs)",
        "repair": "System reparieren (Auto-Heal)",
    }
    for cmd, desc in commands.items():
        print(f"    python3 empire_engine.py {cmd:12} — {desc}")

    print()
    print("=" * 62)
    print()


def _check_ollama() -> bool:
    """Quick Ollama health check."""
    try:
        import httpx
        r = httpx.get("http://localhost:11434/api/version", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# AUTONOMOUS CYCLE
# ═══════════════════════════════════════════════════════════════════════════════

def run_autonomous_cycle():
    """
    Full autonomous revenue cycle:
    1. Scan → 2. Produce → 3. Distribute → 4. Lead Process → 5. Optimize
    """
    print()
    print("=" * 62)
    print("  AUTONOMOUS REVENUE CYCLE")
    print("=" * 62)
    print()

    steps = [
        ("Phase 1: News Scanner", Scanner().scan_trends),
        ("Phase 2: Content Producer", Producer().generate_daily_content),
        ("Phase 3: Platform Status", Distributor().get_platform_status),
        ("Phase 4: Revenue Check", Monetizer().get_revenue_status),
    ]

    results = {}
    for name, func in steps:
        print(f"\n  {name}...")
        try:
            result = func()
            results[name] = {"status": "ok", "data": result}
            print("    Abgeschlossen")
        except Exception as e:
            results[name] = {"status": "error", "error": str(e)}
            print(f"    Fehler: {e}")

    # Save cycle result
    data_dir = PROJECT_ROOT / "empire_data"
    data_dir.mkdir(exist_ok=True)
    cycle_file = data_dir / f"cycle_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    cycle_file.write_text(json.dumps(
        {"timestamp": datetime.now().isoformat(), "results": {k: v["status"] for k, v in results.items()}},
        indent=2, ensure_ascii=False,
    ))

    print(f"\n  Zyklus gespeichert: {cycle_file}")
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ""

    if command == "scan":
        scanner = Scanner()
        result = scanner.scan_trends()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif command == "produce":
        producer = Producer()
        result = producer.generate_daily_content()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif command == "distribute":
        dist = Distributor()
        result = dist.get_platform_status()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif command == "leads":
        print("  Lead Processing — CRM auf Port 3500 pruefen...")
        print("  cd crm && npm start")

    elif command == "revenue":
        mon = Monetizer()
        result = mon.get_revenue_status()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif command == "auto":
        run_autonomous_cycle()

    elif command == "repair":
        print("  Running Auto-Repair...")
        os.system(f"python3 {PROJECT_ROOT / 'scripts' / 'auto_repair.py'}")

    elif command == "setup":
        print("  Running Setup...")
        os.system(f"bash {PROJECT_ROOT / 'scripts' / 'setup_optimal_dev.sh'}")

    elif command == "godmode":
        task = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "--status"
        print("  Godmode Router (4-Role: Architect / Fixer / Coder / QA)...")
        os.system(f"python3 {PROJECT_ROOT / 'godmode' / 'router.py'} {task}")

    elif command == "mirror":
        print("  Mirror System (Mac <-> Gemini Dual-Brain)...")
        os.system(f"python3 {PROJECT_ROOT / 'mirror-system' / 'sync' / 'sync_manager.py'}")

    else:
        show_dashboard()


if __name__ == "__main__":
    main()
