#!/bin/bash
#
# Super Brain Galaxia - iCloud Sync Automation
# Bidirectional synchronization of Galaxia workspace with iCloud Drive
# Preserves project DNA: AGENTS.md, configs, skills, state
#
# Dependencies: rclone (v1.69+)
#

set -e

# ============================================================================
# CONFIGURATION
# ============================================================================

GALAXIA_ROOT="/opt/openclaw/workspace_galaxia"
ICLOUD_REMOTE="icloud_galaxia"
ICLOUD_PATH="/iCloud Drive/AIEmpire-Galaxia"

LOG_FILE="/var/log/galaxia_sync.log"
STATE_FILE="/var/lib/galaxia_sync_state.json"
LOCK_FILE="/tmp/galaxia_sync.lock"

SYNC_TIMEOUT_SECONDS=300
MAX_RETRIES=5
RETRY_DELAY_SECONDS=5

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# LOGGING
# ============================================================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[✅]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[⚠️]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[❌]${NC} $1" | tee -a "$LOG_FILE"
}

# ============================================================================
# INITIALIZATION
# ============================================================================

check_dependencies() {
    log_info "Checking dependencies..."

    if ! command -v rclone &> /dev/null; then
        log_error "rclone not found. Install with: brew install rclone (macOS) or apt-get install rclone (Linux)"
        exit 1
    fi

    RCLONE_VERSION=$(rclone --version | head -n 1)
    log_success "Found: $RCLONE_VERSION"

    if ! command -v jq &> /dev/null; then
        log_warning "jq not found (optional). Some features will be limited."
    fi

    if ! command -v curl &> /dev/null; then
        log_error "curl not found. Required for health checks."
        exit 1
    fi
}

check_lock() {
    if [ -f "$LOCK_FILE" ]; then
        PID=$(cat "$LOCK_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            log_warning "Sync already running (PID: $PID). Exiting."
            exit 1
        else
            log_warning "Stale lock file found. Removing."
            rm -f "$LOCK_FILE"
        fi
    fi

    echo $$ > "$LOCK_FILE"
}

cleanup() {
    rm -f "$LOCK_FILE"
}

trap cleanup EXIT

# ============================================================================
# RCLONE CONFIGURATION
# ============================================================================

setup_rclone_remote() {
    log_info "Setting up rclone remote for iCloud Drive..."

    # Check if remote already configured
    if rclone listremotes | grep -q "^${ICLOUD_REMOTE}$"; then
        log_success "iCloud remote already configured: $ICLOUD_REMOTE"
        return 0
    fi

    log_warning "iCloud remote not found. Manual setup required:"
    log_warning ""
    log_warning "1. Run: rclone config"
    log_warning "2. Choose 'n' for new remote"
    log_warning "3. Name: $ICLOUD_REMOTE"
    log_warning "4. Type: iclouddrive"
    log_warning "5. Follow prompts for authentication"
    log_warning ""
    log_warning "NOTE: You need:"
    log_warning "  - iCloud email and password"
    log_warning "  - 2FA code (when prompted)"
    log_warning "  - Advanced Data Protection DISABLED in iCloud settings"
    log_warning "  - Web access for iCloud enabled"
    log_warning ""

    read -p "Continue after setup? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
}

validate_rclone_connection() {
    log_info "Validating rclone connection to iCloud..."

    if ! timeout 30 rclone ls "$ICLOUD_REMOTE:" &> /dev/null; then
        log_error "Cannot connect to iCloud. Check authentication."
        log_error "Run: rclone config and re-authenticate"
        exit 1
    fi

    log_success "iCloud connection verified"
}

# ============================================================================
# SYNC LOGIC
# ============================================================================

prepare_sync_dirs() {
    log_info "Preparing directories..."

    # Ensure local directory exists
    if [ ! -d "$GALAXIA_ROOT" ]; then
        log_error "Galaxia root directory not found: $GALAXIA_ROOT"
        exit 1
    fi

    # Create iCloud directory if needed (rclone creates it)
    log_success "Directories ready"
}

create_filter_file() {
    log_info "Creating sync filter rules..."

    # Create filter file to exclude unneeded files
    cat > /tmp/galaxia_rclone_filter << 'EOF'
# Include essential files
+ AGENTS.md
+ *.yaml
+ *.yml
+ *.json
+ *.md
+ *.py
+ *.js
+ *.ts
+ *.sh
+ Dockerfile

# Exclude cache and build artifacts
- node_modules/
- __pycache__/
- .pyc
- .egg-info/
- dist/
- build/
- .docker/
- venv/
- .env
- .git/objects/
- cache/
- tmp/
- *.tmp
- *.log

# Include everything else
+ **
EOF

    log_success "Filter file created"
}

run_sync() {
    local attempt=1

    while [ $attempt -le $MAX_RETRIES ]; do
        log_info "Sync attempt $attempt/$MAX_RETRIES..."

        # Run bisync with comprehensive parameters
        if timeout $SYNC_TIMEOUT_SECONDS rclone bisync \
            "$GALAXIA_ROOT" \
            "$ICLOUD_REMOTE:$ICLOUD_PATH" \
            --compare size,modtime,checksum \
            --filter-from /tmp/galaxia_rclone_filter \
            --resilient \
            --metadata \
            --no-modtime \
            --verbose \
            --log-file "$LOG_FILE"; then

            log_success "Sync completed successfully (attempt $attempt)"
            return 0
        else
            SYNC_EXIT=$?
            log_warning "Sync failed with exit code $SYNC_EXIT"

            if [ $attempt -lt $MAX_RETRIES ]; then
                log_warning "Waiting ${RETRY_DELAY_SECONDS}s before retry..."
                sleep $RETRY_DELAY_SECONDS
            fi
        fi

        ((attempt++))
    done

    log_error "Sync failed after $MAX_RETRIES attempts"
    return 1
}

# ============================================================================
# TOKEN MANAGEMENT
# ============================================================================

check_token_expiry() {
    log_info "Checking iCloud token expiry..."

    # Apple tokens expire in 30 days
    # We should rotate every 25 days to be safe

    STATE_FILE_EXISTS=false
    if [ -f "$STATE_FILE" ]; then
        STATE_FILE_EXISTS=true
        LAST_AUTH=$(jq -r '.last_authentication // empty' "$STATE_FILE" 2>/dev/null || echo "")
    fi

    if [ -z "$LAST_AUTH" ] || [ "$LAST_AUTH" = "" ]; then
        log_info "No previous authentication recorded"
        return 0
    fi

    # Calculate days since last auth
    LAST_AUTH_EPOCH=$(date -d "$LAST_AUTH" +%s 2>/dev/null || date -jf "%Y-%m-%dT%H:%M:%S" "$LAST_AUTH" +%s 2>/dev/null || echo 0)
    NOW_EPOCH=$(date +%s)
    DAYS_ELAPSED=$(( ($NOW_EPOCH - $LAST_AUTH_EPOCH) / 86400 ))

    if [ "$DAYS_ELAPSED" -gt 25 ]; then
        log_warning "Token will expire in $(( 30 - DAYS_ELAPSED )) days"
        log_warning "Running token refresh..."

        if rclone reconnect "$ICLOUD_REMOTE:"; then
            log_success "Token refreshed successfully"
            save_sync_state "success"
        else
            log_error "Token refresh failed. Please re-authenticate manually."
            return 1
        fi
    else
        log_info "Token valid for $(( 30 - DAYS_ELAPSED )) more days"
    fi

    return 0
}

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

save_sync_state() {
    local status=$1

    cat > "$STATE_FILE" << EOF
{
  "last_sync": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "last_authentication": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "$status",
  "sync_direction": "bidirectional",
  "files_synced": 0,
  "bytes_transferred": 0
}
EOF

    log_success "State saved to $STATE_FILE"
}

# ============================================================================
# HEALTH CHECKS
# ============================================================================

verify_sync_integrity() {
    log_info "Verifying sync integrity..."

    # Check critical files exist locally
    CRITICAL_FILES=(
        "AGENTS.md"
        "galaxia_architecture.yaml"
        "galaxia_agents.md"
    )

    for file in "${CRITICAL_FILES[@]}"; do
        if [ ! -f "$GALAXIA_ROOT/$file" ]; then
            log_error "Critical file missing: $file"
            return 1
        fi
    done

    log_success "Integrity check passed"
    return 0
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    log_info "🚀 Super Brain Galaxia - iCloud Sync Started"
    log_info "================================================"

    check_lock
    check_dependencies
    setup_rclone_remote
    validate_rclone_connection
    prepare_sync_dirs
    create_filter_file

    # Check token expiry (proactive renewal)
    check_token_expiry || {
        log_error "Token management failed"
        exit 1
    }

    # Run sync
    run_sync || {
        log_error "Synchronization failed"
        exit 1
    }

    # Verify integrity
    verify_sync_integrity || {
        log_error "Integrity check failed"
        exit 1
    }

    # Save state
    save_sync_state "success"

    log_success "================================================"
    log_success "✅ Sync completed successfully"
    log_info "Next sync in 1 hour"
}

# ============================================================================
# CRON SETUP
# ============================================================================

setup_cron() {
    log_info "Setting up cron job..."

    SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"

    # Add to crontab (runs every hour)
    CRON_CMD="0 * * * * $SCRIPT_PATH >> $LOG_FILE 2>&1"

    if ! crontab -l 2>/dev/null | grep -F "$SCRIPT_PATH" > /dev/null; then
        (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
        log_success "Cron job installed"
    else
        log_info "Cron job already installed"
    fi
}

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

case "${1:-sync}" in
    sync)
        main
        ;;
    setup)
        check_dependencies
        setup_rclone_remote
        validate_rclone_connection
        log_success "Setup complete"
        ;;
    cron-setup)
        setup_cron
        ;;
    token-refresh)
        check_token_expiry
        ;;
    verify)
        verify_sync_integrity
        ;;
    status)
        if [ -f "$STATE_FILE" ]; then
            cat "$STATE_FILE" | jq . 2>/dev/null || cat "$STATE_FILE"
        else
            log_warning "No sync state found"
        fi
        ;;
    help)
        cat << EOF
Usage: $0 [command]

Commands:
  sync           - Run synchronization (default)
  setup          - Interactive setup for iCloud connection
  cron-setup     - Install cron job for hourly sync
  token-refresh  - Check and refresh iCloud token
  verify         - Verify sync integrity
  status         - Show last sync status
  help           - Show this help message

Environment Variables:
  GALAXIA_ROOT   - Local workspace path (default: $GALAXIA_ROOT)
  ICLOUD_REMOTE  - Rclone remote name (default: $ICLOUD_REMOTE)
  LOG_FILE       - Log file path (default: $LOG_FILE)

Examples:
  ./galaxia_rclone_sync.sh              # Run sync
  ./galaxia_rclone_sync.sh setup        # Interactive setup
  ./galaxia_rclone_sync.sh cron-setup   # Install cron
  ./galaxia_rclone_sync.sh status       # Check status

EOF
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Run '$0 help' for usage"
        exit 1
        ;;
esac
