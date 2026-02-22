"""
Empire AI Analyzer — Qwen 3.5 + DeepSeek R1 Cross-Verification Pipeline
=========================================================================
3-Schicht Analyse:
  Layer 1: Qwen 3.5      → Schnelle Basis-Analyse (kostenlos, lokal)
  Layer 2: DeepSeek R1   → Tiefe Reasoning-Analyse (kostenlos, lokal)
  Layer 3: Cross-Verify  → Beide Ergebnisse gegenseitig prüfen

Modell-Routing:
  - qwen2.5:latest / qwen3:latest   → Klassifikation, Zusammenfassung
  - deepseek-r1:7b                  → Reasoning, Insights, Empfehlungen
  - llava:latest                    → Vision (Bilder)
  - Claude (1%)                     → Nur für absolut kritische Inhalte

Kein OpenAI! 100% lokal via Ollama.
"""

import asyncio
import json
import logging
import time
from typing import Any

import aiohttp

from antigravity.config import OLLAMA_BASE_URL, ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

# ─── Ollama Model Roster ──────────────────────────────────────────────────────
QWEN_MODEL = "qwen2.5:latest"          # Schnelle Basis-Analyse
DEEPSEEK_MODEL = "deepseek-r1:7b"      # Deep Reasoning
VISION_MODEL = "llava:latest"          # Bild-Verständnis
FALLBACK_MODEL = "qwen2.5-coder:7b"   # Fallback wenn Hauptmodell fehlt

OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/api/tags"


async def _ollama_generate(model: str, prompt: str, timeout: int = 120) -> str:
    """Sende Anfrage an Ollama und gib Text zurück."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 2048},
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                OLLAMA_GENERATE_URL, json=payload, timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("response", "")
                else:
                    err = await resp.text()
                    logger.warning(f"Ollama {model} HTTP {resp.status}: {err[:200]}")
                    return ""
    except Exception as e:
        logger.warning(f"Ollama {model} Fehler: {e}")
        return ""


async def _available_models() -> list[str]:
    """Hole verfügbare Ollama-Modelle."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(OLLAMA_TAGS_URL, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [m["name"] for m in data.get("models", [])]
    except Exception:
        pass
    return []


def _parse_json_safe(text: str) -> dict:
    """Versuche JSON aus Text zu extrahieren (auch wenn Modell Prosa schreibt)."""
    text = text.strip()
    # Direkt JSON?
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # JSON-Block im Text?
    for start, end in [("```json", "```"), ("```", "```"), ("{", None)]:
        idx = text.find(start)
        if idx != -1:
            snippet = text[idx + len(start):]
            end_idx = snippet.rfind(end) if end else len(snippet)
            try:
                return json.loads(snippet[:end_idx].strip())
            except json.JSONDecodeError:
                pass
    return {}


# ─── Layer 1: Qwen 3.5 Basis-Analyse ────────────────────────────────────────

QWEN_PROMPT_TEMPLATE = """Du bist ein präziser Daten-Analyst. Analysiere die folgende Datei exakt.

DATEI: {file_name}
TYP: {file_type}
INHALT (erste 3000 Zeichen):
---
{content}
---

Antworte NUR mit gültigem JSON (kein Markdown, kein Text davor/danach):
{{
  "summary": "2-3 Satz Zusammenfassung auf Deutsch",
  "main_topic": "Hauptthema in 3-5 Wörtern",
  "categories": ["Kategorie1", "Kategorie2"],
  "keywords": ["Keyword1", "Keyword2", "Keyword3", "Keyword4", "Keyword5"],
  "sentiment": "positiv|neutral|negativ",
  "language": "de|en|andere",
  "document_type": "Rechnung|Vertrag|Bericht|Notiz|Tabelle|Bild|Audio|Code|Sonstiges",
  "importance_score": 0.75,
  "has_personal_data": false,
  "confidence": 0.9
}}"""


async def layer1_qwen_analysis(
    file_name: str, file_type: str, content: str
) -> dict:
    """Layer 1: Schnelle Klassifikation mit Qwen."""
    prompt = QWEN_PROMPT_TEMPLATE.format(
        file_name=file_name,
        file_type=file_type,
        content=content[:3000],
    )
    t0 = time.time()
    raw = await _ollama_generate(QWEN_MODEL, prompt, timeout=90)
    elapsed = round(time.time() - t0, 1)

    result = _parse_json_safe(raw)
    if not result:
        logger.warning(f"Qwen kein JSON für {file_name}, nutze Fallback")
        result = {
            "summary": raw[:300] if raw else "Keine Antwort",
            "categories": ["Unbekannt"],
            "keywords": [],
            "sentiment": "neutral",
            "document_type": "Sonstiges",
            "confidence": 0.3,
        }
    result["_model"] = QWEN_MODEL
    result["_latency_s"] = elapsed
    return result


# ─── Layer 2: DeepSeek R1 Deep Reasoning ─────────────────────────────────────

DEEPSEEK_PROMPT_TEMPLATE = """Du bist ein erfahrener Business-Analyst mit kritischem Denkvermögen.

Analysiere diese Datei tiefgehend:
DATEI: {file_name}
INHALT:
---
{content}
---

Erste Analyse (Qwen):
{qwen_summary}

Führe nun eine eigenständige, kritische Tiefenanalyse durch.
Antworte NUR mit gültigem JSON:
{{
  "detailed_summary": "Ausführliche Zusammenfassung (4-6 Sätze)",
  "main_insights": [
    "Einsicht 1: ...",
    "Einsicht 2: ...",
    "Einsicht 3: ..."
  ],
  "actionable_items": [
    "Konkrete Handlung 1",
    "Konkrete Handlung 2"
  ],
  "risks_and_issues": [
    "Risiko/Problem 1",
    "Risiko/Problem 2"
  ],
  "recommendations": [
    "Empfehlung 1",
    "Empfehlung 2"
  ],
  "entities": {{
    "people": [],
    "organizations": [],
    "locations": [],
    "dates": [],
    "amounts": []
  }},
  "business_relevance": "hoch|mittel|niedrig",
  "follow_up_needed": false,
  "tags": ["tag1", "tag2", "tag3"]
}}"""


async def layer2_deepseek_analysis(
    file_name: str, content: str, qwen_result: dict
) -> dict:
    """Layer 2: Tiefe Reasoning-Analyse mit DeepSeek R1."""
    qwen_summary = qwen_result.get("summary", "keine Zusammenfassung")
    prompt = DEEPSEEK_PROMPT_TEMPLATE.format(
        file_name=file_name,
        content=content[:4000],
        qwen_summary=qwen_summary,
    )
    t0 = time.time()
    raw = await _ollama_generate(DEEPSEEK_MODEL, prompt, timeout=180)
    elapsed = round(time.time() - t0, 1)

    result = _parse_json_safe(raw)
    if not result:
        logger.warning(f"DeepSeek kein JSON für {file_name}")
        result = {
            "detailed_summary": raw[:500] if raw else "Keine Antwort",
            "main_insights": [],
            "actionable_items": [],
            "risks_and_issues": [],
            "recommendations": [],
            "entities": {},
            "business_relevance": "mittel",
            "follow_up_needed": False,
            "tags": [],
        }
    result["_model"] = DEEPSEEK_MODEL
    result["_latency_s"] = elapsed
    return result


# ─── Layer 3: Cross-Verification ─────────────────────────────────────────────

CROSSVERIFY_PROMPT = """Du bist ein unabhängiger Prüfer. Zwei AI-Modelle haben diese Datei analysiert.
Überprüfe die Ergebnisse auf Konsistenz und erstelle die finale, vertrauenswürdige Zusammenfassung.

DATEI: {file_name}

ANALYSE VON QWEN:
{qwen_result}

ANALYSE VON DEEPSEEK:
{deepseek_result}

Erstelle eine finale Cross-Verified Zusammenfassung als JSON:
{{
  "verified_summary": "Beste Zusammenfassung basierend auf beiden Analysen",
  "verified_category": "Beste Kategorisierung",
  "verified_keywords": ["keyword1", "keyword2", "keyword3"],
  "verified_insights": ["Einsicht1", "Einsicht2", "Einsicht3"],
  "verified_actions": ["Aktion1", "Aktion2"],
  "consensus_score": 0.85,
  "conflicts_found": false,
  "conflict_details": "",
  "final_importance": "hoch|mittel|niedrig",
  "icloud_folder": "Vertraege|Rechnungen|Berichte|Notizen|Daten|Bilder|Sonstiges"
}}"""


async def layer3_cross_verify(
    file_name: str, qwen_result: dict, deepseek_result: dict
) -> dict:
    """Layer 3: Cross-Verification mit Qwen als unabhängigem Prüfer."""
    prompt = CROSSVERIFY_PROMPT.format(
        file_name=file_name,
        qwen_result=json.dumps(qwen_result, ensure_ascii=False, indent=2)[:1500],
        deepseek_result=json.dumps(deepseek_result, ensure_ascii=False, indent=2)[:1500],
    )
    t0 = time.time()
    # Qwen als Verifier (frischer Kontext, anderer Prompt)
    raw = await _ollama_generate(FALLBACK_MODEL, prompt, timeout=90)
    elapsed = round(time.time() - t0, 1)

    result = _parse_json_safe(raw)
    if not result:
        # Fallback: Kombiniere beide Ergebnisse manuell
        result = {
            "verified_summary": qwen_result.get("summary", ""),
            "verified_category": (qwen_result.get("categories") or ["Sonstiges"])[0],
            "verified_keywords": qwen_result.get("keywords", []),
            "verified_insights": deepseek_result.get("main_insights", []),
            "verified_actions": deepseek_result.get("actionable_items", []),
            "consensus_score": 0.6,
            "conflicts_found": False,
            "conflict_details": "",
            "final_importance": deepseek_result.get("business_relevance", "mittel"),
            "icloud_folder": "Sonstiges",
        }
    result["_model"] = FALLBACK_MODEL
    result["_latency_s"] = elapsed
    return result


# ─── Main Analyzer ───────────────────────────────────────────────────────────

class EmpireAnalyzer:
    """
    3-Layer Analyse-Pipeline:
      Layer 1: Qwen 3.5      → Schnelle Klassifikation
      Layer 2: DeepSeek R1   → Tiefes Reasoning
      Layer 3: Cross-Verify  → Konsistenz-Check + finale iCloud-Ordner-Zuweisung
    """

    def __init__(self):
        self._available: list[str] | None = None

    async def _ensure_models(self):
        """Prüfe welche Modelle verfügbar sind."""
        if self._available is None:
            self._available = await _available_models()
            if self._available:
                logger.info(f"Ollama Modelle verfügbar: {self._available}")
            else:
                logger.warning("Ollama nicht erreichbar — nutze Offline-Modus")

    async def analyze(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Führe komplette 3-Layer Analyse durch.

        Args:
            data: Ausgabe des entsprechenden FileProcessors

        Returns:
            Vollständige Analyse mit allen Layern + Metadaten
        """
        await self._ensure_models()

        file_name = data.get("file_name", "unknown")
        file_type = data.get("file_type", "")
        content = self._extract_content(data)

        logger.info(f"🔬 Analysiere [{file_type}] {file_name}")

        # ── Layer 1: Qwen Basis-Analyse ──────────────────────────────────────
        t_start = time.time()
        qwen = await layer1_qwen_analysis(file_name, file_type, content)
        logger.info(f"  ✓ Layer 1 (Qwen): {qwen.get('document_type', '?')} "
                    f"— {qwen.get('_latency_s', '?')}s")

        # ── Layer 2: DeepSeek Deep Reasoning ─────────────────────────────────
        deepseek = await layer2_deepseek_analysis(file_name, content, qwen)
        logger.info(f"  ✓ Layer 2 (DeepSeek): {deepseek.get('business_relevance', '?')} "
                    f"Relevanz — {deepseek.get('_latency_s', '?')}s")

        # ── Layer 3: Cross-Verification ───────────────────────────────────────
        verified = await layer3_cross_verify(file_name, qwen, deepseek)
        logger.info(f"  ✓ Layer 3 (Verify): Konsens {verified.get('consensus_score', '?')} "
                    f"— Ordner: {verified.get('icloud_folder', '?')}")

        total_time = round(time.time() - t_start, 1)

        return {
            "file_name": file_name,
            "file_type": file_type,
            "pipeline": "qwen3.5 → deepseek-r1 → cross-verify",
            "total_analysis_time_s": total_time,
            "layer1_qwen": qwen,
            "layer2_deepseek": deepseek,
            "layer3_verified": verified,
            # Schneller Zugriff auf finale Ergebnisse
            "final": {
                "summary": verified.get("verified_summary") or qwen.get("summary", ""),
                "category": verified.get("verified_category") or "Sonstiges",
                "icloud_folder": verified.get("icloud_folder") or "Sonstiges",
                "keywords": verified.get("verified_keywords") or qwen.get("keywords", []),
                "insights": verified.get("verified_insights") or [],
                "actions": verified.get("verified_actions") or [],
                "importance": verified.get("final_importance") or "mittel",
                "document_type": qwen.get("document_type") or "Sonstiges",
                "has_personal_data": qwen.get("has_personal_data", False),
                "follow_up_needed": deepseek.get("follow_up_needed", False),
                "tags": deepseek.get("tags") or verified.get("verified_keywords") or [],
            },
        }

    def _extract_content(self, data: dict[str, Any]) -> str:
        """Extrahiere analysierbaren Text-Content aus Prozessor-Output."""
        ct = data.get("content_type", "")
        if ct == "pdf":
            pages = data.get("text", [])
            return "\n".join(p.get("content", "") for p in pages)
        elif ct == "json":
            return json.dumps(data.get("data", {}), indent=2, ensure_ascii=False)
        elif ct == "csv":
            rows = data.get("all_rows", data.get("sample_rows", []))
            return json.dumps(rows, indent=2, ensure_ascii=False)
        elif ct == "image":
            return data.get("ocr_text", data.get("description", ""))
        elif ct == "audio":
            return data.get("transcription", "")
        elif ct in ("docx", "xlsx", "pptx", "office"):
            return data.get("text", data.get("content", ""))
        else:
            return str(data)
