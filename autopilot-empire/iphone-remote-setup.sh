#!/bin/bash
#═══════════════════════════════════════════════════════════════
# Autopilot Empire - iPhone Remote Setup Script
# Maurice's AI Business System - Mac Mini Configuration
#═══════════════════════════════════════════════════════════════
#
# Dieses Script konfiguriert den Mac Mini für iPhone-Fernzugriff:
# 1. SSH aktivieren
# 2. Homebrew installieren/prüfen
# 3. Tailscale installieren (VPN)
# 4. Node.js installieren
# 5. Mac wach halten (kein Sleep)
# 6. Projektordner erstellen
# 7. Verbindungsdaten ausgeben
#
# USAGE: bash iphone-remote-setup.sh
#
#═══════════════════════════════════════════════════════════════

set -e  # Exit on error

echo "═══════════════════════════════════════════════════════════════"
echo "🚀 AUTOPILOT EMPIRE - Mac Mini Setup für iPhone Remote Access"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ═══════════════════════════════════════════════════════════════
# 1. SSH AKTIVIEREN
# ═══════════════════════════════════════════════════════════════
echo "📡 [1/7] Aktiviere SSH..."
if sudo systemsetup -getremotelogin | grep -q "On"; then
    echo "✅ SSH bereits aktiviert"
else
    sudo systemsetup -setremotelogin on
    echo "✅ SSH aktiviert"
fi
echo ""

# ═══════════════════════════════════════════════════════════════
# 2. HOMEBREW
# ═══════════════════════════════════════════════════════════════
echo "🍺 [2/7] Prüfe Homebrew..."
if command -v brew &> /dev/null; then
    echo "✅ Homebrew bereits installiert"
    brew update
else
    echo "⚙️  Installiere Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add to PATH
    if [[ $(uname -m) == 'arm64' ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/usr/local/bin/brew shellenv)"
    fi
    echo "✅ Homebrew installiert"
fi
echo ""

# ═══════════════════════════════════════════════════════════════
# 3. TAILSCALE (VPN für sicheren Remote-Zugriff)
# ═══════════════════════════════════════════════════════════════
echo "🔐 [3/7] Installiere Tailscale..."
if command -v tailscale &> /dev/null; then
    echo "✅ Tailscale bereits installiert"
else
    brew install tailscale
    echo "✅ Tailscale installiert"
fi

# Tailscale starten
if tailscale status &> /dev/null; then
    echo "✅ Tailscale läuft bereits"
else
    echo "⚙️  Starte Tailscale..."
    echo "⚠️  WICHTIG: Tailscale Login-Fenster öffnet sich - bitte anmelden!"
    sudo tailscale up
    echo "✅ Tailscale gestartet"
fi
echo ""

# ═══════════════════════════════════════════════════════════════
# 4. NODE.JS
# ═══════════════════════════════════════════════════════════════
echo "📦 [4/7] Prüfe Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js bereits installiert: $NODE_VERSION"
else
    brew install node
    echo "✅ Node.js installiert"
fi
echo ""

# ═══════════════════════════════════════════════════════════════
# 5. MAC WACH HALTEN (kein Sleep-Modus)
# ═══════════════════════════════════════════════════════════════
echo "⚡ [5/7] Konfiguriere Power Management..."
sudo pmset -c sleep 0
sudo pmset -c displaysleep 10
sudo pmset -c disksleep 0
sudo pmset -c womp 1  # Wake on LAN
echo "✅ Mac bleibt wach (kein Sleep bei Netzteil)"
echo ""

# ═══════════════════════════════════════════════════════════════
# 6. PROJEKTORDNER ERSTELLEN
# ═══════════════════════════════════════════════════════════════
echo "📁 [6/7] Erstelle Projektordner..."
PROJECT_DIR="$HOME/autopilot-empire"

if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p "$PROJECT_DIR"
    echo "✅ Projektordner erstellt: $PROJECT_DIR"
else
    echo "✅ Projektordner existiert bereits: $PROJECT_DIR"
fi
echo ""

# ═══════════════════════════════════════════════════════════════
# 7. VERBINDUNGSDATEN AUSGEBEN
# ═══════════════════════════════════════════════════════════════
echo "🎉 [7/7] Setup abgeschlossen!"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📱 IPHONE-VERBINDUNG - SETUP ANLEITUNG"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Tailscale IP ermitteln
TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "NICHT VERFÜGBAR - Bitte 'tailscale ip -4' ausführen")
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "NICHT VERFÜGBAR")
USERNAME=$(whoami)
HOSTNAME=$(hostname)

echo "🔐 VERBINDUNGSDATEN:"
echo "   Tailscale IP:  $TAILSCALE_IP (empfohlen - von überall)"
echo "   Lokale IP:     $LOCAL_IP (nur im gleichen WLAN)"
echo "   Username:      $USERNAME"
echo "   Port:          22 (SSH)"
echo ""

echo "📱 IPHONE APPS ZU INSTALLIEREN:"
echo "   1. Tailscale (App Store) - VPN Verbindung"
echo "   2. Termius (App Store) - SSH Client"
echo ""

echo "⚙️  IPHONE SETUP SCHRITTE:"
echo ""
echo "SCHRITT 1: Tailscale einrichten"
echo "   - Tailscale App öffnen"
echo "   - Mit dem GLEICHEN Account anmelden wie auf diesem Mac"
echo "   - Verbindung herstellen"
echo ""

echo "SCHRITT 2: Termius konfigurieren"
echo "   - Termius App öffnen"
echo "   - 'New Host' erstellen:"
echo "     * Alias: Mac Mini Autopilot"
echo "     * Hostname: $TAILSCALE_IP"
echo "     * Port: 22"
echo "     * Username: $USERNAME"
echo "     * Password: [Dein Mac-Passwort]"
echo "   - Verbindung testen"
echo ""

echo "SCHRITT 3: System starten"
echo "   Im Termius Terminal:"
echo "   cd ~/autopilot-empire"
echo "   docker-compose up -d"
echo ""

echo "SCHRITT 4: Dashboard aufrufen"
echo "   Im Safari Browser:"
echo "   http://$TAILSCALE_IP:8000     (Agent Dashboard)"
echo "   http://$TAILSCALE_IP:9090     (Monitoring)"
echo ""

# Speichere Infos in Datei
SETUP_FILE="$PROJECT_DIR/IPHONE-SETUP.txt"
cat > "$SETUP_FILE" << EOF
═══════════════════════════════════════════════════════════════
AUTOPILOT EMPIRE - iPhone Remote Access Setup
Erstellt: $(date)
═══════════════════════════════════════════════════════════════

VERBINDUNGSDATEN:
   Tailscale IP:  $TAILSCALE_IP
   Lokale IP:     $LOCAL_IP
   Username:      $USERNAME
   SSH Port:      22
   Hostname:      $HOSTNAME

IPHONE APPS:
   - Tailscale (VPN)
   - Termius (SSH)

URLS:
   Agent Dashboard:  http://$TAILSCALE_IP:8000
   Monitoring:       http://$TAILSCALE_IP:9090

QUICK COMMANDS:
   # System starten
   cd ~/autopilot-empire && docker-compose up -d
   
   # System stoppen
   cd ~/autopilot-empire && docker-compose down
   
   # Logs anzeigen
   cd ~/autopilot-empire && docker-compose logs -f
   
   # System Status
   cd ~/autopilot-empire && docker-compose ps
   
   # Tmux Session erstellen (persistent)
   tmux new -s autopilot
   
   # Tmux wieder verbinden
   tmux attach -t autopilot
   
   # Alle Tmux Sessions anzeigen
   tmux ls

═══════════════════════════════════════════════════════════════
EOF

echo "💾 Setup-Info gespeichert: $SETUP_FILE"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ SETUP ERFOLGREICH ABGESCHLOSSEN!"
echo ""
echo "📝 Nächste Schritte:"
echo "   1. Tailscale auf iPhone installieren und anmelden"
echo "   2. Termius auf iPhone installieren und Host konfigurieren"
echo "   3. Vom iPhone aus verbinden"
echo "   4. Docker Stack starten: cd ~/autopilot-empire && docker-compose up -d"
echo ""
echo "📄 Alle Infos wurden gespeichert in: $SETUP_FILE"
echo "═══════════════════════════════════════════════════════════════"
