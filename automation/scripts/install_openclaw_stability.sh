#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TPL_DIR="$ROOT_DIR/ai-vault/launchagents"
DST_DIR="$HOME/Library/LaunchAgents"
RUNTIME_ROOT="$HOME/Library/Application Support/ai-empire/stability-runtime"
RUNTIME_SCRIPT_DIR="$RUNTIME_ROOT/automation/scripts"

mkdir -p "$DST_DIR"
mkdir -p "$RUNTIME_SCRIPT_DIR"

cp "$SCRIPT_DIR/openclaw_healthcheck.sh" "$RUNTIME_SCRIPT_DIR/openclaw_healthcheck.sh"
cp "$SCRIPT_DIR/openclaw_self_heal.sh" "$RUNTIME_SCRIPT_DIR/openclaw_self_heal.sh"
cp "$SCRIPT_DIR/openclaw_snapshot.sh" "$RUNTIME_SCRIPT_DIR/openclaw_snapshot.sh"

chmod +x "$RUNTIME_SCRIPT_DIR/openclaw_healthcheck.sh"
chmod +x "$RUNTIME_SCRIPT_DIR/openclaw_self_heal.sh"
chmod +x "$RUNTIME_SCRIPT_DIR/openclaw_snapshot.sh"

render_plist() {
  local src="$1"
  local dst="$2"
  local escaped_root
  escaped_root="$(printf '%s' "$RUNTIME_ROOT" | sed 's/[\/&]/\\&/g')"
  sed "s/__ROOT_DIR__/$escaped_root/g" "$src" >"$dst"
}

install_one() {
  local label="$1"
  local template="$2"
  local dest="$DST_DIR/$label.plist"

  render_plist "$template" "$dest"
  plutil -lint "$dest" >/dev/null

  launchctl bootout "gui/$(id -u)" "$dest" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "$dest"
  launchctl enable "gui/$(id -u)/$label" >/dev/null 2>&1 || true
  launchctl kickstart -k "gui/$(id -u)/$label" >/dev/null 2>&1 || true
}

install_one "com.ai-empire.openclaw-self-heal" "$TPL_DIR/com.ai-empire.openclaw-self-heal.plist"
install_one "com.ai-empire.openclaw-snapshot" "$TPL_DIR/com.ai-empire.openclaw-snapshot.plist"

echo "Installed and started:"
echo "- com.ai-empire.openclaw-self-heal"
echo "- com.ai-empire.openclaw-snapshot"
echo
echo "Runtime root:"
echo "- $RUNTIME_ROOT"
echo
echo "Logs:"
echo "- $RUNTIME_ROOT/00_SYSTEM/stability/self_heal.log"
echo "- $RUNTIME_ROOT/00_SYSTEM/stability/healthcheck.log"
