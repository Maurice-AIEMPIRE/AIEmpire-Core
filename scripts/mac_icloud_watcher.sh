#!/usr/bin/env bash
# =============================================================================
# AIEmpire iCloud Watcher — läuft dauerhaft auf dem Mac
# =============================================================================
# Überwacht ~/iCloud Drive/AIEmpire-Input/
# Neue Datei → sofort per rsync zum Hetzner-Server → Server analysiert
# Dieser Script wird als macOS LaunchAgent automatisch bei jedem Start geladen.
# =============================================================================

ICLOUD_BASE="$HOME/Library/Mobile Documents/com~apple~CloudDocs"
INPUT_FOLDER="$ICLOUD_BASE/AIEmpire-Input"
LOG_FILE="$HOME/Library/Logs/aiempire-watcher.log"
LOCK_FILE="/tmp/aiempire-watcher.lock"
CONFIG="$HOME/.empire_config"

# ─── Config laden ─────────────────────────────────────────────────────────────
if [[ ! -f "$CONFIG" ]]; then
    echo "$(date) FEHLER: ~/.empire_config nicht gefunden. Bitte setup_mac.sh ausführen." >> "$LOG_FILE"
    exit 1
fi
# shellcheck disable=SC1090
source "$CONFIG"

# ─── Duplikat-Schutz ──────────────────────────────────────────────────────────
if [[ -f "$LOCK_FILE" ]]; then
    OLD_PID=$(cat "$LOCK_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "$(date) Watcher läuft bereits (PID $OLD_PID)" >> "$LOG_FILE"
        exit 0
    fi
fi
echo $$ > "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

# ─── Ordner anlegen ──────────────────────────────────────────────────────────
mkdir -p "$INPUT_FOLDER"
mkdir -p "$(dirname "$LOG_FILE")"

echo "$(date) AIEmpire iCloud Watcher gestartet" >> "$LOG_FILE"
echo "$(date) Überwache: $INPUT_FOLDER" >> "$LOG_FILE"
echo "$(date) Server: ${SERVER_USER}@${SERVER_HOST}:${SERVER_INPUT_DIR}" >> "$LOG_FILE"

# ─── Verbindungstest beim Start ───────────────────────────────────────────────
SSH_OPTS="-i $SERVER_KEY_PATH -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=10"
if ! ssh $SSH_OPTS "${SERVER_USER}@${SERVER_HOST}" "mkdir -p ${SERVER_INPUT_DIR} && echo ok" &>/dev/null; then
    echo "$(date) WARNUNG: Server nicht erreichbar — warte auf Verbindung..." >> "$LOG_FILE"
fi

# ─── Upload-Funktion ──────────────────────────────────────────────────────────
upload_file() {
    local FILE="$1"
    local NAME
    NAME=$(basename "$FILE")

    # Warte kurz bis Datei vollständig von iCloud runtergeladen ist
    sleep 3

    # iCloud Placeholder (.icloud) überspringen (noch nicht runtergeladen)
    if [[ "$NAME" == .*.icloud ]]; then
        echo "$(date) SKIP (iCloud-Placeholder): $NAME" >> "$LOG_FILE"
        return
    fi

    # Versteckte Dateien überspringen
    if [[ "$NAME" == .* ]] || [[ "$NAME" == *~ ]]; then
        return
    fi

    # Bereits-hochgeladen Check (Tracking-Datei)
    TRACKING_FILE="$HOME/.empire_uploaded"
    touch "$TRACKING_FILE"
    if grep -qF "$FILE" "$TRACKING_FILE" 2>/dev/null; then
        echo "$(date) SKIP (bereits hochgeladen): $NAME" >> "$LOG_FILE"
        return
    fi

    echo "$(date) UPLOAD: $NAME" >> "$LOG_FILE"

    # rsync zum Server
    if rsync -avz --timeout=60 \
        -e "ssh $SSH_OPTS" \
        "$FILE" \
        "${SERVER_USER}@${SERVER_HOST}:${SERVER_INPUT_DIR}/" \
        >> "$LOG_FILE" 2>&1; then

        echo "$(date) OK: $NAME erfolgreich hochgeladen" >> "$LOG_FILE"
        echo "$FILE" >> "$TRACKING_FILE"

        # Mac-Benachrichtigung
        osascript -e "display notification \"$NAME wird analysiert...\" with title \"AIEmpire\" subtitle \"Hochgeladen zum Server\"" 2>/dev/null || true
    else
        echo "$(date) FEHLER: Upload fehlgeschlagen für $NAME" >> "$LOG_FILE"
    fi
}

# ─── Batch-Check: alle vorhandenen Dateien prüfen ─────────────────────────────
echo "$(date) Prüfe vorhandene Dateien in Input-Ordner..." >> "$LOG_FILE"
for FILE in "$INPUT_FOLDER"/*; do
    [[ -f "$FILE" ]] && upload_file "$FILE"
done

# ─── fswatch Loop ─────────────────────────────────────────────────────────────
# Reagiert auf neue Dateien in Echtzeit (0 Latenz)
if command -v fswatch &>/dev/null; then
    echo "$(date) fswatch aktiv — warte auf neue Dateien..." >> "$LOG_FILE"
    fswatch -0 -r --event Created --event Renamed --event MovedTo \
        "$INPUT_FOLDER" | while IFS= read -r -d '' FILE; do
        [[ -f "$FILE" ]] && upload_file "$FILE"
    done
else
    # Fallback: Polling alle 30 Sekunden (wenn fswatch nicht installiert)
    echo "$(date) WARNUNG: fswatch nicht gefunden — nutze Polling (alle 30s)" >> "$LOG_FILE"
    while true; do
        for FILE in "$INPUT_FOLDER"/*; do
            [[ -f "$FILE" ]] && upload_file "$FILE"
        done
        sleep 30
    done
fi
