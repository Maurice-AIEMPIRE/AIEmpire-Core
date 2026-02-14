#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

PROFILE="${JARVIS_PROFILE:-$ROOT_DIR/automation/config/jarvis_profile.json}"
HOST="${JARVIS_HOST:-0.0.0.0}"
PORT="${JARVIS_PORT:-8877}"
MODEL="${JARVIS_MODEL:-${OLLAMA_PRIMARY_MODEL:-minimax-m2.5:cloud}}"
OLLAMA_URL="${JARVIS_OLLAMA_URL:-http://127.0.0.1:11434}"
TOKEN="${JARVIS_TOKEN:-}"
NO_TTS="${JARVIS_NO_TTS:-0}"
EXECUTE="${JARVIS_EXECUTE:-0}"

RUN_ID="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="$ROOT_DIR/automation/runs/jarvis_${RUN_ID}"
mkdir -p "$OUT_DIR"

if [[ ! -f "$PROFILE" ]]; then
  echo "Profile missing, writing default profile: $PROFILE"
  python3 -m automation.jarvis --profile "$PROFILE" init-profile
fi

echo "# Jarvis Live"
echo "run_id=$RUN_ID"
echo "profile=$PROFILE"
echo "host=$HOST"
echo "port=$PORT"
echo "model=$MODEL"

if ! command -v ollama >/dev/null 2>&1; then
  echo "WARN: ollama not found. Install for local QA mode: brew install ollama"
else
  if ! curl -fsS "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
    echo "Starting ollama serve..."
    nohup ollama serve >"$OUT_DIR/ollama.log" 2>&1 &
    sleep 2
  fi

  if curl -fsS "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
    if ! ollama list | awk '{print $1}' | rg -x "$MODEL" >/dev/null 2>&1; then
      echo "Pulling model: $MODEL"
      ollama pull "$MODEL" || true
    fi
  else
    echo "WARN: Ollama backend not reachable at $OLLAMA_URL"
  fi
fi

CMD=(python3 -m automation.jarvis --profile "$PROFILE" serve --host "$HOST" --port "$PORT")
if [[ "$NO_TTS" == "1" ]]; then
  CMD+=(--no-tts)
fi
if [[ "$EXECUTE" == "1" ]]; then
  CMD+=(--execute)
fi
if [[ -n "$TOKEN" ]]; then
  CMD+=(--token "$TOKEN")
fi

LOG_FILE="$OUT_DIR/jarvis.log"
nohup "${CMD[@]}" >"$LOG_FILE" 2>&1 &
PID=$!

sleep 1
if ! kill -0 "$PID" >/dev/null 2>&1; then
  echo "ERROR: Jarvis process exited. Check log: $LOG_FILE" >&2
  exit 3
fi

LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || true)"
if [[ -z "$LAN_IP" ]]; then
  LAN_IP="$(ipconfig getifaddr en1 2>/dev/null || true)"
fi
if [[ -z "$LAN_IP" ]]; then
  LAN_IP="127.0.0.1"
fi

LOCAL_URL="http://127.0.0.1:${PORT}"
LAN_URL="http://${LAN_IP}:${PORT}"

cat >"$OUT_DIR/README.txt" <<EOF
Jarvis live started.
PID: $PID
Local URL: $LOCAL_URL
LAN URL: $LAN_URL
Profile: $PROFILE
Log: $LOG_FILE

Stop:
kill $PID

Audio doctor:
python3 -m automation.jarvis --profile "$PROFILE" doctor

Apply audio profile (requires SwitchAudioSource):
python3 -m automation.jarvis --profile "$PROFILE" audio-apply
EOF

echo "Jarvis ready"
echo "Local: $LOCAL_URL"
echo "Mobile (same WLAN): $LAN_URL"
echo "PID: $PID"
echo "Log: $LOG_FILE"
echo "Session: $OUT_DIR/README.txt"

if command -v open >/dev/null 2>&1; then
  open "$LOCAL_URL" >/dev/null 2>&1 || true
fi

if command -v cloudflared >/dev/null 2>&1; then
  echo
  echo "Optional remote tunnel command:"
  echo "cloudflared tunnel --url $LOCAL_URL"
fi
