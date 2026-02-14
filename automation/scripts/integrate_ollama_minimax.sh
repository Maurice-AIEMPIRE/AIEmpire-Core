#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

MODEL="${OLLAMA_PRIMARY_MODEL:-minimax-m2.5:cloud}"
ENV_FILE="$ROOT_DIR/ai-vault/empire.env"
LAUNCH_INTEGRATION=""
SKIP_PULL=0
SKIP_SERVE=0

usage() {
  cat <<'EOF'
Usage:
  automation/scripts/integrate_ollama_minimax.sh [options]

Options:
  --model <name>         Override model (default: minimax-m2.5:cloud)
  --launch <app>         Launch one integration after config (claude|codex|opencode|openclaw)
  --skip-pull            Skip model pull step
  --skip-serve           Skip automatic `ollama serve` bootstrap
  -h, --help             Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      MODEL="$2"
      shift 2
      ;;
    --launch)
      LAUNCH_INTEGRATION="$2"
      shift 2
      ;;
    --skip-pull)
      SKIP_PULL=1
      shift
      ;;
    --skip-serve)
      SKIP_SERVE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if ! command -v ollama >/dev/null 2>&1; then
  echo "ERROR: ollama is not installed. Install first and rerun." >&2
  exit 1
fi

if [[ "$SKIP_SERVE" -ne 1 ]]; then
  if ! curl -fsS "http://127.0.0.1:11434/api/tags" >/dev/null 2>&1; then
    echo "[minimax] starting ollama serve..."
    nohup ollama serve >/tmp/ollama_serve_minimax.log 2>&1 &
    sleep 2
  fi
fi

if ! curl -fsS "http://127.0.0.1:11434/api/tags" >/dev/null 2>&1; then
  echo "ERROR: Ollama API unavailable on http://127.0.0.1:11434" >&2
  exit 1
fi

if [[ "$SKIP_PULL" -ne 1 ]]; then
  if ! ollama list | awk 'NR>1 {print $1}' | rg -x "$MODEL" >/dev/null 2>&1; then
    echo "[minimax] pulling model: $MODEL"
    ollama pull "$MODEL"
  fi
fi

mkdir -p "$(dirname "$ENV_FILE")"
touch "$ENV_FILE"

upsert_env() {
  local key="$1"
  local value="$2"
  local tmp_file
  tmp_file="$(mktemp)"
  awk -v k="$key" -v v="$value" '
    BEGIN { done=0 }
    $0 ~ ("^" k "=") { print k "=" v; done=1; next }
    { print }
    END { if (!done) print k "=" v }
  ' "$ENV_FILE" >"$tmp_file"
  mv "$tmp_file" "$ENV_FILE"
}

upsert_env "OLLAMA_API_KEY" "${OLLAMA_API_KEY:-local}"
upsert_env "OLLAMA_PRIMARY_MODEL" "$MODEL"
upsert_env "OLLAMA_FALLBACK_MODEL_1" "${OLLAMA_FALLBACK_MODEL_1:-qwen3-coder:480b-cloud}"
upsert_env "OLLAMA_FALLBACK_MODEL_2" "${OLLAMA_FALLBACK_MODEL_2:-deepseek-v3.1:671b-cloud}"
upsert_env "JARVIS_MODEL" "${JARVIS_MODEL:-$MODEL}"
upsert_env "FREE_NETWORK_MODEL" "${FREE_NETWORK_MODEL:-$MODEL}"

echo "[minimax] configure: codex -> $MODEL"
ollama launch codex --config --model "$MODEL"

echo "[minimax] configure: opencode -> $MODEL"
ollama launch opencode --config --model "$MODEL"

if command -v openclaw >/dev/null 2>&1; then
  echo "[minimax] configure: openclaw defaults -> $MODEL"
  openclaw models set "$MODEL" >/dev/null
  openclaw models fallbacks clear >/dev/null
  openclaw models fallbacks add "${OLLAMA_FALLBACK_MODEL_1:-qwen3-coder:480b-cloud}" >/dev/null
  openclaw models fallbacks add "${OLLAMA_FALLBACK_MODEL_2:-deepseek-v3.1:671b-cloud}" >/dev/null
else
  echo "[minimax] WARN: openclaw CLI not found, skipped openclaw default model setup."
fi

if [[ -t 1 ]]; then
  echo "[minimax] configure: claude -> $MODEL"
  ollama launch claude --config --model "$MODEL" || true
else
  echo "[minimax] claude config requires interactive TTY once:"
  echo "  ollama launch claude --config --model $MODEL"
fi

echo "[minimax] persisted defaults in: $ENV_FILE"

if [[ -n "$LAUNCH_INTEGRATION" ]]; then
  case "$LAUNCH_INTEGRATION" in
    claude|codex|opencode|openclaw)
      echo "[minimax] launching $LAUNCH_INTEGRATION with $MODEL"
      exec ollama launch "$LAUNCH_INTEGRATION" --model "$MODEL"
      ;;
    *)
      echo "ERROR: --launch must be one of: claude|codex|opencode|openclaw" >&2
      exit 2
      ;;
  esac
fi

echo "[minimax] done. Start any app with:"
echo "  ollama launch claude --model $MODEL"
echo "  ollama launch codex --model $MODEL"
echo "  ollama launch opencode --model $MODEL"
echo "  ollama launch openclaw --model $MODEL"
