#!/usr/bin/env bash
# =============================================================================
# AIEmpire Server Shortcut — Desktop-App + Terminal-Alias + SSH-Config
# =============================================================================
# Ausführen mit: bash /tmp/create_server_shortcut.sh
# Erstellt:
#   ~/Desktop/Server.app       ← Doppelklick → Terminal öffnet sich, SSH startet
#   ssh server                 ← im Terminal
#   alias server               ← im Terminal
# =============================================================================

CONFIG="$HOME/.empire_config"
[[ -f "$CONFIG" ]] && source "$CONFIG" 2>/dev/null || true

# Tailscale IP (Hetzner Dedicated Server) — öffentliche IP ist SSH-gesperrt
TAILSCALE_IP="100.124.239.46"

# ─── Farben ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
ok()   { echo -e "${GREEN}  ✅ $*${RESET}"; }
info() { echo -e "${CYAN}  →  $*${RESET}"; }

clear
echo ""
echo -e "${BOLD}${CYAN}  AIEmpire — Server Shortcut Setup${RESET}"
echo ""

# ─── IP ermitteln ────────────────────────────────────────────────────────────
if [[ -z "${SERVER_HOST:-}" ]]; then
    SERVER_HOST="$TAILSCALE_IP"   # Tailscale-IP verwenden (öffentliche IP ist SSH-gesperrt)
fi
SERVER_USER="${SERVER_USER:-root}"
SERVER_KEY="${SERVER_KEY_PATH:-$HOME/.ssh/id_ed25519}"
echo ""
info "Server: ${SERVER_USER}@${SERVER_HOST}"
info "Key:    ${SERVER_KEY}"
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# 1. Desktop App (Doppelklick → SSH)
# ═══════════════════════════════════════════════════════════════════════════

APP="$HOME/Desktop/🖥 Server.app"
mkdir -p "$APP/Contents/MacOS"

# Haupt-Binary (Shell Script als ausführbare Datei)
cat > "$APP/Contents/MacOS/server" << APPEOF
#!/bin/bash
# Öffne Terminal und SSH
if [ -d "/Applications/iTerm.app" ]; then
    # iTerm2 bevorzugen
    osascript << 'APPLE'
tell application "iTerm"
    activate
    tell current window
        create tab with default profile
        tell current session
            write text "ssh -i ${SERVER_KEY} ${SERVER_USER}@${SERVER_HOST}"
        end tell
    end tell
end tell
APPLE
else
    # Standard Terminal
    osascript << 'APPLE'
tell application "Terminal"
    activate
    do script "ssh -i ${SERVER_KEY} ${SERVER_USER}@${SERVER_HOST}"
end tell
APPLE
fi
APPEOF
chmod +x "$APP/Contents/MacOS/server"

# Info.plist (damit macOS es als App erkennt)
cat > "$APP/Contents/Info.plist" << 'PLISTEOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>server</string>
    <key>CFBundleIdentifier</key>
    <string>com.aiempire.server</string>
    <key>CFBundleName</key>
    <string>Server</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>LSUIElement</key>
    <false/>
</dict>
</plist>
PLISTEOF

ok "Desktop-App erstellt: ~/Desktop/🖥 Server.app"

# ═══════════════════════════════════════════════════════════════════════════
# 2. SSH Config (~/.ssh/config)
# ═══════════════════════════════════════════════════════════════════════════

mkdir -p "$HOME/.ssh"
touch "$HOME/.ssh/config"
chmod 600 "$HOME/.ssh/config"

# Entferne alten Empire-Eintrag falls vorhanden
sed -i '' '/# AIEmpire/,/^$/d' "$HOME/.ssh/config" 2>/dev/null || true

cat >> "$HOME/.ssh/config" << SSHEOF

# AIEmpire Server
Host server empire hetzner
    HostName ${SERVER_HOST}
    User ${SERVER_USER}
    IdentityFile ${SERVER_KEY}
    ServerAliveInterval 60
    ServerAliveCountMax 3
    StrictHostKeyChecking no
SSHEOF

ok "SSH-Config gespeichert → 'ssh server' funktioniert jetzt"

# ═══════════════════════════════════════════════════════════════════════════
# 3. Shell-Aliases in .zshrc
# ═══════════════════════════════════════════════════════════════════════════

ZSHRC="$HOME/.zshrc"

# Alte Empire-Aliases entfernen
sed -i '' '/# ── AIEmpire/,/^$/d' "$ZSHRC" 2>/dev/null || true

cat >> "$ZSHRC" << 'ALIASEOF'

# ── AIEmpire Server ──────────────────────────────────────────────────────
alias server='ssh server'
alias empire='ssh server'
alias server-log='ssh server "tail -f /var/log/aiempire-pipeline.log"'
alias server-db='ssh server "cd /root/AIEmpire-Core && python3 data_processor/main.py db stats"'
alias server-status='ssh server "cd /root/AIEmpire-Core && python3 data_processor/main.py status"'
# ────────────────────────────────────────────────────────────────────────
ALIASEOF

ok "Aliases in ~/.zshrc eingetragen"

# Sofort aktivieren
source "$ZSHRC" 2>/dev/null || true

# ═══════════════════════════════════════════════════════════════════════════
# Fertig
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${BOLD}  Fertig! So verbindest du dich:${RESET}"
echo ""
echo -e "  ${CYAN}Doppelklick${RESET}   → ~/Desktop/🖥 Server.app"
echo -e "  ${CYAN}server${RESET}        → Terminal-Befehl (nach Terminal-Neustart)"
echo -e "  ${CYAN}empire${RESET}        → identisch"
echo -e "  ${CYAN}server-log${RESET}    → Pipeline-Log live"
echo -e "  ${CYAN}server-status${RESET} → Pipeline-Status"
echo -e "  ${CYAN}server-db${RESET}     → Datenbank-Statistiken"
echo ""
echo "  Terminal neu starten damit Aliases aktiv werden."
echo ""
