#!/usr/bin/env bash
# =============================================================================
# mac_upload.sh — Einfacher Daten-Upload vom Mac zum AIEmpire Server
# =============================================================================
#
# Nutzung:
#   ./mac_upload.sh datei.pdf
#   ./mac_upload.sh /Users/maurice/Documents/Rechnung.pdf
#   ./mac_upload.sh /Users/maurice/Downloads/mein-ordner/
#   ./mac_upload.sh *.pdf
#
# Was passiert:
#   1. Datei(en) werden per rsync auf den Server übertragen
#   2. Server verarbeitet automatisch (AI-Analyse, Klassifikation)
#   3. Ergebnisse kommen strukturiert in iCloud zurück
#      → ~/Library/Mobile Documents/com~apple~CloudDocs/AIEmpire-Results/
#
# Einmaliges Setup (auf Mac):
#   1. Diese Datei ausführbar machen: chmod +x mac_upload.sh
#   2. .env anpassen (SERVER_HOST, SERVER_USER, SERVER_KEY_PATH)
#   3. Optional: Script in ~/bin/ legen für globalen Zugriff
#      cp mac_upload.sh ~/bin/empire-upload && chmod +x ~/bin/empire-upload
# =============================================================================

set -euo pipefail

# ─── Konfiguration ───────────────────────────────────────────────────────────
# Entweder hier direkt setzen ODER in ~/.empire_config (wird automatisch geladen)
CONFIG_FILE="$HOME/.empire_config"
ENV_FILE="$(dirname "$0")/../.env"

# Defaults (werden durch Config überschrieben)
SERVER_HOST="${SERVER_HOST:-}"
SERVER_USER="${SERVER_USER:-root}"
SERVER_PORT="${SERVER_PORT:-22}"
SERVER_KEY_PATH="${SERVER_KEY_PATH:-$HOME/.ssh/id_rsa}"
SERVER_INPUT_DIR="${SERVER_INPUT_DIR:-/data/input}"

# ─── Config laden ─────────────────────────────────────────────────────────────
if [[ -f "$CONFIG_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$CONFIG_FILE"
fi

# .env aus Projekt laden (falls vorhanden)
if [[ -f "$ENV_FILE" ]]; then
    while IFS='=' read -r key value; do
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue
        value="${value%\"}"
        value="${value#\"}"
        export "$key"="$value" 2>/dev/null || true
    done < <(grep -v '^#' "$ENV_FILE" | grep '=')
fi

# ─── Farben ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

log_info()  { echo -e "${BLUE}ℹ${RESET}  $*"; }
log_ok()    { echo -e "${GREEN}✅${RESET} $*"; }
log_warn()  { echo -e "${YELLOW}⚠️${RESET}  $*"; }
log_error() { echo -e "${RED}❌${RESET} $*" >&2; }
log_step()  { echo -e "${CYAN}▶${RESET}  ${BOLD}$*${RESET}"; }

# ─── Validierung ─────────────────────────────────────────────────────────────
usage() {
    echo -e "${BOLD}Empire Upload — Mac → Server → iCloud${RESET}"
    echo ""
    echo "Nutzung: $0 <datei_oder_ordner> [<datei2> ...]"
    echo ""
    echo "Beispiele:"
    echo "  $0 Rechnung.pdf"
    echo "  $0 ~/Downloads/Dokumente/"
    echo "  $0 *.csv"
    echo ""
    echo "Konfiguration in ~/.empire_config:"
    echo "  SERVER_HOST=123.456.789.0"
    echo "  SERVER_USER=root"
    echo "  SERVER_PORT=22"
    echo "  SERVER_KEY_PATH=~/.ssh/id_rsa"
    exit 1
}

if [[ $# -eq 0 ]]; then
    usage
fi

if [[ -z "$SERVER_HOST" ]]; then
    log_error "SERVER_HOST nicht gesetzt!"
    echo ""
    echo "Erstelle ~/.empire_config mit:"
    echo "  SERVER_HOST=deine.server.ip"
    echo "  SERVER_USER=root"
    echo "  SERVER_KEY_PATH=~/.ssh/id_rsa"
    exit 1
fi

# ─── SSH-Optionen ─────────────────────────────────────────────────────────────
SSH_OPTS=(
    -p "$SERVER_PORT"
    -i "$SERVER_KEY_PATH"
    -o "StrictHostKeyChecking=no"
    -o "ConnectTimeout=15"
    -o "BatchMode=yes"
)

RSYNC_OPTS=(
    --archive
    --compress
    --progress
    --human-readable
    --partial                    # Resume bei Abbruch
    --timeout=60
    -e "ssh ${SSH_OPTS[*]}"
)

REMOTE="${SERVER_USER}@${SERVER_HOST}:${SERVER_INPUT_DIR}/"

# ─── Verbindungstest ──────────────────────────────────────────────────────────
log_step "Verbinde mit Server $SERVER_HOST..."
if ! ssh "${SSH_OPTS[@]}" "$SERVER_USER@$SERVER_HOST" "mkdir -p $SERVER_INPUT_DIR && echo ok" &>/dev/null; then
    log_error "Verbindung zum Server fehlgeschlagen!"
    echo "  Host: $SERVER_HOST"
    echo "  User: $SERVER_USER"
    echo "  Port: $SERVER_PORT"
    echo "  Key:  $SERVER_KEY_PATH"
    exit 1
fi
log_ok "Verbunden mit $SERVER_HOST"

# ─── Upload ───────────────────────────────────────────────────────────────────
TOTAL=0
SUCCESS=0
FAILED=0

for SOURCE in "$@"; do
    if [[ ! -e "$SOURCE" ]]; then
        log_warn "Nicht gefunden: $SOURCE"
        ((FAILED++)) || true
        continue
    fi

    BASENAME=$(basename "$SOURCE")
    ((TOTAL++)) || true

    log_step "Upload: $BASENAME"

    if rsync "${RSYNC_OPTS[@]}" "$SOURCE" "$REMOTE"; then
        log_ok "Erfolgreich: $BASENAME"
        ((SUCCESS++)) || true
    else
        log_error "Fehlgeschlagen: $BASENAME"
        ((FAILED++)) || true
    fi
    echo ""
done

# ─── Zusammenfassung ─────────────────────────────────────────────────────────
echo "─────────────────────────────────────"
echo -e "${BOLD}Upload-Zusammenfassung:${RESET}"
echo -e "  Gesamt:      $TOTAL"
echo -e "  ${GREEN}Erfolgreich: $SUCCESS${RESET}"
[[ $FAILED -gt 0 ]] && echo -e "  ${RED}Fehlgeschlagen: $FAILED${RESET}"
echo ""

if [[ $SUCCESS -gt 0 ]]; then
    echo -e "${GREEN}Server analysiert die Dateien jetzt automatisch...${RESET}"
    echo ""
    echo "Ergebnisse kommen in:"
    echo "  📂 ~/Library/Mobile Documents/com~apple~CloudDocs/AIEmpire-Results/"
    echo ""
    echo "Tipp: Fortschritt auf Server überwachen:"
    echo "  ssh ${SERVER_USER}@${SERVER_HOST} 'tail -f /var/log/empire-pipeline.log'"
fi

exit $([[ $FAILED -eq 0 ]] && echo 0 || echo 1)
