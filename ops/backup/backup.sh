#!/usr/bin/env bash
# AI Empire Backup Script — 3-2-1 Strategy
# Version: 1.0
# Last Updated: 2026-02-10

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
BACKUP_DIR="${BACKUP_DIR:-$HOME/.aiempire-backups}"
RETENTION_HOURLY_HOURS=72    # Keep hourly for 3 days
RETENTION_DAILY_DAYS=30       # Keep daily for 30 days
RETENTION_MONTHLY_DAYS=365    # Keep monthly for 1 year
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Database credentials (from environment or macOS Keychain)
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(security find-generic-password -a "$USER" -s "aiempire-postgres" -w 2>/dev/null || echo '')}"
REDIS_PASSWORD="${REDIS_PASSWORD:-$(security find-generic-password -a "$USER" -s "aiempire-redis" -w 2>/dev/null || echo '')}"

# Backup destinations
HOURLY_DIR="$BACKUP_DIR/hourly"
DAILY_DIR="$BACKUP_DIR/daily"
MONTHLY_DIR="$BACKUP_DIR/monthly"
PRIVATE_VAULT_DIR="$HOME/.private-vault"

# Encryption key (from macOS Keychain)
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-$(security find-generic-password -a "$USER" -s "aiempire-backup-key" -w 2>/dev/null || echo '')}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

# Create backup directories
mkdir -p "$HOURLY_DIR" "$DAILY_DIR" "$MONTHLY_DIR"

# --- PostgreSQL Backup ---
backup_postgres() {
    log "Backing up PostgreSQL..."

    if ! command -v pg_dump &>/dev/null; then
        error "pg_dump not found. Install PostgreSQL client."
        return 1
    fi

    local backup_file="$HOURLY_DIR/postgres_$TIMESTAMP.sql.gz"

    PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
        -h localhost \
        -p 5432 \
        -U empire \
        -d aiempire \
        --no-owner \
        --no-privileges \
        | gzip > "$backup_file"

    if [ -f "$backup_file" ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        log "PostgreSQL backup complete: $backup_file ($size)"

        # Encrypt if key available
        if [ -n "$ENCRYPTION_KEY" ]; then
            openssl enc -aes-256-cbc -salt -pbkdf2 -in "$backup_file" -out "$backup_file.enc" -k "$ENCRYPTION_KEY"
            rm "$backup_file"  # Remove unencrypted
            log "PostgreSQL backup encrypted: $backup_file.enc"
        fi
    else
        error "PostgreSQL backup failed"
        return 1
    fi
}

# --- Redis Backup ---
backup_redis() {
    log "Backing up Redis..."

    if ! command -v redis-cli &>/dev/null; then
        error "redis-cli not found. Install Redis client."
        return 1
    fi

    # Trigger RDB snapshot
    redis-cli -a "$REDIS_PASSWORD" --no-auth-warning BGSAVE >/dev/null

    # Wait for BGSAVE to complete (max 60 seconds)
    local wait_count=0
    while [ $wait_count -lt 60 ]; do
        if redis-cli -a "$REDIS_PASSWORD" --no-auth-warning LASTSAVE | grep -q "$(date +%s)"; then
            break
        fi
        sleep 1
        ((wait_count++))
    done

    # Copy RDB file
    local rdb_file="/usr/local/var/db/redis/dump.rdb"  # macOS Homebrew default
    if [ ! -f "$rdb_file" ]; then
        rdb_file="/var/lib/redis/dump.rdb"  # Linux default
    fi

    if [ -f "$rdb_file" ]; then
        local backup_file="$HOURLY_DIR/redis_$TIMESTAMP.rdb.gz"
        gzip -c "$rdb_file" > "$backup_file"

        local size=$(du -h "$backup_file" | cut -f1)
        log "Redis backup complete: $backup_file ($size)"

        # Encrypt if key available
        if [ -n "$ENCRYPTION_KEY" ]; then
            openssl enc -aes-256-cbc -salt -pbkdf2 -in "$backup_file" -out "$backup_file.enc" -k "$ENCRYPTION_KEY"
            rm "$backup_file"
            log "Redis backup encrypted: $backup_file.enc"
        fi
    else
        error "Redis RDB file not found: $rdb_file"
        return 1
    fi
}

# --- Private Vault Backup (P3 Data, Local-Only) ---
backup_private_vault() {
    log "Backing up Private Vault (P3 data)..."

    if [ ! -d "$PRIVATE_VAULT_DIR" ]; then
        warn "Private Vault not found: $PRIVATE_VAULT_DIR (skipping)"
        return 0
    fi

    local backup_file="$DAILY_DIR/private-vault_$TIMESTAMP.tar.gz"
    tar -czf "$backup_file" -C "$HOME" .private-vault/

    local size=$(du -h "$backup_file" | cut -f1)
    log "Private Vault backup complete: $backup_file ($size)"

    # Always encrypt P3 data
    if [ -n "$ENCRYPTION_KEY" ]; then
        openssl enc -aes-256-cbc -salt -pbkdf2 -in "$backup_file" -out "$backup_file.enc" -k "$ENCRYPTION_KEY"
        rm "$backup_file"
        log "Private Vault backup encrypted: $backup_file.enc"
    else
        error "Encryption key not found. P3 data MUST be encrypted."
        rm "$backup_file"
        return 1
    fi
}

# --- ChromaDB Backup ---
backup_chromadb() {
    log "Backing up ChromaDB..."

    local chromadb_dir="$HOME/.chromadb"  # Default ChromaDB storage
    if [ ! -d "$chromadb_dir" ]; then
        warn "ChromaDB directory not found (skipping)"
        return 0
    fi

    local backup_file="$DAILY_DIR/chromadb_$TIMESTAMP.tar.gz"
    tar -czf "$backup_file" -C "$HOME" .chromadb/

    local size=$(du -h "$backup_file" | cut -f1)
    log "ChromaDB backup complete: $backup_file ($size)"
}

# --- Cleanup Old Backups (Retention Policy) ---
cleanup_old_backups() {
    log "Cleaning up old backups (retention policy)..."

    # Hourly: Keep 72 hours
    find "$HOURLY_DIR" -type f -name "*.gz*" -mtime +3 -delete
    log "Deleted hourly backups older than 72 hours"

    # Daily: Keep 30 days
    find "$DAILY_DIR" -type f -name "*.gz*" -mtime +30 -delete
    log "Deleted daily backups older than 30 days"

    # Monthly: Keep 365 days
    find "$MONTHLY_DIR" -type f -name "*.gz*" -mtime +365 -delete
    log "Deleted monthly backups older than 365 days"
}

# --- Promote Hourly to Daily/Monthly ---
promote_backups() {
    local current_hour=$(date +%H)
    local current_day=$(date +%d)

    # Promote to daily at midnight (00:00)
    if [ "$current_hour" = "00" ]; then
        log "Promoting hourly backups to daily..."
        cp "$HOURLY_DIR"/postgres_*.enc "$DAILY_DIR/" 2>/dev/null || true
        cp "$HOURLY_DIR"/redis_*.enc "$DAILY_DIR/" 2>/dev/null || true
    fi

    # Promote to monthly on 1st of month
    if [ "$current_day" = "01" ] && [ "$current_hour" = "00" ]; then
        log "Promoting daily backups to monthly..."
        cp "$DAILY_DIR"/postgres_*.enc "$MONTHLY_DIR/" 2>/dev/null || true
        cp "$DAILY_DIR"/redis_*.enc "$MONTHLY_DIR/" 2>/dev/null || true
        cp "$DAILY_DIR"/private-vault_*.enc "$MONTHLY_DIR/" 2>/dev/null || true
    fi
}

# --- Health Check (Verify Backup Integrity) ---
verify_backup_integrity() {
    log "Verifying backup integrity..."

    local latest_postgres=$(ls -t "$HOURLY_DIR"/postgres_*.enc 2>/dev/null | head -1)
    local latest_redis=$(ls -t "$HOURLY_DIR"/redis_*.enc 2>/dev/null | head -1)

    if [ -f "$latest_postgres" ]; then
        if openssl enc -d -aes-256-cbc -pbkdf2 -in "$latest_postgres" -k "$ENCRYPTION_KEY" | gunzip -t 2>/dev/null; then
            log "✅ PostgreSQL backup integrity verified"
        else
            error "❌ PostgreSQL backup integrity check FAILED"
            return 1
        fi
    fi

    if [ -f "$latest_redis" ]; then
        if openssl enc -d -aes-256-cbc -pbkdf2 -in "$latest_redis" -k "$ENCRYPTION_KEY" | gunzip -t 2>/dev/null; then
            log "✅ Redis backup integrity verified"
        else
            error "❌ Redis backup integrity check FAILED"
            return 1
        fi
    fi
}

# --- Main Execution ---
main() {
    log "Starting AI Empire backup process..."

    # Check prerequisites
    if [ -z "$POSTGRES_PASSWORD" ]; then
        error "PostgreSQL password not found in environment or Keychain"
        exit 1
    fi

    if [ -z "$ENCRYPTION_KEY" ]; then
        warn "Encryption key not found. Backups will NOT be encrypted (except P3 data)."
    fi

    # Run backups
    backup_postgres || error "PostgreSQL backup failed"
    backup_redis || error "Redis backup failed"
    backup_chromadb || warn "ChromaDB backup skipped"

    # Daily backups (Private Vault)
    if [ "$(date +%H)" = "00" ]; then
        backup_private_vault || error "Private Vault backup failed"
    fi

    # Promote and cleanup
    promote_backups
    cleanup_old_backups

    # Verify integrity
    verify_backup_integrity || error "Backup integrity check failed"

    log "Backup process complete! 🎉"
}

# Run main function
main "$@"
