#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# AIEmpire Telegram Bridge — Persistent Service
# Keeps the Telegram bot running, auto-restarts on crash
# ═══════════════════════════════════════════════════════════════
#
# Usage:
#   ./scripts/telegram_service.sh start    — Start bot (background)
#   ./scripts/telegram_service.sh stop     — Stop bot
#   ./scripts/telegram_service.sh restart  — Restart bot
#   ./scripts/telegram_service.sh status   — Check if running
#   ./scripts/telegram_service.sh logs     — Tail logs
#
# Auto-Start bei Boot (macOS):
#   cp scripts/com.aiempire.telegram.plist ~/Library/LaunchAgents/
#   launchctl load ~/Library/LaunchAgents/com.aiempire.telegram.plist
#
# Auto-Start bei Boot (Linux/Hetzner):
#   sudo cp scripts/aiempire-telegram.service /etc/systemd/system/
#   sudo systemctl enable aiempire-telegram
#   sudo systemctl start aiempire-telegram
# ═══════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_ROOT/.telegram_bridge.pid"
LOG_FILE="$PROJECT_ROOT/logs/telegram_bridge.log"

# Ensure logs directory exists
mkdir -p "$PROJECT_ROOT/logs"

start() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Telegram Bridge laeuft bereits (PID: $(cat "$PID_FILE"))"
        return 1
    fi

    echo "Starte Telegram Bridge..."
    cd "$PROJECT_ROOT" || exit 1

    # Load .env if exists
    if [ -f .env ]; then
        set -a
        # shellcheck source=/dev/null
        . .env
        set +a
    fi

    # Start in background with auto-restart loop
    nohup bash -c '
        while true; do
            echo "[$(date)] Starte telegram_bridge.py..."
            python3 telegram_bridge.py 2>&1
            EXIT_CODE=$?
            echo "[$(date)] Bridge gestoppt (exit: $EXIT_CODE). Neustart in 5s..."
            sleep 5
        done
    ' >> "$LOG_FILE" 2>&1 &

    echo $! > "$PID_FILE"
    echo "Telegram Bridge gestartet (PID: $!)"
    echo "Logs: tail -f $LOG_FILE"
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "Telegram Bridge laeuft nicht."
        return 1
    fi

    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stoppe Telegram Bridge (PID: $PID)..."
        kill "$PID"
        # Also kill child python process
        pkill -P "$PID" 2>/dev/null
        rm -f "$PID_FILE"
        echo "Gestoppt."
    else
        echo "PID $PID existiert nicht mehr."
        rm -f "$PID_FILE"
    fi
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Telegram Bridge: RUNNING (PID: $(cat "$PID_FILE"))"
    else
        echo "Telegram Bridge: STOPPED"
    fi
}

logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "Keine Logs gefunden: $LOG_FILE"
    fi
}

case "${1:-status}" in
    start)   start ;;
    stop)    stop ;;
    restart) stop; sleep 2; start ;;
    status)  status ;;
    logs)    logs ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
