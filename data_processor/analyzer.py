"""
Hybrid Analyzer - Ollama (lokal) + Claude (komplex)
"""

import asyncio
import json
from typing import Dict, Any
from antigravity.empire_bridge import get_bridge
from antigravity.unified_router import UnifiedRouter
import logging

logger = logging.getLogger(__name__)


class HybridAnalyzer:
    """Nutzt Ollama für schnelle Analyse, Claude für komplexe Tasks"""

    def __init__(self):
        self.bridge = get_bridge()
        self.router = UnifiedRouter()

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analysiere Daten mit Hybrid-Ansatz"""
        file_name = data.get("file_name", "unknown")
        file_type = data.get("file_type", "")
        content = self._extract_content(data)

        logger.info(f"🔍 Analysiere {file_name}...")

        # Phase 1: Schnelle Ollama-Analyse (lokal, kostenlos)
        ollama_result = await self._analyze_with_ollama(file_name, file_type, content)

        # Phase 2: Claude für komplexe Analyse (nur bei Bedarf)
        is_complex = self._is_complex_content(ollama_result)
        claude_result = None
        if is_complex:
            logger.info(f"🧠 Komplexe Analyse mit Claude: {file_name}")
            claude_result = await self._analyze_with_claude(file_name, content)

        return {
            "file_name": file_name,
            "ollama_analysis": ollama_result,
            "claude_analysis": claude_result,
            "is_complex": is_complex,
            "analysis_timestamp": asyncio.get_event_loop().time(),
        }

    def _extract_content(self, data: Dict[str, Any]) -> str:
        """Extrahiere analysierbaren Content"""
        if data.get("content_type") == "pdf":
            return "\n".join([p.get("content", "") for p in data.get("text", [])])
        elif data.get("content_type") == "json":
            return json.dumps(data.get("data", {}), indent=2)
        elif data.get("content_type") == "csv":
            return json.dumps(data.get("all_rows", []), indent=2)
        elif data.get("content_type") == "image":
            return data.get("ocr_text", "")
        elif data.get("content_type") == "audio":
            return data.get("transcription", "")
        elif data.get("content_type") == "docx":
            return data.get("text", "")
        return str(data)

    async def _analyze_with_ollama(
        self, file_name: str, file_type: str, content: str
    ) -> Dict[str, Any]:
        """Schnelle Analyse mit Ollama (lokal)"""
        try:
            prompt = f"""Analysiere diese {file_type} Datei und gib kompakte Erkenntnisse:
Datei: {file_name}

Inhalt (erste 2000 Zeichen):
{content[:2000]}

Gib folgende Struktur zurück als JSON:
{{
  "summary": "1-2 Sätze Zusammenfassung",
  "categories": ["Kategorie1", "Kategorie2"],
  "keywords": ["Keyword1", "Keyword2"],
  "sentiment": "neutral/positive/negative",
  "confidence": 0.85
}}"""

            result = await self.router.execute(prompt, model="ollama")
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            logger.warning(f"Ollama-Fehler: {str(e)}")
            return {
                "summary": f"Datei: {file_name}",
                "error": str(e),
            }

    async def _analyze_with_claude(self, file_name: str, content: str) -> Dict[str, Any]:
        """Tiefe Analyse mit Claude"""
        try:
            prompt = f"""Führe eine tiefgehende Analyse dieser Datei durch:
Datei: {file_name}

Inhalt:
{content}

Gib folgende Struktur als JSON zurück:
{{
  "detailed_summary": "Ausführliche Zusammenfassung (3-5 Sätze)",
  "main_insights": ["Einsicht 1", "Einsicht 2", "Einsicht 3"],
  "actionable_items": ["Aktion 1", "Aktion 2"],
  "risks": ["Risiko 1", "Risiko 2"],
  "recommendations": ["Empfehlung 1", "Empfehlung 2"],
  "entities": {{"people": [], "organizations": [], "locations": []}},
  "sentiment_detail": {{"overall": "neutral", "score": 0.5, "reasons": []}},
  "relevance_score": 0.85
}}"""

            result = await self.bridge.execute(prompt)
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            logger.error(f"Claude-Fehler: {str(e)}")
            return {"error": str(e)}

    def _is_complex_content(self, ollama_result: Dict[str, Any]) -> bool:
        """Entscheide ob Claude-Analyse nötig ist"""
        # Claude für: hohe Confidence, viele Keywords, komplexe Kategorien
        keywords = ollama_result.get("keywords", [])
        confidence = ollama_result.get("confidence", 0)
        return len(keywords) > 3 and confidence > 0.7
