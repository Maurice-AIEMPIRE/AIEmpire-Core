"""
STEP 4 - THE REFINERY
Convergence loop: generate, score, diagnose, rewrite, re-score.
Stops when quality converges (score delta < threshold).
This is the step that turns good into great.
"""

import json
from typing import Dict, Tuple

SYSTEM_PROMPT = """Du bist ein Qualitaets-Optimizer. Dein Job: Iterativ verbessern.
Generiere v1, bewerte, diagnostiziere Schwaechen, schreibe um, bewerte erneut.
Stoppe wenn die Qualitaet konvergiert. Antworte IMMER als valides JSON."""

REFINE_PROMPT_TEMPLATE = """Starte den Convergence Loop fuer die Implementation.

ANALYST REVIEW (Step 3):
{analyst_result}

ARCHITECT BLUEPRINT (Step 2):
{architect_summary}

ITERATION: {iteration} von max {max_iterations}
VORHERIGER SCORE: {previous_score}

{iteration_context}

AUFGABE: Generiere/Verfeinere die Implementation.

OUTPUT als JSON:
{{
    "iteration": {iteration},
    "version": "v{iteration}",
    "implementation": {{
        "name": "Name der Automatisierung",
        "code_outline": "Pseudocode oder konkreter Code-Entwurf",
        "config_changes": ["Was in welcher Config aendern"],
        "new_files": ["Welche Dateien erstellen"],
        "modified_files": ["Welche bestehenden Dateien aendern"]
    }},
    "quality_scores": {{
        "completeness": <1-10>,
        "correctness": <1-10>,
        "simplicity": <1-10>,
        "robustness": <1-10>,
        "cost_efficiency": <1-10>,
        "overall": <1-10 Durchschnitt>
    }},
    "diagnosis": {{
        "weaknesses": ["Schwaeche 1", "Schwaeche 2"],
        "root_causes": ["Ursache 1", "Ursache 2"],
        "improvement_actions": ["Aktion 1", "Aktion 2"]
    }},
    "converged": <true wenn overall >= 8 ODER delta < 0.3>,
    "delta_from_previous": <score_change>,
    "refinement_summary": "Was wurde in dieser Iteration verbessert"
}}"""

MAX_ITERATIONS = 3
CONVERGENCE_THRESHOLD = 0.3
TARGET_SCORE = 8.0


def build_prompt(
    context: Dict,
    iteration: int = 1,
    previous_score: float = 0.0,
    previous_result: Dict = None,
) -> str:
    analyst = context.get("prior_steps", {}).get("analyst", {})
    architect = context.get("prior_steps", {}).get("architect", {})

    iteration_context = ""
    if previous_result:
        iteration_context = (
            f"VORHERIGE VERSION:\n"
            f"{json.dumps(previous_result.get('implementation', {}), indent=2, ensure_ascii=False)[:2000]}\n\n"
            f"VORHERIGE DIAGNOSE:\n"
            f"{json.dumps(previous_result.get('diagnosis', {}), indent=2, ensure_ascii=False)}\n\n"
            f"VERBESSERUNGS-ANWEISUNGEN: Behebe die diagnostizierten Schwaechen."
        )

    return REFINE_PROMPT_TEMPLATE.format(
        analyst_result=json.dumps(analyst, indent=2, ensure_ascii=False)[:3000],
        architect_summary=architect.get("summary", "No architect data"),
        iteration=iteration,
        max_iterations=MAX_ITERATIONS,
        previous_score=previous_score,
        iteration_context=iteration_context,
    )


def check_convergence(result: Dict, previous_score: float) -> Tuple[bool, float]:
    """Check if the refinement loop should stop."""
    scores = result.get("quality_scores", {})
    current = scores.get("overall", 0)
    delta = abs(current - previous_score)
    converged = current >= TARGET_SCORE or delta < CONVERGENCE_THRESHOLD
    return converged, current


def parse_result(raw: str) -> Dict:
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    try:
        data = json.loads(text.strip())
        data["step"] = "refinery"
        scores = data.get("quality_scores", {})
        data["summary"] = (
            f"Refinery v{data.get('iteration', '?')}: "
            f"score {scores.get('overall', '?')}/10, "
            f"converged={data.get('converged', False)}"
        )
        return data
    except json.JSONDecodeError:
        return {
            "step": "refinery",
            "summary": "Refinement completed (raw output)",
            "raw": raw,
            "parse_error": True,
        }
