"""
Output Formatter — Strukturiert Analyse-Ergebnisse in iCloud-Ordner
====================================================================
Ausgabe pro Datei:
  /data/results/<icloud_folder>/
    <dateiname>_report.md      ← Lesbarer Bericht
    <dateiname>_analysis.json  ← Vollständige Daten

iCloud-Ordner werden automatisch durch Layer 3 (Cross-Verify) zugewiesen:
  Vertraege | Rechnungen | Berichte | Notizen | Daten | Bilder | Sonstiges
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Standard iCloud-Ordner (darf durch AI erweitert werden)
ICLOUD_FOLDERS = {
    "Vertraege", "Rechnungen", "Berichte", "Notizen",
    "Daten", "Bilder", "Audio", "Code", "Sonstiges",
}


class OutputFormatter:
    """Erstellt strukturierten Output für iCloud-Sync."""

    def __init__(self, output_dir: str = "/data/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def format_and_save(
        self, extracted: dict[str, Any], analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Erstelle strukturierten Output.

        Args:
            extracted: Output des File-Prozessors (Rohdaten)
            analysis:  Output des EmpireAnalyzers (AI-Analyse)

        Returns:
            Pfade der erstellten Dateien
        """
        file_name = extracted.get("file_name", "unknown")
        stem = Path(file_name).stem

        # iCloud-Ordner aus Layer 3 (Cross-Verify)
        final = analysis.get("final", {})
        icloud_folder = self._safe_folder(final.get("icloud_folder", "Sonstiges"))

        # Erstelle Ziel-Ordner
        dest_dir = self.output_dir / icloud_folder
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Speichere beide Formate parallel
        json_path = await self._save_json(stem, extracted, analysis, dest_dir)
        md_path = await self._save_markdown(stem, file_name, extracted, analysis, dest_dir)

        logger.info(f"📁 Gespeichert in [{icloud_folder}]: {stem}")
        return {
            "json": json_path,
            "markdown": md_path,
            "folder": icloud_folder,
            "dest_dir": str(dest_dir),
        }

    def _safe_folder(self, folder: str) -> str:
        """Stelle sicher dass Ordner-Name sicher ist (kein Path Traversal)."""
        clean = "".join(c for c in folder if c.isalnum() or c in "-_")
        return clean if clean else "Sonstiges"

    async def _save_json(
        self,
        stem: str,
        extracted: dict,
        analysis: dict,
        dest_dir: Path,
    ) -> str:
        """Speichere vollständige Analyse als JSON."""
        path = dest_dir / f"{stem}_analysis.json"
        output = {
            "metadata": {
                "original_file": extracted.get("file_name"),
                "processed_date": datetime.now().isoformat(),
                "file_type": extracted.get("file_type"),
                "pipeline": analysis.get("pipeline"),
                "total_analysis_time_s": analysis.get("total_analysis_time_s"),
            },
            "final": analysis.get("final", {}),
            "extraction_summary": self._extraction_summary(extracted),
            "full_analysis": {
                "layer1_qwen": analysis.get("layer1_qwen", {}),
                "layer2_deepseek": analysis.get("layer2_deepseek", {}),
                "layer3_verified": analysis.get("layer3_verified", {}),
            },
        }
        try:
            path.write_text(
                json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"JSON-Fehler: {e}")
        return str(path)

    async def _save_markdown(
        self,
        stem: str,
        file_name: str,
        extracted: dict,
        analysis: dict,
        dest_dir: Path,
    ) -> str:
        """Speichere lesbaren Markdown-Bericht."""
        path = dest_dir / f"{stem}_report.md"
        final = analysis.get("final", {})
        qwen = analysis.get("layer1_qwen", {})
        deepseek = analysis.get("layer2_deepseek", {})
        verified = analysis.get("layer3_verified", {})
        now = datetime.now().strftime("%d.%m.%Y %H:%M")

        # Badges
        importance = final.get("importance", "mittel")
        importance_badge = {"hoch": "🔴 HOCH", "mittel": "🟡 MITTEL", "niedrig": "🟢 NIEDRIG"}.get(
            importance, importance
        )
        follow_up = "⚠️ JA" if final.get("follow_up_needed") else "✅ NEIN"
        personal = "🔒 JA" if final.get("has_personal_data") else "✅ NEIN"

        md = f"""# {file_name}

| Feld | Wert |
|------|------|
| **Verarbeitungsdatum** | {now} |
| **Dateityp** | `{extracted.get("file_type", "?")}` |
| **Dokument-Typ** | {final.get("document_type", "?")} |
| **iCloud-Ordner** | 📂 {final.get("icloud_folder", "Sonstiges")} |
| **Wichtigkeit** | {importance_badge} |
| **Follow-up nötig** | {follow_up} |
| **Personenbezogene Daten** | {personal} |
| **Analyse-Zeit** | {analysis.get("total_analysis_time_s", "?")}s |
| **Pipeline** | `{analysis.get("pipeline", "?")}` |

---

## Zusammenfassung

{final.get("summary", "Keine Zusammenfassung verfügbar")}

**Keywords:** {", ".join(f"`{k}`" for k in final.get("keywords", []))}

**Tags:** {", ".join(f"#{t}" for t in final.get("tags", []))}

---

## Erkenntnisse (DeepSeek R1)

{self._md_list(final.get("insights", []))}

## Empfohlene Aktionen

{self._md_list(final.get("actions", []))}

## Risiken & Probleme

{self._md_list(deepseek.get("risks_and_issues", []))}

---

## Layer 1: Qwen Schnellanalyse

- **Thema:** {qwen.get("main_topic", "?")}
- **Kategorie:** {", ".join(qwen.get("categories", []))}
- **Stimmung:** {qwen.get("sentiment", "?")}
- **Sprache:** {qwen.get("language", "?")}
- **Konfidenz:** {qwen.get("confidence", "?")}
- **Modell:** `{qwen.get("_model", "?")}` ({qwen.get("_latency_s", "?")}s)

## Layer 3: Cross-Verification

- **Konsens-Score:** {verified.get("consensus_score", "?")}
- **Konflikte:** {"JA — " + verified.get("conflict_details", "") if verified.get("conflicts_found") else "Keine"}
- **Verifier-Modell:** `{verified.get("_model", "?")}`

---
*Generiert von AIEmpire Data Pipeline*
"""

        # Entitäten falls vorhanden
        entities = deepseek.get("entities", {})
        entity_lines = []
        for etype, items in entities.items():
            if items:
                entity_lines.append(f"- **{etype.capitalize()}:** {', '.join(str(i) for i in items)}")
        if entity_lines:
            md += "\n## Erkannte Entitäten\n\n" + "\n".join(entity_lines) + "\n"

        try:
            path.write_text(md, encoding="utf-8")
        except Exception as e:
            logger.error(f"Markdown-Fehler: {e}")
        return str(path)

    def _md_list(self, items: list) -> str:
        """Formatiere als Markdown-Liste."""
        if not items:
            return "_Keine Einträge_"
        return "\n".join(f"- {item}" for item in items)

    def _extraction_summary(self, extracted: dict) -> dict:
        """Kompakte Zusammenfassung der Extraktion (ohne riesige Rohdaten)."""
        ct = extracted.get("content_type", "")
        summary = {
            "content_type": ct,
            "processing_status": extracted.get("processing_status"),
        }
        if ct == "pdf":
            pages = extracted.get("text", [])
            summary["page_count"] = len(pages)
            summary["total_chars"] = sum(len(p.get("content", "")) for p in pages)
        elif ct == "csv":
            summary["row_count"] = extracted.get("row_count", 0)
            summary["column_count"] = extracted.get("column_count", 0)
            summary["columns"] = extracted.get("columns", [])
        elif ct == "image":
            summary["dimensions"] = extracted.get("dimensions")
            summary["has_ocr"] = bool(extracted.get("ocr_text"))
        elif ct == "audio":
            summary["duration_s"] = extracted.get("duration_s")
            summary["has_transcription"] = bool(extracted.get("transcription"))
        return summary
