#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [ -f "$ROOT_DIR/ai-vault/empire.env" ]; then
  # shellcheck disable=SC1090
  source "$ROOT_DIR/ai-vault/empire.env"
fi
if [ -f "$HOME/.openclaw/.env" ]; then
  # shellcheck disable=SC1090
  source "$HOME/.openclaw/.env"
fi

LOOKBACK_HOURS="${1:-${STRIPE_LOOKBACK_HOURS:-24}}"
MAX_RECORDS="${2:-${STRIPE_MAX_RECORDS:-200}}"

python3 -m automation.stripe_sync --lookback-hours "$LOOKBACK_HOURS" --max-records "$MAX_RECORDS"
