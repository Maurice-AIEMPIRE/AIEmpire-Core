#!/usr/bin/env bash
# =============================================================================
# Server → Mac iCloud Sync — läuft als Cron auf Hetzner (alle 5 Min)
# =============================================================================
# Syncт /data/results/ und /data/empire.db Exports zurück auf den Mac
# Mac legt sie automatisch in iCloud ab (AIEmpire-Results/)
#
# Cron einrichten (auf Server):
#   crontab -e
#   */5 * * * * /root/AIEmpire-Core/scripts/server_sync_back.sh
# =============================================================================

set -euo pipefail

PROJECT="/root/AIEmpire-Core"
RESULTS_DIR="/data/results"
DB_PATH="/data/empire.db"
LOG="/var/log/aiempire-sync.log"
CONFIG="$PROJECT/.env"

# ─── Config laden ─────────────────────────────────────────────────────────────
if [[ -f "$CONFIG" ]]; then
    while IFS='=' read -r key value; do
        [[ "$key" =~ ^# ]] && continue; [[ -z "$key" ]] && continue
        value="${value%\"*}"; value="${value#\"}"
        export "$key"="$value" 2>/dev/null || true
    done < <(grep -v '^#' "$CONFIG" | grep '=')
fi

MAC_USER="${MAC_USER:-}"
MAC_HOST="${MAC_HOST:-}"
MAC_KEY="${SERVER_KEY_PATH:-/root/.ssh/id_rsa}"
ICLOUD_PATH="${MAC_ICLOUD_PATH:-/Users/$MAC_USER/Library/Mobile Documents/com~apple~CloudDocs}"
RESULTS_FOLDER="${MAC_RESULTS_FOLDER:-AIEmpire-Results}"
REMOTE_DEST="${MAC_USER}@${MAC_HOST}:${ICLOUD_PATH}/${RESULTS_FOLDER}/"

mkdir -p "$(dirname "$LOG")"
exec >> "$LOG" 2>&1

if [[ -z "$MAC_HOST" ]]; then
    echo "$(date) SKIP: MAC_HOST nicht gesetzt"
    exit 0
fi

SSH_OPTS="-i $MAC_KEY -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=10"

# Verbindungscheck
if ! ssh $SSH_OPTS "${MAC_USER}@${MAC_HOST}" "echo ok" &>/dev/null; then
    echo "$(date) SKIP: Mac nicht erreichbar ($MAC_HOST)"
    exit 0
fi

echo "$(date) Sync gestartet → $REMOTE_DEST"

# ─── 1. DB-Exports aktualisieren ─────────────────────────────────────────────
python3 "$PROJECT/data_processor/database.py" export >> "$LOG" 2>&1 || true

# ─── 2. Results → iCloud ──────────────────────────────────────────────────────
if [[ -d "$RESULTS_DIR" ]]; then
    rsync -avz --delete --timeout=30 \
        -e "ssh $SSH_OPTS" \
        --exclude="*.tmp" \
        --exclude=".DS_Store" \
        "$RESULTS_DIR/" \
        "$REMOTE_DEST" && echo "$(date) OK: Results synct"
fi

# ─── 3. Input-Ordner aufräumen (verarbeitete Dateien löschen) ─────────────────
# Dateien die älter als 24h in /data/input/ sind → löschen (schon verarbeitet)
find /data/input/ -type f -mmin +1440 -delete 2>/dev/null && true

echo "$(date) Sync fertig"
