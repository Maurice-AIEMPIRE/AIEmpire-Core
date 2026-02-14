#!/bin/zsh
set -euo pipefail

LOG_DIR="$HOME/AIEmpire-Core/03_LOGS"
mkdir -p "$LOG_DIR"

echo "$(date '+%F %T') [whisperwatch] START (pid=$$)"

while true; do
  echo "$(date '+%F %T') [whisperwatch] heartbeat"
  sleep 10
done
