"""
Sync Engine - Bidirektionale Synchronisation zwischen Main und Mirror.

Architektur:
  Mac (Main System)  <--Git+JSON-->  Gemini Mirror
       Kimi/Ollama                     Gemini Flash/Pro

Sync-Strategie:
1. State-Dateien werden per JSON synchronisiert
2. Patterns und Insights werden gemerged (nicht ueberschrieben)
3. Git ist der Transport-Layer
4. Konflikte werden durch Merge-Strategie geloest
5. n8n Webhooks triggern Real-Time Sync

Was wird synchronisiert:
- Workflow State (Zyklen, Schritte, Ergebnisse)
- Pattern Libraries (beidseitig)
- Vision Memory (Fragen + Antworten)
- Dual-Brain Insights
- Cowork Actions + Reflections
"""

import asyncio
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

MIRROR_DIR = Path(__file__).parent
sys.path.insert(0, str(MIRROR_DIR))

from config import (
    SYNC_STATE_FILE,
    SYNC_CONFIG,
    PROJECT_ROOT,
    STATE_DIR,
    MEMORY_DIR,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SYNC] %(levelname)s %(message)s",
)
logger = logging.getLogger("sync-engine")


class SyncEngine:
    """Bidirektionale Synchronisation zwischen Main und Mirror System."""

    def __init__(self):
        self.state = self._load_sync_state()
        self.project_root = PROJECT_ROOT

        # Pfade die synchronisiert werden
        self.sync_pairs = [
            {
                "name": "workflow_state",
                "main": PROJECT_ROOT / "workflow_system" / "state" / "current_state.json",
                "mirror": STATE_DIR / "mirror_state.json",
                "strategy": "merge_context",
            },
            {
                "name": "pattern_library",
                "main": PROJECT_ROOT / "workflow_system" / "state" / "pattern_library.json",
                "mirror": MEMORY_DIR / "cross_patterns.json",
                "strategy": "merge_append",
            },
            {
                "name": "cowork_state",
                "main": PROJECT_ROOT / "workflow_system" / "state" / "cowork_state.json",
                "mirror": STATE_DIR / "mirror_cowork_state.json",
                "strategy": "merge_actions",
            },
        ]

    def _load_sync_state(self) -> Dict:
        """Laedt Sync-Zustand."""
        if SYNC_STATE_FILE.exists():
            return json.loads(SYNC_STATE_FILE.read_text())
        default = {
            "created": datetime.now().isoformat(),
            "last_sync": None,
            "sync_count": 0,
            "conflicts_resolved": 0,
            "bytes_transferred": 0,
            "sync_history": [],
        }
        self._save_sync_state(default)
        return default

    def _save_sync_state(self, state: Dict):
        """Speichert Sync-Zustand."""
        state["updated"] = datetime.now().isoformat()
        SYNC_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))

    # === Core Sync ===

    async def full_sync(self) -> Dict:
        """Fuehrt komplette bidirektionale Synchronisation durch."""
        logger.info("╔══════════════════════════════════════╗")
        logger.info("║       BIDIREKTIONALER SYNC           ║")
        logger.info("╚══════════════════════════════════════╝")

        results = {
            "timestamp": datetime.now().isoformat(),
            "pairs_synced": 0,
            "conflicts": 0,
            "errors": [],
            "details": [],
        }

        for pair in self.sync_pairs:
            try:
                detail = await self._sync_pair(pair)
                results["details"].append(detail)
                results["pairs_synced"] += 1
                if detail.get("had_conflict"):
                    results["conflicts"] += 1
            except Exception as e:
                logger.error(f"Sync-Fehler bei {pair['name']}: {e}")
                results["errors"].append({
                    "pair": pair["name"],
                    "error": str(e),
                })

        # Cross-Pollination: Insights austauschen
        cross_result = await self._cross_pollinate()
        results["cross_pollination"] = cross_result

        # State aktualisieren
        self.state["last_sync"] = datetime.now().isoformat()
        self.state["sync_count"] = self.state.get("sync_count", 0) + 1
        self.state["sync_history"].append({
            "timestamp": results["timestamp"],
            "pairs": results["pairs_synced"],
            "conflicts": results["conflicts"],
            "errors": len(results["errors"]),
        })
        # Nur letzte 100 behalten
        self.state["sync_history"] = self.state["sync_history"][-100:]
        self._save_sync_state(self.state)

        logger.info("\n=== SYNC ABGESCHLOSSEN ===")
        logger.info(f"Paare synchronisiert: {results['pairs_synced']}")
        logger.info(f"Konflikte geloest: {results['conflicts']}")
        logger.info(f"Fehler: {len(results['errors'])}")

        return results

    async def _sync_pair(self, pair: Dict) -> Dict:
        """Synchronisiert ein Dateipaar."""
        name = pair["name"]
        main_path = pair["main"]
        mirror_path = pair["mirror"]
        strategy = pair["strategy"]

        logger.info(f"  Sync: {name} ({strategy})")

        main_data = self._safe_load_json(main_path)
        mirror_data = self._safe_load_json(mirror_path)

        if not main_data and not mirror_data:
            return {"pair": name, "action": "skip", "reason": "both_empty"}

        if not main_data:
            return {"pair": name, "action": "skip", "reason": "main_missing"}

        if not mirror_data:
            # Mirror hat noch keine Daten - Main kopieren
            mirror_path.parent.mkdir(parents=True, exist_ok=True)
            mirror_path.write_text(json.dumps(main_data, indent=2, ensure_ascii=False))
            return {"pair": name, "action": "init_from_main"}

        # Merge basierend auf Strategie
        had_conflict = False
        if strategy == "merge_context":
            merged = self._merge_context(main_data, mirror_data)
            had_conflict = merged.get("_had_conflict", False)
        elif strategy == "merge_append":
            merged = self._merge_append(main_data, mirror_data)
        elif strategy == "merge_actions":
            merged = self._merge_actions(main_data, mirror_data)
        else:
            merged = {**main_data, **mirror_data}

        # Zurueckschreiben
        mirror_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False))

        return {
            "pair": name,
            "action": "merged",
            "strategy": strategy,
            "had_conflict": had_conflict,
        }

    # === Merge-Strategien ===

    def _merge_context(self, main: Dict, mirror: Dict) -> Dict:
        """Merged Workflow-Kontexte (beide Seiten behalten)."""
        merged = {
            "main_system": {
                "cycle": main.get("cycle", 0),
                "steps": main.get("steps_completed", []),
                "patterns": main.get("patterns", []),
                "updated": main.get("updated", ""),
            },
            "mirror_system": {
                "cycle": mirror.get("cycle", 0),
                "steps": mirror.get("steps_completed", []),
                "patterns": mirror.get("patterns", []),
                "updated": mirror.get("updated", ""),
            },
            "sync_timestamp": datetime.now().isoformat(),
        }

        # Patterns zusammenfuehren (Duplikate entfernen)
        all_patterns = main.get("patterns", []) + mirror.get("patterns", [])
        seen_names = set()
        unique_patterns = []
        for p in all_patterns:
            name = p.get("name", "")
            if name not in seen_names:
                seen_names.add(name)
                unique_patterns.append(p)

        merged["combined_patterns"] = unique_patterns
        return merged

    def _merge_append(self, main: List, mirror: List) -> List:
        """Merged Listen durch Anhaengen (mit Deduplizierung)."""
        if isinstance(main, dict):
            main = main.get("patterns", []) if "patterns" in main else [main]
        if isinstance(mirror, dict):
            mirror = mirror.get("patterns", []) if "patterns" in mirror else [mirror]

        all_items = list(main) + list(mirror)
        seen = set()
        unique = []
        for item in all_items:
            key = json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item)
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique

    def _merge_actions(self, main: Dict, mirror: Dict) -> Dict:
        """Merged Cowork-Actions (beide behalten, sortiert nach Zeit)."""
        main_actions = main.get("actions_taken", [])
        mirror_actions = mirror.get("actions_taken", [])

        # Alle Actions zusammen, nach Timestamp sortiert
        all_actions = []
        for a in main_actions:
            a["_source"] = "main"
            all_actions.append(a)
        for a in mirror_actions:
            a["_source"] = "mirror"
            all_actions.append(a)

        all_actions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        merged = {
            "main_state": {k: v for k, v in main.items() if k != "actions_taken"},
            "mirror_state": {k: v for k, v in mirror.items() if k != "actions_taken"},
            "combined_actions": all_actions[:100],  # Letzte 100
            "sync_timestamp": datetime.now().isoformat(),
            "total_actions_main": len(main_actions),
            "total_actions_mirror": len(mirror_actions),
        }
        return merged

    # === Cross-Pollination ===

    async def _cross_pollinate(self) -> Dict:
        """Tauscht Insights zwischen Main und Mirror aus."""
        logger.info("  Cross-Pollination...")

        # Main-Output lesen
        main_output_dir = PROJECT_ROOT / "workflow_system" / "output"
        mirror_output_dir = MIRROR_DIR / "output"

        main_insights = self._extract_insights(main_output_dir, "main")
        mirror_insights = self._extract_insights(mirror_output_dir, "mirror")

        # Kombinierte Insights speichern
        cross_file = MEMORY_DIR / "cross_pollination_log.json"
        cross_data = []
        if cross_file.exists():
            try:
                cross_data = json.loads(cross_file.read_text())
            except json.JSONDecodeError:
                pass

        new_entry = {
            "timestamp": datetime.now().isoformat(),
            "main_insights_count": len(main_insights),
            "mirror_insights_count": len(mirror_insights),
            "combined": main_insights + mirror_insights,
        }
        cross_data.append(new_entry)
        cross_data = cross_data[-50:]  # Letzte 50

        cross_file.write_text(json.dumps(cross_data, indent=2, ensure_ascii=False))

        return {
            "main_insights": len(main_insights),
            "mirror_insights": len(mirror_insights),
            "total_cross_entries": len(cross_data),
        }

    def _extract_insights(self, output_dir: Path, source: str) -> List[Dict]:
        """Extrahiert Insights aus Output-Dateien."""
        insights = []
        if not output_dir.exists():
            return insights

        for f in sorted(output_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
            try:
                data = json.loads(f.read_text())
                insights.append({
                    "source": source,
                    "file": f.name,
                    "timestamp": data.get("timestamp", ""),
                    "step": data.get("step", f.stem),
                    "summary": json.dumps(data)[:300],
                })
            except (json.JSONDecodeError, OSError):
                continue

        return insights

    # === Git-basierter Sync ===

    def git_sync(self, message: str = "auto-sync") -> Dict:
        """Git-basierter Sync (add, commit, push)."""
        results = {"actions": [], "errors": []}

        try:
            # Stage sync-relevante Dateien
            for path in SYNC_CONFIG["sync_paths"]:
                full_path = PROJECT_ROOT / path
                if full_path.exists():
                    subprocess.run(
                        ["git", "add", str(full_path)],
                        cwd=str(PROJECT_ROOT),
                        capture_output=True,
                    )
                    results["actions"].append(f"staged: {path}")

            # Commit
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            commit_msg = f"[mirror-sync] {message} ({timestamp})"
            commit_result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
            )
            if commit_result.returncode == 0:
                results["actions"].append("committed")
            else:
                results["actions"].append("nothing_to_commit")

            # Push (wenn aktiviert)
            if SYNC_CONFIG.get("auto_push"):
                push_result = subprocess.run(
                    ["git", "push", "origin", "HEAD"],
                    cwd=str(PROJECT_ROOT),
                    capture_output=True,
                    text=True,
                )
                if push_result.returncode == 0:
                    results["actions"].append("pushed")
                else:
                    results["errors"].append(f"push_failed: {push_result.stderr[:200]}")

        except Exception as e:
            results["errors"].append(str(e))

        return results

    # === Hilfsfunktionen ===

    @staticmethod
    def _safe_load_json(path: Path) -> Optional[Dict]:
        """Laedt JSON sicher (gibt None bei Fehler)."""
        if not path.exists():
            return None
        try:
            content = path.read_text()
            if not content.strip():
                return None
            return json.loads(content)
        except (json.JSONDecodeError, OSError):
            return None

    def get_sync_status(self) -> Dict:
        """Gibt Sync-Status zurueck."""
        return {
            "last_sync": self.state.get("last_sync"),
            "sync_count": self.state.get("sync_count", 0),
            "conflicts_resolved": self.state.get("conflicts_resolved", 0),
            "recent_syncs": self.state.get("sync_history", [])[-5:],
        }


# === Daemon Mode ===

async def run_sync_daemon(interval: int = None):
    """Sync-Daemon der regelmaessig synchronisiert."""
    if interval is None:
        interval = SYNC_CONFIG["interval_seconds"]

    engine = SyncEngine()
    logger.info(f"Sync-Daemon gestartet (Intervall: {interval}s)")

    cycle = 0
    try:
        while True:
            cycle += 1
            logger.info(f"\n--- Sync-Zyklus {cycle} ---")
            try:
                result = await engine.full_sync()
                logger.info(f"Sync OK: {result['pairs_synced']} Paare, {result['conflicts']} Konflikte")
            except Exception as e:
                logger.error(f"Sync-Fehler: {e}")

            await asyncio.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Sync-Daemon gestoppt.")


# === CLI ===

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gemini Mirror Sync Engine")
    parser.add_argument("--daemon", action="store_true", help="Daemon-Modus")
    parser.add_argument("--interval", type=int, default=900, help="Sync-Intervall in Sekunden")
    parser.add_argument("--status", action="store_true", help="Sync-Status anzeigen")
    parser.add_argument("--git-sync", action="store_true", help="Git-Sync ausfuehren")
    args = parser.parse_args()

    if args.status:
        engine = SyncEngine()
        status = engine.get_sync_status()
        print(json.dumps(status, indent=2))
    elif args.git_sync:
        engine = SyncEngine()
        result = engine.git_sync()
        print(json.dumps(result, indent=2))
    elif args.daemon:
        asyncio.run(run_sync_daemon(args.interval))
    else:
        asyncio.run(SyncEngine().full_sync())
