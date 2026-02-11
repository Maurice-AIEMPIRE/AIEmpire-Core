"""
STEP 3 - THE ANALYST
Structured engineering review - not vague feedback.
Evaluates architecture, code quality, reliability, performance.
Every issue includes tradeoffs, options, and recommendations.
Feeds from: Step 2 (Architect) blueprint.
"""

import json
from typing import Dict

SYSTEM_PROMPT = """Du bist ein Senior Engineering Reviewer.
Kein Lob, keine vagen Kommentare. Nur strukturierte Analyse.
Jedes Issue: Tradeoff + Optionen + Empfehlung.
Antworte IMMER als valides JSON."""

ANALYST_PROMPT_TEMPLATE = """Fuehre ein strukturiertes Engineering Review der Architektur durch.

ARCHITEKTUR-BLUEPRINT (Step 2):
{architect_result}

AUDIT-KONTEXT (Step 1):
{audit_summary}

BESTEHENDER CODE IM REPO:
- atomic-reactor/run_tasks.py: Async task execution mit Kimi API
- kimi-swarm/swarm_500k.py: 500K Agent Swarm mit Claude Orchestration
- x-lead-machine/: Content + Lead Generation (4 Python Module)
- crm/server.js: Express.js CRM mit SQLite + Socket.io
- openclaw-config/: 9 Cron Jobs, Kimi K2.5 Model Config

AUFGABE: Bewerte JEDEN vorgeschlagenen Ansatz auf 5 Dimensionen.

OUTPUT als JSON:
{{
    "review_date": "YYYY-MM-DD",
    "reviews": [
        {{
            "automation_name": "Name",
            "recommended_approach": "Ansatz X",
            "scores": {{
                "architecture": {{
                    "score": 8,
                    "strengths": ["..."],
                    "issues": [
                        {{
                            "severity": "high|medium|low",
                            "description": "Was ist das Problem",
                            "tradeoff": "Was verliert man vs. was gewinnt man",
                            "options": ["Option A", "Option B"],
                            "recommendation": "Empfohlene Loesung"
                        }}
                    ]
                }},
                "code_quality": {{
                    "score": 7,
                    "issues": [...]
                }},
                "reliability": {{
                    "score": 8,
                    "issues": [...]
                }},
                "performance": {{
                    "score": 7,
                    "issues": [...]
                }},
                "cost_efficiency": {{
                    "score": 9,
                    "issues": [...]
                }}
            }},
            "overall_score": 7.8,
            "go_no_go": "GO|NO-GO|CONDITIONAL",
            "conditions": ["Bedingung fuer GO falls CONDITIONAL"],
            "quick_wins": ["Sofort umsetzbare Verbesserung"]
        }}
    ],
    "critical_blockers": ["Was MUSS gefixt werden bevor irgendwas gebaut wird"],
    "integration_risks": ["Risiken bei der Integration der Systeme"],
    "recommended_build_order": ["Was zuerst", "Was zweitens", "Was drittens"],
    "analyst_verdict": "1-2 Saetze Gesamturteil"
}}"""


def build_prompt(context: Dict) -> str:
    architect = context.get("prior_steps", {}).get("architect", {})
    audit = context.get("prior_steps", {}).get("audit", {})
    return ANALYST_PROMPT_TEMPLATE.format(
        architect_result=json.dumps(architect, indent=2, ensure_ascii=False)[:4000],
        audit_summary=audit.get("summary", "No audit data"),
    )


def parse_result(raw: str) -> Dict:
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    try:
        data = json.loads(text.strip())
        data["step"] = "analyst"
        reviews = data.get("reviews", [])
        go_count = sum(1 for r in reviews if r.get("go_no_go") == "GO")
        data["summary"] = (
            f"Review complete: {len(reviews)} automations reviewed, "
            f"{go_count} GO, verdict: {data.get('analyst_verdict', 'N/A')}"
        )
        return data
    except json.JSONDecodeError:
        return {
            "step": "analyst",
            "summary": "Analysis completed (raw output)",
            "raw": raw,
            "parse_error": True,
        }
