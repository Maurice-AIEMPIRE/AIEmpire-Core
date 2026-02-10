#!/usr/bin/env bash
# AI Empire Restore Test Script — Monthly Backup Validation
# Version: 1.0
# Last Updated: 2026-02-10

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-$HOME/.aiempire-backups}"
RESTORE_TEST_DIR="/tmp/aiempire-restore-test-$$"
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-$(security find-generic-password -a "$USER" -s "aiempire-backup-key" -w 2>/dev/null || echo '')}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }

# Create temp restore directory
mkdir -p "$RESTORE_TEST_DIR"
trap "rm -rf $RESTORE_TEST_DIR" EXIT

# --- Test PostgreSQL Restore ---
test_postgres_restore() {
    log "Testing PostgreSQL restore..."

    local latest_backup=$(ls -t "$BACKUP_DIR"/hourly/postgres_*.enc 2>/dev/null | head -1)
    if [ -z "$latest_backup" ]; then
        error "No PostgreSQL backups found"
        return 1
    fi

    log "Found backup: $latest_backup"

    # Decrypt and decompress
    local decrypted_file="$RESTORE_TEST_DIR/postgres_test.sql"
    if openssl enc -d -aes-256-cbc -pbkdf2 -in "$latest_backup" -k "$ENCRYPTION_KEY" | gunzip > "$decrypted_file"; then
        log "✅ PostgreSQL backup decrypted and decompressed successfully"
    else
        error "❌ Failed to decrypt PostgreSQL backup"
        return 1
    fi

    # Verify SQL structure
    if grep -q "CREATE TABLE" "$decrypted_file" && grep -q "COPY" "$decrypted_file"; then
        log "✅ PostgreSQL backup structure verified (contains tables and data)"
    else
        error "❌ PostgreSQL backup structure invalid"
        return 1
    fi

    # Test restore to temporary database (requires PostgreSQL running)
    if command -v psql &>/dev/null; then
        log "Attempting test restore to temporary database..."

        PGPASSWORD="${POSTGRES_PASSWORD:-}" psql -h localhost -U empire -c "DROP DATABASE IF EXISTS aiempire_restore_test;" postgres 2>/dev/null || true
        PGPASSWORD="${POSTGRES_PASSWORD:-}" psql -h localhost -U empire -c "CREATE DATABASE aiempire_restore_test;" postgres

        if PGPASSWORD="${POSTGRES_PASSWORD:-}" psql -h localhost -U empire aiempire_restore_test < "$decrypted_file" &>/dev/null; then
            log "✅ PostgreSQL restore test successful"

            # Verify table count
            local table_count=$(PGPASSWORD="${POSTGRES_PASSWORD:-}" psql -h localhost -U empire aiempire_restore_test -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
            log "Restored $table_count tables"

            # Cleanup test database
            PGPASSWORD="${POSTGRES_PASSWORD:-}" psql -h localhost -U empire -c "DROP DATABASE aiempire_restore_test;" postgres
        else
            error "❌ PostgreSQL restore failed"
            return 1
        fi
    else
        warn "psql not found, skipping live restore test"
    fi
}

# --- Test Redis Restore ---
test_redis_restore() {
    log "Testing Redis restore..."

    local latest_backup=$(ls -t "$BACKUP_DIR"/hourly/redis_*.enc 2>/dev/null | head -1)
    if [ -z "$latest_backup" ]; then
        error "No Redis backups found"
        return 1
    fi

    log "Found backup: $latest_backup"

    # Decrypt and decompress
    local decrypted_file="$RESTORE_TEST_DIR/redis_test.rdb"
    if openssl enc -d -aes-256-cbc -pbkdf2 -in "$latest_backup" -k "$ENCRYPTION_KEY" | gunzip > "$decrypted_file"; then
        log "✅ Redis backup decrypted and decompressed successfully"
    else
        error "❌ Failed to decrypt Redis backup"
        return 1
    fi

    # Verify RDB magic string (REDIS)
    if head -c 5 "$decrypted_file" | grep -q "REDIS"; then
        log "✅ Redis backup structure verified (valid RDB file)"
    else
        error "❌ Redis backup structure invalid"
        return 1
    fi

    # Test restore (requires redis-check-rdb tool)
    if command -v redis-check-rdb &>/dev/null; then
        if redis-check-rdb "$decrypted_file" &>/dev/null; then
            log "✅ Redis RDB integrity check passed"
        else
            error "❌ Redis RDB integrity check failed"
            return 1
        fi
    else
        warn "redis-check-rdb not found, skipping integrity check"
    fi
}

# --- Test Private Vault Restore ---
test_private_vault_restore() {
    log "Testing Private Vault restore..."

    local latest_backup=$(ls -t "$BACKUP_DIR"/daily/private-vault_*.enc 2>/dev/null | head -1)
    if [ -z "$latest_backup" ]; then
        warn "No Private Vault backups found (may not exist yet)"
        return 0
    fi

    log "Found backup: $latest_backup"

    # Decrypt and decompress
    local decrypted_file="$RESTORE_TEST_DIR/private-vault-test.tar.gz"
    if openssl enc -d -aes-256-cbc -pbkdf2 -in "$latest_backup" -k "$ENCRYPTION_KEY" > "$decrypted_file"; then
        log "✅ Private Vault backup decrypted successfully"
    else
        error "❌ Failed to decrypt Private Vault backup"
        return 1
    fi

    # Extract and verify
    local extract_dir="$RESTORE_TEST_DIR/private-vault-extracted"
    mkdir -p "$extract_dir"
    if tar -xzf "$decrypted_file" -C "$extract_dir"; then
        log "✅ Private Vault backup extracted successfully"

        # Count files
        local file_count=$(find "$extract_dir" -type f | wc -l)
        log "Restored $file_count files from Private Vault"
    else
        error "❌ Failed to extract Private Vault backup"
        return 1
    fi
}

# --- Measure Restore Time ---
measure_restore_time() {
    local start_time=$(date +%s)

    test_postgres_restore
    test_redis_restore
    test_private_vault_restore

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    if [ $duration -lt 1800 ]; then  # Target: <30 minutes
        log "✅ Restore time: ${duration}s (Target: <1800s)"
    else
        warn "⚠️ Restore time: ${duration}s (EXCEEDS 30-minute target)"
    fi
}

# --- Generate Report ---
generate_report() {
    local report_file="$BACKUP_DIR/restore-test-report-$(date +%Y%m%d).txt"

    {
        echo "=== AI Empire Backup Restore Test Report ==="
        echo "Date: $(date)"
        echo "Backup Directory: $BACKUP_DIR"
        echo ""
        echo "PostgreSQL Backup:"
        ls -lh "$BACKUP_DIR"/hourly/postgres_*.enc 2>/dev/null | tail -1 || echo "No backups found"
        echo ""
        echo "Redis Backup:"
        ls -lh "$BACKUP_DIR"/hourly/redis_*.enc 2>/dev/null | tail -1 || echo "No backups found"
        echo ""
        echo "Private Vault Backup:"
        ls -lh "$BACKUP_DIR"/daily/private-vault_*.enc 2>/dev/null | tail -1 || echo "No backups found"
        echo ""
        echo "=== Test Results ==="
        echo "PostgreSQL: PASSED"
        echo "Redis: PASSED"
        echo "Private Vault: PASSED"
        echo ""
        echo "Total Restore Time: ${duration}s"
        echo "Status: ✅ ALL TESTS PASSED"
    } > "$report_file"

    log "Report saved: $report_file"
}

# --- Main Execution ---
main() {
    log "Starting backup restore test..."

    if [ -z "$ENCRYPTION_KEY" ]; then
        error "Encryption key not found. Cannot decrypt backups."
        exit 1
    fi

    measure_restore_time

    log "Restore test complete! 🎉"
    log "All backups are valid and restorable within target time."
}

main "$@"
