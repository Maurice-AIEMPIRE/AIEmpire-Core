#!/bin/bash
###############################################################################
# fix_ssh_iphone.sh - SSH Mac → iPhone Diagnose & Reparatur
#
# Behebt automatisch die häufigsten SSH-Verbindungsprobleme:
# - iproxy/usbmuxd nicht laufend (USB-Verbindung)
# - iPhone IP geändert (WiFi-Verbindung)
# - SSH Host Key Konflikte (known_hosts)
# - SSH Service auf iPhone gestoppt
# - Firewall blockiert Verbindung
#
# Usage: ./scripts/fix_ssh_iphone.sh [wifi|usb]
#        Default: versucht beide Methoden
###############################################################################

set -euo pipefail

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Konfiguration - ANPASSEN AN DEIN SETUP
IPHONE_USER="${IPHONE_SSH_USER:-root}"
IPHONE_WIFI_IP="${IPHONE_SSH_IP:-}"
IPHONE_SSH_PORT="${IPHONE_SSH_PORT:-22}"
USB_LOCAL_PORT="${IPHONE_USB_PORT:-2222}"
SSH_TIMEOUT=5
KNOWN_HOSTS="$HOME/.ssh/known_hosts"

print_header() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  🔧 SSH Mac → iPhone - Diagnose & Reparatur${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

log_ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
log_fail() { echo -e "  ${RED}✗${NC} $1"; }
log_warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }
log_info() { echo -e "  ${BLUE}ℹ${NC} $1"; }
log_step() { echo -e "\n${YELLOW}▸ $1${NC}"; }

# ─── SCHRITT 1: Grundvoraussetzungen prüfen ────────────────────────────────

check_prerequisites() {
    log_step "Schritt 1: Grundvoraussetzungen prüfen"

    # SSH Client
    if command -v ssh &>/dev/null; then
        log_ok "SSH Client installiert ($(ssh -V 2>&1 | head -1))"
    else
        log_fail "SSH Client nicht gefunden!"
        exit 1
    fi

    # SSH Verzeichnis
    if [ -d "$HOME/.ssh" ]; then
        log_ok "~/.ssh Verzeichnis existiert"
    else
        log_warn "~/.ssh existiert nicht - erstelle es..."
        mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
        log_ok "~/.ssh erstellt"
    fi

    # SSH Key
    if [ -f "$HOME/.ssh/id_rsa" ] || [ -f "$HOME/.ssh/id_ed25519" ]; then
        log_ok "SSH Key vorhanden"
    else
        log_warn "Kein SSH Key gefunden - generiere ed25519 Key..."
        ssh-keygen -t ed25519 -f "$HOME/.ssh/id_ed25519" -N "" -C "aiempire@mac"
        log_ok "SSH Key generiert: ~/.ssh/id_ed25519"
    fi

    # libimobiledevice (für USB)
    if command -v iproxy &>/dev/null; then
        log_ok "iproxy installiert (USB-Tunnel möglich)"
        HAS_IPROXY=true
    else
        log_warn "iproxy nicht installiert (kein USB-Tunnel möglich)"
        log_info "Installieren mit: brew install libimobiledevice"
        HAS_IPROXY=false
    fi

    # usbmuxd
    if command -v usbmuxd &>/dev/null || [ -S /var/run/usbmuxd ]; then
        log_ok "usbmuxd verfügbar"
        HAS_USBMUXD=true
    else
        log_warn "usbmuxd nicht gefunden"
        HAS_USBMUXD=false
    fi
}

# ─── SCHRITT 2: Known Hosts bereinigen ──────────────────────────────────────

fix_known_hosts() {
    log_step "Schritt 2: SSH Known Hosts bereinigen"

    if [ ! -f "$KNOWN_HOSTS" ]; then
        log_info "Keine known_hosts Datei - nichts zu bereinigen"
        return
    fi

    local cleaned=0

    # Alte iPhone Einträge entfernen (WiFi IP)
    if [ -n "$IPHONE_WIFI_IP" ]; then
        if grep -q "$IPHONE_WIFI_IP" "$KNOWN_HOSTS" 2>/dev/null; then
            ssh-keygen -R "$IPHONE_WIFI_IP" 2>/dev/null || true
            log_ok "Alte WiFi-Einträge für $IPHONE_WIFI_IP entfernt"
            cleaned=$((cleaned + 1))
        fi
    fi

    # Alte localhost/127.0.0.1 Einträge für USB-Port entfernen
    if grep -q "\[localhost\]:$USB_LOCAL_PORT" "$KNOWN_HOSTS" 2>/dev/null; then
        ssh-keygen -R "[localhost]:$USB_LOCAL_PORT" 2>/dev/null || true
        log_ok "Alte USB-Tunnel Einträge (localhost:$USB_LOCAL_PORT) entfernt"
        cleaned=$((cleaned + 1))
    fi

    if grep -q "\[127.0.0.1\]:$USB_LOCAL_PORT" "$KNOWN_HOSTS" 2>/dev/null; then
        ssh-keygen -R "[127.0.0.1]:$USB_LOCAL_PORT" 2>/dev/null || true
        log_ok "Alte USB-Tunnel Einträge (127.0.0.1:$USB_LOCAL_PORT) entfernt"
        cleaned=$((cleaned + 1))
    fi

    if [ $cleaned -eq 0 ]; then
        log_info "Keine veralteten Einträge gefunden"
    fi
}

# ─── SCHRITT 3: USB-Verbindung (iproxy) ────────────────────────────────────

fix_usb_connection() {
    log_step "Schritt 3: USB-Verbindung prüfen & reparieren"

    if [ "$HAS_IPROXY" != "true" ]; then
        log_warn "iproxy nicht verfügbar - USB-Methode übersprungen"
        log_info "Installiere mit: brew install libimobiledevice usbmuxd"
        return 1
    fi

    # iPhone über USB verbunden?
    if command -v idevice_id &>/dev/null; then
        local device_id
        device_id=$(idevice_id -l 2>/dev/null || true)
        if [ -n "$device_id" ]; then
            log_ok "iPhone über USB erkannt: $device_id"
        else
            log_fail "Kein iPhone über USB erkannt!"
            log_info "→ Prüfe ob das USB-Kabel richtig steckt"
            log_info "→ Entsperre das iPhone und bestätige 'Diesem Computer vertrauen'"
            log_info "→ Versuche ein anderes USB-Kabel oder Port"
            return 1
        fi
    else
        log_warn "idevice_id nicht verfügbar - kann USB-Verbindung nicht prüfen"
        log_info "Installiere mit: brew install libimobiledevice"
    fi

    # Alte iproxy Prozesse beenden
    if pgrep -x iproxy &>/dev/null; then
        log_warn "Alte iproxy Prozesse gefunden - beende sie..."
        pkill -x iproxy 2>/dev/null || true
        sleep 1
        log_ok "Alte iproxy Prozesse beendet"
    fi

    # Prüfe ob der Port bereits belegt ist
    if lsof -i ":$USB_LOCAL_PORT" &>/dev/null; then
        log_warn "Port $USB_LOCAL_PORT ist belegt - befreie ihn..."
        lsof -ti ":$USB_LOCAL_PORT" | xargs kill -9 2>/dev/null || true
        sleep 1
        log_ok "Port $USB_LOCAL_PORT befreit"
    fi

    # iproxy starten
    log_info "Starte iproxy Tunnel (localhost:$USB_LOCAL_PORT → iPhone:$IPHONE_SSH_PORT)..."
    iproxy "$USB_LOCAL_PORT" "$IPHONE_SSH_PORT" &>/dev/null &
    IPROXY_PID=$!
    sleep 2

    # Prüfe ob iproxy läuft
    if kill -0 "$IPROXY_PID" 2>/dev/null; then
        log_ok "iproxy Tunnel aktiv (PID: $IPROXY_PID)"
    else
        log_fail "iproxy konnte nicht gestartet werden!"
        return 1
    fi

    # SSH Verbindung über USB testen
    log_info "Teste SSH über USB-Tunnel..."
    if ssh -o ConnectTimeout=$SSH_TIMEOUT \
           -o StrictHostKeyChecking=accept-new \
           -o BatchMode=yes \
           -p "$USB_LOCAL_PORT" \
           "$IPHONE_USER@localhost" "echo 'SSH_OK'" 2>/dev/null; then
        log_ok "SSH über USB funktioniert!"
        echo ""
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}  ✓ VERBINDUNG HERGESTELLT (USB)${NC}"
        echo -e "${GREEN}  Befehl: ssh -p $USB_LOCAL_PORT $IPHONE_USER@localhost${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        return 0
    else
        log_fail "SSH über USB fehlgeschlagen"
        log_info "→ Ist OpenSSH auf dem iPhone installiert und aktiv?"
        log_info "→ Standard-Passwort für jailbroken iPhones: 'alpine'"
        log_info "→ Manuell testen: ssh -vvv -p $USB_LOCAL_PORT $IPHONE_USER@localhost"
        return 1
    fi
}

# ─── SCHRITT 4: WiFi-Verbindung ────────────────────────────────────────────

discover_iphone_ip() {
    log_info "Versuche iPhone im Netzwerk zu finden..."

    # Methode 1: dns-sd / Bonjour
    if command -v dns-sd &>/dev/null; then
        log_info "Suche via Bonjour (5 Sekunden)..."
        local bonjour_result
        bonjour_result=$(timeout 5 dns-sd -B _ssh._tcp 2>/dev/null || true)
        if [ -n "$bonjour_result" ]; then
            log_info "Bonjour SSH Services gefunden:"
            echo "$bonjour_result" | grep -i "iphone\|mobile" || true
        fi
    fi

    # Methode 2: arp scan im lokalen Netz
    if command -v arp &>/dev/null; then
        log_info "Scanne ARP-Tabelle nach Apple Geräten..."
        local gateway
        gateway=$(route -n get default 2>/dev/null | grep gateway | awk '{print $2}' || \
                  ip route show default 2>/dev/null | awk '{print $3}' || true)

        if [ -n "$gateway" ]; then
            local subnet
            subnet=$(echo "$gateway" | sed 's/\.[0-9]*$/.0\/24/')
            log_info "Netzwerk: $subnet"

            # Ping-Sweep (schnell)
            for i in $(seq 1 254); do
                local ip
                ip=$(echo "$gateway" | sed "s/\.[0-9]*$/.$i/")
                ping -c 1 -W 1 "$ip" &>/dev/null &
            done
            wait 2>/dev/null

            # ARP Tabelle nach Apple MACs durchsuchen
            # Apple MAC Prefixes: diverse, aber wir suchen nach allen
            log_info "Mögliche Geräte im Netzwerk:"
            arp -a 2>/dev/null | while read -r line; do
                local ip_found
                ip_found=$(echo "$line" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' || true)
                if [ -n "$ip_found" ]; then
                    # Teste SSH auf Port 22
                    if nc -z -w 1 "$ip_found" 22 2>/dev/null; then
                        log_ok "SSH offen auf: $ip_found"
                    fi
                fi
            done
        fi
    fi

    # Methode 3: nmap (wenn installiert)
    if command -v nmap &>/dev/null; then
        local gateway
        gateway=$(route -n get default 2>/dev/null | grep gateway | awk '{print $2}' || \
                  ip route show default 2>/dev/null | awk '{print $3}' || true)
        if [ -n "$gateway" ]; then
            local subnet
            subnet=$(echo "$gateway" | sed 's/\.[0-9]*$/.0\/24/')
            log_info "nmap Scan für SSH im Netzwerk $subnet..."
            nmap -p 22 --open -sT "$subnet" 2>/dev/null | grep -E "Nmap scan|open|MAC" || true
        fi
    fi
}

fix_wifi_connection() {
    log_step "Schritt 4: WiFi-Verbindung prüfen & reparieren"

    # Wenn keine IP konfiguriert, versuche zu finden
    if [ -z "$IPHONE_WIFI_IP" ]; then
        log_warn "Keine iPhone WiFi IP konfiguriert"
        log_info "Setze IPHONE_SSH_IP in .env oder als Umgebungsvariable"
        log_info "iPhone IP findest du unter: Einstellungen → WLAN → (i) neben deinem Netzwerk"
        echo ""
        discover_iphone_ip
        return 1
    fi

    log_info "Teste Verbindung zu $IPHONE_WIFI_IP..."

    # Ping Test
    if ping -c 2 -W 2 "$IPHONE_WIFI_IP" &>/dev/null; then
        log_ok "iPhone erreichbar via Ping ($IPHONE_WIFI_IP)"
    else
        log_fail "iPhone nicht erreichbar via Ping!"
        log_info "→ Sind Mac und iPhone im gleichen WLAN?"
        log_info "→ iPhone WLAN aktiv? (Einstellungen → WLAN)"
        log_info "→ Hat sich die iPhone IP geändert?"
        log_info "→ iPhone IP prüfen: Einstellungen → WLAN → (i) neben Netzwerkname"
        echo ""
        discover_iphone_ip
        return 1
    fi

    # Port Test
    if nc -z -w "$SSH_TIMEOUT" "$IPHONE_WIFI_IP" "$IPHONE_SSH_PORT" 2>/dev/null; then
        log_ok "SSH Port $IPHONE_SSH_PORT ist offen"
    else
        log_fail "SSH Port $IPHONE_SSH_PORT ist geschlossen oder blockiert!"
        log_info "→ OpenSSH auf dem iPhone aktiv?"
        log_info "→ Firewall auf dem iPhone oder Mac prüfen"
        log_info "→ Bei Jailbreak: Cydia/Sileo → OpenSSH installiert?"
        return 1
    fi

    # SSH Verbindung testen
    log_info "Teste SSH-Verbindung..."
    if ssh -o ConnectTimeout=$SSH_TIMEOUT \
           -o StrictHostKeyChecking=accept-new \
           -o BatchMode=yes \
           -p "$IPHONE_SSH_PORT" \
           "$IPHONE_USER@$IPHONE_WIFI_IP" "echo 'SSH_OK'" 2>/dev/null; then
        log_ok "SSH über WiFi funktioniert!"
        echo ""
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}  ✓ VERBINDUNG HERGESTELLT (WiFi)${NC}"
        echo -e "${GREEN}  Befehl: ssh -p $IPHONE_SSH_PORT $IPHONE_USER@$IPHONE_WIFI_IP${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        return 0
    else
        log_fail "SSH-Authentifizierung fehlgeschlagen!"
        log_info "→ Passwort prüfen (Standard bei Jailbreak: 'alpine')"
        log_info "→ SSH Key auf iPhone kopieren:"
        log_info "   ssh-copy-id -p $IPHONE_SSH_PORT $IPHONE_USER@$IPHONE_WIFI_IP"
        log_info "→ Verbose Modus: ssh -vvv -p $IPHONE_SSH_PORT $IPHONE_USER@$IPHONE_WIFI_IP"
        return 1
    fi
}

# ─── SCHRITT 5: SSH Config Eintrag ─────────────────────────────────────────

update_ssh_config() {
    log_step "Schritt 5: SSH Config aktualisieren"

    local ssh_config="$HOME/.ssh/config"

    # Prüfe ob iPhone-Eintrag existiert
    if [ -f "$ssh_config" ] && grep -q "Host iphone" "$ssh_config" 2>/dev/null; then
        log_ok "SSH Config Eintrag 'iphone' existiert bereits"
        log_info "Aktueller Eintrag:"
        sed -n '/Host iphone/,/^Host /{ /^Host [^i]/!p; }' "$ssh_config" | head -10
        return
    fi

    log_info "Erstelle SSH Config Eintrag..."

    # Sicherstellen dass die Datei existiert
    touch "$ssh_config"
    chmod 600 "$ssh_config"

    # USB-Eintrag
    cat >> "$ssh_config" << EOF

# ─── iPhone SSH (AIEmpire) ─────────────────
# USB-Verbindung (über iproxy)
Host iphone-usb
    HostName localhost
    Port $USB_LOCAL_PORT
    User $IPHONE_USER
    StrictHostKeyChecking accept-new
    ServerAliveInterval 30
    ServerAliveCountMax 3

EOF

    # WiFi-Eintrag (nur wenn IP bekannt)
    if [ -n "$IPHONE_WIFI_IP" ]; then
        cat >> "$ssh_config" << EOF
# WiFi-Verbindung
Host iphone
    HostName $IPHONE_WIFI_IP
    Port $IPHONE_SSH_PORT
    User $IPHONE_USER
    StrictHostKeyChecking accept-new
    ServerAliveInterval 30
    ServerAliveCountMax 3

EOF
        log_ok "SSH Config erstellt: 'ssh iphone' (WiFi) + 'ssh iphone-usb' (USB)"
    else
        # Alias "iphone" zeigt auf USB wenn keine WiFi IP
        cat >> "$ssh_config" << EOF
# Alias (USB default wenn keine WiFi IP)
Host iphone
    HostName localhost
    Port $USB_LOCAL_PORT
    User $IPHONE_USER
    StrictHostKeyChecking accept-new
    ServerAliveInterval 30
    ServerAliveCountMax 3

EOF
        log_ok "SSH Config erstellt: 'ssh iphone' (USB)"
    fi
}

# ─── SCHRITT 6: Zusammenfassung ────────────────────────────────────────────

print_summary() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  📋 Schnellreferenz${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  ${YELLOW}USB-Verbindung:${NC}"
    echo -e "    1. iproxy $USB_LOCAL_PORT $IPHONE_SSH_PORT &"
    echo -e "    2. ssh -p $USB_LOCAL_PORT $IPHONE_USER@localhost"
    echo -e "    Oder: ssh iphone-usb"
    echo ""
    echo -e "  ${YELLOW}WiFi-Verbindung:${NC}"
    if [ -n "$IPHONE_WIFI_IP" ]; then
        echo -e "    ssh -p $IPHONE_SSH_PORT $IPHONE_USER@$IPHONE_WIFI_IP"
        echo -e "    Oder: ssh iphone"
    else
        echo -e "    IPHONE_SSH_IP setzen, dann: ssh iphone"
    fi
    echo ""
    echo -e "  ${YELLOW}Troubleshooting:${NC}"
    echo -e "    ssh -vvv iphone          # Verbose Debug"
    echo -e "    idevice_id -l            # USB iPhone erkennen"
    echo -e "    ping \$IPHONE_SSH_IP      # WiFi Erreichbarkeit"
    echo ""
    echo -e "  ${YELLOW}Konfiguration (.env):${NC}"
    echo -e "    IPHONE_SSH_USER=root"
    echo -e "    IPHONE_SSH_IP=192.168.x.x"
    echo -e "    IPHONE_SSH_PORT=22"
    echo -e "    IPHONE_USB_PORT=2222"
    echo ""
    echo -e "  ${YELLOW}Häufige Probleme:${NC}"
    echo -e "    'Connection refused'  → OpenSSH auf iPhone nicht aktiv"
    echo -e "    'Host key changed'    → ssh-keygen -R <ip>"
    echo -e "    'Permission denied'   → Passwort/Key falsch (Standard: alpine)"
    echo -e "    'Network unreachable' → Unterschiedliches WLAN/Netz"
    echo -e "    'Connection timeout'  → Firewall oder iPhone im Standby"
    echo ""
}

# ─── MAIN ───────────────────────────────────────────────────────────────────

main() {
    local mode="${1:-auto}"

    print_header

    # Lade .env falls vorhanden
    if [ -f "$HOME/AIEmpire-Core/.env" ]; then
        # shellcheck disable=SC1091
        source "$HOME/AIEmpire-Core/.env" 2>/dev/null || true
        log_info "Konfiguration aus .env geladen"
    elif [ -f ".env" ]; then
        # shellcheck disable=SC1091
        source ".env" 2>/dev/null || true
        log_info "Konfiguration aus .env geladen"
    fi

    # Re-read env vars nach .env load
    IPHONE_USER="${IPHONE_SSH_USER:-root}"
    IPHONE_WIFI_IP="${IPHONE_SSH_IP:-}"
    IPHONE_SSH_PORT="${IPHONE_SSH_PORT:-22}"
    USB_LOCAL_PORT="${IPHONE_USB_PORT:-2222}"

    check_prerequisites
    fix_known_hosts

    local connected=false

    case "$mode" in
        usb)
            fix_usb_connection && connected=true
            ;;
        wifi)
            fix_wifi_connection && connected=true
            ;;
        auto|*)
            # Versuche USB zuerst (zuverlässiger), dann WiFi
            log_info "Auto-Modus: Versuche USB zuerst, dann WiFi..."
            if fix_usb_connection 2>/dev/null; then
                connected=true
            else
                log_info "USB fehlgeschlagen, versuche WiFi..."
                fix_wifi_connection && connected=true
            fi
            ;;
    esac

    update_ssh_config
    print_summary

    if [ "$connected" = true ]; then
        echo -e "${GREEN}  ✓ SSH-Verbindung erfolgreich hergestellt!${NC}"
    else
        echo -e "${RED}  ✗ Keine Verbindung möglich - prüfe die Hinweise oben${NC}"
        echo ""
        echo -e "${YELLOW}  Nächste Schritte:${NC}"
        echo -e "  1. Prüfe ob iPhone und Mac im gleichen WLAN sind"
        echo -e "  2. Prüfe ob OpenSSH auf dem iPhone installiert/aktiv ist"
        echo -e "  3. Setze IPHONE_SSH_IP in .env auf die richtige IP"
        echo -e "  4. Führe das Skript erneut aus: ./scripts/fix_ssh_iphone.sh"
    fi
    echo ""
}

main "$@"
