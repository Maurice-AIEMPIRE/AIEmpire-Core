"""
Libra Legal AI Connector
==========================
Integrates with Libra (libratech.ai) — the AI Workspace for Legal Professionals.

Features:
  - Legal research queries (German law, EU law)
  - Document analysis and review
  - Contract review with risk flagging
  - Case law research
  - Legal drafting assistance
  - Deep thinking mode for complex legal reasoning

Security: Libra is ISO 27001 certified, GDPR compliant, hosted in EEA.
Legal documents sent to Libra are processed within the EEA.

Usage:
    from data.libra_connector import LibraConnector

    libra = LibraConnector()

    # Legal research query
    result = await libra.research("Kuendigungsschutz bei Krankheit nach KSchG")

    # Analyze a document
    result = await libra.analyze_document(text, "Pruefe diesen Vertrag auf Risiken")

    # Full case analysis
    result = await libra.case_analysis(documents, case_context)
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


PROJECT_ROOT = Path(__file__).parent.parent
LIBRA_LOG_DIR = PROJECT_ROOT / "data" / "libra_logs"


@dataclass
class LibraConfig:
    """Configuration for Libra API."""
    api_key: str = ""
    base_url: str = "https://api.libratech.ai/v1"
    # Alternative endpoints
    chat_endpoint: str = "/chat/completions"
    analyze_endpoint: str = "/analyze"
    research_endpoint: str = "/research"
    # Model selection
    model: str = "libra-legal"  # Default Libra model
    # Settings
    max_tokens: int = 8192
    temperature: float = 0.1  # Low temperature for legal precision
    deep_thinking: bool = True  # Enable deep reasoning mode
    language: str = "de"  # German legal context
    # Rate limiting
    max_requests_per_minute: int = 20  # Free tier limit
    timeout_seconds: int = 120

    @classmethod
    def from_env(cls) -> "LibraConfig":
        """Load config from environment variables."""
        return cls(
            api_key=get_api_key("LIBRA_API_KEY"),
            base_url=get_api_key("LIBRA_BASE_URL") or "https://api.libratech.ai/v1",
            model=get_api_key("LIBRA_MODEL") or "libra-legal",
        )


@dataclass
class LibraResponse:
    """Structured response from Libra API."""
    content: str
    sources: list[dict] = field(default_factory=list)
    confidence: str = "medium"
    model: str = ""
    tokens_used: int = 0
    processing_time_ms: int = 0
    warnings: list[str] = field(default_factory=list)


class LibraConnector:
    """
    Connector for Libra Legal AI workspace.

    Handles API communication, rate limiting, response parsing,
    and logging for audit trail.
    """

    def __init__(self, config: Optional[LibraConfig] = None):
        self.config = config or LibraConfig.from_env()
        self._request_times: list[float] = []
        LIBRA_LOG_DIR.mkdir(parents=True, exist_ok=True)

    def validate_config(self) -> tuple[bool, str]:
        """Check if Libra config is valid."""
        if not self.config.api_key:
            return False, (
                "LIBRA_API_KEY nicht gesetzt. "
                "Erstelle einen API Key unter: https://app.libratech.ai/settings/api-keys "
                "und trage ihn in .env ein."
            )
        return True, "OK"

    def _check_rate_limit(self):
        """Enforce rate limiting."""
        now = time.time()
        # Remove requests older than 60 seconds
        self._request_times = [t for t in self._request_times if now - t < 60]
        if len(self._request_times) >= self.config.max_requests_per_minute:
            wait_time = 60 - (now - self._request_times[0])
            if wait_time > 0:
                print(f"  [RATE LIMIT] Warte {wait_time:.0f}s ...")
                time.sleep(wait_time)

    def _log_request(self, request_type: str, prompt: str, response: LibraResponse):
        """Log API request for audit trail."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": request_type,
            "prompt_preview": prompt[:200],
            "response_length": len(response.content),
            "sources_count": len(response.sources),
            "confidence": response.confidence,
            "model": response.model,
            "tokens": response.tokens_used,
            "time_ms": response.processing_time_ms,
        }
        log_file = LIBRA_LOG_DIR / f"libra_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    async def _api_call(
        self,
        messages: list[dict],
        system_prompt: str = "",
        endpoint: str = "",
    ) -> LibraResponse:
        """Make an API call to Libra."""
        import httpx

        valid, msg = self.validate_config()
        if not valid:
            return LibraResponse(content=f"[FEHLER] {msg}", confidence="none")

        self._check_rate_limit()

        url = f"{self.config.base_url}{endpoint or self.config.chat_endpoint}"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }

        if system_prompt:
            payload["messages"] = [
                {"role": "system", "content": system_prompt},
                *messages,
            ]

        if self.config.deep_thinking:
            payload["metadata"] = {"deep_thinking": True}

        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                resp = await client.post(url, json=payload, headers=headers)
                self._request_times.append(time.time())

                if resp.status_code == 200:
                    data = resp.json()
                    content = ""
                    sources = []
                    tokens = 0

                    # Parse OpenAI-compatible response format
                    if "choices" in data:
                        choice = data["choices"][0]
                        content = choice.get("message", {}).get("content", "")
                    elif "content" in data:
                        content = data["content"]
                    elif "response" in data:
                        content = data["response"]

                    # Extract sources if available
                    if "sources" in data:
                        sources = data["sources"]
                    elif "citations" in data:
                        sources = data["citations"]

                    # Token usage
                    usage = data.get("usage", {})
                    tokens = usage.get("total_tokens", 0)

                    elapsed_ms = int((time.time() - start_time) * 1000)

                    return LibraResponse(
                        content=content,
                        sources=sources,
                        confidence="high" if sources else "medium",
                        model=data.get("model", self.config.model),
                        tokens_used=tokens,
                        processing_time_ms=elapsed_ms,
                    )
                elif resp.status_code == 429:
                    return LibraResponse(
                        content="[RATE LIMIT] Libra API Rate Limit erreicht. Bitte spaeter erneut versuchen.",
                        confidence="none",
                        warnings=["Rate limit exceeded"],
                    )
                elif resp.status_code == 401:
                    return LibraResponse(
                        content="[AUTH FEHLER] Libra API Key ungueltig oder abgelaufen.",
                        confidence="none",
                        warnings=["Authentication failed"],
                    )
                else:
                    error_text = resp.text[:500]
                    return LibraResponse(
                        content=f"[API FEHLER] Status {resp.status_code}: {error_text}",
                        confidence="none",
                        warnings=[f"HTTP {resp.status_code}"],
                    )

        except httpx.TimeoutException:
            return LibraResponse(
                content="[TIMEOUT] Libra API Anfrage hat zu lange gedauert.",
                confidence="none",
                warnings=["Timeout"],
            )
        except Exception as e:
            return LibraResponse(
                content=f"[FEHLER] Libra API Verbindungsfehler: {e}",
                confidence="none",
                warnings=[str(e)],
            )

    # ── Public API Methods ────────────────────────────────────────────

    async def research(self, query: str, context: str = "") -> LibraResponse:
        """
        Legal research query to Libra.

        Args:
            query: The legal research question (German or English)
            context: Additional context (case details, relevant facts)
        """
        system_prompt = (
            "Du bist ein deutscher Rechtsexperte. Beantworte die Frage praezise "
            "mit Verweis auf relevante Gesetze, Paragraphen und Rechtsprechung. "
            "Nenne immer die Quelle (Gesetz, Paragraph, Urteil mit Aktenzeichen). "
            "Wenn du unsicher bist, kennzeichne es als [NEEDS VERIFICATION]."
        )

        messages = []
        if context:
            messages.append({"role": "user", "content": f"Kontext:\n{context}"})
        messages.append({"role": "user", "content": query})

        response = await self._api_call(messages, system_prompt)
        self._log_request("research", query, response)
        return response

    async def analyze_document(
        self,
        document_text: str,
        instruction: str = "",
        document_type: str = "general",
    ) -> LibraResponse:
        """
        Analyze a legal document with Libra.

        Args:
            document_text: The extracted text of the document
            instruction: What to look for (risks, claims, obligations, etc.)
            document_type: Type hint (CONTRACT, EMAIL, COURT, etc.)
        """
        if not instruction:
            instruction = (
                "Analysiere dieses Dokument vollstaendig: "
                "1) Zusammenfassung, 2) Kernaussagen, 3) Rechtliche Risiken, "
                "4) Relevante Paragraphen, 5) Handlungsempfehlungen."
            )

        system_prompt = (
            "Du bist ein spezialisierter Rechtsanalyst. Analysiere das folgende "
            f"Dokument (Typ: {document_type}) praezise und strukturiert. "
            "Jede Behauptung muss auf eine konkrete Textstelle verweisen. "
            "Kennzeichne Risiken mit Schweregrad (HOCH/MITTEL/NIEDRIG)."
        )

        # Truncate very long documents
        max_chars = 50000
        if len(document_text) > max_chars:
            document_text = document_text[:max_chars] + "\n\n[... DOKUMENT GEKUERZT ...]"

        messages = [
            {"role": "user", "content": f"{instruction}\n\n---\n\nDOKUMENT:\n{document_text}"},
        ]

        response = await self._api_call(messages, system_prompt)
        self._log_request("analyze_document", instruction, response)
        return response

    async def case_analysis(
        self,
        documents: list[dict],
        case_context: str,
        focus_areas: Optional[list[str]] = None,
    ) -> LibraResponse:
        """
        Full case analysis across multiple documents.

        Args:
            documents: List of {filename, type, text, dates, entities} dicts
            case_context: Description of the case/dispute
            focus_areas: Specific areas to focus on (e.g., ["Kuendigungsschutz", "Schadensersatz"])
        """
        if focus_areas is None:
            focus_areas = []

        system_prompt = (
            "Du fuehrst eine vollstaendige Fallanalyse durch. "
            "Erstelle: 1) Chronologische Timeline aller Ereignisse, "
            "2) Beweiswuerdigung pro Dokument, 3) Anspruchsmatrix (eigene Ansprueche + "
            "Gegenansprueche + Beweislage + Risiko), 4) Strategieempfehlung. "
            "Jede Aussage muss auf ein konkretes Dokument verweisen. "
            "Format: Strukturiertes Markdown mit klaren Abschnitten."
        )

        # Build document summary
        doc_summaries = []
        total_chars = 0
        for i, doc in enumerate(documents, 1):
            text = doc.get("text", "")
            # Budget text per document to stay within limits
            max_per_doc = min(10000, 80000 // max(len(documents), 1))
            if len(text) > max_per_doc:
                text = text[:max_per_doc] + " [...]"

            summary = (
                f"### Dokument {i}: {doc.get('filename', 'Unbekannt')}\n"
                f"Typ: {doc.get('type', 'OTHER')}\n"
                f"Daten gefunden: {', '.join(doc.get('dates', [])[:5])}\n"
                f"Betraege: {', '.join(doc.get('amounts', [])[:5])}\n\n"
                f"{text}\n"
            )
            doc_summaries.append(summary)
            total_chars += len(summary)

        focus_text = ""
        if focus_areas:
            focus_text = f"\n\nFokus-Bereiche: {', '.join(focus_areas)}"

        messages = [
            {
                "role": "user",
                "content": (
                    f"FALLBESCHREIBUNG:\n{case_context}\n{focus_text}\n\n"
                    f"DOKUMENTE ({len(documents)} Stueck):\n\n"
                    + "\n---\n".join(doc_summaries)
                    + "\n\nErstelle jetzt die vollstaendige Fallanalyse."
                ),
            },
        ]

        response = await self._api_call(messages, system_prompt)
        self._log_request("case_analysis", case_context[:200], response)
        return response

    async def draft_document(
        self,
        document_type: str,
        context: str,
        tone: str = "formal",
    ) -> LibraResponse:
        """
        Draft a legal document (letter, motion, memo, etc.).

        Args:
            document_type: E.g., "Abmahnung", "Widerspruch", "Vergleichsangebot"
            context: What the document should address
            tone: "formal", "assertive", "diplomatic"
        """
        system_prompt = (
            f"Du erstellst einen professionellen Entwurf fuer: {document_type}. "
            f"Ton: {tone}. Verwende korrektes juristisches Deutsch. "
            "Markiere den Entwurf als ENTWURF — KEINE RECHTSBERATUNG im Header. "
            "Fuege Platzhalter [NAME], [DATUM], [ADRESSE] ein wo noetig."
        )

        messages = [{"role": "user", "content": context}]
        response = await self._api_call(messages, system_prompt)
        self._log_request("draft", f"{document_type}: {context[:100]}", response)
        return response

    async def risk_assessment(
        self,
        claims: list[dict],
        evidence_summary: str,
    ) -> LibraResponse:
        """
        Perform a legal risk assessment.

        Args:
            claims: List of {claim, evidence, strength} dicts
            evidence_summary: Summary of available evidence
        """
        system_prompt = (
            "Du erstellst eine professionelle Risikobewertung. "
            "Bewerte jede Position mit: Erfolgswahrscheinlichkeit (%), "
            "finanzielles Risiko (Best/Worst/Likely Case), "
            "und empfohlene Strategie (Klagen/Vergleichen/Aufgeben). "
            "Beruecksichtige Prozesskosten und Zeitfaktor."
        )

        claims_text = ""
        for i, claim in enumerate(claims, 1):
            claims_text += (
                f"\n{i}. Anspruch: {claim.get('claim', '')}\n"
                f"   Beweis: {claim.get('evidence', '')}\n"
                f"   Staerke: {claim.get('strength', 'unbekannt')}\n"
            )

        messages = [
            {
                "role": "user",
                "content": (
                    f"ANSPRUECHE:\n{claims_text}\n\n"
                    f"BEWEISLAGE:\n{evidence_summary}\n\n"
                    "Erstelle die Risikobewertung mit Decision Matrix."
                ),
            },
        ]

        response = await self._api_call(messages, system_prompt)
        self._log_request("risk_assessment", f"{len(claims)} claims", response)
        return response

    async def check_health(self) -> dict:
        """Check if Libra API is reachable and authenticated."""
        valid, msg = self.validate_config()
        if not valid:
            return {"status": "error", "message": msg}

        try:
            import httpx

            url = f"{self.config.base_url}/models"
            headers = {"Authorization": f"Bearer {self.config.api_key}"}

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    return {"status": "ok", "models": resp.json()}
                elif resp.status_code == 401:
                    return {"status": "auth_error", "message": "API Key ungueltig"}
                else:
                    return {"status": "error", "message": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"status": "connection_error", "message": str(e)}

    def get_usage_stats(self) -> dict:
        """Get usage statistics from log files."""
        stats = {"total_requests": 0, "total_tokens": 0, "by_type": {}}
        log_pattern = LIBRA_LOG_DIR / "libra_*.jsonl"

        for log_file in sorted(LIBRA_LOG_DIR.glob("libra_*.jsonl")):
            try:
                with open(log_file, "r") as f:
                    for line in f:
                        entry = json.loads(line)
                        stats["total_requests"] += 1
                        stats["total_tokens"] += entry.get("tokens", 0)
                        req_type = entry.get("type", "unknown")
                        stats["by_type"][req_type] = stats["by_type"].get(req_type, 0) + 1
            except Exception:
                continue

        return stats


# ── CLI ───────────────────────────────────────────────────────────────
async def main():
    import sys

    libra = LibraConnector()

    valid, msg = libra.validate_config()
    if not valid:
        print(f"\n[CONFIG] {msg}")
        print("\nSetup:")
        print("  1. Gehe zu https://app.libratech.ai/settings/api-keys")
        print("  2. Erstelle einen neuen API Key")
        print("  3. Trage in .env ein: LIBRA_API_KEY=dein-key-hier")
        return

    cmd = sys.argv[1] if len(sys.argv) > 1 else "health"

    if cmd == "health":
        health = await libra.check_health()
        print(f"Libra Status: {health['status']}")
        if health.get("message"):
            print(f"  {health['message']}")

    elif cmd == "research" and len(sys.argv) > 2:
        query = " ".join(sys.argv[2:])
        print(f"[LIBRA] Recherche: {query}\n")
        result = await libra.research(query)
        print(result.content)
        if result.sources:
            print(f"\nQuellen: {len(result.sources)}")

    elif cmd == "stats":
        stats = libra.get_usage_stats()
        print(f"Requests gesamt: {stats['total_requests']}")
        print(f"Tokens gesamt: {stats['total_tokens']}")
        for req_type, count in stats["by_type"].items():
            print(f"  {req_type}: {count}")

    else:
        print("Usage:")
        print("  python -m data.libra_connector health")
        print("  python -m data.libra_connector research <frage>")
        print("  python -m data.libra_connector stats")


if __name__ == "__main__":
    asyncio.run(main())
