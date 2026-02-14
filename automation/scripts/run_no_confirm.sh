#!/usr/bin/env bash
set -euo pipefail

# Non-interactive wrapper for terminal automation tasks.
# Usage:
#   automation/scripts/run_no_confirm.sh git pull
#   AUTO_CONFIRM=1 automation/scripts/run_no_confirm.sh some-command

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <command> [args...]" >&2
  exit 1
fi

export CI=1
export GIT_TERMINAL_PROMPT=0
export PYTHONUNBUFFERED=1

if [ "${AUTO_CONFIRM:-0}" = "1" ]; then
  yes | "$@"
else
  "$@"
fi
