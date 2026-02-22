"""
Output Formatter - Strukturiert Ergebnisse in Folder + Excel + Markdown + JSON
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OutputFormatter:
    """Erstellt strukturierte Output in verschiedenen Formaten"""

    def __init__(self, output_dir="/data/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def format_and_save(
        self, extracted: Dict[str, Any], analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Formatiere Daten und speichere in alle Formate"""
        file_name = extracted.get("file_name", "unknown")
        category = self._determine_category(analysis)

        # Erstelle Kategorie-Ordner
        category_dir = self.output_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)

        # Speichere in verschiedenen Formaten
        results = {
            "json": await self._save_as_json(
                file_name, extracted, analysis, category_dir
            ),
            "markdown": await self._save_as_markdown(
                file_name, extracted, analysis, category_dir
            ),
        }

        return results

    def _determine_category(self, analysis: Dict[str, Any]) -> str:
        """Bestimme Kategorie basierend auf Analyse"""
        ollama = analysis.get("ollama_analysis", {})
        categories = ollama.get("categories", ["Sonstiges"])
        return categories[0] if categories else "Sonstiges"

    async def _save_as_json(
        self,
        file_name: str,
        extracted: Dict[str, Any],
        analysis: Dict[str, Any],
        output_dir: Path,
    ) -> str:
        """Speichere als JSON mit voller Struktur"""
        json_file = output_dir / f"{Path(file_name).stem}_analysis.json"

        output = {
            "metadata": {
                "original_file": file_name,
                "processed_date": datetime.now().isoformat(),
                "file_type": extracted.get("file_type"),
            },
            "extraction": self._clean_for_json(extracted),
            "analysis": self._clean_for_json(analysis),
        }

        try:
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ JSON gespeichert: {json_file}")
            return str(json_file)
        except Exception as e:
            logger.error(f"JSON-Fehler: {str(e)}")
            return ""

    async def _save_as_markdown(
        self,
        file_name: str,
        extracted: Dict[str, Any],
        analysis: Dict[str, Any],
        output_dir: Path,
    ) -> str:
        """Speichere als strukturiertes Markdown"""
        md_file = output_dir / f"{Path(file_name).stem}_report.md"

        ollama = analysis.get("ollama_analysis", {})
        claude = analysis.get("claude_analysis", {})

        md_content = f"""# Analyse-Bericht: {file_name}

**Verarbeitungsdatum:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
**Dateityp:** {extracted.get('file_type', 'unknown')}

## Schnellanalyse (Ollama)

**Zusammenfassung:**
{ollama.get('summary', 'Keine Zusammenfassung')}

**Kategorien:** {', '.join(ollama.get('categories', []))}

**Stichworte:** {', '.join(ollama.get('keywords', []))}

**Stimmung:** {ollama.get('sentiment', 'neutral')}

---

"""

        if claude:
            md_content += f"""## Tiefenanalyse (Claude)

**Detaillierte Zusammenfassung:**
{claude.get('detailed_summary', 'N/A')}

### Erkenntnisse
{self._format_list(claude.get('main_insights', []))}

### Handlungsempfehlungen
{self._format_list(claude.get('actionable_items', []))}

### Risiken
{self._format_list(claude.get('risks', []))}

### Empfehlungen
{self._format_list(claude.get('recommendations', []))}

---
"""

        try:
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(md_content)
            logger.info(f"✅ Markdown gespeichert: {md_file}")
            return str(md_file)
        except Exception as e:
            logger.error(f"Markdown-Fehler: {str(e)}")
            return ""

    def _format_list(self, items: List[str]) -> str:
        """Formatiere Liste als Markdown"""
        return "\n".join([f"- {item}" for item in items]) if items else "Keine Items"

    def _clean_for_json(self, obj: Any) -> Any:
        """Entferne nicht-serialisierbare Objekte"""
        if isinstance(obj, dict):
            return {k: self._clean_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_for_json(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            return str(obj)
