#!/usr/bin/env python3
"""
AIEmpire Codebase Exporter
==========================
Exportiert den gesamten relevanten Code als eine einzige Markdown-Datei.
Ideal zum Einfuegen in ChatGPT, Claude, Gemini etc.

Usage:
    python3 scripts/export_codebase.py
    python3 scripts/export_codebase.py --output ~/Desktop/empire_code.md
    python3 scripts/export_codebase.py --section souls    # nur Souls
    python3 scripts/export_codebase.py --section core     # nur Core
    python3 scripts/export_codebase.py --section config   # nur Config
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent

# ─── Was wird exportiert (in dieser Reihenfolge) ──────────────────────────────
EXPORT_SECTIONS = {
    "core": {
        "title": "CORE SYSTEM",
        "files": [
            "empire_engine.py",
            "antigravity/empire_bridge.py",
            "antigravity/unified_router.py",
            "antigravity/config.py",
            "antigravity/knowledge_store.py",
            "antigravity/cross_verify.py",
            "antigravity/planning_mode.py",
            "antigravity/sync_engine.py",
        ],
    },
    "souls": {
        "title": "SOUL ARCHITECTURE v2.0",
        "files": [
            "souls/soul_spawner.py",
            "souls/core/architect.md",
            "souls/core/builder.md",
            "souls/core/money_maker.md",
            "souls/core/operator.md",
            "souls/specialists/engineering.yaml",
            "souls/specialists/revenue.yaml",
            "souls/specialists/operations.yaml",
            "souls/specialists/research.yaml",
            "souls/specialists/content.yaml",
            "souls/teams/default.yaml",
        ],
    },
    "workflow": {
        "title": "WORKFLOW SYSTEM",
        "files": [
            "workflow_system/orchestrator.py",
            "workflow_system/cowork.py",
            "workflow_system/resource_guard.py",
        ],
    },
    "revenue": {
        "title": "REVENUE + CONTENT",
        "files": [
            "x_lead_machine/x_automation.py",
            "src/content_scheduler.py",
            "atomic_reactor/runner.py",
        ],
    },
    "config": {
        "title": "CONFIGURATION",
        "files": [
            "openclaw-config/SOUL.md",
            "openclaw-config/AGENTS.md",
            "openclaw-config/LEAD_AGENT_PROMPT.md",
            "openclaw-config/jobs.json",
            "openclaw-config/models.json",
            "openclaw-config/settings.json",
            ".env.example",
            "CLAUDE.md",
        ],
    },
    "scripts": {
        "title": "SCRIPTS + AUTOMATION",
        "files": [
            "scripts/auto_repair.py",
            "scripts/bombproof_startup.sh",
            "scripts/setup_empire_local.sh",
            "scripts/start_all_services.sh",
            "telegram_bot/empire_bot.py",
        ],
    },
    "brain": {
        "title": "BRAIN SYSTEM",
        "glob": "brain_system/*.py",
        "files": [],
    },
}

# ─── Was NICHT exportiert wird ────────────────────────────────────────────────
SKIP_PATTERNS = {
    "dirs": {
        "node_modules", "__pycache__", ".git", "venv", ".venv",
        "empire_data", "empire_brain", "publish", "publish_ready",
        "gold-nuggets", "BMA_ACADEMY", "products", "warroom",
        ".github", "workspace", "docs", "gemini-mirror",
    },
    "extensions": {
        ".pyc", ".pyo", ".log", ".db", ".sqlite", ".sqlite3",
        ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
        ".zip", ".tar", ".gz", ".whl", ".egg",
        ".lock", ".DS_Store",
    },
    "files": {
        "package-lock.json", "yarn.lock", ".gitignore",
        "known_hosts", "known_hosts.old",
    },
}

LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".sh": "bash",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".md": "markdown",
    ".toml": "toml",
    ".env": "bash",
    ".txt": "text",
    ".sql": "sql",
    "": "text",
}

MAX_FILE_SIZE = 80_000  # Max 80KB pro Datei


def get_lang(path: Path) -> str:
    return LANG_MAP.get(path.suffix.lower(), "text")


def format_file(path: Path, rel_path: str) -> str:
    """Formatiert eine einzelne Datei als Markdown-Block."""
    try:
        size = path.stat().st_size
        if size > MAX_FILE_SIZE:
            return f"\n### `{rel_path}`\n> [Datei zu gross: {size//1024}KB — nur erste 200 Zeilen]\n\n```{get_lang(path)}\n" + \
                   "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[:200]) + \
                   "\n```\n"

        content = path.read_text(encoding="utf-8", errors="replace").strip()
        if not content:
            return f"\n### `{rel_path}`\n> [Leere Datei]\n"

        lang = get_lang(path)
        lines = len(content.splitlines())
        size_kb = size / 1024

        return f"\n### `{rel_path}`\n> {lines} Zeilen • {size_kb:.1f}KB\n\n```{lang}\n{content}\n```\n"

    except Exception as e:
        return f"\n### `{rel_path}`\n> [Fehler beim Lesen: {e}]\n"


def export_section(section_key: str, section: dict) -> str:
    """Exportiert eine Section als Markdown."""
    output = []
    output.append(f"\n## {section['title']}\n")
    output.append("---\n")

    files_found = 0

    # Spezifische Dateien
    for rel_path in section.get("files", []):
        path = PROJECT_ROOT / rel_path
        if path.exists():
            output.append(format_file(path, rel_path))
            files_found += 1
        else:
            output.append(f"\n### `{rel_path}`\n> [Nicht gefunden]\n")

    # Glob patterns
    if "glob" in section:
        for path in sorted(PROJECT_ROOT.glob(section["glob"])):
            if should_skip(path):
                continue
            rel = str(path.relative_to(PROJECT_ROOT))
            output.append(format_file(path, rel))
            files_found += 1

    output.append(f"\n> *{files_found} Dateien in dieser Section*\n")
    return "\n".join(output)


def should_skip(path: Path) -> bool:
    """Check ob eine Datei uebersprungen werden soll."""
    # Check dir parts
    for part in path.parts:
        if part in SKIP_PATTERNS["dirs"]:
            return True

    # Check extension
    if path.suffix.lower() in SKIP_PATTERNS["extensions"]:
        return True

    # Check filename
    if path.name in SKIP_PATTERNS["files"]:
        return True

    return False


def export_full(output_path: Path, sections: list = None):
    """Exportiert den gesamten Codebase."""
    if sections is None:
        sections = list(EXPORT_SECTIONS.keys())

    lines = []

    # Header
    lines.append("# AIEmpire-Core — Codebase Export")
    lines.append(f"> Exportiert: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"> Server: Hetzner Ubuntu 24.04 • /opt/aiempire")
    lines.append(f"> Branch: claude/empire-infrastructure-setup-KtNDE")
    lines.append("")
    lines.append("## Uebersicht")
    lines.append("")
    lines.append("| Section | Beschreibung |")
    lines.append("|---------|-------------|")
    lines.append("| CORE | empire_engine.py, empire_bridge.py, antigravity/ |")
    lines.append("| SOULS | 4 Core Souls + 39 Specialists + soul_spawner.py |")
    lines.append("| WORKFLOW | orchestrator.py, cowork.py, resource_guard.py |")
    lines.append("| REVENUE | x_automation.py, content_scheduler.py |")
    lines.append("| CONFIG | openclaw-config/, jobs.json, CLAUDE.md |")
    lines.append("| SCRIPTS | auto_repair.py, bombproof_startup.sh |")
    lines.append("| BRAIN | brain_system/*.py |")
    lines.append("")
    lines.append("---")

    total_files = 0

    for section_key in sections:
        if section_key not in EXPORT_SECTIONS:
            print(f"  [SKIP] Unbekannte Section: {section_key}")
            continue

        section = EXPORT_SECTIONS[section_key]
        print(f"  [EXPORT] {section['title']}...")
        section_md = export_section(section_key, section)
        lines.append(section_md)

        # Count files
        n = section_md.count("### `")
        total_files += n
        print(f"           {n} Dateien")

    # Footer
    lines.append("\n---")
    lines.append(f"\n> **Export komplett**: {total_files} Dateien • {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("> Erstellt mit: `python3 scripts/export_codebase.py`")

    content = "\n".join(lines)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")

    size_kb = len(content.encode()) / 1024
    size_mb = size_kb / 1024

    return total_files, size_kb, size_mb


def main():
    parser = argparse.ArgumentParser(description="AIEmpire Codebase Exporter")
    parser.add_argument(
        "--output", "-o",
        default=str(PROJECT_ROOT / "empire_export.md"),
        help="Output Datei (default: empire_export.md)"
    )
    parser.add_argument(
        "--section", "-s",
        choices=list(EXPORT_SECTIONS.keys()) + ["all"],
        default="all",
        help="Welche Section exportieren (default: all)"
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    sections = list(EXPORT_SECTIONS.keys()) if args.section == "all" else [args.section]

    print()
    print("=" * 50)
    print("  AIEmpire Codebase Exporter")
    print("=" * 50)
    print(f"  Output: {output_path}")
    print(f"  Sections: {', '.join(sections)}")
    print()

    total_files, size_kb, size_mb = export_full(output_path, sections)

    print()
    print("=" * 50)
    print("  EXPORT COMPLETE")
    print("=" * 50)
    print(f"  Datei:  {output_path}")
    print(f"  Groesse: {size_kb:.0f}KB ({size_mb:.2f}MB)")
    print(f"  Dateien: {total_files}")
    print()

    if size_kb > 100:
        print("  TIPP fuer ChatGPT/Claude:")
        print("  Falls zu gross, einzelne Sections exportieren:")
        for s in EXPORT_SECTIONS:
            print(f"    python3 scripts/export_codebase.py --section {s}")
        print()

    print(f"  cat {output_path}")
    print()


if __name__ == "__main__":
    main()
