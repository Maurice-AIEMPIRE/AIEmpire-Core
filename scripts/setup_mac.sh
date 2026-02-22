#!/usr/bin/env bash
# =============================================================================
# AIEmpire — Einmaliges Mac-Setup (vollautomatisch)
# =============================================================================
#
#   bash ~/AIEmpire-Core/scripts/setup_mac.sh
#
# Was dieses Script macht (automatisch, ohne weiteres Zutun):
#   1. Server-IP abfragen
#   2. SSH-Key erstellen falls nötig
#   3. SSH-Key auf Server kopieren (einmal Passwort eingeben)
#   4. iCloud-Ordner erstellen (AIEmpire-Input + AIEmpire-Results)
#   5. fswatch installieren (Homebrew)
#   6. Watcher als macOS LaunchAgent installieren (startet bei jedem Boot)
#   7. Befehle empire-upload + empire-status installieren
#   8. Server-Cron einrichten (alle 5 Min sync zurück zu iCloud)
#   9. Pipeline auf Server starten
#
# Danach: Dateien in iCloud "AIEmpire-Input" ablegen → fertig.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ICLOUD_BASE="$HOME/Library/Mobile Documents/com~apple~CloudDocs"
CONFIG="$HOME/.empire_config"
LOG_DIR="$HOME/Library/Logs"
PLIST="$HOME/Library/LaunchAgents/com.aiempire.watcher.plist"

# ─── Farben + Hilfsfunktionen ─────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
ok()   { echo -e "${GREEN}  ✅ $*${RESET}"; }
info() { echo -e "${CYAN}  ℹ  $*${RESET}"; }
warn() { echo -e "${YELLOW}  ⚠  $*${RESET}"; }
err()  { echo -e "${RED}  ❌ $*${RESET}" >&2; }
step() { echo ""; echo -e "${BOLD}${CYAN}▶ $*${RESET}"; }
line() { echo -e "  ${CYAN}──────────────────────────────────────${RESET}"; }

clear
echo ""
echo -e "${BOLD}${CYAN}"
echo "  ╔════════════════════════════════════════════╗"
echo "  ║       AIEmpire Data Pipeline Setup         ║"
echo "  ║   iCloud → Hetzner → KI → iCloud zurück   ║"
echo "  ╚════════════════════════════════════════════╝"
echo -e "${RESET}"
echo "  Dieses Script richtet alles einmalig ein."
echo "  Danach legst du Dateien in iCloud ab — fertig."
echo ""

# ═══════════════════════════════════════════════════════════════════
# SCHRITT 1: Server-IP
# ═══════════════════════════════════════════════════════════════════
step "Schritt 1/8 — Server-Verbindung"
line

# Bestehende Config laden falls vorhanden
[[ -f "$CONFIG" ]] && source "$CONFIG" 2>/dev/null || true

if [[ -n "${SERVER_HOST:-}" ]]; then
    echo -e "  Aktuelle Server-IP: ${CYAN}$SERVER_HOST${RESET}"
    echo -n "  Andere IP eingeben? (Enter = beibehalten): "
    read -r NEW_HOST
    [[ -n "$NEW_HOST" ]] && SERVER_HOST="$NEW_HOST"
else
    echo -e "  Gib die IP-Adresse deines Hetzner-Servers ein:"
    echo -n "  Server-IP: "
    read -r SERVER_HOST
fi

SERVER_USER="${SERVER_USER:-root}"
SERVER_PORT="${SERVER_PORT:-22}"

# ═══════════════════════════════════════════════════════════════════
# SCHRITT 2: SSH-Key
# ═══════════════════════════════════════════════════════════════════
step "Schritt 2/8 — SSH-Key"
line

# Vorhandene Keys finden
AVAILABLE_KEYS=()
for k in "$HOME/.ssh/id_ed25519" "$HOME/.ssh/id_rsa" "$HOME/.ssh/id_ecdsa"; do
    [[ -f "$k" ]] && AVAILABLE_KEYS+=("$k")
done

if [[ ${#AVAILABLE_KEYS[@]} -eq 0 ]]; then
    info "Erstelle neuen SSH-Key (ed25519)..."
    ssh-keygen -t ed25519 -C "aiempire@$(hostname)" -f "$HOME/.ssh/id_ed25519" -N ""
    AVAILABLE_KEYS=("$HOME/.ssh/id_ed25519")
    ok "Neuer SSH-Key erstellt: ~/.ssh/id_ed25519"
elif [[ ${#AVAILABLE_KEYS[@]} -eq 1 ]]; then
    SERVER_KEY_PATH="${AVAILABLE_KEYS[0]}"
    ok "SSH-Key gefunden: $SERVER_KEY_PATH"
else
    echo "  Mehrere SSH-Keys vorhanden:"
    for i in "${!AVAILABLE_KEYS[@]}"; do
        echo "    $((i+1))) ${AVAILABLE_KEYS[$i]}"
    done
    echo -n "  Welchen verwenden? (1-${#AVAILABLE_KEYS[@]}): "
    read -r CHOICE
    SERVER_KEY_PATH="${AVAILABLE_KEYS[$((CHOICE-1))]}"
    ok "Verwende: $SERVER_KEY_PATH"
fi

# ═══════════════════════════════════════════════════════════════════
# SCHRITT 3: SSH-Key auf Server kopieren + Verbindung testen
# ═══════════════════════════════════════════════════════════════════
step "Schritt 3/8 — Server verbinden"
line

info "Kopiere SSH-Key auf Server (gibt einmal das Root-Passwort ein)..."
echo ""
ssh-copy-id -i "${SERVER_KEY_PATH}.pub" \
    -p "$SERVER_PORT" \
    "${SERVER_USER}@${SERVER_HOST}" 2>/dev/null || {
    warn "ssh-copy-id fehlgeschlagen (Key evtl. bereits vorhanden)"
}
echo ""

SSH_CMD="ssh -i $SERVER_KEY_PATH -p $SERVER_PORT -o StrictHostKeyChecking=no -o ConnectTimeout=15 -o BatchMode=yes"

echo -n "  Teste Verbindung... "
if $SSH_CMD "${SERVER_USER}@${SERVER_HOST}" "echo ok" &>/dev/null; then
    ok "Verbindung erfolgreich!"
else
    err "Verbindung fehlgeschlagen! Bitte prüfen:"
    echo "    IP: $SERVER_HOST"
    echo "    User: $SERVER_USER"
    echo "    Key: $SERVER_KEY_PATH"
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════
# SCHRITT 4: iCloud-Ordner erstellen
# ═══════════════════════════════════════════════════════════════════
step "Schritt 4/8 — iCloud-Ordner"
line

INPUT_FOLDER="$ICLOUD_BASE/AIEmpire-Input"
RESULTS_FOLDER="$ICLOUD_BASE/AIEmpire-Results"

mkdir -p "$INPUT_FOLDER"
mkdir -p "$RESULTS_FOLDER"
mkdir -p "$RESULTS_FOLDER/_Datenbank"
mkdir -p "$RESULTS_FOLDER/Vertraege"
mkdir -p "$RESULTS_FOLDER/Rechnungen"
mkdir -p "$RESULTS_FOLDER/Berichte"
mkdir -p "$RESULTS_FOLDER/Notizen"
mkdir -p "$RESULTS_FOLDER/Daten"
mkdir -p "$RESULTS_FOLDER/Sonstiges"

# Willkommens-Datei
cat > "$INPUT_FOLDER/HIER_DATEIEN_ABLEGEN.txt" <<'EOF'
AIEmpire Input-Ordner
=====================
Lege hier beliebige Dateien ab:
  PDF, Word, Excel, PowerPoint
  Bilder (JPG, PNG)
  Audio (MP3, WAV, M4A)
  CSV, JSON, TXT

Die Dateien werden automatisch:
  1. Zum Server übertragen
  2. Von KI analysiert und klassifiziert
  3. In AIEmpire-Results/ abgelegt

Diese Datei hier lassen — sie stört nicht.
EOF

ok "iCloud-Ordner erstellt:"
info "  Eingabe:  iCloud Drive/AIEmpire-Input/"
info "  Ausgabe:  iCloud Drive/AIEmpire-Results/"

# ═══════════════════════════════════════════════════════════════════
# SCHRITT 5: Konfiguration speichern
# ═══════════════════════════════════════════════════════════════════
step "Schritt 5/8 — Konfiguration"
line

cat > "$CONFIG" <<EOF
# AIEmpire Konfiguration — $(date)
SERVER_HOST=$SERVER_HOST
SERVER_USER=$SERVER_USER
SERVER_PORT=$SERVER_PORT
SERVER_KEY_PATH=$SERVER_KEY_PATH
SERVER_INPUT_DIR=/data/input
MAC_USER=$(whoami)
MAC_HOST=$(ipconfig getifaddr en0 2>/dev/null || hostname)
MAC_ICLOUD_PATH=$ICLOUD_BASE
MAC_RESULTS_FOLDER=AIEmpire-Results
EOF

ok "Konfiguration gespeichert: ~/.empire_config"

# ═══════════════════════════════════════════════════════════════════
# SCHRITT 6: fswatch installieren (Homebrew)
# ═══════════════════════════════════════════════════════════════════
step "Schritt 6/8 — Watcher-Software (fswatch)"
line

if command -v fswatch &>/dev/null; then
    ok "fswatch bereits installiert"
else
    if command -v brew &>/dev/null; then
        info "Installiere fswatch via Homebrew..."
        brew install fswatch
        ok "fswatch installiert"
    else
        warn "Homebrew nicht gefunden — nutze Polling statt fswatch"
        info "Homebrew installieren: https://brew.sh"
    fi
fi

# ═══════════════════════════════════════════════════════════════════
# SCHRITT 7: LaunchAgent installieren
# ═══════════════════════════════════════════════════════════════════
step "Schritt 7/8 — Auto-Start einrichten (LaunchAgent)"
line

WATCHER_SCRIPT="$SCRIPT_DIR/mac_icloud_watcher.sh"
chmod +x "$WATCHER_SCRIPT"

# Plist mit echten Pfaden befüllen
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aiempire.watcher</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$WATCHER_SCRIPT</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>ThrottleInterval</key>
    <integer>10</integer>

    <key>StandardOutPath</key>
    <string>$LOG_DIR/aiempire-watcher.log</string>

    <key>StandardErrorPath</key>
    <string>$LOG_DIR/aiempire-watcher.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>HOME</key>
        <string>$HOME</string>
    </dict>
</dict>
</plist>
EOF

# Lade LaunchAgent (stoppe alten falls vorhanden)
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
ok "LaunchAgent installiert — Watcher startet automatisch bei jedem Mac-Boot"

# ═══════════════════════════════════════════════════════════════════
# SCHRITT 8: Server-Cron + Pipeline starten
# ═══════════════════════════════════════════════════════════════════
step "Schritt 8/8 — Server einrichten"
line

SYNC_SCRIPT="/root/AIEmpire-Core/scripts/server_sync_back.sh"
SERVER_PROJECT="/root/AIEmpire-Core"

# Config auf Server kopieren
info "Kopiere Konfiguration auf Server..."
scp -i "$SERVER_KEY_PATH" -P "$SERVER_PORT" \
    "$CONFIG" \
    "${SERVER_USER}@${SERVER_HOST}:/root/AIEmpire-Core/.env" 2>/dev/null || \
    warn "Konfiguration manuell auf Server kopieren"

# Server einrichten
info "Richte Server ein (Datenbank + Cron + Daemon)..."
$SSH_CMD "${SERVER_USER}@${SERVER_HOST}" bash << SERVERSCRIPT
set -e

# Verzeichnisse anlegen
mkdir -p /data/input /data/results /data/processed
chmod +x $SERVER_PROJECT/scripts/server_sync_back.sh 2>/dev/null || true

# Datenbank initialisieren
cd $SERVER_PROJECT
python3 data_processor/database.py stats 2>/dev/null || python3 -c "
import sys; sys.path.insert(0, '.')
from data_processor.database import init_db
init_db()
print('DB initialisiert')
" 2>/dev/null || true

# Cron einrichten (alle 5 Min: Ergebnisse nach Mac/iCloud syncen)
(crontab -l 2>/dev/null | grep -v aiempire; echo "*/5 * * * * $SYNC_SCRIPT >> /var/log/aiempire-sync.log 2>&1") | crontab -
echo "Cron eingerichtet"

# Pipeline-Daemon im Hintergrund starten (falls nicht schon läuft)
if ! pgrep -f "data_processor/main.py" > /dev/null; then
    nohup python3 $SERVER_PROJECT/data_processor/main.py daemon \
        > /var/log/aiempire-pipeline.log 2>&1 &
    echo "Pipeline-Daemon gestartet (PID \$!)"
else
    echo "Pipeline-Daemon läuft bereits"
fi
SERVERSCRIPT

ok "Server eingerichtet"

# ─── Fertig! ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}"
echo "  ╔════════════════════════════════════════════╗"
echo "  ║         Setup abgeschlossen! 🎉            ║"
echo "  ╚════════════════════════════════════════════╝"
echo -e "${RESET}"
echo ""
echo -e "${BOLD}So verwendest du die Pipeline:${RESET}"
echo ""
echo -e "  1. Öffne ${CYAN}Finder → iCloud Drive → AIEmpire-Input${RESET}"
echo -e "  2. Lege beliebige Dateien dort ab"
echo -e "  3. KI analysiert automatisch"
echo -e "  4. Ergebnisse erscheinen in ${CYAN}iCloud Drive → AIEmpire-Results${RESET}"
echo ""
echo -e "${BOLD}Unterstützte Dateitypen:${RESET}"
echo "  PDF • Word • Excel • PowerPoint • Bilder • Audio • CSV • JSON"
echo ""
echo -e "${BOLD}Logs:${RESET}"
echo -e "  Mac-Watcher:  ${CYAN}tail -f ~/Library/Logs/aiempire-watcher.log${RESET}"
echo -e "  Server:       ${CYAN}ssh root@$SERVER_HOST 'tail -f /var/log/aiempire-pipeline.log'${RESET}"
echo ""
