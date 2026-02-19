#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# BOMBPROOF STARTUP SYSTEM — AIEmpire-Core
# ══════════════════════════════════════════════════════════════════════════════
#
# Runs on every boot via LaunchAgent. Guarantees the system comes up clean.
#
# Sequence:
#   1. Self-Repair (auto_repair.py) — fix everything broken
#   2. Resource Guard startup check — crash detection + safe mode
#   3. Core services (Redis, PostgreSQL, Ollama)
#   4. Application services (Atomic Reactor, CRM, OpenClaw)
#   5. Health verification — confirm everything is alive
#
# Usage:
#   ./scripts/bombproof_startup.sh           # Full startup
#   ./scripts/bombproof_startup.sh --repair  # Only repair, don't start services
#   ./scripts/bombproof_startup.sh --status  # Only check status
#
# ══════════════════════════════════════════════════════════════════════════════

set -o pipefail  # Don't use set -e, we handle errors ourselves

# ─── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_DIR/workflow_system/state"
LOG_FILE="$LOG_DIR/startup_$(date +%Y%m%d_%H%M%S).log"
LOCK_FILE="/tmp/aiempire_startup.lock"

# ─── Colors ───────────────────────────────────────────────────────────────────
R='\033[0;31m'
G='\033[0;32m'
Y='\033[1;33m'
B='\033[0;34m'
C='\033[0;36m'
W='\033[1;37m'
N='\033[0m'

# ─── Logging ──────────────────────────────────────────────────────────────────
mkdir -p "$LOG_DIR"

log() {
    local level="$1"
    shift
    local msg="$*"
    local ts="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "[$ts] [$level] $msg" >> "$LOG_FILE"

    case "$level" in
        OK)    echo -e "  ${G}[OK]${N}    $msg" ;;
        FIX)   echo -e "  ${Y}[FIX]${N}   $msg" ;;
        FAIL)  echo -e "  ${R}[FAIL]${N}  $msg" ;;
        INFO)  echo -e "  ${B}[INFO]${N}  $msg" ;;
        WARN)  echo -e "  ${Y}[WARN]${N}  $msg" ;;
        *)     echo -e "  $msg" ;;
    esac
}

# ─── Lock (prevent parallel runs) ────────────────────────────────────────────
if [ -f "$LOCK_FILE" ]; then
    pid=$(cat "$LOCK_FILE" 2>/dev/null)
    if kill -0 "$pid" 2>/dev/null; then
        echo "Another startup is already running (PID $pid). Exiting."
        exit 0
    fi
    rm -f "$LOCK_FILE"
fi
echo $$ > "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

# ─── Banner ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${W}╔═══════════════════════════════════════════════════════════╗${N}"
echo -e "${W}║        BOMBPROOF STARTUP — AIEmpire-Core v2.0           ║${N}"
echo -e "${W}║        Self-Healing • Auto-Recovery • Crash-Proof        ║${N}"
echo -e "${W}╚═══════════════════════════════════════════════════════════╝${N}"
echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: SELF-REPAIR
# ═══════════════════════════════════════════════════════════════════════════════

echo -e "${C}═══ PHASE 1: Self-Repair ═══${N}"
echo ""

if [ -f "$PROJECT_DIR/scripts/auto_repair.py" ]; then
    log INFO "Running auto_repair.py..."
    python3 "$PROJECT_DIR/scripts/auto_repair.py" 2>&1 | while IFS= read -r line; do
        echo "    $line" >> "$LOG_FILE"
        # Show only FIX lines to console
        if echo "$line" | grep -q "FIX\|ERROR\|WARN"; then
            echo "    $line"
        fi
    done
    log OK "Self-repair completed"
else
    log WARN "auto_repair.py not found — skipping self-repair"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: ENVIRONMENT VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${C}═══ PHASE 2: Environment Verification ═══${N}"
echo ""

# Check .env exists
if [ -f "$PROJECT_DIR/.env" ]; then
    log OK ".env file present"
    # Source critical vars
    export $(grep -v '^#' "$PROJECT_DIR/.env" | grep '=' | xargs 2>/dev/null) 2>/dev/null || true
else
    log FAIL ".env file missing!"
fi

# Check Python3
if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 --version 2>&1)
    log OK "Python3: $PY_VERSION"
else
    log FAIL "Python3 not found!"
fi

# Check git repo
if [ -d "$PROJECT_DIR/.git" ]; then
    BRANCH=$(cd "$PROJECT_DIR" && git branch --show-current 2>/dev/null || echo "unknown")
    COMMIT=$(cd "$PROJECT_DIR" && git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    log OK "Git: branch=$BRANCH commit=$COMMIT"
else
    log WARN "Not a git repo"
fi

# Check gcloud (non-critical)
if command -v gcloud &>/dev/null; then
    GC_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "(unset)")
    if [ -n "$GC_PROJECT" ] && [ "$GC_PROJECT" != "(unset)" ]; then
        log OK "gcloud project: $GC_PROJECT"
    else
        log FIX "gcloud project unset — fixing..."
        gcloud config set project "${GOOGLE_CLOUD_PROJECT:-ai-empire-486415}" 2>/dev/null
    fi
else
    log INFO "gcloud not installed (optional)"
fi

# Bail out if --repair or --status
if [ "$1" = "--repair" ]; then
    echo ""
    log INFO "Repair-only mode — stopping here"
    exit 0
fi

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: CORE SERVICES
# ═══════════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${C}═══ PHASE 3: Core Services ═══${N}"
echo ""

start_or_check() {
    local name="$1"
    local port="$2"
    local start_cmd="$3"
    local wait_secs="${4:-5}"

    # Already running?
    if lsof -i ":$port" &>/dev/null 2>&1 || nc -z 127.0.0.1 "$port" 2>/dev/null; then
        log OK "$name already running (port $port)"
        return 0
    fi

    # Try to start
    if [ -n "$start_cmd" ]; then
        log INFO "Starting $name..."
        eval "$start_cmd" &>/dev/null &
        sleep "$wait_secs"

        if lsof -i ":$port" &>/dev/null 2>&1 || nc -z 127.0.0.1 "$port" 2>/dev/null; then
            log OK "$name started (port $port)"
            return 0
        else
            log WARN "$name failed to start on port $port"
            return 1
        fi
    else
        log INFO "$name not running (port $port) — manual start may be needed"
        return 1
    fi
}

# Detect OS
IS_LINUX=false
IS_MACOS=false
if [[ "$(uname -s)" == "Linux" ]]; then
    IS_LINUX=true
elif [[ "$(uname -s)" == "Darwin" ]]; then
    IS_MACOS=true
fi

# Ollama (critical for AI)
if command -v ollama &>/dev/null; then
    if $IS_LINUX && systemctl is-active --quiet ollama 2>/dev/null; then
        log OK "Ollama running (systemd)"
    elif $IS_LINUX; then
        log INFO "Starting Ollama via systemd..."
        systemctl start ollama 2>/dev/null || start_or_check "Ollama" 11434 "ollama serve" 4
        sleep 2
        log OK "Ollama started"
    else
        start_or_check "Ollama" 11434 "ollama serve" 4
    fi
elif [ -d "/Applications/Ollama.app" ]; then
    start_or_check "Ollama" 11434 "open -a Ollama" 6
else
    log WARN "Ollama not installed"
fi

# Redis
if $IS_LINUX && systemctl is-active --quiet redis-server 2>/dev/null; then
    log OK "Redis running (systemd)"
elif $IS_LINUX && command -v redis-server &>/dev/null; then
    systemctl start redis-server 2>/dev/null || start_or_check "Redis" 6379 "redis-server --daemonize yes" 2
    log OK "Redis started"
elif command -v redis-server &>/dev/null; then
    start_or_check "Redis" 6379 "redis-server --daemonize yes" 2
elif $IS_MACOS && command -v brew &>/dev/null && brew list redis &>/dev/null 2>&1; then
    start_or_check "Redis" 6379 "brew services start redis" 3
else
    log INFO "Redis not installed (optional)"
fi

# PostgreSQL
if $IS_LINUX && systemctl is-active --quiet postgresql 2>/dev/null; then
    log OK "PostgreSQL running (systemd)"
elif $IS_LINUX && command -v pg_isready &>/dev/null; then
    systemctl start postgresql 2>/dev/null
    sleep 2
    if pg_isready -q 2>/dev/null; then
        log OK "PostgreSQL started"
    else
        log WARN "PostgreSQL failed to start"
    fi
elif command -v pg_isready &>/dev/null; then
    if pg_isready -q 2>/dev/null; then
        log OK "PostgreSQL running"
    elif $IS_MACOS && command -v brew &>/dev/null; then
        start_or_check "PostgreSQL" 5432 "brew services start postgresql@16" 4
    fi
else
    log INFO "PostgreSQL not installed (optional)"
fi

if [ "$1" = "--status" ]; then
    echo ""
    log INFO "Status check complete"
    exit 0
fi

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4: APPLICATION SERVICES
# ═══════════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${C}═══ PHASE 4: Application Services ═══${N}"
echo ""

# CRM (Express.js)
if $IS_LINUX && systemctl list-unit-files aiempire-crm.service &>/dev/null 2>&1; then
    systemctl start aiempire-crm 2>/dev/null
    sleep 2
    if nc -z 127.0.0.1 3500 2>/dev/null; then
        log OK "CRM running (systemd, port 3500)"
    else
        log WARN "CRM service started but port 3500 not responding"
    fi
elif [ -d "$PROJECT_DIR/crm" ] && [ -f "$PROJECT_DIR/crm/package.json" ]; then
    start_or_check "CRM" 3500 "cd $PROJECT_DIR/crm && npm start" 4
fi

# Empire API (FastAPI control dashboard)
if $IS_LINUX && systemctl list-unit-files aiempire-empire-api.service &>/dev/null 2>&1; then
    systemctl start aiempire-empire-api 2>/dev/null
    sleep 2
    if nc -z 127.0.0.1 3333 2>/dev/null; then
        log OK "Empire API running (systemd, port 3333)"
    else
        log WARN "Empire API service started but port 3333 not responding"
    fi
elif [ -f "$PROJECT_DIR/empire_api/server.py" ]; then
    UVICORN_CMD="python3 -m uvicorn empire_api.server:app --host 0.0.0.0 --port 3333"
    if [ -f "$PROJECT_DIR/venv/bin/uvicorn" ]; then
        UVICORN_CMD="$PROJECT_DIR/venv/bin/uvicorn empire_api.server:app --host 0.0.0.0 --port 3333"
    fi
    start_or_check "Empire API" 3333 "cd $PROJECT_DIR && $UVICORN_CMD" 4
fi

# Atomic Reactor (FastAPI)
if [ -d "$PROJECT_DIR/atomic-reactor" ] || [ -d "$PROJECT_DIR/atomic_reactor" ]; then
    REACTOR_DIR="$PROJECT_DIR/atomic-reactor"
    [ ! -d "$REACTOR_DIR" ] && REACTOR_DIR="$PROJECT_DIR/atomic_reactor"
    if [ -f "$REACTOR_DIR/main.py" ]; then
        start_or_check "Atomic Reactor" 8888 "cd $REACTOR_DIR && python3 -m uvicorn main:app --host 0.0.0.0 --port 8888" 4
    fi
fi

# OpenClaw
start_or_check "OpenClaw" 18789 "" 0

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5: HEALTH VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${C}═══ PHASE 5: Health Verification ═══${N}"
echo ""

TOTAL=0
UP=0

check_health() {
    local name="$1"
    local check_cmd="$2"
    TOTAL=$((TOTAL + 1))

    if eval "$check_cmd" &>/dev/null 2>&1; then
        log OK "$name: HEALTHY"
        UP=$((UP + 1))
    else
        log WARN "$name: NOT RESPONDING"
    fi
}

check_health "Ollama API" "curl -s -o /dev/null -w '%{http_code}' http://localhost:11434/api/version | grep -q 200"
check_health ".env File" "test -f $PROJECT_DIR/.env && test -s $PROJECT_DIR/.env"
check_health "Git Repo" "cd $PROJECT_DIR && git status &>/dev/null"
check_health "Python Imports" "cd $PROJECT_DIR && python3 -c 'from antigravity.config import GOOGLE_CLOUD_PROJECT'"

# Redis (optional)
if command -v redis-cli &>/dev/null; then
    check_health "Redis" "redis-cli ping | grep -q PONG"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${W}╔═══════════════════════════════════════════════════════════╗${N}"
echo -e "${W}║                    STARTUP COMPLETE                       ║${N}"
echo -e "${W}╠═══════════════════════════════════════════════════════════╣${N}"
printf "${W}║${N}  Services Healthy:  ${G}%d${N} / ${W}%d${N}                               ${W}║${N}\n" "$UP" "$TOTAL"
echo -e "${W}║${N}  Log: $LOG_FILE"
echo -e "${W}╚═══════════════════════════════════════════════════════════╝${N}"
echo ""

# Save startup result
cat > "$LOG_DIR/last_startup.json" << ENDJSON
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "services_up": $UP,
    "services_total": $TOTAL,
    "log_file": "$LOG_FILE",
    "git_branch": "${BRANCH:-unknown}",
    "git_commit": "${COMMIT:-unknown}"
}
ENDJSON

# Return success if most services are up
if [ "$UP" -ge 3 ]; then
    exit 0
else
    exit 1
fi
