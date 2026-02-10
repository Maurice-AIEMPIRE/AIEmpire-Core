#!/usr/bin/env python3
"""
MEMORY BRIDGE - Unified Knowledge System
Shared knowledge graph between Claude (Primary) and Gemini (Mirror).

Both brains write to and read from a shared memory system that
accumulates knowledge, decisions, patterns, and insights over time.

This is Maurice's "digital memory" - everything both brains learn
is permanently stored and accessible to both.

Usage:
  python memory_bridge.py --status           # Show memory status
  python memory_bridge.py --add "key" "val"  # Add knowledge entry
  python memory_bridge.py --search "query"   # Search knowledge
  python memory_bridge.py --export           # Export full knowledge graph
  python memory_bridge.py --consolidate      # Merge and deduplicate
"""

import asyncio
import argparse
import json
import os
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))
from config import PROJECT_ROOT, MIRROR_DIR, MEMORY_DIR

# ── Knowledge Files ──────────────────────────────────────────

KNOWLEDGE_FILE = MEMORY_DIR / "shared_knowledge.json"
DECISIONS_FILE = MEMORY_DIR / "decisions_log.json"
PATTERNS_FILE = MEMORY_DIR / "discovered_patterns.json"
INSIGHTS_FILE = MEMORY_DIR / "insights.json"
MAURICE_PROFILE = MEMORY_DIR / "vision_profile.json"  # Shared with vision_engine


def load_knowledge() -> Dict:
    if KNOWLEDGE_FILE.exists():
        return json.loads(KNOWLEDGE_FILE.read_text())
    return {
        "created": datetime.now().isoformat(),
        "version": 1,
        "categories": {
            "business": {},       # Business strategies, revenue models
            "technical": {},      # Code patterns, architecture decisions
            "market": {},         # Market insights, competitor intel
            "personal": {},       # Maurice's preferences, work style
            "products": {},       # Product ideas, designs, pricing
            "contacts": {},       # People, partnerships, leads
            "legal": {},          # Legal knowledge, contracts, compliance
            "bma": {},            # BMA-specific expertise (Maurice's domain)
            "automation": {},     # Automation patterns, workflows
            "content": {},        # Content strategies, viral patterns
        },
        "total_entries": 0,
        "sources": {
            "claude_primary": 0,
            "gemini_mirror": 0,
            "user_input": 0,
            "cowork_engine": 0,
            "kimi_swarm": 0,
        },
    }


def save_knowledge(knowledge: Dict) -> None:
    knowledge["updated"] = datetime.now().isoformat()
    KNOWLEDGE_FILE.write_text(json.dumps(knowledge, indent=2, ensure_ascii=False))


def load_decisions() -> List[Dict]:
    if DECISIONS_FILE.exists():
        return json.loads(DECISIONS_FILE.read_text())
    return []


def save_decisions(decisions: List[Dict]) -> None:
    DECISIONS_FILE.write_text(json.dumps(decisions, indent=2, ensure_ascii=False))


def load_patterns() -> List[Dict]:
    if PATTERNS_FILE.exists():
        return json.loads(PATTERNS_FILE.read_text())
    return []


def save_patterns(patterns: List[Dict]) -> None:
    PATTERNS_FILE.write_text(json.dumps(patterns, indent=2, ensure_ascii=False))


def load_insights() -> List[Dict]:
    if INSIGHTS_FILE.exists():
        return json.loads(INSIGHTS_FILE.read_text())
    return []


def save_insights(insights: List[Dict]) -> None:
    INSIGHTS_FILE.write_text(json.dumps(insights, indent=2, ensure_ascii=False))


# ── Knowledge Operations ─────────────────────────────────────

def add_knowledge(category: str, key: str, value: str,
                  source: str = "user_input", confidence: float = 0.8,
                  tags: List[str] = None) -> Dict:
    """Add a knowledge entry to the shared graph."""
    knowledge = load_knowledge()

    if category not in knowledge["categories"]:
        knowledge["categories"][category] = {}

    entry_id = hashlib.md5(f"{category}:{key}:{value[:50]}".encode()).hexdigest()[:8]

    entry = {
        "id": entry_id,
        "key": key,
        "value": value,
        "source": source,
        "confidence": confidence,
        "tags": tags or [],
        "created": datetime.now().isoformat(),
        "accessed_count": 0,
        "last_accessed": None,
    }

    # Check for existing entry with same key
    existing = knowledge["categories"][category].get(key)
    if existing:
        # Merge: keep higher confidence, append to value if different
        if existing.get("value") != value:
            entry["value"] = f"{existing['value']}\n---\n[Update {source}]: {value}"
            entry["confidence"] = max(existing.get("confidence", 0), confidence)
            entry["accessed_count"] = existing.get("accessed_count", 0)

    knowledge["categories"][category][key] = entry
    knowledge["total_entries"] = sum(
        len(cat) for cat in knowledge["categories"].values()
    )
    knowledge["sources"][source] = knowledge["sources"].get(source, 0) + 1
    save_knowledge(knowledge)

    return entry


def search_knowledge(query: str, category: str = None) -> List[Dict]:
    """Search the knowledge graph."""
    knowledge = load_knowledge()
    results = []
    query_lower = query.lower()

    categories = {category: knowledge["categories"][category]} if category else knowledge["categories"]

    for cat_name, entries in categories.items():
        for key, entry in entries.items():
            # Search in key and value
            if (query_lower in key.lower() or
                query_lower in entry.get("value", "").lower() or
                any(query_lower in tag.lower() for tag in entry.get("tags", []))):
                results.append({
                    "category": cat_name,
                    **entry,
                })

    # Sort by confidence
    results.sort(key=lambda x: x.get("confidence", 0), reverse=True)

    # Update access counts
    for r in results:
        cat = r["category"]
        key = r.get("key")
        if key and key in knowledge["categories"].get(cat, {}):
            knowledge["categories"][cat][key]["accessed_count"] = \
                knowledge["categories"][cat][key].get("accessed_count", 0) + 1
            knowledge["categories"][cat][key]["last_accessed"] = datetime.now().isoformat()
    save_knowledge(knowledge)

    return results


def record_decision(decision: str, reasoning: str, alternatives: List[str] = None,
                    source: str = "user_input") -> Dict:
    """Record a key decision."""
    decisions = load_decisions()

    entry = {
        "id": f"dec_{len(decisions)+1:04d}",
        "decision": decision,
        "reasoning": reasoning,
        "alternatives": alternatives or [],
        "source": source,
        "timestamp": datetime.now().isoformat(),
        "outcome": None,  # To be filled later
    }

    decisions.append(entry)
    save_decisions(decisions)
    return entry


def record_pattern(pattern: str, context: str, frequency: int = 1,
                   source: str = "gemini_mirror") -> Dict:
    """Record a discovered pattern."""
    patterns = load_patterns()

    # Check for existing
    for p in patterns:
        if p.get("pattern") == pattern:
            p["frequency"] = p.get("frequency", 0) + frequency
            p["last_seen"] = datetime.now().isoformat()
            save_patterns(patterns)
            return p

    entry = {
        "id": f"pat_{len(patterns)+1:04d}",
        "pattern": pattern,
        "context": context,
        "frequency": frequency,
        "source": source,
        "discovered": datetime.now().isoformat(),
        "last_seen": datetime.now().isoformat(),
        "applied_count": 0,
    }

    patterns.append(entry)
    save_patterns(patterns)
    return entry


def record_insight(insight: str, category: str, impact: str = "medium",
                   source: str = "gemini_mirror") -> Dict:
    """Record a strategic insight."""
    insights = load_insights()

    entry = {
        "id": f"ins_{len(insights)+1:04d}",
        "insight": insight,
        "category": category,
        "impact": impact,
        "source": source,
        "timestamp": datetime.now().isoformat(),
        "acted_on": False,
    }

    insights.append(entry)
    save_insights(insights)
    return entry


# ── Consolidation ────────────────────────────────────────────

def consolidate_knowledge() -> Dict:
    """Merge and deduplicate knowledge across all sources."""
    knowledge = load_knowledge()
    stats = {"merged": 0, "deduplicated": 0, "categories_cleaned": 0}

    for cat_name, entries in knowledge["categories"].items():
        # Remove entries with very low confidence
        low_confidence = [k for k, v in entries.items() if v.get("confidence", 0) < 0.2]
        for k in low_confidence:
            del entries[k]
            stats["deduplicated"] += 1

        stats["categories_cleaned"] += 1

    knowledge["total_entries"] = sum(
        len(cat) for cat in knowledge["categories"].values()
    )
    save_knowledge(knowledge)

    return stats


# ── Import from existing systems ─────────────────────────────

def import_from_workflow_patterns() -> int:
    """Import patterns from the workflow system's pattern library."""
    pattern_file = PROJECT_ROOT / "workflow-system" / "state" / "pattern_library.json"
    if not pattern_file.exists():
        return 0

    imported = 0
    try:
        patterns = json.loads(pattern_file.read_text())
        if isinstance(patterns, list):
            for p in patterns:
                if isinstance(p, str):
                    record_pattern(p, context="Imported from workflow pattern library",
                                   source="cowork_engine")
                    imported += 1
                elif isinstance(p, dict):
                    record_pattern(
                        p.get("pattern", str(p)),
                        context=p.get("context", "Workflow pattern library"),
                        source="cowork_engine",
                    )
                    imported += 1
    except json.JSONDecodeError:
        pass

    return imported


def import_from_cowork_state() -> int:
    """Import insights from cowork engine state."""
    cowork_file = PROJECT_ROOT / "workflow-system" / "state" / "cowork_state.json"
    if not cowork_file.exists():
        return 0

    imported = 0
    try:
        state = json.loads(cowork_file.read_text())

        # Import observations as insights
        for obs in state.get("observations", []):
            if isinstance(obs, str):
                record_insight(obs, category="automation", source="cowork_engine")
                imported += 1
            elif isinstance(obs, dict):
                record_insight(
                    obs.get("observation", str(obs)),
                    category=obs.get("category", "automation"),
                    source="cowork_engine",
                )
                imported += 1

        # Import discovered patterns
        for pat in state.get("patterns_discovered", []):
            if isinstance(pat, str):
                record_pattern(pat, context="Cowork engine discovery", source="cowork_engine")
                imported += 1
            elif isinstance(pat, dict):
                record_pattern(
                    pat.get("pattern", str(pat)),
                    context=pat.get("context", "Cowork engine"),
                    source="cowork_engine",
                )
                imported += 1
    except json.JSONDecodeError:
        pass

    return imported


# ── Export ────────────────────────────────────────────────────

def export_full_graph() -> Dict:
    """Export the complete knowledge graph."""
    return {
        "knowledge": load_knowledge(),
        "decisions": load_decisions(),
        "patterns": load_patterns(),
        "insights": load_insights(),
        "profile": json.loads(MAURICE_PROFILE.read_text()) if MAURICE_PROFILE.exists() else {},
        "exported_at": datetime.now().isoformat(),
    }


# ── Status Display ───────────────────────────────────────────

def show_status() -> None:
    """Show memory bridge status."""
    knowledge = load_knowledge()
    decisions = load_decisions()
    patterns = load_patterns()
    insights = load_insights()

    print("\n  MEMORY BRIDGE - Unified Knowledge System")
    print("  " + "=" * 50)
    print(f"  Total Knowledge Entries: {knowledge.get('total_entries', 0)}")
    print(f"  Decisions Recorded:      {len(decisions)}")
    print(f"  Patterns Discovered:     {len(patterns)}")
    print(f"  Insights Stored:         {len(insights)}")
    print(f"  Last Updated:            {knowledge.get('updated', 'never')}")

    # Category breakdown
    print(f"\n  KNOWLEDGE CATEGORIES:")
    for cat_name, entries in knowledge["categories"].items():
        if entries:
            print(f"    {cat_name:15s}: {len(entries)} entries")

    # Sources
    sources = knowledge.get("sources", {})
    if any(v > 0 for v in sources.values()):
        print(f"\n  KNOWLEDGE SOURCES:")
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                print(f"    {source:20s}: {count} entries")

    # Recent decisions
    if decisions:
        print(f"\n  RECENT DECISIONS:")
        for d in decisions[-3:]:
            print(f"    [{d.get('timestamp', 'N/A')[:10]}] {d.get('decision', 'N/A')[:55]}")

    # Top patterns
    if patterns:
        top = sorted(patterns, key=lambda x: x.get("frequency", 0), reverse=True)[:5]
        print(f"\n  TOP PATTERNS:")
        for p in top:
            freq = p.get("frequency", 0)
            print(f"    (x{freq}) {p.get('pattern', 'N/A')[:55]}")

    # Memory files
    print(f"\n  MEMORY FILES:")
    for f in MEMORY_DIR.iterdir():
        if f.is_file():
            size = f.stat().st_size
            print(f"    {f.name:30s} ({size/1024:.1f} KB)")

    print()


# ── Main ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Memory Bridge - Unified Knowledge System")
    parser.add_argument("--status", action="store_true", help="Show memory status")
    parser.add_argument("--add", nargs=3, metavar=("CATEGORY", "KEY", "VALUE"),
                        help="Add knowledge entry")
    parser.add_argument("--search", type=str, help="Search knowledge")
    parser.add_argument("--export", action="store_true", help="Export full knowledge graph")
    parser.add_argument("--consolidate", action="store_true", help="Merge and deduplicate")
    parser.add_argument("--import-all", action="store_true", help="Import from existing systems")
    parser.add_argument("--decide", nargs=2, metavar=("DECISION", "REASONING"),
                        help="Record a decision")

    args = parser.parse_args()

    if args.add:
        entry = add_knowledge(args.add[0], args.add[1], args.add[2])
        print(f"  Added: {entry['id']} -> {args.add[0]}/{args.add[1]}")
    elif args.search:
        results = search_knowledge(args.search)
        print(f"\n  Search: '{args.search}' -> {len(results)} results")
        for r in results[:10]:
            print(f"    [{r['category']}] {r['key']}: {r.get('value', 'N/A')[:50]}")
        print()
    elif args.export:
        graph = export_full_graph()
        export_file = MEMORY_DIR / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        export_file.write_text(json.dumps(graph, indent=2, ensure_ascii=False))
        print(f"  Exported to: {export_file}")
    elif args.consolidate:
        stats = consolidate_knowledge()
        print(f"  Consolidated: {stats}")
    elif args.import_all:
        wf = import_from_workflow_patterns()
        cw = import_from_cowork_state()
        print(f"  Imported: {wf} from workflow, {cw} from cowork")
    elif args.decide:
        entry = record_decision(args.decide[0], args.decide[1])
        print(f"  Decision recorded: {entry['id']}")
    else:
        show_status()


if __name__ == "__main__":
    main()
