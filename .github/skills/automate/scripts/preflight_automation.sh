#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(pwd)}"
if command -v git >/dev/null 2>&1 && git -C "$ROOT" rev-parse --show-toplevel >/dev/null 2>&1; then
  ROOT="$(git -C "$ROOT" rev-parse --show-toplevel)"
fi

ok() {
  printf '[OK] %s\n' "$1"
}

warn() {
  printf '[WARN] %s\n' "$1"
}

check_cmd() {
  local cmd="$1"
  local required="${2:-optional}"
  if command -v "$cmd" >/dev/null 2>&1; then
    ok "command available: $cmd"
  elif [[ "$required" == "required" ]]; then
    warn "missing required command: $cmd"
  else
    warn "missing optional command: $cmd"
  fi
}

check_path() {
  local path="$1"
  local required="${2:-required}"
  if [[ -e "$ROOT/$path" ]]; then
    ok "path present: $path"
  elif [[ "$required" == "required" ]]; then
    warn "missing required path: $path"
  else
    warn "missing optional path: $path"
  fi
}

check_env() {
  local name="$1"
  local required="${2:-optional}"
  if [[ -n "${!name:-}" ]]; then
    ok "env set: $name"
  elif [[ "$required" == "required" ]]; then
    warn "env missing: $name"
  else
    warn "env not set: $name"
  fi
}

check_port() {
  local port="$1"
  local label="$2"
  if lsof -i ":$port" >/dev/null 2>&1; then
    ok "port in use ($label): $port"
  else
    warn "port not in use ($label): $port"
  fi
}

printf 'Automation preflight in: %s\n' "$ROOT"

printf '\n== Commands ==\n'
check_cmd python3 required
check_cmd rg required
check_cmd gh optional
check_cmd docker optional
check_cmd node optional
check_cmd npm optional
check_cmd n8n optional

printf '\n== Paths ==\n'
check_path .github/workflows required
check_path openclaw-config/jobs.json required
check_path n8n-workflows required
check_path workflow-system required
check_path atomic_reactor required
check_path scripts/start_all_services.sh required
check_path scripts/check_status.sh required

printf '\n== Environment ==\n'
check_env GITHUB_TOKEN optional
check_env MOONSHOT_API_KEY optional
check_env ANTHROPIC_API_KEY optional
check_env OPENAI_API_KEY optional

printf '\n== Service ports ==\n'
check_port 11434 ollama
check_port 6379 redis
check_port 5432 postgresql
check_port 5678 n8n
check_port 3500 crm
check_port 8888 atomic_reactor

printf '\nPreflight complete.\n'
