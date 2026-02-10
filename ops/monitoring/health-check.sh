#!/usr/bin/env bash
# AI Empire Health Check Script
# Version: 1.0
# Last Updated: 2026-02-10

set -euo pipefail

# Configuration
ALERT_THRESHOLD_MINUTES=5
STATE_FILE="/tmp/aiempire-health-state.json"

# Services to monitor
declare -A SERVICES=(
    ["Redis"]="localhost:6379"
    ["PostgreSQL"]="localhost:5432"
    ["Ollama"]="localhost:11434"
    ["OpenClaw"]="localhost:18789"
    ["AtomicReactor"]="localhost:8888"
    ["CRM"]="localhost:3500"
)

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Check service health
check_service() {
    local name=$1
    local host_port=$2
    local host=${host_port%:*}
    local port=${host_port#*:}

    if nc -z -w 2 "$host" "$port" 2>/dev/null; then
        echo "✅"
        return 0
    else
        echo "❌"
        return 1
    fi
}

# Send alert (Telegram)
send_alert() {
    local message=$1

    if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
        curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
            -d "chat_id=$TELEGRAM_CHAT_ID" \
            -d "text=$message" \
            -d "parse_mode=Markdown" >/dev/null
    fi
}

# Main health check
for service in "${!SERVICES[@]}"; do
    result=$(check_service "$service" "${SERVICES[$service]}")
    echo "[$service] $result"

    if [ "$result" = "❌" ]; then
        send_alert "🚨 *AI Empire Alert*\n\nService DOWN: *$service*\nTime: $(date)"
    fi
done
