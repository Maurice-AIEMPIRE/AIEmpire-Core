#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/Users/maurice/Documents/New project"
ENV_FILE="$REPO_DIR/ai-vault/empire.env"

# Shared secrets live in OpenClaw's env.
if [ -f "$HOME/.openclaw/.env" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$HOME/.openclaw/.env"
  set +a
fi

cd "$REPO_DIR"

if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

/usr/bin/env python3 -m automation.report --send
/bin/bash "$REPO_DIR/automation/scripts/run_income_stream_report.sh" send || true
