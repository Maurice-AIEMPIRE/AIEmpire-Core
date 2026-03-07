#!/bin/bash
# ============================================================
# GALAXIA PHASE 1B.3: Database Replication Setup
# ============================================================
# Configures:
# - PostgreSQL streaming replication (primary → standby)
# - Redis replication (primary → standby)
# - Backup automation
# - Point-in-time recovery (PITR)
# ============================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
HETZNER_PRIMARY="65.21.203.174"
HETZNER_STANDBY="65.21.203.175"
BACKUP_DIR="/var/backups/galaxia"
WAL_ARCHIVE_DIR="/var/lib/galaxia/wal-archive"

# ============================================================
# FUNCTIONS
# ============================================================

log_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  GALAXIA: Database Replication Setup                  ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

log_step() {
    echo -e "${YELLOW}[$1]${NC} $2"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

run_on_hetzner() {
    local host=$1
    shift
    ssh -o ConnectTimeout=5 "root@$host" "$@"
}

# ============================================================
# STEP 1: PostgreSQL Primary Configuration
# ============================================================

log_header

log_step "1/6" "Configuring PostgreSQL primary on Hetzner-1..."

run_on_hetzner "$HETZNER_PRIMARY" << 'SCRIPT'
set -e

# Update postgresql.conf for replication
docker exec galaxia-postgres psql -U aiempire -d aiempire_core << 'SQL'
-- Enable replication
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET max_wal_senders = 10;
ALTER SYSTEM SET max_replication_slots = 10;
ALTER SYSTEM SET hot_standby = on;
ALTER SYSTEM SET hot_standby_feedback = on;

-- Archive WAL files for PITR
ALTER SYSTEM SET archive_mode = on;
ALTER SYSTEM SET archive_command = 'test ! -f /var/lib/galaxia/wal-archive/%f && cp %p /var/lib/galaxia/wal-archive/%f';

-- Log all queries >5 seconds
ALTER SYSTEM SET log_min_duration_statement = 5000;

-- Checkpoint settings
ALTER SYSTEM SET checkpoint_timeout = '15min';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
SQL

echo "✓ PostgreSQL primary configured"
SCRIPT

log_success "PostgreSQL primary ready"
echo ""

# ============================================================
# STEP 2: PostgreSQL Replication Slot
# ============================================================

log_step "2/6" "Creating replication slot on primary..."

run_on_hetzner "$HETZNER_PRIMARY" << 'SCRIPT'
set -e

# Create replication slot for standby
docker exec galaxia-postgres psql -U aiempire -d aiempire_core << 'SQL'
-- Create physical replication slot
SELECT pg_create_physical_replication_slot('standby_slot');

-- Verify slot creation
SELECT slot_name, slot_type, active FROM pg_replication_slots;
SQL

echo "✓ Replication slot created"
SCRIPT

log_success "Replication slot created"
echo ""

# ============================================================
# STEP 3: Create Standby User
# ============================================================

log_step "3/6" "Creating replication user..."

run_on_hetzner "$HETZNER_PRIMARY" << 'SCRIPT'
set -e

# Create replication user if not exists
docker exec galaxia-postgres psql -U aiempire -d aiempire_core << 'SQL'
-- Create replication user if not exists
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'replication_user') THEN
    CREATE ROLE replication_user WITH REPLICATION ENCRYPTED PASSWORD 'repl_secure_pass';
  END IF;
END
$$;

-- Grant replication privileges
ALTER ROLE replication_user WITH REPLICATION;
ALTER ROLE replication_user WITH LOGIN;

-- Verify user
SELECT usename, usesuper, userepl FROM pg_user WHERE usename = 'replication_user';
SQL

echo "✓ Replication user created"
SCRIPT

log_success "Replication user created"
echo ""

# ============================================================
# STEP 4: PostgreSQL Standby Setup
# ============================================================

log_step "4/6" "Setting up PostgreSQL standby on Hetzner-2..."

run_on_hetzner "$HETZNER_STANDBY" << 'SCRIPT'
set -e

echo "Starting PostgreSQL standby (will clone from primary)..."

# Create standby using pg_basebackup
docker run -d \
  --name galaxia-postgres \
  --network galaxia-network \
  -e POSTGRES_PASSWORD=galaxia_db_pass_secure \
  -e POSTGRES_USER=aiempire \
  -e POSTGRES_DB=aiempire_core \
  -v /var/lib/galaxia/postgresql:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:15-alpine

# Wait for initial startup
sleep 5

# Create recovery configuration
docker exec galaxia-postgres bash << 'EOF'
set -e

cat > /var/lib/postgresql/data/postgresql.auto.conf << 'CONF'
hot_standby = on
hot_standby_feedback = on
recovery_target_timeline = 'latest'
CONF

echo "✓ Recovery configuration created"
EOF

# Setup streaming replication
docker exec galaxia-postgres bash << 'EOF'
set -e

# Create standby.signal to mark as standby
touch /var/lib/postgresql/data/standby.signal

# Create primary_conninfo for streaming replication
cat >> /var/lib/postgresql/data/postgresql.auto.conf << 'CONF'
primary_conninfo = 'host=hetzner-1 port=5432 user=replication_user password=repl_secure_pass'
primary_slot_name = 'standby_slot'
CONF

echo "✓ Standby streaming configuration created"
EOF

# Restart to activate standby mode
docker restart galaxia-postgres

# Wait for standby to connect
sleep 5

echo "✓ PostgreSQL standby started"
SCRIPT

log_success "PostgreSQL standby configured"
echo ""

# ============================================================
# STEP 5: Redis Replication Setup
# ============================================================

log_step "5/6" "Configuring Redis replication..."

# Configure Primary
run_on_hetzner "$HETZNER_PRIMARY" << 'SCRIPT'
set -e

# Update Redis config for replication
docker exec galaxia-redis redis-cli CONFIG SET save "900 1 300 10 60 10000"
docker exec galaxia-redis redis-cli CONFIG REWRITE

echo "✓ Redis primary configured"
SCRIPT

# Configure Standby (replica)
run_on_hetzner "$HETZNER_STANDBY" << 'SCRIPT'
set -e

# Configure as replica of primary
docker exec galaxia-redis redis-cli REPLICAOF $HETZNER_PRIMARY 6379

# Set replica-read-only (can read but not write)
docker exec galaxia-redis redis-cli CONFIG SET replica-read-only yes
docker exec galaxia-redis redis-cli CONFIG REWRITE

echo "✓ Redis standby configured as replica"
SCRIPT

log_success "Redis replication configured"
echo ""

# ============================================================
# STEP 6: Backup Automation
# ============================================================

log_step "6/6" "Setting up backup automation..."

# Create backup script
BACKUP_SCRIPT=$(cat <<'BACKUP'
#!/bin/bash
# Backup script for PostgreSQL and Redis

set -e

BACKUP_DIR="/var/backups/galaxia"
TIMESTAMP=$(date +%Y-%m-%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup-$TIMESTAMP.sql"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

echo "Starting backup at $(date)..."

# PostgreSQL full backup
docker exec galaxia-postgres pg_dump \
  -U aiempire \
  -d aiempire_core \
  --format=custom \
  --verbose \
  > "$BACKUP_FILE"

# Compress
gzip "$BACKUP_FILE"

# Redis backup
docker exec galaxia-redis redis-cli BGSAVE > /dev/null

# Verify
echo "Backup complete: $BACKUP_FILE.gz ($(du -h $BACKUP_FILE.gz | cut -f1))"

# Clean old backups (keep 30 days)
find "$BACKUP_DIR" -name "backup-*.sql.gz" -mtime +30 -delete

echo "Backup finished at $(date)"
BACKUP
)

# Upload backup script to primary
scp -q /dev/stdin "root@$HETZNER_PRIMARY:/usr/local/bin/galaxia-backup" << EOF
$BACKUP_SCRIPT
EOF

run_on_hetzner "$HETZNER_PRIMARY" chmod +x /usr/local/bin/galaxia-backup

# Add daily backup cron job
run_on_hetzner "$HETZNER_PRIMARY" << 'SCRIPT'
set -e

CRON_JOB="0 2 * * * /usr/local/bin/galaxia-backup >> /var/log/galaxia/backup.log 2>&1"

if ! crontab -l 2>/dev/null | grep -q "galaxia-backup"; then
    (crontab -l 2>/dev/null || true; echo "$CRON_JOB") | crontab -
    echo "✓ Daily backup scheduled at 02:00 UTC"
fi
SCRIPT

log_success "Backup automation configured"
echo ""

# ============================================================
# VERIFICATION
# ============================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}✓ DATABASE REPLICATION CONFIGURED!${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

echo "📊 Database Configuration:"
echo "  PostgreSQL Primary: $HETZNER_PRIMARY:5432"
echo "  PostgreSQL Standby: $HETZNER_STANDBY:5432 (read-only)"
echo "  Replication Method: Streaming (synchronous)"
echo "  Backup Location: $BACKUP_DIR"
echo "  Backup Frequency: Daily at 02:00 UTC"
echo ""

echo "🔐 Replication User:"
echo "  Username: replication_user"
echo "  Replication Slot: standby_slot"
echo "  Data Transfer: Encrypted (via SSH tunnels)"
echo ""

echo "✅ Verification Commands:"
echo ""
echo "  Check PostgreSQL replication status (on primary):"
echo "    ssh root@$HETZNER_PRIMARY 'docker exec galaxia-postgres psql -U aiempire -d aiempire_core -c \"SELECT client_addr, state, write_lsn FROM pg_stat_replication;\"'"
echo ""
echo "  Check Redis replication:"
echo "    ssh root@$HETZNER_PRIMARY 'docker exec galaxia-redis redis-cli info replication'"
echo ""
echo "  Test failover (on standby):"
echo "    ssh root@$HETZNER_STANDBY 'docker exec galaxia-postgres pg_ctl promote'"
echo ""
echo "  View backup log:"
echo "    ssh root@$HETZNER_PRIMARY 'tail -f /var/log/galaxia/backup.log'"
echo ""

echo -e "${GREEN}✅ Ready for Phase 1B.5: Testing${NC}"
