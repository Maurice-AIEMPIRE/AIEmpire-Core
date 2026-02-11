#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
APP_DIR="$HOME/Library/Application Support/ai-empire"
TARGET_SCRIPT="$APP_DIR/automation/run_daily_content_sprint.sh"
TARGET_ENV="$APP_DIR/daily_content_sprint.env"
PLIST_PATH="$REPO_DIR/ai-vault/launchagents/com.ai-empire.daily-content-sprint.plist"

mkdir -p "$APP_DIR/automation" "$APP_DIR/daily_sprints"

cp "$REPO_DIR/automation/scripts/run_daily_content_sprint.sh" "$TARGET_SCRIPT"
chmod +x "$TARGET_SCRIPT"

if [ ! -f "$TARGET_ENV" ]; then
  cp "$REPO_DIR/automation/config/daily_content_sprint.env.example" "$TARGET_ENV"
fi

launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl kickstart -k "gui/$(id -u)/com.ai-empire.daily-content-sprint"

echo "Installed: $TARGET_SCRIPT"
echo "Config: $TARGET_ENV"
echo "Agent: com.ai-empire.daily-content-sprint"
