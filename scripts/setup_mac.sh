#!/usr/bin/env bash
# =============================================================================
# Empire Setup — Einmaliges Mac-Setup für die Data Pipeline
# =============================================================================
# Ausführen mit: bash setup_mac.sh
# Danach einfach: empire-upload datei.pdf
# =============================================================================

set -euo pipefail

# ─── Farben ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

clear
echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}║       AIEmpire Data Pipeline — Mac Setup         ║${RESET}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════╝${RESET}"
echo ""
echo "  Einmaliges Setup. Danach: empire-upload datei.pdf"
echo ""

# ─── Schritt 1: Server-IP ────────────────────────────────────────────────────
echo -e "${BOLD}Schritt 1/4 — Server-Adresse${RESET}"
echo -e "  Gib die IP-Adresse deines Hetzner-Servers ein:"
echo -n "  Server-IP: "
read -r SERVER_HOST
echo ""

# ─── Schritt 2: SSH-Key ──────────────────────────────────────────────────────
echo -e "${BOLD}Schritt 2/4 — SSH-Key${RESET}"

# Suche vorhandene Keys
AVAILABLE_KEYS=()
for k in ~/.ssh/id_rsa ~/.ssh/id_ed25519 ~/.ssh/id_ecdsa; do
    [[ -f "$k" ]] && AVAILABLE_KEYS+=("$k")
done

if [[ ${#AVAILABLE_KEYS[@]} -eq 0 ]]; then
    echo -e "  ${YELLOW}Kein SSH-Key gefunden — erstelle neuen Key...${RESET}"
    ssh-keygen -t ed25519 -C "aiempire-mac" -f ~/.ssh/id_ed25519 -N ""
    AVAILABLE_KEYS=("$HOME/.ssh/id_ed25519")
    echo -e "  ${GREEN}✅ Neuer SSH-Key erstellt: ~/.ssh/id_ed25519${RESET}"
    echo ""
fi

if [[ ${#AVAILABLE_KEYS[@]} -eq 1 ]]; then
    SERVER_KEY_PATH="${AVAILABLE_KEYS[0]}"
    echo -e "  Verwende: ${CYAN}$SERVER_KEY_PATH${RESET}"
else
    echo "  Mehrere Keys gefunden. Welchen möchtest du verwenden?"
    for i in "${!AVAILABLE_KEYS[@]}"; do
        echo "  $((i+1))) ${AVAILABLE_KEYS[$i]}"
    done
    echo -n "  Auswahl (1-${#AVAILABLE_KEYS[@]}): "
    read -r KEY_CHOICE
    SERVER_KEY_PATH="${AVAILABLE_KEYS[$((KEY_CHOICE-1))]}"
fi
echo ""

# ─── Schritt 3: SSH-Key auf Server kopieren ───────────────────────────────────
echo -e "${BOLD}Schritt 3/4 — Verbindung einrichten${RESET}"
echo -e "  Kopiere SSH-Key auf Server (einmalig Passwort eingeben)..."
echo ""

SERVER_USER="root"
if ssh-copy-id -i "${SERVER_KEY_PATH}.pub" "${SERVER_USER}@${SERVER_HOST}" 2>/dev/null; then
    echo -e "  ${GREEN}✅ SSH-Key erfolgreich übertragen${RESET}"
else
    echo -e "  ${YELLOW}Hinweis: Entweder Key schon vorhanden oder manuelle Eingabe nötig${RESET}"
fi
echo ""

# Verbindungstest
echo -n "  Teste Verbindung... "
if ssh -o ConnectTimeout=10 -o BatchMode=yes -o StrictHostKeyChecking=no \
       -i "$SERVER_KEY_PATH" "${SERVER_USER}@${SERVER_HOST}" "echo ok" &>/dev/null; then
    echo -e "${GREEN}✅ Verbunden!${RESET}"
else
    echo -e "${RED}❌ Verbindung fehlgeschlagen${RESET}"
    echo "  Bitte prüfe ob der Server läuft und die IP stimmt."
    exit 1
fi
echo ""

# ─── Schritt 4: Konfiguration speichern ──────────────────────────────────────
echo -e "${BOLD}Schritt 4/4 — Konfiguration speichern${RESET}"

cat > "$HOME/.empire_config" <<EOF
# AIEmpire Mac Konfiguration — automatisch erstellt
SERVER_HOST=$SERVER_HOST
SERVER_USER=$SERVER_USER
SERVER_PORT=22
SERVER_KEY_PATH=$SERVER_KEY_PATH
SERVER_INPUT_DIR=/data/input
MAC_ICLOUD_PATH=$HOME/Library/Mobile Documents/com~apple~CloudDocs
MAC_RESULTS_FOLDER=AIEmpire-Results
EOF

echo -e "  ${GREEN}✅ Konfiguration gespeichert: ~/.empire_config${RESET}"

# ─── empire-upload Befehl installieren ───────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPLOAD_SCRIPT="$SCRIPT_DIR/mac_upload.sh"

# In ~/bin installieren (funktioniert ohne sudo)
mkdir -p "$HOME/bin"
cp "$UPLOAD_SCRIPT" "$HOME/bin/empire-upload"
chmod +x "$HOME/bin/empire-upload"

# Auch empire-status installieren
cat > "$HOME/bin/empire-status" <<'STATUSEOF'
#!/usr/bin/env bash
source "$HOME/.empire_config" 2>/dev/null || true
echo "AIEmpire Pipeline Status"
echo "========================"
echo "Server: $SERVER_HOST"
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes"
RESULT=$(ssh $SSH_OPTS -i "$SERVER_KEY_PATH" "${SERVER_USER}@${SERVER_HOST}" \
    "python3 /root/AIEmpire-Core/empire_engine.py pipeline status 2>/dev/null" 2>&1)
echo "$RESULT"
STATUSEOF
chmod +x "$HOME/bin/empire-status"

# PATH in Shell-Config eintragen (falls ~/bin noch nicht drin)
SHELL_CONFIG=""
if [[ -f "$HOME/.zshrc" ]]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [[ -f "$HOME/.bash_profile" ]]; then
    SHELL_CONFIG="$HOME/.bash_profile"
fi

if [[ -n "$SHELL_CONFIG" ]] && ! grep -q 'HOME/bin' "$SHELL_CONFIG"; then
    echo '' >> "$SHELL_CONFIG"
    echo '# AIEmpire Tools' >> "$SHELL_CONFIG"
    echo 'export PATH="$HOME/bin:$PATH"' >> "$SHELL_CONFIG"
    echo -e "  ${GREEN}✅ ~/bin zum PATH hinzugefügt in $SHELL_CONFIG${RESET}"
fi

# PATH für aktuelle Session setzen
export PATH="$HOME/bin:$PATH"

# ─── Fertig! ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${GREEN}║              Setup abgeschlossen!                ║${RESET}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "${BOLD}So verwendest du die Pipeline:${RESET}"
echo ""
echo -e "  ${CYAN}empire-upload Rechnung.pdf${RESET}"
echo -e "  ${CYAN}empire-upload ~/Downloads/mein-vertrag.docx${RESET}"
echo -e "  ${CYAN}empire-upload ~/Desktop/*.pdf${RESET}"
echo ""
echo -e "  ${CYAN}empire-status${RESET}   ← zeigt was der Server gerade macht"
echo ""
echo -e "Ergebnisse erscheinen automatisch in:"
echo -e "  ${BOLD}iCloud Drive → AIEmpire-Results/${RESET}"
echo -e "  (Vertraege / Rechnungen / Berichte / Notizen / Daten)"
echo ""
echo -e "${YELLOW}Hinweis: Terminal neu starten damit 'empire-upload' überall funktioniert${RESET}"
echo ""

# Schnelltest anbieten
echo -n "Willst du die Verbindung kurz testen? (j/n): "
read -r TEST_CHOICE
if [[ "$TEST_CHOICE" =~ ^[jJyY]$ ]]; then
    echo ""
    echo "  Verbindungstest..."
    ssh -i "$SERVER_KEY_PATH" -o StrictHostKeyChecking=no \
        "${SERVER_USER}@${SERVER_HOST}" \
        "echo '✅ Verbindung OK' && python3 /root/AIEmpire-Core/data_processor/main.py status 2>/dev/null || echo 'Pipeline bereit'"
fi
echo ""
