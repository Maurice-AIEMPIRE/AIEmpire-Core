#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_DIR"

EXECUTE=0
TIER="cheap"
TASK_TYPE="strategy"
AGENTS_PER_WAVE=10
BASE_PROMPT="Baue heute Umsatz und Autoritaet: bessere Angebote, besseren Content, bessere Automationen."
MAX_OUTPUT_TOKENS=280
ROUTER_CONFIG="automation/config/router_local.json"
USE_LOCAL=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --execute)
      EXECUTE=1
      shift
      ;;
    --tier)
      TIER="$2"
      shift 2
      ;;
    --task-type)
      TASK_TYPE="$2"
      shift 2
      ;;
    --agents-per-wave)
      AGENTS_PER_WAVE="$2"
      shift 2
      ;;
    --prompt)
      BASE_PROMPT="$2"
      shift 2
      ;;
    --max-output-tokens)
      MAX_OUTPUT_TOKENS="$2"
      shift 2
      ;;
    --router-config)
      ROUTER_CONFIG="$2"
      USE_LOCAL=0
      shift 2
      ;;
    --cloud)
      ROUTER_CONFIG="automation/config/router.json"
      USE_LOCAL=0
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ "$USE_LOCAL" -eq 1 ]]; then
  export OLLAMA_API_KEY="${OLLAMA_API_KEY:-local}"
  export MISSION_MAX_WORKERS="${MISSION_MAX_WORKERS:-3}"
fi

run_wave() {
  local wave="$1"
  local label="$2"
  local objective="$3"
  local run_id
  run_id="legion50_w${wave}_$(date +%Y%m%d_%H%M%S)_$RANDOM"

  echo ""
  echo "=== Wave $wave/5: $label ==="

  local prompt
  prompt="$BASE_PROMPT

WAVE $wave - $label
$objective

Liefere konkrete, umsetzbare Outputs mit Prioritaet P1/P2/P3, Risikohinweisen und naechsten 3 Schritten."

  local cmd=(python3 -m automation.mission_control multi-chat
    --prompt "$prompt"
    --task-type "$TASK_TYPE"
    --tier "$TIER"
    --agents "$AGENTS_PER_WAVE"
    --max-output-tokens "$MAX_OUTPUT_TOKENS"
    --router-config "$ROUTER_CONFIG"
    --run-id "$run_id"
    --diversify)

  if [[ "$EXECUTE" -eq 1 ]]; then
    cmd+=(--execute)
  fi

  "${cmd[@]}"
}

run_wave 1 "Intelligence" "Analysiere Nachfrage, Zielgruppe, Kaufmotive, Einwaende und Chancen im aktuellen Markt."
run_wave 2 "Offer & Sales" "Baue bessere Angebote, Preislogik, DM-Skripte, CTA-Varianten und Closing-Argumente."
run_wave 3 "Content Engine" "Erstelle hochkonvertierenden Content-Plan fuer Longform, Shortform und Distribution."
run_wave 4 "Automation" "Definiere Workflows, Trigger, SOPs und Stabilitaetschecks fuer taeglichen Betrieb."
run_wave 5 "Quality & Command" "Fuehre QA, KPI-Review, Priorisierung und 24h-Execution-Plan zusammen."

echo ""
echo "=== Legion Run Complete ==="
python3 -m automation.mission_control status
