#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# TERMINUS FIX — SSH-Zugriff auf Mac aktivieren
# ═══════════════════════════════════════════════════════════════
# Dieses Script fixt die haeufigsten Probleme warum Terminus
# nicht mit dem Mac verbinden kann:
#
#   1. SSH nicht aktiviert
#   2. Firewall blockiert Port 22
#   3. Falsche IP-Adresse
#   4. macOS Privacy-Einstellungen
#
# Usage: bash telegram_bot/fix_terminus.sh
# ═══════════════════════════════════════════════════════════════

echo ""
echo "══════════════════════════════════════════════"
echo "  TERMINUS FIX — SSH aktivieren"
echo "══════════════════════════════════════════════"
echo ""

# ─── 1. Check & Enable SSH ──────────────────────────────────────
echo "[1/6] SSH Status pruefen..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    SSH_STATUS=$(sudo systemsetup -getremotelogin 2>/dev/null)
    echo "  Aktuell: $SSH_STATUS"

    if echo "$SSH_STATUS" | grep -qi "off"; then
        echo "  SSH aktivieren..."
        sudo systemsetup -setremotelogin on
        echo "  SSH: AKTIVIERT"
    else
        echo "  SSH: Bereits aktiv"
    fi
else
    # Linux
    if systemctl is-active --quiet sshd 2>/dev/null; then
        echo "  SSH: Aktiv"
    else
        echo "  SSH starten..."
        sudo systemctl enable --now sshd 2>/dev/null || sudo service ssh start 2>/dev/null
    fi
fi

# ─── 2. Firewall pruefen ────────────────────────────────────────
echo ""
echo "[2/6] Firewall pruefen..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    FW_STATUS=$(sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null)
    echo "  $FW_STATUS"

    if echo "$FW_STATUS" | grep -qi "enabled"; then
        echo "  Firewall ist AN — SSH-Ausnahme pruefen..."
        # Allow SSH through firewall
        sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/libexec/sshd-keygen-wrapper 2>/dev/null
        sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /usr/libexec/sshd-keygen-wrapper 2>/dev/null
        echo "  SSH-Ausnahme hinzugefuegt"
    else
        echo "  Firewall ist AUS — kein Problem"
    fi
fi

# ─── 3. IP-Adressen anzeigen ────────────────────────────────────
echo ""
echo "[3/6] Netzwerk-Adressen..."

if [[ "$OSTYPE" == "darwin"* ]]; then
    echo ""
    echo "  WLAN (en0):"
    WLAN_IP=$(ifconfig en0 2>/dev/null | grep "inet " | awk '{print $2}')
    echo "    IP: ${WLAN_IP:-Nicht verbunden}"

    echo "  Ethernet (en1):"
    ETH_IP=$(ifconfig en1 2>/dev/null | grep "inet " | awk '{print $2}')
    echo "    IP: ${ETH_IP:-Nicht verbunden}"

    # Thunderbolt/USB Ethernet
    echo "  Thunderbolt (en2-en5):"
    for i in 2 3 4 5; do
        TB_IP=$(ifconfig en$i 2>/dev/null | grep "inet " | awk '{print $2}')
        if [ -n "$TB_IP" ]; then
            echo "    en$i: $TB_IP"
        fi
    done

    LOCAL_IP="${WLAN_IP:-${ETH_IP:-Nicht gefunden}}"
else
    LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
    echo "  IP: $LOCAL_IP"
fi

# Externe IP
echo ""
echo "  Externe IP:"
EXT_IP=$(curl -s --connect-timeout 3 ifconfig.me 2>/dev/null)
echo "    ${EXT_IP:-Nicht erreichbar (offline?)}"

# ─── 4. SSH Port testen ─────────────────────────────────────────
echo ""
echo "[4/6] SSH Port 22 testen..."
if nc -z localhost 22 2>/dev/null; then
    echo "  Port 22: OFFEN (SSH laeuft)"
else
    echo "  Port 22: GESCHLOSSEN"
    echo "  Versuche SSH zu starten..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sudo launchctl load -w /System/Library/LaunchDaemons/ssh.plist 2>/dev/null
    fi
fi

# ─── 5. SSH Key generieren (falls nicht vorhanden) ──────────────
echo ""
echo "[5/6] SSH Keys pruefen..."
if [ -f "$HOME/.ssh/id_ed25519" ] || [ -f "$HOME/.ssh/id_rsa" ]; then
    echo "  SSH Key: Vorhanden"
    echo "  Public Key:"
    cat "$HOME/.ssh/id_ed25519.pub" 2>/dev/null || cat "$HOME/.ssh/id_rsa.pub" 2>/dev/null
else
    echo "  Kein SSH Key gefunden. Generiere..."
    ssh-keygen -t ed25519 -f "$HOME/.ssh/id_ed25519" -N "" -C "maurice@aiempire"
    echo "  SSH Key generiert!"
    echo "  Public Key:"
    cat "$HOME/.ssh/id_ed25519.pub"
fi

# ─── 6. Zusammenfassung ─────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════"
echo "  TERMINUS VERBINDUNGSDATEN"
echo "══════════════════════════════════════════════"
echo ""
echo "  Host:     $LOCAL_IP"
echo "  Port:     22"
echo "  User:     $(whoami)"
echo "  Auth:     Passwort oder SSH Key"
echo ""
echo "  TERMINUS APP SETUP:"
echo "  1. Terminus oeffnen"
echo "  2. Hosts → + (Plus-Button)"
echo "  3. Adresse: $LOCAL_IP"
echo "  4. Port: 22 (Standard)"
echo "  5. Benutzername: $(whoami)"
echo "  6. Authentifizierung: Passwort"
echo "  7. Dein Mac-Login-Passwort eingeben"
echo "  8. Connect druecken!"
echo ""
echo "  PROBLEMLOESUNGEN:"
echo "  - 'Connection refused' → SSH ist aus"
echo "    Fix: sudo systemsetup -setremotelogin on"
echo ""
echo "  - 'Connection timed out' → Falsche IP oder anderes WLAN"
echo "    Fix: Mac und Handy muessen im SELBEN WLAN sein"
echo ""
echo "  - 'Permission denied' → Falsches Passwort"
echo "    Fix: Dein Mac-Login-Passwort verwenden"
echo ""
echo "  - Von unterwegs zugreifen → Tailscale installieren"
echo "    Mac: brew install tailscale"
echo "    Handy: Tailscale aus App Store"
echo "    Dann Tailscale-IP in Terminus verwenden"
echo ""
echo "══════════════════════════════════════════════"
echo ""
