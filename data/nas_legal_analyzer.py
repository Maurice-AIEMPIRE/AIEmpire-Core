"""
NAS Legal Analyzer — Full Legal Analysis Pipeline
====================================================
Orchestrates the complete legal analysis workflow on Hetzner NAS:

1. SCAN: Find all legal documents on local storage
2. PROCESS: Extract text, OCR, entities from all documents
3. ANALYZE: Run multi-phase legal analysis (Timeline, Evidence, Claims, Risk)
4. CROSS-VERIFY: Libra cross-checks local analysis for accuracy
5. EXPORT: Generate professional legal work products

Integrates:
  - Local Ollama models (free, P3-compliant for privacy)
  - Libra Legal AI (GDPR/EEA-compliant, cross-verification)
  - Gemini (fallback for non-sensitive analysis tasks)

Usage:
    python -m data.nas_legal_analyzer run /pfad/zu/dokumenten
    python -m data.nas_legal_analyzer run                      # uses data/inbox/
    python -m data.nas_legal_analyzer status
    python -m data.nas_legal_analyzer report

Architecture:
    Documents → Processing → Ollama (local analysis) → Libra (cross-verify)
                                                      → Professional Outputs
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    from config.env_config import get_api_key
except ImportError:
    def get_api_key(name: str) -> str:
        return os.getenv(name, "")

from data.legal_doc_processor import LegalDocProcessor, ProcessedDocument
from data.libra_connector import LibraConnector, LibraResponse


# ── Project paths ─────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
LEGAL_DIR = PROJECT_ROOT / "legal"
LEGAL_TIMELINE = LEGAL_DIR / "timeline"
LEGAL_EVIDENCE = LEGAL_DIR / "evidence"
LEGAL_CLAIMS = LEGAL_DIR / "claims"
LEGAL_STRATEGY = LEGAL_DIR / "strategy"
LEGAL_DRAFTS = LEGAL_DIR / "drafts"
LEGAL_MEMOS = LEGAL_DIR / "memos"
DATA_EXPORTS = PROJECT_ROOT / "data" / "exports"

# Ensure directories exist
for d in [LEGAL_TIMELINE, LEGAL_EVIDENCE, LEGAL_CLAIMS, LEGAL_STRATEGY,
          LEGAL_DRAFTS, LEGAL_MEMOS, DATA_EXPORTS]:
    d.mkdir(parents=True, exist_ok=True)


# ── YAML Header Template ─────────────────────────────────────────────
def yaml_header(title: str, agent: str, inputs: list[str], confidence: str = "medium") -> str:
    """Generate standard YAML header for legal outputs."""
    inputs_str = json.dumps(inputs[:10], ensure_ascii=False)
    return (
        f"---\n"
        f"title: {title}\n"
        f"agent: {agent}\n"
        f"team: Legal\n"
        f"created_at: {datetime.now(timezone.utc).isoformat()}\n"
        f"inputs: {inputs_str}\n"
        f"confidence: {confidence}\n"
        f"disclaimer: \"ENTWURF - KEINE RECHTSBERATUNG. Zur Pruefung durch Rechtsanwalt.\"\n"
        f"---\n\n"
    )


# ── Ollama Local Connector ───────────────────────────────────────────
class OllamaLegalClient:
    """
    Local Ollama client for legal analysis.
    Uses models running on the Hetzner server.
    P3 compliant — all data stays local.
    """

    def __init__(self):
        self.base_url = get_api_key("OLLAMA_BASE_URL") or "http://localhost:11434"
        self.model = get_api_key("OLLAMA_LEGAL_MODEL") or "gemma3:27b"
        self.fallback_models = [
            "gemma3:27b",
            "llama3.1:70b",
            "qwen2.5:32b",
            "mistral-large:latest",
            "llama3.1:8b",
            "qwen2.5-coder:14b",
        ]

    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.1,
        max_tokens: int = 8192,
    ) -> str:
        """Generate text using local Ollama model."""
        import httpx

        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=300) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("response", "")
                else:
                    # Try fallback models
                    return await self._try_fallbacks(prompt, system, temperature, max_tokens)
        except Exception as e:
            print(f"  [WARN] Ollama Fehler ({self.model}): {e}")
            return await self._try_fallbacks(prompt, system, temperature, max_tokens)

    async def _try_fallbacks(
        self, prompt: str, system: str, temperature: float, max_tokens: int
    ) -> str:
        """Try fallback models if primary model fails."""
        import httpx

        for model in self.fallback_models:
            if model == self.model:
                continue
            try:
                url = f"{self.base_url}/api/generate"
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "system": system,
                    "stream": False,
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                }
                async with httpx.AsyncClient(timeout=300) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        result = data.get("response", "")
                        if result:
                            print(f"  [OK] Fallback-Model: {model}")
                            return result
            except Exception:
                continue
        return "[FEHLER] Kein Ollama-Model verfuegbar. Bitte Ollama starten."

    async def check_available(self) -> tuple[bool, list[str]]:
        """Check which Ollama models are available."""
        import httpx

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    models = [m["name"] for m in resp.json().get("models", [])]
                    return True, models
        except Exception:
            pass
        return False, []


# ── Analysis Phases ───────────────────────────────────────────────────

LEGAL_SYSTEM_PROMPT = (
    "Du bist ein hochspezialisierter deutscher Rechtsanalyst. "
    "Du arbeitest praezise, quellenbasiert und strukturiert. "
    "Jede Aussage MUSS auf ein konkretes Dokument oder eine Textstelle verweisen. "
    "Wenn Informationen fehlen, markiere sie als [MISSING]. "
    "Wenn du unsicher bist, markiere als [NEEDS VERIFICATION]. "
    "Format: Professionelles Markdown, bereit fuer Anwaltsuebergabe. "
    "Sprache: Deutsch (juristisches Fachvokabular)."
)


@dataclass
class AnalysisResult:
    """Result of the full legal analysis pipeline."""
    documents_processed: int = 0
    timeline_path: str = ""
    evidence_map_path: str = ""
    claims_matrix_path: str = ""
    risk_report_path: str = ""
    opponent_analysis_path: str = ""
    settlement_plan_path: str = ""
    exec_brief_path: str = ""
    consistency_report_path: str = ""
    libra_cross_check_path: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    total_time_seconds: float = 0
    models_used: list[str] = field(default_factory=list)


class NASLegalAnalyzer:
    """
    Full legal analysis pipeline for NAS/Hetzner stored documents.

    Runs the complete L01-L10 agent pipeline:
    1. Document intake and processing
    2. Timeline generation (L01)
    3. Evidence mapping (L02)
    4. Claims matrix (L03)
    5. Opponent analysis (L05)
    6. Risk assessment (L06)
    7. Settlement strategy (L07)
    8. Consistency check (L09)
    9. Executive brief (L10)
    10. Libra cross-verification
    """

    def __init__(self, case_context: str = ""):
        self.processor = LegalDocProcessor()
        self.ollama = OllamaLegalClient()
        self.libra = LibraConnector()
        self.case_context = case_context
        self._processed_docs: list[ProcessedDocument] = []
        self._doc_texts: list[dict] = []

    async def run_full_analysis(
        self,
        document_path: Optional[str | Path] = None,
        case_context: str = "",
        use_libra: bool = True,
    ) -> AnalysisResult:
        """
        Run the complete legal analysis pipeline.

        Args:
            document_path: Path to documents (directory or inbox)
            case_context: Description of the case/dispute
            use_libra: Whether to use Libra for cross-verification
        """
        start_time = time.time()
        result = AnalysisResult()

        if case_context:
            self.case_context = case_context

        print("\n" + "=" * 70)
        print("  NAS LEGAL ANALYZER — Vollstaendige Rechtsanalyse")
        print("=" * 70)

        # ── Phase 1: Document Processing ──────────────────────────────
        print("\n[PHASE 1/9] Dokumentenverarbeitung")
        print("-" * 40)

        if document_path:
            self._processed_docs = await self.processor.process_directory(document_path)
        else:
            self._processed_docs = await self.processor.process_inbox()

        result.documents_processed = len(self._processed_docs)

        if not self._processed_docs:
            result.errors.append("Keine Dokumente gefunden oder verarbeitet.")
            print("[ABBRUCH] Keine Dokumente gefunden.")
            return result

        # Prepare text data for analysis
        self._doc_texts = []
        for doc in self._processed_docs:
            if not doc.is_duplicate and doc.text_content:
                self._doc_texts.append({
                    "filename": doc.filename,
                    "normalized_name": doc.normalized_name,
                    "type": doc.file_type,
                    "text": doc.text_content,
                    "dates": doc.dates_found,
                    "amounts": doc.amounts_found,
                    "companies": doc.companies_found,
                    "entities": [
                        {"type": e.entity_type, "value": e.value}
                        for e in doc.entities[:20]
                    ],
                })

        print(f"\n  {len(self._doc_texts)} eindeutige Dokumente mit Text fuer Analyse bereit")

        # Check Ollama availability
        ollama_ok, available_models = await self.ollama.check_available()
        if ollama_ok:
            print(f"  Ollama: {len(available_models)} Models verfuegbar")
            result.models_used.append(f"ollama:{self.ollama.model}")
        else:
            result.warnings.append("Ollama nicht erreichbar. Nur Libra wird verwendet.")
            print("  [WARN] Ollama nicht erreichbar!")

        # Check Libra availability
        libra_valid = self.libra.validate_config()[0]
        if use_libra and libra_valid:
            print("  Libra: API Key konfiguriert")
            result.models_used.append("libra")
        elif use_libra:
            result.warnings.append("Libra API Key fehlt. Cross-Verification uebersprungen.")
            use_libra = False

        # Build document context for prompts
        doc_context = self._build_document_context()

        # ── Phase 2: Timeline (L01) ──────────────────────────────────
        print("\n[PHASE 2/9] Timeline erstellen (L01)")
        print("-" * 40)
        result.timeline_path = await self._generate_timeline(doc_context)

        # ── Phase 3: Evidence Map (L02) ───────────────────────────────
        print("\n[PHASE 3/9] Beweismatrix erstellen (L02)")
        print("-" * 40)
        result.evidence_map_path = await self._generate_evidence_map(doc_context)

        # ── Phase 4: Claims Matrix (L03) ──────────────────────────────
        print("\n[PHASE 4/9] Anspruchsmatrix erstellen (L03)")
        print("-" * 40)
        result.claims_matrix_path = await self._generate_claims_matrix(doc_context)

        # ── Phase 5: Opponent Analysis (L05) ──────────────────────────
        print("\n[PHASE 5/9] Gegneranalyse (L05)")
        print("-" * 40)
        result.opponent_analysis_path = await self._generate_opponent_analysis(doc_context)

        # ── Phase 6: Risk Assessment (L06) ────────────────────────────
        print("\n[PHASE 6/9] Risikobewertung (L06)")
        print("-" * 40)
        result.risk_report_path = await self._generate_risk_report(doc_context)

        # ── Phase 7: Settlement Strategy (L07) ────────────────────────
        print("\n[PHASE 7/9] Vergleichsstrategie (L07)")
        print("-" * 40)
        result.settlement_plan_path = await self._generate_settlement_plan(doc_context)

        # ── Phase 8: Consistency Check (L09) ──────────────────────────
        print("\n[PHASE 8/9] Konsistenzpruefung (L09)")
        print("-" * 40)
        result.consistency_report_path = await self._generate_consistency_report()

        # ── Phase 9: Libra Cross-Verification ─────────────────────────
        if use_libra and libra_valid:
            print("\n[PHASE 9/9] Libra Cross-Verification")
            print("-" * 40)
            result.libra_cross_check_path = await self._libra_cross_verify(doc_context)

        # ── Executive Brief (L10) ─────────────────────────────────────
        print("\n[BONUS] Executive Brief erstellen (L10)")
        print("-" * 40)
        result.exec_brief_path = await self._generate_exec_brief()

        # ── Summary ───────────────────────────────────────────────────
        result.total_time_seconds = time.time() - start_time

        print("\n" + "=" * 70)
        print("  ANALYSE ABGESCHLOSSEN")
        print("=" * 70)
        print(f"\n  Dokumente verarbeitet: {result.documents_processed}")
        print(f"  Models verwendet: {', '.join(result.models_used)}")
        print(f"  Dauer: {result.total_time_seconds:.0f} Sekunden")
        print(f"\n  Generierte Outputs:")
        for label, path in [
            ("Timeline", result.timeline_path),
            ("Beweismatrix", result.evidence_map_path),
            ("Anspruchsmatrix", result.claims_matrix_path),
            ("Gegneranalyse", result.opponent_analysis_path),
            ("Risikobewertung", result.risk_report_path),
            ("Vergleichsplan", result.settlement_plan_path),
            ("Konsistenz", result.consistency_report_path),
            ("Libra Check", result.libra_cross_check_path),
            ("Executive Brief", result.exec_brief_path),
        ]:
            if path:
                print(f"    {label:20} -> {path}")

        if result.warnings:
            print(f"\n  Warnungen: {len(result.warnings)}")
            for w in result.warnings:
                print(f"    - {w}")

        if result.errors:
            print(f"\n  Fehler: {len(result.errors)}")
            for e in result.errors:
                print(f"    - {e}")

        return result

    def _build_document_context(self, max_chars: int = 80000) -> str:
        """Build a text context from all processed documents for analysis prompts."""
        parts = []
        total = 0

        for doc in self._doc_texts:
            max_per_doc = min(15000, (max_chars - total) // max(1, len(self._doc_texts) - len(parts)))
            text = doc["text"][:max_per_doc]

            part = (
                f"\n### DOKUMENT: {doc['filename']}\n"
                f"Typ: {doc['type']} | "
                f"Daten: {', '.join(doc['dates'][:5])} | "
                f"Betraege: {', '.join(doc['amounts'][:3])}\n\n"
                f"{text}\n"
            )
            parts.append(part)
            total += len(part)

            if total >= max_chars:
                break

        return "\n---\n".join(parts)

    def _write_output(self, filepath: Path, content: str) -> str:
        """Write output file atomically."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        tmp = filepath.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(content)
        tmp.replace(filepath)
        return str(filepath)

    # ── Phase Implementations ─────────────────────────────────────────

    async def _generate_timeline(self, doc_context: str) -> str:
        """L01: Generate chronological timeline."""
        prompt = f"""Erstelle eine detaillierte chronologische Timeline aller Ereignisse aus den folgenden Dokumenten.

FALLKONTEXT: {self.case_context}

DOKUMENTE:
{doc_context}

ANFORDERUNGEN:
1. Jeder Eintrag: DATUM | EREIGNIS | BETEILIGTE | QUELLE (Dokumentname + Stelle)
2. Chronologisch sortiert (aeltestes zuerst)
3. Luecken zwischen Ereignissen markieren: [LUECKE: DD.MM.YYYY - DD.MM.YYYY — keine Dokumente]
4. Wenn ein Datum geschaetzt ist: [GESCHAETZT]
5. Mindestens eine Tabelle im Markdown-Format

Format als professionelle Timeline-Tabelle."""

        print("  Generiere Timeline mit Ollama ...", end=" ", flush=True)
        content = await self.ollama.generate(prompt, LEGAL_SYSTEM_PROMPT)
        print("OK")

        filenames = [d["filename"] for d in self._doc_texts[:10]]
        header = yaml_header("Chronologische Timeline", "L01_Legal_Timeline", filenames)

        output = (
            header
            + "# TIMELINE — Chronologische Ereigniskette\n\n"
            + f"> Erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            + f"> Dokumente analysiert: {len(self._doc_texts)}\n"
            + f"> Fallkontext: {self.case_context[:200]}\n\n"
            + content
            + "\n\n## Next Actions\n"
            + "- [ ] Timeline mit Originaldokumenten abgleichen\n"
            + "- [ ] Fehlende Zeitraeume recherchieren\n"
            + "- [ ] Timeline an Anwalt zur Pruefung uebergeben\n"
        )

        return self._write_output(LEGAL_TIMELINE / "TIMELINE.md", output)

    async def _generate_evidence_map(self, doc_context: str) -> str:
        """L02: Generate evidence mapping."""
        prompt = f"""Erstelle eine vollstaendige Beweismatrix (Evidence Map) fuer den folgenden Fall.

FALLKONTEXT: {self.case_context}

DOKUMENTE:
{doc_context}

ANFORDERUNGEN:
1. Fuer JEDES Dokument: Was beweist es? Fuer wen? Gegen wen?
2. Exhibit-Nummerierung: EX-001, EX-002, ...
3. Beweiswert: STARK / MITTEL / SCHWACH mit Begruendung
4. Tabelle: Exhibit-Nr | Dokument | Beweist | Fuer/Gegen | Beweiswert | Anmerkungen
5. Fehlende Beweismittel identifizieren: [MISSING EVIDENCE: ...]
6. Beweiskette: Welche Dokumente stuetzen sich gegenseitig?

Erstelle die professionelle Evidence Map."""

        print("  Generiere Beweismatrix mit Ollama ...", end=" ", flush=True)
        content = await self.ollama.generate(prompt, LEGAL_SYSTEM_PROMPT)
        print("OK")

        filenames = [d["filename"] for d in self._doc_texts[:10]]
        header = yaml_header("Beweismatrix / Evidence Map", "L02_Legal_EvidenceMapper", filenames)

        output = (
            header
            + "# EVIDENCE MAP — Beweismatrix\n\n"
            + f"> Erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            + f"> Exhibits erfasst: {len(self._doc_texts)}\n\n"
            + content
            + "\n\n## Next Actions\n"
            + "- [ ] Beweismittel nach Relevanz priorisieren\n"
            + "- [ ] Fehlende Beweismittel beschaffen\n"
            + "- [ ] Beweiskette mit Anwalt durchgehen\n"
        )

        return self._write_output(LEGAL_EVIDENCE / "EVIDENCE_MAP.md", output)

    async def _generate_claims_matrix(self, doc_context: str) -> str:
        """L03: Generate claims matrix."""
        prompt = f"""Erstelle eine vollstaendige Anspruchsmatrix (Claims Matrix) fuer den folgenden Fall.

FALLKONTEXT: {self.case_context}

DOKUMENTE:
{doc_context}

ANFORDERUNGEN:
1. EIGENE Ansprueche: Anspruchsgrundlage (§), Tatbestand, Beweis, Erfolgsaussicht (1-5)
2. GEGNERISCHE Ansprueche/Einwaende: Gleiche Struktur
3. Verteidigungsmoeglickeiten gegen jeden gegnerischen Anspruch
4. Risikobewertung pro Anspruch: HOCH / MITTEL / NIEDRIG
5. Naechste Schritte pro Anspruch
6. Tabelle: Nr | Anspruch | Grundlage | Beweis | Staerke | Risiko | Aktion

Erstelle die professionelle Claims Matrix."""

        print("  Generiere Anspruchsmatrix mit Ollama ...", end=" ", flush=True)
        content = await self.ollama.generate(prompt, LEGAL_SYSTEM_PROMPT)
        print("OK")

        filenames = [d["filename"] for d in self._doc_texts[:10]]
        header = yaml_header("Anspruchsmatrix / Claims Matrix", "L03_Legal_ClaimsMatrix", filenames)

        output = (
            header
            + "# CLAIM MATRIX — Anspruchsmatrix\n\n"
            + f"> Erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            + content
            + "\n\n## Next Actions\n"
            + "- [ ] Anspruchsgrundlagen mit Anwalt verifizieren\n"
            + "- [ ] Beweislage fuer schwache Ansprueche verbessern\n"
            + "- [ ] Priorisierung der Ansprueche festlegen\n"
        )

        return self._write_output(LEGAL_CLAIMS / "CLAIM_MATRIX.md", output)

    async def _generate_opponent_analysis(self, doc_context: str) -> str:
        """L05: Generate opponent analysis."""
        prompt = f"""Analysiere die Gegenseite basierend auf den vorliegenden Dokumenten.

FALLKONTEXT: {self.case_context}

DOKUMENTE:
{doc_context}

ANFORDERUNGEN:
1. Argumentationsmuster der Gegenseite identifizieren
2. Widersprueche in den gegnerischen Aussagen/Dokumenten aufdecken
3. Angriffsflaechen und Schwachpunkte
4. Wahrscheinliche naechste Schritte der Gegenseite
5. Empfohlene Gegenstrategien

Erstelle die professionelle Gegneranalyse."""

        print("  Generiere Gegneranalyse mit Ollama ...", end=" ", flush=True)
        content = await self.ollama.generate(prompt, LEGAL_SYSTEM_PROMPT)
        print("OK")

        filenames = [d["filename"] for d in self._doc_texts[:10]]
        header = yaml_header("Gegneranalyse", "L05_Legal_OpponentAnalysis", filenames)

        output = (
            header
            + "# OPPONENT ANALYSIS — Gegneranalyse\n\n"
            + f"> Erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            + content
            + "\n\n## Next Actions\n"
            + "- [ ] Widersprueche dokumentieren und belegen\n"
            + "- [ ] Gegenstrategie mit Anwalt abstimmen\n"
        )

        return self._write_output(LEGAL_STRATEGY / "OPPONENT_ANALYSIS.md", output)

    async def _generate_risk_report(self, doc_context: str) -> str:
        """L06: Generate risk assessment."""
        prompt = f"""Erstelle eine professionelle Risikobewertung fuer den folgenden Fall.

FALLKONTEXT: {self.case_context}

DOKUMENTE:
{doc_context}

ANFORDERUNGEN:
1. Szenario-Modellierung:
   - BEST CASE: Alle eigenen Ansprueche erfolgreich → finanzielles Ergebnis
   - WORST CASE: Alle eigenen Ansprueche scheitern → finanzielles Ergebnis
   - MOST LIKELY: Gewichtet nach Beweislage → finanzielles Ergebnis
2. Kostenanalyse:
   - Geschaetzte Anwaltskosten
   - Gerichtskosten
   - Sachverstaendigenkosten
   - Zeitkosten
3. Decision Matrix:
   | Szenario | Wahrscheinlichkeit | Finanzielles Ergebnis | Netto (nach Kosten) |
4. Empfehlung: Klagen vs. Vergleichen vs. Aufgeben
5. Alle Zahlen als SCHAETZUNG markieren

Erstelle die professionelle Risikobewertung mit allen Tabellen."""

        print("  Generiere Risikobewertung mit Ollama ...", end=" ", flush=True)
        content = await self.ollama.generate(prompt, LEGAL_SYSTEM_PROMPT)
        print("OK")

        filenames = [d["filename"] for d in self._doc_texts[:10]]
        header = yaml_header("Risikobewertung / Risk Report", "L06_Legal_RiskOfficer", filenames)

        output = (
            header
            + "# RISK REPORT — Risikobewertung\n\n"
            + f"> Erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            + "> WICHTIG: Alle Zahlen sind Schaetzungen. Verifizierung mit Anwalt erforderlich.\n\n"
            + content
            + "\n\n## Next Actions\n"
            + "- [ ] Kostenschaetzung mit Anwalt abgleichen\n"
            + "- [ ] Streitwert pruefen\n"
            + "- [ ] Prozesskostenhilfe pruefen falls relevant\n"
        )

        return self._write_output(LEGAL_STRATEGY / "RISK_REPORT.md", output)

    async def _generate_settlement_plan(self, doc_context: str) -> str:
        """L07: Generate settlement strategy."""
        prompt = f"""Erstelle eine Vergleichsstrategie fuer den folgenden Fall.

FALLKONTEXT: {self.case_context}

DOKUMENTE:
{doc_context}

ANFORDERUNGEN:
1. EIGENE BATNA (Best Alternative To Negotiated Agreement)
2. GEGNERISCHE BATNA (geschaetzt)
3. ZOPA (Zone Of Possible Agreement)
4. Vergleichsvorschlaege (3 Varianten: minimal, fair, optimal)
5. Verhandlungstaktik und -reihenfolge
6. Red Lines (was ist nicht verhandelbar?)
7. Zeitdruck-Analyse: Wer hat mehr Zeitdruck?

Erstelle die professionelle Vergleichsstrategie."""

        print("  Generiere Vergleichsstrategie mit Ollama ...", end=" ", flush=True)
        content = await self.ollama.generate(prompt, LEGAL_SYSTEM_PROMPT)
        print("OK")

        filenames = [d["filename"] for d in self._doc_texts[:10]]
        header = yaml_header("Vergleichsstrategie", "L07_Legal_Settlement", filenames)

        output = (
            header
            + "# SETTLEMENT PLAN — Vergleichsstrategie\n\n"
            + f"> Erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            + content
            + "\n\n## Next Actions\n"
            + "- [ ] Vergleichsspielraum mit Anwalt festlegen\n"
            + "- [ ] Red Lines definieren\n"
            + "- [ ] Erstes Vergleichsangebot vorbereiten\n"
        )

        return self._write_output(LEGAL_STRATEGY / "SETTLEMENT_PLAN.md", output)

    async def _generate_consistency_report(self) -> str:
        """L09: Cross-check all generated outputs for consistency."""
        # Read all generated outputs
        outputs = {}
        for name, filepath in [
            ("Timeline", LEGAL_TIMELINE / "TIMELINE.md"),
            ("Evidence Map", LEGAL_EVIDENCE / "EVIDENCE_MAP.md"),
            ("Claims Matrix", LEGAL_CLAIMS / "CLAIM_MATRIX.md"),
            ("Opponent Analysis", LEGAL_STRATEGY / "OPPONENT_ANALYSIS.md"),
            ("Risk Report", LEGAL_STRATEGY / "RISK_REPORT.md"),
        ]:
            if filepath.exists():
                with open(filepath, "r") as f:
                    outputs[name] = f.read()[:5000]  # First 5000 chars per output

        if not outputs:
            return ""

        outputs_text = "\n\n---\n\n".join(
            f"### {name}\n{text}" for name, text in outputs.items()
        )

        prompt = f"""Fuehre einen Konsistenzcheck ueber alle bisherigen Analyseoutputs durch.

OUTPUTS:
{outputs_text}

ANFORDERUNGEN:
1. Widersprueche zwischen Timeline und Evidence Map?
2. Stimmen die Ansprueche in der Claims Matrix mit den Beweisen ueberein?
3. Ist die Risikobewertung konsistent mit der Beweislage?
4. Gibt es Luecken, die in keinem Output adressiert werden?
5. Bewertung: KONSISTENT / TEILWEISE KONSISTENT / WIDERSPRUECHE

Fuer jeden gefundenen Widerspruch: Genauer Verweis auf beide Stellen."""

        print("  Generiere Konsistenzpruefung mit Ollama ...", end=" ", flush=True)
        content = await self.ollama.generate(prompt, LEGAL_SYSTEM_PROMPT)
        print("OK")

        header = yaml_header(
            "Konsistenzpruefung",
            "L09_Legal_Consistency",
            list(outputs.keys()),
        )

        output = (
            header
            + "# CONSISTENCY REPORT — Konsistenzpruefung\n\n"
            + f"> Erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            + f"> Geprueft: {', '.join(outputs.keys())}\n\n"
            + content
            + "\n\n## Next Actions\n"
            + "- [ ] Widersprueche klaeren\n"
            + "- [ ] Betroffene Outputs aktualisieren\n"
        )

        return self._write_output(LEGAL_MEMOS / "CONSISTENCY_REPORT.md", output)

    async def _libra_cross_verify(self, doc_context: str) -> str:
        """Cross-verify local analysis with Libra Legal AI."""
        # Read local analysis outputs
        local_outputs = {}
        for name, filepath in [
            ("Timeline", LEGAL_TIMELINE / "TIMELINE.md"),
            ("Claims Matrix", LEGAL_CLAIMS / "CLAIM_MATRIX.md"),
            ("Risk Report", LEGAL_STRATEGY / "RISK_REPORT.md"),
        ]:
            if filepath.exists():
                with open(filepath, "r") as f:
                    local_outputs[name] = f.read()[:4000]

        local_summary = "\n\n".join(
            f"### {name}\n{text}" for name, text in local_outputs.items()
        )

        # Ask Libra to verify
        print("  Sende an Libra zur Cross-Verification ...", end=" ", flush=True)

        case_docs = []
        for doc in self._doc_texts[:5]:  # Limit to 5 docs for Libra
            case_docs.append({
                "filename": doc["filename"],
                "type": doc["type"],
                "text": doc["text"][:8000],
                "dates": doc["dates"][:5],
                "amounts": doc["amounts"][:5],
            })

        response = await self.libra.case_analysis(
            documents=case_docs,
            case_context=(
                f"{self.case_context}\n\n"
                f"BISHERIGE LOKALE ANALYSE (zur Verifizierung):\n{local_summary}"
            ),
            focus_areas=[
                "Fehler in der lokalen Analyse",
                "Fehlende rechtliche Aspekte",
                "Alternative Rechtsauffassungen",
                "Aktuelle Rechtsprechung",
            ],
        )
        print("OK")

        header = yaml_header(
            "Libra Cross-Verification",
            "Libra_Legal_AI",
            [d["filename"] for d in case_docs],
            confidence="high" if response.sources else "medium",
        )

        output = (
            header
            + "# LIBRA CROSS-VERIFICATION\n\n"
            + f"> Erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            + f"> Model: {response.model or 'Libra Legal AI'}\n"
            + f"> Quellen: {len(response.sources)}\n\n"
            + "## Libra-Analyse\n\n"
            + response.content
        )

        if response.sources:
            output += "\n\n## Quellen\n"
            for src in response.sources:
                if isinstance(src, dict):
                    output += f"- {src.get('title', '')} | {src.get('url', '')}\n"
                else:
                    output += f"- {src}\n"

        if response.warnings:
            output += "\n\n## Warnungen\n"
            for w in response.warnings:
                output += f"- {w}\n"

        output += (
            "\n\n## Next Actions\n"
            "- [ ] Abweichungen zwischen lokaler Analyse und Libra pruefen\n"
            "- [ ] Fehlende Rechtsprechung recherchieren\n"
            "- [ ] Ergebnisse mit Anwalt besprechen\n"
        )

        return self._write_output(LEGAL_MEMOS / "LIBRA_CROSS_CHECK.md", output)

    async def _generate_exec_brief(self) -> str:
        """L10: Generate executive summary."""
        # Read all outputs
        all_outputs = {}
        for name, filepath in [
            ("Timeline", LEGAL_TIMELINE / "TIMELINE.md"),
            ("Evidence", LEGAL_EVIDENCE / "EVIDENCE_MAP.md"),
            ("Claims", LEGAL_CLAIMS / "CLAIM_MATRIX.md"),
            ("Risk", LEGAL_STRATEGY / "RISK_REPORT.md"),
            ("Settlement", LEGAL_STRATEGY / "SETTLEMENT_PLAN.md"),
            ("Consistency", LEGAL_MEMOS / "CONSISTENCY_REPORT.md"),
            ("Libra Check", LEGAL_MEMOS / "LIBRA_CROSS_CHECK.md"),
        ]:
            if filepath.exists():
                with open(filepath, "r") as f:
                    all_outputs[name] = f.read()[:3000]

        outputs_text = "\n\n---\n\n".join(
            f"### {name}\n{text}" for name, text in all_outputs.items()
        )

        prompt = f"""Erstelle ein Executive Briefing (maximal 2 Seiten) fuer den Anwalt.

FALLKONTEXT: {self.case_context}

ANALYSE-ERGEBNISSE:
{outputs_text}

ANFORDERUNGEN:
1. Maximal 2 Seiten
2. Klare Struktur: Sachverhalt → Rechtslage → Risiken → Empfehlung
3. Entscheidungsvorlage: Was soll der Anwalt tun?
4. Top 5 Prioritaeten
5. Kritische Fristen (falls erkennbar)

Schreibe das Executive Briefing, bereit zur Uebergabe an den Anwalt."""

        print("  Generiere Executive Brief mit Ollama ...", end=" ", flush=True)
        content = await self.ollama.generate(prompt, LEGAL_SYSTEM_PROMPT)
        print("OK")

        header = yaml_header(
            "Executive Briefing fuer Rechtsanwalt",
            "L10_Legal_SummaryExec",
            list(all_outputs.keys()),
        )

        output = (
            header
            + "# EXECUTIVE BRIEF — Zusammenfassung fuer Rechtsanwalt\n\n"
            + f"> Erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            + f"> Fallkontext: {self.case_context[:200]}\n"
            + f"> Dokumente analysiert: {len(self._doc_texts)}\n"
            + "> **ENTWURF — Zur Pruefung und Freigabe durch Rechtsanwalt**\n\n"
            + content
            + "\n\n---\n\n"
            + "*Dieses Briefing wurde AI-gestuetzt erstellt und ersetzt keine Rechtsberatung. "
            + "Alle Aussagen sind zur Pruefung durch qualifizierten Rechtsanwalt vorgesehen.*\n"
        )

        return self._write_output(LEGAL_MEMOS / "EXEC_BRIEF.md", output)


# ── CLI ───────────────────────────────────────────────────────────────
async def main():
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "run":
        doc_path = sys.argv[2] if len(sys.argv) > 2 else None
        context = ""
        # Check for --context flag
        for i, arg in enumerate(sys.argv):
            if arg == "--context" and i + 1 < len(sys.argv):
                context = sys.argv[i + 1]

        if not context:
            context = input("Fallbeschreibung (kurz): ")

        analyzer = NASLegalAnalyzer(case_context=context)
        result = await analyzer.run_full_analysis(
            document_path=doc_path,
            use_libra=True,
        )

        if result.exec_brief_path:
            print(f"\n  Executive Brief: {result.exec_brief_path}")

    elif cmd == "status":
        processor = LegalDocProcessor()
        stats = processor.get_stats()
        print("\n=== Legal Analysis Status ===")
        print(f"Dokumente: {stats['total_documents']}")
        print(f"Eindeutige: {stats['unique_documents']}")
        print(f"Text extrahiert: {stats['total_text_chars']:,} Zeichen")

        # Check outputs
        print("\nGenerierte Outputs:")
        for name, filepath in [
            ("Timeline", LEGAL_TIMELINE / "TIMELINE.md"),
            ("Evidence Map", LEGAL_EVIDENCE / "EVIDENCE_MAP.md"),
            ("Claims Matrix", LEGAL_CLAIMS / "CLAIM_MATRIX.md"),
            ("Opponent Analysis", LEGAL_STRATEGY / "OPPONENT_ANALYSIS.md"),
            ("Risk Report", LEGAL_STRATEGY / "RISK_REPORT.md"),
            ("Settlement Plan", LEGAL_STRATEGY / "SETTLEMENT_PLAN.md"),
            ("Consistency", LEGAL_MEMOS / "CONSISTENCY_REPORT.md"),
            ("Libra Check", LEGAL_MEMOS / "LIBRA_CROSS_CHECK.md"),
            ("Exec Brief", LEGAL_MEMOS / "EXEC_BRIEF.md"),
        ]:
            exists = "vorhanden" if filepath.exists() else "fehlt"
            print(f"  [{exists:10}] {name}: {filepath.name}")

    elif cmd == "report":
        brief = LEGAL_MEMOS / "EXEC_BRIEF.md"
        if brief.exists():
            with open(brief, "r") as f:
                print(f.read())
        else:
            print("Noch kein Executive Brief vorhanden. Erst 'run' ausfuehren.")

    else:
        print("NAS Legal Analyzer — Vollstaendige Rechtsanalyse-Pipeline")
        print()
        print("Usage:")
        print("  python -m data.nas_legal_analyzer run [/pfad/zu/docs] [--context 'Beschreibung']")
        print("  python -m data.nas_legal_analyzer status")
        print("  python -m data.nas_legal_analyzer report")
        print()
        print("Beispiel:")
        print('  python -m data.nas_legal_analyzer run /home/user/legal-docs --context "Kuendigung durch AG"')


if __name__ == "__main__":
    asyncio.run(main())
