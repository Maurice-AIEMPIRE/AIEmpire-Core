"""
STEP 2 - THE ARCHITECT
Plan before you build. Claude proposes multiple approaches,
ranks them by simplicity, and delivers a clear blueprint.
Feeds from: Step 1 (Audit) - knows what to automate.
"""

import json
from typing import Dict

SYSTEM_PROMPT = """Du bist ein System-Architekt fuer AI-gesteuerte Business Automation.
Du planst BEVOR gebaut wird. Mehrere Ansaetze, nach Einfachheit gerankt.
Liefere klare Blueprints. Antworte IMMER als valides JSON."""

ARCHITECT_PROMPT_TEMPLATE = """Basierend auf dem Audit-Ergebnis: Entwirf die Architektur.

AUDIT-ERGEBNIS (Step 1):
{audit_result}

VERFUEGBARE INFRASTRUKTUR:
- Python 3 + asyncio + aiohttp (async I/O)
- Kimi K2.5 API (256K context, $0.0005/1K tokens)
- Claude API (Haiku/Sonnet/Opus als Fallback)
- Ollama lokal (qwen2.5-coder:7b, kostenlos)
- OpenClaw Agent Framework (Cron Jobs, Skills)
- FastAPI (Atomic Reactor, Port 8888)
- Redis (Queue/Cache)
- PostgreSQL (Persistenz)
- n8n (Workflow Automation)

BEKANNTE PATTERNS:
{patterns}

AUFGABE: Fuer die TOP 3 Automatisierungen aus dem Audit,
entwirf je 2-3 Architektur-Ansaetze und ranke sie.

OUTPUT als JSON:
{{
    "architect_date": "YYYY-MM-DD",
    "automations": [
        {{
            "name": "Name der Automatisierung",
            "from_audit_task": "Referenz zum Audit-Task",
            "approaches": [
                {{
                    "name": "Ansatz A: ...",
                    "description": "Wie es funktioniert",
                    "stack": ["Tool1", "Tool2"],
                    "simplicity_score": 9,
                    "reliability_score": 8,
                    "cost_monthly": "0-5 EUR",
                    "setup_hours": 2,
                    "pros": ["Pro 1", "Pro 2"],
                    "cons": ["Con 1"],
                    "implementation_steps": [
                        "Schritt 1: ...",
                        "Schritt 2: ...",
                        "Schritt 3: ..."
                    ]
                }}
            ],
            "recommended_approach": "Ansatz A",
            "reason": "Warum dieser Ansatz"
        }}
    ],
    "blueprint_summary": "Gesamtplan in 3 Saetzen",
    "total_setup_hours": <number>,
    "total_monthly_cost": "X EUR",
    "dependencies": ["Was zuerst gebaut werden muss"],
    "risks": ["Risiko 1", "Risiko 2"],
    "critical_path": "Der eine Engpass der alles blockiert"
}}"""


def build_prompt(context: Dict) -> str:
    audit = context.get("prior_steps", {}).get("audit", {})
    audit_str = json.dumps(audit, indent=2, ensure_ascii=False)
    patterns = json.dumps(context.get("patterns", []), indent=2, ensure_ascii=False)
    return ARCHITECT_PROMPT_TEMPLATE.format(
        audit_result=audit_str[:3000] if len(audit_str) > 3000 else audit_str,
        patterns=patterns[:1000] if len(patterns) > 1000 else patterns,
    )


def parse_result(raw: str) -> Dict:
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    try:
        data = json.loads(text.strip())
        data["step"] = "architect"
        n = len(data.get("automations", []))
        data["summary"] = (
            f"Architecture complete: {n} automations designed, "
            f"{data.get('total_setup_hours', '?')}h total setup, "
            f"{data.get('total_monthly_cost', '?')} monthly"
        )
        return data
    except json.JSONDecodeError:
        return {
            "step": "architect",
            "summary": "Architecture completed (raw output)",
            "raw": raw,
            "parse_error": True,
        }
