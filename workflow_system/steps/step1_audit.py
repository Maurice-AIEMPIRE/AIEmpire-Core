"""
STEP 1 - THE AUDIT
Turn the AI into a productivity analyst that maps your workflow.
Scores tasks by: time spent, mental energy drain, automation feasibility.
Output: prioritized 4-week automation plan with clear setup steps.
"""

import json
from typing import Dict

SYSTEM_PROMPT = """Du bist ein Elite Productivity Analyst fuer Maurice's AI Empire.
Dein Job: Identifiziere was WIRKLICH Zeit und Energie frisst.
Sei brutal ehrlich. Keine Schoenrederei.
Antworte IMMER als valides JSON."""

AUDIT_PROMPT_TEMPLATE = """Fuehre ein umfassendes Workflow-Audit durch.

AKTUELLER KONTEXT:
{prior_context}

BESTEHENDE SYSTEME:
- OpenClaw (AI Agent, 9 Cron Jobs, Port 18789)
- Kimi Swarm (50K-500K Agents, Moonshot API)
- Atomic Reactor (Task Orchestration, Port 8888)
- CRM System (Express.js + SQLite, Port 3500)
- X/Twitter Lead Machine (Content + Leads)
- Gumroad (1 Produkt: AI Prompt Vault, 27 EUR)
- Fiverr/Upwork (0 aktive Gigs)

BEKANNTE PATTERNS AUS FRUEHEREN ZYKLEN:
{patterns}

AUFGABE: Analysiere ALLE wiederkehrenden Tasks und bewerte sie:

Fuer JEDEN Task liefere:
1. task_name: Was wird gemacht
2. frequency: Wie oft (taeglich/woechentlich/monatlich)
3. time_hours: Geschaetzter Zeitaufwand pro Woche
4. energy_drain: 1-10 (10 = total erschoepfend)
5. automation_feasibility: 1-10 (10 = sofort automatisierbar)
6. automation_approach: WIE automatisieren (konkretes Tool/Agent)
7. priority_score: (energy_drain * automation_feasibility) / time_hours
8. estimated_setup_hours: Wie lange dauert die Automatisierung

OUTPUT als JSON:
{{
    "audit_date": "YYYY-MM-DD",
    "total_weekly_hours_manual": <number>,
    "total_weekly_hours_after_automation": <number>,
    "time_savings_percent": <number>,
    "tasks": [<task objects sorted by priority_score DESC>],
    "four_week_plan": {{
        "week_1": {{
            "focus": "Quick Wins",
            "tasks_to_automate": ["task1", "task2"],
            "expected_time_saved": "<X> hours/week",
            "setup_effort": "<Y> hours"
        }},
        "week_2": {{ ... }},
        "week_3": {{ ... }},
        "week_4": {{ ... }}
    }},
    "critical_insight": "Die EINE Erkenntnis die alles aendert",
    "biggest_time_waste": "Der groesste Zeitfresser",
    "highest_roi_automation": "Die Automatisierung mit dem besten ROI"
}}"""


def build_prompt(context: Dict) -> str:
    prior = json.dumps(context.get("prior_steps", {}), indent=2, ensure_ascii=False)
    patterns = json.dumps(context.get("patterns", []), indent=2, ensure_ascii=False)
    return AUDIT_PROMPT_TEMPLATE.format(
        prior_context=prior[:2000] if len(prior) > 2000 else prior,
        patterns=patterns[:1000] if len(patterns) > 1000 else patterns,
    )


def parse_result(raw: str) -> Dict:
    """Extract JSON from model response."""
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    try:
        data = json.loads(text.strip())
        data["step"] = "audit"
        data["summary"] = (
            f"Audit complete: {data.get('total_weekly_hours_manual', '?')}h manual -> "
            f"{data.get('total_weekly_hours_after_automation', '?')}h automated "
            f"({data.get('time_savings_percent', '?')}% savings)"
        )
        return data
    except json.JSONDecodeError:
        return {
            "step": "audit",
            "summary": "Audit completed (raw output)",
            "raw": raw,
            "parse_error": True,
        }
