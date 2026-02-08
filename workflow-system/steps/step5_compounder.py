"""
STEP 5 - THE COMPOUNDER
Weekly review that makes the system smarter.
Tracks what worked, what failed, what to automate next.
Builds a personal pattern library of effective workflows.
THIS is what makes the system compound over time.
"""

import json
from typing import Dict, List

SYSTEM_PROMPT = """Du bist der Meta-Optimizer. Du analysierst den gesamten Zyklus
und extrahierst Patterns die das System BESSER machen.
Jede Woche smarter. Compounding Intelligence.
Antworte IMMER als valides JSON."""

COMPOUNDER_PROMPT_TEMPLATE = """Fuehre das Weekly Compounding Review durch.

KOMPLETTER ZYKLUS-KONTEXT:
- Cycle #{cycle}
- Audit: {audit_summary}
- Architect: {architect_summary}
- Analyst: {analyst_summary}
- Refinery: {refinery_summary}

BISHERIGE PATTERN LIBRARY ({pattern_count} Patterns):
{existing_patterns}

BISHERIGE IMPROVEMENTS ({improvement_count} Eintraege):
{existing_improvements}

AUFGABE: Extrahiere was funktioniert hat, was nicht, und was
beim naechsten Zyklus anders laufen soll.

OUTPUT als JSON:
{{
    "review_date": "YYYY-MM-DD",
    "cycle": {cycle},
    "what_worked": [
        {{
            "description": "Was gut funktioniert hat",
            "why": "Warum es funktioniert hat",
            "pattern_name": "Kurzer Name fuer die Pattern Library",
            "reusable": true,
            "category": "automation|content|leads|revenue|process"
        }}
    ],
    "what_failed": [
        {{
            "description": "Was nicht funktioniert hat",
            "root_cause": "Ursache",
            "lesson": "Was wir daraus lernen",
            "avoid_pattern": "Anti-Pattern Name"
        }}
    ],
    "new_patterns": [
        {{
            "name": "Pattern Name",
            "description": "Was das Pattern macht",
            "when_to_use": "Wann anwenden",
            "implementation": "Wie implementieren",
            "expected_impact": "Erwarteter Effekt"
        }}
    ],
    "next_cycle_priorities": [
        {{
            "priority": 1,
            "task": "Was als naechstes",
            "why": "Warum",
            "expected_impact": "Erwarteter Effekt"
        }}
    ],
    "automation_candidates": [
        "Neuer Task der automatisiert werden sollte"
    ],
    "metrics": {{
        "cycle_effectiveness": <1-10>,
        "improvement_vs_last_cycle": "+/- X%",
        "compound_score": <Gesamtscore ueber alle Zyklen>
    }},
    "one_big_insight": "DIE eine Erkenntnis dieses Zyklus"
}}"""


def build_prompt(context: Dict) -> str:
    prior = context.get("prior_steps", {})
    return COMPOUNDER_PROMPT_TEMPLATE.format(
        cycle=context.get("cycle", 0),
        audit_summary=prior.get("audit", {}).get("summary", "N/A"),
        architect_summary=prior.get("architect", {}).get("summary", "N/A"),
        analyst_summary=prior.get("analyst", {}).get("summary", "N/A"),
        refinery_summary=prior.get("refinery", {}).get("summary", "N/A"),
        pattern_count=len(context.get("patterns", [])),
        existing_patterns=json.dumps(context.get("patterns", [])[-10:], indent=2, ensure_ascii=False)[:2000],
        improvement_count=len(context.get("improvements", [])),
        existing_improvements=json.dumps(context.get("improvements", [])[-5:], indent=2, ensure_ascii=False)[:1000],
    )


def extract_patterns(result: Dict) -> List[Dict]:
    """Extract new patterns for the persistent library."""
    return result.get("new_patterns", [])


def extract_priorities(result: Dict) -> List[Dict]:
    """Extract next-cycle priorities."""
    return result.get("next_cycle_priorities", [])


def parse_result(raw: str) -> Dict:
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    try:
        data = json.loads(text.strip())
        data["step"] = "compounder"
        metrics = data.get("metrics", {})
        data["summary"] = (
            f"Cycle #{data.get('cycle', '?')} review: "
            f"effectiveness {metrics.get('cycle_effectiveness', '?')}/10, "
            f"{len(data.get('new_patterns', []))} new patterns, "
            f"insight: {data.get('one_big_insight', 'N/A')[:80]}"
        )
        return data
    except json.JSONDecodeError:
        return {
            "step": "compounder",
            "summary": "Compounding review completed (raw output)",
            "raw": raw,
            "parse_error": True,
        }
