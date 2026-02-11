#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

MODEL="${FREE_NETWORK_MODEL:-llama3.1:8b}"
HOST="${FREE_NETWORK_HOST:-127.0.0.1}"
PORT="${FREE_NETWORK_PORT:-8765}"
URL="http://${HOST}:${PORT}"
RUN_ID="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="$ROOT_DIR/automation/runs/free_network_${RUN_ID}"
mkdir -p "$OUT_DIR"

echo "# Free Network Live"
echo "run_id=$RUN_ID"
echo "model=$MODEL"
echo "url=$URL"

if ! command -v ollama >/dev/null 2>&1; then
  echo "ERROR: ollama not found. Install first: brew install ollama" >&2
  exit 2
fi

if ! curl -fsS "http://127.0.0.1:11434/api/tags" >/dev/null 2>&1; then
  echo "Starting ollama serve..."
  nohup ollama serve >"$OUT_DIR/ollama.log" 2>&1 &
  sleep 2
fi

if ! curl -fsS "http://127.0.0.1:11434/api/tags" >/dev/null 2>&1; then
  echo "ERROR: ollama server unreachable on 127.0.0.1:11434" >&2
  exit 3
fi

if ! ollama list | awk '{print $1}' | rg -x "$MODEL" >/dev/null 2>&1; then
  echo "Pulling model: $MODEL"
  ollama pull "$MODEL"
fi

echo "Starting web UI..."
echo "Logs: $OUT_DIR/free_network_server.log"
nohup python3 -m automation.free_network_server --host "$HOST" --port "$PORT" --model "$MODEL" \
  >"$OUT_DIR/free_network_server.log" 2>&1 &
SERVER_PID=$!

sleep 1
if ! curl -fsS "$URL/api/health" >"$OUT_DIR/health.json"; then
  echo "ERROR: web UI did not start correctly. Check: $OUT_DIR/free_network_server.log" >&2
  kill "$SERVER_PID" >/dev/null 2>&1 || true
  exit 4
fi

cat >"$OUT_DIR/README.txt" <<EOF
Free network started.
URL: $URL
PID: $SERVER_PID
Model: $MODEL

Stop:
kill $SERVER_PID
EOF

echo "Live ready: $URL"
echo "PID: $SERVER_PID"
echo "Health: $OUT_DIR/health.json"
echo "Session: $OUT_DIR/README.txt"

if command -v open >/dev/null 2>&1; then
  open "$URL" >/dev/null 2>&1 || true
fi
